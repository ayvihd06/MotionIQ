from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from app.api.schemas.context import DetectedVideoContext

class SuitabilityCheckItem(BaseModel):
    name: str = Field(..., description="Check name e.g., 'Duration', 'FPS', 'Resolution', 'Side-View'")
    passed: bool = Field(..., description="True if check passed or acceptable")
    rating: Literal["Optimal", "Acceptable", "Warning", "Critical"] = Field(...)
    message: str = Field(..., description="Explainable description of the check result")

class VideoMetadata(BaseModel):
    filename: str
    file_size_bytes: int
    duration_sec: float
    fps: float
    width: int
    height: int
    frame_count: int
    format: str

class VideoSuitabilityReport(BaseModel):
    overall_status: Literal["Ready for analysis", "Analysis may be unreliable", "Unsuitable for analysis"]
    suitability_score: float = Field(..., ge=0.0, le=100.0, description="0 to 100 overall score")
    checks: List[SuitabilityCheckItem]
    warnings: List[str]
    recommendations: List[str]

class VideoUploadResponse(BaseModel):
    video_id: str
    metadata: VideoMetadata
    suitability: VideoSuitabilityReport
    detected_context: DetectedVideoContext
