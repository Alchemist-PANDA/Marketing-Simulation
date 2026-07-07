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
from dotenv import load_dotenv
load_dotenv()
from src.simulation.ab_test_runner import ABTestRunner
from src.ad_processing.neural_scorer import predict_scores
from src.utils.ai_reasoning import get_ai_insights

@st.cache_data
def get_benchmarks():
    return {
        "industry_avg_conversion": 2.5,
        "industry_avg_engagement": 18.0,
        "seasonality_factor": "June is peak for e-commerce"
    }
benchmarks = get_benchmarks()

try:
    import psutil
    _PSUTIL_AVAILABLE = True
except ImportError:
    _PSUTIL_AVAILABLE = False

# Check if user is logged in
from src.ui.auth_ui import initialize_auth_session
initialize_auth_session()

if "user" not in st.session_state or st.session_state.user is None:
    if st.query_params.get("login") == "true":
        st.switch_page("pages/_Login.py")
    elif st.query_params.get("register") == "true":
        st.switch_page("pages/_Register.py")
    else:
        # Render the custom SaaS landing page
        import streamlit.components.v1 as components
        import os
        
        # Hide Streamlit's default UI elements to make it full screen
        st.markdown("""
            <style>
                .block-container {
                    padding: 0rem !important;
                    max-width: 100% !important;
                }
                header {
                    display: none !important;
                }
                footer {
                    display: none !important;
                }
                #MainMenu {
                    display: none !important;
                }
                [data-testid="stSidebar"] {
                    display: none !important;
                }
                [data-testid="collapsedControl"] {
                    display: none !important;
                }
                [data-testid="stSidebarNav"] {
                    display: none !important;
                }
            </style>
        """, unsafe_allow_html=True)
        
        landing_component = components.declare_component("landing", path="landing_component")
        action = landing_component(default=None)
        
        if action == "login":
            st.switch_page("pages/_Login.py")
        elif action == "register":
            st.switch_page("pages/_Register.py")
            
        st.stop()

# --- Custom Sidebar Navigation (only when logged in) ---
with st.sidebar:
    st.title("🌀 Digital Wind Tunnel")
    st.page_link("app.py", label="Dashboard", icon="📊")
    st.page_link("pages/1_📊_Validation_Results.py", label="Validation Results", icon="📊")
    st.page_link("pages/2_🎁_Free_Prediction.py", label="Free Prediction", icon="🎁")
    st.page_link("pages/API_Keys.py", label="API Keys", icon="🔑")
    
    st.divider()
    if st.button("Logout"):
        # Clear session and redirect to login
        st.session_state.user = None
        st.switch_page("pages/_Login.py")
        st.rerun()


st.title("🚀 Marketing Simulation: Digital Wind Tunnel")
st.markdown("""
Predict how your audience will react to your ads before you spend a single rupee.
This simulation uses **Big Five Personality Traits** and **Prospect Theory** to model behavior.
""")

apply_theme()
render_app_header()

with st.sidebar:
    st.header("Simulation Settings")
    multi_ad_mode = st.toggle("🧪 Multi-Ad Experimentation Mode", value=False)
    
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
    
    st.subheader("DTC Offer Settings")
    price = st.slider("Product Price ($)", 5.0, 500.0, 49.99)
    offer_type = st.selectbox("Offer Type", ["None", "Discount (%)", "Free Shipping", "BOGO", "Bundle"])
    customer_segment = st.selectbox("Target Segment", ["General Broad", "Budget-Conscious", "Premium/Luxury", "Early Adopters"])
    
    st.subheader("Engine Options")
    use_ai = st.checkbox("✨ Enable AI Insights (beta)", value=False)
    if not multi_ad_mode:
        run_sim = st.button("Run Simulation")

