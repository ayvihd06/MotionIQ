import pytest
import numpy as np
from app.context.running_type_classifier import running_type_classifier
from app.insights.confidence_engine import confidence_engine
from app.insights.insight_engine import insight_engine
from app.metrics.cadence_engine import cadence_engine
from app.metrics.temporal_engine import temporal_engine
from app.metrics.kinematics_engine import kinematics_engine
from app.pipeline.gait_detector import GaitContactEvent
from app.pipeline.landmark_processor import LandmarkTrajectories, TrajectorySeries
from app.pipeline.runner_validator import ValidationReport

def test_running_type_classification():
    det = {
        "surface": {"value": "Road / Asphalt"},
        "observed_movement": {"value": "Running"}
    }
    opt = {
        "training_goal": "5K",
        "perceived_effort": "Hard",
        "experience_level": "Intermediate",
        "age_category": "30-39",
        "bmi": 22.4
    }
    ctx = running_type_classifier.classify_running_type(det, opt)
    assert ctx.distance_category == "5K – 10K Distance"
    assert ctx.surface_category == "Road / Asphalt"
    assert ctx.intensity_category == "Tempo / Threshold"
    assert "Intermediate" in ctx.runner_profile_summary

def test_confidence_engine_breakdown():
    n = 40
    t = np.linspace(0, 1.33, n)
    joints = {
        "left_shoulder": TrajectorySeries(t, np.full(n, 0.5), np.full(n, 0.3), np.zeros(n), np.full(n, 0.9), np.zeros(n, bool)),
        "right_shoulder": TrajectorySeries(t, np.full(n, 0.5), np.full(n, 0.3), np.zeros(n), np.full(n, 0.9), np.zeros(n, bool)),
        "left_hip": TrajectorySeries(t, np.full(n, 0.5), np.full(n, 0.6), np.zeros(n), np.full(n, 0.9), np.zeros(n, bool)),
        "right_hip": TrajectorySeries(t, np.full(n, 0.5), np.full(n, 0.6), np.zeros(n), np.full(n, 0.9), np.zeros(n, bool)),
        "left_knee": TrajectorySeries(t, np.full(n, 0.5), np.full(n, 0.7), np.zeros(n), np.full(n, 0.9), np.zeros(n, bool)),
        "left_heel": TrajectorySeries(t, np.full(n, 0.5), np.full(n, 0.85), np.zeros(n), np.full(n, 0.85), np.zeros(n, bool)),
        "left_foot_index": TrajectorySeries(t, np.full(n, 0.55), np.full(n, 0.82), np.zeros(n), np.full(n, 0.85), np.zeros(n, bool)),
    }
    trajectories = LandmarkTrajectories(np.arange(n), t, 30.0, 1.33, joints)
    events = [
        GaitContactEvent(frame_idx=5, timestamp_s=0.17, side="left", event_type="initial_contact", confidence=0.9, foot_y=0.8),
        GaitContactEvent(frame_idx=15, timestamp_s=0.50, side="right", event_type="initial_contact", confidence=0.9, foot_y=0.8),
        GaitContactEvent(frame_idx=25, timestamp_s=0.83, side="left", event_type="initial_contact", confidence=0.9, foot_y=0.8),
        GaitContactEvent(frame_idx=35, timestamp_s=1.16, side="right", event_type="initial_contact", confidence=0.9, foot_y=0.8),
    ]
    val_report = ValidationReport(True, 85.0, 95.0, True, True, "Good", [], [])

    conf_breakdown = confidence_engine.evaluate_confidence(
        trajectories, events, val_report, fps=30.0, width=1280, height=720
    )

    assert conf_breakdown.cadence_confidence.confidence_level in ["High", "Medium"]
    assert conf_breakdown.symmetry_confidence.confidence_level in ["High", "Medium"]
    assert conf_breakdown.trunk_lean_confidence.confidence_level == "High"
    assert conf_breakdown.overall_confidence in ["High", "Medium"]

