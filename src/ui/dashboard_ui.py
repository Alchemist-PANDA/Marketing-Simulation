"""
Full Marketing Intelligence Dashboard renderer.

All metrics are derived from the existing ABTestRunner result dict and the
raw Ad score fields — no changes to the simulation engine are required.

Design philosophy:
  - Every section is wrapped in try/except so a bad value can never crash the app.
  - Optional fields use .get() with sensible defaults throughout.
  - If a computation genuinely cannot run, a styled info box is shown instead.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, Any, Optional


# ── Colour palette (mirrors theme.py) ─────────────────────────────────────
_PRIMARY   = "#4F46E5"
_SUCCESS   = "#10B981"
_WARNING   = "#F59E0B"
_DANGER    = "#EF4444"
_TRAITS    = ["Openness", "Conscientiousness", "Extraversion", "Agreeableness", "Neuroticism"]
_ARCHETYPES = ["Price-Sensitive", "Impulsive", "Social Proof", "Skeptical"]
_ARCH_DIST  = [0.30, 0.25, 0.25, 0.20]   # mirrors DEFAULT_DISTRIBUTION


# ═══════════════════════════════════════════════════════════════════════════
#  DERIVED-METRIC HELPERS
# ═══════════════════════════════════════════════════════════════════════════

def _safe(fn, default=0.0):
    """Run fn(); return default on any exception."""
    try:
        return fn()
    except Exception:
        return default


def _derive_personality_resonance(ad_data: Dict) -> Dict[str, float]:
    """
    Compute estimated OCEAN-trait resonance from the ad's price / trust /
    urgency scores.  These scores already encode how the ad's messaging
    interacts with personality-driven sensitivities in the engine.
    """
    analysis = ad_data.get("analysis", {})
    scores   = analysis.get("scores", {})

    price_s   = scores.get("price",   0.5)
    trust_s   = scores.get("trust",   0.5)
    urgency_s = scores.get("urgency", 0.5)

    # Each OCEAN trait correlates differently with ad dimensions:
    #   Openness        → responds to novelty / emotional appeal
    #   Conscientiousness → responds to value / quality signals (price)
    #   Extraversion    → responds to urgency / social cues
    #   Agreeableness   → responds to trust / social proof
    #   Neuroticism     → inverse to urgency (high urgency hurts high-N agents)
    openness        = round(min(1.0, 0.4 + 0.3 * trust_s  + 0.2 * urgency_s), 3)
    conscientiousness = round(min(1.0, 0.3 + 0.5 * price_s  + 0.2 * trust_s),  3)
    extraversion    = round(min(1.0, 0.3 + 0.5 * urgency_s + 0.2 * trust_s),  3)
    agreeableness   = round(min(1.0, 0.3 + 0.6 * trust_s  + 0.1 * price_s),   3)
    neuroticism     = round(min(1.0, max(0.0, 0.6 - 0.4 * urgency_s)),          3)

    return {
        "Openness":          openness,
        "Conscientiousness": conscientiousness,
        "Extraversion":      extraversion,
        "Agreeableness":     agreeableness,
        "Neuroticism":       neuroticism,
    }


def _derive_prospect_insights(ad_data: Dict, price: float) -> Dict[str, Any]:
    """
    Compute Prospect Theory metrics from cohort stats.
    Uses Kahneman-Tversky loss aversion (λ=2.25) and the ad's price score.
    """
    analysis = ad_data.get("analysis", {})
    scores   = analysis.get("scores", {})
    csize    = ad_data.get("cohort_size", 1)

    price_s   = scores.get("price",   0.5)
    trust_s   = scores.get("trust",   0.5)
    urgency_s = scores.get("urgency", 0.5)

    # Perceived value = utility-weighted combo of scores
    perceived_value = round((price_s * 0.4 + trust_s * 0.35 + urgency_s * 0.25), 3)

    # Loss aversion impact: how much the *price* feels like a loss
    # Higher price → lower price_score → more aversion
    loss_aversion = round(2.25 * (1.0 - price_s), 3)

    # Price elasticity proxy: simulated conversions / cohort as % of agents
    conversions  = ad_data.get("conversions", 0)
    cvr          = conversions / max(1, csize)
    price_elasticity = round(cvr * 100, 2)

    # Income-segment sensitivity: higher income → less price sensitive
    ps_high   = round(max(0.0, 1.0 - loss_aversion * 0.5),  3)
    ps_medium = round(max(0.0, 1.0 - loss_aversion * 0.75), 3)
    ps_low    = round(max(0.0, 1.0 - loss_aversion * 1.0),  3)

    return {
        "perceived_value":     perceived_value,
        "loss_aversion_impact": loss_aversion,
        "price_elasticity":    price_elasticity,
        "price_sensitivity":   {"high": ps_high, "medium": ps_medium, "low": ps_low},
    }


def _derive_segment_analysis(ad_data: Dict, price: float) -> Dict[str, Dict]:
    """
    Approximate income-segment breakdown using the archetype distribution.
    Price-sensitive (30%) → low income proxy
    Social-proof (25%)    → medium income proxy
    Impulsive (25%)       → medium-high income proxy
    Skeptical (20%)       → high income proxy
    """
    csize       = ad_data.get("cohort_size", 1)
    conversions = ad_data.get("conversions", 0)
    analysis    = ad_data.get("analysis", {})
    scores      = analysis.get("scores", {})
    price_s     = scores.get("price", 0.5)

    # Weights derived from archetype sensitivity to price signal
    low_w    = 0.30 * price_s        # price-sensitive → buys when price is good
    med_w    = 0.50 * (0.5 + price_s * 0.3)
    high_w   = 0.20 * (1.0 - price_s * 0.3)

    total_w  = low_w + med_w + high_w or 1.0
    low_conv  = int(conversions * low_w  / total_w)
    med_conv  = int(conversions * med_w  / total_w)
    high_conv = conversions - low_conv - med_conv

    low_n  = int(csize * 0.30)
    med_n  = int(csize * 0.50)
    high_n = csize - low_n - med_n

    return {
        "low_income": {
            "count":           low_n,
            "conversions":     low_conv,
            "conversion_rate": round(low_conv  / max(1, low_n)  * 100, 2),
        },
        "medium_income": {
            "count":           med_n,
            "conversions":     med_conv,
            "conversion_rate": round(med_conv  / max(1, med_n)  * 100, 2),
        },
        "high_income": {
            "count":           high_n,
            "conversions":     high_conv,
            "conversion_rate": round(high_conv / max(1, high_n) * 100, 2),
        },
    }


def _build_recommendations(ad_data: Dict, label: str) -> list:
    """Generate prioritised recommendations from failure_reasons and scores."""
    analysis = ad_data.get("analysis", {})
    reasons  = analysis.get("failure_reasons", [])
    scores   = analysis.get("scores", {})
    recs     = []

    mapping = {
        "Price too high for perceived value": {
            "category": "pricing",
            "priority": "high",
            "message":  "Add a clear discount or compare to a higher reference price to anchor perceived savings.",
        },
        "Weak pricing incentive": {
            "category": "pricing",
            "priority": "medium",
            "message":  "Introduce a time-limited offer (e.g., '20% off this week only') to strengthen price appeal.",
        },
        "Low trust signals - lacks social proof": {
            "category": "trust",
            "priority": "high",
            "message":  "Add social proof: customer reviews, star ratings, or '10,000+ happy customers'.",
        },
        "Insufficient brand authority": {
            "category": "trust",
            "priority": "medium",
            "message":  "Include a credibility marker such as a press mention, award, or industry certification.",
        },
        "Weak urgency - no incentive to act now": {
            "category": "urgency",
            "priority": "high",
            "message":  "Add a hard deadline: 'Offer ends Sunday midnight' or 'Only 12 left in stock'.",
        },
        "Low FOMO factor": {
            "category": "urgency",
            "priority": "medium",
            "message":  "Use scarcity language: 'Limited edition' or 'Selling fast – order now'.",
        },
        "Creative lacks stopping power (Low CTR)": {
            "category": "creative",
            "priority": "high",
            "message":  "Open with a bold, benefit-driven headline. The first 5 words must hook the reader.",
        },
        "Poor offer-to-audience fit (Low CVR)": {
            "category": "audience",
            "priority": "high",
            "message":  "Re-segment targeting: test this creative against a narrower, higher-intent audience.",
        },
        "Market saturation / High skepticism": {
            "category": "positioning",
            "priority": "medium",
            "message":  "Differentiate with a unique angle: specific result ('Lose 5kg in 30 days') beats generic claims.",
        },
        "Generic creative messaging": {
            "category": "creative",
            "priority": "medium",
            "message":  "Personalise copy to a specific pain-point or demographic for stronger resonance.",
        },
    }

    for reason in reasons:
        rec = mapping.get(reason)
        if rec:
            recs.append({"ad": label, **rec})

    # Add a generic win-consolidation rec if no specific weaknesses
    if not recs:
        recs.append({
            "ad":       label,
            "category": "optimisation",
            "priority": "low",
            "message":  "Performance looks solid — consider scaling budget and running multi-variant tests.",
        })

    return recs


def _build_reasoning(result: Dict, ad1_text: str, ad2_text: str) -> Dict:
    """Assemble the full Marketing Intelligence Report dict from result data."""
    ad_a = result.get("ad_a", {})
    ad_b = result.get("ad_b", {})
    winner = result.get("winner", "A")

    a_analysis = ad_a.get("analysis", {})
    b_analysis = ad_b.get("analysis", {})
    a_scores   = a_analysis.get("scores", {})
    b_scores   = b_analysis.get("scores", {})

    # Overall summary
    lift = result.get("lift_percentage", 0.0)
    summary = (
        f"Ad {winner} won the simulation with a **{lift:.1f}% lift** over the alternative. "
    )
    if lift < 5:
        summary += "The margin is slim — both creatives are competitive."
    elif lift < 20:
        summary += "A meaningful performance gap; confidence is moderate."
    else:
        summary += "A strong performance gap; Ad " + winner + " is the clear winner."

    # Key drivers
    drivers = []
    if abs(a_scores.get("trust", 0.5) - b_scores.get("trust", 0.5)) > 0.1:
        better = "A" if a_scores.get("trust", 0.5) > b_scores.get("trust", 0.5) else "B"
        drivers.append(f"Trust & Social Proof (Ad {better} leads)")
    if abs(a_scores.get("urgency", 0.5) - b_scores.get("urgency", 0.5)) > 0.1:
        better = "A" if a_scores.get("urgency", 0.5) > b_scores.get("urgency", 0.5) else "B"
        drivers.append(f"Urgency / FOMO (Ad {better} leads)")
    if abs(a_scores.get("price", 0.5) - b_scores.get("price", 0.5)) > 0.1:
        better = "A" if a_scores.get("price", 0.5) > b_scores.get("price", 0.5) else "B"
        drivers.append(f"Price Perception (Ad {better} leads)")
    if not drivers:
        drivers = ["Overall Conversion Volume", "Engagement Rate"]

    # Per-ad breakdowns (re-use failure analysis scores)
    def _ad_breakdown(ad_data, analysis, scores):
        strengths, weaknesses = [], []
        csize    = ad_data.get("cohort_size", 1)
        cvr      = ad_data.get("conversions", 0) / max(1, csize) * 100
        eng      = (ad_data.get("likes", 0) + ad_data.get("shares", 0)) / max(1, csize) * 100

        if cvr > 2.5:  strengths.append(f"Strong conversion rate ({cvr:.1f}%)")
        elif cvr < 0.5: weaknesses.append(f"Low conversion rate ({cvr:.1f}%)")
        if eng > 15:  strengths.append(f"High engagement ({eng:.1f}%)")
        elif eng < 5:  weaknesses.append(f"Low engagement ({eng:.1f}%)")
        if scores.get("trust", 0.5)   > 0.65: strengths.append("High trust signals")
        if scores.get("urgency", 0.5) > 0.65: strengths.append("Strong urgency cues")
        if scores.get("price", 0.5)   > 0.65: strengths.append("Attractive price positioning")
        weaknesses.extend(analysis.get("failure_reasons", []))

        perf_data = _derive_personality_resonance(ad_data)
        best_trait = max(perf_data, key=perf_data.get)
        personality_insight = f"Resonates strongest with high-{best_trait} audiences."

        return {
            "strengths":           list(dict.fromkeys(strengths))[:3],
            "weaknesses":          list(dict.fromkeys(weaknesses))[:3],
            "personality_insight": personality_insight,
        }

    ad_a_bd = _ad_breakdown(ad_a, a_analysis, a_scores)
    ad_b_bd = _ad_breakdown(ad_b, b_analysis, b_scores)

    recs = _build_recommendations(ad_a, "A") + _build_recommendations(ad_b, "B")

    return {
        "overall_summary":          summary,
        "key_drivers":              drivers[:3],
        "ad_a_breakdown":           ad_a_bd,
        "ad_b_breakdown":           ad_b_bd,
        "actionable_recommendations": recs,
    }


# ═══════════════════════════════════════════════════════════════════════════
#  RENDERING SECTIONS
# ═══════════════════════════════════════════════════════════════════════════

def _render_confidence_banner(result: Dict):
    """Show a confidence/stats summary banner."""
    try:
        ad_a = result.get("ad_a", {})
        ad_b = result.get("ad_b", {})
        conf_a = ad_a.get("analysis", {}).get("confidence_score", 0.0)
        conf_b = ad_b.get("analysis", {}).get("confidence_score", 0.0)
        conf = round((conf_a + conf_b) / 2 * 100, 1)
        total_agents = ad_a.get("cohort_size", 0) + ad_b.get("cohort_size", 0)

        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("🎯 Simulation Confidence", f"{conf:.1f}%",
                      help="Based on cohort size relative to statistical minimum (500 agents = 100%)")
        with c2:
            st.metric("👥 Total Agents Simulated", f"{total_agents:,}")
        with c3:
            ctr_a = ad_a.get("analysis", {}).get("predicted_ctr", 0.0)
            ctr_b = ad_b.get("analysis", {}).get("predicted_ctr", 0.0)
            st.metric("📊 Predicted CTR", f"A: {ctr_a:.2%}  |  B: {ctr_b:.2%}")
    except Exception:
        pass


def _render_personality_heatmap(result: Dict):
    """OCEAN trait resonance bar chart."""
    try:
        ad_a = result.get("ad_a", {})
        ad_b = result.get("ad_b", {})

        perf_a = _derive_personality_resonance(ad_a)
        perf_b = _derive_personality_resonance(ad_b)

        df = pd.DataFrame({
            "Trait":  _TRAITS,
            "Ad A":   [perf_a.get(t, 0.0) for t in _TRAITS],
            "Ad B":   [perf_b.get(t, 0.0) for t in _TRAITS],
        })

        fig = px.bar(
            df, x="Trait", y=["Ad A", "Ad B"],
            barmode="group",
            color_discrete_map={"Ad A": _PRIMARY, "Ad B": _SUCCESS},
            title="Personality Trait Resonance (OCEAN model)",
            labels={"value": "Resonance Score (0–1)", "variable": "Ad"},
        )
        fig.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font_color="#D1D5DB",
            title_font_color="#F9FAFB",
            legend=dict(bgcolor="rgba(0,0,0,0)"),
        )
        st.plotly_chart(fig, use_container_width=True)
        st.caption("Higher score = stronger resonance with that personality trait group")
    except Exception as exc:
        st.info(f"ℹ️ Personality heatmap unavailable: {exc}")


def _render_archetype_donut(result: Dict):
    """Pie chart showing archetype composition of winning ad's cohort."""
    try:
        winner = result.get("winner", "A")
        ad_data = result.get(f"ad_{winner.lower()}", {})
        csize   = ad_data.get("cohort_size", 1)

        counts = [int(csize * w) for w in _ARCH_DIST]
        counts[-1] = csize - sum(counts[:-1])   # fix rounding

        fig = go.Figure(go.Pie(
            labels=_ARCHETYPES,
            values=counts,
            hole=0.5,
            marker_colors=[_PRIMARY, _SUCCESS, _WARNING, _DANGER],
        ))
        fig.update_layout(
            title=f"Ad {winner} – Audience Archetype Mix",
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font_color="#D1D5DB",
            title_font_color="#F9FAFB",
        )
        st.plotly_chart(fig, use_container_width=True)
    except Exception:
        pass


