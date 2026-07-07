import os

# Must be set before numpy/MKL-linked libraries are imported anywhere in the
# process, including transitively via src.* modules below.
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")

import gc
import time
import json
import streamlit as st
import pandas as pd
import plotly.express as px

from src.simulation.ab_test_runner import ABTestRunner
from src.simulation.max_engine import MaxSimulation
from src.ad_processing.ad import Ad
from src.agents.agent_generator import generate_population_arrays, population_memory_bytes
from src.ui.auth_ui import render_auth_sidebar
from src.ui.save_results_ui import render_save_results_section
from src.ui.history_ui import render_history_tab
from src.ui.export_ui import render_export_buttons
from src.ui.theme import apply_theme, render_app_header, render_metric_card, render_section_header

try:
    import psutil
    _PSUTIL_AVAILABLE = True
except ImportError:
    _PSUTIL_AVAILABLE = False

st.set_page_config(page_title="Marketing Sim Dashboard", page_icon="🚀", layout="wide")

apply_theme()
render_app_header()

if "sim_results" not in st.session_state:
    st.session_state["sim_results"] = None
if "sim_ad1" not in st.session_state:
    st.session_state["sim_ad1"] = ""
if "sim_ad2" not in st.session_state:
    st.session_state["sim_ad2"] = ""
if "last_runtime_ms" not in st.session_state:
    st.session_state["last_runtime_ms"] = None
if "last_pop_memory_mb" not in st.session_state:
    st.session_state["last_pop_memory_mb"] = None


@st.cache_data(ttl=3600, max_entries=5, show_spinner=False)
def cached_population(num_agents: int, seed):
    """Cache generated agent population arrays by (num_agents, seed)."""
    return generate_population_arrays(num_agents, seed=seed)


def get_available_ram_mb():
    if not _PSUTIL_AVAILABLE:
        return None
    try:
        return psutil.virtual_memory().available / 1e6
    except Exception:
        return None


tab1, tab2, tab3 = st.tabs(["🚀 New Simulation", "📂 History", "🤖 AI Predictions"])

