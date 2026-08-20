from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class MilestoneItem(BaseModel):
    type: str = Field(..., description="Unique milestone identifier type")
    title: str = Field(..., description="Display title of the milestone")
    icon: str = Field("trophy", description="Lucide icon name")
    value: Optional[float] = Field(None, description="Achieved milestone value")
    unit: str = Field("", description="Measurement unit (e.g. %, SPM, sessions)")
    label: str = Field(..., description="Short badge label (e.g. Personal Best, +2.4 percentage points)")
    metric_name: str = Field(..., description="Name of the underlying biomechanical metric")
    analysis_id: Optional[str] = Field(None, description="UUID of the analysis where the milestone was achieved")
    comparison_analysis_id: Optional[str] = Field(None, description="UUID of the comparison baseline session if applicable")
    achieved_at: Optional[str] = Field(None, description="ISO timestamp of when the milestone was achieved")
    previous_value: Optional[float] = Field(None, description="Prior personal record before this milestone")
    current_value: Optional[float] = Field(None, description="Current value at the milestone session")
    improvement_delta: Optional[float] = Field(None, description="Delta over previous personal best or session")
    improvement_unit: Optional[str] = Field(None, description="Unit of the delta (e.g. percentage points, SPM)")
    description: str = Field(..., description="Detailed explanation of the milestone")
    motivational_note: Optional[str] = Field(None, description="Encouraging summary note")

class MilestoneEmptyState(BaseModel):
    title: str
    subtitle: str
    message: str
    action_label: str

class MilestonesResponse(BaseModel):
    total_analyses: int = Field(..., description="Total valid analysis records evaluated")
    has_milestones: bool = Field(..., description="True if any milestones are established")
    is_demo: bool = Field(False, description="True if demo mode sample milestones")
    empty_state: Optional[MilestoneEmptyState] = None
    milestones: List[MilestoneItem] = Field(default_factory=list)
    recent_achievements: List[Dict[str, Any]] = Field(default_factory=list)
