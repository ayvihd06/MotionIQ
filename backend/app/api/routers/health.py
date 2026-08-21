from fastapi import APIRouter
from typing import Dict, Any

router = APIRouter(tags=["Health"])

@router.get("/health")
@router.get("/api/health")
def health_check() -> Dict[str, Any]:
    return {
        "status": "healthy",
        "service": "MotionIQ API Engine",
        "version": "1.0.0",
        "features": {
            "video_upload": True,
            "suitability_validation": True,
            "analysis_shell": True
        }
    }
