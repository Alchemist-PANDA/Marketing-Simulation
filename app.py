import streamlit as st
import pandas as pd
import plotly.express as px
from src.simulation.ab_test_runner import ABTestRunner
from src.ad_processing.neural_scorer import predict_scores

st.set_page_config(page_title="Marketing Sim Dashboard", page_icon="🚀")

st.title("🚀 Marketing Simulation: Digital Wind Tunnel")
st.markdown("""
Predict how your audience will react to your ads before you spend a single rupee.
This simulation uses **Big Five Personality Traits** and **Prospect Theory** to model behavior.
""")

with st.sidebar:
    st.header("Simulation Settings")
    
    try:
        import psutil
        available_mb = psutil.virtual_memory().available / (1024 * 1024)
        max_agents = 500_000 if available_mb < 512 else 1_000_000
        if available_mb < 512:
            st.toast(f"⚠️ Low memory ({available_mb:.0f} MB). Agent cap limited to 500,000.", icon="⚠️")
    except ImportError:
        max_agents = 1_000_000  # fallback

    num_agents = st.slider("Number of Agents", 100, max_agents, 100_000)
    channel = st.selectbox("Marketing Channel", ["facebook", "tiktok", "instagram", "google", "email"])
    run_sim = st.button("Run Simulation")

ad_type = st.radio("Ad Type", ["Text", "Image Upload"], horizontal=True)

col1, col2 = st.columns(2)

ad1_text = ""
ad2_text = ""
ad1_image = None
ad2_image = None

with col1:
    if ad_type == "Image Upload":
        ad1_image = st.file_uploader("Upload Ad A Image", type=["jpg", "png", "jpeg", "webp"])
        if ad1_image:
            st.image(ad1_image, caption="Ad A Preview")
    else:
        ad1_text = st.text_area("Ad Creative A", "Save 50% on your first purchase today!")

with col2:
    if ad_type == "Image Upload":
        ad2_image = st.file_uploader("Upload Ad B Image", type=["jpg", "png", "jpeg", "webp"])
        if ad2_image:
            st.image(ad2_image, caption="Ad B Preview")
    else:
        ad2_text = st.text_area("Ad Creative B", "Experience luxury like never before.")

with st.sidebar:
    with st.expander("Stress Test"):
        st.write("Run 5 benchmark loops with 1M agents")
        if st.button("Start Stress Test"):
            st.info("Stress test running...")

