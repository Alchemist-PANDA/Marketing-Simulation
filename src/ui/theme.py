"""
Modern SaaS theme for Marketing Simulation Dashboard.
Provides WordPress-inspired styling with clean cards, shadows, and professional layout.
"""
import streamlit as st
from typing import Optional


# Color Palette
PRIMARY = "#4F46E5"        # Indigo (CTA buttons)
SECONDARY = "#10B981"      # Green (success states)
ACCENT = "#F59E0B"         # Amber (highlights)
BACKGROUND = "#F5F7FB"     # Soft cool gray (page background)
CARD_BG = "#FFFFFF"        # White (cards)
TEXT_PRIMARY = "#111827"   # Dark gray (headings)
TEXT_SECONDARY = "#6B7280" # Medium gray (body text)
BORDER = "#E5E7EB"         # Light border
SHADOW = "0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)"
SHADOW_LG = "0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)"


def apply_theme():
    """Inject custom CSS for modern SaaS styling."""
    css = f"""
    <style>
    /* Global Styles */
    .main {{
        background-color: {BACKGROUND};
    }}

    /* Typography */
    h1, h2, h3 {{
        color: {TEXT_PRIMARY};
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
        font-weight: 700;
        letter-spacing: -0.02em;
    }}

    p, div, span {{
        color: {TEXT_SECONDARY};
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    }}

    /* Hero Section */
    .hero-title {{
        font-size: 3rem;
        font-weight: 800;
        color: {TEXT_PRIMARY};
        margin-bottom: 0.5rem;
        line-height: 1.2;
    }}

    .hero-subtitle {{
        font-size: 1.25rem;
        color: {TEXT_SECONDARY};
        line-height: 1.6;
        margin-bottom: 2rem;
    }}

    .hero-badge {{
        display: inline-block;
        background: linear-gradient(135deg, {PRIMARY} 0%, {ACCENT} 100%);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 9999px;
        font-size: 0.875rem;
        font-weight: 600;
        margin-bottom: 1rem;
    }}

    /* Cards */
    .metric-card {{
        background: {CARD_BG};
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: {SHADOW};
        border: 1px solid {BORDER};
        transition: all 0.3s ease;
    }}

    .metric-card:hover {{
        box-shadow: {SHADOW_LG};
        transform: translateY(-2px);
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

    /* Section Headers */
    .section-header {{
        display: flex;
        align-items: center;
        gap: 0.75rem;
        padding-bottom: 0.75rem;
        border-bottom: 2px solid {BORDER};
        margin-top: 2rem;
        margin-bottom: 1.5rem;
    }}

    .section-header-icon {{
        font-size: 1.5rem;
    }}

    .section-header-text {{
        font-size: 1.5rem;
        font-weight: 700;
        color: {TEXT_PRIMARY};
        margin: 0;
    }}

    /* Buttons */
    .stButton > button {{
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.2s ease;
        border: none;
        box-shadow: {SHADOW};
    }}

    .stButton > button:hover {{
        box-shadow: {SHADOW_LG};
        transform: translateY(-1px);
    }}

    /* Primary Button */
    .stButton > button[kind="primary"] {{
        background: linear-gradient(135deg, {PRIMARY} 0%, #6366F1 100%);
    }}

    /* Sidebar */
    .css-1d391kg, [data-testid="stSidebar"] {{
        background-color: {CARD_BG};
        border-right: 1px solid {BORDER};
    }}

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 1rem;
        background-color: transparent;
    }}

    .stTabs [data-baseweb="tab"] {{
        background-color: {CARD_BG};
        border-radius: 8px;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
        border: 1px solid {BORDER};
        box-shadow: {SHADOW};
        color: {TEXT_PRIMARY};
    }}

    .stTabs [aria-selected="true"] {{
        background-color: {PRIMARY};
        color: white;
        border-color: {PRIMARY};
        box-shadow: {SHADOW_LG};
    }}

    .stTabs [aria-selected="true"] p {{
        color: white !important;
    }}

    /* Text Areas */
    .stTextArea textarea {{
        border-radius: 8px;
        border: 1px solid {BORDER};
        box-shadow: {SHADOW};
    }}

    .stTextArea textarea:focus {{
        border-color: {PRIMARY};
        box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.1);
    }}

    /* Expanders */
    .streamlit-expanderHeader {{
        background-color: {CARD_BG};
        border-radius: 8px;
        border: 1px solid {BORDER};
        box-shadow: {SHADOW};
        font-weight: 600;
    }}

    /* Info/Warning/Success boxes */
    .stAlert {{
        border-radius: 8px;
        border: 1px solid {BORDER};
    }}

    /* Spacing */
    .block-container {{
        padding-top: 2rem;
        padding-bottom: 2rem;
    }}
    </style>
    """
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