if multi_ad_mode:
    st.header("🧪 Multi-Ad Experimentation")
    st.write("Upload a CSV or paste multiple ads to simulate them concurrently.")
    
    multi_ad_input = st.radio("Input Method", ["Paste Text", "Upload CSV"], horizontal=True)
    ads_data = []
    
    if multi_ad_input == "Paste Text":
        pasted = st.text_area("Paste ads (one per line)")
        if pasted:
            for i, line in enumerate(pasted.split('\n')):
                if line.strip():
                    ads_data.append({"name": f"Ad {i+1}", "text": line.strip()})
    else:
        st.caption("CSV should contain columns: `ad_text`, and optionally `ad_name`")
        multi_file = st.file_uploader("Upload Ads CSV", type=["csv"], key="multi_ad")
        if multi_file:
            df_multi = pd.read_csv(multi_file)
            if 'ad_text' in df_multi.columns:
                for i, row in df_multi.iterrows():
                    name = row['ad_name'] if 'ad_name' in df_multi.columns else f"Ad {i+1}"
                    ads_data.append({"name": name, "text": row['ad_text']})
            else:
                st.error("CSV must contain 'ad_text' column.")
                
    if st.button("Run Multi-Ad Simulation") and ads_data:
        from src.simulation.multi_ad_runner import MultiAdRunner
        runner = MultiAdRunner(num_agents=num_agents)
        with st.spinner("Simulating multiple ads..."):
            multi_result = runner.run_multi_test(ads_data, channel=channel, benchmarks=benchmarks)
            
        st.success(f"Simulation Complete! Winner: **{multi_result['winner']['ad_name']}**")
        
        # Leaderboard
        st.subheader("🏆 Leaderboard")
        df_lead = pd.DataFrame(multi_result['ranked_results'])
        display_df = df_lead[['ad_name', 'conversion_rate', 'engagement_rate', 'ad_text']].copy()
        display_df['conversion_rate'] = display_df['conversion_rate'].round(2).astype(str) + "%"
        display_df['engagement_rate'] = display_df['engagement_rate'].round(2).astype(str) + "%"
        st.dataframe(display_df, use_container_width=True)
        
        # Bar Chart
        fig = px.bar(df_lead, x='ad_name', y='conversion_rate', title="Conversion Rates by Ad", color='ad_name')
        st.plotly_chart(fig, use_container_width=True)
        
    st.stop()

ad_type = st.radio("Ad Type", ["Text", "Image Upload"], horizontal=True)

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

ad1_text = ""
ad2_text = ""
ad1_image = None
ad2_image = None

col1, col2 = st.columns(2)

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
            
    st.divider()
    st.header("✅ Validate Against Your Data")
    st.caption("Upload a historical performance CSV (Meta/Google/TikTok exports accepted).")
    val_file = st.file_uploader("Upload Historical Data (CSV)", type=["csv"], key="val_uploader")

tab1, tab2, tab3 = st.tabs(["🚀 New Simulation", "📂 History", "🤖 AI Predictions"])

