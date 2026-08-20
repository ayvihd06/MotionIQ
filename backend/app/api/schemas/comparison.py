from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field

ComparisonDirection = Literal["INCREASED", "DECREASED", "UNCHANGED", "CHANGED", "NOT_AVAILABLE"]
ComparisonCategory = Literal["NOTABLE_CHANGE", "MODERATE_CHANGE", "LITTLE_CHANGE", "NOT_AVAILABLE"]

class MetricComparisonItem(BaseModel):
    key: str = Field(..., description="Unique metric key (e.g. cadence, symmetry, trunk_lean)")
    name: str = Field(..., description="Human-readable metric name")
    previous_value: Optional[Any] = Field(None, description="Value from immediately previous analysis")
    current_value: Optional[Any] = Field(None, description="Value from current analysis")
    previous_display: str = Field(..., description="Formatted previous string with units")
    current_display: str = Field(..., description="Formatted current string with units")
    absolute_change: Optional[float] = Field(None, description="Absolute mathematical difference")
    percentage_change: Optional[float] = Field(None, description="Percentage change where applicable")
    change_display: str = Field(..., description="User-facing change label (e.g. '+4 SPM', '+3.0 percentage points')")
    unit: str = Field(..., description="Metric unit")
    direction: ComparisonDirection = Field(..., description="Directional movement")
    category: ComparisonCategory = Field(..., description="Engineering significance category")
    goal_relevant: bool = Field(False, description="Whether metric directly relates to user's active personal goal")
    observation_text: str = Field(..., description="Factual, non-diagnostic statement describing observed change")

class UserGoalContext(BaseModel):
    type: str
    title: str
    description: Optional[str] = None
    explanation: str

class AnalysisComparisonResponse(BaseModel):
    analysis_id: str
    has_previous: bool = Field(..., description="True if an immediately previous completed session was found")
    is_first_analysis: bool = Field(..., description="True if this is the user's first recorded analysis")
    previous_analysis_id: Optional[str] = None
    previous_created_at: Optional[str] = None
    current_created_at: Optional[str] = None
    user_goal: Optional[UserGoalContext] = None
    comparison_summary: str = Field(..., description="Factual session-over-session summary")
    metrics: List[MetricComparisonItem] = Field(default_factory=list)
