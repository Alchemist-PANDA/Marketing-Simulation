"""
AI Marketing Copilot — immersive 3D galactic chat experience.

IMPORTANT DESIGN NOTE:
Streamlit Cloud serves `components.html` inside a *sandboxed, cross-origin*
iframe. Any JavaScript that reaches into `window.parent.document` is blocked by
the browser and silently fails — which is why the previous parent-DOM injection
approach never rendered on the deployed app. This version keeps every canvas /
animation fully *self-contained* inside its own iframe, and uses native
Streamlit widgets (styled with in-document CSS via st.markdown, which is NOT
sandboxed) for the chat itself. That combination renders reliably everywhere.
"""
import streamlit as st
import streamlit.components.v1 as components
from src.ai.copilot import (
    add_api_key,
    extract_file_content,
    get_copilot_response,
    has_api_key,
)


def _init_copilot_state():
    """Initialize copilot session state keys."""
    st.session_state.setdefault("copilot_messages", [])
    st.session_state.setdefault("copilot_visible", False)
    st.session_state.setdefault("copilot_file_context", "")


def render_copilot():
    """Render the copilot when it is open. Safe to call on every page."""
    _init_copilot_state()
    if st.session_state["copilot_visible"]:
        _render_galaxy_header()
        _render_chat_interface()


def render_copilot_toggle():
    """Sidebar toggle button — the reliable, native way to open/close the copilot."""
    _init_copilot_state()
    is_open = st.session_state["copilot_visible"]
    label = "✖  Close Copilot" if is_open else "🤖  Marketing Copilot"
    if st.sidebar.button(label, use_container_width=True, key="copilot_toggle_btn",
                         type="primary" if not is_open else "secondary"):
        st.session_state["copilot_visible"] = not is_open
        st.rerun()
    if st.session_state["copilot_visible"]:
        st.sidebar.caption("Copilot open — scroll the main panel to chat.")


