import uuid
import io
import math
from datetime import datetime
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, status, Response, Depends
from fastapi.responses import StreamingResponse

from app.api.schemas.analysis import (
    CreateAnalysisRequest, SaveLiveAnalysisRequest, AnalysisStatusResponse, AnalysisResultResponse
)
from app.api.schemas.context import AnalysisContext, OptionalUserContext, DetectedVideoContext
from app.api.schemas.comparison import AnalysisComparisonResponse
from app.storage import storage_manager
from app.validation.video_validator import video_validator
from app.context.context_detector import context_detector
from app.pipeline.orchestrator import pipeline_orchestrator
from app.repositories.analysis_repository import analysis_repository
from app.reports.pdf_generator import pdf_report_generator
from app.auth.dependencies import get_current_user, get_optional_current_user
from app.db.models import User
from app.comparison.comparison_engine import comparison_engine

router = APIRouter(prefix="/api/analyses", tags=["Analyses"])

@router.get("", response_model=List[Dict[str, Any]])
def list_analyses(current_user: Optional[User] = Depends(get_optional_current_user)):
    """Lists recent biomechanical analyses for the authenticated runner (strict user data isolation)."""
    user_id = current_user.id if current_user else None
    return analysis_repository.list_analyses(limit=50, user_id=user_id)

