import streamlit as st
import pandas as pd
import json
import plotly.express as px
from src.simulation.ab_test_runner import ABTestRunner
from src.ui.auth_ui import render_auth_sidebar
from src.ui.save_results_ui import render_save_results_section
from src.ui.history_ui import render_history_tab
from src.ui.export_ui import render_export_buttons
from src.ui.theme import apply_theme, render_app_header, render_metric_card, render_section_header

st.set_page_config(page_title="Marketing Sim Dashboard", page_icon="🚀", layout="wide")

apply_theme()
render_app_header()

if "sim_results" not in st.session_state:
    st.session_state["sim_results"] = None
if "sim_ad1" not in st.session_state:
    st.session_state["sim_ad1"] = ""
if "sim_ad2" not in st.session_state:
    st.session_state["sim_ad2"] = ""

tab1, tab2 = st.tabs(["🚀 New Simulation", "📂 History"])

with tab1:
    with st.sidebar:
        render_auth_sidebar()
        st.divider()
        st.header("Simulation Settings")
        num_agents = st.slider("Number of Agents", 100, 10000, 500, step=100)
        channel = st.selectbox("Marketing Channel", ["facebook", "tiktok", "instagram", "google", "email"])
        price = st.slider("Product Price ($)", 1.0, 500.0, 20.0, step=1.0)
        objective = st.radio("Optimization Objective", ["conversions", "engagement", "conversion_rate"])
        st.divider()
        run_sim = st.button("Run Simulation", type="primary", use_container_width=True)
        if st.session_state["sim_results"] is not None:
            if st.button("Clear Results", use_container_width=True):
                st.session_state["sim_results"] = None
                st.session_state["sim_ad1"] = ""
                st.session_state["sim_ad2"] = ""
                st.rerun()

    input_method = st.radio("Input Method", ["Text", "Image Upload"], horizontal=True)

    ad1_text = ""
    ad2_text = ""
    uploaded_img_a = None
    uploaded_img_b = None

    if input_method == "Text":
        col1, col2 = st.columns(2)
        with col1:
            ad1_text = st.text_area("Ad Creative A", "Save 50% on your first purchase today!", height=150)
        with col2:
            ad2_text = st.text_area("Ad Creative B", "Experience luxury like never before.", height=150)
    else:
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Ad A Image")
            uploaded_img_a = st.file_uploader(
                "Upload Ad A screenshot", type=["jpg", "jpeg", "png", "webp"],
                key="img_a"
            )
            if uploaded_img_a:
                st.image(uploaded_img_a, caption="Ad A Preview", use_container_width=True)
        with col2:
            st.subheader("Ad B Image")
            uploaded_img_b = st.file_uploader(
                "Upload Ad B screenshot", type=["jpg", "jpeg", "png", "webp"],
                key="img_b"
            )
            if uploaded_img_b:
                st.image(uploaded_img_b, caption="Ad B Preview", use_container_width=True)

    if run_sim:
        if input_method == "Image Upload":
            if not uploaded_img_a or not uploaded_img_b:
                st.error("Please upload images for both Ad A and Ad B.")
                st.stop()

            from src.utils.ocr_engine import extract_text_from_image

            with st.spinner("Extracting text from Ad A image..."):
                ad1_text = extract_text_from_image(uploaded_img_a.getvalue())
            if not ad1_text:
                st.error("No readable text found in Ad A image. Please upload a clearer image.")
                st.stop()

            with st.spinner("Extracting text from Ad B image..."):
                ad2_text = extract_text_from_image(uploaded_img_b.getvalue())
            if not ad2_text:
                st.error("No readable text found in Ad B image. Please upload a clearer image.")
                st.stop()

            st.info(f"**Extracted Ad A text:** {ad1_text}")
            st.info(f"**Extracted Ad B text:** {ad2_text}")

        if not ad1_text or not ad1_text.strip():
            st.error("Ad Creative A text cannot be empty. Please enter ad copy or upload an image.")
            st.stop()
        if not ad2_text or not ad2_text.strip():
            st.error("Ad Creative B text cannot be empty. Please enter ad copy or upload an image.")
            st.stop()

        runner = ABTestRunner(num_agents=num_agents)

        with st.status("Running Simulation...", expanded=True) as status:
            progress_bar = st.progress(0)
            status_text = st.empty()

            def on_progress(pct, msg):
                progress_bar.progress(min(pct, 1.0))
                agent_count = int(pct * num_agents)
                status_text.markdown(f"**{msg}** — Processing agent {agent_count:,} / {num_agents:,}")

            result = runner.run_test(
                ad1_text, ad2_text,
                channel=channel, price=price, objective=objective,
                progress_callback=on_progress
            )
            progress_bar.progress(1.0)
            status.update(label="Simulation Complete!", state="complete", expanded=False)

        st.session_state["sim_results"] = result
        st.session_state["sim_ad1"] = ad1_text
        st.session_state["sim_ad2"] = ad2_text

    result = st.session_state.get("sim_results")
    if result:
        ad1_text_display = st.session_state.get("sim_ad1", "")
        ad2_text_display = st.session_state.get("sim_ad2", "")

        st.success(f"Simulation Complete! Winner: **Ad {result['winner']}** (Objective: {result['objective']})")

        m1, m2, m3, m4 = st.columns(4)
        with m1:
            render_metric_card("Lift", f"{result['lift_percentage']:.2f}%", "📈")
        with m2:
            render_metric_card("Ad A Conversions", str(result['ad_a']['conversions']), "🎯")
        with m3:
            render_metric_card("Ad B Conversions", str(result['ad_b']['conversions']), "🎯")
        with m4:
            render_metric_card("Objective", result['objective'].replace('_', ' ').title(), "⚡")

        df = pd.DataFrame({
            "Ad": ["Ad A", "Ad B", "Ad A", "Ad B", "Ad A", "Ad B"],
            "Metric": ["Likes", "Likes", "Conversions", "Conversions", "Shares", "Shares"],
            "Count": [
                result['ad_a']['likes'], result['ad_b']['likes'],
                result['ad_a']['conversions'], result['ad_b']['conversions'],
                result['ad_a']['shares'], result['ad_b']['shares']
            ]
        })

        fig = px.bar(df, x="Metric", y="Count", color="Ad", barmode="group",
                     title="Engagement Comparison",
                     color_discrete_map={"Ad A": "#4F46E5", "Ad B": "#10B981"})
        st.plotly_chart(fig, use_container_width=True)

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

        render_save_results_section(result, ad1_text_display, ad2_text_display, channel, num_agents)
        render_export_buttons(result)

        render_section_header("Export Summary", "📥")
        summary = {
            "winner": result['winner'],
            "lift_percentage": result['lift_percentage'],
            "objective": result['objective'],
            "ad_a": {
                "likes": result['ad_a']['likes'],
                "conversions": result['ad_a']['conversions'],
                "shares": result['ad_a']['shares'],
                "cohort_size": result['ad_a'].get('cohort_size', num_agents // 2),
                "failure_reasons": result['ad_a']['analysis']['failure_reasons']
            },
            "ad_b": {
                "likes": result['ad_b']['likes'],
                "conversions": result['ad_b']['conversions'],
                "shares": result['ad_b']['shares'],
                "cohort_size": result['ad_b'].get('cohort_size', num_agents // 2),
                "failure_reasons": result['ad_b']['analysis']['failure_reasons']
            }
        }
        col_dl1, col_dl2 = st.columns(2)
        with col_dl1:
            st.download_button(
                "Download Summary (JSON)",
                data=json.dumps(summary, indent=2),
                file_name="simulation_summary.json",
                mime="application/json"
            )
        with col_dl2:
            csv_rows = []
            for label, data in [("Ad A", summary["ad_a"]), ("Ad B", summary["ad_b"])]:
                csv_rows.append({
                    "Ad": label,
                    "Likes": data["likes"],
                    "Conversions": data["conversions"],
                    "Shares": data["shares"],
                    "Cohort Size": data["cohort_size"],
                    "Failure Reasons": "; ".join(data["failure_reasons"])
                })
            csv_df = pd.DataFrame(csv_rows)
            st.download_button(
                "Download Summary (CSV)",
                data=csv_df.to_csv(index=False),
                file_name="simulation_summary.csv",
                mime="text/csv"
            )

        with st.expander("View Raw Data"):
            st.json(result)
    elif not run_sim:
        st.info("Enter your ad copy and click 'Run Simulation' in the sidebar to begin.")

with tab2:
    render_history_tab()
