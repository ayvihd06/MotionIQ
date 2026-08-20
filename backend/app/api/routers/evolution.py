from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models import User
from app.auth.dependencies import get_current_user, get_optional_current_user
from app.repositories.analysis_repository import analysis_repository
from app.evolution.evolution_engine import evolution_engine

router = APIRouter(prefix="/api/evolution", tags=["Personal Form Evolution"])

@router.get("", response_model=Dict[str, Any])
def get_personal_form_evolution(
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """Retrieves the personal baseline, comparative change metrics, and historical trend series for the authenticated runner."""
    user_id = current_user.id if current_user else None
    
    # Retrieve user's historical analyses (strict user data isolation)
    analyses_summaries = analysis_repository.list_analyses(limit=50, user_id=user_id)
    
    # Load full analysis payloads for evolution calculations
    full_analyses = []
    for summary in analyses_summaries:
        analysis_id = summary.get("analysis_id")
        if analysis_id:
            full_data = analysis_repository.get_analysis(analysis_id, user_id=user_id)
            if full_data:
                full_analyses.append(full_data)

    evolution_report = evolution_engine.compute_evolution(full_analyses)
    return evolution_report
