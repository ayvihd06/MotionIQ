from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status

from app.db.models import User
from app.auth.dependencies import get_current_user, get_optional_current_user
from app.api.schemas.recommendation import PersonalizedRecommendationResponse
from app.recommendations.recommendation_engine import personalized_recommendation_engine

router = APIRouter(prefix="/api/profile/recommendations", tags=["Personalized Recommendations"])

@router.get("", response_model=PersonalizedRecommendationResponse)
def get_personalized_recommendations(
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """
    Returns personalized, evidence-informed training suggestions for the authenticated runner.
    Synthesizes active Personal Goal, Personal Focus Area, What Changed? deltas, and running context.
    Enforces strict user isolation.
    """
    user_id = current_user.id if current_user else None
    return personalized_recommendation_engine.generate_recommendation(user_id=user_id)
