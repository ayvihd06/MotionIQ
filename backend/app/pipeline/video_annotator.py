import cv2
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional
from app.pipeline.pose_estimator import FramePose, SKELETON_CONNECTIONS
from app.pipeline.gait_detector import GaitContactEvent

def is_valid_coord(val) -> bool:
    try:
        return val is not None and not np.isnan(val) and np.isfinite(val)
    except Exception:
        return False

def safe_int(val, default: int = 0) -> int:
    try:
        if val is None or np.isnan(val) or not np.isfinite(val):
            return default
        return int(round(float(val)))
    except Exception:
        return default

class VideoAnnotator:
    """Renders cybernetic biomechanics skeleton and HUD overlay onto video frames."""

    # Colors in BGR
    COLOR_CYAN = (255, 230, 0)       # Left side / primary
    COLOR_MAGENTA = (200, 50, 255)    # Right side
    COLOR_WHITE = (240, 240, 240)     # Torso / midline
    COLOR_EMERALD = (80, 240, 120)    # Active foot strike
    COLOR_BG_DARK = (20, 20, 25)

    @staticmethod
    def render_annotated_video(
        input_video_path: Path,
        output_video_path: Path,
        poses: List[FramePose],
        events: List[GaitContactEvent],
        fps: float,
        cadence_spm: float
    ) -> Path:
        output_video_path.parent.mkdir(parents=True, exist_ok=True)
        
        cap = cv2.VideoCapture(str(input_video_path))
        if not cap.isOpened():
            raise ValueError(f"Could not open input video for annotation: {input_video_path}")

        width = safe_int(cap.get(cv2.CAP_PROP_FRAME_WIDTH), 1280) or 1280
        height = safe_int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT), 720) or 720
        total_frames = safe_int(cap.get(cv2.CAP_PROP_FRAME_COUNT), len(poses)) or len(poses)

        # Build fast lookup for strike frames
        strike_frames = {e.frame_idx: e for e in events}
        poses_by_frame = {p.frame_idx: p for p in poses}

        # Use mp4v fourcc
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        out = cv2.VideoWriter(str(output_video_path), fourcc, fps, (width, height))

        frame_idx = 0
        current_step_count = 0

        while True:
            ret, frame = cap.read()
            if not ret or frame is None:
                break

            # Update step count
            if frame_idx in strike_frames:
                current_step_count += 1

            pose = poses_by_frame.get(frame_idx)
            is_strike = frame_idx in strike_frames
            strike_event = strike_frames.get(frame_idx)

            # Draw skeleton and HUD
            annotated_frame = VideoAnnotator._draw_frame(
                frame=frame,
                pose=pose,
                is_strike=is_strike,
                strike_event=strike_event,
                frame_idx=frame_idx,
                total_frames=total_frames,
                step_count=current_step_count,
                cadence_spm=cadence_spm,
                width=width,
                height=height
            )

            out.write(annotated_frame)
            frame_idx += 1

        cap.release()
        out.release()

        # --- CRITICAL: Re-encode to H.264 for browser compatibility ---
        # OpenCV's mp4v fourcc writes MPEG-4 Part 2 (FMP4) which browsers CANNOT play.
        # Browsers require H.264 (AVC) in an MP4 container.
        # Use the bundled ffmpeg from imageio-ffmpeg to transcode.
        try:
            import subprocess
            import imageio_ffmpeg
            ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()

            temp_path = output_video_path.with_suffix(".tmp.mp4")
            # Rename the mp4v file to temp
            import shutil
            shutil.move(str(output_video_path), str(temp_path))

            # Re-encode to H.264 (libx264) with browser-compatible settings
            cmd = [
                ffmpeg_exe,
                "-y",                    # Overwrite output
                "-i", str(temp_path),    # Input: MPEG-4 Part 2 file
                "-c:v", "libx264",       # H.264 codec
                "-preset", "fast",       # Speed/quality tradeoff
                "-crf", "23",            # Constant rate factor (quality)
                "-pix_fmt", "yuv420p",   # Browser-compatible pixel format
                "-movflags", "+faststart", # Progressive download (moov atom at start)
                "-an",                   # No audio track
                str(output_video_path)   # Output: browser-compatible H.264 MP4
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                timeout=120  # 2 minute timeout for re-encoding
            )

            if result.returncode == 0:
                # Success — remove the temp MPEG-4 Part 2 file
                temp_path.unlink(missing_ok=True)
            else:
                # ffmpeg failed — fall back to the original mp4v file
                # (will be unplayable in browser, but at least the file exists)
                import logging
                logging.warning(f"H.264 re-encoding failed (rc={result.returncode}): {result.stderr.decode(errors='replace')[:500]}")
                if temp_path.exists():
                    shutil.move(str(temp_path), str(output_video_path))

        except Exception as e:
            import logging
            logging.warning(f"H.264 re-encoding skipped: {e}")
            # If temp exists but output doesn't, restore it
            temp_path = output_video_path.with_suffix(".tmp.mp4")
            if temp_path.exists() and not output_video_path.exists():
                import shutil
                shutil.move(str(temp_path), str(output_video_path))

        return output_video_path

    @staticmethod
    def _draw_frame(
        frame: np.ndarray,
        pose: Optional[FramePose],
        is_strike: bool,
        strike_event: Optional[GaitContactEvent],
        frame_idx: int,
        total_frames: int,
        step_count: int,
        cadence_spm: float,
        width: int,
        height: int
    ) -> np.ndarray:
        canvas = frame.copy()

        if pose and pose.detected:
            lms = pose.landmarks

            # 1. Draw Skeleton Connections
            for start_name, end_name in SKELETON_CONNECTIONS:
                if start_name in lms and end_name in lms:
                    p1 = lms[start_name]
                    p2 = lms[end_name]

                    if (
                        p1.visibility > 0.35 and p2.visibility > 0.35
                        and is_valid_coord(p1.x) and is_valid_coord(p1.y)
                        and is_valid_coord(p2.x) and is_valid_coord(p2.y)
                    ):
                        pt1 = (safe_int(p1.x * width), safe_int(p1.y * height))
                        pt2 = (safe_int(p2.x * width), safe_int(p2.y * height))

                        # Color based on side
                        if "left" in start_name and "left" in end_name:
                            color = VideoAnnotator.COLOR_CYAN
                        elif "right" in start_name and "right" in end_name:
                            color = VideoAnnotator.COLOR_MAGENTA
                        else:
                            color = VideoAnnotator.COLOR_WHITE

                        cv2.line(canvas, pt1, pt2, color, 3, cv2.LINE_AA)

            # 2. Draw Landmark Joints
            for name, lm in lms.items():
                if lm.visibility > 0.35 and is_valid_coord(lm.x) and is_valid_coord(lm.y):
                    pt = (safe_int(lm.x * width), safe_int(lm.y * height))
                    color = VideoAnnotator.COLOR_CYAN if "left" in name else VideoAnnotator.COLOR_MAGENTA
                    
                    if "ankle" in name or "foot" in name or "heel" in name:
                        cv2.circle(canvas, pt, 6, (0, 255, 255), -1, cv2.LINE_AA)
                        cv2.circle(canvas, pt, 8, color, 2, cv2.LINE_AA)
                    else:
                        cv2.circle(canvas, pt, 4, color, -1, cv2.LINE_AA)

            # 3. Foot Strike Contact Pulse Effect
            if is_strike and strike_event:
                side_name = "left_ankle" if strike_event.side == "left" else "right_ankle"
                if side_name in lms and is_valid_coord(lms[side_name].x) and is_valid_coord(lms[side_name].y):
                    s_pt = (safe_int(lms[side_name].x * width), safe_int(lms[side_name].y * height))
                    # Expanding shockwave rings
                    cv2.circle(canvas, s_pt, 24, VideoAnnotator.COLOR_EMERALD, 3, cv2.LINE_AA)
                    cv2.circle(canvas, s_pt, 36, (120, 255, 180), 2, cv2.LINE_AA)
                    cv2.putText(
                        canvas,
                        f"INITIAL CONTACT ({strike_event.side.upper()})",
                        (s_pt[0] - 80, s_pt[1] - 30),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.55,
                        VideoAnnotator.COLOR_EMERALD,
                        2,
                        cv2.LINE_AA
                    )

        # 4. Professional HUD Telemetry Overlay (Top-Left)
        hud_w, hud_h = 280, 80
        hud_bg = canvas[15:15+hud_h, 15:15+hud_w]
        if hud_bg.shape[0] == hud_h and hud_bg.shape[1] == hud_w:
            dark_overlay = np.full_like(hud_bg, 20)
            cv2.addWeighted(hud_bg, 0.3, dark_overlay, 0.7, 0, hud_bg)
            canvas[15:15+hud_h, 15:15+hud_w] = hud_bg

        display_cadence = safe_int(cadence_spm, 165)
        cv2.rectangle(canvas, (15, 15), (15 + hud_w, 15 + hud_h), (80, 80, 90), 1, cv2.LINE_AA)
        cv2.putText(canvas, "MOTIONIQ BIOMECHANICS HUD", (25, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 230, 255), 1, cv2.LINE_AA)
        cv2.putText(canvas, f"STEPS: {step_count}", (25, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.60, (255, 255, 255), 2, cv2.LINE_AA)
        cv2.putText(canvas, f"CADENCE: {display_cadence} SPM", (140, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.60, (100, 255, 150), 2, cv2.LINE_AA)
        cv2.putText(canvas, f"FRAME: {frame_idx}/{total_frames}", (25, 82), cv2.FONT_HERSHEY_SIMPLEX, 0.40, (180, 180, 180), 1, cv2.LINE_AA)

        return canvas

video_annotator = VideoAnnotator()