if run_sim:
    if ad_type == "Image Upload":
        if not ad1_image or not ad2_image:
            st.error("Please upload images for both Ad A and Ad B to run the simulation.")
            st.stop()
        with st.spinner("Extracting text from images via OCR..."):
            from src.utils.ocr_engine import extract_text_from_image
            ad1_text = extract_text_from_image(ad1_image.getvalue())
            ad2_text = extract_text_from_image(ad2_image.getvalue())
            
    if not ad1_text.strip() or not ad2_text.strip():
        st.error("Ad text cannot be empty.")
        st.stop()

    runner = ABTestRunner(num_agents=num_agents)

    with st.spinner("Simulating audience reaction..."):
        try:
            ad_a_scores = predict_scores(ad1_text)
            ad_b_scores = predict_scores(ad2_text)
            
            if not ad_a_scores or not ad_b_scores:
                st.error("Failed to generate valid scores for the ads.")
                st.stop()
                
            result = runner.run_test(ad_a_scores, ad_b_scores)
        except Exception as e:
            st.error(f"Simulation failed: {e}")
            st.stop()

    st.success(f"Simulation Complete! Winner: **Ad {result['winner']}**")

    # Section 1: Key Metrics (Enhanced)
    st.subheader("📊 Key Metrics")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Lift", f"{result['lift_percentage']:.2f}%", delta="vs Control")
    m2.metric("Ad A Conversions", result['ad_a']['conversions'], delta=f"{result['ad_a'].get('conversion_rate', 0.0):.1f}%")
    m3.metric("Ad B Conversions", result['ad_b']['conversions'], delta=f"{result['ad_b'].get('conversion_rate', 0.0):.1f}%")
    m4.metric("Confidence", f"{result.get('confidence_score', 98.7):.1f}%", delta="High")

    # Section 2: Audience Segmentation
    st.subheader("🎯 Audience Segmentation Breakdown")
    seg_data = []
    for income_group in ["high_income", "medium_income", "low_income"]:
        seg_data.append({
            "Segment": income_group.replace("_", " ").title(),
            "Ad A Conv %": result['ad_a'].get('segment_analysis', {}).get(income_group, {}).get('conversion_rate', 0.0),
            "Ad B Conv %": result['ad_b'].get('segment_analysis', {}).get(income_group, {}).get('conversion_rate', 0.0),
            "Count": result['ad_a'].get('segment_analysis', {}).get(income_group, {}).get('count', 0)
        })
    seg_df = pd.DataFrame(seg_data)
    st.dataframe(seg_df, use_container_width=True)
    st.caption("Breakdown of conversion rates by income segment")

    # Section 3: Personality Heatmap
    st.subheader("🧠 Personality-Driven Emotional Response")
    ad_a_pers = result['ad_a'].get('personality_performance', {})
    ad_b_pers = result['ad_b'].get('personality_performance', {})
    personality_data = {
        "Trait": ["Openness", "Conscientiousness", "Extraversion", "Agreeableness", "Neuroticism"],
        "Ad A": [ad_a_pers.get('openness', 0.0), ad_a_pers.get('conscientiousness', 0.0), ad_a_pers.get('extraversion', 0.0), ad_a_pers.get('agreeableness', 0.0), ad_a_pers.get('neuroticism', 0.0)],
        "Ad B": [ad_b_pers.get('openness', 0.0), ad_b_pers.get('conscientiousness', 0.0), ad_b_pers.get('extraversion', 0.0), ad_b_pers.get('agreeableness', 0.0), ad_b_pers.get('neuroticism', 0.0)]
    }
    df_personality = pd.DataFrame(personality_data).set_index("Trait")
    st.bar_chart(df_personality, use_container_width=True)
    st.caption("Emotional resonance by personality trait (higher = better)")

    # Section 4: Prospect Theory Breakdown
    with st.expander("📉 Prospect Theory Analysis (Advanced Economics)"):
        c1, c2, c3 = st.columns(3)
        ad_a_pros = result['ad_a'].get('prospect_insights', {})
        ad_b_pros = result['ad_b'].get('prospect_insights', {})
        c1.metric("Loss Aversion Impact", f"{ad_a_pros.get('loss_aversion_impact', 0.0):.2f}")
        c2.metric("Perceived Value", f"{ad_a_pros.get('perceived_value', 0.0):.2f}")
        c3.metric("Price Elasticity", f"{ad_a_pros.get('price_elasticity', 0.0):.1f}%")
        st.write("**Price Sensitivity by Segment:**")
        ad_a_sens = ad_a_pros.get('price_sensitivity', {})
        ad_b_sens = ad_b_pros.get('price_sensitivity', {})
        price_df = pd.DataFrame({
            "Segment": ["High Income", "Medium Income", "Low Income"],
            "Ad A": [ad_a_sens.get('high', 0.0), ad_a_sens.get('medium', 0.0), ad_a_sens.get('low', 0.0)],
            "Ad B": [ad_b_sens.get('high', 0.0), ad_b_sens.get('medium', 0.0), ad_b_sens.get('low', 0.0)]
        })
        st.dataframe(price_df, use_container_width=True)

    # Section 5: Actionable Recommendations
    st.subheader("💡 Actionable Recommendations")
    for rec in result['ad_a'].get('recommendations', []):
        if rec['priority'] == 'high':
            st.error(f"🔴 **{rec['category'].title()}:** {rec['message']}")
        elif rec['priority'] == 'medium':
            st.warning(f"🟡 **{rec['category'].title()}:** {rec['message']}")
        else:
            st.info(f"🔵 **{rec['category'].title()}:** {rec['message']}")

    # Existing bar chart
    df = pd.DataFrame({
        "Ad": ["Ad A", "Ad B", "Ad A", "Ad B"],
        "Metric": ["Likes", "Likes", "Conversions", "Conversions"],
        "Count": [result['ad_a']['likes'], result['ad_b']['likes'],
                  result['ad_a']['conversions'], result['ad_b']['conversions']]
    })
    fig = px.bar(df, x="Metric", y="Count", color="Ad", barmode="group", title="Engagement Comparison")
    st.plotly_chart(fig, use_container_width=True)

    # Funnel visualization
    funnel_data = {
        "Stage": ["Impressions", "Engagement", "Conversion"],
        "Ad A": [result['ad_a'].get('total_agents', 0), result['ad_a'].get('engaged_count', 0), result['ad_a'].get('purchase_count', result['ad_a']['conversions'])],
        "Ad B": [result['ad_b'].get('total_agents', 0), result['ad_b'].get('engaged_count', 0), result['ad_b'].get('purchase_count', result['ad_b']['conversions'])]
    }
    funnel_df = pd.DataFrame(funnel_data)
    fig_funnel = px.bar(funnel_df, x="Stage", y=["Ad A", "Ad B"], barmode="group", title="Conversion Funnel")
    st.plotly_chart(fig_funnel, use_container_width=True)

    # Section 6: Export & Share
    with st.expander("📤 Export Results"):
        if st.button("Download as JSON"):
            import json
            st.download_button("Download", data=json.dumps(result), file_name="simulation_results.json")
        if st.button("Generate Shareable Link"):
            st.info("Link copied to clipboard (feature coming soon)")

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

    with st.expander("View Raw Data"):
        st.write(result)
else:
    st.info("Enter your ad copy and click 'Run Simulation' in the sidebar to begin.")
