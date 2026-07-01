import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(
    page_title="Digital Wind Tunnel",
    page_icon="🌀",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Hide sidebar completely on login page
st.markdown("""
<style>
    [data-testid="stSidebar"] { display: none !important; }
    [data-testid="stSidebarNav"] { display: none !important; }
    section[data-testid="stSidebar"] { display: none !important; }
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    .stApp { background: transparent !important; }
</style>
""", unsafe_allow_html=True)

# 3D Background (Three.js)
three_js_code = """
<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
<style>
    #login-canvas {
        position: fixed;
        top: 0;
        left: 0;
        width: 100vw;
        height: 100vh;
        z-index: 0;
        pointer-events: none;
    }
    .glass-card {
        position: relative;
        z-index: 1;
        background: rgba(255, 255, 255, 0.07);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border-radius: 24px;
        border: 1px solid rgba(255, 255, 255, 0.15);
        box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5), inset 0 1px 0 rgba(255, 255, 255, 0.1);
        padding: 48px 40px;
        max-width: 420px;
        margin: 0 auto;
        animation: fadeIn 1s ease-out;
    }
    .glass-card h1 {
        font-size: 28px;
        font-weight: 700;
        background: linear-gradient(135deg, #a78bfa, #60a5fa);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 8px;
        letter-spacing: -0.5px;
    }
    .glass-card .subtitle {
        text-align: center;
        color: rgba(255,255,255,0.6);
        font-size: 14px;
        margin-bottom: 32px;
    }
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    .stTextInput > div > div > input {
        background: rgba(255,255,255,0.08) !important;
        border: 1px solid rgba(255,255,255,0.12) !important;
        border-radius: 12px !important;
        color: white !important;
        padding: 12px 16px !important;
        font-size: 15px !important;
        transition: all 0.3s ease;
    }
    .stTextInput > div > div > input:focus {
        border-color: #a78bfa !important;
        box-shadow: 0 0 0 3px rgba(167, 139, 250, 0.2) !important;
    }
    .stButton > button {
        width: 100%;
        background: linear-gradient(135deg, #a78bfa, #60a5fa) !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 12px !important;
        font-weight: 600 !important;
        font-size: 16px !important;
        color: white !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 15px rgba(167, 139, 250, 0.3) !important;
    }
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 25px rgba(167, 139, 250, 0.5) !important;
    }
    .links {
        display: flex;
        justify-content: space-between;
        margin-top: 16px;
        font-size: 14px;
    }
    .links a {
        color: rgba(255,255,255,0.6) !important;
        text-decoration: none !important;
        transition: color 0.3s ease;
    }
    .links a:hover {
        color: #a78bfa !important;
    }
</style>
<div id="login-canvas"></div>
<script>
    // --- 3D Scene Setup ---
    const container = document.getElementById('login-canvas');
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    container.appendChild(renderer.domElement);

    // --- Particle System ---
    const particlesGeometry = new THREE.BufferGeometry();
    const particlesCount = 2000;
    const posArray = new Float32Array(particlesCount * 3);
    for (let i = 0; i < particlesCount * 3; i++) {
        posArray[i] = (Math.random() - 0.5) * 20;
    }
    particlesGeometry.setAttribute('position', new THREE.BufferAttribute(posArray, 3));
    const particlesMaterial = new THREE.PointsMaterial({
        size: 0.04,
        color: 0xa78bfa,
        transparent: true,
        opacity: 0.6,
        blending: THREE.AdditiveBlending
    });
    const particlesMesh = new THREE.Points(particlesGeometry, particlesMaterial);
    scene.add(particlesMesh);

    // --- Rotating Icosahedron ---
    const geometry = new THREE.IcosahedronGeometry(1.8, 1);
    const material = new THREE.MeshPhysicalMaterial({
        color: 0x60a5fa,
        metalness: 0.1,
        roughness: 0.1,
        transparent: true,
        opacity: 0.15,
        wireframe: true,
        emissive: 0xa78bfa,
        emissiveIntensity: 0.1
    });
    const mesh = new THREE.Mesh(geometry, material);
    scene.add(mesh);

    // --- Glow ring ---
    const ringGeometry = new THREE.TorusGeometry(2.2, 0.03, 16, 100);
    const ringMaterial = new THREE.MeshPhysicalMaterial({
        color: 0xa78bfa,
        emissive: 0xa78bfa,
        emissiveIntensity: 0.3,
        transparent: true,
        opacity: 0.3
    });
    const ring = new THREE.Mesh(ringGeometry, ringMaterial);
    ring.rotation.x = Math.PI / 2;
    scene.add(ring);

    camera.position.z = 5;

    // --- Animation ---
    let mouseX = 0, mouseY = 0;
    document.addEventListener('mousemove', (e) => {
        mouseX = (e.clientX / window.innerWidth - 0.5) * 2;
        mouseY = (e.clientY / window.innerHeight - 0.5) * 2;
    });

    function animate() {
        requestAnimationFrame(animate);
        mesh.rotation.x += 0.0015;
        mesh.rotation.y += 0.003;
        particlesMesh.rotation.x += 0.0005;
        particlesMesh.rotation.y += 0.0005;
        ring.rotation.z += 0.005;
        mesh.position.x += (mouseX * 0.3 - mesh.position.x) * 0.02;
        mesh.position.y += (-mouseY * 0.3 - mesh.position.y) * 0.02;
        renderer.render(scene, camera);
    }
    animate();

    // --- Resize ---
    window.addEventListener('resize', () => {
        camera.aspect = window.innerWidth / window.innerHeight;
        camera.updateProjectionMatrix();
        renderer.setSize(window.innerWidth, window.innerHeight);
    });
</script>
"""

st.html(three_js_code, unsafe_allow_javascript=True)

# --- Login Form (Glassmorphism Card) ---
st.markdown('<div class="glass-card">', unsafe_allow_html=True)

st.markdown('<h1>🌀 Digital Wind Tunnel</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Predict ad performance before spending a dollar.</p>', unsafe_allow_html=True)

from src.core.supabase_client import sign_in
from src.core.auth_utils import set_user_session

with st.form("login_form", clear_on_submit=False):
    email = st.text_input("Email", placeholder="you@company.com")
    password = st.text_input("Password", type="password", placeholder="••••••••")
    submitted = st.form_submit_button("Sign In")

if submitted:
    if not email or not password:
        st.error("Please fill in all fields.")
    else:
        with st.spinner("Signing in..."):
            result = sign_in(email, password)
            if result.get("status") == "success":
                set_user_session(result["user"])
                st.success("✅ Login successful! Redirecting...")
                st.switch_page("app.py")
            else:
                st.error(f"❌ {result.get('message', 'Login failed.')}")

st.markdown("""
<div class="links">
    <a href="/Register">Create Account</a>
    <a href="/ResetPassword">Forgot Password?</a>
</div>
""", unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)
