"""
AI Marketing Copilot – Streamlit UI.
Renders a floating chat button (bottom-right) that expands into a full
chat window powered by src.ai.copilot.chat().
"""
import streamlit as st
from typing import Optional


# ── Floating Button + Panel CSS ─────────────────────────────────────────────

_COPILOT_CSS = """
<style>
/* ── Hide the hidden sentinel toggle button ───────────────────────────────── */
button[data-testid="baseButton-secondary"]:has(p:empty),
div:has(> button > p:empty) { display: none !important; }

/* Fallback: hide any button whose visible text is the sentinel */
button p:empty { display: none !important; }

/* ── Floating Copilot Button ──────────────────────────────────────────────── */
#copilot-fab {
    position: fixed;
    bottom: 28px;
    right: 28px;
    width: 56px;
    height: 56px;
    border-radius: 50%;
    background: linear-gradient(135deg, #4F46E5 0%, #7C3AED 100%);
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    z-index: 9999;
    box-shadow: 0 4px 24px rgba(79, 70, 229, 0.6), 0 0 0 0 rgba(79, 70, 229, 0.4);
    animation: copilot-pulse 2.5s infinite;
    transition: transform 0.2s ease;
    font-size: 1.5rem;
    user-select: none;
}
#copilot-fab:hover {
    transform: scale(1.1);
}
@keyframes copilot-pulse {
    0%   { box-shadow: 0 4px 24px rgba(79,70,229,0.6), 0 0 0 0   rgba(79,70,229,0.4); }
    70%  { box-shadow: 0 4px 24px rgba(79,70,229,0.6), 0 0 0 14px rgba(79,70,229,0.0); }
    100% { box-shadow: 0 4px 24px rgba(79,70,229,0.6), 0 0 0 0   rgba(79,70,229,0.0); }
}

/* ── Copilot Panel ────────────────────────────────────────────────────────── */
.copilot-panel-header {
    background: linear-gradient(135deg, #4F46E5 0%, #7C3AED 100%);
    padding: 14px 18px;
    border-radius: 16px 16px 0 0;
    display: flex;
    align-items: center;
    gap: 10px;
    font-size: 1rem;
    font-weight: 700;
    color: #fff;
    margin: -1rem -1rem 1rem -1rem;
}

.copilot-msg-user {
    background: rgba(79, 70, 229, 0.25);
    border: 1px solid rgba(99, 102, 241, 0.4);
    border-radius: 12px 12px 4px 12px;
    padding: 10px 14px;
    margin: 6px 0 6px 24px;
    font-size: 0.9rem;
    color: #E0E7FF;
}
.copilot-msg-assistant {
    background: rgba(26, 29, 41, 0.7);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 12px 12px 12px 4px;
    padding: 10px 14px;
    margin: 6px 24px 6px 0;
    font-size: 0.9rem;
    color: #D1D5DB;
    backdrop-filter: blur(8px);
}
</style>
"""


def _fab_html() -> str:
    """Return the floating action button HTML (injected once via st.markdown)."""
    return """
<div id="copilot-fab" title="AI Marketing Copilot">🤖</div>
"""


# ── Session-state keys ───────────────────────────────────────────────────────
_KEY_OPEN = "copilot_open"
_KEY_MSGS = "copilot_messages"


def _init_state():
    if _KEY_OPEN not in st.session_state:
        st.session_state[_KEY_OPEN] = False
    if _KEY_MSGS not in st.session_state:
        st.session_state[_KEY_MSGS] = []


# ── Public API ───────────────────────────────────────────────────────────────