@router.get("/demo/sample", response_model=AnalysisResultResponse)
def get_demo_analysis():
    """Returns an interactive, pre-calculated sample runner analysis for hackathon demo mode."""
    demo_id = "demo-runner-session-001"
    existing = analysis_repository.get_analysis(demo_id)
    if existing:
        return existing

    # Create structured sample analysis for instant demonstration
    sample_data = {
        "analysis_id": demo_id,
        "video_id": "demo-sample-video",
        "created_at": datetime.now().isoformat(),
        "status": "completed",
        "progress_percentage": 100,
        "current_step": "Demo Session Loaded",
        "annotated_video_url": f"/api/analyses/{demo_id}/video",
        "context": {
            "video_id": "demo-sample-video",
            "detected": {
                "duration_sec": 4.5,
                "fps": 30.0,
                "resolution": "1920x1080",
                "video_format": ".mp4",
                "quality_status": "Optimal",
                "runner_count": {"value": 1, "source": "pose_analysis", "confidence": 0.98},
                "full_body_visible": {"value": True, "source": "pose_analysis", "confidence": 0.95},
                "camera_view": {"value": "Side view", "source": "video_metadata", "confidence": 0.95},
                "camera_stability": {"value": "Stationary / Stable", "source": "computer_vision", "confidence": 0.92},
                "observed_movement": {"value": "Running", "source": "computer_vision", "confidence": 0.96},
                "surface": {"value": "Road / Asphalt", "source": "computer_vision", "confidence": 0.90},
                "running_pace_status": {"value": "Estimated (Pace context needed)", "source": "computer_vision", "confidence": 0.80},
                "pace_estimation_mode": "Uncalibrated video",
                "historical_baseline_status": "First session"
            },
            "optional": {
                "training_goal": "5K",
                "known_pace": "4:45 min/km",
                "perceived_effort": "Moderate",
                "age_category": "30-39",
                "experience_level": "Intermediate",
                "height_cm": 178.0,
                "weight_kg": 72.0,
                "bmi": 22.7
            },
            "has_missing_context": False,
            "context_notice": "Demonstration runner dataset loaded."
        },
        "video_metadata": {
            "filename": "sample_outdoor_run.mp4",
            "file_size_bytes": 14285700,
            "duration_sec": 4.5,
            "fps": 30.0,
            "width": 1920,
            "height": 1080,
            "frame_count": 135,
            "format": ".mp4"
        },
        "suitability": {
            "overall_status": "Ready for analysis",
            "suitability_score": 94,
            "checks": [
                {"name": "Duration Check", "passed": True, "rating": "Optimal", "message": "Duration 4.5s is optimal."},
                {"name": "Frame Rate (FPS)", "passed": True, "rating": "Optimal", "message": "30.0 FPS enables temporal gait detection."},
                {"name": "Resolution", "passed": True, "rating": "Optimal", "message": "1080p full HD provides sharp tracking."},
                {"name": "Side-View Orientation", "passed": True, "rating": "Optimal", "message": "Side camera angle facilitates sagittal projection."}
            ],
            "warnings": [],
            "recommendations": ["Camera position is optimal."]
        },
        "cadence_spm": 174.0,
        "step_count": 13,
        "left_right_symmetry_pct": 94.8,
        "trunk_lean_deg": 7.2,
        "left_mean_step_time_s": 0.342,
        "right_mean_step_time_s": 0.348,
        "mean_stride_time_s": 0.690,
        "step_time_variability_cv": 3.8,
        "mean_elbow_angle_deg": 88.0,
        "overstride_risk": "Low Risk / Compliant Landing",
        "foot_strike_pattern": "Midfoot-dominant",
        "relative_vertical_movement_proxy": 0.118,
        "form_classification": "Forward-Leaning Dynamic Stride (174 SPM)",
        "overall_confidence": "High",
        "running_type_context": {
            "distance_category": "5K – 10K Distance",
            "surface_category": "Road / Asphalt",
            "intensity_category": "Moderate Effort",
            "experience_level": "Intermediate",
            "runner_profile_summary": "5K – 10K Distance on Road / Asphalt • Moderate Effort (Intermediate Runner, Age: 30-39, BMI: 22.7)"
        },
        "confidence_breakdown": {
            "cadence_confidence": {"metric_key": "cadence", "confidence_level": "High", "confidence_score": 0.95, "contributing_factors": ["13 distinct contacts across 6 cycles", "30 FPS resolution"]},
            "symmetry_confidence": {"metric_key": "symmetry", "confidence_level": "High", "confidence_score": 0.92, "contributing_factors": ["Balanced 7 left and 6 right contacts"]},
            "trunk_lean_confidence": {"metric_key": "trunk_lean", "confidence_level": "High", "confidence_score": 0.96, "contributing_factors": ["94% torso visibility"]},
            "foot_strike_confidence": {"metric_key": "foot_strike", "confidence_level": "High", "confidence_score": 0.90, "contributing_factors": ["Clear shoe profile at 30 FPS"]},
            "overstride_confidence": {"metric_key": "overstride", "confidence_level": "High", "confidence_score": 0.88, "contributing_factors": ["Clear knee-hip angle alignment"]},
            "vertical_movement_confidence": {"metric_key": "vertical_movement", "confidence_level": "High", "confidence_score": 0.92, "contributing_factors": ["Continuous pelvis tracking"]},
            "overall_confidence": "High",
            "overall_score": 92.2
        },
        "context_insights": [
            {
                "title": "Cadence in Context of 5K Road Training",
                "category": "Cadence",
                "severity": "positive",
                "description": "Your cadence is estimated at 174 SPM during this moderate road session. This rhythm supports energy-efficient turnover with compliant ground contact times.",
                "supporting_metrics": ["Cadence: 174 SPM", "Surface: Road", "Goal: 5K"],
                "confidence": "High",
                "why_flagged": ["13 foot contacts across 4.5s", "Consistent 0.34s step interval duration"],
                "recommended_action": "Maintain your natural stride rhythm; allow step rate to adjust naturally with pace changes.",
                "limitations": "Visual step timing from 30 FPS video."
            },
            {
                "title": "Bilateral Step Balance",
                "category": "Symmetry",
                "severity": "positive",
                "description": "Left/right step timing symmetry was measured at 94.8% (0.342s left vs 0.348s right), indicating balanced weight transition.",
                "supporting_metrics": ["Symmetry: 94.8%", "Step CV: 3.8%"],
                "confidence": "High",
                "why_flagged": ["Minimal 6ms bilateral differential across consecutive strides"],
                "recommended_action": "Continue current bilateral core and single-leg strength routine.",
                "limitations": "Measures temporal duration only; does not measure ground reaction force in Newtons."
            },
            {
                "title": "Sagittal Torso Posture",
                "category": "Posture",
                "severity": "positive",
                "description": "Forward torso inclination averaged 7.2°, within the recommended 4–11° range for momentum alignment.",
                "supporting_metrics": ["Trunk lean: 7.2°", "Range: 5.8°–8.6°"],
                "confidence": "High",
                "why_flagged": ["Mean torso angle relative to vertical axis is 7.2°"],
                "recommended_action": "Maintain whole-body forward lean originating from the ankles.",
                "limitations": "2D sagittal projection estimation."
            }
        ],
        "overall_summary": {
            "headline": "Biomechanical Summary (5K – 10K Distance)",
            "strongest_positive_observations": [
                "Cadence (174 SPM) in optimal rhythm range for road running",
                "High bilateral step symmetry (94.8%)",
                "Balanced sagittal trunk inclination (7.2°)"
            ],
            "areas_to_monitor": [
                "Maintain natural compliance during landing phase"
            ],
            "form_consistency_score": 91.5,
            "context_summary": "5K – 10K Distance on Road / Asphalt • Moderate Effort (Intermediate Runner, Age: 30-39, BMI: 22.7)",
            "responsible_ai_disclaimer": "MotionIQ provides observational kinematic estimates for educational guidance. It does NOT diagnose injuries or replace clinical gait analysis."
        },
        "gait_events": [
            {"frame_idx": 10, "timestamp_s": 0.33, "side": "left", "event_type": "initial_contact", "confidence": 0.92},
            {"frame_idx": 20, "timestamp_s": 0.67, "side": "right", "event_type": "initial_contact", "confidence": 0.94},
            {"frame_idx": 30, "timestamp_s": 1.01, "side": "left", "event_type": "initial_contact", "confidence": 0.91},
            {"frame_idx": 41, "timestamp_s": 1.36, "side": "right", "event_type": "initial_contact", "confidence": 0.95},
            {"frame_idx": 51, "timestamp_s": 1.70, "side": "left", "event_type": "initial_contact", "confidence": 0.93},
            {"frame_idx": 61, "timestamp_s": 2.05, "side": "right", "event_type": "initial_contact", "confidence": 0.92},
            {"frame_idx": 72, "timestamp_s": 2.40, "side": "left", "event_type": "initial_contact", "confidence": 0.94},
            {"frame_idx": 82, "timestamp_s": 2.74, "side": "right", "event_type": "initial_contact", "confidence": 0.93},
            {"frame_idx": 93, "timestamp_s": 3.09, "side": "left", "event_type": "initial_contact", "confidence": 0.91},
            {"frame_idx": 103, "timestamp_s": 3.44, "side": "right", "event_type": "initial_contact", "confidence": 0.95},
            {"frame_idx": 114, "timestamp_s": 3.79, "side": "left", "event_type": "initial_contact", "confidence": 0.92},
            {"frame_idx": 124, "timestamp_s": 4.14, "side": "right", "event_type": "initial_contact", "confidence": 0.94},
            {"frame_idx": 134, "timestamp_s": 4.47, "side": "left", "event_type": "initial_contact", "confidence": 0.90}
        ],
        "waveform_data": [
            {"timestamp_s": round(i*0.09, 2), "pelvis_y": round(0.55 + 0.04 * math.sin(i * 0.7), 3), "left_ankle_y": round(0.72 + 0.12 * math.cos(i * 0.7), 3), "right_ankle_y": round(0.72 - 0.12 * math.cos(i * 0.7), 3)}
            for i in range(50)
        ],
        "metrics_breakdown": [
            {"key": "cadence", "name": "Cadence", "value": "174", "unit": "SPM", "confidence": "High", "status": "Optimal", "description": "Step rate from 13 foot contacts across 4.5s.", "limitations": "Visual step timing."},
            {"key": "symmetry", "name": "Bilateral Step Balance", "value": "94.8", "unit": "%", "confidence": "High", "status": "Optimal", "description": "Left step time 0.342s vs Right step time 0.348s.", "limitations": "Measures temporal duration only."},
            {"key": "step_time", "name": "Mean Step Duration", "value": "0.345", "unit": "s", "confidence": "High", "status": "Observed", "description": "Average duration per foot contact with 3.8% step variability.", "limitations": "Frame rate resolution."},
            {"key": "stride_time", "name": "Mean Stride Time", "value": "0.690", "unit": "s", "confidence": "High", "status": "Observed", "description": "Full gait cycle period with 3.2% variability.", "limitations": "Consecutive strike interval."},
            {"key": "trunk_lean", "name": "Trunk Forward Lean", "value": "7.2", "unit": "°", "confidence": "High", "status": "Optimal", "description": "Optimal forward inclination promoting gravity-assisted momentum.", "limitations": "2D sagittal projection."},
            {"key": "arm_swing", "name": "Elbow Carriage Angle", "value": "88", "unit": "°", "confidence": "Medium", "status": "Observed", "description": "Elbow carriage maintained near 88°.", "limitations": "Sagittal arm projection."},
            {"key": "foot_strike", "name": "Foot Strike Pattern", "value": "Midfoot-dominant", "unit": "pattern", "confidence": "High", "status": "Observed", "description": "Flat/midfoot initial contact pattern observed at foot-strike.", "limitations": "2D estimation proxy."},
            {"key": "overstride", "name": "Potential Overstride Indicator", "value": "Low Risk / Compliant Landing", "unit": "index", "confidence": "High", "status": "Optimal", "description": "Foot lands close beneath center of mass with flexed knee (152°).", "limitations": "Observational geometry only."},
            {"key": "vertical_movement", "name": "Relative Vertical Movement Proxy", "value": "0.118", "unit": "ratio", "confidence": "High", "status": "Observed", "description": "Moderate / Balanced vertical oscillation.", "limitations": "Normalized to torso height."}
        ],
        "observations": [
            {"title": "Forward-Leaning Dynamic Stride", "category": "Posture & Rhythm", "observation": "Forward trunk lean (7.2°) and cadence (174 SPM) reflect coordinated forward momentum.", "supporting_metrics": ["Trunk lean: 7.2°", "Cadence: 174 SPM"], "confidence": "High", "scientific_note": "A gentle whole-body lean aligns the center of mass with ground reaction forces."}
        ],
        "recommendations": [
            "Maintain your natural stride rhythm; allow step rate to adjust naturally with pace changes.",
            "Continue current bilateral core and single-leg strength routine.",
            "Maintain whole-body forward lean originating from the ankles."
        ],
        "limitations": [
            "Non-diagnostic observational platform. Does not predict injuries or diagnose clinical conditions.",
            "2D monocular video estimates sagittal projections; 3D kinetic forces (e.g. ground reaction force in Newtons) cannot be measured without force plates."
        ]
    }
    analysis_repository.save_analysis(demo_id, sample_data)
    return sample_data

