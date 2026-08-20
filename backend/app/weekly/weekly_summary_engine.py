import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.db.models import Analysis, UserProfile
from app.api.schemas.goal import GOAL_CATALOG
from app.api.schemas.weekly_summary import (
    PersonalizedWeeklySummaryResponse, WeeklyPeriod, WeeklyMetricItem,
    WeeklyHighlight, WeeklySummaryState, ActionCTA
)
from app.focus.focus_engine import personal_focus_engine
from app.recommendations.recommendation_engine import personalized_recommendation_engine
from app.milestones.milestone_service import milestone_service

logger = logging.getLogger(__name__)

def get_week_bounds(offset: int = 0) -> tuple[datetime, datetime, str, str, str]:
    """
    Calculates Monday 00:00:00 to Sunday 23:59:59 UTC for the given week offset.
    offset = 0 -> current week
    offset = 1 -> previous week
    """
    now = datetime.now(timezone.utc)
    # weekday(): Monday is 0, Sunday is 6
    days_since_monday = now.weekday()
    current_monday = (now - timedelta(days=days_since_monday)).replace(hour=0, minute=0, second=0, microsecond=0)
    
    target_monday = current_monday - timedelta(weeks=offset)
    target_sunday = target_monday + timedelta(days=6, hours=23, minutes=59, seconds=59)
    
    start_str = target_monday.strftime("%Y-%m-%d")
    end_str = target_sunday.strftime("%Y-%m-%d")
    
    m_name = target_monday.strftime("%b %d")
    s_name = target_sunday.strftime("%b %d")
    label_prefix = "This Week" if offset == 0 else ("Previous Week" if offset == 1 else f"{offset} Weeks Ago")
    label = f"{label_prefix} ({m_name} – {s_name})"
    
    return target_monday, target_sunday, start_str, end_str, label


