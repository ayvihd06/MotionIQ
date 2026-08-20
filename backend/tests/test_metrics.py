import pytest
import numpy as np
from app.pipeline.gait_detector import GaitContactEvent
from app.pipeline.landmark_processor import LandmarkTrajectories, TrajectorySeries
from app.metrics.cadence_engine import cadence_engine
from app.metrics.temporal_engine import temporal_engine
from app.metrics.kinematics_engine import kinematics_engine
from app.metrics.form_classifier import form_classifier

def test_cadence_calculation():
    # 10 steps over 3.5 seconds -> Cadence should be ~171 SPM
    events = [
        GaitContactEvent(frame_idx=i*10, timestamp_s=round(i*0.35, 3), side="left" if i%2==0 else "right", event_type="initial_contact", confidence=0.9, foot_y=0.7)
        for i in range(10)
    ]
    res = cadence_engine.calculate_cadence(events, duration_s=3.5)
    assert 165.0 <= res.value <= 178.0
    assert res.step_count == 10
    assert res.cycles_used == 5
    assert res.confidence == "High"

def test_temporal_symmetry_calculation():
    # Symmetric 0.35s steps
    events = [
        GaitContactEvent(frame_idx=i*10, timestamp_s=round(i*0.35, 3), side="left" if i%2==0 else "right", event_type="initial_contact", confidence=0.9, foot_y=0.7)
        for i in range(8)
    ]
    res = temporal_engine.calculate_temporal_metrics(events)
    assert res.symmetry_pct >= 95.0
    assert res.mean_stride_time_s == pytest.approx(0.70, abs=0.05)
    assert res.step_time_variability_cv < 5.0

def test_trunk_lean_calculation():
    n = 30
    t = np.linspace(0, 1.0, n)
    # Simulate a forward lean of ~7 degrees
    # Shoulder is forward of hip by dx = 0.04 and torso height is 0.30 -> arctan2(0.04, 0.30) ~ 7.6 degrees
    joints = {
        "left_shoulder": TrajectorySeries(t, np.full(n, 0.54), np.full(n, 0.30), np.zeros(n), np.ones(n), np.zeros(n, bool)),
        "right_shoulder": TrajectorySeries(t, np.full(n, 0.54), np.full(n, 0.30), np.zeros(n), np.ones(n), np.zeros(n, bool)),
        "left_hip": TrajectorySeries(t, np.full(n, 0.50), np.full(n, 0.60), np.zeros(n), np.ones(n), np.zeros(n, bool)),
        "right_hip": TrajectorySeries(t, np.full(n, 0.50), np.full(n, 0.60), np.zeros(n), np.ones(n), np.zeros(n, bool)),
    }
    traj = LandmarkTrajectories(np.arange(n), t, 30.0, 1.0, joints)
    res = kinematics_engine.calculate_trunk_lean(traj)
    assert 6.0 <= res.mean_trunk_lean_deg <= 9.0
    assert res.confidence == "High"

def test_foot_strike_classification():
    n = 30
    t = np.linspace(0, 1.0, n)
    # Toe is higher than heel (heel contacts first -> rearfoot)
    joints = {
        "left_heel": TrajectorySeries(t, np.full(n, 0.50), np.full(n, 0.85), np.zeros(n), np.ones(n), np.zeros(n, bool)),
        "left_foot_index": TrajectorySeries(t, np.full(n, 0.60), np.full(n, 0.80), np.zeros(n), np.ones(n), np.zeros(n, bool)),
        "right_heel": TrajectorySeries(t, np.full(n, 0.50), np.full(n, 0.85), np.zeros(n), np.ones(n), np.zeros(n, bool)),
        "right_foot_index": TrajectorySeries(t, np.full(n, 0.60), np.full(n, 0.80), np.zeros(n), np.ones(n), np.zeros(n, bool)),
    }
    traj = LandmarkTrajectories(np.arange(n), t, 30.0, 1.0, joints)
    events = [
        GaitContactEvent(frame_idx=5, timestamp_s=0.17, side="left", event_type="initial_contact", confidence=0.9, foot_y=0.85),
        GaitContactEvent(frame_idx=15, timestamp_s=0.50, side="right", event_type="initial_contact", confidence=0.9, foot_y=0.85),
    ]
    res = kinematics_engine.classify_foot_strike(traj, events)
    assert res.pattern == "Rearfoot-dominant"
    assert res.mean_strike_angle_deg > 7.0

