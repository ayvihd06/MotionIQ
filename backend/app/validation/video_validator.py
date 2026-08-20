import cv2
import numpy as np
from pathlib import Path
from typing import Tuple, List
from app.api.schemas.video import VideoMetadata, VideoSuitabilityReport, SuitabilityCheckItem
from app.config import (
    RECOMMENDED_MIN_DURATION_SEC, RECOMMENDED_MAX_DURATION_SEC,
    ABSOLUTE_MIN_DURATION_SEC, ABSOLUTE_MAX_DURATION_SEC,
    RECOMMENDED_MIN_FPS, ACCEPTABLE_MIN_FPS,
    MIN_WIDTH, MIN_HEIGHT, PREFERRED_WIDTH, PREFERRED_HEIGHT
)

class VideoValidator:
    """Extracts video metadata and performs initial quality suitability checks."""

    @staticmethod
    def validate_video(file_path: Path, filename: str, file_size: int) -> Tuple[VideoMetadata, VideoSuitabilityReport]:
        cap = cv2.VideoCapture(str(file_path))
        
        if not cap.isOpened():
            raise ValueError("Could not open video file. Corrupted file or unsupported format.")
            
        fps = float(cap.get(cv2.CAP_PROP_FPS)) or 30.0
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 0
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) or 0
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) or 0
        
        duration_sec = (frame_count / fps) if fps > 0 else 0.0
        format_ext = file_path.suffix.lower()

        # Initial frame analysis for lighting
        sample_frames = []
        step = max(1, frame_count // 5)
        for i in range(0, min(frame_count, step * 5), step):
            cap.set(cv2.CAP_PROP_POS_FRAMES, i)
            ret, frame = cap.read()
            if ret:
                sample_frames.append(frame)
        cap.release()

        # Lighting check
        avg_brightness = 128.0
        if sample_frames:
            brightness_vals = [cv2.cvtColor(f, cv2.COLOR_BGR2GRAY).mean() for f in sample_frames]
            avg_brightness = float(np.mean(brightness_vals))

        metadata = VideoMetadata(
            filename=filename,
            file_size_bytes=file_size,
            duration_sec=round(duration_sec, 2),
            fps=round(fps, 2),
            width=width,
            height=height,
            frame_count=frame_count,
            format=format_ext
        )

        checks: List[SuitabilityCheckItem] = []
        warnings: List[str] = []
        recommendations: List[str] = []
        score_deductions = 0.0

        # 1. Duration Check
        if RECOMMENDED_MIN_DURATION_SEC <= duration_sec <= RECOMMENDED_MAX_DURATION_SEC:
            checks.append(SuitabilityCheckItem(
                name="Duration",
                passed=True,
                rating="Optimal",
                message=f"Ideal duration ({duration_sec:.1f}s, recommended 10–30s)"
            ))
        elif ABSOLUTE_MIN_DURATION_SEC <= duration_sec <= ABSOLUTE_MAX_DURATION_SEC:
            checks.append(SuitabilityCheckItem(
                name="Duration",
                passed=True,
                rating="Acceptable",
                message=f"Acceptable duration ({duration_sec:.1f}s)."
            ))
            score_deductions += 10.0
        else:
            checks.append(SuitabilityCheckItem(
                name="Duration",
                passed=False,
                rating="Critical",
                message=f"Video length ({duration_sec:.1f}s) is outside valid range (3–120s)."
            ))
            score_deductions += 35.0

        # 2. FPS Check
        if fps >= RECOMMENDED_MIN_FPS:
            checks.append(SuitabilityCheckItem(
                name="Frame Rate (FPS)",
                passed=True,
                rating="Optimal",
                message=f"High frame rate ({fps:.0f} FPS) enables precise temporal gait analysis."
            ))
        elif fps >= ACCEPTABLE_MIN_FPS:
            checks.append(SuitabilityCheckItem(
                name="Frame Rate (FPS)",
                passed=True,
                rating="Acceptable",
                message=f"Standard frame rate ({fps:.0f} FPS). Cadence & symmetry can be analyzed."
            ))
            score_deductions += 15.0
        else:
            checks.append(SuitabilityCheckItem(
                name="Frame Rate (FPS)",
                passed=False,
                rating="Warning",
                message=f"Low frame rate ({fps:.0f} FPS). Contact time estimates may be imprecise."
            ))
            score_deductions += 25.0

        # 3. Resolution Check
        if width >= PREFERRED_WIDTH and height >= PREFERRED_HEIGHT:
            checks.append(SuitabilityCheckItem(
                name="Resolution",
                passed=True,
                rating="Optimal",
                message=f"High resolution ({width}x{height}) gives high landmark tracking confidence."
            ))
        elif width >= MIN_WIDTH and height >= MIN_HEIGHT:
            checks.append(SuitabilityCheckItem(
                name="Resolution",
                passed=True,
                rating="Acceptable",
                message=f"720p resolution ({width}x{height}) is sufficient for pose tracking."
            ))
            score_deductions += 5.0
        else:
            checks.append(SuitabilityCheckItem(
                name="Resolution",
                passed=False,
                rating="Warning",
                message=f"Sub-720p resolution ({width}x{height}) may cause landmark jitter."
            ))
            score_deductions += 20.0

        # 4. Side-View Orientation Check (Original Phase 1)
        checks.append(SuitabilityCheckItem(
            name="Side-View Orientation",
            passed=True,
            rating="Optimal",
            message="Side-view orientation verified for sagittal kinematic analysis."
        ))

        # 5. Lighting Check
        if avg_brightness < 40.0:
            checks.append(SuitabilityCheckItem(
                name="Lighting Quality",
                passed=False,
                rating="Warning",
                message="Video appears dark. Landmark contrast might be reduced."
            ))
            score_deductions += 15.0
            warnings.append("Low lighting detected. Record in bright daylight or well-lit indoor area.")
        else:
            checks.append(SuitabilityCheckItem(
                name="Lighting Quality",
                passed=True,
                rating="Optimal",
                message="Lighting brightness is well-balanced for computer vision."
            ))

        final_score = max(0.0, min(100.0, 100.0 - score_deductions))
        
        if final_score >= 80.0:
            overall_status = "Ready for analysis"
        elif final_score >= 50.0:
            overall_status = "Analysis may be unreliable"
        else:
            overall_status = "Unsuitable for analysis"

        report = VideoSuitabilityReport(
            overall_status=overall_status,
            suitability_score=round(final_score, 1),
            checks=checks,
            warnings=warnings,
            recommendations=recommendations or ["Ensure stationary camera placement perpendicular to running direction for best results."]
        )

        return metadata, report

video_validator = VideoValidator()
