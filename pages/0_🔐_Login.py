import streamlit as st
import streamlit.components.v1 as components
from src.core.supabase_client import SupabaseManager
from src.core.auth_utils import is_auth_enabled, get_local_user

st.set_page_config(page_title="Login", page_icon="🔐", layout="centered")

# Initialize session
if "auth_initialized" not in st.session_state:
    st.session_state["auth_initialized"] = True
    st.session_state["auth_mode"] = "supabase" if is_auth_enabled() else "local"
    st.session_state["user"] = None
    st.session_state["access_token"] = None

    if st.session_state["auth_mode"] == "local":
        st.session_state["user"] = get_local_user()

# Auto-redirect if already logged in
if st.session_state.get("user") and st.session_state["user"].get("is_authenticated"):
    st.switch_page("app.py")

# CSS for Glassmorphism
st.markdown("""
    <style>
    /* Make standard Streamlit background transparent */
    .stApp {
        background-color: transparent !important;
    }
    
    /* Center and style the login card */
    .main .block-container {
        max-width: 450px !important;
        padding: 2.5rem !important;
        margin-top: 15vh !important;
        background: rgba(20, 20, 30, 0.6) !important;
        backdrop-filter: blur(12px) !important;
        -webkit-backdrop-filter: blur(12px) !important;
        border-radius: 16px !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        box-shadow: 0 12px 40px 0 rgba(0, 0, 0, 0.5) !important;
        color: white !important;
    }

    h1 {
        text-align: center;
        background: linear-gradient(90deg, #bb86fc, #03dac6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }

    p, label, .stMarkdown {
        color: #e0e0e0 !important;
    }

    .stButton>button {
        background: linear-gradient(90deg, #6200ea 0%, #03dac6 100%);
        border: none;
        color: white;
        width: 100%;
        font-weight: bold;
        transition: transform 0.2s, box-shadow 0.2s;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(3, 218, 198, 0.4);
        color: white;
    }
    
    .secondary-btn>button {
        background: transparent !important;
        border: 1px solid rgba(255, 255, 255, 0.3) !important;
        box-shadow: none !important;
    }
    </style>
""", unsafe_allow_html=True)