with tab1:
    with st.sidebar:
        render_auth_sidebar()
        st.divider()
        st.header("Simulation Settings")

        scale_tier = st.radio(
            "Scale",
            ["Standard (100 - 2,000)", "Large (2,000 - 100,000)", "Massive (100,000 - 1,000,000)"],
            index=0
        )
        if scale_tier.startswith("Standard"):
            num_agents = st.slider("Number of Agents", 100, 2000, 500, step=100)
        elif scale_tier.startswith("Large"):
            num_agents = st.slider("Number of Agents", 2000, 100_000, 10_000, step=1000)
        else:
            num_agents = st.slider("Number of Agents", 100_000, 1_000_000, 100_000, step=10_000)

        proceed_large = True
        if num_agents > 500_000:
            st.warning(f"This will use ~{4.6 * (num_agents / 100_000):.1f} MB of RAM. Proceed?")
            proceed_large = st.checkbox("Yes, I understand — run anyway", key="proceed_large")

        channel = st.selectbox("Marketing Channel", ["facebook", "tiktok", "instagram", "google", "email"])
        price = st.slider("Product Price ($)", 1.0, 500.0, 20.0, step=1.0)
        objective = st.radio("Optimization Objective", ["conversions", "engagement", "conversion_rate"])
        st.divider()
        run_sim = st.button("Run Simulation", type="primary", use_container_width=True, disabled=not proceed_large)
        if st.session_state["sim_results"] is not None:
            if st.button("Clear Results", use_container_width=True):
                st.session_state["sim_results"] = None
                st.session_state["sim_ad1"] = ""
                st.session_state["sim_ad2"] = ""
                st.rerun()

        st.divider()
        st.caption("⚡ Engine Stats")
        mc1, mc2 = st.columns(2)
        with mc1:
            mem_val = st.session_state["last_pop_memory_mb"]
            st.metric("Population RAM", f"{mem_val:.2f} MB" if mem_val else "—")
        with mc2:
            rt_val = st.session_state["last_runtime_ms"]
            st.metric("Last Runtime", f"{rt_val:.1f} ms" if rt_val else "—")
        avail_ram = get_available_ram_mb()
        if avail_ram is not None:
            st.caption(f"System RAM available: {avail_ram:,.0f} MB")
        else:
            st.caption("Install `psutil` for system RAM monitoring")

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

            # Lazy import: OCR model only loads when image mode is actually used.
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

        master_population = cached_population(num_agents, None)
        mem_bytes = population_memory_bytes(master_population)
        runner = ABTestRunner(num_agents=num_agents, master_population=master_population)

        with st.status("Running Simulation...", expanded=True) as status:
            progress_bar = st.progress(0)
            status_text = st.empty()

            def on_progress(pct, msg):
                progress_bar.progress(min(pct, 1.0))
                agent_count = int(pct * num_agents)
                status_text.markdown(f"**{msg}** — Processing agent {agent_count:,} / {num_agents:,}")

            t0 = time.perf_counter()
            result = runner.run_test(
                ad1_text, ad2_text,
                channel=channel, price=price, objective=objective,
                progress_callback=on_progress
            )
            runtime_ms = (time.perf_counter() - t0) * 1000
            progress_bar.progress(1.0)
            status.update(label=f"Simulation Complete! ({runtime_ms:.1f} ms)", state="complete", expanded=False)

        st.session_state["sim_results"] = result
        st.session_state["sim_ad1"] = ad1_text
        st.session_state["sim_ad2"] = ad2_text
        st.session_state["last_runtime_ms"] = runtime_ms
        st.session_state["last_pop_memory_mb"] = mem_bytes / 1e6

        del master_population, runner
        gc.collect()

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
            if st.download_button(
                "Download Summary (JSON)",
                data=json.dumps(summary, indent=2),
                file_name="simulation_summary.json",
                mime="application/json"
            ):
                gc.collect()
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

    with st.expander("⚡ Stress Test / Benchmark"):
        st.caption("Run the raw simulation engine repeatedly at full scale to see real throughput on this machine.")
        bench_n = st.number_input("Benchmark Agent Count", min_value=1000, max_value=1_000_000, value=1_000_000, step=10_000)
        if st.button("Run Benchmark (5x)"):
            ad = Ad(text="Limited time offer — act now!", channel="facebook", creative_type="text", price=20.0)
            bench_pop = cached_population(int(bench_n), 999)
            mem_mb = population_memory_bytes(bench_pop) / 1e6

            rss_before = None
            if _PSUTIL_AVAILABLE:
                try:
                    rss_before = psutil.Process().memory_info().rss / 1e6
                except Exception:
                    rss_before = None

            times_ms = []
            peak_rss = rss_before or 0
            for i in range(5):
                sim = MaxSimulation(seed=999, population={k: v.copy() for k, v in bench_pop.items()})
                t0 = time.perf_counter()
                sim.simulate_exposure(ad)
                times_ms.append((time.perf_counter() - t0) * 1000)
                if _PSUTIL_AVAILABLE:
                    try:
                        peak_rss = max(peak_rss, psutil.Process().memory_info().rss / 1e6)
                    except Exception:
                        pass
                del sim

            del bench_pop
            gc.collect()

            bc1, bc2, bc3 = st.columns(3)
            with bc1:
                st.metric("Min Runtime", f"{min(times_ms):.2f} ms")
            with bc2:
                st.metric("Avg Runtime", f"{sum(times_ms)/len(times_ms):.2f} ms")
            with bc3:
                st.metric("Max Runtime", f"{max(times_ms):.2f} ms")

            st.metric("Population Array Memory", f"{mem_mb:.2f} MB")
            if _PSUTIL_AVAILABLE and rss_before is not None:
                st.metric("Peak Process Memory (RSS)", f"{peak_rss:.1f} MB")

            bench_df = pd.DataFrame({"Run": [f"Run {i+1}" for i in range(5)], "Runtime (ms)": times_ms})
            st.bar_chart(bench_df.set_index("Run"))

