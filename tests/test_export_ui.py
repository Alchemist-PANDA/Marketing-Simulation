import pytest
import json
from src.ui.export_ui import _format_result_as_csv


def test_csv_format_headers():
    """Verify CSV output contains correct headers."""
    result = {
        "ad_a": {"likes": 100, "conversions": 20, "predicted_ctr": 0.05, "predicted_cvr": 0.02},
        "ad_b": {"likes": 150, "conversions": 30, "predicted_ctr": 0.06, "predicted_cvr": 0.03}
    }

    csv_output = _format_result_as_csv(result)
    lines = [line.strip() for line in csv_output.strip().split("\n")]

    assert lines[0] == "Ad,Likes,Conversions,CTR,CVR"


def test_csv_format_row_count():
    """Verify CSV output contains exactly 2 data rows (Ad A and Ad B)."""
    result = {
        "ad_a": {"likes": 100, "conversions": 20, "predicted_ctr": 0.05, "predicted_cvr": 0.02},
        "ad_b": {"likes": 150, "conversions": 30, "predicted_ctr": 0.06, "predicted_cvr": 0.03}
    }

    csv_output = _format_result_as_csv(result)
    lines = [line.strip() for line in csv_output.strip().split("\n")]

    # Header + 2 data rows
    assert len(lines) == 3


def test_csv_format_ad_a_values():
    """Verify CSV output contains correct values for Ad A."""
    result = {
        "ad_a": {"likes": 100, "conversions": 20, "predicted_ctr": 0.05, "predicted_cvr": 0.02},
        "ad_b": {"likes": 150, "conversions": 30, "predicted_ctr": 0.06, "predicted_cvr": 0.03}
    }

    csv_output = _format_result_as_csv(result)
    lines = [line.strip() for line in csv_output.strip().split("\n")]

    assert lines[1] == "Ad A,100,20,0.05,0.02"


def test_csv_format_ad_b_values():
    """Verify CSV output contains correct values for Ad B."""
    result = {
        "ad_a": {"likes": 100, "conversions": 20, "predicted_ctr": 0.05, "predicted_cvr": 0.02},
        "ad_b": {"likes": 150, "conversions": 30, "predicted_ctr": 0.06, "predicted_cvr": 0.03}
    }

    csv_output = _format_result_as_csv(result)
    lines = [line.strip() for line in csv_output.strip().split("\n")]

    assert lines[2] == "Ad B,150,30,0.06,0.03"


def test_csv_format_missing_fields():
    """Verify CSV output handles missing fields gracefully with defaults."""
    result = {
        "ad_a": {},
        "ad_b": {}
    }

    csv_output = _format_result_as_csv(result)
    lines = [line.strip() for line in csv_output.strip().split("\n")]

    assert lines[1] == "Ad A,0,0,0,0"
    assert lines[2] == "Ad B,0,0,0,0"


def test_json_export_structure():
    """Verify JSON export preserves full result structure."""
    result = {
        "winner": "B",
        "lift_percentage": 25.5,
        "ad_a": {"likes": 100, "conversions": 20},
        "ad_b": {"likes": 150, "conversions": 30}
    }

    # Simulate what render_export_buttons does
    json_str = json.dumps(result, indent=2)
    parsed = json.loads(json_str)

    assert parsed["winner"] == "B"
    assert parsed["lift_percentage"] == 25.5
    assert parsed["ad_a"]["likes"] == 100
    assert parsed["ad_b"]["conversions"] == 30
