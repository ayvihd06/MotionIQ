from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field

# Stable catalog of recognized personal running goals
GOAL_CATALOG: Dict[str, Dict[str, str]] = {
    "IMPROVE_EFFICIENCY": {
        "title": "Improve Running Efficiency",
        "explanation": "Focus on movement patterns associated with efficient running mechanics.",
        "icon": "activity"
    },
    "IMPROVE_CADENCE": {
        "title": "Improve Cadence",
        "explanation": "Focus MotionIQ on cadence-related progress and observations.",
        "icon": "zap"
    },
    "IMPROVE_SYMMETRY": {
        "title": "Improve Movement Symmetry",
        "explanation": "Focus on left/right movement balance.",
        "icon": "scale"
    },
    "IMPROVE_FORM": {
        "title": "Improve Running Form",
        "explanation": "Focus on observable form characteristics.",
        "icon": "target"
    },
    "IMPROVE_CONSISTENCY": {
        "title": "Improve Running Consistency",
        "explanation": "Focus on consistency across your sessions.",
        "icon": "trending-up"
    },
    "GENERAL_PERFORMANCE": {
        "title": "General Performance",
        "explanation": "Use a broad performance-oriented perspective.",
        "icon": "trophy"
    }
}

GoalType = Literal[
    "IMPROVE_EFFICIENCY",
    "IMPROVE_CADENCE",
    "IMPROVE_SYMMETRY",
    "IMPROVE_FORM",
    "IMPROVE_CONSISTENCY",
    "GENERAL_PERFORMANCE"
]

GoalStatus = Literal["ACTIVE", "COMPLETED", "PAUSED"]

class GoalOption(BaseModel):
    type: GoalType
    title: str
    explanation: str
    icon: str

class GoalItem(BaseModel):
    type: GoalType = Field(..., description="Stable internal identifier")
    title: str = Field(..., description="Display title")
    description: Optional[str] = Field(None, max_length=255, description="Optional user note or focus description")
    status: GoalStatus = Field("ACTIVE", description="Current goal state")
    created_at: Optional[str] = Field(None, description="ISO timestamp when goal was established")
    updated_at: Optional[str] = Field(None, description="ISO timestamp when goal was last updated")
    explanation: str = Field("", description="Educational focus explanation")
    icon: str = Field("target", description="Lucide icon key")

class GoalResponse(BaseModel):
    goal: Optional[GoalItem] = None
    available_goals: List[GoalOption] = Field(default_factory=list)

class GoalUpdateRequest(BaseModel):
    type: GoalType = Field(..., description="Selected goal type identifier")
    description: Optional[str] = Field(None, max_length=255, description="Optional short user note")
    status: Optional[GoalStatus] = Field("ACTIVE", description="Desired goal status")
