"""
Deep-space design system for the Marketing Simulation Dashboard.

3D galactic background + glass-morphism surfaces, applied on every page via
apply_theme() (dashboard pages) or inject_auth_css() -> inject_galaxy_background()
(auth pages).

IMPORTANT: the background is pure CSS injected into the MAIN document with
st.markdown. Earlier versions drew a canvas into window.parent.document from a
components.html iframe — Streamlit Cloud sandboxes those iframes cross-origin,
so the canvas never rendered and every page showed a flat background. CSS in
the main document is not sandboxed, so this approach renders everywhere.
The "3D" feel comes from parallax: star layers drifting at different speeds
over fixed nebula gradients.
"""
import random
import streamlit as st
from typing import Optional


# Color Palette
PRIMARY = "#4F46E5"        # Indigo (CTA buttons)
SECONDARY = "#10B981"      # Green (success states)
ACCENT = "#F59E0B"         # Amber (highlights)
BACKGROUND = "#0d0f1d"     # Dark cosmic blue background
CARD_BG = "rgba(26, 29, 41, 0.6)"        # Transparent dark card background
TEXT_PRIMARY = "#F9FAFB"   # Light gray (headings)
TEXT_SECONDARY = "#D1D5DB" # Medium light gray (body text)
BORDER = "rgba(255, 255, 255, 0.08)" # Translucent border
SHADOW = "0 4px 30px rgba(0, 0, 0, 0.4)"
SHADOW_LG = "0 10px 30px rgba(0, 0, 0, 0.6)"

# Star tints for the CSS starfield (white, ice-blue, violet, sky-blue, lilac)
_STAR_COLORS = ["#ffffff", "#dbe4ff", "#a78bfa", "#60a5fa", "#c7d2fe"]


def _star_shadows(count: int, seed: int, max_y_vh: int = 200) -> str:
    """Build a CSS box-shadow list that paints `count` stars.

    Positions use vw/vh units so the field scales with the viewport. The field
    is `max_y_vh` tall (default 2x viewport) so a translateY(-50%) loop drifts
    seamlessly. Seeded so the sky is stable across Streamlit reruns.
    """
    rng = random.Random(seed)
    shadows = []
    for _ in range(count):
        x = round(rng.uniform(0, 100), 2)
        y = round(rng.uniform(0, max_y_vh), 2)
        color = rng.choice(_STAR_COLORS)
        shadows.append(f"{x}vw {y}vh {color}")
    return ", ".join(shadows)


def inject_galaxy_background():
    """Paint the fixed deep-space background: nebulae + two parallax star layers.

    Pure CSS on the main document — no canvas, no parent-DOM access — so it
    renders reliably on Streamlit Cloud. Pages keep .stApp transparent and the
    cosmos shows through from `body`.
    """
    small_stars = _star_shadows(170, seed=42)
    big_stars = _star_shadows(60, seed=7)

    st.markdown(f"""
    <style>
    /* ── Deep-space base: nebulae live on <body>, beneath everything ── */
    body {{
        background:
            radial-gradient(ellipse 55% 45% at 18% 22%, rgba(109, 74, 255, 0.16), transparent 60%),
            radial-gradient(ellipse 50% 40% at 82% 68%, rgba(37, 99, 235, 0.13), transparent 60%),
            radial-gradient(ellipse 45% 35% at 60% 8%, rgba(168, 85, 247, 0.10), transparent 55%),
            radial-gradient(ellipse 70% 55% at 50% 115%, rgba(16, 185, 129, 0.05), transparent 60%),
            linear-gradient(180deg, #0a0c1c 0%, #070818 40%, #04050e 100%) !important;
        background-attachment: fixed !important;
    }}

    /* ── Star layer 1: dense small stars, slow drift (far away) ── */
    [data-testid="stAppViewContainer"]::before {{
        content: '';
        position: fixed;
        top: 0; left: 0;
        width: 2px; height: 2px;
        border-radius: 50%;
        background: transparent;
        box-shadow: {small_stars};
        animation: starDriftFar 240s linear infinite, starTwinkle 7s ease-in-out infinite;
        z-index: 0;
        pointer-events: none;
    }}

    /* ── Star layer 2: sparse bigger stars, faster drift (close = 3D parallax) ── */
    [data-testid="stAppViewContainer"]::after {{
        content: '';
        position: fixed;
        top: 0; left: 0;
        width: 3px; height: 3px;
        border-radius: 50%;
        background: transparent;
        box-shadow: {big_stars};
        filter: drop-shadow(0 0 6px rgba(167, 139, 250, 0.55));
        animation: starDriftNear 130s linear infinite, starTwinkle 5s ease-in-out infinite reverse;
        z-index: 0;
        pointer-events: none;
    }}

    @keyframes starDriftFar {{
        from {{ transform: translateY(0); }}
        to   {{ transform: translateY(-100vh); }}
    }}
    @keyframes starDriftNear {{
        from {{ transform: translateY(0) translateX(0); }}
        to   {{ transform: translateY(-100vh) translateX(-3vw); }}
    }}
    @keyframes starTwinkle {{
        0%, 100% {{ opacity: 0.85; }}
        50%      {{ opacity: 0.45; }}
    }}

    /* Content always paints above the cosmos */
    .block-container {{
        position: relative;
        z-index: 1;
    }}
    </style>
    """, unsafe_allow_html=True)


