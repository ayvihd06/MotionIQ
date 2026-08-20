import pytest
from app.api.schemas.context import OptionalUserContext
from app.api.schemas.video import VideoMetadata, VideoSuitabilityReport, SuitabilityCheckItem

def test_optional_user_context():
    context = OptionalUserContext(
        age_category="30-39",
        experience_level="Intermediate",
        training_goal="5K",
        perceived_effort="Moderate"
    )
    assert context.age_category == "30-39"
    assert context.training_goal == "5K"

def test_suitability_report_model():
    checks = [
        SuitabilityCheckItem(
            name="Duration",
            passed=True,
            rating="Optimal",
            message="Ideal duration"
        ),
        SuitabilityCheckItem(
            name="Side-View Orientation",
            passed=True,
            rating="Optimal",
            message="Side-view orientation verified"
        )
    ]
    report = VideoSuitabilityReport(
        overall_status="Ready for analysis",
        suitability_score=92.5,
        checks=checks,
        warnings=[],
        recommendations=["Keep camera level"]
    )
    assert report.overall_status == "Ready for analysis"
    assert report.suitability_score == 92.5
    assert len(report.checks) == 2
