from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.models import User
from app.auth.dependencies import get_optional_current_user
from app.repositories.analysis_repository import analysis_repository
from app.milestones.milestone_service import milestone_service
from app.api.schemas.milestone import MilestonesResponse

router = APIRouter(prefix="/api/milestones", tags=["Personal Milestones"])

@router.get("", response_model=MilestonesResponse)
def get_personal_milestones(
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """
    Calculates and returns personal milestones derived strictly from the authenticated runner's own historical analyses.
    Enforces strict user isolation. Unauthenticated guests receive an encouraging empty state.
    """
    # Unauthenticated guests receive the clean personal empty state
    if not current_user:
        return milestone_service.calculate_milestones([], is_demo=False)

    user_id = current_user.id

    # Retrieve authenticated user's historical analyses (strict user data isolation)
    analyses_summaries = analysis_repository.list_analyses(limit=100, user_id=user_id)

    # Load full analysis payloads for milestone evaluation
    full_analyses = []
    for summary in analyses_summaries:
        analysis_id = summary.get("analysis_id")
        if analysis_id:
            full_data = analysis_repository.get_analysis(analysis_id, user_id=user_id)
            if full_data:
                full_analyses.append(full_data)

    report = milestone_service.calculate_milestones(full_analyses, is_demo=False)
    return report

@router.get("/celebration/{analysis_id}", response_model=Dict[str, Any])
def get_session_celebration(
    analysis_id: str,
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """
    Evaluates whether a specific completed session established any new personal records for celebration.
    """
    user_id = current_user.id if current_user else None

    # Verify session ownership
    target = analysis_repository.get_analysis(analysis_id, user_id=user_id)
    if not target:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis session not found or unauthorized."
        )

    # Load user's full history to evaluate personal best progression
    analyses_summaries = analysis_repository.list_analyses(limit=100, user_id=user_id)
    full_analyses = []
    for summary in analyses_summaries:
        a_id = summary.get("analysis_id")
        if a_id:
            full_data = analysis_repository.get_analysis(a_id, user_id=user_id)
            if full_data:
                full_analyses.append(full_data)

    report = milestone_service.calculate_milestones(full_analyses, is_demo=False)

    # Find any milestones matching this specific analysis_id
    achieved = [
        m for m in report.get("milestones", [])
        if m.get("value") is not None and m.get("analysis_id") == analysis_id and m.get("type") != "analysis_streak"
    ]

    return {
        "analysis_id": analysis_id,
        "has_celebration": len(achieved) > 0,
        "new_personal_bests": achieved
    }
