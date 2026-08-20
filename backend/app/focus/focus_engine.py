import logging
import math
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.db.models import Analysis, UserProfile
from app.api.schemas.goal import GOAL_CATALOG
from app.api.schemas.focus import (
    PersonalFocusResponse, FocusAreaItem, FocusState, FocusConfidence, ActionCTA
)
from app.comparison.comparison_engine import comparison_engine

logger = logging.getLogger(__name__)

# Candidate Focus Area Definitions per Goal Type
GOAL_FOCUS_CANDIDATES: Dict[str, List[Dict[str, Any]]] = {
    "IMPROVE_CADENCE": [
        {
            "focus_type": "CADENCE_CONSISTENCY",
            "title": "Cadence Consistency",
            "subtitle": "Maintaining steady step turnover across varying distances and paces",
            "primary_metric_key": "cadence",
            "primary_metric_name": "Cadence",
            "goal_relevance": 1.0,
            "metric_type": "numeric"
        },
        {
            "focus_type": "STRIDE_RHYTHM",
            "title": "Step & Stride Rhythm",
            "subtitle": "Even temporal contact and flight phases throughout your gait cycle",
            "primary_metric_key": "step_time",
            "primary_metric_name": "Mean Step Duration",
            "goal_relevance": 0.75,
            "metric_type": "numeric"
        }
    ],
    "IMPROVE_SYMMETRY": [
        {
            "focus_type": "BILATERAL_BALANCE",
            "title": "Bilateral Movement Balance",
            "subtitle": "Equalizing left vs right contact duration and kinetic loading symmetry",
            "primary_metric_key": "symmetry",
            "primary_metric_name": "Movement Symmetry",
            "goal_relevance": 1.0,
            "metric_type": "numeric"
        },
        {
            "focus_type": "STEP_TIMING_SYMMETRY",
            "title": "Left/Right Step Timing Balance",
            "subtitle": "Minimizing temporal differences in ground contact time between limbs",
            "primary_metric_key": "step_time",
            "primary_metric_name": "Step Duration",
            "goal_relevance": 0.8,
            "metric_type": "numeric"
        }
    ],
    "IMPROVE_FORM": [
        {
            "focus_type": "TRUNK_POSTURE",
            "title": "Forward Trunk Posture",
            "subtitle": "Maintaining aligned whole-body forward inclination originating from the ankles",
            "primary_metric_key": "trunk_lean",
            "primary_metric_name": "Trunk Forward Lean",
            "goal_relevance": 1.0,
            "metric_type": "numeric"
        },
        {
            "focus_type": "FOOT_STRIKE_MECHANICS",
            "title": "Foot Strike Mechanics",
            "subtitle": "Observing compliant landing patterns beneath your center of mass",
            "primary_metric_key": "foot_strike",
            "primary_metric_name": "Foot Strike Pattern",
            "goal_relevance": 0.85,
            "metric_type": "categorical"
        },
        {
            "focus_type": "ARM_CARRIAGE",
            "title": "Elbow & Arm Carriage",
            "subtitle": "Maintaining compact, coordinated arm drive aligned with cadence",
            "primary_metric_key": "arm_swing",
            "primary_metric_name": "Elbow Carriage Angle",
            "goal_relevance": 0.7,
            "metric_type": "numeric"
        }
    ],
    "IMPROVE_EFFICIENCY": [
        {
            "focus_type": "VERTICAL_OSCILLATION_CONTROL",
            "title": "Vertical Oscillation Control",
            "subtitle": "Directing momentum smoothly forward with controlled vertical displacement",
            "primary_metric_key": "vertical_movement",
            "primary_metric_name": "Vertical Movement Proxy",
            "goal_relevance": 1.0,
            "metric_type": "numeric"
        },
        {
            "focus_type": "CADENCE_TURNOVER",
            "title": "Cadence Turnover Efficiency",
            "subtitle": "Coordinating step frequency to promote efficient momentum",
            "primary_metric_key": "cadence",
            "primary_metric_name": "Cadence",
            "goal_relevance": 0.8,
            "metric_type": "numeric"
        },
        {
            "focus_type": "POSTURE_ALIGNMENT",
            "title": "Posture Alignment",
            "subtitle": "Forward inclination aligned with ground reaction forces",
            "primary_metric_key": "trunk_lean",
            "primary_metric_name": "Trunk Forward Lean",
            "goal_relevance": 0.75,
            "metric_type": "numeric"
        }
    ],
    "IMPROVE_CONSISTENCY": [
        {
            "focus_type": "GAIT_CONSISTENCY",
            "title": "Multi-Session Gait Consistency",
            "subtitle": "Maintaining reproducible, balanced kinematics across consecutive workouts",
            "primary_metric_key": "symmetry",
            "primary_metric_name": "Bilateral Symmetry",
            "goal_relevance": 1.0,
            "metric_type": "numeric"
        },
        {
            "focus_type": "CADENCE_STABILITY",
            "title": "Cadence Stability",
            "subtitle": "Steady step frequency across varying fatigue states",
            "primary_metric_key": "cadence",
            "primary_metric_name": "Cadence",
            "goal_relevance": 0.85,
            "metric_type": "numeric"
        }
    ],
    "GENERAL_PERFORMANCE": [
        {
            "focus_type": "OVERALL_CADENCE_TURNOVER",
            "title": "Cadence Turnover",
            "subtitle": "Step rate optimization across training paces",
            "primary_metric_key": "cadence",
            "primary_metric_name": "Cadence",
            "goal_relevance": 0.85,
            "metric_type": "numeric"
        },
        {
            "focus_type": "OVERALL_BILATERAL_BALANCE",
            "title": "Bilateral Movement Balance",
            "subtitle": "Left/right balance across consecutive workouts",
            "primary_metric_key": "symmetry",
            "primary_metric_name": "Movement Symmetry",
            "goal_relevance": 0.85,
            "metric_type": "numeric"
        },
        {
            "focus_type": "OVERALL_TRUNK_POSTURE",
            "title": "Trunk Forward Posture",
            "subtitle": "Dynamic forward torso inclination",
            "primary_metric_key": "trunk_lean",
            "primary_metric_name": "Trunk Forward Lean",
            "goal_relevance": 0.85,
            "metric_type": "numeric"
        }
    ]
}


