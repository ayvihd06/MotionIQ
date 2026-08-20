import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
STORAGE_DIR = BASE_DIR / "storage"

RAW_VIDEOS_DIR = STORAGE_DIR / "raw_videos"
TEMP_VIDEOS_DIR = STORAGE_DIR / "temp_videos"
ANNOTATED_VIDEOS_DIR = STORAGE_DIR / "annotated_videos"
REPORTS_DIR = STORAGE_DIR / "reports"
ANALYSES_DIR = STORAGE_DIR / "analyses"

# Ensure all storage directories exist
for path in [RAW_VIDEOS_DIR, TEMP_VIDEOS_DIR, ANNOTATED_VIDEOS_DIR, REPORTS_DIR, ANALYSES_DIR]:
    path.mkdir(parents=True, exist_ok=True)

# Database Configuration (PostgreSQL with graceful SQLite fallback for unit tests)
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://stridesense_user:stridesense_password@localhost:5432/stridesense_db"
)

# Authentication & Security
SECRET_KEY = os.getenv("SECRET_KEY", "stridesense-local-dev-jwt-key-2026-secure")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440")) # 24 hours
AUTH_COOKIE_NAME = os.getenv("AUTH_COOKIE_NAME", "stridesense_session")
AUTH_COOKIE_SECURE = os.getenv("AUTH_COOKIE_SECURE", "false").lower() in ("true", "1", "yes")

# Privacy & Video Lifecycle
# By default, videos are deleted after biomechanical extraction
VIDEO_RETENTION_DEFAULT = os.getenv("VIDEO_RETENTION_DEFAULT", "false").lower() in ("true", "1", "yes")

# Video validation thresholds
RECOMMENDED_MIN_DURATION_SEC = 10.0
RECOMMENDED_MAX_DURATION_SEC = 30.0
ABSOLUTE_MIN_DURATION_SEC = 3.0
ABSOLUTE_MAX_DURATION_SEC = 120.0

RECOMMENDED_MIN_FPS = 55.0
ACCEPTABLE_MIN_FPS = 24.0

MIN_WIDTH = 1280
MIN_HEIGHT = 720
PREFERRED_WIDTH = 1920
PREFERRED_HEIGHT = 1080

MAX_FILE_SIZE_MB = 150
ALLOWED_EXTENSIONS = {".mp4", ".mov", ".avi", ".m4v", ".webm"}

PORT = int(os.getenv("PORT", 8000))
HOST = os.getenv("HOST", "0.0.0.0")
