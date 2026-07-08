"""
Modern SaaS theme for Marketing Simulation Dashboard.
Provides WordPress-inspired styling with clean cards, shadows, and professional layout.
"""
import streamlit as st
import streamlit.components.v1 as components
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


def inject_galaxy_background():
    """Inject a dynamic, interactive 3D particle galaxy into the parent window's background."""
    js_code = """
    <script>
    (function() {
        const parentDoc = window.parent.document;
        if (parentDoc.getElementById('galaxy-bg-canvas')) return;

        const canvas = parentDoc.createElement('canvas');
        canvas.id = 'galaxy-bg-canvas';
        canvas.style.position = 'fixed';
        canvas.style.top = '0';
        canvas.style.left = '0';
        canvas.style.width = '100vw';
        canvas.style.height = '100vh';
        canvas.style.zIndex = '-1';
        canvas.style.pointerEvents = 'none';
        
        parentDoc.body.insertBefore(canvas, parentDoc.body.firstChild);
        
        const ctx = canvas.getContext('2d');
        
        function resize() {
            canvas.width = parentDoc.documentElement.clientWidth;
            canvas.height = parentDoc.documentElement.clientHeight;
        }
        window.parent.addEventListener('resize', resize);
        resize();
        
        class Particle {
            constructor(angle, distance, speed, y) {
                this.angle = angle;
                this.distance = distance;
                this.speed = speed;
                this.y = y;
                this.color = Math.random() > 0.4 ? 'rgba(79, 70, 229, ' : 'rgba(16, 185, 129, ';
                this.size = Math.random() * 2.5 + 0.8;
            }
            update() {
                this.angle += this.speed;
            }
            get3DPosition() {
                const x = Math.cos(this.angle) * this.distance;
                const z = Math.sin(this.angle) * this.distance;
                return { x, y: this.y, z };
            }
        }
        
        const particles = [];
        const particleCount = 300;
        const numArms = 3;
        const armAngle = (Math.PI * 2) / numArms;
        
        for (let i = 0; i < particleCount; i++) {
            const arm = i % numArms;
            const t = Math.random();
            const dist = t * t * 450 + 20; 
            const twist = dist * 0.015;
            const angle = arm * armAngle + twist + (Math.random() - 0.5) * 0.35;
            const speed = (0.0008 + Math.random() * 0.0012) * (150 / (dist + 50));
            const yOffset = (Math.random() - 0.5) * 45 * (1 - (dist / 500));
            
            particles.push(new Particle(angle, dist, speed, yOffset));
        }
        
        const fov = 350;
        
        function draw() {
            if (!canvas.isConnected) return; // Stop loop if element removed
            
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            
            // Deep space gradient
            const bgGrad = ctx.createRadialGradient(canvas.width/2, canvas.height/2, 10, canvas.width/2, canvas.height/2, Math.max(canvas.width, canvas.height));
            bgGrad.addColorStop(0, '#0d0f1d');
            bgGrad.addColorStop(1, '#05060d');
            ctx.fillStyle = bgGrad;
            ctx.fillRect(0, 0, canvas.width, canvas.height);
            
            const currentCx = canvas.width / 2;
            const currentCy = canvas.height / 2;
            
            const time = Date.now() * 0.0001;
            const camAngle = time * 0.05;
            const cosCam = Math.cos(camAngle);
            const sinCam = Math.sin(camAngle);
            
            const rendered = particles.map(p => {
                p.update();
                const pos = p.get3DPosition();
                
                const rotX = pos.x * cosCam - pos.z * sinCam;
                const rotZ = pos.x * sinCam + pos.z * cosCam;
                
                const zDistance = rotZ + 600;
                const scale = fov / zDistance;
                
                const screenX = currentCx + rotX * scale;
                const screenY = currentCy + pos.y * scale;
                
                return {
                    x: screenX,
                    y: screenY,
                    size: p.size * scale,
                    z: zDistance,
                    color: p.color,
                    raw: pos
                };
            });
            
            rendered.sort((a, b) => b.z - a.z);
            
            ctx.globalCompositeOperation = 'screen';
            
            // Render connection lines (agent networks)
            ctx.lineWidth = 0.5;
            for (let i = 0; i < rendered.length; i++) {
                const p1 = rendered[i];
                let linksCount = 0;
                for (let j = i + 1; j < rendered.length; j++) {
                    const p2 = rendered[j];
                    const dx = p1.x - p2.x;
                    const dy = p1.y - p2.y;
                    const distSq = dx*dx + dy*dy;
                    
                    if (distSq < 4800 && Math.abs(p1.z - p2.z) < 80 && linksCount < 2) {
                        const alpha = (1 - Math.sqrt(distSq) / 70) * 0.12;
                        ctx.strokeStyle = `rgba(99, 102, 241, ${alpha})`;
                        ctx.beginPath();
                        ctx.moveTo(p1.x, p1.y);
                        ctx.lineTo(p2.x, p2.y);
                        ctx.stroke();
                        linksCount++;
                    }
                }
            }
            
            // Draw particles (representing consumer agents)
            rendered.forEach(p => {
                if (p.x < 0 || p.x > canvas.width || p.y < 0 || p.y > canvas.height) return;
                
                const alpha = Math.min(1.0, Math.max(0.1, (800 - p.z) / 400));
                ctx.fillStyle = p.color + alpha + ')';
                
                if (p.size > 2.2) {
                    ctx.shadowBlur = p.size * 2.5;
                    ctx.shadowColor = p.color.includes('79,') ? '#4F46E5' : '#10B981';
                } else {
                    ctx.shadowBlur = 0;
                }
                
                ctx.beginPath();
                ctx.arc(p.x, p.y, Math.max(0.6, p.size), 0, Math.PI * 2);
                ctx.fill();
            });
            
            ctx.shadowBlur = 0;
            requestAnimationFrame(draw);
        }
        
        requestAnimationFrame(draw);
    })();
    </script>
    """
    components.html(js_code, height=0, width=0)


def apply_theme():
    """Inject glassmorphism styles and 3D galaxy canvas."""
    css = f"""
    <style>
    /* Reset Streamlit Backgrounds to display the background canvas */
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

    /* Sidebar Glassmorphism */
    [data-testid="stSidebar"] {{
        background-color: rgba(13, 15, 29, 0.7) !important;
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

    .metric-card:hover {{
        background-color: rgba(30, 34, 52, 0.7) !important;
        border: 1px solid rgba(255, 255, 255, 0.15) !important;
        box-shadow: 0 12px 40px 0 rgba(79, 70, 229, 0.15) !important;
        transform: translateY(-2px) !important;
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
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)
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
