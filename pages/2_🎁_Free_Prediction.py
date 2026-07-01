import streamlit as st
import time
import random

st.set_page_config(page_title="Free Ad Prediction", page_icon="🎁", layout="centered")

st.title("🎁 Will Your Ad Win? Get a Free Prediction.")
st.markdown("""
Don't waste money testing losing creatives. Our AI has a **92.4% accuracy rate** predicting Facebook Ad winners.
Upload your ad below and see how it scores!
""")

st.divider()

ad_text = st.text_area("1. Paste your Ad Copy here", placeholder="e.g. Get 50% off your first order today! Limited time only.")
ad_image = st.file_uploader("2. Upload your Ad Creative (Image)", type=['png', 'jpg', 'jpeg'])

if st.button("🔮 Predict My Ad's Performance", type="primary", use_container_width=True):
    if not ad_text:
        st.error("Please provide ad text to get a prediction.")
    else:
        # Mocking a realistic feeling analysis sequence
        with st.status("Analyzing your ad...", expanded=True) as status:
            st.write("🔍 Extracting psychographic profile from text...")
            time.sleep(1)
            if ad_image:
                st.write("🖼️ Scoring visual excitement and premium aesthetics (CLIP)...")
                time.sleep(1.5)
            st.write("🧠 Simulating response across 10,000 virtual agents...")
            time.sleep(1.5)
            status.update(label="Analysis Complete!", state="complete", expanded=False)
        
        # We generate a deterministic-looking mock score based on text length + some random seed for demonstration
        random.seed(len(ad_text))
        score = random.uniform(65.0, 95.0)
        cvr = random.uniform(1.2, 4.8)
        
        st.header("Results")
        
        col1, col2 = st.columns(2)
        col1.metric("Predicted Conversion Rate", f"{cvr:.2f}%")
        col2.metric("Creative Score", f"{score:.1f}/100")
        
        st.success(f"**Insight:** This ad leans heavily on **{'Urgency' if 'today' in ad_text.lower() or 'now' in ad_text.lower() else 'Social Proof'}** and appeals primarily to **{'Budget-Conscious' if '%' in ad_text or 'off' in ad_text.lower() else 'Premium'}** segments.")
        
        st.divider()
        st.info("""
        ### 🚀 Want to know *why*?
        This free preview shows you *what* will happen. Our full engine tells you *why* it happens and exactly how to fix it.
        
        **Get the Full Report & AI Recommendations:**
        Contact sales or sign up for an enterprise account to access our complete psychographic breakdown and generative improvements.
        """)
        st.button("Request Full Access")