# 3D Background Injection (Targets parent document)
three_js_code = """
<script type="importmap">
  {
    "imports": {
      "three": "https://unpkg.com/three@0.160.0/build/three.module.js"
    }
  }
</script>
<script type="module">
  import * as THREE from 'three';

  const parentBody = window.parent.document.querySelector('.stApp');
  if (parentBody) {
      let container = window.parent.document.getElementById('three-bg');
      if (!container) {
          container = window.parent.document.createElement('div');
          container.id = 'three-bg';
          container.style.position = 'fixed';
          container.style.top = '0';
          container.style.left = '0';
          container.style.width = '100vw';
          container.style.height = '100vh';
          container.style.zIndex = '-1';
          container.style.background = 'radial-gradient(circle at center, #1e1e2f 0%, #0a0a12 100%)';
          parentBody.insertBefore(container, parentBody.firstChild);
      } else {
          // Clear previous renderers if hot-reloading
          container.innerHTML = '';
      }

      const scene = new THREE.Scene();
      const camera = new THREE.PerspectiveCamera(75, window.parent.innerWidth / window.parent.innerHeight, 0.1, 1000);
      const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
      renderer.setSize(window.parent.innerWidth, window.parent.innerHeight);
      renderer.setPixelRatio(window.devicePixelRatio);
      container.appendChild(renderer.domElement);

      // Core shape
      const geometry = new THREE.IcosahedronGeometry(2.5, 1);
      const material = new THREE.MeshBasicMaterial({ color: 0x03dac6, wireframe: true, transparent: true, opacity: 0.3 });
      const core = new THREE.Mesh(geometry, material);
      scene.add(core);
      
      const geometry2 = new THREE.IcosahedronGeometry(3, 0);
      const material2 = new THREE.MeshBasicMaterial({ color: 0xbb86fc, wireframe: true, transparent: true, opacity: 0.1 });
      const outer = new THREE.Mesh(geometry2, material2);
      scene.add(outer);

      // Particles
      const particlesGeometry = new THREE.BufferGeometry();
      const particlesCount = 800;
      const posArray = new Float32Array(particlesCount * 3);
      for(let i=0; i<particlesCount * 3; i++) {
          posArray[i] = (Math.random() - 0.5) * 20;
      }
      particlesGeometry.setAttribute('position', new THREE.BufferAttribute(posArray, 3));
      const particlesMaterial = new THREE.PointsMaterial({ size: 0.03, color: 0xbb86fc, transparent: true, opacity: 0.6 });
      const particlesMesh = new THREE.Points(particlesGeometry, particlesMaterial);
      scene.add(particlesMesh);

      camera.position.z = 6;

      // Mouse interaction
      let mouseX = 0;
      let mouseY = 0;
      window.parent.addEventListener('mousemove', (event) => {
          mouseX = (event.clientX / window.parent.innerWidth) * 2 - 1;
          mouseY = -(event.clientY / window.parent.innerHeight) * 2 + 1;
      });

      function animate() {
          requestAnimationFrame(animate);
          
          core.rotation.x += 0.001;
          core.rotation.y += 0.002;
          outer.rotation.x -= 0.001;
          outer.rotation.z += 0.001;
          
          particlesMesh.rotation.y -= 0.0005;
          particlesMesh.rotation.x += 0.0002;

          // Parallax effect
          camera.position.x += (mouseX * 0.5 - camera.position.x) * 0.05;
          camera.position.y += (mouseY * 0.5 - camera.position.y) * 0.05;
          camera.lookAt(scene.position);

          renderer.render(scene, camera);
      }
      animate();

      window.parent.addEventListener('resize', () => {
          camera.aspect = window.parent.innerWidth / window.parent.innerHeight;
          camera.updateProjectionMatrix();
          renderer.setSize(window.parent.innerWidth, window.parent.innerHeight);
      });
  }
</script>
"""
components.html(three_js_code, height=0, width=0)

# Form Content
st.title("Digital Wind Tunnel")
st.markdown("<p style='text-align: center; margin-bottom: 2rem;'>Predict ad performance before spending a dollar.</p>", unsafe_allow_html=True)

if st.session_state["auth_mode"] == "local":
    st.warning("Running in Local Mode. Supabase credentials not found.")
    if st.button("Continue as Local Developer"):
        st.session_state["user"] = get_local_user()
        st.switch_page("app.py")
else:
    with st.form("login_form", clear_on_submit=True):
        email = st.text_input("Email", placeholder="you@company.com")
        password = st.text_input("Password", type="password", placeholder="••••••••")
        submit = st.form_submit_button("Sign In")

    if submit:
        if not email or not password:
            st.error("Email and password are required")
        else:
            manager = SupabaseManager()
            with st.spinner("Authenticating..."):
                response = manager.sign_in(email, password)
                
            if response.get("status") == "success":
                session = response.get("session")
                user_data = response.get("user")
                if session and user_data:
                    st.session_state["access_token"] = session.access_token
                    st.session_state["user"] = {
                        "id": user_data.id,
                        "email": user_data.email,
                        "is_authenticated": True,
                        "mode": "supabase"
                    }
                    st.success("Access Granted. Initializing simulation engine...")
                    import time
                    time.sleep(1)
                    st.switch_page("app.py")
                else:
                    st.error("Invalid response from auth service")
            else:
                st.error(f"Login failed: {response.get('message', 'Unknown error')}")

    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<div class="secondary-btn">', unsafe_allow_html=True)
        if st.button("Create Account"):
            st.switch_page("pages/Register.py")
        st.markdown('</div>', unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="secondary-btn">', unsafe_allow_html=True)
        if st.button("Forgot Password?"):
            st.switch_page("pages/ResetPassword.py")
        st.markdown('</div>', unsafe_allow_html=True)