class PersonalFocusEngine:
    """
    Deterministic scoring engine that calculates the authenticated runner's
    current personalized focus area based on their active goal, recent session changes,
    multi-session history, and measurement confidence.
    """

    def compute_personal_focus(self, user_id: Optional[str] = None) -> PersonalFocusResponse:
        db: Session = SessionLocal()
        try:
            # 1. Fetch authenticated user's active personal goal
            user_profile = None
            goal_type: Optional[str] = None
            goal_meta: Optional[Dict[str, str]] = None
            if user_id:
                user_profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
                if user_profile and user_profile.goal_type:
                    goal_type = user_profile.goal_type
                    cat = GOAL_CATALOG.get(goal_type, {
                        "title": goal_type.replace("_", " ").title(),
                        "explanation": "Personal running focus."
                    })
                    goal_meta = {
                        "type": goal_type,
                        "title": cat["title"],
                        "description": user_profile.goal_description or "",
                        "explanation": cat["explanation"]
                    }

            # 2. Fetch completed analyses for this user (ordered by created_at DESC)
            query = db.query(Analysis).filter(Analysis.status == "completed")
            if user_id:
                query = query.filter(Analysis.user_id == user_id)
            else:
                query = query.filter(Analysis.user_id == None)

            analyses = query.order_by(Analysis.created_at.desc()).limit(10).all()
            total_analyses = len(analyses)

            # ── STATE 1: Zero Sessions ───────────────────────────────────────
            if total_analyses == 0:
                return PersonalFocusResponse(
                    state="INSUFFICIENT_DATA",
                    has_goal=bool(goal_type),
                    total_analyses=0,
                    goal=goal_meta,
                    focus=None,
                    headline="Your Current Focus",
                    message="No recorded analyses found. Complete your first running analysis to establish your baseline and uncover personalized focus areas.",
                    action_cta=ActionCTA(label="Analyze Your First Run", target="upload")
                )

            # ── STATE 2: Exactly One Session (First Analysis) ────────────────
            if total_analyses == 1:
                goal_acknowledgment = f" Your current goal is {goal_meta['title']}. Future sessions will help MotionIQ identify changes related to this goal." if goal_meta else ""
                return PersonalFocusResponse(
                    state="FIRST_ANALYSIS",
                    has_goal=bool(goal_type),
                    total_analyses=1,
                    goal=goal_meta,
                    focus=None,
                    headline="Getting Your Baseline",
                    message=f"This is your first recorded analysis. MotionIQ will learn more about your running patterns as you complete additional sessions.{goal_acknowledgment}",
                    action_cta=ActionCTA(label="Set Personal Goal", target="profile") if not goal_type else None
                )

            # ── STATE 3: Multiple Sessions but No Goal Set ───────────────────
            if not goal_type:
                return PersonalFocusResponse(
                    state="NO_GOAL",
                    has_goal=False,
                    total_analyses=total_analyses,
                    goal=None,
                    focus=None,
                    headline="Set Your Personal Goal",
                    message="MotionIQ needs to know what you would like to improve so we can tailor your primary focus area.",
                    action_cta=ActionCTA(label="Set Personal Goal", target="profile")
                )

            # ── STATE 4: Evaluate Focus Candidates ───────────────────────────
            latest_analysis = analyses[0]
            
            # Fetch What Changed comparison data for the latest analysis
            comparison_data = None
            try:
                comparison_data = comparison_engine.compare_analyses(
                    current_analysis_id=latest_analysis.id,
                    user_id=user_id
                )
            except Exception as e:
                logger.warning(f"Failed to fetch comparison in focus engine: {e}")

            # Map recent metric changes from comparison data
            recent_metric_changes: Dict[str, Any] = {}
            if comparison_data and comparison_data.has_previous:
                for item in comparison_data.metrics:
                    recent_metric_changes[item.key] = item

            # Candidate pool for active goal
            candidates_defs = GOAL_FOCUS_CANDIDATES.get(goal_type, GOAL_FOCUS_CANDIDATES["GENERAL_PERFORMANCE"])

            scored_candidates: List[Dict[str, Any]] = []

            for cand in candidates_defs:
                m_key = cand["primary_metric_key"]
                goal_rel = cand["goal_relevance"]

                # 4a. Recent Change Score (from What Changed?)
                recent_change_score = 0.2  # default baseline
                change_item = recent_metric_changes.get(m_key)
                recent_change_display = None
                recent_obs_text = None

                if change_item:
                    recent_change_display = change_item.change_display
                    recent_obs_text = change_item.observation_text
                    if change_item.category == "NOTABLE_CHANGE":
                        recent_change_score = 1.0
                    elif change_item.category == "MODERATE_CHANGE":
                        recent_change_score = 0.65
                    elif change_item.direction in ["INCREASED", "DECREASED"]:
                        recent_change_score = 0.45
                    else:
                        recent_change_score = 0.25

                # 4b. History / Pattern Score (across recent 3-5 sessions)
                history_score = 0.4
                historical_values = []
                for a in analyses[:5]:
                    if m_key == "cadence" and a.cadence_spm:
                        historical_values.append(a.cadence_spm)
                    elif m_key == "symmetry" and a.left_right_symmetry_pct:
                        historical_values.append(a.left_right_symmetry_pct)
                    elif m_key == "trunk_lean" and a.trunk_lean_deg:
                        historical_values.append(a.trunk_lean_deg)
                    elif m_key == "vertical_movement" and a.relative_vertical_movement_proxy:
                        historical_values.append(a.relative_vertical_movement_proxy)

                if len(historical_values) >= 2:
                    val_range = max(historical_values) - min(historical_values)
                    # Significant historical variance indicates active adaptation area
                    if m_key == "cadence" and val_range >= 4.0:
                        history_score = 0.85
                    elif m_key == "symmetry" and val_range >= 3.0:
                        history_score = 0.85
                    elif m_key == "trunk_lean" and val_range >= 2.0:
                        history_score = 0.80
                    elif val_range > 0:
                        history_score = 0.60

                # 4c. Confidence & Video Quality Score
                conf_score = 0.85
                if latest_analysis.overall_confidence == "High":
                    conf_score = 1.0
                elif latest_analysis.overall_confidence == "Medium":
                    conf_score = 0.70
                elif latest_analysis.overall_confidence == "Low":
                    conf_score = 0.35

                # Weighted Priority Formula
                # 40% Goal Relevance + 30% Recent Change + 20% Historical Variance + 10% Confidence
                priority_score = (
                    (0.40 * goal_rel) +
                    (0.30 * recent_change_score) +
                    (0.20 * history_score) +
                    (0.10 * conf_score)
                )

                # Construct explainable reasoning bullets supported by real data
                reasoning_bullets: List[str] = [
                    f"Directly related to your current goal ({goal_meta['title']})"
                ]
                supporting_obs: List[str] = []

                if recent_change_display:
                    reasoning_bullets.append(
                        f"Recent session change detected ({recent_change_display} in your latest analysis)"
                    )
                if len(historical_values) >= 3:
                    reasoning_bullets.append(
                        f"Pattern evaluated across your {len(historical_values)} recent analyzed workouts"
                    )
                if conf_score >= 0.8:
                    reasoning_bullets.append("Underlying biomechanical tracking has high confidence")

                if recent_obs_text:
                    supporting_obs.append(recent_obs_text)

                scored_candidates.append({
                    "cand": cand,
                    "priority_score": round(priority_score, 3),
                    "confidence_score": conf_score,
                    "recent_change_score": recent_change_score,
                    "history_score": history_score,
                    "reasoning": reasoning_bullets,
                    "supporting_obs": supporting_obs
                })

            # Sort by priority score descending
            scored_candidates.sort(key=lambda x: x["priority_score"], reverse=True)

            top = scored_candidates[0]
            top_cand = top["cand"]
            top_score = top["priority_score"]

            # ── STATE 5: No Strong Focus State ───────────────────────────────
            # If all recent changes are tiny (<0.3) and history shows zero variation and score is low
            if top_score < 0.40:
                return PersonalFocusResponse(
                    state="NO_STRONG_FOCUS",
                    has_goal=True,
                    total_analyses=total_analyses,
                    goal=goal_meta,
                    focus=None,
                    headline="No Strong Focus Identified Yet",
                    message="Your recent running form metrics are steady and consistent with your baseline. MotionIQ will continue monitoring future sessions.",
                    action_cta=None
                )

            # Determine Confidence Rating (HIGH, MEDIUM, LOW)
            conf_rating: FocusConfidence = "HIGH" if (top_score >= 0.65 and top["confidence_score"] >= 0.75) else ("MEDIUM" if top_score >= 0.48 else "LOW")

            focus_item = FocusAreaItem(
                focus_type=top_cand["focus_type"],
                title=top_cand["title"],
                subtitle=top_cand["subtitle"],
                primary_metric_key=top_cand["primary_metric_key"],
                primary_metric_name=top_cand["primary_metric_name"],
                goal_type=goal_type,
                goal_title=goal_meta["title"],
                confidence=conf_rating,
                reasoning=top["reasoning"],
                supporting_observations=top["supporting_obs"],
                priority_score=top_score
            )

            return PersonalFocusResponse(
                state="ACTIVE_FOCUS",
                has_goal=True,
                total_analyses=total_analyses,
                goal=goal_meta,
                focus=focus_item,
                headline="Your Current Focus",
                message="Derived from your active goal, recent session changes, and historical consistency.",
                action_cta=None
            )

        finally:
            db.close()

personal_focus_engine = PersonalFocusEngine()
