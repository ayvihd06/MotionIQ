from typing import List, Dict, Any, Optional
import numpy as np
from datetime import datetime

class PersonalFormEvolutionEngine:
    """Calculates personalized running form baselines, change detection, and historical evolution trends."""

    @staticmethod
    def compute_evolution(analyses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Computes personal baseline, change detection, and historical trend series from a user's chronological analyses."""
        if not analyses:
            return {
                "total_analyses": 0,
                "baseline_status": "No history",
                "baseline_message": "No recorded analyses yet. Complete your first session to begin tracking form evolution.",
                "personal_baseline": None,
                "latest_analysis": None,
                "previous_analysis": None,
                "change_metrics": [],
                "trend_series": [],
                "context_notices": []
            }

        # Ensure sorted chronologically (oldest -> newest)
        sorted_analyses = sorted(
            analyses,
            key=lambda a: a.get("created_at") or ""
        )
        total_count = len(sorted_analyses)

        # Determine Baseline Status
        if total_count == 1:
            baseline_status = "Baseline unavailable"
            baseline_message = "1 session recorded. Complete at least 2 sessions to begin tracking your personal form evolution."
        elif 2 <= total_count <= 3:
            baseline_status = "Early baseline"
            baseline_message = f"Early personal baseline calculated from {total_count} recorded running sessions."
        else:
            baseline_status = "Personal baseline established"
            baseline_message = f"Robust personal baseline established across {total_count} historical sessions."

        # Extract metric arrays for baseline computation
        cadences = [float(a.get("cadence_spm") or 0) for a in sorted_analyses if a.get("cadence_spm")]
        symmetries = [float(a.get("left_right_symmetry_pct") or 0) for a in sorted_analyses if a.get("left_right_symmetry_pct")]
        trunk_leans = [float(a.get("trunk_lean_deg") or 0) for a in sorted_analyses if a.get("trunk_lean_deg") is not None]
        consistency_scores = [float(a.get("form_consistency_score") or (a.get("overall_summary") or {}).get("form_consistency_score", 85.0)) for a in sorted_analyses]

        personal_baseline = None
        if total_count >= 2:
            personal_baseline = {
                "cadence_spm": round(float(np.mean(cadences)), 1) if cadences else None,
                "left_right_symmetry_pct": round(float(np.mean(symmetries)), 1) if symmetries else None,
                "trunk_lean_deg": round(float(np.mean(trunk_leans)), 1) if trunk_leans else None,
                "form_consistency_score": round(float(np.mean(consistency_scores)), 1) if consistency_scores else None,
                "sessions_averaged": total_count
            }

        latest = sorted_analyses[-1]
        previous = sorted_analyses[-2] if total_count >= 2 else None

        # Build Change Detection Metrics
        change_metrics = []
        
        # 1. Cadence Delta
        latest_cadence = float(latest.get("cadence_spm") or 0)
        prev_cadence = float(previous.get("cadence_spm") or 0) if previous else None
        base_cadence = personal_baseline["cadence_spm"] if personal_baseline else None

        delta_prev_cadence = round(latest_cadence - prev_cadence, 1) if prev_cadence else None
        delta_base_cadence = round(latest_cadence - base_cadence, 1) if base_cadence else None

        change_metrics.append({
            "metric_key": "cadence",
            "name": "Cadence",
            "unit": "SPM",
            "latest_value": round(latest_cadence, 1),
            "previous_value": round(prev_cadence, 1) if prev_cadence else None,
            "baseline_value": base_cadence,
            "delta_from_previous": delta_prev_cadence,
            "delta_from_baseline": delta_base_cadence,
            "interpretation": f"Step rate shifted by {'+' if delta_prev_cadence and delta_prev_cadence > 0 else ''}{delta_prev_cadence} SPM compared to previous run." if delta_prev_cadence is not None else "Baseline tracking initiated."
        })

        # 2. Symmetry Delta
        latest_symm = float(latest.get("left_right_symmetry_pct") or 0)
        prev_symm = float(previous.get("left_right_symmetry_pct") or 0) if previous else None
        base_symm = personal_baseline["left_right_symmetry_pct"] if personal_baseline else None

        delta_prev_symm = round(latest_symm - prev_symm, 1) if prev_symm else None
        delta_base_symm = round(latest_symm - base_symm, 1) if base_symm else None

        change_metrics.append({
            "metric_key": "symmetry",
            "name": "Bilateral Step Balance",
            "unit": "%",
            "latest_value": round(latest_symm, 1),
            "previous_value": round(prev_symm, 1) if prev_symm else None,
            "baseline_value": base_symm,
            "delta_from_previous": delta_prev_symm,
            "delta_from_baseline": delta_base_symm,
            "interpretation": f"Bilateral balance shifted by {'+' if delta_prev_symm and delta_prev_symm > 0 else ''}{delta_prev_symm}% relative to prior session." if delta_prev_symm is not None else "Initial balance baseline."
        })

        # 3. Trunk Lean Delta
        latest_lean = float(latest.get("trunk_lean_deg") or 0)
        prev_lean = float(previous.get("trunk_lean_deg") or 0) if previous else None
        base_lean = personal_baseline["trunk_lean_deg"] if personal_baseline else None

        delta_prev_lean = round(latest_lean - prev_lean, 1) if prev_lean else None
        delta_base_lean = round(latest_lean - base_lean, 1) if base_lean else None

        change_metrics.append({
            "metric_key": "trunk_lean",
            "name": "Trunk Forward Lean",
            "unit": "°",
            "latest_value": round(latest_lean, 1),
            "previous_value": round(prev_lean, 1) if prev_lean else None,
            "baseline_value": base_lean,
            "delta_from_previous": delta_prev_lean,
            "delta_from_baseline": delta_base_lean,
            "interpretation": f"Torso inclination adjusted by {'+' if delta_prev_lean and delta_prev_lean > 0 else ''}{delta_prev_lean}°." if delta_prev_lean is not None else "Initial posture recorded."
        })

        # 4. Consistency Index Delta
        latest_score = float(latest.get("form_consistency_score") or (latest.get("overall_summary") or {}).get("form_consistency_score", 85.0))
        prev_score = float(previous.get("form_consistency_score") or (previous.get("overall_summary") or {}).get("form_consistency_score", 85.0)) if previous else None
        base_score = personal_baseline["form_consistency_score"] if personal_baseline else None

        delta_prev_score = round(latest_score - prev_score, 1) if prev_score else None
        delta_base_score = round(latest_score - base_score, 1) if base_score else None

        change_metrics.append({
            "metric_key": "consistency",
            "name": "Form & Consistency Index",
            "unit": "/100",
            "latest_value": round(latest_score, 1),
            "previous_value": round(prev_score, 1) if prev_score else None,
            "baseline_value": base_score,
            "delta_from_previous": delta_prev_score,
            "delta_from_baseline": delta_base_score,
            "interpretation": f"Movement consistency index moved by {'+' if delta_prev_score and delta_prev_score > 0 else ''}{delta_prev_score} pts." if delta_prev_score is not None else "Initial index baseline."
        })

        # Context-Aware Comparison Guard
        context_notices = []
        if previous:
            latest_ctx = latest.get("running_type_context") or {}
            prev_ctx = previous.get("running_type_context") or {}
            
            latest_intensity = latest_ctx.get("intensity_category") or "Standard"
            prev_intensity = prev_ctx.get("intensity_category") or "Standard"
            
            latest_surface = latest_ctx.get("surface_category") or "Road"
            prev_surface = prev_ctx.get("surface_category") or "Road"

            if latest_intensity != prev_intensity:
                context_notices.append(
                    f"Context Notice: Comparison between recent sessions may be influenced by different running intensity levels ({latest_intensity} vs {prev_intensity})."
                )
            if latest_surface != prev_surface:
                context_notices.append(
                    f"Context Notice: Surface differences ({latest_surface} vs {prev_surface}) naturally alter foot strike dynamics and cadence."
                )

        # Build Trend Time Series for Recharts
        trend_series = []
        for i, a in enumerate(sorted_analyses):
            created = a.get("created_at", "")
            date_label = created[:10] if len(created) >= 10 else f"Session #{i+1}"
            ctx = a.get("running_type_context") or {}
            
            trend_series.append({
                "session_index": i + 1,
                "analysis_id": a.get("analysis_id"),
                "date_label": date_label,
                "created_at": created,
                "cadence_spm": round(float(a.get("cadence_spm") or 0), 1),
                "left_right_symmetry_pct": round(float(a.get("left_right_symmetry_pct") or 0), 1),
                "trunk_lean_deg": round(float(a.get("trunk_lean_deg") or 0), 1),
                "form_consistency_score": round(float(a.get("form_consistency_score") or (a.get("overall_summary") or {}).get("form_consistency_score", 85.0)), 1),
                "form_classification": a.get("form_classification", "Form Pattern"),
                "surface": ctx.get("surface_category", "Road"),
                "intensity": ctx.get("intensity_category", "Moderate Effort"),
                "distance": ctx.get("distance_category", "Standard")
            })

        return {
            "total_analyses": total_count,
            "baseline_status": baseline_status,
            "baseline_message": baseline_message,
            "personal_baseline": personal_baseline,
            "latest_analysis": {
                "analysis_id": latest.get("analysis_id"),
                "created_at": latest.get("created_at"),
                "form_classification": latest.get("form_classification"),
                "overall_confidence": latest.get("overall_confidence")
            },
            "previous_analysis": {
                "analysis_id": previous.get("analysis_id"),
                "created_at": previous.get("created_at"),
                "form_classification": previous.get("form_classification"),
                "overall_confidence": previous.get("overall_confidence")
            } if previous else None,
            "change_metrics": change_metrics,
            "trend_series": trend_series,
            "context_notices": context_notices
        }

evolution_engine = PersonalFormEvolutionEngine()
