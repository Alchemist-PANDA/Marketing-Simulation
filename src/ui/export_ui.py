"""
Streamlit UI component for exporting simulation results.
"""
import streamlit as st
import json
import pandas as pd
from typing import Dict, Any
from io import StringIO


def render_export_buttons(result: Dict[str, Any]):
    """Render export buttons for the current simulation result."""
    st.subheader("📥 Export Results")

    col1, col2 = st.columns(2)

    with col1:
        json_str = json.dumps(result, indent=2)
        st.download_button(
            label="Download JSON",
            data=json_str,
            file_name="simulation_result.json",
            mime="application/json"
        )

    with col2:
        csv_str = _format_result_as_csv(result)
        st.download_button(
            label="Download CSV",
            data=csv_str,
            file_name="simulation_result.csv",
            mime="text/csv"
        )


def render_campaign_export_buttons(campaign_data: Dict[str, Any]):
    """Render export buttons for a saved campaign from History."""
    st.subheader("📥 Export Campaign")

    campaign = campaign_data.get("campaign", {})
    campaign_id = campaign.get("id", "unknown")
    # Use first 8 chars of campaign ID for filename
    campaign_slug = campaign_id[:8] if len(campaign_id) >= 8 else campaign_id

    col1, col2 = st.columns(2)

    with col1:
        json_str = json.dumps(campaign_data, indent=2)
        st.download_button(
            label="Download JSON",
            data=json_str,
            file_name=f"campaign_{campaign_slug}.json",
            mime="application/json"
        )

    with col2:
        csv_str = _format_campaign_as_csv(campaign_data)
        st.download_button(
            label="Download CSV",
            data=csv_str,
            file_name=f"campaign_{campaign_slug}.csv",
            mime="text/csv"
        )


def _format_result_as_csv(result: Dict[str, Any]) -> str:
    """Convert simulation result to CSV format."""
    rows = []

    # Ad A row
    ad_a = result.get("ad_a", {})
    rows.append({
        "Ad": "Ad A",
        "Likes": ad_a.get("likes", 0),
        "Conversions": ad_a.get("conversions", 0),
        "CTR": ad_a.get("predicted_ctr", 0),
        "CVR": ad_a.get("predicted_cvr", 0)
    })

    # Ad B row
    ad_b = result.get("ad_b", {})
    rows.append({
        "Ad": "Ad B",
        "Likes": ad_b.get("likes", 0),
        "Conversions": ad_b.get("conversions", 0),
        "CTR": ad_b.get("predicted_ctr", 0),
        "CVR": ad_b.get("predicted_cvr", 0)
    })

    # Convert to CSV string
    df = pd.DataFrame(rows)
    csv_buffer = StringIO()
    df.to_csv(csv_buffer, index=False)
    return csv_buffer.getvalue()


def _format_campaign_as_csv(campaign_data: Dict[str, Any]) -> str:
    """Convert saved campaign to CSV format (one row per variant)."""
    rows = []
    variants = campaign_data.get("variants", [])

    for i, variant in enumerate(variants):
        variant_label = f"Variant {i+1}"
        ad_text = variant.get("text", "")
        runs = variant.get("runs", [])

        # Use latest run metrics if available
        if runs:
            latest_run = runs[0]  # Runs are already sorted by created_at desc
            results = latest_run.get("results_json", {})
            likes = results.get("likes", 0)
            conversions = results.get("conversions", 0)
            ctr = results.get("predicted_ctr", 0)
            cvr = results.get("predicted_cvr", 0)
        else:
            likes = conversions = ctr = cvr = 0

        rows.append({
            "Variant": variant_label,
            "Ad Text": ad_text,
            "Likes": likes,
            "Conversions": conversions,
            "CTR": ctr,
            "CVR": cvr
        })

    # Convert to CSV string
    df = pd.DataFrame(rows)
    csv_buffer = StringIO()
    df.to_csv(csv_buffer, index=False)
    return csv_buffer.getvalue()