def _render_galaxy_header():
    """Self-contained immersive 3D galaxy banner with the title overlaid.

    Everything (canvas, animation, title) lives inside this single iframe, so it
    renders correctly on Streamlit Cloud without touching the parent document.
    """
    galaxy_html = """
    <div id="galaxy-wrap">
        <canvas id="galaxy"></canvas>
        <div id="galaxy-overlay">
            <div id="galaxy-title-row">
                <span id="galaxy-emoji">🤖</span>
                <span id="galaxy-title">Marketing Copilot</span>
                <span id="galaxy-badge">AI-POWERED</span>
            </div>
            <div id="galaxy-sub">Ask anything about your campaigns, ads, or marketing strategy</div>
        </div>
    </div>
    <style>
        html, body { margin: 0; padding: 0; overflow: hidden; }
        #galaxy-wrap {
            position: relative;
            width: 100%;
            height: 240px;
            border-radius: 20px;
            overflow: hidden;
            box-shadow: 0 20px 60px rgba(0,0,0,0.45), 0 0 40px rgba(79,70,229,0.15);
            border: 1px solid rgba(167,139,250,0.25);
        }
        #galaxy { position: absolute; top: 0; left: 0; width: 100%; height: 100%; display: block; }
        #galaxy-overlay {
            position: absolute;
            left: 0; bottom: 0;
            width: 100%;
            padding: 22px 28px;
            box-sizing: border-box;
            background: linear-gradient(to top, rgba(6,8,18,0.85), rgba(6,8,18,0.0));
        }
        #galaxy-title-row { display: flex; align-items: center; gap: 14px; flex-wrap: wrap; }
        #galaxy-emoji {
            font-size: 26px;
            filter: drop-shadow(0 0 12px rgba(167,139,250,0.7));
            animation: floaty 3.5s ease-in-out infinite;
        }
        #galaxy-title {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            font-size: 1.6rem;
            font-weight: 800;
            letter-spacing: 0.3px;
            background: linear-gradient(135deg, #c4b5fd, #93c5fd, #a78bfa);
            -webkit-background-clip: text; background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        #galaxy-badge {
            font-size: 0.62rem; font-weight: 700; letter-spacing: 0.8px;
            color: #c4b5fd;
            background: rgba(167,139,250,0.12);
            border: 1px solid rgba(167,139,250,0.3);
            padding: 3px 10px; border-radius: 20px;
        }
        #galaxy-sub {
            margin-top: 8px;
            color: rgba(210,210,230,0.65);
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            font-size: 0.85rem;
        }
        @keyframes floaty { 0%,100% { transform: translateY(0); } 50% { transform: translateY(-5px); } }
    </style>
    <script>
    (function() {
        const canvas = document.getElementById('galaxy');
        const ctx = canvas.getContext('2d');
        const wrap = document.getElementById('galaxy-wrap');

        function size() {
            const dpr = window.devicePixelRatio || 1;
            const w = wrap.clientWidth, h = wrap.clientHeight;
            canvas.width = w * dpr; canvas.height = h * dpr;
            canvas.style.width = w + 'px'; canvas.style.height = h + 'px';
            ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
            return { w, h };
        }
        let { w: W, h: H } = size();
        window.addEventListener('resize', () => { const s = size(); W = s.w; H = s.h; build(); });

        let stars = [], galaxy = [], shooters = [];
        function build() {
            stars = [];
            for (let i = 0; i < 260; i++) {
                const d = Math.random();
                stars.push({
                    x: Math.random()*W, y: Math.random()*H,
                    size: (0.3 + d*1.8)*(0.6+Math.random()*0.4),
                    tw: Math.random()*Math.PI*2, sp: 0.01+Math.random()*0.03,
                    hue: ['255,255,255','210,210,255','167,139,250','96,165,250','200,180,255'][Math.floor(Math.random()*5)],
                    depth: d
                });
            }
            galaxy = [];
            const arms = 4;
            for (let i = 0; i < 220; i++) {
                const arm = i % arms, t = Math.random();
                const dist = t*t*(Math.min(W,H)*0.7)+3;
                const angle = (arm*Math.PI*2/arms) + dist*0.012 + (Math.random()-0.5)*0.5;
                galaxy.push({
                    angle, dist,
                    speed: (0.0004+Math.random()*0.001)*(50/(dist+20)),
                    size: 0.5+Math.random()*2.2*(1-t*0.3),
                    hue: ['167,139,250','129,140,248','96,165,250','192,132,252','139,92,246'][Math.floor(Math.random()*5)],
                    yOff: (Math.random()-0.5)*18,
                    alpha: 0.3+Math.random()*0.6
                });
            }
        }
        build();

        function maybeShoot() {
            if (shooters.length < 2 && Math.random() < 0.004) {
                shooters.push({ x: Math.random()*W, y: Math.random()*H*0.5,
                    vx: 3+Math.random()*5, vy: 1+Math.random()*2.5, life: 1.0, len: 40+Math.random()*70 });
            }
        }

        function draw() {
            ctx.clearRect(0,0,W,H);
            // deep-space background
            const bg = ctx.createRadialGradient(W*0.5,H*0.45,0,W*0.5,H*0.5,Math.max(W,H)*0.8);
            bg.addColorStop(0,'#0d1024'); bg.addColorStop(0.5,'#080a16'); bg.addColorStop(1,'#04060e');
            ctx.fillStyle = bg; ctx.fillRect(0,0,W,H);
            // nebulae
            [[W*0.25,H*0.4,'139,92,246'],[W*0.75,H*0.55,'59,130,246'],[W*0.55,H*0.2,'167,139,250']].forEach(n => {
                const g = ctx.createRadialGradient(n[0],n[1],0,n[0],n[1],W*0.3);
                g.addColorStop(0,'rgba('+n[2]+',0.07)'); g.addColorStop(1,'transparent');
                ctx.fillStyle = g; ctx.fillRect(0,0,W,H);
            });
            // stars
            stars.forEach(s => {
                s.tw += s.sp;
                const a = 0.2 + s.depth*0.5 + Math.sin(s.tw)*0.25;
                ctx.beginPath(); ctx.arc(s.x,s.y,s.size,0,Math.PI*2);
                ctx.fillStyle = 'rgba('+s.hue+','+a+')'; ctx.fill();
            });
            // galaxy
            const cx = W*0.5, cy = H*0.5, time = Date.now()*0.00004;
            ctx.globalCompositeOperation = 'screen';
            const core = ctx.createRadialGradient(cx,cy,0,cx,cy,50);
            core.addColorStop(0,'rgba(167,139,250,0.14)'); core.addColorStop(1,'transparent');
            ctx.fillStyle = core; ctx.beginPath(); ctx.arc(cx,cy,50,0,Math.PI*2); ctx.fill();
            galaxy.forEach(p => {
                p.angle += p.speed;
                const ang = p.angle + time;
                const x = cx + Math.cos(ang)*p.dist;
                const y = cy + Math.sin(ang)*p.dist*0.4 + p.yOff;
                const fade = Math.max(0.05, 1 - p.dist/(Math.min(W,H)*0.75));
                ctx.beginPath(); ctx.arc(x,y,p.size,0,Math.PI*2);
                ctx.fillStyle = 'rgba('+p.hue+','+(fade*p.alpha*0.75)+')'; ctx.fill();
            });
            ctx.globalCompositeOperation = 'source-over';
            // shooting stars
            maybeShoot();
            for (let i = shooters.length-1; i >= 0; i--) {
                const sh = shooters[i];
                sh.x += sh.vx; sh.y += sh.vy; sh.life -= 0.02;
                if (sh.life <= 0) { shooters.splice(i,1); continue; }
                ctx.beginPath(); ctx.moveTo(sh.x, sh.y);
                ctx.lineTo(sh.x - sh.vx*sh.len*0.12, sh.y - sh.vy*sh.len*0.12);
                const sg = ctx.createLinearGradient(sh.x,sh.y, sh.x-sh.vx*sh.len*0.12, sh.y-sh.vy*sh.len*0.12);
                sg.addColorStop(0,'rgba(255,255,255,'+sh.life*0.8+')'); sg.addColorStop(1,'transparent');
                ctx.strokeStyle = sg; ctx.lineWidth = 1.5; ctx.stroke();
            }
            requestAnimationFrame(draw);
        }
        draw();
    })();
    </script>
    """
    components.html(galaxy_html, height=260)