def test_form_classifier_rules():
    # Test rule matching for Forward-Leaning dynamic stride
    cadence = cadence_engine.calculate_cadence([
        GaitContactEvent(frame_idx=i*10, timestamp_s=round(i*0.35, 3), side="left" if i%2==0 else "right", event_type="initial_contact", confidence=0.9, foot_y=0.7)
        for i in range(8)
    ], duration_s=2.8)
    temporal = temporal_engine.calculate_temporal_metrics([])
    trunk = kinematics_engine.calculate_trunk_lean(
        LandmarkTrajectories(np.arange(10), np.linspace(0, 1, 10), 30.0, 1.0, {
            "left_shoulder": TrajectorySeries(np.linspace(0, 1, 10), np.full(10, 0.54), np.full(10, 0.30), np.zeros(10), np.ones(10), np.zeros(10, bool)),
            "right_shoulder": TrajectorySeries(np.linspace(0, 1, 10), np.full(10, 0.54), np.full(10, 0.30), np.zeros(10), np.ones(10), np.zeros(10, bool)),
            "left_hip": TrajectorySeries(np.linspace(0, 1, 10), np.full(10, 0.50), np.full(10, 0.60), np.zeros(10), np.ones(10), np.zeros(10, bool)),
            "right_hip": TrajectorySeries(np.linspace(0, 1, 10), np.full(10, 0.50), np.full(10, 0.60), np.zeros(10), np.ones(10), np.zeros(10, bool)),
        })
    )
    arms = kinematics_engine.calculate_arm_swing(LandmarkTrajectories(np.arange(2), np.array([0, 1]), 30.0, 1.0, {
        "left_shoulder": TrajectorySeries(np.array([0, 1]), np.array([0.5, 0.5]), np.array([0.3, 0.3]), np.zeros(2), np.ones(2), np.zeros(2, bool)),
        "right_shoulder": TrajectorySeries(np.array([0, 1]), np.array([0.5, 0.5]), np.array([0.3, 0.3]), np.zeros(2), np.ones(2), np.zeros(2, bool)),
        "left_elbow": TrajectorySeries(np.array([0, 1]), np.array([0.5, 0.5]), np.array([0.45, 0.45]), np.zeros(2), np.ones(2), np.zeros(2, bool)),
        "right_elbow": TrajectorySeries(np.array([0, 1]), np.array([0.5, 0.5]), np.array([0.45, 0.45]), np.zeros(2), np.ones(2), np.zeros(2, bool)),
        "left_wrist": TrajectorySeries(np.array([0, 1]), np.array([0.55, 0.55]), np.array([0.45, 0.45]), np.zeros(2), np.ones(2), np.zeros(2, bool)),
        "right_wrist": TrajectorySeries(np.array([0, 1]), np.array([0.55, 0.55]), np.array([0.45, 0.45]), np.zeros(2), np.ones(2), np.zeros(2, bool)),
    }))
    foot_strike = kinematics_engine.classify_foot_strike(LandmarkTrajectories(np.arange(2), np.array([0, 1]), 30.0, 1.0, {}), [])
    overstride = kinematics_engine.calculate_potential_overstride(LandmarkTrajectories(np.arange(2), np.array([0, 1]), 30.0, 1.0, {}), [])
    vertical = kinematics_engine.calculate_relative_vertical_movement(LandmarkTrajectories(np.arange(10), np.linspace(0, 1, 10), 30.0, 1.0, {
        "left_shoulder": TrajectorySeries(np.linspace(0, 1, 10), np.full(10, 0.5), np.full(10, 0.3), np.zeros(10), np.ones(10), np.zeros(10, bool)),
        "right_shoulder": TrajectorySeries(np.linspace(0, 1, 10), np.full(10, 0.5), np.full(10, 0.3), np.zeros(10), np.ones(10), np.zeros(10, bool)),
        "left_hip": TrajectorySeries(np.linspace(0, 1, 10), np.full(10, 0.5), np.array([0.60, 0.63, 0.60, 0.58, 0.60, 0.63, 0.60, 0.58, 0.60, 0.63]), np.zeros(10), np.ones(10), np.zeros(10, bool)),
        "right_hip": TrajectorySeries(np.linspace(0, 1, 10), np.full(10, 0.5), np.array([0.60, 0.63, 0.60, 0.58, 0.60, 0.63, 0.60, 0.58, 0.60, 0.63]), np.zeros(10), np.ones(10), np.zeros(10, bool)),
    }))

    obs = form_classifier.classify_form_patterns(cadence, temporal, trunk, arms, foot_strike, overstride, vertical)
    assert len(obs) >= 3
    labels = [o.label for o in obs]
    assert any("Posture" in l or "Forward" in l or "Dynamic" in l for l in labels)
