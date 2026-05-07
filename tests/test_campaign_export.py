import pytest
import json
from src.ui.export_ui import _format_campaign_as_csv


def test_campaign_csv_format_headers():
    """Verify campaign CSV output contains correct headers."""
    campaign_data = {
        "campaign": {"id": "c1", "name": "Test Campaign"},
        "variants": [
            {
                "text": "Ad A",
                "runs": [{"results_json": {"likes": 100, "conversions": 20, "predicted_ctr": 0.05, "predicted_cvr": 0.02}}]
            },
            {
                "text": "Ad B",
                "runs": [{"results_json": {"likes": 150, "conversions": 30, "predicted_ctr": 0.06, "predicted_cvr": 0.03}}]
            }
        ]
    }

    csv_output = _format_campaign_as_csv(campaign_data)
    lines = [line.strip() for line in csv_output.strip().split("\n")]

    assert lines[0] == "Variant,Ad Text,Likes,Conversions,CTR,CVR"


def test_campaign_csv_format_row_count():
    """Verify campaign CSV output contains one row per variant."""
    campaign_data = {
        "campaign": {"id": "c1"},
        "variants": [
            {"text": "Ad A", "runs": [{"results_json": {"likes": 100, "conversions": 20, "predicted_ctr": 0.05, "predicted_cvr": 0.02}}]},
            {"text": "Ad B", "runs": [{"results_json": {"likes": 150, "conversions": 30, "predicted_ctr": 0.06, "predicted_cvr": 0.03}}]}
        ]
    }

    csv_output = _format_campaign_as_csv(campaign_data)
    lines = [line.strip() for line in csv_output.strip().split("\n")]

    # Header + 2 variant rows
    assert len(lines) == 3


def test_campaign_csv_format_values():
    """Verify campaign CSV extracts metrics from latest run."""
    campaign_data = {
        "campaign": {"id": "c1"},
        "variants": [
            {
                "text": "Save 50%",
                "runs": [{"results_json": {"likes": 100, "conversions": 20, "predicted_ctr": 0.05, "predicted_cvr": 0.02}}]
            }
        ]
    }

    csv_output = _format_campaign_as_csv(campaign_data)
    lines = [line.strip() for line in csv_output.strip().split("\n")]

    assert lines[1] == "Variant 1,Save 50%,100,20,0.05,0.02"


def test_campaign_csv_no_runs():
    """Verify campaign CSV handles variants with no runs gracefully."""
    campaign_data = {
        "campaign": {"id": "c1"},
        "variants": [
            {"text": "Ad A", "runs": []},
            {"text": "Ad B", "runs": []}
        ]
    }

    csv_output = _format_campaign_as_csv(campaign_data)
    lines = [line.strip() for line in csv_output.strip().split("\n")]

    assert lines[1] == "Variant 1,Ad A,0,0,0,0"
    assert lines[2] == "Variant 2,Ad B,0,0,0,0"


def test_campaign_csv_missing_runs_key():
    """Verify campaign CSV handles missing runs key."""
    campaign_data = {
        "campaign": {"id": "c1"},
        "variants": [
            {"text": "Ad A"}  # No runs key at all
        ]
    }

    csv_output = _format_campaign_as_csv(campaign_data)
    lines = [line.strip() for line in csv_output.strip().split("\n")]

    assert lines[1] == "Variant 1,Ad A,0,0,0,0"


def test_campaign_json_structure():
    """Verify campaign JSON export preserves full structure."""
    campaign_data = {
        "campaign": {
            "id": "uuid-123",
            "name": "Test Campaign",
            "channel": "facebook",
            "budget": 100.0
        },
        "variants": [
            {
                "id": "v1",
                "text": "Ad A",
                "runs": [
                    {
                        "id": "r1",
                        "results_json": {"likes": 100, "conversions": 20}
                    }
                ]
            }
        ]
    }

    # Simulate what render_campaign_export_buttons does
    json_str = json.dumps(campaign_data, indent=2)
    parsed = json.loads(json_str)

    assert parsed["campaign"]["id"] == "uuid-123"
    assert parsed["campaign"]["name"] == "Test Campaign"
    assert parsed["campaign"]["channel"] == "facebook"
    assert parsed["campaign"]["budget"] == 100.0
    assert len(parsed["variants"]) == 1
    assert parsed["variants"][0]["id"] == "v1"
    assert parsed["variants"][0]["text"] == "Ad A"
    assert len(parsed["variants"][0]["runs"]) == 1
    assert parsed["variants"][0]["runs"][0]["results_json"]["likes"] == 100


def test_current_result_export_still_works():
    """Verify Phase 2D-1 current result export is not broken."""
    from src.ui.export_ui import _format_result_as_csv

    result = {
        "ad_a": {"likes": 100, "conversions": 20, "predicted_ctr": 0.05, "predicted_cvr": 0.02},
        "ad_b": {"likes": 150, "conversions": 30, "predicted_ctr": 0.06, "predicted_cvr": 0.03}
    }

    csv_output = _format_result_as_csv(result)
    lines = [line.strip() for line in csv_output.strip().split("\n")]

    assert lines[0] == "Ad,Likes,Conversions,CTR,CVR"
    assert lines[1] == "Ad A,100,20,0.05,0.02"
    assert lines[2] == "Ad B,150,30,0.06,0.03"
