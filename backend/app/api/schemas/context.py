from pydantic import BaseModel, Field
from typing import Optional, Generic, TypeVar, Literal
from datetime import datetime

T = TypeVar('T')

class ProvenanceField(BaseModel, Generic[T]):
    value: T
    source: Literal["video_metadata", "computer_vision", "pose_analysis", "user", "historical_baseline", "calibration"] = Field(
        ..., description="Origin source of the context attribute"
    )
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score from 0.0 to 1.0")
    user_confirmed: bool = False
    user_corrected: bool = False
    detected_at: Optional[str] = None

class DetectedVideoContext(BaseModel):
    duration_sec: float
    fps: float
    resolution: str
    video_format: str
    quality_status: str
    
    runner_count: ProvenanceField[int]
    full_body_visible: ProvenanceField[bool]
    camera_view: ProvenanceField[str]
    camera_stability: ProvenanceField[str]
    
    observed_movement: ProvenanceField[str] = Field(
        ..., description="Movement intensity classification e.g. 'Walking', 'Jogging', 'Running', 'Fast running', 'Sprint-like'"
    )
    surface: ProvenanceField[str] = Field(
        ..., description="Surface visual classification e.g. 'Road / Asphalt', 'Track', 'Treadmill', 'Trail', 'Grass', 'Unknown'"
    )
    running_pace_status: ProvenanceField[str] = Field(
        ..., description="Pace estimation status e.g. 'Not available from this video'"
    )
    pace_estimation_mode: Literal["Uncalibrated video", "Calibrated video", "Treadmill", "Track"] = "Uncalibrated video"
    historical_baseline_status: str = "Personal running baseline not established yet"

class OptionalUserContext(BaseModel):
    training_goal: Optional[str] = Field(None, description="e.g. 'General fitness', '5K', '10K', 'Half Marathon', 'Marathon'")
    known_pace: Optional[str] = Field(None, description="User-provided known pace e.g. '5:15 min/km'")
    perceived_effort: Optional[Literal["Very easy", "Easy", "Moderate", "Hard", "Very hard", "Not sure"]] = None
    previous_injury: Optional[str] = Field(None, description="Previous or recent injury focus areas")
    
    # Optional Runner Profile
    age_category: Optional[str] = Field(None, description="'18-29', '30-39', '40-49', '50-59', '60+'")
    experience_level: Optional[str] = Field(None, description="'Beginner', 'Intermediate', 'Advanced', 'Elite'")
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None
    bmi: Optional[float] = None
    weekly_volume_km: Optional[float] = None

class AnalysisContext(BaseModel):
    video_id: str
    detected: DetectedVideoContext
    optional: OptionalUserContext
    has_missing_context: bool = False
    context_notice: str = "Some contextual information is unavailable. Results will still be generated using the information detected from your video."
