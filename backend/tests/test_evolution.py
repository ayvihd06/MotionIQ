import pytest
from app.evolution.evolution_engine import evolution_engine

def test_evolution_baseline_states():
    # 0 analyses
    res0 = evolution_engine.compute_evolution([])
    assert res0["total_analyses"] == 0
    assert res0["baseline_status"] == "No history"

    # 1 analysis -> Baseline unavailable
    sample1 = {
        "analysis_id": "session-1",
        "created_at": "2026-08-01T10:00:00",
        "cadence_spm": 160.0,
        "left_right_symmetry_pct": 92.0,
        "trunk_lean_deg": 6.0,
        "form_consistency_score": 84.0
    }
    res1 = evolution_engine.compute_evolution([sample1])
    assert res1["total_analyses"] == 1
    assert res1["baseline_status"] == "Baseline unavailable"
    assert res1["personal_baseline"] is None

    # 2-3 analyses -> Early baseline
    sample2 = {
        "analysis_id": "session-2",
        "created_at": "2026-08-05T10:00:00",
        "cadence_spm": 166.0,
        "left_right_symmetry_pct": 94.0,
        "trunk_lean_deg": 7.0,
        "form_consistency_score": 88.0
    }
    res2 = evolution_engine.compute_evolution([sample1, sample2])
    assert res2["total_analyses"] == 2
    assert res2["baseline_status"] == "Early baseline"
    assert res2["personal_baseline"]["cadence_spm"] == 163.0 # (160 + 166) / 2
    
    # Delta comparison check (Latest 166 vs Previous 160 -> +6 SPM)
    cadence_change = next(c for c in res2["change_metrics"] if c["metric_key"] == "cadence")
    assert cadence_change["delta_from_previous"] == 6.0
    assert cadence_change["delta_from_baseline"] == 3.0 # 166 - 163

    # 4+ analyses -> Personal baseline established
    sample3 = {
        "analysis_id": "session-3",
        "created_at": "2026-08-10T10:00:00",
        "cadence_spm": 168.0,
        "left_right_symmetry_pct": 95.0,
        "trunk_lean_deg": 7.5,
        "form_consistency_score": 90.0
    }
    sample4 = {
        "analysis_id": "session-4",
        "created_at": "2026-08-15T10:00:00",
        "cadence_spm": 172.0,
        "left_right_symmetry_pct": 96.0,
        "trunk_lean_deg": 8.0,
        "form_consistency_score": 92.0,
        "running_type_context": {"intensity_category": "Tempo", "surface_category": "Track"}
    }
    res4 = evolution_engine.compute_evolution([sample1, sample2, sample3, sample4])
    assert res4["total_analyses"] == 4
    assert res4["baseline_status"] == "Personal baseline established"
    assert len(res4["trend_series"]) == 4

def test_evolution_context_mismatch_warning():
    sample_easy = {
        "analysis_id": "s-easy",
        "created_at": "2026-08-01T10:00:00",
        "cadence_spm": 158.0,
        "left_right_symmetry_pct": 93.0,
        "trunk_lean_deg": 5.5,
        "running_type_context": {"intensity_category": "Recovery / Easy", "surface_category": "Trail"}
    }
    sample_tempo = {
        "analysis_id": "s-tempo",
        "created_at": "2026-08-05T10:00:00",
        "cadence_spm": 174.0,
        "left_right_symmetry_pct": 96.0,
        "trunk_lean_deg": 8.0,
        "running_type_context": {"intensity_category": "Tempo / Threshold", "surface_category": "Track"}
    }
    res = evolution_engine.compute_evolution([sample_easy, sample_tempo])
    assert len(res["context_notices"]) >= 1
    assert any("intensity" in n.lower() for n in res["context_notices"])