def _render_segment_analysis(result: Dict, price: float):
    """Income-segment conversion breakdown table + grouped bar."""
    try:
        ad_a = result.get("ad_a", {})
        ad_b = result.get("ad_b", {})

        seg_a = _derive_segment_analysis(ad_a, price)
        seg_b = _derive_segment_analysis(ad_b, price)

        rows = []
        for seg_key in ["high_income", "medium_income", "low_income"]:
            label = seg_key.replace("_", " ").title()
            rows.append({
                "Segment":        label,
                "Ad A Conv %":    seg_a[seg_key]["conversion_rate"],
                "Ad B Conv %":    seg_b[seg_key]["conversion_rate"],
                "Ad A Converts":  seg_a[seg_key]["conversions"],
                "Ad B Converts":  seg_b[seg_key]["conversions"],
                "Segment Size":   f"{seg_a[seg_key]['count']:,}",
            })

        seg_df = pd.DataFrame(rows)
        st.dataframe(
            seg_df.style.format({
                "Ad A Conv %": "{:.2f}%",
                "Ad B Conv %": "{:.2f}%",
            }),
            use_container_width=True,
            hide_index=True,
        )

        # Bar chart
        fig = px.bar(
            seg_df, x="Segment", y=["Ad A Conv %", "Ad B Conv %"],
            barmode="group",
            color_discrete_map={"Ad A Conv %": _PRIMARY, "Ad B Conv %": _SUCCESS},
            title="Conversion Rate by Income Segment",
            labels={"value": "Conversion %", "variable": "Ad"},
        )
        fig.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font_color="#D1D5DB",
            title_font_color="#F9FAFB",
        )
        st.plotly_chart(fig, use_container_width=True)

    except Exception as exc:
        st.info(f"ℹ️ Segment analysis unavailable: {exc}")


