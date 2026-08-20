import logging
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.db.models import Analysis, UserProfile
from app.api.schemas.recommendation import (
    PersonalizedRecommendationResponse, RecommendationItem,
    RecommendationCategory, RecommendationConfidence, RecommendationState, ActionCTA
)
from app.focus.focus_engine import personal_focus_engine
from app.comparison.comparison_engine import comparison_engine

logger = logging.getLogger(__name__)

# Actionable Recommendation Templates mapped to Focus Type
FOCUS_RECOMMENDATION_TEMPLATES: Dict[str, Dict[str, Any]] = {
    "CADENCE_CONSISTENCY": {
        "title": "Focus on Consistent Rhythm",
        "category": "CONSISTENCY",
        "action_suggestion": "During your next comfortable run, consider focusing on maintaining a steady rhythm rather than deliberately over-accelerating cadence.",
        "action_bullets": [
            "Focus on maintaining a comfortable, repeatable step turnover across your session.",
            "Keep training surface and target pace reasonably consistent for future comparisons.",
            "Recheck cadence metrics during a subsequent workout to observe pattern stability."
        ]
    },
    "STRIDE_RHYTHM": {
        "title": "Maintain Smooth Step Transitions",
        "category": "PRACTICE",
        "action_suggestion": "During your next workout, pay attention to fluid foot contacts and balanced ground contact time.",
        "action_bullets": [
            "Focus on quick, light foot turnover beneath your center of mass.",
            "Incorporate a brief rhythm-focused stride drill into your pre-run warm-up.",
            "Compare step duration in your next recorded session under similar pacing."
        ]
    },
    "BILATERAL_BALANCE": {
        "title": "Monitor Bilateral Movement Symmetry",
        "category": "OBSERVE",
        "action_suggestion": "During your next session, pay attention to maintaining a relaxed, balanced stride rhythm and observe whether left/right timing stabilizes naturally.",
        "action_bullets": [
            "Observe bilateral stride feel during the middle portion of your run.",
            "Incorporate gentle single-leg balance and core stability exercises into routine conditioning.",
            "Compare bilateral symmetry across similar terrain in upcoming sessions."
        ]
    },
    "STEP_TIMING_SYMMETRY": {
        "title": "Equalize Left/Right Ground Contact",
        "category": "PRACTICE",
        "action_suggestion": "Focus on smooth, even foot turnover without favoring one side during push-off or initial contact.",
        "action_bullets": [
            "Pay attention to even foot strike sound and feel on level ground.",
            "Maintain relaxed upper-body posture to support balanced pelvic rotation.",
            "Recheck step timing in a future session under similar surface conditions."
        ]
    },
    "TRUNK_POSTURE": {
        "title": "Maintain Natural Forward Inclination",
        "category": "PRACTICE",
        "action_suggestion": "During your next run, consider maintaining a comfortable, natural forward inclination originating from the ankles rather than bending from the waist.",
        "action_bullets": [
            "Allow forward inclination to adjust naturally with changes in running pace.",
            "Keep shoulders relaxed and gaze directed approximately 15-20 meters ahead.",
            "Record a side-view follow-up video under similar pacing to track trunk posture."
        ]
    },
    "FOOT_STRIKE_MECHANICS": {
        "title": "Observe Foot Landing Geometry",
        "category": "OBSERVE",
        "action_suggestion": "Focus on landing compliant feet close beneath your center of mass with a slightly flexed knee at initial ground contact.",
        "action_bullets": [
            "Focus on light, compliant landings rather than forcing a specific strike type.",
            "Pair with steady step cadence to reduce reaching ahead of your body.",
            "Re-evaluate foot placement during an upcoming run."
        ]
    },
    "ARM_CARRIAGE": {
        "title": "Coordinate Compact Arm Drive",
        "category": "PRACTICE",
        "action_suggestion": "Maintain a relaxed, 90-degree elbow bend with forward-and-back arm drive coordinated with step cadence.",
        "action_bullets": [
            "Avoid excessive cross-body arm swing that can induce rotational torque.",
            "Keep hands relaxed with thumbs gently resting on index fingers.",
            "Observe arm carriage symmetry in future side-view recordings."
        ]
    },
    "VERTICAL_OSCILLATION_CONTROL": {
        "title": "Channel Momentum Forward",
        "category": "PRACTICE",
        "action_suggestion": "Consider focusing on directing propulsion smoothly forward, minimizing excessive vertical bounce during stride transitions.",
        "action_bullets": [
            "Focus on fluid horizontal momentum throughout your stride cycle.",
            "Maintain relaxed arm drive coordinated with stride frequency.",
            "Compare vertical movement proxy in subsequent recordings."
        ]
    },
    "CADENCE_TURNOVER": {
        "title": "Optimize Step Turnover Pacing",
        "category": "CONSISTENCY",
        "action_suggestion": "During your next training run, focus on finding your optimal comfortable step turnover for your target pace.",
        "action_bullets": [
            "Allow cadence to vary naturally with terrain gradients and pace changes.",
            "Focus on relaxed hip extension during the flight phase.",
            "Recheck turnover consistency in your next logged analysis."
        ]
    },
    "POSTURE_ALIGNMENT": {
        "title": "Maintain Balanced Postural Alignment",
        "category": "OBSERVE",
        "action_suggestion": "Focus on tall, aligned running posture with gentle forward inclination originating from the ankles.",
        "action_bullets": [
            "Keep chest open and core lightly engaged to support efficient breathing.",
            "Avoid collapsing at the waist during later stages of longer runs.",
            "Track postural stability across consecutive workouts."
        ]
    },
    "GAIT_CONSISTENCY": {
        "title": "Build Multi-Session Consistency",
        "category": "CONSISTENCY",
        "action_suggestion": "Try to compare future sessions under similar pace, surface, and intensity conditions so changes are easier to interpret.",
        "action_bullets": [
            "Maintain consistent pacing across analyzed segments.",
            "Record videos at consistent camera distance and height.",
            "Observe whether kinematic parameters stabilize over multiple sessions."
        ]
    },
    "CADENCE_STABILITY": {
        "title": "Stabilize Cadence Across Fatigue States",
        "category": "CONSISTENCY",
        "action_suggestion": "Pay attention to maintaining step rhythm during the latter portions of your runs when fatigue typically sets in.",
        "action_bullets": [
            "Focus on light, active foot turnover during long or high-effort runs.",
            "Keep stride length manageable rather than overreaching when tired.",
            "Compare early vs late session recordings in future workouts."
        ]
    },
    "OVERALL_CADENCE_TURNOVER": {
        "title": "Maintain Steady Turnover Rhythm",
        "category": "CONSISTENCY",
        "action_suggestion": "Focus on maintaining an effortless, repeatable stride rhythm across varying workout segments.",
        "action_bullets": [
            "Allow cadence to match pace smoothly without forcing rigid numbers.",
            "Keep stride mechanics fluid and relaxed.",
            "Track progression in upcoming analyses."
        ]
    },
    "OVERALL_BILATERAL_BALANCE": {
        "title": "Promote Bilateral Kinematic Balance",
        "category": "OBSERVE",
        "action_suggestion": "Observe bilateral movement feel and symmetry across varying running surfaces.",
        "action_bullets": [
            "Focus on smooth, symmetrical ground contacts.",
            "Incorporate general lower-body mobility and core stability conditioning.",
            "Compare balance metrics in upcoming workouts."
        ]
    },
    "OVERALL_TRUNK_POSTURE": {
        "title": "Align Forward Running Posture",
        "category": "PRACTICE",
        "action_suggestion": "Focus on aligned, whole-body forward inclination during upcoming sessions.",
        "action_bullets": [
            "Maintain relaxed upper torso posture.",
            "Avoid backward leaning or excessive forward bending.",
            "Re-evaluate with side-view video tracking."
        ]
    }
}


