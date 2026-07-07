"""
Streamlit UI component for saving simulation results.
Handles save button rendering and persistence logic.
"""
import streamlit as st
from typing import Dict, Any
from datetime import datetime
from src.services.persistence_service import PersistenceService


def render_save_results_section(result: Dict[str, Any], ad1_text: str, ad2_text: str,
                                 channel: str, num_agents: int):
    """
    Render the save results section with button and status messages.

    Args:
        result: Full A/B test result dictionary
        ad1_text: Ad A creative text
        ad2_text: Ad B creative text
        channel: Marketing channel
        num_agents: Number of agents in simulation
    """
    st.divider()
    st.subheader("💾 Save Results")

    # Determine if save is available
    can_save = False
    save_tooltip = ""

    auth_mode = st.session_state.get("auth_mode")
    user = st.session_state.get("user", {})

    if auth_mode == "local":
        save_tooltip = "Persistence disabled in local mode"
    elif not user.get("is_authenticated") or user.get("mode") != "supabase":
        save_tooltip = "Log in to save results"
    else:
        can_save = True
        save_tooltip = "Save this simulation to your account"

    if st.button("Save Results", disabled=not can_save, help=save_tooltip, key="save_results_btn"):
        _handle_save(result, ad1_text, ad2_text, channel, num_agents, user["id"])


def _handle_save(result: Dict[str, Any], ad1_text: str, ad2_text: str,
                 channel: str, num_agents: int, user_id: str):
    """
    Handle the save operation with proper error handling and feedback.

    Args:
        result: Full A/B test result dictionary
        ad1_text: Ad A creative text
        ad2_text: Ad B creative text
        channel: Marketing channel
        num_agents: Number of agents in simulation
        user_id: Authenticated user ID
    """
    service = PersistenceService()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

    # Step 1: Save campaign
    campaign_res = service.save_campaign(
        user_id=user_id,
        name=f"A/B Test: {channel} - {timestamp}",
        channel=channel,
        budget=0.0
    )

    if not campaign_res["saved"]:
        if campaign_res["status"] == "disabled":
            st.info("ℹ️ Persistence disabled in local mode. Results not saved.")
        else:
            st.error(f"❌ Failed to save campaign: {campaign_res['message']}")
        return

    campaign_id = campaign_res["id"]

    # Step 2: Save Ad A variant
    ad_a_variant_res = service.save_ad_variant(
        user_id=user_id,
        campaign_id=campaign_id,
        text=ad1_text,
        price=20.0,
        category="general",
        scores={
            "likes": result['ad_a']['likes'],
            "conversions": result['ad_a']['conversions'],
            "shares": result['ad_a']['shares'],
            "predicted_ctr": result['ad_a']['analysis']['predicted_ctr'],
            "predicted_cvr": result['ad_a']['analysis']['predicted_cvr']
        }
    )

    if not ad_a_variant_res["saved"]:
        st.error(f"❌ Failed to save Ad A variant: {ad_a_variant_res['message']}")
        return

    ad_a_variant_id = ad_a_variant_res["id"]

    # Step 3: Save Ad A simulation run
    ad_a_run_res = service.save_simulation_run(
        user_id=user_id,
        variant_id=ad_a_variant_id,
        results={
            "likes": result['ad_a']['likes'],
            "conversions": result['ad_a']['conversions'],
            "shares": result['ad_a']['shares'],
            "predicted_ctr": result['ad_a']['analysis']['predicted_ctr'],
            "predicted_cvr": result['ad_a']['analysis']['predicted_cvr'],
            "confidence_score": result['ad_a']['analysis']['confidence_score'],
            "failure_reasons": result['ad_a']['analysis']['failure_reasons'],
            "num_agents": num_agents,
            "channel": channel
        }
    )

    if not ad_a_run_res["saved"]:
        st.error(f"❌ Failed to save Ad A run: {ad_a_run_res['message']}")
        return

    # Step 4: Save Ad B variant
    ad_b_variant_res = service.save_ad_variant(
        user_id=user_id,
        campaign_id=campaign_id,
        text=ad2_text,
        price=20.0,
        category="general",
        scores={
            "likes": result['ad_b']['likes'],
            "conversions": result['ad_b']['conversions'],
            "shares": result['ad_b']['shares'],
            "predicted_ctr": result['ad_b']['analysis']['predicted_ctr'],
            "predicted_cvr": result['ad_b']['analysis']['predicted_cvr']
        }
    )

    if not ad_b_variant_res["saved"]:
        st.error(f"❌ Failed to save Ad B variant: {ad_b_variant_res['message']}")
        return

    ad_b_variant_id = ad_b_variant_res["id"]

    # Step 5: Save Ad B simulation run
    ad_b_run_res = service.save_simulation_run(
        user_id=user_id,
        variant_id=ad_b_variant_id,
        results={
            "likes": result['ad_b']['likes'],
            "conversions": result['ad_b']['conversions'],
            "shares": result['ad_b']['shares'],
            "predicted_ctr": result['ad_b']['analysis']['predicted_ctr'],
            "predicted_cvr": result['ad_b']['analysis']['predicted_cvr'],
            "confidence_score": result['ad_b']['analysis']['confidence_score'],
            "failure_reasons": result['ad_b']['analysis']['failure_reasons'],
            "num_agents": num_agents,
            "channel": channel
        }
    )

    if not ad_b_run_res["saved"]:
        st.error(f"❌ Failed to save Ad B run: {ad_b_run_res['message']}")
        return

    # All saves succeeded
    st.success("✅ Results saved successfully!")