def _render_prospect_theory(result: Dict, price: float):
    """Prospect Theory metrics inside an expander."""
    try:
        ad_a = result.get("ad_a", {})
        ad_b = result.get("ad_b", {})

        pros_a = _derive_prospect_insights(ad_a, price)
        pros_b = _derive_prospect_insights(ad_b, price)

        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("Ad A – Perceived Value",     f"{pros_a['perceived_value']:.2f}")
            st.metric("Ad B – Perceived Value",     f"{pros_b['perceived_value']:.2f}")
        with c2:
            st.metric("Ad A – Loss Aversion Impact", f"{pros_a['loss_aversion_impact']:.2f}")
            st.metric("Ad B – Loss Aversion Impact", f"{pros_b['loss_aversion_impact']:.2f}")
        with c3:
            st.metric("Ad A – Price Elasticity",    f"{pros_a['price_elasticity']:.2f}%")
            st.metric("Ad B – Price Elasticity",    f"{pros_b['price_elasticity']:.2f}%")

        st.markdown("**Price Sensitivity by Income Segment**")
        ps_a = pros_a["price_sensitivity"]
        ps_b = pros_b["price_sensitivity"]
        price_df = pd.DataFrame({
            "Segment":    ["High Income", "Medium Income", "Low Income"],
            "Ad A Sensitivity": [ps_a["high"], ps_a["medium"], ps_a["low"]],
            "Ad B Sensitivity": [ps_b["high"], ps_b["medium"], ps_b["low"]],
        })
        st.dataframe(price_df, use_container_width=True, hide_index=True)

        st.caption(
            "Loss Aversion λ = 2.25 (Kahneman & Tversky). "
            "Perceived Value is a weighted composite of price, trust, and urgency scores."
        )
    except Exception as exc:
        st.info(f"ℹ️ Prospect Theory analysis unavailable: {exc}")


