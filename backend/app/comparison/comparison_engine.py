import logging
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.db.models import Analysis, UserProfile
from app.api.schemas.goal import GOAL_CATALOG
from app.api.schemas.comparison import (
    AnalysisComparisonResponse, MetricComparisonItem, UserGoalContext,
    ComparisonDirection, ComparisonCategory
)

logger = logging.getLogger(__name__)

# Goal to relevant metric keys mapping
GOAL_METRIC_MAPPINGS: Dict[str, List[str]] = {
    "IMPROVE_CADENCE": ["cadence", "step_time", "stride_time"],
    "IMPROVE_SYMMETRY": ["symmetry", "step_time"],
    "IMPROVE_EFFICIENCY": ["vertical_movement", "cadence", "trunk_lean"],
    "IMPROVE_FORM": ["trunk_lean", "arm_swing", "foot_strike", "overstride"],
    "IMPROVE_CONSISTENCY": ["symmetry", "cadence", "step_time"],
    "GENERAL_PERFORMANCE": ["cadence", "symmetry", "trunk_lean", "vertical_movement"]
}


def _extract_metric_dict(raw_payload: Optional[Dict[str, Any]], record: Analysis) -> Dict[str, Any]:
    """Extracts raw numeric and categorical metrics from analysis payload or table columns."""
    result: Dict[str, Any] = {}
    
    # 1. Start from direct model columns
    if record.cadence_spm is not None:
        result["cadence"] = float(record.cadence_spm)
    if record.left_right_symmetry_pct is not None:
        result["symmetry"] = float(record.left_right_symmetry_pct)
    if record.trunk_lean_deg is not None:
        result["trunk_lean"] = float(record.trunk_lean_deg)
    if record.foot_strike_pattern:
        result["foot_strike"] = str(record.foot_strike_pattern)
    if record.overstride_risk:
        result["overstride"] = str(record.overstride_risk)
    if record.relative_vertical_movement_proxy is not None:
        result["vertical_movement"] = float(record.relative_vertical_movement_proxy)

    # 2. Enrich from raw_payload_json metrics array if present
    if raw_payload and isinstance(raw_payload.get("metrics"), list):
        for m in raw_payload["metrics"]:
            k = m.get("key")
            val_str = str(m.get("value", "")).strip()
            if not k:
                continue
            try:
                # Try numeric conversion
                if val_str.replace(".", "", 1).replace("-", "", 1).isdigit():
                    result[k] = float(val_str)
                else:
                    result[k] = val_str
            except (ValueError, TypeError):
                result[k] = val_str

    return result