class WeeklySummaryEngine:
    """
    Synthesizes the authenticated runner's weekly running activity,
    active Personal Goal, Personal Focus Area, What Changed? deltas,
    milestones, and recommendations into a concise weekly overview.
    """

    def generate_weekly_summary(self, user_id: Optional[str] = None, week_offset: int = 0) -> PersonalizedWeeklySummaryResponse:
        week_start, week_end, start_str, end_str, week_label = get_week_bounds(week_offset)

        period = WeeklyPeriod(
            start_date=start_str,
            end_date=end_str,
            label=week_label,
            week_offset=week_offset
        )

        db: Session = SessionLocal()
        try:
            # 1. Fetch user profile and active goal
            user_profile = None
            goal_meta: Optional[Dict[str, str]] = None
            if user_id:
                user_profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
                if user_profile and user_profile.goal_type:
                    gt = user_profile.goal_type
                    cat = GOAL_CATALOG.get(gt, {
                        "title": gt.replace("_", " ").title(),
                        "explanation": "Personal running goal."
                    })
                    goal_meta = {
                        "type": gt,
                        "title": cat["title"],
                        "description": user_profile.goal_description or "",
                        "explanation": cat["explanation"]
                    }

            # 2. Fetch completed analyses for this user within this week
            q = db.query(Analysis).filter(
                Analysis.status == "completed",
                Analysis.created_at >= week_start,
                Analysis.created_at <= week_end
            )
            if user_id:
                q = q.filter(Analysis.user_id == user_id)
            else:
                q = q.filter(Analysis.user_id == None)

            week_analyses = q.order_by(Analysis.created_at.asc()).all()
            total_sessions = len(week_analyses)

            # 3. Pull Focus Area & Recommendation from existing engines
            focus_resp = personal_focus_engine.compute_personal_focus(user_id=user_id)
            focus_dict = None
            if focus_resp.focus:
                focus_dict = {
                    "focus_type": focus_resp.focus.focus_type,
                    "title": focus_resp.focus.title,
                    "subtitle": focus_resp.focus.subtitle,
                    "confidence": focus_resp.focus.confidence
                }

            rec_resp = personalized_recommendation_engine.generate_recommendation(user_id=user_id)
            rec_dict = None
            if rec_resp.recommendation:
                rec_dict = {
                    "title": rec_resp.recommendation.title,
                    "category": rec_resp.recommendation.category,
                    "action_suggestion": rec_resp.recommendation.action_suggestion,
                    "action_bullets": rec_resp.recommendation.action_bullets,
                    "confidence": rec_resp.recommendation.confidence
                }

            # 4. Check for milestones achieved in this week's analyses
            milestone_dict = None
            try:
                all_user_q = db.query(Analysis).filter(Analysis.status == "completed")
                if user_id:
                    all_user_q = all_user_q.filter(Analysis.user_id == user_id)
                else:
                    all_user_q = all_user_q.filter(Analysis.user_id == None)
                all_user_analyses = all_user_q.all()

                raw_payloads = [a.raw_payload_json for a in all_user_analyses if a.raw_payload_json]
                milestones_report = milestone_service.calculate_milestones(raw_payloads, is_demo=False)
                week_analysis_ids = {a.id for a in week_analyses}
                
                # Check if any unlocked milestone belongs to this week
                for m in milestones_report.milestones:
                    if m.unlocked and m.analysis_id in week_analysis_ids:
                        milestone_dict = {
                            "title": m.title,
                            "category": m.category,
                            "value_display": m.value_display,
                            "description": m.description
                        }
                        break
            except Exception as e:
                logger.warning(f"Could not calculate weekly milestone: {e}")

            # ── STATE 1: Zero Sessions in this week ───────────────────────────
            if total_sessions == 0:
                goal_msg = f" Your current goal is {goal_meta['title']}." if goal_meta else " Set a personal goal to customize your weekly targets."
                return PersonalizedWeeklySummaryResponse(
                    period=period,
                    state="EMPTY_WEEK",
                    total_sessions=0,
                    goal=goal_meta,
                    focus=focus_dict,
                    highlight=None,
                    metrics=[],
                    changes_summary=None,
                    milestone=None,
                    recommendation=rec_dict,
                    insight=f"No analyzed sessions recorded during this week.{goal_msg} Complete a video or live analysis to build your weekly progress view.",
                    context_notes=[],
                    has_previous_week=True,
                    action_cta=ActionCTA(label="Analyze a Run", target="upload")
                )

            # ── STATE 2: Exactly 1 Session in this week ───────────────────────
            if total_sessions == 1:
                single = week_analyses[0]
                metrics_list = []
                if single.cadence_spm:
                    metrics_list.append(WeeklyMetricItem(
                        key="cadence", name="Cadence", value_display=f"{round(single.cadence_spm)}",
                        unit="SPM", change_display=None, is_percentage_points=False
                    ))
                if single.left_right_symmetry_pct:
                    metrics_list.append(WeeklyMetricItem(
                        key="symmetry", name="Bilateral Symmetry", value_display=f"{round(single.left_right_symmetry_pct, 1)}%",
                        unit="%", change_display=None, is_percentage_points=True
                    ))
                if single.trunk_lean_deg:
                    metrics_list.append(WeeklyMetricItem(
                        key="trunk_lean", name="Trunk Forward Lean", value_display=f"{round(single.trunk_lean_deg, 1)}°",
                        unit="°", change_display=None, is_percentage_points=False
                    ))

                hl = WeeklyHighlight(
                    headline="Weekly Session Recorded",
                    description=f"You logged 1 analyzed session this week with a cadence of {round(single.cadence_spm) if single.cadence_spm else '--'} SPM.",
                    badge="Activity"
                )

                return PersonalizedWeeklySummaryResponse(
                    period=period,
                    state="ONE_SESSION",
                    total_sessions=1,
                    goal=goal_meta,
                    focus=focus_dict,
                    highlight=hl,
                    metrics=metrics_list,
                    changes_summary="1 session recorded this week. Additional sessions will build weekly trend insights.",
                    milestone=milestone_dict,
                    recommendation=rec_dict,
                    insight="You completed 1 analyzed workout this week. Keep recording subsequent runs under similar conditions to identify weekly biomechanical patterns.",
                    context_notes=[],
                    has_previous_week=True,
                    action_cta=None
                )

            # ── STATE 3: Multiple Sessions in this week (>= 2) ────────────────
            first_session = week_analyses[0]
            last_session = week_analyses[-1]

            cadences = [a.cadence_spm for a in week_analyses if a.cadence_spm]
            symmetries = [a.left_right_symmetry_pct for a in week_analyses if a.left_right_symmetry_pct]
            trunk_leans = [a.trunk_lean_deg for a in week_analyses if a.trunk_lean_deg]

            metrics_list = []
            changes_bullets = []

            # 3a. Cadence summary
            if cadences:
                avg_cad = sum(cadences) / len(cadences)
                cad_delta = None
                if first_session.cadence_spm and last_session.cadence_spm:
                    diff = last_session.cadence_spm - first_session.cadence_spm
                    if abs(diff) >= 1.0:
                        sign = "+" if diff > 0 else ""
                        cad_delta = f"{sign}{round(diff)} SPM ({round(first_session.cadence_spm)} → {round(last_session.cadence_spm)} SPM)"
                        changes_bullets.append(f"Cadence changed by {cad_delta}")
                    else:
                        cad_delta = "Stable (±0 SPM)"
                        changes_bullets.append("Cadence remained steady across sessions")

                metrics_list.append(WeeklyMetricItem(
                    key="cadence", name="Cadence (Avg)", value_display=f"{round(avg_cad)}",
                    unit="SPM", change_display=cad_delta, is_percentage_points=False
                ))

            # 3b. Symmetry summary (percentage points!)
            if symmetries:
                avg_sym = sum(symmetries) / len(symmetries)
                sym_delta = None
                if first_session.left_right_symmetry_pct and last_session.left_right_symmetry_pct:
                    diff = last_session.left_right_symmetry_pct - first_session.left_right_symmetry_pct
                    if abs(diff) >= 0.5:
                        sign = "+" if diff > 0 else ""
                        sym_delta = f"{sign}{round(diff, 1)} percentage points"
                        changes_bullets.append(f"Bilateral symmetry shifted {sym_delta}")
                    else:
                        sym_delta = "Stable (±0 pts)"
                        changes_bullets.append("Bilateral symmetry remained consistent")

                metrics_list.append(WeeklyMetricItem(
                    key="symmetry", name="Bilateral Symmetry (Avg)", value_display=f"{round(avg_sym, 1)}%",
                    unit="%", change_display=sym_delta, is_percentage_points=True
                ))

            # 3c. Trunk Lean summary
            if trunk_leans:
                avg_trunk = sum(trunk_leans) / len(trunk_leans)
                trunk_delta = None
                if first_session.trunk_lean_deg and last_session.trunk_lean_deg:
                    diff = last_session.trunk_lean_deg - first_session.trunk_lean_deg
                    if abs(diff) >= 0.5:
                        sign = "+" if diff > 0 else ""
                        trunk_delta = f"{sign}{round(diff, 1)}°"
                    else:
                        trunk_delta = "Stable (±0°)"

                metrics_list.append(WeeklyMetricItem(
                    key="trunk_lean", name="Trunk Lean (Avg)", value_display=f"{round(avg_trunk, 1)}°",
                    unit="°", change_display=trunk_delta, is_percentage_points=False
                ))

            # 3d. Check Context Variations (Surface / Pace / Intensity)
            context_notes = []
            surfaces = set()
            paces = set()
            for a in week_analyses:
                if a.raw_payload_json:
                    c = a.raw_payload_json.get("context", {})
                    surf = c.get("optional", {}).get("running_surface") or c.get("detected", {}).get("surface", {}).get("value")
                    pace = c.get("optional", {}).get("known_pace") or c.get("detected", {}).get("running_pace_status", {}).get("value")
                    if surf: surfaces.add(surf)
                    if pace: paces.add(pace)

            if len(surfaces) > 1:
                context_notes.append(f"Sessions were conducted on different surfaces ({', '.join(surfaces)}). Surface variations can naturally influence stride metrics.")
            if len(paces) > 1:
                context_notes.append(f"Different pacing intensities were detected ({', '.join(paces)}). Consider comparing sessions with matching effort.")

            # 3e. Determine Primary Weekly Highlight
            hl_title = "Consistent Weekly Training"
            hl_desc = f"You completed {total_sessions} analyzed sessions this week."
            hl_badge = "Activity"

            if cadences and first_session.cadence_spm and last_session.cadence_spm and abs(last_session.cadence_spm - first_session.cadence_spm) >= 2.0:
                diff = last_session.cadence_spm - first_session.cadence_spm
                hl_title = "Cadence Progression"
                hl_desc = f"Cadence shifted from {round(first_session.cadence_spm)} to {round(last_session.cadence_spm)} SPM across your weekly sessions."
                hl_badge = "Progress"
            elif symmetries and first_session.left_right_symmetry_pct and last_session.left_right_symmetry_pct and abs(last_session.left_right_symmetry_pct - first_session.left_right_symmetry_pct) >= 2.0:
                diff = last_session.left_right_symmetry_pct - first_session.left_right_symmetry_pct
                hl_title = "Symmetry Movement Pattern"
                hl_desc = f"Bilateral balance shifted by {round(diff, 1)} percentage points across analyzed sessions."
                hl_badge = "Balance"
            elif total_sessions >= 3:
                hl_title = "High Session Consistency"
                hl_desc = f"You logged {total_sessions} completed workouts this week with reproducible form metrics."
                hl_badge = "Consistency"

            highlight = WeeklyHighlight(headline=hl_title, description=hl_desc, badge=hl_badge)

            # 3f. Narrative Insight
            changes_str = ". ".join(changes_bullets) if changes_bullets else "Form metrics remained steady."
            insight = f"You completed {total_sessions} analyzed sessions during this week. {changes_str}."

            return PersonalizedWeeklySummaryResponse(
                period=period,
                state="ACTIVE_SUMMARY",
                total_sessions=total_sessions,
                goal=goal_meta,
                focus=focus_dict,
                highlight=highlight,
                metrics=metrics_list,
                changes_summary=changes_str,
                milestone=milestone_dict,
                recommendation=rec_dict,
                insight=insight,
                context_notes=context_notes,
                has_previous_week=True,
                action_cta=None
            )

        finally:
            db.close()

weekly_summary_engine = WeeklySummaryEngine()