with tab2:
    render_history_tab()

with tab3:
    st.header("AI-Enhanced CTR Prediction")
    st.markdown("Predict click-through rates using Classic simulation, trained ML models, or a weighted ensemble.")

    ai_mode = st.radio(
        "Prediction Mode",
        ["Classic (Simulation Engine)", "AI (ML Model)", "Ensemble (Weighted Blend)"],
        horizontal=True,
        key="ai_pred_mode"
    )

    mode_map = {
        "Classic (Simulation Engine)": "classic",
        "AI (ML Model)": "ai",
        "Ensemble (Weighted Blend)": "ensemble",
    }
    selected_mode = mode_map[ai_mode]

    if selected_mode == "ensemble":
        ai_weight = st.slider("AI Model Weight", 0.0, 1.0, 0.5, step=0.1, key="ai_weight_slider",
                              help="0.0 = pure simulation, 1.0 = pure AI model")

    ai_ad_text = st.text_area("Ad Creative Text", "Save 50% on your first purchase today!",
                              height=120, key="ai_ad_text")

    col_predict, col_explain = st.columns(2)
    with col_predict:
        run_ai_pred = st.button("Predict CTR", type="primary", key="run_ai_pred")
    with col_explain:
        run_explain = st.button("Explain Prediction", key="run_explain")

    if run_ai_pred and ai_ad_text.strip():
        from src.ai.predictor import get_predictor
        predictor = get_predictor()

        kwargs = {}
        if selected_mode == "ensemble":
            kwargs["ai_weight"] = ai_weight

        with st.spinner("Running prediction..."):
            result = predictor.predict(ai_ad_text, mode=selected_mode, **kwargs)

        st.success(f"Predicted CTR: **{result['predicted_ctr']:.4%}** (mode: {result['mode']})")

        if "scores" in result:
            sc1, sc2, sc3 = st.columns(3)
            with sc1:
                render_metric_card("Price Score", f"{result['scores']['price_score']:.2f}", "💰")
            with sc2:
                render_metric_card("Trust Score", f"{result['scores']['trust_score']:.2f}", "🛡️")
            with sc3:
                render_metric_card("Urgency Score", f"{result['scores']['urgency_score']:.2f}", "⏰")

        if result['mode'] == 'ensemble':
            e1, e2 = st.columns(2)
            with e1:
                st.metric("Classic CTR", f"{result['classic_ctr']:.4%}")
            with e2:
                st.metric("AI CTR", f"{result['ai_ctr']:.4%}")

        if "engagement" in result:
            st.subheader("Engagement Breakdown")
            eng = result["engagement"]
            eng_cols = st.columns(3)
            with eng_cols[0]:
                st.metric("Likes", f"{eng['likes']:,}")
            with eng_cols[1]:
                st.metric("Shares", f"{eng['shares']:,}")
            with eng_cols[2]:
                st.metric("Conversions", f"{eng['conversions']:,}")

        with st.expander("Raw Prediction Data"):
            st.json(result)

    if run_explain and ai_ad_text.strip():
        from src.ai.predictor import get_predictor
        predictor = get_predictor()

        with st.spinner("Generating explanation..."):
            explanation = predictor.explain(ai_ad_text)

        st.subheader("Feature Explanations")
        for exp in explanation['explanations']:
            direction_icon = "✅" if exp['direction'] == 'positive' else "⚠️" if exp['direction'] == 'negative' else "➖"
            with st.expander(f"{direction_icon} {exp['factor']}", expanded=True):
                st.write(f"**Impact:** {exp['impact']}")
                st.write(f"**Explanation:** {exp['explanation']}")
                if exp['keywords']:
                    st.write(f"**Keywords matched:** {', '.join(exp['keywords'])}")

        st.info(f"**Recommendation:** {explanation['recommendation']}")
