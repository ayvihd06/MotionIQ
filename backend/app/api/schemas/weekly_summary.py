from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field

WeeklySummaryState = Literal[
    "ACTIVE_SUMMARY",
    "ONE_SESSION",
    "EMPTY_WEEK"
]

class WeeklyPeriod(BaseModel):
    start_date: str = Field(..., description="Start of weekly cycle (Monday) in ISO format (YYYY-MM-DD)")
    end_date: str = Field(..., description="End of weekly cycle (Sunday) in ISO format (YYYY-MM-DD)")
    label: str = Field(..., description="Human-readable label for this week")
    week_offset: int = Field(0, description="0 = current week, 1 = previous week")

class WeeklyMetricItem(BaseModel):
    key: str = Field(..., description="Internal metric key (e.g. cadence, symmetry)")
    name: str = Field(..., description="Display metric name")
    value_display: str = Field(..., description="Formatted representative/average value")
    unit: str = Field(..., description="Metric unit (SPM, %, °, etc.)")
    change_display: Optional[str] = Field(None, description="Change vs prior baseline or earlier session in week")
    is_percentage_points: bool = Field(False, description="True if delta represents percentage points")

class WeeklyHighlight(BaseModel):
    headline: str = Field(..., description="Short highlight title")
    description: str = Field(..., description="Factual supporting description of the highlight")
    badge: str = Field("Progress", description="Tag/badge label for highlight card")

class ActionCTA(BaseModel):
    label: str
    target: str

class PersonalizedWeeklySummaryResponse(BaseModel):
    period: WeeklyPeriod = Field(..., description="Evaluated weekly window")
    state: WeeklySummaryState = Field(..., description="Current state: ACTIVE_SUMMARY, ONE_SESSION, or EMPTY_WEEK")
    total_sessions: int = Field(..., description="Total completed analyses during this weekly window")
    goal: Optional[Dict[str, str]] = Field(None, description="Active personal goal metadata")
    focus: Optional[Dict[str, str]] = Field(None, description="Current personal focus area metadata")
    highlight: Optional[WeeklyHighlight] = Field(None, description="Primary weekly highlight based on real data")
    metrics: List[WeeklyMetricItem] = Field(default_factory=list, description="Safely aggregated weekly metrics")
    changes_summary: Optional[str] = Field(None, description="Concise summary of what changed across the week")
    milestone: Optional[Dict[str, str]] = Field(None, description="Milestone or personal record achieved this week")
    recommendation: Optional[Dict[str, Any]] = Field(None, description="Personalized next-step training suggestion")
    insight: str = Field(..., description="Concise evidence-based weekly narrative insight")
    context_notes: List[str] = Field(default_factory=list, description="Contextual considerations (e.g. intensity/surface variation)")
    has_previous_week: bool = Field(True, description="True if older history exists")
    action_cta: Optional[ActionCTA] = Field(None, description="Optional call-to-action metadata")
