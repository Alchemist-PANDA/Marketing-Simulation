"""
Streamlit UI component for displaying campaign history.
"""
import streamlit as st
from typing import List, Dict, Any
from src.services.persistence_service import PersistenceService
from src.ui.export_ui import render_campaign_export_buttons


def render_history_tab():
    """Render the campaign history view for the main area tab."""
    st.header("📂 Campaign History")

    auth_mode = st.session_state.get("auth_mode")
    user = st.session_state.get("user")

    # 1. Access Control
    if auth_mode == "local":
        st.info("📂 History unavailable in local mode. Connect to Supabase to enable persistence.")
        return

    if not user:
        st.warning("🔐 Log in via the sidebar to view your saved campaigns.")
        return

    # Extract user ID safely whether it's a dict or an object
    user_id = user.get("id") if isinstance(user, dict) else getattr(user, "id", None)

    # 2. Fetch Data
    service = PersistenceService()
    with st.spinner("Loading history..."):
        result = service.list_campaigns(user_id)

    if result["status"] != "success":
        st.error(f"❌ Failed to load history: {result.get('message', 'Unknown error')}")
        return

    campaigns = result.get("data", [])

    if not campaigns:
        st.info("📭 No saved campaigns yet. Run a simulation and click 'Save Results' to get started.")
        return

    # 3. Display List
    st.write(f"Showing last {len(campaigns)} campaigns.")

    for campaign in campaigns:
        render_campaign_entry(campaign, user["id"])


def render_campaign_entry(campaign: Dict[str, Any], user_id: str):
    """Render a single campaign entry with expandable details."""
    name = campaign.get("name", "Unnamed Campaign")
    channel = campaign.get("channel", "unknown")
    date_str = campaign.get("created_at", "")

    # Format timestamp for display
    try:
        from datetime import datetime
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        display_date = dt.strftime("%b %d, %Y - %H:%M")
    except Exception:
        display_date = date_str

    with st.expander(f"📊 {name} ({channel}) — {display_date}"):
        if st.button(f"Load Details", key=f"load_{campaign['id']}"):
            _show_campaign_details(campaign["id"], user_id)


def _show_campaign_details(campaign_id: str, user_id: str):
    """Fetch and display the detailed results for a campaign."""
    service = PersistenceService()
    res = service.get_campaign_details(campaign_id, user_id)

    if res["status"] != "success":
        st.error(f"Failed to load details: {res.get('message')}")
        return

    variants = res.get("variants", [])

    if not variants:
        st.warning("No ad variants found for this campaign.")
        return

    # Display variants side-by-side if exactly 2
    if len(variants) == 2:
        v1, v2 = variants[0], variants[1]
        col1, col2 = st.columns(2)

        with col1:
            _render_variant_run_summary("Ad A", v1)
        with col2:
            _render_variant_run_summary("Ad B", v2)
    else:
        for i, variant in enumerate(variants):
            _render_variant_run_summary(f"Variant {i+1}", variant)

    # Export buttons after variant display
    render_campaign_export_buttons(res)


def _render_variant_run_summary(label: str, variant: Dict[str, Any]):
    """Render summary for a specific variant and its latest run."""
    st.subheader(label)
    st.info(variant.get("text", "No text"))

    runs = variant.get("runs", [])
    if not runs:
        st.write("No simulation data saved for this variant.")
        return

    # Show latest run
    run = runs[0] # Usually only one per variant in current flow
    data = run.get("results_json", {})

    st.write(f"**Likes:** {data.get('likes', 0)}")
    st.write(f"**Conversions:** {data.get('conversions', 0)}")
    st.write(f"**CTR:** {data.get('predicted_ctr', 0):.2%}")
    st.write(f"**CVR:** {data.get('predicted_cvr', 0):.2%}")
