"""Streamlit dashboard for GEO audit visualization."""

import streamlit as st
from run_lift_simulation import run_lift_simulation

APP_VERSION = "cebc37b"

st.set_page_config(page_title="GEO Audit Dashboard", page_icon="🌍", layout="wide")

st.title("🌍 GEO Audit Intelligence Dashboard")
st.markdown("Local business visibility audit and optimization system")

# Sidebar inputs
with st.sidebar:
    st.header("Business Information")
    brand_name = st.text_input("Brand Name", "Capital Arena Fitness Club")
    category = st.text_input("Category", "fitness gym")
    city = st.text_input("City", "Islamabad")

    st.divider()
    st.subheader("Business Data")

    review_count = st.number_input("Review Count", min_value=0, value=231)
    rating = st.number_input("Rating", min_value=0.0, max_value=5.0, value=4.5, step=0.1)

    services_input = st.text_area(
        "Services (one per line)",
        "online classes\nsauna\nswimming pool\ngym\nspa\nsteam\nprotein bar\nphysiotherapy"
    )
    services = [s.strip() for s in services_input.split('\n') if s.strip()]

    instagram_followers = st.number_input("Instagram Followers", min_value=0, value=18300)
    facebook_followers = st.number_input("Facebook Followers", min_value=0, value=12200)

    location_description = st.text_input("Location", "F-9 Park / Megazone, Islamabad")
    is_central_location = st.checkbox("Central Location", value=True)

    raw_response = st.text_area(
        "Raw Response (for sentiment/competitor analysis)",
        "Capital Arena Fitness Club stands out for its commitment to customer satisfaction.\n1. Capital Arena Fitness Club\n2. Local Favorite\n3. Established Brand"
    )

    st.divider()
    st.subheader("Current State")
    has_schema = st.checkbox("Has Schema", value=False)
    has_trainer_info = st.checkbox("Has Trainer Info", value=False)
    has_pricing = st.checkbox("Has Pricing", value=False)
    has_schedule = st.checkbox("Has Schedule", value=False)
    has_local_content = st.checkbox("Has Local Content", value=False)

    st.divider()
    business_context = st.text_area(
        "Business Context / Evidence",
        placeholder="Enter additional brand context, website info, or evidence here..."
    )

    run_audit = st.button("🚀 Run Audit", type="primary")

    st.sidebar.caption(f"App version: {APP_VERSION}")

# Main content
if run_audit:
    business_data = {
        'review_count': review_count,
        'rating': rating,
        'services': services,
        'instagram_followers': instagram_followers,
        'facebook_followers': facebook_followers,
        'location_description': location_description,
        'is_central_location': is_central_location,
        'raw_response': raw_response,
        'has_schema': has_schema,
        'has_trainer_info': has_trainer_info,
        'has_pricing': has_pricing,
        'has_schedule': has_schedule,
        'has_local_content': has_local_content,
        'business_context': business_context,
    }

    with st.spinner("Running GEO audit..."):
        results = run_lift_simulation(brand_name, category, city, business_data)

    # Header
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Brand", results['brand_name'])
    with col2:
        st.metric("Category", results['category'])
    with col3:
        st.metric("City", results['city'])

    # Template debug display
    template_used = results.get('template_used', 'Generic')
    st.caption(f"Template used: {template_used}")
    if template_used and template_used != 'Generic':
        st.info(f"Using {template_used} for industry-specific recommendations")
    else:
        st.warning(f"Using Generic template - no industry match for category: {results.get('category', 'unknown')}")

    st.divider()

    # Lift Metrics
    st.header("📈 Lift Simulation Results")
    lift = results['lift_metrics']

    # Display lift status with appropriate styling
    if lift['status'] == 'negative':
        st.error(f"⚠️ {lift['message']}")
    elif lift['status'] == 'baseline_strong':
        st.warning(f"ℹ️ {lift['message']}")
    elif lift['status'] == 'marginal':
        st.info(f"📊 {lift['message']}")
    else:
        st.success(f"✅ {lift['message']}")

    st.markdown(f"**Explanation:** {lift['explanation']}")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Before Score", f"{lift['before_score']:.2f}")
    with col2:
        st.metric("After Score", f"{lift['after_score']:.2f}")
    with col3:
        # Show negative sign for negative lift
        abs_lift_display = f"{lift['absolute_lift']:.2f}"
        st.metric("Absolute Lift", abs_lift_display)
    with col4:
        # Show negative sign for negative percentage
        pct_lift_display = f"{lift['percentage_lift']:.1f}%"
        st.metric("Percentage Lift", pct_lift_display)

    st.divider()

    # Sentiment & Competitors
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("💬 Sentiment Analysis")
        sentiment = results['sentiment']
        if sentiment == 'positive':
            st.success(f"Sentiment: **{sentiment.upper()}**")
        elif sentiment == 'neutral':
            st.info(f"Sentiment: **{sentiment.upper()}**")
        else:
            st.warning(f"Sentiment: **{sentiment.upper()}** (brand not mentioned)")

    with col2:
        st.subheader("🏢 Competitors")
        if results['competitors']:
            for comp in results['competitors']:
                st.write(f"• {comp}")
        else:
            st.info("No competitors identified.")

    st.divider()

    # Strengths
    st.header("💪 Strengths")
    if results['strengths']:
        for strength in results['strengths']:
            with st.expander(f"✅ {strength['title']}", expanded=True):
                st.write(f"**Type:** {strength['type']}")
                st.write(f"**Description:** {strength['description']}")
    else:
        st.info("No strengths identified.")

    st.divider()

    # Gaps
    st.header("🔍 Identified Gaps")
    if results['gaps']:
        for gap in results['gaps']:
            severity_emoji = "🔴" if gap['severity'] == 'high' else "🟡" if gap['severity'] == 'medium' else "🟢"
            with st.expander(f"{severity_emoji} [{gap['severity'].upper()}] {gap['title']}", expanded=True):
                st.write(f"**Type:** {gap['type']}")
                st.write(f"**Description:** {gap['description']}")
    else:
        st.success("No gaps identified!")

    st.divider()

    # Remediation
    st.header("🛠️ Remediation Recommendations")
    if results['remediation']:
        for rem in results['remediation']:
            priority_emoji = "🔴" if rem['priority'] == 'high' else "🟡" if rem['priority'] == 'medium' else "🟢"
            quick_win_badge = " ⚡ QUICK WIN" if rem.get('quick_win') else ""

            with st.expander(f"{priority_emoji} [{rem['priority'].upper()}] {rem['title']}{quick_win_badge}", expanded=True):
                st.write(f"**Reason:** {rem['reason']}")
                st.write(f"**Why this works:** {rem['why_this_works']}")
                st.write(f"**Action:** {rem['action']}")

                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Effort", rem['effort'].upper())
                with col2:
                    st.metric("Impact", rem['impact'].upper())
    else:
        st.warning("No remediation results to display.")

    # Raw data
    with st.expander("🔬 View Raw Data"):
        st.json(results)

else:
    st.info("👈 Enter business information in the sidebar and click 'Run Audit' to begin.")