def apply_theme():
    """Inject the full design system: galaxy background + glass-morphism UI."""
    css = f"""
    <style>
    /* Reset Streamlit surfaces so the cosmos on <body> shows through */
    .main, .stApp, [data-testid="stAppViewContainer"], header[data-testid="stHeader"] {{
        background-color: transparent !important;
        background: transparent !important;
    }}

    .block-container {{
        background-color: transparent !important;
        padding-top: 2rem;
        padding-bottom: 2rem;
    }}

    /* Global text adjustment for dark mode readability */
    p, div, span {{
        color: {TEXT_SECONDARY};
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    }}

    h1, h2, h3 {{
        color: {TEXT_PRIMARY};
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
        font-weight: 700;
        letter-spacing: -0.02em;
        text-shadow: 0 2px 10px rgba(0, 0, 0, 0.5);
    }}

    /* ── Hero section ── */
    .hero-badge {{
        display: inline-block;
        padding: 6px 18px;
        border-radius: 999px;
        font-size: 0.8rem;
        font-weight: 600;
        letter-spacing: 0.06em;
        color: #c7d2fe;
        background: rgba(99, 102, 241, 0.12);
        border: 1px solid rgba(129, 140, 248, 0.35);
        box-shadow: 0 0 24px rgba(79, 70, 229, 0.25);
        backdrop-filter: blur(10px);
        margin-bottom: 1rem;
    }}
    .hero-title {{
        font-size: 3.2rem;
        font-weight: 800;
        line-height: 1.1;
        margin: 0.25rem 0 0.75rem 0;
        background: linear-gradient(135deg, #e0e7ff 10%, #a78bfa 45%, #60a5fa 90%);
        -webkit-background-clip: text;
        background-clip: text;
        -webkit-text-fill-color: transparent;
        text-shadow: none;
    }}
    .hero-subtitle {{
        font-size: 1.05rem;
        color: rgba(209, 213, 219, 0.75);
        line-height: 1.6;
    }}

    /* ── Section headers ── */
    .section-header {{
        display: flex;
        align-items: center;
        gap: 0.6rem;
        margin: 2rem 0 1rem 0;
        padding-bottom: 0.6rem;
        border-bottom: 1px solid rgba(129, 140, 248, 0.25);
    }}
    .section-header-icon {{
        font-size: 1.5rem;
        filter: drop-shadow(0 0 10px rgba(167, 139, 250, 0.5));
    }}
    .section-header-text {{
        margin: 0 !important;
        font-size: 1.4rem !important;
    }}

    /* Sidebar Glassmorphism */
    [data-testid="stSidebar"] {{
        background-color: rgba(13, 15, 29, 0.72) !important;
        backdrop-filter: blur(20px) saturate(180%);
        border-right: 1px solid rgba(255, 255, 255, 0.08) !important;
    }}

    [data-testid="stSidebarContent"] {{
        background-color: transparent !important;
    }}

    /* UI Cards Glassmorphism */
    .metric-card, .streamlit-expanderHeader, .stAlert, div[data-testid="stExpander"] {{
        background-color: rgba(30, 34, 52, 0.5) !important;
        backdrop-filter: blur(16px) saturate(120%) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 12px !important;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3) !important;
        transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1) !important;
    }}

    .metric-card {{
        padding: 1.25rem 1.5rem !important;
    }}

    .metric-card:hover {{
        background-color: rgba(30, 34, 52, 0.7) !important;
        border: 1px solid rgba(255, 255, 255, 0.15) !important;
        box-shadow: 0 12px 40px 0 rgba(79, 70, 229, 0.15) !important;
        transform: translateY(-2px) !important;
    }}

    /* Native st.metric gets the same glass treatment */
    [data-testid="stMetric"] {{
        background: rgba(30, 34, 52, 0.5);
        backdrop-filter: blur(16px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 0.9rem 1.1rem;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
    }}

    .metric-label {{
        font-size: 0.875rem;
        font-weight: 600;
        color: {TEXT_SECONDARY};
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 0.5rem;
    }}

    .metric-value {{
        font-size: 2rem;
        font-weight: 700;
        color: {TEXT_PRIMARY};
        line-height: 1;
    }}

    .metric-icon {{
        font-size: 2rem;
        margin-bottom: 0.5rem;
    }}

    /* Buttons with glowing cyber edges */
    .stButton > button {{
        background: linear-gradient(135deg, {PRIMARY} 0%, #6366F1 100%) !important;
        color: #FFFFFF !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        box-shadow: 0 4px 15px rgba(79, 70, 229, 0.4) !important;
        padding: 0.6rem 1.2rem !important;
    }}

    .stButton > button:hover {{
        background: linear-gradient(135deg, #4338CA 0%, {PRIMARY} 100%) !important;
        box-shadow: 0 6px 20px rgba(99, 102, 241, 0.6) !important;
        transform: translateY(-1.5px) !important;
        border-color: rgba(255, 255, 255, 0.4) !important;
    }}

    .stButton > button:active {{
        transform: translateY(0.5px) !important;
    }}

    /* Download buttons match regular buttons */
    .stDownloadButton > button {{
        background: rgba(30, 34, 52, 0.6) !important;
        color: #e0e7ff !important;
        border: 1px solid rgba(129, 140, 248, 0.35) !important;
        border-radius: 8px !important;
        backdrop-filter: blur(10px) !important;
        transition: all 0.3s ease !important;
    }}
    .stDownloadButton > button:hover {{
        border-color: rgba(167, 139, 250, 0.7) !important;
        box-shadow: 0 0 18px rgba(99, 102, 241, 0.35) !important;
    }}

    /* Input controls styling */
    .stTextArea textarea, .stTextInput input, div[data-baseweb="select"] {{
        background-color: rgba(20, 22, 37, 0.6) !important;
        color: #F9FAFB !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 8px !important;
        backdrop-filter: blur(8px) !important;
    }}

    .stTextArea textarea:focus, .stTextInput input:focus, div[data-baseweb="select"]:focus-within {{
        border-color: {PRIMARY} !important;
        box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.25) !important;
    }}

    /* Override white text styles inside dropdown options */
    div[data-baseweb="select"] * {{
        color: #F9FAFB !important;
        -webkit-text-fill-color: #F9FAFB !important;
    }}

    ul[role="listbox"], li[role="option"], div[data-baseweb="popover"] {{
        background-color: #16192b !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        color: #F9FAFB !important;
    }}

    li[role="option"] * {{
        color: #F9FAFB !important;
        -webkit-text-fill-color: #F9FAFB !important;
    }}

    li[role="option"]:hover, li[role="option"][aria-selected="true"] {{
        background-color: rgba(79, 70, 229, 0.3) !important;
        color: #FFFFFF !important;
    }}

    /* Tabs Styling */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 0.5rem;
    }}

    .stTabs [data-baseweb="tab"] {{
        background-color: rgba(30, 34, 52, 0.4) !important;
        border-radius: 8px 8px 0 0 !important;
        padding: 0.6rem 1.2rem !important;
        border: 1px solid rgba(255, 255, 255, 0.05) !important;
        color: {TEXT_SECONDARY} !important;
        backdrop-filter: blur(8px) !important;
    }}

    .stTabs [aria-selected="true"] {{
        background-color: rgba(79, 70, 229, 0.35) !important;
        color: #FFFFFF !important;
        border: 1px solid rgba(255, 255, 255, 0.15) !important;
        border-bottom: 2px solid #6366F1 !important;
    }}

    .stTabs [aria-selected="true"] p {{
        color: #FFFFFF !important;
    }}

    /* Charts: let the cosmos show through Plotly */
    .js-plotly-plot .main-svg {{
        background: transparent !important;
    }}
    [data-testid="stDataFrame"] {{
        background: rgba(20, 22, 37, 0.55);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        backdrop-filter: blur(12px);
    }}

    /* Chat surfaces */
    [data-testid="stChatInput"] {{
        background: rgba(20, 22, 37, 0.7) !important;
        border: 1px solid rgba(129, 140, 248, 0.3) !important;
        border-radius: 12px !important;
        backdrop-filter: blur(12px) !important;
    }}

    /* Slim glassy scrollbar */
    ::-webkit-scrollbar {{ width: 10px; height: 10px; }}
    ::-webkit-scrollbar-track {{ background: rgba(10, 12, 28, 0.6); }}
    ::-webkit-scrollbar-thumb {{
        background: rgba(99, 102, 241, 0.45);
        border-radius: 999px;
        border: 2px solid rgba(10, 12, 28, 0.6);
    }}
    ::-webkit-scrollbar-thumb:hover {{ background: rgba(129, 140, 248, 0.7); }}
    </style>
    """
    inject_galaxy_background()
    st.markdown(css, unsafe_allow_html=True)


