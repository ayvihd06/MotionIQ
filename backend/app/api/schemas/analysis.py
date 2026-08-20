from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Literal
from app.api.schemas.context import DetectedVideoContext, OptionalUserContext, AnalysisContext
from app.api.schemas.video import VideoMetadata, VideoSuitabilityReport

class CreateAnalysisRequest(BaseModel):
    video_id: str
    detected_context: DetectedVideoContext
    optional_context: Optional[OptionalUserContext] = None

class SaveLiveAnalysisRequest(BaseModel):
    cadence_spm: float = Field(..., ge=0, le=300)
    step_count: int = Field(..., ge=0)
    left_right_symmetry_pct: float = Field(..., ge=0, le=100)
    trunk_lean_deg: float = Field(..., ge=0, le=90)
    duration_sec: float = Field(..., ge=0)
    camera_view: str = Field(default="Side view")
    camera_suitability: str = Field(default="Good")
    tracking_quality_pct: float = Field(default=85.0, ge=0, le=100)
    form_classification: Optional[str] = "Live Observational Running Form"
    overall_confidence: Optional[Literal["High", "Medium", "Low"]] = "Medium"
    observations: Optional[List[str]] = []
    optional_context: Optional[OptionalUserContext] = None

class AnalysisStatusResponse(BaseModel):
    analysis_id: str
    status: Literal["uploaded", "validating", "processing", "completed", "failed"]
    progress_percentage: int = Field(..., ge=0, le=100)
    current_step: str
    error_message: Optional[str] = None

class StandardMetricItem(BaseModel):
    key: str
    name: str
    value: str
    unit: str
    confidence: Literal["High", "Medium", "Low"]
    status: Literal["Optimal", "Normal", "Attention", "Observed", "Estimated"]
    description: str
    limitations: Optional[str] = None

class FormObservationItem(BaseModel):
    title: str
    category: str
    observation: str
    supporting_metrics: List[str]
    confidence: Literal["High", "Medium", "Low"]
    scientific_note: str

class GaitEventItem(BaseModel):
    frame_idx: int
    timestamp_s: float
    side: str
    event_type: str
    confidence: float

class WaveformPoint(BaseModel):
    timestamp_s: float
    pelvis_y: float
    left_ankle_y: float
    right_ankle_y: float

class RunningTypeContextSchema(BaseModel):
    distance_category: str
    surface_category: str
    intensity_category: str
    experience_level: str
    runner_profile_summary: str

class MetricConfidenceItemSchema(BaseModel):
    metric_key: str
    confidence_level: Literal["High", "Medium", "Low"]
    confidence_score: float
    contributing_factors: List[str]

class MetricConfidenceBreakdownSchema(BaseModel):
    cadence_confidence: MetricConfidenceItemSchema
    symmetry_confidence: MetricConfidenceItemSchema
    trunk_lean_confidence: MetricConfidenceItemSchema
    foot_strike_confidence: MetricConfidenceItemSchema
    overstride_confidence: MetricConfidenceItemSchema
    vertical_movement_confidence: MetricConfidenceItemSchema
    overall_confidence: Literal["High", "Medium", "Low"]
    overall_score: float

class ContextAwareInsightSchema(BaseModel):
    title: str
    category: str
    severity: Literal["positive", "neutral", "monitor"]
    description: str
    supporting_metrics: List[str]
    confidence: Literal["High", "Medium", "Low"]
    why_flagged: List[str]
    recommended_action: str
    limitations: str

class OverallSummaryReportSchema(BaseModel):
    headline: str
    strongest_positive_observations: List[str]
    areas_to_monitor: List[str]
    form_consistency_score: float
    context_summary: str
    responsible_ai_disclaimer: str

class AnalysisResultResponse(BaseModel):
    analysis_id: str
    video_id: str
    created_at: str
    context: AnalysisContext
    video_metadata: VideoMetadata
    suitability: VideoSuitabilityReport
    status: Literal["uploaded", "validating", "processing", "completed", "failed"]
    annotated_video_url: Optional[str] = None
    
    # Biomechanical Primary Outputs
    cadence_spm: float
    step_count: int
    left_right_symmetry_pct: float
    trunk_lean_deg: float
    left_mean_step_time_s: float
    right_mean_step_time_s: float
    mean_stride_time_s: float
    step_time_variability_cv: float
    mean_elbow_angle_deg: float
    overstride_risk: str
    foot_strike_pattern: str
    relative_vertical_movement_proxy: float
    form_classification: str
    overall_confidence: Literal["High", "Medium", "Low"]
    
    # Phase 4 Rich Context, Confidence & Insights
    running_type_context: Optional[RunningTypeContextSchema] = None
    confidence_breakdown: Optional[MetricConfidenceBreakdownSchema] = None
    context_insights: List[ContextAwareInsightSchema] = []
    overall_summary: Optional[OverallSummaryReportSchema] = None
    
    gait_events: List[GaitEventItem] = []
    waveform_data: List[WaveformPoint] = []
    metrics_breakdown: List[StandardMetricItem] = []
    observations: List[FormObservationItem] = []
    recommendations: List[str] = []
    limitations: List[str] = []
