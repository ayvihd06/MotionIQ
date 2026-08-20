import pytest
import io
from fastapi.testclient import TestClient
from app.main import app
from app.reports.pdf_generator import pdf_report_generator
from app.repositories.analysis_repository import analysis_repository

client = TestClient(app)

def test_pdf_report_generation():
    dummy_data = {
        "analysis_id": "test-pdf-analysis-12345",
        "created_at": "2026-08-18T22:00:00",
        "form_classification": "Forward-Leaning Dynamic Stride (174 SPM)",
        "running_type_context": {
            "runner_profile_summary": "5K on Road • Moderate Effort (Intermediate Runner)"
        },
        "overall_summary": {
            "headline": "Biomechanical Summary",
            "form_consistency_score": 92.0,
            "strongest_positive_observations": ["Cadence in optimal range", "High bilateral symmetry"],
            "areas_to_monitor": ["Maintain knee compliance"],
            "responsible_ai_disclaimer": "Non-diagnostic observational report."
        },
        "metrics_breakdown": [
            {"name": "Cadence", "value": "174", "unit": "SPM", "confidence": "High", "status": "Optimal", "description": "Step rate from 13 contacts."},
            {"name": "Bilateral Symmetry", "value": "94.8", "unit": "%", "confidence": "High", "status": "Optimal", "description": "Balanced left vs right step times."}
        ],
        "context_insights": [
            {
                "title": "Cadence Context",
                "category": "Cadence",
                "confidence": "High",
                "description": "Natural step rate.",
                "why_flagged": ["13 steps across 4.5s"],
                "recommended_action": "Maintain rhythm."
            }
        ],
        "recommendations": ["Maintain current bilateral strength routine."],
        "limitations": ["2D monocular video estimates sagittal projections only."]
    }

    pdf_buffer = pdf_report_generator.generate_report(dummy_data)
    assert isinstance(pdf_buffer, io.BytesIO)
    pdf_bytes = pdf_buffer.getvalue()
    assert len(pdf_bytes) > 1000
    assert pdf_bytes.startswith(b"%PDF")


def test_pdf_long_value_wrapping():
    """Regression: long metric values like 'Forefoot-dominant pattern' must not overflow the Value column.
    We verify the PDF generates without error and is a valid PDF document when such values are present."""
    long_value_data = {
        "analysis_id": "test-pdf-overflow-check-99",
        "created_at": "2026-08-20T10:00:00",
        "form_classification": "Forward-Leaning Dynamic Stride (174 SPM)",
        "running_type_context": {
            "runner_profile_summary": "5K Road • Moderate Effort (Intermediate)"
        },
        "overall_summary": {
            "form_consistency_score": 78.5,
        },
        "metrics_breakdown": [
            {
                "name": "Foot Strike Pattern",
                "value": "Forefoot-dominant pattern",
                "unit": "",
                "confidence": "Medium",
                "status": "Observational",
                "description": (
                    "Ankle position at initial contact appears anterior to heel; "
                    "suggests forefoot or midfoot loading. Observational only — "
                    "cannot confirm internal joint mechanics from 2D video."
                )
            },
            {
                "name": "Cadence",
                "value": "174",
                "unit": "SPM",
                "confidence": "High",
                "status": "Optimal",
                "description": "Step rate falls within the 170–180 SPM optimal range based on 13 detected contacts."
            },
            {
                "name": "Bilateral Symmetry",
                "value": "91.3",
                "unit": "%",
                "confidence": "High",
                "status": "Good",
                "description": "Left and right step timing within acceptable asymmetry threshold (<10%)."
            },
            {
                "name": "Trunk Lean Angle",
                "value": "8.2",
                "unit": "deg",
                "confidence": "Medium",
                "status": "Mild Forward Lean",
                "description": "Forward lean slightly exceeds 5–7° target range; may indicate fatigue compensation."
            },
        ],
        "context_insights": [
            {
                "title": "Forefoot Contact Observation",
                "category": "Foot Strike",
                "confidence": "Medium",
                "description": "Forefoot-dominant contact pattern was observed across the majority of recorded strides.",
                "why_flagged": ["Ankle landmark anterior to heel at initial contact in >60% of frames"],
                "recommended_action": "Ensure adequate calf/Achilles loading capacity if maintaining forefoot pattern."
            }
        ],
        "recommendations": [
            "Gradually increase weekly mileage to allow tissue adaptation to forefoot loading demands.",
            "Monitor calf tightness after longer runs as an indicator of forefoot loading stress."
        ]
    }

    pdf_buffer = pdf_report_generator.generate_report(long_value_data)
    assert isinstance(pdf_buffer, io.BytesIO)
    pdf_bytes = pdf_buffer.getvalue()
    # Must be a valid PDF
    assert pdf_bytes.startswith(b"%PDF"), "Output is not a valid PDF"
    # Must have substantial content (not empty/truncated)
    assert len(pdf_bytes) > 2000, f"PDF suspiciously small: {len(pdf_bytes)} bytes"

def test_analysis_repository_operations():
    test_id = "test-repo-session-999"
    test_record = {
        "analysis_id": test_id,
        "video_id": "video-999",
        "created_at": "2026-08-18T22:00:00",
        "status": "completed",
        "cadence_spm": 172.0,
        "left_right_symmetry_pct": 95.0,
        "form_classification": "Dynamic Stride (172 SPM)",
        "overall_confidence": "High"
    }

    analysis_repository.save_analysis(test_id, test_record)
    retrieved = analysis_repository.get_analysis(test_id)
    assert retrieved is not None
    assert retrieved["analysis_id"] == test_id
    assert retrieved["cadence_spm"] == 172.0

    recent = analysis_repository.list_analyses(limit=10)
    assert len(recent) > 0
    assert any(a["analysis_id"] == test_id for a in recent)

    deleted = analysis_repository.delete_analysis(test_id)
    assert deleted is True
    assert analysis_repository.get_analysis(test_id) is None

def test_demo_analysis_endpoint():
    response = client.get("/api/analyses/demo/sample")
    assert response.status_code == 200
    data = response.json()
    assert data["analysis_id"] == "demo-runner-session-001"
    assert data["cadence_spm"] == 174.0
    assert "metrics_breakdown" in data
    assert "waveform_data" in data
    assert len(data["context_insights"]) > 0

def test_pdf_download_endpoint():
    # Fetch demo first to ensure it's in the repository
    client.get("/api/analyses/demo/sample")
    response = client.get("/api/analyses/demo-runner-session-001/report.pdf")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert len(response.content) > 1000
    assert response.content.startswith(b"%PDF")