def render_app_header():
    """Render the hero section with modern SaaS styling."""
    st.markdown("""
    <div style="text-align: center; padding: 2rem 0;">
        <div class="hero-badge">🚀 AI-Powered Marketing Intelligence</div>
        <h1 class="hero-title">Marketing Simulation</h1>
        <p class="hero-subtitle">
            Predict how your audience will react to your ads before you spend a single rupee.<br>
            Powered by <strong>Big Five Personality Traits</strong> and <strong>Prospect Theory</strong>.
        </p>
    </div>
    """, unsafe_allow_html=True)


def render_metric_card(label: str, value: str, icon: Optional[str] = None):
    """
    Render a styled metric card.

    Args:
        label: Metric label (e.g., "Lift", "Conversions")
        value: Metric value (e.g., "45.2%", "1234")
        icon: Optional emoji icon
    """
    icon_html = f'<div class="metric-icon">{icon}</div>' if icon else ''

    st.markdown(f"""
    <div class="metric-card">
        {icon_html}
        <div class="metric-label">{label}</div>
        <div class="metric-value">{value}</div>
    </div>
    """, unsafe_allow_html=True)


def render_section_header(text: str, icon: Optional[str] = None):
    """
    Render a styled section header with optional icon.

    Args:
        text: Header text
        icon: Optional emoji icon
    """
    icon_html = f'<span class="section-header-icon">{icon}</span>' if icon else ''

    st.markdown(f"""
    <div class="section-header">
        {icon_html}
        <h2 class="section-header-text">{text}</h2>
    </div>
    """, unsafe_allow_html=True)
