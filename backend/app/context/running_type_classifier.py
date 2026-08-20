from dataclasses import dataclass
from typing import Dict, Any, Optional

@dataclass
class RunningTypeContext:
    distance_category: str       # "Sprint", "Middle Distance", "Long Distance", "Marathon", "General Conditioning"
    surface_category: str        # "Road", "Track", "Trail", "Treadmill", "Cross-Country / Grass", "Indoor Floor"
    intensity_category: str      # "Recovery", "Easy Aerobic", "Tempo / Threshold", "Interval / Fast", "Race Effort", "Moderate"
    experience_level: str        # "Beginner", "Intermediate", "Advanced", "Elite"
    runner_profile_summary: str

class RunningTypeClassifier:
    """Classifies distance, surface, and intensity context for running biomechanics interpretation."""

    @staticmethod
    def classify_running_type(
        detected_context: Dict[str, Any],
        optional_context: Dict[str, Any]
    ) -> RunningTypeContext:
        goal = str(optional_context.get("training_goal", "General fitness")).lower()
        effort = str(optional_context.get("perceived_effort", "Moderate")).lower()
        surface_val = str(detected_context.get("surface", {}).get("value", "Road / Asphalt")).lower()
        experience = str(optional_context.get("experience_level", "Intermediate"))
        movement = str(detected_context.get("observed_movement", {}).get("value", "Running")).lower()

        # 1. Distance Category Classification
        if "sprint" in goal or "100m" in goal or "400m" in goal or "sprint" in movement:
            distance_cat = "Sprint"
        elif "800m" in goal or "1500m" in goal or "3000m" in goal or "middle" in goal:
            distance_cat = "Middle Distance"
        elif "marathon" in goal or "half marathon" in goal or "long" in goal:
            distance_cat = "Marathon / Long Distance"
        elif "5k" in goal or "10k" in goal:
            distance_cat = "5K – 10K Distance"
        else:
            distance_cat = "General Conditioning"

        # 2. Surface Category Classification
        if "track" in surface_val:
            surface_cat = "Track"
        elif "treadmill" in surface_val:
            surface_cat = "Treadmill"
        elif "trail" in surface_val:
            surface_cat = "Trail"
        elif "grass" in surface_val:
            surface_cat = "Cross-Country / Grass"
        elif "indoor" in surface_val:
            surface_cat = "Indoor Floor"
        else:
            surface_cat = "Road / Asphalt"

        # 3. Intensity Category Classification
        if "very easy" in effort or "recovery" in effort:
            intensity_cat = "Recovery Run"
        elif "easy" in effort or "jogging" in movement:
            intensity_cat = "Easy Aerobic"
        elif "hard" in effort or "threshold" in effort or "tempo" in effort:
            intensity_cat = "Tempo / Threshold"
        elif "very hard" in effort or "race" in effort:
            intensity_cat = "Race Effort"
        elif "sprint" in movement or "fast running" in movement:
            intensity_cat = "Interval / Fast Pace"
        else:
            intensity_cat = "Moderate Effort"

        age_cat = optional_context.get("age_category", "30-39")
        bmi_val = optional_context.get("bmi")
        bmi_str = f", BMI: {bmi_val}" if bmi_val else ""

        summary = f"{distance_cat} on {surface_cat} • {intensity_cat} ({experience} Runner, Age: {age_cat}{bmi_str})"

        return RunningTypeContext(
            distance_category=distance_cat,
            surface_category=surface_cat,
            intensity_category=intensity_cat,
            experience_level=experience,
            runner_profile_summary=summary
        )

running_type_classifier = RunningTypeClassifier()
