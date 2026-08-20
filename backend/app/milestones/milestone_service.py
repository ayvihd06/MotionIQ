from typing import List, Dict, Any, Optional
from datetime import datetime

class MilestoneService:
    """
    Computes personalized running biomechanics milestones strictly from the authenticated runner's historical sessions.
    Enforces user data isolation, non-diagnostic safety lexicon, and accurate distinction between percentage points and percent change.
    """

    @staticmethod
    def calculate_milestones(analyses: List[Dict[str, Any]], is_demo: bool = False) -> Dict[str, Any]:
        """
        Calculates all personal milestones for a user given their full analysis history.
        """
        if not analyses:
            return {
                "total_analyses": 0,
                "has_milestones": False,
                "is_demo": is_demo,
                "empty_state": {
                    "title": "Your Personal Milestones",
                    "subtitle": "You're just getting started.",
                    "message": "Complete more analyses to unlock milestones such as Personal Best Symmetry, Highest Cadence, Biggest Improvement, Most Consistent Session, and Analysis Streaks.",
                    "action_label": "Analyze Your First Run"
                },
                "milestones": [],
                "recent_achievements": []
            }

        # Filter out failed/invalid records and sort chronologically (oldest -> newest)
        valid_analyses = [
            a for a in analyses
            if (a.get("status") in ("completed", None))
        ]

        if not valid_analyses:
            return {
                "total_analyses": 0,
                "has_milestones": False,
                "is_demo": is_demo,
                "empty_state": {
                    "title": "Your Personal Milestones",
                    "subtitle": "No completed sessions yet.",
                    "message": "Complete your first running session to begin establishing personal milestones.",
                    "action_label": "Analyze Your First Run"
                },
                "milestones": [],
                "recent_achievements": []
            }

        # Sort chronologically
        sorted_analyses = sorted(
            valid_analyses,
            key=lambda a: a.get("created_at") or ""
        )

        total_count = len(sorted_analyses)
        milestones = []
        recent_achievements = []

        # -------------------------------------------------------------
        # A. BEST SYMMETRY
        # -------------------------------------------------------------
        symmetry_progression = []
        current_max_symm = -1.0
        best_symm_record = None
        prev_best_symm = None

        for a in sorted_analyses:
            symm = a.get("left_right_symmetry_pct")
            if symm is not None and symm > 0:
                symm_val = float(symm)
                if symm_val > current_max_symm:
                    if best_symm_record is not None:
                        prev_best_symm = current_max_symm
                    current_max_symm = symm_val
                    best_symm_record = a
                    symmetry_progression.append({
                        "analysis_id": a.get("id") or a.get("analysis_id"),
                        "symmetry": symm_val,
                        "achieved_at": a.get("created_at")
                    })

        if best_symm_record and current_max_symm > 0:
            symm_delta = round(current_max_symm - prev_best_symm, 1) if prev_best_symm is not None else None
            milestones.append({
                "type": "best_symmetry",
                "title": "Best Symmetry",
                "icon": "trophy",
                "value": round(current_max_symm, 1),
                "unit": "%",
                "label": "Personal Best",
                "metric_name": "Bilateral Step Balance",
                "analysis_id": best_symm_record.get("id") or best_symm_record.get("analysis_id"),
                "achieved_at": best_symm_record.get("created_at"),
                "previous_value": round(prev_best_symm, 1) if prev_best_symm is not None else None,
                "improvement_delta": symm_delta,
                "improvement_unit": "percentage points",
                "description": "Your highest recorded bilateral movement symmetry score."
            })
        else:
            milestones.append({
                "type": "best_symmetry",
                "title": "Best Symmetry",
                "icon": "trophy",
                "value": None,
                "unit": "%",
                "label": "Not enough data yet",
                "metric_name": "Bilateral Step Balance",
                "description": "Requires at least one valid bilateral symmetry observation."
            })

        # -------------------------------------------------------------
        # B. HIGHEST CADENCE
        # -------------------------------------------------------------
        current_max_cadence = -1.0
        best_cadence_record = None
        prev_best_cadence = None

        for a in sorted_analyses:
            cad = a.get("cadence_spm")
            if cad is not None and 100 <= float(cad) <= 260:
                cad_val = float(cad)
                if cad_val > current_max_cadence:
                    if best_cadence_record is not None:
                        prev_best_cadence = current_max_cadence
                    current_max_cadence = cad_val
                    best_cadence_record = a

        if best_cadence_record and current_max_cadence > 0:
            cad_delta = round(current_max_cadence - prev_best_cadence, 1) if prev_best_cadence is not None else None
            milestones.append({
                "type": "highest_cadence",
                "title": "Highest Cadence",
                "icon": "zap",
                "value": round(current_max_cadence, 1),
                "unit": "SPM",
                "label": "Personal Best",
                "metric_name": "Step Cadence",
                "analysis_id": best_cadence_record.get("id") or best_cadence_record.get("analysis_id"),
                "achieved_at": best_cadence_record.get("created_at"),
                "previous_value": round(prev_best_cadence, 1) if prev_best_cadence is not None else None,
                "improvement_delta": cad_delta,
                "improvement_unit": "SPM",
                "description": "Your highest recorded running step cadence."
            })
        else:
            milestones.append({
                "type": "highest_cadence",
                "title": "Highest Cadence",
                "icon": "zap",
                "value": None,
                "unit": "SPM",
                "label": "Not enough data yet",
                "metric_name": "Step Cadence",
                "description": "Requires at least one valid cadence measurement."
            })

        # -------------------------------------------------------------
        # C. BEST FORM CONSISTENCY
        # -------------------------------------------------------------
        current_max_consistency = -1.0
        best_consistency_record = None
        prev_best_consistency = None

        for a in sorted_analyses:
            cons = a.get("form_consistency_score")
            if cons is None:
                summary = a.get("overall_summary") or {}
                cons = summary.get("form_consistency_score")
            if cons is not None and float(cons) > 0:
                cons_val = float(cons)
                if cons_val > current_max_consistency:
                    if best_consistency_record is not None:
                        prev_best_consistency = current_max_consistency
                    current_max_consistency = cons_val
                    best_consistency_record = a

        if best_consistency_record and current_max_consistency > 0:
            cons_delta = round(current_max_consistency - prev_best_consistency, 1) if prev_best_consistency is not None else None
            milestones.append({
                "type": "best_consistency",
                "title": "Most Consistent Session",
                "icon": "target",
                "value": round(current_max_consistency, 1),
                "unit": "%",
                "label": "Personal Best",
                "metric_name": "Form Consistency",
                "analysis_id": best_consistency_record.get("id") or best_consistency_record.get("analysis_id"),
                "achieved_at": best_consistency_record.get("created_at"),
                "previous_value": round(prev_best_consistency, 1) if prev_best_consistency is not None else None,
                "improvement_delta": cons_delta,
                "improvement_unit": "percentage points",
                "description": "Your highest recorded multi-metric form consistency index."
            })
        else:
            milestones.append({
                "type": "best_consistency",
                "title": "Most Consistent Session",
                "icon": "target",
                "value": None,
                "unit": "%",
                "label": "Not enough data yet",
                "metric_name": "Form Consistency",
                "description": "Requires form consistency evaluation across historical sessions."
            })

        # -------------------------------------------------------------
        # D. BIGGEST IMPROVEMENT
        # -------------------------------------------------------------
        biggest_improvement = None
        max_delta = 0.0

        if total_count >= 2:
            for i in range(1, total_count):
                curr = sorted_analyses[i]
                prev = sorted_analyses[i - 1]

                # 1. Symmetry Improvement (percentage points)
                c_symm = curr.get("left_right_symmetry_pct")
                p_symm = prev.get("left_right_symmetry_pct")
                if c_symm is not None and p_symm is not None:
                    delta_symm = float(c_symm) - float(p_symm)
                    if delta_symm > max_delta:
                        max_delta = delta_symm
                        biggest_improvement = {
                            "type": "biggest_improvement",
                            "title": "Biggest Improvement",
                            "icon": "trending-up",
                            "value": round(delta_symm, 1),
                            "unit": "percentage points",
                            "label": f"+{round(delta_symm, 1)} percentage points",
                            "metric_name": "Bilateral Step Balance",
                            "analysis_id": curr.get("id") or curr.get("analysis_id"),
                            "comparison_analysis_id": prev.get("id") or prev.get("analysis_id"),
                            "achieved_at": curr.get("created_at"),
                            "previous_value": round(float(p_symm), 1),
                            "current_value": round(float(c_symm), 1),
                            "description": f"Largest positive single-session change (+{round(delta_symm, 1)} percentage points) compared with your previous session."
                        }

        if biggest_improvement:
            milestones.append(biggest_improvement)
        else:
            milestones.append({
                "type": "biggest_improvement",
                "title": "Biggest Improvement",
                "icon": "trending-up",
                "value": None,
                "unit": "percentage points",
                "label": "Unlocks after 2 sessions",
                "metric_name": "Session-over-Session Delta",
                "description": "Calculates the largest positive change compared with your previous session once 2 or more sessions are recorded."
            })

        # -------------------------------------------------------------
        # E. ANALYSIS STREAK
        # -------------------------------------------------------------
        streak_count = total_count
        milestones.append({
            "type": "analysis_streak",
            "title": "Analysis Streak",
            "icon": "flame",
            "value": streak_count,
            "unit": "sessions",
            "label": f"{streak_count} {'session' if streak_count == 1 else 'sessions'}",
            "metric_name": "Consecutive Sessions",
            "description": f"You have logged {streak_count} consecutive completed running form analyses in your personal history.",
            "motivational_note": "Keep going!" if streak_count >= 2 else "Great start!"
        })

        # -------------------------------------------------------------
        # RECENT ACHIEVEMENTS (Milestones achieved in the latest analysis)
        # -------------------------------------------------------------
        if total_count >= 1:
            latest = sorted_analyses[-1]
            latest_id = latest.get("id") or latest.get("analysis_id")

            for m in milestones:
                if m.get("value") is not None and m.get("analysis_id") == latest_id:
                    recent_achievements.append({
                        "type": m.get("type"),
                        "title": m.get("title"),
                        "value": m.get("value"),
                        "unit": m.get("unit"),
                        "previous_value": m.get("previous_value"),
                        "improvement_delta": m.get("improvement_delta"),
                        "improvement_unit": m.get("improvement_unit"),
                        "achieved_at": m.get("achieved_at"),
                        "analysis_id": latest_id
                    })

        return {
            "total_analyses": total_count,
            "has_milestones": True,
            "is_demo": is_demo,
            "milestones": milestones,
            "recent_achievements": recent_achievements
        }

milestone_service = MilestoneService()