class PersonalizedRecommendationEngine:
    """
    Synthesizes the runner's active Personal Goal, Personal Focus Area, What Changed? deltas,
    and running context to generate non-prescriptive, evidence-informed training suggestions.
    """

    def generate_recommendation(self, user_id: Optional[str] = None) -> PersonalizedRecommendationResponse:
        # 1. Obtain Personal Focus calculation
        focus_resp = personal_focus_engine.compute_personal_focus(user_id=user_id)

        # ── State 1: Zero Analyses ───────────────────────────────────────────
        if focus_resp.state == "INSUFFICIENT_DATA" or focus_resp.total_analyses == 0:
            return PersonalizedRecommendationResponse(
                state="INSUFFICIENT_DATA",
                has_goal=focus_resp.has_goal,
                total_analyses=0,
                goal=focus_resp.goal,
                focus_type=None,
                recommendation=None,
                headline="Build Your Baseline",
                message="MotionIQ needs more session data before it can generate a personalized recommendation. Continue recording sessions to establish your running profile.",
                action_cta=ActionCTA(label="Analyze Your First Run", target="upload")
            )

        # ── State 2: First Analysis (1 session recorded) ─────────────────────
        if focus_resp.state == "FIRST_ANALYSIS" or focus_resp.total_analyses == 1:
            return PersonalizedRecommendationResponse(
                state="FIRST_ANALYSIS",
                has_goal=focus_resp.has_goal,
                total_analyses=1,
                goal=focus_resp.goal,
                focus_type=None,
                recommendation=None,
                headline="Build Your Baseline",
                message="MotionIQ needs more session data before it can make a stronger personalized recommendation. For now, continue recording sessions under similar conditions and keep your goal selected.",
                action_cta=ActionCTA(label="Set Personal Goal", target="profile") if not focus_resp.has_goal else None
            )

        # ── State 3: Multiple Analyses but No Goal Set ───────────────────────
        if focus_resp.state == "NO_GOAL" or not focus_resp.has_goal:
            return PersonalizedRecommendationResponse(
                state="NO_GOAL",
                has_goal=False,
                total_analyses=focus_resp.total_analyses,
                goal=None,
                focus_type=None,
                recommendation=None,
                headline="Set a Personal Goal First",
                message="Your recommendations become more relevant when MotionIQ knows what you want to focus on.",
                action_cta=ActionCTA(label="Set Personal Goal", target="profile")
            )

        # ── State 4: No Strong Focus Identified ──────────────────────────────
        if focus_resp.state == "NO_STRONG_FOCUS" or not focus_resp.focus:
            return PersonalizedRecommendationResponse(
                state="NO_STRONG_FOCUS",
                has_goal=True,
                total_analyses=focus_resp.total_analyses,
                goal=focus_resp.goal,
                focus_type=None,
                recommendation=None,
                headline="Keep Observing",
                message="MotionIQ has not identified a strong personal focus yet. Continue recording comparable sessions to build a clearer personal pattern.",
                action_cta=None
            )

        # ── State 5: Active Focus -> Build Personalized Recommendation ───────
        focus = focus_resp.focus
        f_type = focus.focus_type
        g_title = focus.goal_title
        g_type = focus.goal_type

        # Inspect latest analysis for low video/pose confidence
        db: Session = SessionLocal()
        latest_analysis = None
        try:
            q = db.query(Analysis).filter(Analysis.status == "completed")
            if user_id:
                q = q.filter(Analysis.user_id == user_id)
            else:
                q = q.filter(Analysis.user_id == None)
            latest_analysis = q.order_by(Analysis.created_at.desc()).first()
        finally:
            db.close()

        # Check for low video confidence or poor suitability
        is_low_quality = False
        if latest_analysis and latest_analysis.overall_confidence == "Low":
            is_low_quality = True

        if is_low_quality:
            rec_item = RecommendationItem(
                title="Optimize Video Tracking for Reliable Insights",
                category="RECHECK",
                focus_type=f_type,
                focus_title=focus.title,
                goal_type=g_type,
                goal_title=g_title,
                action_suggestion="Your latest video tracking quality was limited. Consider recording a steady, side-view video with full body visibility for your next session.",
                action_bullets=[
                    "Position your camera perpendicular to your running path (sagittal side view).",
                    "Ensure full body from feet to head remains visible throughout the clip.",
                    "Perform your next recording in bright, even lighting."
                ],
                rationale=[
                    f"Matches your current goal ({g_title})",
                    f"Connected to your current focus ({focus.title})",
                    "Video tracking confidence was limited in your latest analysis"
                ],
                confidence="LOW",
                supporting_evidence=["Camera viewpoint or tracking quality was reduced during portions of the session."]
            )

            return PersonalizedRecommendationResponse(
                state="LOW_CONFIDENCE",
                has_goal=True,
                total_analyses=focus_resp.total_analyses,
                goal=focus_resp.goal,
                focus_type=f_type,
                recommendation=rec_item,
                headline="Personalized Training Suggestion",
                message="Based on your active goal and recent video tracking confidence.",
                action_cta=None
            )

        # Normal Active Recommendation
        template = FOCUS_RECOMMENDATION_TEMPLATES.get(
            f_type,
            FOCUS_RECOMMENDATION_TEMPLATES["CADENCE_CONSISTENCY"]
        )

        # Explainable Rationale
        rationale_bullets = [
            f"Matches your current goal ({g_title})",
            f"Related to your current focus ({focus.title})"
        ]
        if focus.reasoning and len(focus.reasoning) > 1:
            rationale_bullets.append(focus.reasoning[1])
        else:
            rationale_bullets.append("Supported by your recent session history")

        # Action bullets
        action_bullets = list(template["action_bullets"])

        # Check for context variation (e.g. surface or distance category)
        if latest_analysis and latest_analysis.raw_payload_json:
            ctx = latest_analysis.raw_payload_json.get("context", {})
            opt = ctx.get("optional", {})
            det = ctx.get("detected", {})
            surface = opt.get("running_surface") or det.get("surface", {}).get("value")
            if surface:
                action_bullets[1] = f"Keep surface ({surface}) and pacing reasonably consistent for future comparisons."

        rec_item = RecommendationItem(
            title=template["title"],
            category=template["category"],
            focus_type=f_type,
            focus_title=focus.title,
            goal_type=g_type,
            goal_title=g_title,
            action_suggestion=template["action_suggestion"],
            action_bullets=action_bullets,
            rationale=rationale_bullets,
            confidence=focus.confidence,
            supporting_evidence=focus.supporting_observations
        )

        return PersonalizedRecommendationResponse(
            state="ACTIVE_RECOMMENDATION",
            has_goal=True,
            total_analyses=focus_resp.total_analyses,
            goal=focus_resp.goal,
            focus_type=f_type,
            recommendation=rec_item,
            headline="Personalized Training Suggestion",
            message="Evidence-informed suggestion synthesized from your goal, focus area, and recent session changes.",
            action_cta=None
        )

personalized_recommendation_engine = PersonalizedRecommendationEngine()
