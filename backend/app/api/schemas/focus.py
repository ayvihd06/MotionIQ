from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field

FocusState = Literal[
    "ACTIVE_FOCUS",
    "NO_GOAL",
    "FIRST_ANALYSIS",
    "NO_STRONG_FOCUS",
    "INSUFFICIENT_DATA"
]

FocusConfidence = Literal["HIGH", "MEDIUM", "LOW"]

class FocusAreaItem(BaseModel):
    focus_type: str = Field(..., description="Stable internal identifier for the focus area")
    title: str = Field(..., description="Display title of the focus area (e.g. Cadence Consistency)")
    subtitle: str = Field(..., description="Brief one-line summary of what this focus addresses")
    primary_metric_key: str = Field(..., description="Key of the primary underlying metric (e.g. cadence, symmetry)")
    primary_metric_name: str = Field(..., description="Human-readable metric name")
    goal_type: str = Field(..., description="Associated active personal goal identifier")
    goal_title: str = Field(..., description="Display title of the user's active goal")
    confidence: FocusConfidence = Field("MEDIUM", description="Confidence in this focus determination")
    reasoning: List[str] = Field(default_factory=list, description="Factual 'Why this is your focus' bullet points supported by real session data")
    supporting_observations: List[str] = Field(default_factory=list, description="Specific observational notes from recent sessions")
    priority_score: float = Field(..., description="Deterministic priority score used in candidate ranking")

class ActionCTA(BaseModel):
    label: str
    target: str

class PersonalFocusResponse(BaseModel):
    state: FocusState = Field(..., description="Current state of the focus engine")
    has_goal: bool = Field(..., description="True if the authenticated user has set an active personal goal")
    total_analyses: int = Field(..., description="Number of completed sessions evaluated for this runner")
    goal: Optional[Dict[str, str]] = Field(None, description="Active user goal metadata if present")
    focus: Optional[FocusAreaItem] = Field(None, description="Derived top focus area item if state is ACTIVE_FOCUS")
    headline: str = Field(..., description="User-facing headline (e.g. 'Your Current Focus')")
    message: str = Field(..., description="Contextual explanation for the current state")
    action_cta: Optional[ActionCTA] = Field(None, description="Optional call-to-action button metadata")