def _render_funnel(result: Dict):
    """Conversion funnel: impressions → engagement → conversion."""
    try:
        ad_a = result.get("ad_a", {})
        ad_b = result.get("ad_b", {})

        csize_a = ad_a.get("cohort_size", 0)
        csize_b = ad_b.get("cohort_size", 0)
        engaged_a = ad_a.get("likes", 0) + ad_a.get("shares", 0)
        engaged_b = ad_b.get("likes", 0) + ad_b.get("shares", 0)
        conv_a    = ad_a.get("conversions", 0)
        conv_b    = ad_b.get("conversions", 0)

        # Side-by-side funnel comparison
        col1, col2 = st.columns(2)
        for col, label, sizes in [
            (col1, "Ad A", [csize_a, engaged_a, conv_a]),
            (col2, "Ad B", [csize_b, engaged_b, conv_b]),
        ]:
            with col:
                fig = go.Figure(go.Funnel(
                    y=["Impressions (Cohort)", "Engagement (Likes+Shares)", "Conversions"],
                    x=sizes,
                    textinfo="value+percent initial",
                    marker_color=[_PRIMARY, _WARNING, _SUCCESS],
                ))
                fig.update_layout(
                    title=f"Conversion Funnel – {label}",
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    font_color="#D1D5DB",
                    title_font_color="#F9FAFB",
                )
                st.plotly_chart(fig, use_container_width=True)
    except Exception as exc:
        st.info(f"ℹ️ Funnel chart unavailable: {exc}")


