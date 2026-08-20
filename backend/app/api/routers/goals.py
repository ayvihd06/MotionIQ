from typing import Dict, Any, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models import User, UserProfile
from app.auth.dependencies import get_current_user
from app.api.schemas.goal import (
    GoalResponse, GoalItem, GoalUpdateRequest, GoalOption, GOAL_CATALOG
)

router = APIRouter(prefix="/api/profile/goal", tags=["Personal Goals"])

def get_available_goals_list():
    return [
        GoalOption(
            type=k, # type: ignore
            title=v["title"],
            explanation=v["explanation"],
            icon=v["icon"]
        )
        for k, v in GOAL_CATALOG.items()
    ]

@router.get("", response_model=GoalResponse)
def get_user_goal(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieves the currently authenticated runner's active personal goal.
    Enforces strict user isolation via JWT session identity.
    """
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    available = get_available_goals_list()

    if not profile or not profile.goal_type:
        return GoalResponse(goal=None, available_goals=available)

    catalog_meta = GOAL_CATALOG.get(profile.goal_type, {
        "title": profile.goal_type.replace("_", " ").title(),
        "explanation": "Personal running focus.",
        "icon": "target"
    })

    goal_item = GoalItem(
        type=profile.goal_type, # type: ignore
        title=catalog_meta["title"],
        description=profile.goal_description,
        status=profile.goal_status or "ACTIVE", # type: ignore
        created_at=profile.goal_created_at.isoformat() if profile.goal_created_at else None,
        updated_at=profile.goal_updated_at.isoformat() if profile.goal_updated_at else None,
        explanation=catalog_meta["explanation"],
        icon=catalog_meta["icon"]
    )

    return GoalResponse(goal=goal_item, available_goals=available)


@router.put("", response_model=GoalResponse)
def set_or_update_user_goal(
    goal_data: GoalUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Sets or updates the authenticated runner's current personal goal.
    Validates goal type and enforces ownership.
    """
    if goal_data.type not in GOAL_CATALOG:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid goal type '{goal_data.type}'. Must be one of: {list(GOAL_CATALOG.keys())}"
        )

    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    now = datetime.now(timezone.utc)

    if not profile:
        profile = UserProfile(user_id=current_user.id)
        db.add(profile)

    # If first time setting goal
    if not profile.goal_created_at or profile.goal_type != goal_data.type:
        profile.goal_created_at = now

    profile.goal_type = goal_data.type
    profile.goal_description = (goal_data.description.strip() if goal_data.description else None)
    profile.goal_status = goal_data.status or "ACTIVE"
    profile.goal_updated_at = now

    db.commit()
    db.refresh(profile)

    catalog_meta = GOAL_CATALOG[goal_data.type]
    goal_item = GoalItem(
        type=profile.goal_type, # type: ignore
        title=catalog_meta["title"],
        description=profile.goal_description,
        status=profile.goal_status or "ACTIVE", # type: ignore
        created_at=profile.goal_created_at.isoformat() if profile.goal_created_at else None,
        updated_at=profile.goal_updated_at.isoformat() if profile.goal_updated_at else None,
        explanation=catalog_meta["explanation"],
        icon=catalog_meta["icon"]
    )

    return GoalResponse(goal=goal_item, available_goals=get_available_goals_list())


@router.post("", response_model=GoalResponse)
def create_or_update_user_goal_post(
    goal_data: GoalUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """POST alias for setting or updating personal goal."""
    return set_or_update_user_goal(goal_data, current_user, db)


@router.patch("/complete", response_model=GoalResponse)
def complete_user_goal(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Marks the current goal as COMPLETED."""
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    if not profile or not profile.goal_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active goal found to complete."
        )

    now = datetime.now(timezone.utc)
    profile.goal_status = "COMPLETED"
    profile.goal_updated_at = now

    db.commit()
    db.refresh(profile)

    catalog_meta = GOAL_CATALOG.get(profile.goal_type, {
        "title": profile.goal_type.replace("_", " ").title(),
        "explanation": "Personal running focus.",
        "icon": "target"
    })

    goal_item = GoalItem(
        type=profile.goal_type, # type: ignore
        title=catalog_meta["title"],
        description=profile.goal_description,
        status="COMPLETED",
        created_at=profile.goal_created_at.isoformat() if profile.goal_created_at else None,
        updated_at=profile.goal_updated_at.isoformat() if profile.goal_updated_at else None,
        explanation=catalog_meta["explanation"],
        icon=catalog_meta["icon"]
    )

    return GoalResponse(goal=goal_item, available_goals=get_available_goals_list())
