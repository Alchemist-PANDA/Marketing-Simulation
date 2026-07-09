"""
AI Marketing Copilot — full-screen immersive 3D galactic chat experience.
Floating icon triggers a viewport-filling overlay with Canvas 2D galaxy,
glass-morphism chat UI, file upload, and DeepSeek-powered responses.
"""
import streamlit as st
import streamlit.components.v1 as components
from typing import Optional
from src.ai.copilot import get_copilot_response, extract_file_content, build_context_message


def _init_copilot_state():
    """Initialize copilot session state keys."""
    if "copilot_messages" not in st.session_state:
        st.session_state["copilot_messages"] = []
    if "copilot_visible" not in st.session_state:
        st.session_state["copilot_visible"] = False
    if "copilot_file_context" not in st.session_state:
        st.session_state["copilot_file_context"] = ""


def render_copilot():
    """Render the full copilot: floating icon + full-screen overlay."""
    _init_copilot_state()
    _render_floating_icon()
    if st.session_state["copilot_visible"]:
        _render_fullscreen_overlay()
        _render_chat_interface()


def _render_floating_icon():
    """Render the floating 3D copilot icon injected into the parent document."""
    icon_html = """
    <div id="copilot-icon-wrapper">
        <canvas id="copilot-icon-canvas"></canvas>
        <div id="copilot-icon-label">AI</div>
    </div>
    <style>
        #copilot-icon-wrapper {
            position: fixed;
            bottom: 28px;
            right: 28px;
            width: 68px;
            height: 68px;
            z-index: 999999;
            cursor: pointer;
            border-radius: 50%;
            background: radial-gradient(circle at 30% 30%, rgba(120, 100, 255, 0.25), rgba(79, 70, 229, 0.12));
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
            border: 1.5px solid rgba(167, 139, 250, 0.45);
            box-shadow:
                0 0 30px rgba(79, 70, 229, 0.5),
                0 0 60px rgba(79, 70, 229, 0.2),
                inset 0 1px 0 rgba(255, 255, 255, 0.1);
            display: flex;
            align-items: center;
            justify-content: center;
            animation: copilotFloat 4s ease-in-out infinite, copilotGlow 3s ease-in-out infinite;
            transition: transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1), box-shadow 0.3s ease;
        }
        #copilot-icon-wrapper:hover {
            transform: scale(1.15) translateY(-2px);
            box-shadow:
                0 0 50px rgba(99, 102, 241, 0.7),
                0 0 100px rgba(99, 102, 241, 0.3),
                inset 0 1px 0 rgba(255, 255, 255, 0.15);
        }
        #copilot-icon-wrapper:active {
            transform: scale(0.95);
        }
        #copilot-icon-canvas {
            position: absolute;
            width: 100%;
            height: 100%;
            border-radius: 50%;
        }
        #copilot-icon-label {
            position: relative;
            z-index: 2;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            font-size: 17px;
            font-weight: 800;
            background: linear-gradient(135deg, #c4b5fd, #93c5fd);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            letter-spacing: 1px;
            text-shadow: 0 0 20px rgba(167, 139, 250, 0.5);
        }
        @keyframes copilotFloat {
            0%, 100% { transform: translateY(0px); }
            50% { transform: translateY(-6px); }
        }
        @keyframes copilotGlow {
            0%, 100% { box-shadow: 0 0 30px rgba(79, 70, 229, 0.5), 0 0 60px rgba(79, 70, 229, 0.2), inset 0 1px 0 rgba(255,255,255,0.1); }
            50% { box-shadow: 0 0 45px rgba(99, 102, 241, 0.6), 0 0 90px rgba(99, 102, 241, 0.25), inset 0 1px 0 rgba(255,255,255,0.15); }
        }
    </style>
    <script>
    (function() {
        const parentDoc = window.parent.document;
        const existing = parentDoc.getElementById('copilot-floating-icon');
        if (existing) existing.remove();

        const wrapper = document.getElementById('copilot-icon-wrapper');
        if (!wrapper) return;

        const clone = wrapper.cloneNode(true);
        clone.id = 'copilot-floating-icon';

        const style = document.querySelector('style');
        const styleClone = style.cloneNode(true);
        styleClone.id = 'copilot-icon-styles';
        const existingStyle = parentDoc.getElementById('copilot-icon-styles');
        if (existingStyle) existingStyle.remove();
        parentDoc.head.appendChild(styleClone);
        parentDoc.body.appendChild(clone);

        // Orbiting particle ring on the icon
        const canvas = clone.querySelector('#copilot-icon-canvas');
        if (canvas) {
            const ctx = canvas.getContext('2d');
            canvas.width = 136;
            canvas.height = 136;
            const particles = [];
            for (let i = 0; i < 24; i++) {
                particles.push({
                    angle: (i / 24) * Math.PI * 2,
                    dist: 16 + Math.random() * 16,
                    speed: 0.008 + Math.random() * 0.015,
                    size: 0.6 + Math.random() * 1.8,
                    hue: ['167,139,250', '96,165,250', '192,132,252', '129,140,248'][i % 4],
                    alpha: 0.4 + Math.random() * 0.5
                });
            }
            function drawIcon() {
                ctx.clearRect(0, 0, 136, 136);
                const cx = 68, cy = 68;
                // Core glow
                const glow = ctx.createRadialGradient(cx, cy, 2, cx, cy, 30);
                glow.addColorStop(0, 'rgba(139, 92, 246, 0.15)');
                glow.addColorStop(1, 'transparent');
                ctx.fillStyle = glow;
                ctx.fillRect(0, 0, 136, 136);
                particles.forEach(p => {
                    p.angle += p.speed;
                    const x = cx + Math.cos(p.angle) * p.dist;
                    const y = cy + Math.sin(p.angle) * p.dist;
                    ctx.beginPath();
                    ctx.arc(x, y, p.size, 0, Math.PI * 2);
                    ctx.fillStyle = 'rgba(' + p.hue + ',' + p.alpha + ')';
                    ctx.fill();
                    if (p.size > 1.2) {
                        ctx.beginPath();
                        ctx.arc(x, y, p.size * 2.5, 0, Math.PI * 2);
                        ctx.fillStyle = 'rgba(' + p.hue + ',0.08)';
                        ctx.fill();
                    }
                });
                requestAnimationFrame(drawIcon);
            }
            drawIcon();
        }

        clone.addEventListener('click', function() {
            const iframes = parentDoc.querySelectorAll('iframe');
            iframes.forEach(iframe => {
                try { iframe.contentWindow.postMessage({type: 'copilot_toggle'}, '*'); } catch(e) {}
            });
        });

        wrapper.style.display = 'none';
    })();
    </script>
    """
    components.html(icon_html, height=0, width=0)