def _render_intelligence_report(reasoning: Dict):
    """Marketing Intelligence Report section."""
    try:
        st.info(reasoning.get("overall_summary", "No summary available."))

        st.markdown("### 🔑 Key Drivers")
        for driver in reasoning.get("key_drivers", []):
            st.markdown(f"- {driver}")

        c1, c2 = st.columns(2)
        for col, key, label in [(c1, "ad_a_breakdown", "Ad A"), (c2, "ad_b_breakdown", "Ad B")]:
            with col:
                br = reasoning.get(key, {})
                st.markdown(f"#### {label}")
                strengths  = br.get("strengths",  [])
                weaknesses = br.get("weaknesses", [])
                if strengths:
                    st.success("✅ " + " · ".join(strengths))
                if weaknesses:
                    st.warning("⚠️ " + " · ".join(weaknesses))
                pi = br.get("personality_insight", "")
                if pi:
                    st.caption(f"🧠 {pi}")

        st.markdown("### 📋 Actionable Recommendations")
        recs = reasoning.get("actionable_recommendations", [])
        if recs:
            for rec in recs:
                priority = rec.get("priority", "low")
                icon = {"high": "🔴", "medium": "🟡", "low": "🔵"}.get(priority, "⚪")
                cat  = rec.get("category", "general").title()
                msg  = rec.get("message",  "")
                ad   = rec.get("ad", "?")
                st.markdown(f"{icon} **Ad {ad} ({cat}):** {msg}")
        else:
            st.markdown("_No specific recommendations at this time._")

    except Exception as exc:
        st.info(f"ℹ️ Intelligence report unavailable: {exc}")


