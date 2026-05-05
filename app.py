import streamlit as st
import pandas as pd
import plotly.express as px
from src.simulation.ab_test_runner import ABTestRunner
from src.ui.auth_ui import render_auth_sidebar
from src.ui.save_results_ui import render_save_results_section
from src.ui.history_ui import render_history_tab
from src.ui.export_ui import render_export_buttons

st.set_page_config(page_title="Marketing Sim Dashboard", page_icon="🚀")

st.title("🚀 Marketing Simulation: Digital Wind Tunnel")
st.markdown("""
Predict how your audience will react to your ads before you spend a single rupee.
This simulation uses **Big Five Personality Traits** and **Prospect Theory** to model behavior.
""")

tab1, tab2 = st.tabs(["🚀 New Simulation", "📂 History"])

with tab1:
    with st.sidebar:
        render_auth_sidebar()
        st.divider()
        st.header("Simulation Settings")
        num_agents = st.slider("Number of Agents", 100, 2000, 500)
        channel = st.selectbox("Marketing Channel", ["facebook", "tiktok", "instagram", "google", "email"])
        run_sim = st.button("Run Simulation")

    col1, col2 = st.columns(2)

    with col1:
        ad1_text = st.text_area("Ad Creative A", "Save 50% on your first purchase today!")

    with col2:
        ad2_text = st.text_area("Ad Creative B", "Experience luxury like never before.")

    if run_sim:
        runner = ABTestRunner(num_agents=num_agents)

        with st.spinner("Simulating audience reaction..."):
            result = runner.run_test(ad1_text, ad2_text, channel=channel)

        st.success(f"Simulation Complete! Winner: **Ad {result['winner']}**")

        # Metrics
        m1, m2, m3 = st.columns(3)
        m1.metric("Lift", f"{result['lift_percentage']:.2f}%")
        m2.metric("Ad A Conversions", result['ad_a']['conversions'])
        m3.metric("Ad B Conversions", result['ad_b']['conversions'])

        # Visualization
        df = pd.DataFrame({
            "Ad": ["Ad A", "Ad B", "Ad A", "Ad B"],
            "Metric": ["Likes", "Likes", "Conversions", "Conversions"],
            "Count": [result['ad_a']['likes'], result['ad_b']['likes'],
                      result['ad_a']['conversions'], result['ad_b']['conversions']]
        })

        fig = px.bar(df, x="Metric", y="Count", color="Ad", barmode="group", title="Engagement Comparison")
        st.plotly_chart(fig, use_container_width=True)

        # Forensic Analysis
        st.header("🕵️ Forensic Feedback")
        fa1, fa2 = st.columns(2)
        with fa1:
            st.subheader("Ad A Analysis")
            for reason in result['ad_a']['analysis']['failure_reasons']:
                st.warning(reason)
        with fa2:
            st.subheader("Ad B Analysis")
            for reason in result['ad_b']['analysis']['failure_reasons']:
                st.warning(reason)

        # Save Results Section
        render_save_results_section(result, ad1_text, ad2_text, channel, num_agents)

        # Export Section
        render_export_buttons(result)

        with st.expander("View Raw Data"):
            st.write(result)
    else:
        st.info("Enter your ad copy and click 'Run Simulation' in the sidebar to begin.")

with tab2:
    render_history_tab()