def _render_fullscreen_overlay():
    """Inject a full-viewport 3D galactic overlay into the parent document."""
    overlay_html = """
    <style>
        #copilot-fullscreen-overlay {
            position: fixed;
            top: 0; left: 0;
            width: 100vw;
            height: 100vh;
            z-index: 999990;
            pointer-events: none;
            animation: overlayFadeIn 0.6s cubic-bezier(0.16, 1, 0.3, 1) forwards;
        }
        #copilot-galaxy-canvas {
            position: absolute;
            top: 0; left: 0;
            width: 100%;
            height: 100%;
        }
        @keyframes overlayFadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }
    </style>
    <div id="copilot-fullscreen-overlay-src">
        <canvas id="copilot-galaxy-canvas-src"></canvas>
    </div>
    <script>
    (function() {
        const parentDoc = window.parent.document;

        // Remove existing overlay
        const ex = parentDoc.getElementById('copilot-fullscreen-overlay');
        if (ex) ex.remove();
        const exStyle = parentDoc.getElementById('copilot-overlay-styles');
        if (exStyle) exStyle.remove();

        // Copy styles
        const style = document.querySelector('style');
        const sc = style.cloneNode(true);
        sc.id = 'copilot-overlay-styles';
        parentDoc.head.appendChild(sc);

        // Create overlay in parent
        const overlay = document.createElement('div');
        overlay.id = 'copilot-fullscreen-overlay';
        const canvas = document.createElement('canvas');
        canvas.id = 'copilot-galaxy-canvas';
        overlay.appendChild(canvas);
        parentDoc.body.appendChild(overlay);

        // Size canvas
        const dpr = window.devicePixelRatio || 1;
        const W = window.innerWidth || parentDoc.documentElement.clientWidth;
        const H = window.innerHeight || parentDoc.documentElement.clientHeight;
        canvas.width = W * dpr;
        canvas.height = H * dpr;
        canvas.style.width = W + 'px';
        canvas.style.height = H + 'px';
        const ctx = canvas.getContext('2d');
        ctx.scale(dpr, dpr);

        // === Deep-space star field ===
        const stars = [];
        for (let i = 0; i < 600; i++) {
            const depth = Math.random();
            stars.push({
                x: Math.random() * W,
                y: Math.random() * H,
                size: (0.3 + depth * 2.2) * (0.6 + Math.random() * 0.4),
                twinkle: Math.random() * Math.PI * 2,
                speed: 0.005 + Math.random() * 0.025,
                hue: ['255,255,255','220,220,255','167,139,250','96,165,250','200,180,255','255,200,220'][Math.floor(Math.random()*6)],
                depth: depth
            });
        }

        // === Spiral galaxy ===
        const galaxy = [];
        const arms = 4;
        for (let i = 0; i < 350; i++) {
            const arm = i % arms;
            const t = Math.random();
            const dist = t * t * (Math.min(W,H) * 0.38) + 3;
            const twist = dist * 0.01;
            const scatter = (Math.random() - 0.5) * 0.5 * (1 + dist * 0.003);
            const angle = (arm * Math.PI * 2 / arms) + twist + scatter;
            const hues = ['167,139,250','129,140,248','96,165,250','192,132,252','139,92,246'];
            galaxy.push({
                angle: angle,
                dist: dist,
                speed: (0.0003 + Math.random() * 0.0008) * (50 / (dist + 20)),
                size: 0.5 + Math.random() * 2.5 * (1 - t * 0.3),
                hue: hues[Math.floor(Math.random() * hues.length)],
                yOff: (Math.random() - 0.5) * 25 * (1 - dist / (Math.min(W,H) * 0.4)),
                alpha: 0.3 + Math.random() * 0.6
            });
        }

        // === Shooting stars ===
        const shooters = [];
        function maybeShoot() {
            if (shooters.length < 2 && Math.random() < 0.003) {
                shooters.push({
                    x: Math.random() * W,
                    y: Math.random() * H * 0.5,
                    vx: 3 + Math.random() * 5,
                    vy: 1 + Math.random() * 3,
                    life: 1.0,
                    len: 40 + Math.random() * 80
                });
            }
        }

        function draw() {
            ctx.clearRect(0, 0, W, H);

            // Deep space gradient
            const bg = ctx.createRadialGradient(W*0.45, H*0.45, 0, W*0.5, H*0.5, Math.max(W, H) * 0.8);
            bg.addColorStop(0, '#0c0e1a');
            bg.addColorStop(0.3, '#080a14');
            bg.addColorStop(0.7, '#050710');
            bg.addColorStop(1, '#020308');
            ctx.fillStyle = bg;
            ctx.fillRect(0, 0, W, H);

            // Nebula clouds
            const nebulae = [
                { x: W*0.2, y: H*0.3, r: W*0.35, color: '139,92,246' },
                { x: W*0.75, y: H*0.6, r: W*0.3, color: '59,130,246' },
                { x: W*0.5, y: H*0.15, r: W*0.25, color: '167,139,250' },
                { x: W*0.85, y: H*0.2, r: W*0.2, color: '192,132,252' },
            ];
            nebulae.forEach(n => {
                const g = ctx.createRadialGradient(n.x, n.y, 0, n.x, n.y, n.r);
                g.addColorStop(0, 'rgba('+n.color+',0.06)');
                g.addColorStop(0.5, 'rgba('+n.color+',0.025)');
                g.addColorStop(1, 'transparent');
                ctx.fillStyle = g;
                ctx.fillRect(0, 0, W, H);
            });

            // Stars
            stars.forEach(s => {
                s.twinkle += s.speed;
                const alpha = 0.2 + s.depth * 0.5 + Math.sin(s.twinkle) * 0.25;
                ctx.beginPath();
                ctx.arc(s.x, s.y, s.size, 0, Math.PI * 2);
                ctx.fillStyle = 'rgba('+s.hue+','+alpha+')';
                ctx.fill();
                if (s.size > 1.8) {
                    const g = ctx.createRadialGradient(s.x, s.y, 0, s.x, s.y, s.size * 4);
                    g.addColorStop(0, 'rgba('+s.hue+',0.1)');
                    g.addColorStop(1, 'transparent');
                    ctx.fillStyle = g;
                    ctx.beginPath();
                    ctx.arc(s.x, s.y, s.size * 4, 0, Math.PI * 2);
                    ctx.fill();
                }
            });

            // Galaxy
            const cx = W * 0.5, cy = H * 0.48;
            const time = Date.now() * 0.00003;
            ctx.globalCompositeOperation = 'screen';

            // Core glow
            const coreGlow = ctx.createRadialGradient(cx, cy, 0, cx, cy, 60);
            coreGlow.addColorStop(0, 'rgba(167,139,250,0.12)');
            coreGlow.addColorStop(0.5, 'rgba(139,92,246,0.04)');
            coreGlow.addColorStop(1, 'transparent');
            ctx.fillStyle = coreGlow;
            ctx.beginPath();
            ctx.arc(cx, cy, 60, 0, Math.PI * 2);
            ctx.fill();

            galaxy.forEach(p => {
                p.angle += p.speed;
                const a = p.angle + time;
                const x = cx + Math.cos(a) * p.dist;
                const y = cy + Math.sin(a) * p.dist * 0.35 + p.yOff;
                if (x < -20 || x > W+20 || y < -20 || y > H+20) return;
                const fade = Math.max(0.05, 1 - p.dist / (Math.min(W,H) * 0.4));
                const al = fade * p.alpha * 0.7;
                ctx.beginPath();
                ctx.arc(x, y, p.size, 0, Math.PI * 2);
                ctx.fillStyle = 'rgba('+p.hue+','+al+')';
                ctx.fill();
                if (p.size > 1.5) {
                    const pg = ctx.createRadialGradient(x, y, 0, x, y, p.size * 3);
                    pg.addColorStop(0, 'rgba('+p.hue+','+(al*0.4)+')');
                    pg.addColorStop(1, 'transparent');
                    ctx.fillStyle = pg;
                    ctx.beginPath();
                    ctx.arc(x, y, p.size * 3, 0, Math.PI * 2);
                    ctx.fill();
                }
            });
            ctx.globalCompositeOperation = 'source-over';

            // Milky Way dust band
            const dust = ctx.createLinearGradient(0, H*0.3, 0, H*0.7);
            dust.addColorStop(0, 'transparent');
            dust.addColorStop(0.2, 'rgba(167,139,250,0.015)');
            dust.addColorStop(0.4, 'rgba(200,180,255,0.025)');
            dust.addColorStop(0.5, 'rgba(220,210,255,0.03)');
            dust.addColorStop(0.6, 'rgba(96,165,250,0.02)');
            dust.addColorStop(0.8, 'rgba(139,92,246,0.015)');
            dust.addColorStop(1, 'transparent');
            ctx.fillStyle = dust;
            ctx.fillRect(0, 0, W, H);

            // Shooting stars
            maybeShoot();
            for (let i = shooters.length - 1; i >= 0; i--) {
                const sh = shooters[i];
                sh.x += sh.vx;
                sh.y += sh.vy;
                sh.life -= 0.015;
                if (sh.life <= 0) { shooters.splice(i, 1); continue; }
                ctx.beginPath();
                ctx.moveTo(sh.x, sh.y);
                ctx.lineTo(sh.x - sh.vx * sh.len * 0.15, sh.y - sh.vy * sh.len * 0.15);
                const sg = ctx.createLinearGradient(sh.x, sh.y,
                    sh.x - sh.vx * sh.len * 0.15, sh.y - sh.vy * sh.len * 0.15);
                sg.addColorStop(0, 'rgba(255,255,255,'+sh.life*0.8+')');
                sg.addColorStop(1, 'transparent');
                ctx.strokeStyle = sg;
                ctx.lineWidth = 1.5;
                ctx.stroke();
            }

            requestAnimationFrame(draw);
        }
        draw();

        // Hide source
        document.getElementById('copilot-fullscreen-overlay-src').style.display = 'none';
    })();
    </script>
    """
    components.html(overlay_html, height=0, width=0)