def test_medical_language_safety_in_insights():
    # Verify that all generated insights comply with the strict non-diagnostic language policy
    cadence = cadence_engine.calculate_cadence([
        GaitContactEvent(frame_idx=i*10, timestamp_s=round(i*0.35, 3), side="left" if i%2==0 else "right", event_type="initial_contact", confidence=0.9, foot_y=0.7)
        for i in range(8)
    ], duration_s=2.8)
    temporal = temporal_engine.calculate_temporal_metrics([
        GaitContactEvent(frame_idx=i*10, timestamp_s=round(i*0.35, 3), side="left" if i%2==0 else "right", event_type="initial_contact", confidence=0.9, foot_y=0.7)
        for i in range(8)
    ])
    trunk = kinematics_engine.calculate_trunk_lean(LandmarkTrajectories(np.arange(5), np.linspace(0, 1, 5), 30.0, 1.0, {
        "left_shoulder": TrajectorySeries(np.linspace(0, 1, 5), np.full(5, 0.54), np.full(5, 0.30), np.zeros(5), np.ones(5), np.zeros(5, bool)),
        "right_shoulder": TrajectorySeries(np.linspace(0, 1, 5), np.full(5, 0.54), np.full(5, 0.30), np.zeros(5), np.ones(5), np.zeros(5, bool)),
        "left_hip": TrajectorySeries(np.linspace(0, 1, 5), np.full(5, 0.50), np.full(5, 0.60), np.zeros(5), np.ones(5), np.zeros(5, bool)),
        "right_hip": TrajectorySeries(np.linspace(0, 1, 5), np.full(5, 0.50), np.full(5, 0.60), np.zeros(5), np.ones(5), np.zeros(5, bool)),
    }))
    arms = kinematics_engine.calculate_arm_swing(LandmarkTrajectories(np.arange(2), np.array([0, 1]), 30.0, 1.0, {}))
    foot_strike = kinematics_engine.classify_foot_strike(LandmarkTrajectories(np.arange(2), np.array([0, 1]), 30.0, 1.0, {}), [])
    overstride = kinematics_engine.calculate_potential_overstride(LandmarkTrajectories(np.arange(2), np.array([0, 1]), 30.0, 1.0, {}), [])
    vertical = kinematics_engine.calculate_relative_vertical_movement(LandmarkTrajectories(np.arange(2), np.array([0, 1]), 30.0, 1.0, {
        "left_shoulder": TrajectorySeries(np.array([0, 1]), np.array([0.5, 0.5]), np.array([0.3, 0.3]), np.zeros(2), np.ones(2), np.zeros(2, bool)),
        "right_shoulder": TrajectorySeries(np.array([0, 1]), np.array([0.5, 0.5]), np.array([0.3, 0.3]), np.zeros(2), np.ones(2), np.zeros(2, bool)),
        "left_hip": TrajectorySeries(np.array([0, 1]), np.array([0.5, 0.5]), np.array([0.6, 0.62]), np.zeros(2), np.ones(2), np.zeros(2, bool)),
        "right_hip": TrajectorySeries(np.array([0, 1]), np.array([0.5, 0.5]), np.array([0.6, 0.62]), np.zeros(2), np.ones(2), np.zeros(2, bool)),
    }))
    context = running_type_classifier.classify_running_type({}, {"training_goal": "Marathon", "perceived_effort": "Easy"})
    conf = confidence_engine.evaluate_confidence(
        LandmarkTrajectories(np.arange(2), np.array([0, 1]), 30.0, 1.0, {}),
        [],
        ValidationReport(True, 80.0, 90.0, True, True, "Good", [], []),
        30.0, 1280, 720
    )

    insights, overall = insight_engine.generate_insights(
        cadence, temporal, trunk, arms, foot_strike, overstride, vertical, context, conf
    )

    # Prohibited phrases check
    prohibited = [
        "will get injured",
        "you have an injury",
        "high injury risk",
        "your form is dangerous",
        "clinical diagnosis",
        "pathological"
    ]

    all_texts = [overall.headline, overall.responsible_ai_disclaimer]
    for ins in insights:
        all_texts.append(ins.title)
        all_texts.append(ins.description)
        all_texts.append(ins.recommended_action)
        all_texts.extend(ins.why_flagged)

    full_corpus = " ".join(all_texts).lower()
    for phrase in prohibited:
        assert phrase not in full_corpus, f"Prohibited phrase '{phrase}' found in output."

    assert len(insights) >= 4
    assert overall.form_consistency_score > 0
