from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field

RecommendationCategory = Literal[
    "OBSERVE",
    "PRACTICE",
    "CONSISTENCY",
    "RECHECK",
    "CONTEXT_MATCH",
    "LEARN"
]

RecommendationConfidence = Literal["HIGH", "MEDIUM", "LOW"]

RecommendationState = Literal[
    "ACTIVE_RECOMMENDATION",
    "NO_GOAL",
    "FIRST_ANALYSIS",
    "NO_STRONG_FOCUS",
    "LOW_CONFIDENCE",
    "INSUFFICIENT_DATA"
]

class RecommendationItem(BaseModel):
    title: str = Field(..., description="Action-oriented title of the recommendation")
    category: RecommendationCategory = Field(..., description="Category: OBSERVE, PRACTICE, CONSISTENCY, RECHECK, CONTEXT_MATCH, LEARN")
    focus_type: str = Field(..., description="Associated Personal Focus Area identifier")
    focus_title: str = Field(..., description="Display title of the connected focus area")
    goal_type: str = Field(..., description="Connected Personal Goal identifier")
    goal_title: str = Field(..., description="Display title of the user's active goal")
    action_suggestion: str = Field(..., description="Primary non-prescriptive training suggestion")
    action_bullets: List[str] = Field(default_factory=list, description="Practical suggestions for the runner's next session")
    rationale: List[str] = Field(default_factory=list, description="Explainable 'Why this recommendation?' bullet points based on real user data")
    confidence: RecommendationConfidence = Field("MEDIUM", description="Recommendation confidence based on evidence quality")
    supporting_evidence: List[str] = Field(default_factory=list, description="Specific supporting metrics and session observations")

class ActionCTA(BaseModel):
    label: str
    target: str

class PersonalizedRecommendationResponse(BaseModel):
    state: RecommendationState = Field(..., description="Current state of the recommendation engine")
    has_goal: bool = Field(..., description="True if the user has an active personal goal")
    total_analyses: int = Field(..., description="Number of analyses evaluated")
    goal: Optional[Dict[str, str]] = Field(None, description="Active user goal metadata")
    focus_type: Optional[str] = Field(None, description="Active focus area key if available")
    recommendation: Optional[RecommendationItem] = Field(None, description="Top personalized recommendation if state is ACTIVE_RECOMMENDATION or LOW_CONFIDENCE")
    headline: str = Field(..., description="User-facing headline (e.g. 'Personalized Recommendation')")
    message: str = Field(..., description="Contextual message for the current state")
    action_cta: Optional[ActionCTA] = Field(None, description="Optional call-to-action metadata")