def _render_brand_profile():
    """Brand intake + correction form (plan Section 3.1 / 3.6).

    The copilot grounds every answer in this profile, so it's surfaced right in
    the panel. Auto-expands until the load-bearing fields are set, then collapses.
    """
    from src.ai import brand_profile as bp

    profile = bp.get_profile()
    configured = bp.is_configured()
    header = ("🏷️ Brand profile" if configured
              else "🏷️ Set up your brand profile (the copilot uses this for every answer)")

    with st.expander(header, expanded=not configured):
        st.caption(
            "The more the copilot knows, the more specific its advice. Business "
            "model and stage do the most calibration work. You can correct any "
            "field anytime — changes are logged."
        )
        with st.form("brand_profile_form"):
            vals = {}
            vals["business_name"] = st.text_input("Business / product name", profile.get("business_name", ""))
            c1, c2 = st.columns(2)
            with c1:
                model_opts = ["", "B2C", "B2B", "Hybrid"]
                cur_model = profile.get("business_model", "")
                vals["business_model"] = st.selectbox(
                    "Business model", model_opts,
                    index=model_opts.index(cur_model) if cur_model in model_opts else 0,
                )
            with c2:
                stage_opts = ["", "Pre-revenue", "Early growth", "Scaling", "Mature"]
                cur_stage = profile.get("business_stage", "")
                vals["business_stage"] = st.selectbox(
                    "Business stage", stage_opts,
                    index=stage_opts.index(cur_stage) if cur_stage in stage_opts else 0,
                )
            vals["monthly_budget"] = st.text_input("Monthly marketing budget", profile.get("monthly_budget", ""))
            vals["brand_voice"] = st.text_input("Brand voice (3–5 adjectives)", profile.get("brand_voice", ""))
            vals["icp"] = st.text_area("Ideal customer profile (ICP)", profile.get("icp", ""), height=70)
            vals["competitors"] = st.text_input("Key competitors", profile.get("competitors", ""))
            vals["active_channels"] = st.text_input("Active channels", profile.get("active_channels", ""))
            vals["seasonality"] = st.text_input("Seasonality / high-low periods", profile.get("seasonality", ""))

            if st.form_submit_button("Save profile", type="primary", use_container_width=True):
                bp.save_profile(vals)
                st.success("Brand profile saved — the copilot will use it from now on.")
                st.rerun()

        log = profile.get("change_log", [])
        if log:
            with st.expander(f"🕓 Change history ({len(log)})"):
                for entry in reversed(log[-10:]):
                    st.caption(f"**{entry['at'][:16].replace('T', ' ')}**")
                    for change in entry["changes"]:
                        st.caption(f"• {change}")