def render_copilot_fab():
    """
    Inject the floating 🤖 button into the page.
    Clicking it triggers a Streamlit button that opens the chat panel.
    Call this ONCE per page, after the main content.
    """
    _init_state()

    # Inject CSS + FAB HTML (zero height so it doesn't take space)
    st.markdown(_COPILOT_CSS + _fab_html(), unsafe_allow_html=True)

    # Invisible Streamlit button that is triggered by JS click on the FAB
    # We rely on the sidebar-toggle pattern: a small button below the FAB HTML.
    # The JS snippet wires the FAB click to trigger this hidden button.
    fab_js = """
<script>
(function() {
    function wireButton() {
        var fab = window.parent.document.getElementById('copilot-fab');
        if (!fab) { setTimeout(wireButton, 500); return; }
        fab.addEventListener('click', function() {
            // Find the hidden streamlit button by its key
            var btns = window.parent.document.querySelectorAll('button[data-testid="baseButton-secondary"]');
            btns.forEach(function(b) {
                if (b.innerText.trim() === '__copilot_toggle__') { b.click(); }
            });
        });
    }
    wireButton();
})();
</script>
"""
    st.markdown(fab_js, unsafe_allow_html=True)

    # Hidden toggle button (label is the sentinel string matched by JS above)
    if st.button("__copilot_toggle__", key="copilot_toggle_btn",
                 help="Toggle AI Copilot", type="secondary"):
        st.session_state[_KEY_OPEN] = not st.session_state[_KEY_OPEN]
        st.rerun()


def render_copilot_panel(sim_context: Optional[str] = None):
    """
    Render the AI Copilot chat panel inline (shown when the FAB is clicked).

    Args:
        sim_context: Optional string containing the latest simulation results
                     to inject as context for the AI.
    """
    _init_state()

    if not st.session_state[_KEY_OPEN]:
        return

    with st.container():
        # Panel header
        st.markdown("""
        <div class="copilot-panel-header">
            🤖&nbsp; AI Marketing Copilot
        </div>
        """, unsafe_allow_html=True)

        # --- Conversation history ---
        msgs = st.session_state[_KEY_MSGS]
        for m in msgs:
            css_cls = "copilot-msg-user" if m["role"] == "user" else "copilot-msg-assistant"
            st.markdown(
                f'<div class="{css_cls}">{m["content"]}</div>',
                unsafe_allow_html=True,
            )

        # --- Context indicator ---
        if sim_context:
            st.caption("📊 Simulation context loaded – ask me about your results!")

        # --- Input row ---
        col_inp, col_send, col_clear = st.columns([6, 1, 1])
        with col_inp:
            user_input = st.text_input(
                "Ask the copilot…",
                key="copilot_input",
                label_visibility="collapsed",
                placeholder="E.g. How do I improve my CTR on TikTok?",
            )
        with col_send:
            send = st.button("➤", key="copilot_send", help="Send")
        with col_clear:
            if st.button("🗑", key="copilot_clear", help="Clear chat"):
                st.session_state[_KEY_MSGS] = []
                st.rerun()

        # --- File upload for extra context ---
        with st.expander("📎 Upload ad creative / brief for context", expanded=False):
            uploaded = st.file_uploader(
                "Upload a text file (.txt, .md, .csv)",
                type=["txt", "md", "csv"],
                key="copilot_upload",
            )
            file_context = ""
            if uploaded:
                try:
                    file_context = uploaded.read().decode("utf-8", errors="replace")[:3000]
                    st.success(f"✅ File loaded: {uploaded.name} ({len(file_context)} chars)")
                except Exception as e:
                    st.error(f"Could not read file: {e}")

        # --- Send logic ---
        if send and user_input.strip():
            msgs.append({"role": "user", "content": user_input.strip()})

            combined_context = ""
            if sim_context:
                combined_context += sim_context + "\n"
            if file_context:
                combined_context += f"\n--- Uploaded File ---\n{file_context}"

            with st.spinner("Thinking…"):
                from src.ai.copilot import chat
                reply = chat(msgs[-10:], extra_context=combined_context or None)

            msgs.append({"role": "assistant", "content": reply})
            st.session_state[_KEY_MSGS] = msgs
            st.rerun()
