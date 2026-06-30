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
BACKGROUND = "#1A1D29"     # Dark blue-gray (page background)
CARD_BG = "#252936"        # Dark card background
TEXT_PRIMARY = "#F9FAFB"   # Light gray (headings)
TEXT_SECONDARY = "#D1D5DB" # Medium light gray (body text)
BORDER = "#374151"         # Dark border
SHADOW = "0 1px 3px 0 rgba(0, 0, 0, 0.3), 0 1px 2px 0 rgba(0, 0, 0, 0.2)"
SHADOW_LG = "0 10px 15px -3px rgba(0, 0, 0, 0.4), 0 4px 6px -2px rgba(0, 0, 0, 0.3)"


def apply_theme():
    """Inject custom CSS for modern SaaS styling."""
    css = f"""
    <style>
    /* Global Styles */
    .main {{
        background: linear-gradient(135deg, #1A1D29 0%, #252936 100%);
    }}

    .stApp {{
        background: linear-gradient(135deg, #1A1D29 0%, #252936 100%);
    }}

    [data-testid="stAppViewContainer"] {{
        background: linear-gradient(135deg, #1A1D29 0%, #252936 100%);
    }}

    .block-container {{
        background-color: transparent;
        padding-top: 1rem;
    }}

    /* Top Header Integration */
    header[data-testid="stHeader"] {{
        background: linear-gradient(135deg, #1A1D29 0%, #252936 100%);
        border-bottom: 1px solid {BORDER};
    }}

    [data-testid="stToolbar"] {{
        background-color: transparent;
    }}

    [data-testid="stToolbar"] button {{
        color: {TEXT_SECONDARY};
    }}

    [data-testid="stToolbar"] button:hover {{
        color: {TEXT_PRIMARY};
    }}

    /* Sidebar Alignment */
    [data-testid="stSidebar"] {{
        background-color: {CARD_BG};
        border-right: 1px solid {BORDER};
        padding-top: 0;
    }}

    [data-testid="stSidebarContent"] {{
        padding-top: 1rem;
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
        background-color: {PRIMARY};
        color: #FFFFFF !important;
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.2s ease;
        border: 1px solid transparent;
        box-shadow: 0 4px 10px rgba(79, 70, 229, 0.25);
        padding: 0.5rem 1rem;
    }}

    .stButton > button:hover {{
        background-color: #4338CA;
        color: #FFFFFF !important;
        box-shadow: 0 6px 15px rgba(79, 70, 229, 0.35);
        transform: translateY(-1px);
    }}

    .stButton > button:active {{
        background-color: #3730A3;
        color: #FFFFFF !important;
        transform: translateY(0);
    }}

    .stButton > button:disabled {{
        background-color: #E5E7EB !important;
        color: #9CA3AF !important;
        box-shadow: none;
        cursor: not-allowed;
        opacity: 0.6;
    }}

    /* Primary Button */
    .stButton > button[kind="primary"] {{
        background-color: {PRIMARY};
        color: #FFFFFF !important;
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

    /* Selectbox / Dropdown */
    .stSelectbox {{
        color: #111827;
    }}

    .stSelectbox label {{
        color: {TEXT_PRIMARY};
        font-weight: 600;
    }}

    .stSelectbox > div > div {{
        background-color: #FFFFFF !important;
        color: #111827 !important;
        border: 1px solid #D1D5DB;
        border-radius: 8px;
    }}

    div[data-baseweb="select"] {{
        background-color: #FFFFFF !important;
        border-radius: 8px;
        border: 1px solid #D1D5DB !important;
    }}

    div[data-baseweb="select"] * {{
        color: #111827 !important;
        -webkit-text-fill-color: #111827 !important;
        opacity: 1 !important;
    }}

    div[data-baseweb="select"] > div {{
        background-color: #FFFFFF !important;
        color: #111827 !important;
    }}

    div[data-baseweb="select"] span {{
        color: #111827 !important;
        -webkit-text-fill-color: #111827 !important;
    }}

    div[data-baseweb="select"] input {{
        color: #111827 !important;
        -webkit-text-fill-color: #111827 !important;
    }}

    div[data-baseweb="select"] svg {{
        fill: #111827 !important;
    }}

    div[data-baseweb="select"]:focus-within {{
        border-color: {PRIMARY};
        box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.1);
    }}

    /* Dropdown Menu */
    div[data-baseweb="popover"] {{
        background-color: #FFFFFF !important;
    }}

    div[data-baseweb="popover"] * {{
        color: #111827 !important;
        -webkit-text-fill-color: #111827 !important;
        opacity: 1 !important;
    }}

    ul[role="listbox"] {{
        background-color: #FFFFFF !important;
        border: 1px solid #D1D5DB;
        border-radius: 8px;
    }}

    li[role="option"] {{
        background-color: #FFFFFF !important;
        color: #111827 !important;
        -webkit-text-fill-color: #111827 !important;
        font-weight: 500;
        opacity: 1 !important;
    }}

    li[role="option"] * {{
        color: #111827 !important;
        -webkit-text-fill-color: #111827 !important;
        opacity: 1 !important;
    }}

    li[role="option"]:hover {{
        background-color: #F3F4F6 !important;
        color: #111827 !important;
        -webkit-text-fill-color: #111827 !important;
    }}

    li[role="option"]:hover * {{
        color: #111827 !important;
        -webkit-text-fill-color: #111827 !important;
    }}

    li[role="option"][aria-selected="true"] {{
        background-color: #EEF2FF !important;
        color: #111827 !important;
        -webkit-text-fill-color: #111827 !important;
        font-weight: 600;
    }}

    li[role="option"][aria-selected="true"] * {{
        color: #111827 !important;
        -webkit-text-fill-color: #111827 !important;
    }}

    [data-baseweb="menu"] * {{
        color: #111827 !important;
        -webkit-text-fill-color: #111827 !important;
        opacity: 1 !important;
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
