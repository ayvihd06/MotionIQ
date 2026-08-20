import json
import uuid
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from app.config import (
    RAW_VIDEOS_DIR, TEMP_VIDEOS_DIR, ANNOTATED_VIDEOS_DIR, REPORTS_DIR, ANALYSES_DIR
)

logger = logging.getLogger(__name__)

class StorageManager:
    """Storage abstraction for local filesystem handling with privacy-first temporary video management."""
    
    raw_videos_dir = RAW_VIDEOS_DIR
    temp_videos_dir = TEMP_VIDEOS_DIR
    annotated_videos_dir = ANNOTATED_VIDEOS_DIR
    reports_dir = REPORTS_DIR
    analyses_dir = ANALYSES_DIR

    @staticmethod
    def save_temp_video(filename: str, content: bytes) -> Tuple[str, Path]:
        """Saves an incoming video to an isolated temporary storage directory with a secure random UUID."""
        TEMP_VIDEOS_DIR.mkdir(parents=True, exist_ok=True)
        video_id = str(uuid.uuid4())
        ext = Path(filename).suffix.lower() or ".mp4"
        saved_filename = f"{video_id}{ext}"
        filepath = TEMP_VIDEOS_DIR / saved_filename
        
        with open(filepath, "wb") as f:
            f.write(content)
            
        return video_id, filepath

    @staticmethod
    def save_raw_video(filename: str, content: bytes) -> Tuple[str, Path]:
        """Saves video to raw storage directory (used when video retention is explicitly enabled)."""
        RAW_VIDEOS_DIR.mkdir(parents=True, exist_ok=True)
        video_id = str(uuid.uuid4())
        ext = Path(filename).suffix.lower() or ".mp4"
        saved_filename = f"{video_id}{ext}"
        filepath = RAW_VIDEOS_DIR / saved_filename
        
        with open(filepath, "wb") as f:
            f.write(content)
            
        return video_id, filepath

    @staticmethod
    def get_raw_video_path(video_id: str) -> Optional[Path]:
        """Searches for video in temp directory first (privacy-first default), then raw storage."""
        # 1. Check temp videos directory
        if TEMP_VIDEOS_DIR.exists():
            for file in TEMP_VIDEOS_DIR.iterdir():
                if file.stem == video_id:
                    return file

        # 2. Check raw videos directory
        if RAW_VIDEOS_DIR.exists():
            for file in RAW_VIDEOS_DIR.iterdir():
                if file.stem == video_id:
                    return file
        return None

    @staticmethod
    def cleanup_temp_video(video_id: str) -> bool:
        """Safely purges temporary video file from disk after analysis completion or on failure."""
        if not TEMP_VIDEOS_DIR.exists():
            return False
        cleaned = False
        for file in TEMP_VIDEOS_DIR.iterdir():
            if file.stem == video_id:
                try:
                    file.unlink(missing_ok=True)
                    logger.info(f"Privacy-First: Temporary video {file.name} successfully deleted from disk.")
                    cleaned = True
                except Exception as e:
                    logger.warning(f"Failed to delete temporary video {file.name}: {e}")
        return cleaned

    @staticmethod
    def cleanup_raw_video(video_id: str) -> bool:
        """Deletes raw video file from disk."""
        if not RAW_VIDEOS_DIR.exists():
            return False
        cleaned = False
        for file in RAW_VIDEOS_DIR.iterdir():
            if file.stem == video_id:
                try:
                    file.unlink(missing_ok=True)
                    cleaned = True
                except Exception as e:
                    logger.warning(f"Failed to delete raw video {file.name}: {e}")
        return cleaned

    @staticmethod
    def get_annotated_video_path(analysis_id: str, ext: str = ".mp4") -> Path:
        ANNOTATED_VIDEOS_DIR.mkdir(parents=True, exist_ok=True)
        return ANNOTATED_VIDEOS_DIR / f"{analysis_id}{ext}"

    @staticmethod
    def cleanup_annotated_video(analysis_id: str) -> bool:
        """Deletes annotated video file from disk."""
        path = StorageManager.get_annotated_video_path(analysis_id)
        if path.exists():
            try:
                path.unlink(missing_ok=True)
                return True
            except Exception as e:
                logger.warning(f"Failed to delete annotated video for {analysis_id}: {e}")
        return False

    @staticmethod
    def get_report_path(analysis_id: str, ext: str = ".pdf") -> Path:
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        return REPORTS_DIR / f"{analysis_id}{ext}"

    @staticmethod
    def get_analysis_path(analysis_id: str) -> Path:
        ANALYSES_DIR.mkdir(parents=True, exist_ok=True)
        return ANALYSES_DIR / f"{analysis_id}.json"

    @staticmethod
    def save_analysis_json(analysis_id: str, data: Dict[str, Any]) -> Path:
        ANALYSES_DIR.mkdir(parents=True, exist_ok=True)
        filepath = ANALYSES_DIR / f"{analysis_id}.json"
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        return filepath

    @staticmethod
    def get_analysis_json(analysis_id: str) -> Optional[Dict[str, Any]]:
        filepath = ANALYSES_DIR / f"{analysis_id}.json"
        if filepath.exists():
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        return None

storage_manager = StorageManager()
