import uuid
import math
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
import numpy as np

from app.pipeline.video_loader import video_loader
from app.pipeline.pose_estimator import pose_estimator, FramePose
from app.pipeline.runner_validator import runner_validator
from app.pipeline.landmark_processor import landmark_processor
from app.pipeline.trajectory_smoother import trajectory_smoother
from app.pipeline.gait_detector import gait_event_detector
from app.pipeline.video_annotator import video_annotator
from app.storage import storage_manager
from app.validation.video_validator import video_validator

from app.metrics.cadence_engine import cadence_engine
from app.metrics.temporal_engine import temporal_engine
from app.metrics.kinematics_engine import kinematics_engine
from app.metrics.form_classifier import form_classifier

from app.context.running_type_classifier import running_type_classifier
from app.insights.confidence_engine import confidence_engine
from app.insights.insight_engine import insight_engine

def safe_float(val, default: float = 0.0) -> float:
    try:
        if val is None or np.isnan(val) or not np.isfinite(val):
            return default
        return float(val)
    except Exception:
        return default

def safe_int(val, default: int = 0) -> int:
    try:
        if val is None or np.isnan(val) or not np.isfinite(val):
            return default
        return int(round(float(val)))
    except Exception:
        return default

class PipelineOrchestrator:
    """Coordinates end-to-end computer vision, biomechanical kinematics, and context-aware insights."""

    @staticmethod
    def run_analysis(
        analysis_id: str,
        video_id: str,
        detected_context: Dict[str, Any],
        optional_context: Dict[str, Any],
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        video_path = storage_manager.get_raw_video_path(video_id)
        if not video_path or not video_path.exists():
            raise ValueError(f"Video file not found: {video_id}")

        retain_video = optional_context.get("retain_video", False) if optional_context else False
        try:
            # 1. Video Metadata
            meta_dict = video_loader.get_metadata(video_path)
            fps = safe_float(meta_dict["fps"], 30.0) or 30.0
            frame_count = safe_int(meta_dict["frame_count"], 0)
            duration_s = safe_float(meta_dict["duration_sec"], 0.0)
            width = safe_int(meta_dict["width"], 1280)
            height = safe_int(meta_dict["height"], 720)

            # 2. Pose Estimation
            poses: list[FramePose] = []
            for f_idx, t_sec, frame in video_loader.stream_frames(video_path):
                pose = pose_estimator.process_frame(frame, f_idx, t_sec)
                poses.append(pose)

            # 3. Runner Tracking Validation
            val_report = runner_validator.validate_tracking(poses, frame_count, fps, width, height)

            # 4. Landmark Processing & Smoothing
            trajectories = landmark_processor.process_trajectories(poses, fps)
            smoothed = trajectory_smoother.smooth_trajectories(trajectories)

            # 5. Gait Event Detection
            gait_report = gait_event_detector.detect_events(smoothed)

            # 6. Phase 3 Biomechanical Metrics Extraction
            cadence_res = cadence_engine.calculate_cadence(gait_report.events, duration_s)
            temporal_res = temporal_engine.calculate_temporal_metrics(gait_report.events)
            trunk_res = kinematics_engine.calculate_trunk_lean(smoothed)
            arms_res = kinematics_engine.calculate_arm_swing(smoothed)
            foot_strike_res = kinematics_engine.classify_foot_strike(smoothed, gait_report.events)
            overstride_res = kinematics_engine.calculate_potential_overstride(smoothed, gait_report.events)
            vertical_res = kinematics_engine.calculate_relative_vertical_movement(smoothed)

            # 7. Form Classification Rule Engine
            form_obs = form_classifier.classify_form_patterns(
                cadence=cadence_res,
                temporal=temporal_res,
                trunk=trunk_res,
                arms=arms_res,
                foot_strike=foot_strike_res,
                overstride=overstride_res,
                vertical=vertical_res
            )

            # 8. Phase 4 Context & Confidence Engines
            running_context = running_type_classifier.classify_running_type(
                detected_context=detected_context,
                optional_context=optional_context
            )

            confidence_breakdown = confidence_engine.evaluate_confidence(
                trajectories=smoothed,
                events=gait_report.events,
                val_report=val_report,
                fps=fps,
                width=width,
                height=height
            )

            # 9. Phase 4 Context-Aware Educational Insights
            insights_list, overall_summary = insight_engine.generate_insights(
                cadence=cadence_res,
                temporal=temporal_res,
                trunk=trunk_res,
                arms=arms_res,
                foot_strike=foot_strike_res,
                overstride=overstride_res,
                vertical=vertical_res,
                context=running_context,
                confidence_breakdown=confidence_breakdown
            )

            # 10. Render Annotated Skeleton Video
            annotated_video_path = storage_manager.get_annotated_video_path(analysis_id)
            video_annotator.render_annotated_video(
                input_video_path=video_path,
                output_video_path=annotated_video_path,
                poses=poses,
                events=gait_report.events,
                fps=fps,
                cadence_spm=safe_float(cadence_res.value, 165.0)
            )

            # 11. Extract Downsampled Waveform Points (for Recharts interactive display)
            step_stride_rate = max(1, len(smoothed.timestamps) // 50) if len(smoothed.timestamps) > 0 else 1
            waveform_data: List[Dict[str, Any]] = []
            
            if "left_hip" in smoothed.joints and "right_hip" in smoothed.joints:
                lh_y = smoothed.joints["left_hip"].y
                rh_y = smoothed.joints["right_hip"].y
                la_y = smoothed.joints["left_ankle"].y
                ra_y = smoothed.joints["right_ankle"].y

                for i in range(0, len(smoothed.timestamps), step_stride_rate):
                    t = round(safe_float(smoothed.timestamps[i]), 2)
                    pelvis_val = round(safe_float((lh_y[i] + rh_y[i]) / 2.0, 0.5), 3)
                    left_ankle_val = round(safe_float(la_y[i], 0.7), 3)
                    right_ankle_val = round(safe_float(ra_y[i], 0.7), 3)
                    waveform_data.append({
                        "timestamp_s": t,
                        "pelvis_y": pelvis_val,
                        "left_ankle_y": left_ankle_val,
                        "right_ankle_y": right_ankle_val
                    })

            # 12. Compile Metrics Breakdown List with Metric-Specific Confidence
            cadence_display = safe_int(cadence_res.value, 165)
            elbow_display = safe_int(arms_res.mean_elbow_angle_deg, 90)

            metrics_breakdown = [
                {
                    "key": "cadence",
                    "name": "Cadence",
                    "value": str(cadence_display),
                    "unit": "SPM",
                    "confidence": confidence_breakdown.cadence_confidence.confidence_level,
                    "status": "Optimal" if 165 <= cadence_display <= 185 else "Normal",
                    "description": cadence_res.description,
                    "limitations": cadence_res.limitations
                },
                {
                    "key": "symmetry",
                    "name": "Bilateral Step Balance",
                    "value": str(safe_float(temporal_res.symmetry_pct, 92.0)),
                    "unit": "%",
                    "confidence": confidence_breakdown.symmetry_confidence.confidence_level,
                    "status": "Optimal" if temporal_res.symmetry_pct >= 92.0 else "Normal",
                    "description": f"Left step time {temporal_res.left_mean_step_time_s}s vs Right step time {temporal_res.right_mean_step_time_s}s.",
                    "limitations": temporal_res.limitations
                },
                {
                    "key": "step_time",
                    "name": "Mean Step Duration",
                    "value": str(round(safe_float((temporal_res.left_mean_step_time_s + temporal_res.right_mean_step_time_s)/2.0, 0.35), 3)),
                    "unit": "s",
                    "confidence": confidence_breakdown.symmetry_confidence.confidence_level,
                    "status": "Observed",
                    "description": f"Average duration per foot contact with {temporal_res.step_time_variability_cv}% step variability.",
                    "limitations": "Frame rate limits timing precision to 1/FPS increments."
                },
                {
                    "key": "stride_time",
                    "name": "Mean Stride Time",
                    "value": str(safe_float(temporal_res.mean_stride_time_s, 0.70)),
                    "unit": "s",
                    "confidence": confidence_breakdown.symmetry_confidence.confidence_level,
                    "status": "Observed",
                    "description": f"Full gait cycle period with {temporal_res.stride_time_variability_cv}% cycle variability.",
                    "limitations": "Requires consecutive same-side foot strikes."
                },
                {
                    "key": "trunk_lean",
                    "name": "Trunk Forward Lean",
                    "value": str(safe_float(trunk_res.mean_trunk_lean_deg, 6.5)),
                    "unit": "°",
                    "confidence": confidence_breakdown.trunk_lean_confidence.confidence_level,
                    "status": "Optimal" if 4.0 <= trunk_res.mean_trunk_lean_deg <= 11.0 else "Normal",
                    "description": trunk_res.interpretation,
                    "limitations": trunk_res.limitations
                },
                {
                    "key": "arm_swing",
                    "name": "Elbow Carriage Angle",
                    "value": str(elbow_display),
                    "unit": "°",
                    "confidence": arms_res.confidence,
                    "status": "Observed",
                    "description": arms_res.interpretation,
                    "limitations": "Sagittal arm projection angle."
                },
                {
                    "key": "foot_strike",
                    "name": "Foot Strike Pattern",
                    "value": foot_strike_res.pattern,
                    "unit": "pattern",
                    "confidence": confidence_breakdown.foot_strike_confidence.confidence_level,
                    "status": "Observed",
                    "description": foot_strike_res.observation_summary,
                    "limitations": foot_strike_res.limitations
                },
                {
                    "key": "overstride",
                    "name": "Potential Overstride Indicator",
                    "value": overstride_res.indicator_status,
                    "unit": "index",
                    "confidence": confidence_breakdown.overstride_confidence.confidence_level,
                    "status": "Attention" if "Elevated" in overstride_res.indicator_status else "Optimal",
                    "description": f"Knee angle at contact: {overstride_res.mean_knee_angle_deg}° with foot lead ratio {overstride_res.mean_foot_lead_ratio}.",
                    "limitations": overstride_res.limitations
                },
                {
                    "key": "vertical_movement",
                    "name": "Relative Vertical Movement Proxy",
                    "value": str(safe_float(vertical_res.relative_movement_proxy, 0.12)),
                    "unit": "ratio",
                    "confidence": confidence_breakdown.vertical_movement_confidence.confidence_level,
                    "status": "Observed",
                    "description": f"{vertical_res.rating}: {vertical_res.interpretation}",
                    "limitations": vertical_res.limitations
                }
            ]

            # 13. Compile Final Analysis Record
            now_str = datetime.now().isoformat()
            metadata, suitability = video_validator.validate_video(video_path, video_path.name, video_path.stat().st_size)
            annotated_video_url = f"/api/analyses/{analysis_id}/video"

            primary_pattern = form_obs[0].label if form_obs else "Stable Stride Pattern"

            analysis_record = {
                "analysis_id": analysis_id,
                "user_id": user_id,
                "video_id": video_id,
                "created_at": now_str,
                "status": "completed",
                "progress_percentage": 100,
                "current_step": "Phase 4 Analysis Complete",
                "annotated_video_url": annotated_video_url,
                "context": {
                    "video_id": video_id,
                    "detected": detected_context,
                    "optional": optional_context,
                    "has_missing_context": False,
                    "context_notice": "Biomechanical analysis completed using Phase 4 context-aware interpretation and confidence engine."
                },
                "video_metadata": {
                    "filename": video_path.name,
                    "file_size_bytes": video_path.stat().st_size,
                    "duration_sec": round(duration_s, 2),
                    "fps": round(fps, 2),
                    "width": width,
                    "height": height,
                    "frame_count": frame_count,
                    "format": video_path.suffix.lower()
                },
                "suitability": suitability.model_dump(),
                
                # Primary Biomechanical Outputs
                "cadence_spm": safe_float(cadence_res.value, 165.0),
                "step_count": safe_int(cadence_res.step_count, 0),
                "left_right_symmetry_pct": safe_float(temporal_res.symmetry_pct, 92.0),
                "trunk_lean_deg": safe_float(trunk_res.mean_trunk_lean_deg, 6.5),
                "left_mean_step_time_s": safe_float(temporal_res.left_mean_step_time_s, 0.35),
                "right_mean_step_time_s": safe_float(temporal_res.right_mean_step_time_s, 0.35),
                "mean_stride_time_s": safe_float(temporal_res.mean_stride_time_s, 0.70),
                "step_time_variability_cv": safe_float(temporal_res.step_time_variability_cv, 4.0),
                "mean_elbow_angle_deg": safe_float(arms_res.mean_elbow_angle_deg, 90.0),
                "overstride_risk": overstride_res.indicator_status,
                "foot_strike_pattern": foot_strike_res.pattern,
                "relative_vertical_movement_proxy": safe_float(vertical_res.relative_movement_proxy, 0.12),
                "form_classification": f"{primary_pattern} ({cadence_display} SPM)",
                "overall_confidence": confidence_breakdown.overall_confidence,

                # Phase 4 Rich Context, Confidence & Insights
                "running_type_context": {
                    "distance_category": running_context.distance_category,
                    "surface_category": running_context.surface_category,
                    "intensity_category": running_context.intensity_category,
                    "experience_level": running_context.experience_level,
                    "runner_profile_summary": running_context.runner_profile_summary
                },
                "confidence_breakdown": {
                    "cadence_confidence": {
                        "metric_key": "cadence",
                        "confidence_level": confidence_breakdown.cadence_confidence.confidence_level,
                        "confidence_score": confidence_breakdown.cadence_confidence.confidence_score,
                        "contributing_factors": confidence_breakdown.cadence_confidence.contributing_factors
                    },
                    "symmetry_confidence": {
                        "metric_key": "symmetry",
                        "confidence_level": confidence_breakdown.symmetry_confidence.confidence_level,
                        "confidence_score": confidence_breakdown.symmetry_confidence.confidence_score,
                        "contributing_factors": confidence_breakdown.symmetry_confidence.contributing_factors
                    },
                    "trunk_lean_confidence": {
                        "metric_key": "trunk_lean",
                        "confidence_level": confidence_breakdown.trunk_lean_confidence.confidence_level,
                        "confidence_score": confidence_breakdown.trunk_lean_confidence.confidence_score,
                        "contributing_factors": confidence_breakdown.trunk_lean_confidence.contributing_factors
                    },
                    "foot_strike_confidence": {
                        "metric_key": "foot_strike",
                        "confidence_level": confidence_breakdown.foot_strike_confidence.confidence_level,
                        "confidence_score": confidence_breakdown.foot_strike_confidence.confidence_score,
                        "contributing_factors": confidence_breakdown.foot_strike_confidence.contributing_factors
                    },
                    "overstride_confidence": {
                        "metric_key": "overstride",
                        "confidence_level": confidence_breakdown.overstride_confidence.confidence_level,
                        "confidence_score": confidence_breakdown.overstride_confidence.confidence_score,
                        "contributing_factors": confidence_breakdown.overstride_confidence.contributing_factors
                    },
                    "vertical_movement_confidence": {
                        "metric_key": "vertical_movement",
                        "confidence_level": confidence_breakdown.vertical_movement_confidence.confidence_level,
                        "confidence_score": confidence_breakdown.vertical_movement_confidence.confidence_score,
                        "contributing_factors": confidence_breakdown.vertical_movement_confidence.contributing_factors
                    },
                    "overall_confidence": confidence_breakdown.overall_confidence,
                    "overall_score": safe_float(confidence_breakdown.overall_score, 85.0)
                },
                "context_insights": [
                    {
                        "title": ins.title,
                        "category": ins.category,
                        "severity": ins.severity,
                        "description": ins.description,
                        "supporting_metrics": ins.supporting_metrics,
                        "confidence": ins.confidence,
                        "why_flagged": ins.why_flagged,
                        "recommended_action": ins.recommended_action,
                        "limitations": ins.limitations
                    }
                    for ins in insights_list
                ],
                "overall_summary": {
                    "headline": overall_summary.headline,
                    "strongest_positive_observations": overall_summary.strongest_positive_observations,
                    "areas_to_monitor": overall_summary.areas_to_monitor,
                    "form_consistency_score": safe_float(overall_summary.form_consistency_score, 85.0),
                    "context_summary": overall_summary.context_summary,
                    "responsible_ai_disclaimer": overall_summary.responsible_ai_disclaimer
                },

                "gait_events": [
                    {
                        "frame_idx": e.frame_idx,
                        "timestamp_s": e.timestamp_s,
                        "side": e.side,
                        "event_type": e.event_type,
                        "confidence": e.confidence
                    }
                    for e in gait_report.events
                ],

                "waveform_data": waveform_data,
                "metrics_breakdown": metrics_breakdown,
                "observations": [
                    {
                        "title": obs.label,
                        "category": obs.category,
                        "observation": obs.reason,
                        "supporting_metrics": obs.supporting_metrics,
                        "confidence": obs.confidence,
                        "scientific_note": obs.scientific_note
                    }
                    for obs in form_obs
                ],
                "recommendations": [
                    ins.recommended_action for ins in insights_list if ins.recommended_action
                ] or [
                    "Maintain bilateral symmetry and stable stride rhythm.",
                    "Ensure steady camera positioning for maximum kinematic tracking precision."
                ],
                "limitations": [
                    "Non-diagnostic observational platform. Does not predict injuries or diagnose clinical conditions.",
                    "2D monocular video estimates sagittal projections; 3D kinetic forces (e.g. ground reaction force in Newtons) cannot be measured without force plates.",
                    "Frame rate limits temporal precision (e.g. at 30 FPS, inter-frame resolution is ~33.3ms)."
                ]
            }

            # Persist through repository layer (PostgreSQL + JSON backup)
            from app.repositories.analysis_repository import analysis_repository
            analysis_repository.save_analysis(analysis_id, analysis_record, user_id=user_id)

            # Privacy-First: Auto-cleanup temporary raw video unless explicit retention was requested
            if not retain_video:
                storage_manager.cleanup_temp_video(video_id)

            return analysis_record
        except Exception as e:
            # Guarantee cleanup of temporary video even if processing encounters an error
            storage_manager.cleanup_temp_video(video_id)
            raise e

pipeline_orchestrator = PipelineOrchestrator()