def _render_chat_interface():
    """Render the full-screen glass-morphism chat UI using native Streamlit widgets."""

    # Glass-morphism container CSS injected globally
    st.markdown("""
    <style>
        /* Full-screen copilot chat styling */
        .copilot-glass-header {
            background: linear-gradient(135deg, rgba(13, 15, 29, 0.85), rgba(30, 20, 60, 0.8));
            border: 1px solid rgba(167, 139, 250, 0.25);
            border-radius: 20px;
            padding: 1.5rem 2rem;
            backdrop-filter: blur(24px);
            -webkit-backdrop-filter: blur(24px);
            box-shadow:
                0 20px 60px rgba(0, 0, 0, 0.4),
                0 0 40px rgba(79, 70, 229, 0.1),
                inset 0 1px 0 rgba(255, 255, 255, 0.06);
            margin-bottom: 1rem;
            position: relative;
            overflow: hidden;
        }
        .copilot-glass-header::before {
            content: '';
            position: absolute;
            top: 0; left: 0; right: 0;
            height: 1px;
            background: linear-gradient(90deg, transparent, rgba(167,139,250,0.4), rgba(96,165,250,0.3), transparent);
        }
        .copilot-title-row {
            display: flex;
            align-items: center;
            gap: 14px;
        }
        .copilot-title-icon {
            width: 44px;
            height: 44px;
            border-radius: 14px;
            background: linear-gradient(135deg, rgba(139,92,246,0.2), rgba(59,130,246,0.15));
            border: 1px solid rgba(167,139,250,0.3);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 22px;
            box-shadow: 0 0 20px rgba(139,92,246,0.2);
        }
        .copilot-title-text {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            font-size: 1.35rem;
            font-weight: 800;
            background: linear-gradient(135deg, #c4b5fd, #93c5fd, #a78bfa);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            letter-spacing: 0.3px;
        }
        .copilot-badge {
            font-size: 0.7rem;
            color: rgba(167, 139, 250, 0.8);
            background: rgba(167, 139, 250, 0.1);
            padding: 3px 10px;
            border-radius: 12px;
            border: 1px solid rgba(167, 139, 250, 0.2);
            font-weight: 600;
            letter-spacing: 0.5px;
            text-transform: uppercase;
        }
        .copilot-subtitle {
            color: rgba(200, 200, 220, 0.5);
            font-size: 0.8rem;
            margin-top: 8px;
            font-weight: 400;
        }
        /* Chat message container glass effect */
        [data-testid="stChatMessage"] {
            background: rgba(15, 17, 30, 0.5) !important;
            backdrop-filter: blur(12px) !important;
            -webkit-backdrop-filter: blur(12px) !important;
            border: 1px solid rgba(167, 139, 250, 0.1) !important;
            border-radius: 14px !important;
            margin-bottom: 8px !important;
        }
    </style>
    """, unsafe_allow_html=True)

    # Header
    st.markdown("""
    <div class="copilot-glass-header">
        <div class="copilot-title-row">
            <div class="copilot-title-icon">🤖</div>
            <span class="copilot-title-text">Marketing Copilot</span>
            <span class="copilot-badge">AI-Powered</span>
        </div>
        <div class="copilot-subtitle">
            Ask anything about your campaigns, ads, or marketing strategy
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Chat history
    for msg in st.session_state["copilot_messages"]:
        role = msg["role"]
        with st.chat_message(role, avatar="🧑‍💼" if role == "user" else "🤖"):
            st.markdown(msg["content"])

    # File upload
    with st.expander("📎 Upload a file for analysis", expanded=False):
        uploaded = st.file_uploader(
            "Upload PDF, CSV, Excel, Word, or text file",
            type=["pdf", "csv", "xlsx", "xls", "docx", "txt", "md", "json", "png", "jpg", "jpeg"],
            key="copilot_file_upload",
        )
        if uploaded:
            with st.spinner("Extracting file content..."):
                content = extract_file_content(uploaded)
                st.session_state["copilot_file_context"] = content
                st.success(f"File '{uploaded.name}' loaded into context")

    # Chat input
    user_input = st.chat_input("Ask the Marketing Copilot anything...", key="copilot_chat_input")

    if user_input:
        st.session_state["copilot_messages"].append({"role": "user", "content": user_input})
        report_context = st.session_state.get("sim_results")
        history = st.session_state["copilot_messages"][-10:]

        with st.spinner("Thinking..."):
            response = get_copilot_response(
                user_message=user_input,
                chat_history=history[:-1],
                report_context=report_context,
                file_context=st.session_state.get("copilot_file_context", ""),
            )

        if response["status"] == "success":
            content = response["content"]
            if response.get("fallback"):
                content = "*[Offline mode — configure DeepSeek API for full responses]*\n\n" + content
            st.session_state["copilot_messages"].append({"role": "assistant", "content": content})
        else:
            st.session_state["copilot_messages"].append({
                "role": "assistant",
                "content": f"Error: {response.get('message', 'Unknown error')}"
            })
        st.rerun()

    # Action buttons
    c1, c2, c3 = st.columns([1, 1, 4])
    with c1:
        if st.button("Close Copilot", key="copilot_close", type="primary"):
            _cleanup_overlay()
            st.session_state["copilot_visible"] = False
            st.rerun()
    with c2:
        if st.button("Clear Chat", key="copilot_clear"):
            st.session_state["copilot_messages"] = []
            st.session_state["copilot_file_context"] = ""
            st.rerun()


def _cleanup_overlay():
    """Inject a script to remove the full-screen overlay from the parent document."""
    cleanup_html = """
    <script>
    (function() {
        const parentDoc = window.parent.document;
        const overlay = parentDoc.getElementById('copilot-fullscreen-overlay');
        if (overlay) {
            overlay.style.animation = 'overlayFadeOut 0.3s ease forwards';
            setTimeout(function() { overlay.remove(); }, 300);
        }
        const style = parentDoc.getElementById('copilot-overlay-styles');
        if (style) {
            const fadeOut = document.createElement('style');
            fadeOut.textContent = '@keyframes overlayFadeOut { from { opacity: 1; } to { opacity: 0; } }';
            parentDoc.head.appendChild(fadeOut);
            setTimeout(function() { if (style) style.remove(); fadeOut.remove(); }, 350);
        }
    })();
    </script>
    """
    components.html(cleanup_html, height=0, width=0)


def render_copilot_toggle():
    """Render a sidebar toggle for the copilot."""
    _init_copilot_state()
    label = "Close Copilot" if st.session_state["copilot_visible"] else "Marketing Copilot"
    icon = "✖" if st.session_state["copilot_visible"] else "🤖"
    if st.sidebar.button(f"{icon} {label}", use_container_width=True, key="copilot_toggle_btn"):
        if st.session_state["copilot_visible"]:
            _cleanup_overlay()
        st.session_state["copilot_visible"] = not st.session_state["copilot_visible"]
        st.rerun()
    if st.session_state["copilot_visible"]:
        st.sidebar.caption("Copilot is open — scroll down to chat")