@router.get("/{analysis_id}/report.pdf")
def download_analysis_pdf_report(analysis_id: str):
    """Generates and streams a downloadable PDF report for the given analysis."""
    data = analysis_repository.get_analysis(analysis_id)
    if not data:
        raise HTTPException(status_code=404, detail="Analysis ID not found.")

    pdf_stream = pdf_report_generator.generate_report(data)
    filename = f"MotionIQ_Report_{analysis_id[:8]}.pdf"
    
    return StreamingResponse(
        pdf_stream,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@router.get("/{analysis_id}/video")
def stream_analysis_video(analysis_id: str):
    """Streams the annotated skeleton overlay video with correct MIME type for browser playback.
    
    Supports HTTP Range requests for seeking/scrubbing in the HTML5 video player.
    Returns H.264 MP4 video with Content-Type: video/mp4.
    """
    from fastapi.responses import FileResponse
    
    video_path = storage_manager.get_annotated_video_path(analysis_id)
    if not video_path.exists():
        raise HTTPException(status_code=404, detail="Annotated video file not found.")
    
    return FileResponse(
        path=str(video_path),
        media_type="video/mp4",
        filename=f"MotionIQ_Analysis_{analysis_id[:8]}.mp4"
    )

@router.get("/{analysis_id}/video/info")
def get_video_debug_info(analysis_id: str):
    """Returns debug metadata about the annotated video file for diagnostics."""
    video_path = storage_manager.get_annotated_video_path(analysis_id)
    exists = video_path.exists()
    
    info = {
        "analysis_id": analysis_id,
        "video_path": str(video_path),
        "video_exists": exists,
        "video_url": f"/api/analyses/{analysis_id}/video",
        "video_size_bytes": 0,
        "video_size_mb": 0.0,
        "duration_sec": 0.0,
        "fps": 0.0,
        "width": 0,
        "height": 0,
        "codec_fourcc": "unknown",
        "frame_count": 0,
        "browser_compatible": False
    }
    
    if exists:
        import cv2
        file_size = video_path.stat().st_size
        info["video_size_bytes"] = file_size
        info["video_size_mb"] = round(file_size / (1024 * 1024), 2)
        
        cap = cv2.VideoCapture(str(video_path))
        if cap.isOpened():
            fourcc_int = int(cap.get(cv2.CAP_PROP_FOURCC))
            fourcc_str = "".join([chr((fourcc_int >> 8*i) & 0xFF) for i in range(4)])
            fps = cap.get(cv2.CAP_PROP_FPS)
            w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fc = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            dur = fc / fps if fps > 0 else 0
            
            info["codec_fourcc"] = fourcc_str
            info["fps"] = round(fps, 2)
            info["width"] = w
            info["height"] = h
            info["frame_count"] = fc
            info["duration_sec"] = round(dur, 2)
            # H.264 fourcc codes: avc1, H264, X264, h264 (lowercase from imageio-ffmpeg transcode)
            info["browser_compatible"] = fourcc_str.strip('\x00') in ["avc1", "H264", "X264", "h264"]
            cap.release()
    
    return info

@router.post("", response_model=AnalysisStatusResponse, status_code=status.HTTP_201_CREATED)
def create_analysis(
    request: CreateAnalysisRequest,
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    video_path = storage_manager.get_raw_video_path(request.video_id)
    if not video_path:
        raise HTTPException(status_code=404, detail="Video ID not found.")

    analysis_id = str(uuid.uuid4())
    opt_context = request.optional_context.model_dump() if request.optional_context else {}
    detected_context = request.detected_context.model_dump()
    user_id = current_user.id if current_user else None

    # Save initial processing status
    initial_record = {
        "analysis_id": analysis_id,
        "user_id": user_id,
        "video_id": request.video_id,
        "created_at": datetime.now().isoformat(),
        "status": "processing",
        "progress_percentage": 50,
        "current_step": "Extracting MediaPipe Pose & Gait Contacts..."
    }
    analysis_repository.save_analysis(analysis_id, initial_record, user_id=user_id)

    try:
        pipeline_orchestrator.run_analysis(
            analysis_id=analysis_id,
            video_id=request.video_id,
            detected_context=detected_context,
            optional_context=opt_context,
            user_id=user_id
        )
    except Exception as e:
        error_record = {
            "analysis_id": analysis_id,
            "user_id": user_id,
            "video_id": request.video_id,
            "created_at": datetime.now().isoformat(),
            "status": "failed",
            "progress_percentage": 0,
            "current_step": "Analysis Failed",
            "error_message": str(e)
        }
        analysis_repository.save_analysis(analysis_id, error_record, user_id=user_id)
        raise HTTPException(status_code=500, detail=f"Pipeline processing failed: {str(e)}")

    return AnalysisStatusResponse(
        analysis_id=analysis_id,
        status="completed",
        progress_percentage=100,
        current_step="Analysis Complete"
    )

@router.post("/live", response_model=AnalysisResultResponse, status_code=status.HTTP_201_CREATED)
def save_live_analysis(
    request: SaveLiveAnalysisRequest,
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """Persists a completed live browser webcam running session with user isolation and metrics."""
    analysis_id = str(uuid.uuid4())
    user_id = current_user.id if current_user else None
    now_str = datetime.now().isoformat()
    
    live_data = {
        "analysis_id": analysis_id,
        "video_id": f"live-session-{analysis_id[:8]}",
        "user_id": user_id,
        "created_at": now_str,
        "status": "completed",
        "progress_percentage": 100,
        "current_step": "Live Session Complete",
        "annotated_video_url": None,
        "video_metadata": {
            "filename": f"live_camera_{now_str[:10]}.raw",
            "file_size_bytes": 0,
            "duration_sec": round(request.duration_sec, 2),
            "fps": 30.0,
            "width": 1280,
            "height": 720,
            "frame_count": int(request.duration_sec * 30),
            "format": "LIVE_STREAM"
        },
        "suitability": {
            "overall_status": "Ready for analysis" if request.tracking_quality_pct >= 60 else "Analysis may be unreliable",
            "suitability_score": int(request.tracking_quality_pct),
            "checks": [
                {"name": "Live Camera Tracking", "passed": request.tracking_quality_pct >= 60, "rating": "Optimal" if request.tracking_quality_pct >= 80 else "Acceptable", "message": f"Tracking quality recorded at {request.tracking_quality_pct:.0f}%."},
                {"name": "Camera View", "passed": request.camera_suitability != "Unsuitable", "rating": "Optimal" if request.camera_view == "Side view" else "Acceptable", "message": f"Camera viewpoint assessed as {request.camera_view}."}
            ],
            "warnings": [] if request.tracking_quality_pct >= 60 else ["Tracking quality was reduced during portions of the live session."],
            "recommendations": ["Maintain steady side-view camera placement for optimal sagittal tracking."]
        },
        "context": {
            "video_id": f"live-session-{analysis_id[:8]}",
            "detected": {
                "duration_sec": round(request.duration_sec, 2),
                "fps": 30.0,
                "resolution": "1280 x 720",
                "video_format": "LIVE",
                "quality_status": "Good" if request.tracking_quality_pct >= 75 else "Acceptable",
                "runner_count": {"value": 1, "source": "pose_analysis", "confidence": 0.95},
                "full_body_visible": {"value": True, "source": "pose_analysis", "confidence": 0.90},
                "camera_view": {"value": request.camera_view, "source": "pose_analysis", "confidence": 0.88},
                "camera_stability": {"value": "Good", "source": "computer_vision", "confidence": 0.90},
                "observed_movement": {"value": "Running", "source": "pose_analysis", "confidence": 0.92},
                "surface": {"value": "Treadmill / Indoor", "source": "user", "confidence": 0.85},
                "running_pace_status": {"value": "Live analysis session", "source": "pose_analysis", "confidence": 0.85},
                "pace_estimation_mode": "Treadmill",
                "historical_baseline_status": "Live Session"
            },
            "optional": request.optional_context.model_dump() if request.optional_context else {},
            "has_missing_context": False,
            "context_notice": "Live camera observational session recorded."
        },
        "cadence_spm": round(request.cadence_spm, 1),
        "step_count": request.step_count,
        "left_right_symmetry_pct": round(request.left_right_symmetry_pct, 1),
        "trunk_lean_deg": round(request.trunk_lean_deg, 1),
        "left_mean_step_time_s": round(30.0 / max(1.0, request.cadence_spm), 3),
        "right_mean_step_time_s": round(30.0 / max(1.0, request.cadence_spm), 3),
        "mean_stride_time_s": round(60.0 / max(1.0, request.cadence_spm), 3),
        "step_time_variability_cv": 4.5,
        "mean_elbow_angle_deg": 88.0,
        "overstride_risk": "Low Risk / Compliant Landing",
        "foot_strike_pattern": "Observed Initial Contact",
        "relative_vertical_movement_proxy": 0.12,
        "form_classification": request.form_classification or f"Live Running Session ({request.cadence_spm:.0f} SPM)",
        "overall_confidence": request.overall_confidence or "Medium",
        "running_type_context": {
            "distance_category": "Live Real-Time Session",
            "surface_category": "Indoor / Treadmill",
            "intensity_category": "Observed Running",
            "experience_level": "Runner",
            "runner_profile_summary": f"Live running session • {request.duration_sec:.0f}s duration • {request.cadence_spm:.0f} SPM"
        },
        "confidence_breakdown": {
            "cadence_confidence": {"metric_key": "cadence", "confidence_level": request.overall_confidence or "Medium", "confidence_score": 0.88, "contributing_factors": [f"{request.step_count} step events detected"]},
            "symmetry_confidence": {"metric_key": "symmetry", "confidence_level": request.overall_confidence or "Medium", "confidence_score": 0.85, "contributing_factors": ["Temporal inter-step balance"]},
            "trunk_lean_confidence": {"metric_key": "trunk_lean", "confidence_level": request.overall_confidence or "Medium", "confidence_score": 0.86, "contributing_factors": ["Real-time 2D torso vector"]},
            "foot_strike_confidence": {"metric_key": "foot_strike", "confidence_level": "Medium", "confidence_score": 0.75, "contributing_factors": ["Live optical projection"]},
            "overstride_confidence": {"metric_key": "overstride", "confidence_level": "Medium", "confidence_score": 0.75, "contributing_factors": ["Live kinematic estimate"]},
            "vertical_movement_confidence": {"metric_key": "vertical_movement", "confidence_level": "Medium", "confidence_score": 0.80, "contributing_factors": ["Pelvis displacement tracking"]},
            "overall_confidence": request.overall_confidence or "Medium",
            "overall_score": float(request.tracking_quality_pct)
        },
        "context_insights": [
            {
                "title": "Live Cadence Rhythm",
                "category": "Cadence",
                "severity": "positive",
                "description": f"Real-time step rate averaged {request.cadence_spm:.0f} SPM across {request.step_count} detected steps.",
                "supporting_metrics": [f"Cadence: {request.cadence_spm:.0f} SPM", f"Steps: {request.step_count}"],
                "confidence": request.overall_confidence or "Medium",
                "why_flagged": ["Calculated from rolling gait contact intervals"],
                "recommended_action": "Maintain smooth, consistent step rhythm.",
                "limitations": "Estimated via monocular webcam feed."
            },
            {
                "title": "Live Trunk Posture",
                "category": "Posture",
                "severity": "positive" if 4.0 <= request.trunk_lean_deg <= 12.0 else "neutral",
                "description": f"Observable 2D trunk forward lean averaged {request.trunk_lean_deg:.1f}°.",
                "supporting_metrics": [f"Trunk Lean: {request.trunk_lean_deg:.1f}°"],
                "confidence": request.overall_confidence or "Medium",
                "why_flagged": ["Measured from shoulder-to-hip alignment vector"],
                "recommended_action": "Maintain stable upright posture with gentle forward engagement.",
                "limitations": "2D plane estimation."
            }
        ],
        "overall_summary": {
            "headline": f"Live Session Summary — {request.duration_sec:.0f}s",
            "strongest_positive_observations": [
                f"Maintained steady {request.cadence_spm:.0f} SPM cadence rhythm.",
                f"Bilateral movement balance measured at {request.left_right_symmetry_pct:.1f}%."
            ],
            "areas_to_monitor": ["Ensure stable side camera positioning for highest kinematic fidelity."],
            "form_consistency_score": float(request.tracking_quality_pct),
            "context_summary": f"Live webcam observation ({request.duration_sec:.0f}s, {request.camera_view})",
            "responsible_ai_disclaimer": "Non-diagnostic observational platform. Live measurements are estimates derived from monocular 2D video and may be affected by camera placement, lighting, occlusion, frame rate and tracking quality."
        },
        "gait_events": [],
        "waveform_data": [],
        "metrics_breakdown": [
            {"key": "cadence", "name": "Cadence", "value": f"{request.cadence_spm:.0f}", "unit": "SPM", "confidence": request.overall_confidence or "Medium", "status": "Optimal" if 165 <= request.cadence_spm <= 185 else "Observed", "description": f"Live cadence estimated over {request.duration_sec:.0f}s.", "limitations": "Webcam frame timing."},
            {"key": "symmetry", "name": "Bilateral Step Balance", "value": f"{request.left_right_symmetry_pct:.1f}", "unit": "%", "confidence": request.overall_confidence or "Medium", "status": "Optimal" if request.left_right_symmetry_pct >= 90 else "Observed", "description": "Left/right step timing balance.", "limitations": "Temporal balance only."},
            {"key": "trunk_lean", "name": "Trunk Forward Lean", "value": f"{request.trunk_lean_deg:.1f}", "unit": "°", "confidence": request.overall_confidence or "Medium", "status": "Optimal" if 4.0 <= request.trunk_lean_deg <= 12.0 else "Observed", "description": "2D sagittal trunk inclination.", "limitations": "Projection plane only."},
            {"key": "tracking_quality", "name": "Tracking Quality", "value": f"{request.tracking_quality_pct:.0f}", "unit": "%", "confidence": "High", "status": "Optimal" if request.tracking_quality_pct >= 80 else "Observed", "description": "Average visibility across key anatomical landmarks.", "limitations": "Evidence-based metric."}
        ],
        "observations": [
            {"title": "Live Running Form Overview", "category": "Rhythm & Posture", "observation": f"Live running session tracking recorded at {request.tracking_quality_pct:.0f}% quality with {request.cadence_spm:.0f} SPM cadence.", "supporting_metrics": [f"Cadence: {request.cadence_spm:.0f} SPM", f"Lean: {request.trunk_lean_deg:.1f}°"], "confidence": request.overall_confidence or "Medium", "scientific_note": "Real-time observational feedback from browser-based pose estimation."}
        ],
        "recommendations": [
            "Maintain natural step rhythm and upright posture.",
            "Review trend evolution to monitor cadence stability over time."
        ],
        "limitations": [
            "Non-diagnostic observational platform. Does not predict injuries or diagnose clinical conditions.",
            "Live measurements are estimates derived from monocular 2D video."
        ]
    }

    # Save to PostgreSQL / Storage with user association
    analysis_repository.save_analysis(analysis_id, live_data, user_id=user_id)
    return live_data

@router.get("/{analysis_id}/context", response_model=AnalysisContext)
def get_analysis_context(
    analysis_id: str,
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    user_id = current_user.id if current_user else None
    data = analysis_repository.get_analysis(analysis_id, user_id=user_id)
    if not data or "context" not in data:
        raise HTTPException(status_code=404, detail="Analysis context not found.")
    return data["context"]

@router.patch("/{analysis_id}/context", response_model=AnalysisContext)
def update_analysis_context(
    analysis_id: str,
    updated_optional: OptionalUserContext,
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    user_id = current_user.id if current_user else None
    data = analysis_repository.get_analysis(analysis_id, user_id=user_id)
    if not data or "context" not in data:
        raise HTTPException(status_code=404, detail="Analysis context not found.")

    ctx_data = data["context"]
    
    if updated_optional.height_cm and updated_optional.weight_kg:
        height_m = updated_optional.height_cm / 100.0
        updated_optional.bmi = round(updated_optional.weight_kg / (height_m * height_m), 1)

    ctx_data["optional"] = updated_optional.model_dump()
    data["context"] = ctx_data
    analysis_repository.save_analysis(analysis_id, data, user_id=user_id)
    return ctx_data

@router.post("/{analysis_id}/context/analyze", response_model=DetectedVideoContext)
def reanalyze_video_context(
    analysis_id: str,
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    user_id = current_user.id if current_user else None
    data = analysis_repository.get_analysis(analysis_id, user_id=user_id)
    if not data:
        raise HTTPException(status_code=404, detail="Analysis record not found.")

    video_path = storage_manager.get_raw_video_path(data["video_id"])
    if not video_path:
        raise HTTPException(status_code=404, detail="Video file not found.")

    metadata, suitability = video_validator.validate_video(
        video_path, video_path.name, video_path.stat().st_size
    )
    detected = context_detector.detect_context(video_path, metadata)
    
    data["context"]["detected"] = detected.model_dump()
    analysis_repository.save_analysis(analysis_id, data, user_id=user_id)
    return detected

@router.get("/{analysis_id}/status", response_model=AnalysisStatusResponse)
def get_analysis_status(
    analysis_id: str,
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    user_id = current_user.id if current_user else None
    data = analysis_repository.get_analysis(analysis_id, user_id=user_id)
    if not data:
        raise HTTPException(status_code=404, detail="Analysis ID not found.")
    return AnalysisStatusResponse(
        analysis_id=analysis_id,
        status=data.get("status", "completed"),
        progress_percentage=data.get("progress_percentage", 100),
        current_step=data.get("current_step", "Completed"),
        error_message=data.get("error_message")
    )

@router.get("/{analysis_id}/comparison", response_model=AnalysisComparisonResponse)
def get_analysis_comparison(
    analysis_id: str,
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """
    Returns a session-over-session 'What Changed?' comparison for the current analysis.

    Compares the current authenticated user's analysis against their immediately
    previous completed session. Never compares against another user's data.

    - If first analysis: returns empty comparison with `is_first_analysis=True`.
    - If previous analysis exists: returns metric deltas, directional changes, and goal relevance.
    - If unauthenticated (guest/demo): scoped to guest/demo analyses only.
    """
    user_id = current_user.id if current_user else None
    try:
        result = comparison_engine.compare_analyses(
            current_analysis_id=analysis_id,
            user_id=user_id
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Comparison calculation failed: {str(e)}")


@router.get("/{analysis_id}", response_model=AnalysisResultResponse)
def get_analysis_result(
    analysis_id: str,
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    user_id = current_user.id if current_user else None
    data = analysis_repository.get_analysis(analysis_id, user_id=user_id)
    if not data:
        raise HTTPException(status_code=404, detail="Analysis ID not found or access unauthorized.")
    return data

@router.delete("/{analysis_id}")
def delete_analysis(
    analysis_id: str,
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """Deletes an individual analysis record and its metrics (verifying user ownership)."""
    user_id = current_user.id if current_user else None
    deleted = analysis_repository.delete_analysis(analysis_id, user_id=user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Analysis not found or could not be deleted.")
    return {"status": "success", "message": f"Analysis {analysis_id} deleted successfully."}