def _render_score_radar(result: Dict, ad1_text: str, ad2_text: str):
    """Radar chart of the three core ad scores (price, trust, urgency)."""
    try:
        ad_a = result.get("ad_a", {})
        ad_b = result.get("ad_b", {})
        sa   = ad_a.get("analysis", {}).get("scores", {})
        sb   = ad_b.get("analysis", {}).get("scores", {})

        categories = ["Price Score", "Trust Score", "Urgency Score"]
        vals_a = [sa.get("price", 0.5), sa.get("trust", 0.5), sa.get("urgency", 0.5)]
        vals_b = [sb.get("price", 0.5), sb.get("trust", 0.5), sb.get("urgency", 0.5)]

        fig = go.Figure()
        for label, vals, colour in [
            ("Ad A", vals_a, _PRIMARY),
            ("Ad B", vals_b, _SUCCESS),
        ]:
            fig.add_trace(go.Scatterpolar(
                r=vals + vals[:1],
                theta=categories + categories[:1],
                fill="toself",
                name=label,
                line_color=colour,
                fillcolor=colour + "22",
            ))
        fig.update_layout(
            polar=dict(
                bgcolor="rgba(0,0,0,0)",
                radialaxis=dict(visible=True, range=[0, 1], color="#D1D5DB"),
                angularaxis=dict(color="#D1D5DB"),
            ),
            showlegend=True,
            title="Ad Score Radar",
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font_color="#D1D5DB",
            title_font_color="#F9FAFB",
            legend=dict(bgcolor="rgba(0,0,0,0)"),
        )
        st.plotly_chart(fig, use_container_width=True)
    except Exception:
        pass


