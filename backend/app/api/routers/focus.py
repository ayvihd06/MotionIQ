from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status

from app.db.models import User
from app.auth.dependencies import get_current_user, get_optional_current_user
from app.api.schemas.focus import PersonalFocusResponse
from app.focus.focus_engine import personal_focus_engine

router = APIRouter(prefix="/api/profile/focus", tags=["Personal Focus Area"])

@router.get("", response_model=PersonalFocusResponse)
def get_personal_focus(
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """
    Computes the authenticated runner's current Personal Focus Area.
    Synthesizes active personal goal, latest session-over-session changes,
    multi-session history, and measurement confidence.
    Enforces strict user isolation.
    """
    user_id = current_user.id if current_user else None
    return personal_focus_engine.compute_personal_focus(user_id=user_id)
