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
