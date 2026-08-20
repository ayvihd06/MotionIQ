import cv2
from pathlib import Path
from typing import Generator, Tuple, Dict, Any, Optional

class VideoLoader:
    """Efficient OpenCV-based video streaming loader."""

    @staticmethod
    def get_metadata(video_path: Path) -> Dict[str, Any]:
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            raise ValueError(f"Could not open video file: {video_path}")

        fps = float(cap.get(cv2.CAP_PROP_FPS)) or 30.0
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 0
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) or 0
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) or 0
        duration_sec = (frame_count / fps) if fps > 0 else 0.0

        cap.release()
        return {
            "fps": fps,
            "frame_count": frame_count,
            "width": width,
            "height": height,
            "duration_sec": duration_sec
        }

    @staticmethod
    def stream_frames(video_path: Path, max_frames: Optional[int] = None) -> Generator[Tuple[int, float, Any], None, None]:
        """
        Yields (frame_idx, timestamp_sec, bgr_frame) one-by-one
        without loading the entire video into memory.
        """
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            raise ValueError(f"Could not open video file: {video_path}")

        fps = float(cap.get(cv2.CAP_PROP_FPS)) or 30.0
        frame_idx = 0

        while True:
            if max_frames and frame_idx >= max_frames:
                break

            ret, frame = cap.read()
            if not ret or frame is None:
                break

            timestamp_sec = frame_idx / fps
            yield frame_idx, timestamp_sec, frame
            frame_idx += 1

        cap.release()

video_loader = VideoLoader()