class ComparisonEngine:
    """Computes session-over-session changes between the current analysis and the immediately previous analysis."""

    def compare_analyses(
        self,
        current_analysis_id: str,
        user_id: Optional[str] = None
    ) -> AnalysisComparisonResponse:
        db: Session = SessionLocal()
        try:
            # 1. Fetch current analysis
            curr_query = db.query(Analysis).filter(Analysis.id == current_analysis_id)
            if user_id:
                curr_query = curr_query.filter(Analysis.user_id == user_id)
            else:
                curr_query = curr_query.filter(Analysis.user_id == None)

            current_record = curr_query.first()
            if not current_record:
                # If demo session fallback
                if current_analysis_id == "demo-runner-session-001":
                    return AnalysisComparisonResponse(
                        analysis_id=current_analysis_id,
                        has_previous=False,
                        is_first_analysis=True,
                        comparison_summary="This is your first recorded analysis. MotionIQ will use this session as your personal baseline for future comparisons.",
                        metrics=[]
                    )
                raise ValueError("Analysis record not found or unauthorized access.")

            curr_created = current_record.created_at

            # 2. Fetch user's active personal goal
            user_goal_ctx: Optional[UserGoalContext] = None
            relevant_metric_keys: List[str] = []
            if user_id:
                profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
                if profile and profile.goal_type:
                    meta = GOAL_CATALOG.get(profile.goal_type, {
                        "title": profile.goal_type.replace("_", " ").title(),
                        "explanation": "Personal running focus."
                    })
                    user_goal_ctx = UserGoalContext(
                        type=profile.goal_type,
                        title=meta["title"],
                        description=profile.goal_description,
                        explanation=meta["explanation"]
                    )
                    relevant_metric_keys = GOAL_METRIC_MAPPINGS.get(profile.goal_type, [])

            # 3. Find immediately previous completed analysis for the same user
            prev_query = db.query(Analysis).filter(
                Analysis.id != current_analysis_id,
                Analysis.status == "completed"
            )
            if user_id:
                prev_query = prev_query.filter(Analysis.user_id == user_id)
            else:
                prev_query = prev_query.filter(Analysis.user_id == None)

            if curr_created:
                prev_query = prev_query.filter(Analysis.created_at < curr_created)

            previous_record = prev_query.order_by(Analysis.created_at.desc()).first()

            # 4. Handle First Analysis / No Previous Analysis Case
            if not previous_record:
                return AnalysisComparisonResponse(
                    analysis_id=current_analysis_id,
                    has_previous=False,
                    is_first_analysis=True,
                    previous_analysis_id=None,
                    current_created_at=curr_created.isoformat() if curr_created else None,
                    user_goal=user_goal_ctx,
                    comparison_summary="This is your first recorded analysis. MotionIQ will use this session as your personal baseline for future comparisons.",
                    metrics=[]
                )

            # 5. Extract metrics from both sessions
            curr_metrics = _extract_metric_dict(current_record.raw_payload_json, current_record)
            prev_metrics = _extract_metric_dict(previous_record.raw_payload_json, previous_record)

            metric_comparisons: List[MetricComparisonItem] = []
            summary_sentences: List[str] = []

            # ── 5a. Cadence Comparison ───────────────────────────────────────
            if "cadence" in curr_metrics and "cadence" in prev_metrics and isinstance(curr_metrics["cadence"], (int, float)) and isinstance(prev_metrics["cadence"], (int, float)):
                c_val = float(curr_metrics["cadence"])
                p_val = float(prev_metrics["cadence"])
                diff = c_val - p_val
                pct = ((diff / p_val) * 100) if p_val > 0 else None
                
                direction: ComparisonDirection = "INCREASED" if diff >= 0.5 else ("DECREASED" if diff <= -0.5 else "UNCHANGED")
                category: ComparisonCategory = "NOTABLE_CHANGE" if abs(diff) >= 3.0 else ("MODERATE_CHANGE" if abs(diff) >= 1.0 else "LITTLE_CHANGE")
                
                sign = "+" if diff >= 0 else ""
                change_str = f"{sign}{round(diff)} SPM"
                obs = f"Cadence {'increased' if diff > 0 else 'decreased' if diff < 0 else 'remained steady'} by {abs(round(diff))} SPM compared with your previous session."
                
                if category in ["NOTABLE_CHANGE", "MODERATE_CHANGE"]:
                    summary_sentences.append(f"Cadence {'increased' if diff > 0 else 'decreased'} by {abs(round(diff))} SPM ({round(p_val)} → {round(c_val)} SPM)")

                metric_comparisons.append(MetricComparisonItem(
                    key="cadence",
                    name="Cadence",
                    previous_value=round(p_val),
                    current_value=round(c_val),
                    previous_display=f"{round(p_val)} SPM",
                    current_display=f"{round(c_val)} SPM",
                    absolute_change=round(diff, 1),
                    percentage_change=round(pct, 1) if pct is not None else None,
                    change_display=change_str,
                    unit="SPM",
                    direction=direction,
                    category=category,
                    goal_relevant="cadence" in relevant_metric_keys,
                    observation_text=obs
                ))

            # ── 5b. Movement Symmetry Comparison ─────────────────────────────
            if "symmetry" in curr_metrics and "symmetry" in prev_metrics and isinstance(curr_metrics["symmetry"], (int, float)) and isinstance(prev_metrics["symmetry"], (int, float)):
                c_val = float(curr_metrics["symmetry"])
                p_val = float(prev_metrics["symmetry"])
                diff = c_val - p_val
                
                direction: ComparisonDirection = "INCREASED" if diff >= 0.3 else ("DECREASED" if diff <= -0.3 else "UNCHANGED")
                category: ComparisonCategory = "NOTABLE_CHANGE" if abs(diff) >= 2.0 else ("MODERATE_CHANGE" if abs(diff) >= 0.5 else "LITTLE_CHANGE")
                
                sign = "+" if diff >= 0 else ""
                change_str = f"{sign}{diff:.1f} percentage points"
                obs = f"Bilateral movement balance shifted by {abs(diff):.1f} percentage points."
                
                if category in ["NOTABLE_CHANGE", "MODERATE_CHANGE"]:
                    summary_sentences.append(f"bilateral movement symmetry shifted by {sign}{diff:.1f} percentage points ({p_val:.1f}% → {c_val:.1f}%)")

                metric_comparisons.append(MetricComparisonItem(
                    key="symmetry",
                    name="Movement Symmetry",
                    previous_value=round(p_val, 1),
                    current_value=round(c_val, 1),
                    previous_display=f"{p_val:.1f}%",
                    current_display=f"{c_val:.1f}%",
                    absolute_change=round(diff, 2),
                    percentage_change=None, # Symmetry deltas are expressed in percentage points
                    change_display=change_str,
                    unit="percentage points",
                    direction=direction,
                    category=category,
                    goal_relevant="symmetry" in relevant_metric_keys,
                    observation_text=obs
                ))

            # ── 5c. Trunk Lean Comparison ────────────────────────────────────
            if "trunk_lean" in curr_metrics and "trunk_lean" in prev_metrics and isinstance(curr_metrics["trunk_lean"], (int, float)) and isinstance(prev_metrics["trunk_lean"], (int, float)):
                c_val = float(curr_metrics["trunk_lean"])
                p_val = float(prev_metrics["trunk_lean"])
                diff = c_val - p_val
                
                direction: ComparisonDirection = "INCREASED" if diff >= 0.3 else ("DECREASED" if diff <= -0.3 else "UNCHANGED")
                category: ComparisonCategory = "NOTABLE_CHANGE" if abs(diff) >= 1.5 else ("MODERATE_CHANGE" if abs(diff) >= 0.4 else "LITTLE_CHANGE")
                
                sign = "+" if diff >= 0 else ""
                change_str = f"{sign}{diff:.1f}°"
                obs = f"Forward trunk inclination changed by {abs(diff):.1f}°."
                
                if category == "NOTABLE_CHANGE":
                    summary_sentences.append(f"forward trunk lean changed by {sign}{diff:.1f}° ({p_val:.1f}° → {c_val:.1f}°)")

                metric_comparisons.append(MetricComparisonItem(
                    key="trunk_lean",
                    name="Trunk Forward Lean",
                    previous_value=round(p_val, 1),
                    current_value=round(c_val, 1),
                    previous_display=f"{p_val:.1f}°",
                    current_display=f"{c_val:.1f}°",
                    absolute_change=round(diff, 2),
                    percentage_change=None,
                    change_display=change_str,
                    unit="°",
                    direction=direction,
                    category=category,
                    goal_relevant="trunk_lean" in relevant_metric_keys,
                    observation_text=obs
                ))

            # ── 5d. Step & Stride Duration Comparison ────────────────────────
            if "step_time" in curr_metrics and "step_time" in prev_metrics and isinstance(curr_metrics["step_time"], (int, float)) and isinstance(prev_metrics["step_time"], (int, float)):
                c_val = float(curr_metrics["step_time"])
                p_val = float(prev_metrics["step_time"])
                diff_ms = (c_val - p_val) * 1000
                sign = "+" if diff_ms >= 0 else ""
                
                metric_comparisons.append(MetricComparisonItem(
                    key="step_time",
                    name="Mean Step Duration",
                    previous_value=round(p_val, 3),
                    current_value=round(c_val, 3),
                    previous_display=f"{p_val*1000:.0f} ms",
                    current_display=f"{c_val*1000:.0f} ms",
                    absolute_change=round(diff_ms, 1),
                    percentage_change=round(((c_val - p_val) / p_val) * 100, 1) if p_val > 0 else None,
                    change_display=f"{sign}{diff_ms:.0f} ms",
                    unit="ms",
                    direction="INCREASED" if diff_ms >= 5 else ("DECREASED" if diff_ms <= -5 else "UNCHANGED"),
                    category="MODERATE_CHANGE" if abs(diff_ms) >= 10 else "LITTLE_CHANGE",
                    goal_relevant="step_time" in relevant_metric_keys,
                    observation_text=f"Mean ground step duration changed by {abs(diff_ms):.0f} ms."
                ))

            # ── 5e. Relative Vertical Movement Proxy ─────────────────────────
            if "vertical_movement" in curr_metrics and "vertical_movement" in prev_metrics and isinstance(curr_metrics["vertical_movement"], (int, float)) and isinstance(prev_metrics["vertical_movement"], (int, float)):
                c_val = float(curr_metrics["vertical_movement"])
                p_val = float(prev_metrics["vertical_movement"])
                diff = c_val - p_val
                sign = "+" if diff >= 0 else ""

                metric_comparisons.append(MetricComparisonItem(
                    key="vertical_movement",
                    name="Vertical Movement Proxy",
                    previous_value=round(p_val, 3),
                    current_value=round(c_val, 3),
                    previous_display=f"{p_val:.3f}",
                    current_display=f"{c_val:.3f}",
                    absolute_change=round(diff, 3),
                    percentage_change=round(((diff) / p_val) * 100, 1) if p_val > 0 else None,
                    change_display=f"{sign}{diff:.3f}",
                    unit="ratio",
                    direction="INCREASED" if diff >= 0.005 else ("DECREASED" if diff <= -0.005 else "UNCHANGED"),
                    category="MODERATE_CHANGE" if abs(diff) >= 0.015 else "LITTLE_CHANGE",
                    goal_relevant="vertical_movement" in relevant_metric_keys,
                    observation_text=f"Relative vertical displacement proxy shifted by {abs(diff):.3f}."
                ))

            # ── 5f. Foot Strike Categorical Comparison ───────────────────────
            if "foot_strike" in curr_metrics and "foot_strike" in prev_metrics:
                c_str = str(curr_metrics["foot_strike"])
                p_str = str(prev_metrics["foot_strike"])
                changed = (c_str.lower() != p_str.lower())

                metric_comparisons.append(MetricComparisonItem(
                    key="foot_strike",
                    name="Foot Strike Pattern",
                    previous_value=p_str,
                    current_value=c_str,
                    previous_display=p_str,
                    current_display=c_str,
                    absolute_change=None,
                    percentage_change=None,
                    change_display="Pattern Shift" if changed else "Consistent",
                    unit="pattern",
                    direction="CHANGED" if changed else "UNCHANGED",
                    category="NOTABLE_CHANGE" if changed else "LITTLE_CHANGE",
                    goal_relevant="foot_strike" in relevant_metric_keys,
                    observation_text=f"Foot strike observed as {c_str} (previously {p_str})." if changed else f"Foot strike remained consistently observed as {c_str}."
                ))

            # Sort comparisons: Goal-relevant metrics first, then notable changes
            metric_comparisons.sort(
                key=lambda x: (
                    not x.goal_relevant,
                    0 if x.category == "NOTABLE_CHANGE" else 1 if x.category == "MODERATE_CHANGE" else 2
                )
            )

            # Build factual overall summary
            if summary_sentences:
                comp_summary = "Compared with your previous analysis: " + ", while ".join(summary_sentences) + "."
            else:
                comp_summary = "Kinematic measurements remained steady across consecutive sessions within typical observational variance."

            return AnalysisComparisonResponse(
                analysis_id=current_analysis_id,
                has_previous=True,
                is_first_analysis=False,
                previous_analysis_id=previous_record.id,
                previous_created_at=previous_record.created_at.isoformat() if previous_record.created_at else None,
                current_created_at=curr_created.isoformat() if curr_created else None,
                user_goal=user_goal_ctx,
                comparison_summary=comp_summary,
                metrics=metric_comparisons
            )

        finally:
            db.close()

comparison_engine = ComparisonEngine()