if val_file:
    st.header("✅ Smart Validation Mapping")
    
    if 'val_df_raw' not in st.session_state or st.session_state.get('val_file_name') != val_file.name:
        st.session_state['val_df_raw'] = pd.read_csv(val_file)
        st.session_state['val_file_name'] = val_file.name
        
    df_raw = st.session_state['val_df_raw']
    
    aliases = {
        "ad_name": ["ad_name", "campaign", "ad", "name", "title", "creative name", "ad set"],
        "ad_text": ["ad_text", "copy", "creative", "headline", "body", "ad copy", "description", "message"],
        "platform": ["platform", "channel", "source", "medium", "placement"],
        "conversions": ["conversions", "purchases", "sales", "orders", "results", "goal completions", "conversion count"],
        "impressions": ["impressions", "views", "reach", "exposure", "imp", "show"]
    }
    
    if 'mapping' not in st.session_state or st.session_state.get('val_file_name_mapped') != val_file.name:
        mapping = {}
        cols = list(df_raw.columns)
        for std, variants in aliases.items():
            for col in cols:
                if any(v in col.lower() for v in variants):
                    mapping[std] = col
                    break
            if std not in mapping:
                mapping[std] = "Not Found (Use Fallback)"
        st.session_state['mapping'] = mapping
        st.session_state['val_file_name_mapped'] = val_file.name
        
    st.write("We auto-detected your columns based on common names. Please confirm or correct them below:")
    
    cols_opts = ["Not Found (Use Fallback)"] + list(df_raw.columns)
    
    c1, c2 = st.columns(2)
    with c1:
        st.session_state['mapping']["ad_name"] = st.selectbox("Ad Name", cols_opts, index=cols_opts.index(st.session_state['mapping']["ad_name"]) if st.session_state['mapping']["ad_name"] in cols_opts else 0)
        st.session_state['mapping']["ad_text"] = st.selectbox("Ad Text / Copy (Required)", cols_opts, index=cols_opts.index(st.session_state['mapping']["ad_text"]) if st.session_state['mapping']["ad_text"] in cols_opts else 0)
        st.session_state['mapping']["platform"] = st.selectbox("Platform / Channel", cols_opts, index=cols_opts.index(st.session_state['mapping']["platform"]) if st.session_state['mapping']["platform"] in cols_opts else 0)
    with c2:
        st.session_state['mapping']["conversions"] = st.selectbox("Conversions / Sales (Required)", cols_opts, index=cols_opts.index(st.session_state['mapping']["conversions"]) if st.session_state['mapping']["conversions"] in cols_opts else 0)
        st.session_state['mapping']["impressions"] = st.selectbox("Impressions / Views", cols_opts, index=cols_opts.index(st.session_state['mapping']["impressions"]) if st.session_state['mapping']["impressions"] in cols_opts else 0)

    # New Fallback Logic for Ad Text
    ad_text_fallback_method = None
    mapping_csv_path = None
    ad_text_placeholder = None
    identifier_col = None
    
    if st.session_state['mapping']["ad_text"] == "Not Found (Use Fallback)":
        with st.expander("⚠️ Ad Text Missing – How would you like to proceed?", expanded=True):
            option = st.radio("Ad Text Handling", 
                              ["Upload mapping CSV", "Use generic placeholder", "Skip simulation"])
            if option == "Upload mapping CSV":
                ad_text_fallback_method = "csv"
                st.info("Upload a secondary CSV containing your Ad IDs and their text.")
                identifier_col = st.selectbox("Identifier Column in Main CSV", list(df_raw.columns))
                mapping_file = st.file_uploader("Upload mapping CSV (must contain the identifier and 'ad_text')", type=["csv"], key="map_csv")
                if mapping_file:
                    import tempfile
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as t_map:
                        t_map.write(mapping_file.getvalue())
                        mapping_csv_path = t_map.name
            elif option == "Use generic placeholder":
                ad_text_fallback_method = "placeholder"
                ad_text_placeholder = st.text_input("Placeholder text", "Facebook Ad")
            else:
                ad_text_fallback_method = "skip"
                st.info("Simulation will be skipped. Only descriptive statistics will be shown.")

    st.write("---")
    if st.button("Confirm & Run Validation"):
        mapping = st.session_state['mapping']
        
        if mapping["conversions"] == "Not Found (Use Fallback)":
            st.error("❌ 'Conversions' is strictly required.")
        elif mapping["ad_text"] == "Not Found (Use Fallback)" and ad_text_fallback_method == "csv" and not mapping_csv_path:
            st.error("❌ Please upload the mapping CSV to proceed.")
        else:
            df_mapped = df_raw.copy()
            notes = []
            
            if mapping["ad_name"] != "Not Found (Use Fallback)":
                df_mapped.rename(columns={mapping["ad_name"]: "ad_name"}, inplace=True)
            else:
                df_mapped["ad_name"] = [f"Ad {i+1}" for i in range(len(df_mapped))]
                notes.append("Assigned generic names for 'ad_name'.")
                
            if mapping["ad_text"] != "Not Found (Use Fallback)":
                df_mapped.rename(columns={mapping["ad_text"]: "ad_text"}, inplace=True)
            
            df_mapped.rename(columns={mapping["conversions"]: "conversions"}, inplace=True)
            
            if mapping["impressions"] != "Not Found (Use Fallback)":
                df_mapped.rename(columns={mapping["impressions"]: "impressions"}, inplace=True)
            else:
                df_mapped["impressions"] = 1000
                notes.append("Assigned default 1000 for missing 'impressions'.")
                
            if mapping["platform"] != "Not Found (Use Fallback)":
                df_mapped.rename(columns={mapping["platform"]: "platform"}, inplace=True)
            else:
                df_mapped["platform"] = "facebook"
                
            # Check for test_id to support legacy paired test mode if present, else fallback
            if "test_id" not in df_mapped.columns:
                df_mapped["test_id"] = 1
            if "ad_id" not in df_mapped.columns:
                df_mapped["ad_id"] = [f"A{i}" for i in range(len(df_mapped))]

            import tempfile
            with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
                df_mapped.to_csv(tmp.name, index=False)
                tmp_path = tmp.name
                
            from scripts.validate_with_real_data import validate_data
            with st.spinner("Running deep validation (this may take a minute)..."):
                report = validate_data(
                    tmp_path, 
                    output_dir="outputs",
                    ad_text_fallback_method=ad_text_fallback_method,
                    ad_text_placeholder=ad_text_placeholder,
                    mapping_csv_path=mapping_csv_path,
                    identifier_col=identifier_col
                )
                
            if report:
                st.success("Validation Complete!")
                st.metric("Directional Accuracy", f"{report.get('directional_accuracy', 0):.2f}%")
                if notes:
                    with st.expander("⚠️ Mapping Assumptions Applied"):
                        for n in notes:
                            st.write(f"- {n}")
                
                if report.get('tests'):
                    st.subheader("Detailed Breakdown")
                    for test in report['tests']:
                        with st.expander(f"Test {test['test_id']} - Match: {'✅' if test['match'] else '❌'}"):
                            st.write(f"**Actual Winner:** {test['actual_winner']} | **Predicted Winner:** {test['predicted_winner']}")
                            if 'ad_a_text' in test:
                                st.text(f"Ad A: {test['ad_a_text']}")
                                st.text(f"Ad B: {test['ad_b_text']}")
            else:
                st.error("Validation failed. See console.")
    st.stop()



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
            result = runner.run_test(ad1_text, ad2_text, channel=channel, price=price, benchmarks=benchmarks)
        except Exception as e:
            st.error(f"Simulation failed: {e}")
            st.stop()
            
    ai_insights = None
    if use_ai:
        with st.spinner("✨ AI is generating insights..."):
            ai_insights = get_ai_insights(result, ad1_text, ad2_text, benchmarks=benchmarks)


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
    st.subheader("🧠 Marketing Intelligence Report")
    
    reasoning = result.get('reasoning', {})
    if reasoning:
        st.info(reasoning.get('overall_summary', 'No summary available.'))
        
        st.markdown("### 🔑 Key Drivers")
        for driver in reasoning.get('key_drivers', []):
            st.markdown(f"- {driver}")
            
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("#### Ad A Breakdown")
            ad_a_br = reasoning.get('ad_a_breakdown', {})
            st.markdown("**Strengths:** " + ", ".join(ad_a_br.get('strengths', [])))
            st.markdown("**Weaknesses:** " + ", ".join(ad_a_br.get('weaknesses', [])))
            st.caption(ad_a_br.get('personality_insight', ''))
        with c2:
            st.markdown("#### Ad B Breakdown")
            ad_b_br = reasoning.get('ad_b_breakdown', {})
            st.markdown("**Strengths:** " + ", ".join(ad_b_br.get('strengths', [])))
            st.markdown("**Weaknesses:** " + ", ".join(ad_b_br.get('weaknesses', [])))
            st.caption(ad_b_br.get('personality_insight', ''))
            
        st.markdown("### 📋 Actionable Recommendations")
        for rec in reasoning.get('actionable_recommendations', []):
            icon = "🔴" if rec['priority'] == 'high' else ("🟡" if rec['priority'] == 'medium' else "🔵")
            st.markdown(f"{icon} **Ad {rec['ad']} ({rec['category'].title()}):** {rec['message']}")
            
        st.markdown("### 📊 Market Context")
        st.write(reasoning.get('benchmark_comparison', ''))
        
    if use_ai and ai_insights:
        with st.expander("✨ AI-Powered Insights (beta)", expanded=True):
            st.markdown(ai_insights)
            
    st.divider()
    st.subheader("⚡ Generate Improved Ad Variants")
    st.write("Turn diagnosis into treatment. Use AI to automatically rewrite your ads fixing identified weaknesses.")
    
    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("Generate 3 variants for Ad A"):
            from src.recommendation.engine import generate_ad_variants
            ad_a_br = reasoning.get('ad_a_breakdown', {})
            with st.spinner("Generating variants..."):
                variants = generate_ad_variants(ad1_text, ad_a_br.get('strengths', []), ad_a_br.get('weaknesses', []))
            for i, v in enumerate(variants):
                st.success(f"**Variant {i+1}** (Expected {v.get('predicted_lift', 'N/A')})\n\n**{v.get('new_text', '')}**\n\n*Why: {v.get('explanation', '')}*")
                
    with col_b:
        if st.button("Generate 3 variants for Ad B"):
            from src.recommendation.engine import generate_ad_variants
            ad_b_br = reasoning.get('ad_b_breakdown', {})
            with st.spinner("Generating variants..."):
                variants = generate_ad_variants(ad2_text, ad_b_br.get('strengths', []), ad_b_br.get('weaknesses', []))
            for i, v in enumerate(variants):
                st.success(f"**Variant {i+1}** (Expected {v.get('predicted_lift', 'N/A')})\n\n**{v.get('new_text', '')}**\n\n*Why: {v.get('explanation', '')}*")

    st.divider()
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

<<<<<<< HEAD
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
=======
>>>>>>> origin/main
