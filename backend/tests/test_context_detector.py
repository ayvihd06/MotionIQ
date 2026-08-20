import pytest
from app.api.schemas.context import (
    ProvenanceField, DetectedVideoContext, OptionalUserContext, AnalysisContext
)

def test_provenance_field_schema():
    field = ProvenanceField[str](
        value="Road / Asphalt",
        source="computer_vision",
        confidence=0.82
    )
    assert field.value == "Road / Asphalt"
    assert field.source == "computer_vision"
    assert field.confidence == 0.82
    assert field.user_confirmed is False

def test_optional_user_context_bmi():
    ctx = OptionalUserContext(
        height_cm=180.0,
        weight_kg=75.0
    )
    height_m = ctx.height_cm / 100.0
    ctx.bmi = round(ctx.weight_kg / (height_m * height_m), 1)
    assert ctx.bmi == 23.1