# ═══════════════════════════════════════════════════════════════════════════
#  PUBLIC ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════

def render_full_dashboard(
    result: Dict[str, Any],
    ad1_text: str,
    ad2_text: str,
    price: float = 49.99,
):
    """
    Render the complete Marketing Intelligence Dashboard below the basic
    results section.  Every sub-section is independently guarded so a single
    failure cannot crash the whole page.

    Args:
        result:   The dict returned by ABTestRunner.run_test()
        ad1_text: Raw text of Ad A (used for labelling only)
        ad2_text: Raw text of Ad B (used for labelling only)
        price:    Product price used in the simulation run
    """
    winner = result.get("winner", "?")
    lift   = result.get("lift_percentage", 0.0)

    # Prominent winner banner
    banner_color = _SUCCESS if winner == "A" else _PRIMARY
    st.markdown(
        f"""
        <div style="
            background: linear-gradient(135deg, {banner_color}22 0%, {banner_color}11 100%);
            border-left: 4px solid {banner_color};
            border-radius: 8px;
            padding: 16px 20px;
            margin: 8px 0 16px 0;
        ">
            <span style="font-size:1.6rem; font-weight:700; color:{banner_color};">
                🧠 Marketing Intelligence Dashboard
            </span><br/>
            <span style="color:#D1D5DB; font-size:0.95rem;">
                Ad <strong>{winner}</strong> is the predicted winner &nbsp;•&nbsp;
                <strong>{lift:.1f}%</strong> lift over the alternative
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Confidence banner ─────────────────────────────────────────────────
    _render_confidence_banner(result)

    st.divider()

    # ── Row 1: Score Radar + Archetype Donut ─────────────────────────────
    col_radar, col_donut = st.columns(2)
    with col_radar:
        st.markdown("##### Ad Score Radar")
        _render_score_radar(result, ad1_text, ad2_text)
    with col_donut:
        st.markdown("##### Audience Archetype Mix")
        _render_archetype_donut(result)

    st.divider()

    # ── Row 2: OCEAN Personality Heatmap ─────────────────────────────────
    st.markdown("### 🧠 Personality-Driven Emotional Resonance")
    _render_personality_heatmap(result)

    st.divider()

    # ── Row 3: Audience Segmentation ─────────────────────────────────────
    st.markdown("### 🎯 Audience Segmentation Breakdown")
    _render_segment_analysis(result, price)

    st.divider()

    # ── Row 4: Prospect Theory ────────────────────────────────────────────
    with st.expander("📉 Prospect Theory Analysis (Advanced Economics)", expanded=False):
        _render_prospect_theory(result, price)

    # ── Row 5: Conversion Funnel ──────────────────────────────────────────
    st.markdown("### 🔽 Conversion Funnel")
    _render_funnel(result)

    st.divider()

    # ── Row 6: Intelligence Report ────────────────────────────────────────
    st.markdown("### 🧠 Marketing Intelligence Report")
    reasoning = _safe(lambda: _build_reasoning(result, ad1_text, ad2_text), default={})
    if reasoning:
        _render_intelligence_report(reasoning)
    else:
        st.info("ℹ️ Intelligence report could not be generated.")
