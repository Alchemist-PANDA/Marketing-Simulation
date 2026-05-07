import streamlit as st
import pandas as pd
import plotly.express as px
from src.simulation.ab_test_runner import ABTestRunner
from src.ui.auth_ui import render_auth_sidebar
from src.ui.save_results_ui import render_save_results_section
from src.ui.history_ui import render_history_tab
from src.ui.export_ui import render_export_buttons
from src.ui.theme import apply_theme, render_app_header, render_metric_card, render_section_header

st.set_page_config(page_title="Marketing Sim Dashboard", page_icon="🚀")

apply_theme()
render_app_header()

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
        with m1:
            render_metric_card("Lift", f"{result['lift_percentage']:.2f}%", "📈")
        with m2:
            render_metric_card("Ad A Conversions", str(result['ad_a']['conversions']), "🎯")
        with m3:
            render_metric_card("Ad B Conversions", str(result['ad_b']['conversions']), "🎯")

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
        render_section_header("Forensic Feedback", "🕵️")
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