def _render_chat_interface():
    """Native Streamlit chat with glass-morphism styling injected into the main doc."""
    st.markdown("""
    <style>
        [data-testid="stChatMessage"] {
            background: rgba(15, 17, 30, 0.55) !important;
            backdrop-filter: blur(12px);
            border: 1px solid rgba(167, 139, 250, 0.14) !important;
            border-radius: 14px !important;
            margin-bottom: 8px !important;
        }
    </style>
    """, unsafe_allow_html=True)

    _render_brand_profile()

    # Gemini key entry — shown only when no key is configured from any source.
    # This is the fix for "I entered my key but it's still offline": there was
    # previously no in-app place to enter a Gemini key that the copilot reads.
    if not has_api_key():
        with st.expander("🔑 Connect Gemini for full AI responses (no key detected)", expanded=True):
            st.caption(
                "The copilot works in offline mode without a key. To enable full "
                "Gemini answers, paste a free API key from "
                "[Google AI Studio](https://aistudio.google.com/app/apikey). "
                "It's stored only in this browser session."
            )
            kc1, kc2 = st.columns([4, 1])
            with kc1:
                new_key = st.text_input(
                    "Gemini API key", type="password", key="copilot_key_input",
                    placeholder="AIza…", label_visibility="collapsed",
                )
            with kc2:
                if st.button("Save", key="copilot_key_save", use_container_width=True):
                    if add_api_key(new_key):
                        st.success("Key saved — Gemini is now active.")
                        st.rerun()
                    else:
                        st.error("Enter a valid key (or it's already saved).")

    # Chat history
    for msg in st.session_state["copilot_messages"]:
        role = msg["role"]
        with st.chat_message(role, avatar="🧑‍💼" if role == "user" else "🤖"):
            st.markdown(msg["content"])

    # File upload
    with st.expander("📎 Upload a file for analysis (PDF, CSV, Excel, Word, image)"):
        uploaded = st.file_uploader(
            "Attach a file to give the copilot context",
            type=["pdf", "csv", "xlsx", "xls", "docx", "txt", "md", "json", "png", "jpg", "jpeg"],
            key="copilot_file_upload",
            label_visibility="collapsed",
        )
        if uploaded is not None:
            with st.spinner("Extracting file content..."):
                try:
                    content = extract_file_content(uploaded)
                    st.session_state["copilot_file_context"] = content
                    st.success(f"'{uploaded.name}' loaded into context.")
                except Exception as e:
                    st.error(f"Could not read that file: {e}")

    # Chat input
    user_input = st.chat_input("Ask the Marketing Copilot anything...", key="copilot_chat_input")
    if user_input:
        st.session_state["copilot_messages"].append({"role": "user", "content": user_input})
        history = st.session_state["copilot_messages"][-10:]
        report_context = st.session_state.get("sim_results")

        with st.spinner("Thinking..."):
            response = get_copilot_response(
                user_message=user_input,
                chat_history=history[:-1],
                report_context=report_context,
                file_context=st.session_state.get("copilot_file_context", ""),
            )

        if response.get("status") == "success":
            content = response["content"]
            if response.get("fallback"):
                if response.get("fallback_reason") == "api_error":
                    banner = ("*[⚠️ AI is temporarily unavailable (service/network issue). "
                              "Showing a quick rule-based answer — please try again shortly.]*")
                else:
                    banner = ("*[Offline mode — add your Gemini API keys for full AI responses]*")
                content = banner + "\n\n" + content
            st.session_state["copilot_messages"].append({"role": "assistant", "content": content})
        else:
            st.session_state["copilot_messages"].append({
                "role": "assistant",
                "content": f"⚠️ {response.get('message', 'Something went wrong.')}",
            })
        st.rerun()

    # Actions
    c1, c2, _ = st.columns([1, 1, 3])
    with c1:
        if st.button("Close", key="copilot_close", use_container_width=True):
            st.session_state["copilot_visible"] = False
            st.rerun()
    with c2:
        if st.button("Clear chat", key="copilot_clear", use_container_width=True):
            st.session_state["copilot_messages"] = []
            st.session_state["copilot_file_context"] = ""
            st.rerun()
