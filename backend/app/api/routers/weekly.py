from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status

from app.db.models import User
from app.auth.dependencies import get_current_user, get_optional_current_user
from app.api.schemas.weekly_summary import PersonalizedWeeklySummaryResponse
from app.weekly.weekly_summary_engine import weekly_summary_engine

router = APIRouter(prefix="/api/profile/weekly-summary", tags=["Personalized Weekly Running Summary"])

@router.get("", response_model=PersonalizedWeeklySummaryResponse)
def get_weekly_summary(
    week_offset: int = Query(0, ge=0, le=12, description="0 = current week, 1 = previous week, up to 12 weeks ago"),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """
    Retrieves the authenticated runner's personalized weekly summary.
    Enforces strict user isolation. Unauthenticated guests receive an empty week state.
    """
    user_id = current_user.id if current_user else None
    return weekly_summary_engine.generate_weekly_summary(user_id=user_id, week_offset=week_offset)
