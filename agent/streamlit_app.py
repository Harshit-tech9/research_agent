import streamlit as st
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.orchestrator import Orchestrator
from tools.registry import tool_info

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Agent Dashboard",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  [data-testid="stAppViewContainer"] { background: #0d1117; }
  [data-testid="stSidebar"] {
      background: #161b22;
      border-right: 1px solid #30363d;
  }
  /* Hero */
  .hero {
      background: linear-gradient(135deg, #1a1f35 0%, #0d1117 100%);
      border: 1px solid #30363d;
      border-radius: 16px;
      padding: 32px 40px;
      margin-bottom: 24px;
      text-align: center;
  }
  .hero h1 {
      font-size: 2.4rem; font-weight: 700;
      background: linear-gradient(90deg, #58a6ff, #a371f7);
      -webkit-background-clip: text; -webkit-text-fill-color: transparent;
      margin: 0 0 8px 0;
  }
  .hero p { color: #8b949e; font-size: 1rem; margin: 0; }

  /* Step cards */
  .step-card {
      border-radius: 10px; padding: 14px 18px;
      margin: 10px 0; border-left: 4px solid;
  }
  .card-thought     { background: #12192b; border-color: #58a6ff; }
  .card-action      { background: #1c1500; border-color: #d29922; }
  .card-observation { background: #0d1f0d; border-color: #3fb950; }
  .card-plan        { background: #12192b; border-left: 4px solid #a371f7; }
  .card-final {
      background: linear-gradient(135deg, #1a0d2e, #0d1a2e);
      border: 2px solid #a371f7; border-radius: 12px;
      padding: 20px 24px; margin: 16px 0;
  }
  .card-label {
      font-size: 0.7rem; font-weight: 700;
      letter-spacing: 0.12em; text-transform: uppercase; margin-bottom: 6px;
  }
  .label-thought { color: #58a6ff; }
  .label-action  { color: #d29922; }
  .label-obs     { color: #3fb950; }
  .label-final   { color: #a371f7; }
  .label-plan    { color: #a371f7; }
  .card-content  { color: #e6edf3; font-size: 0.9rem; line-height: 1.6; white-space: pre-wrap; }

  /* Tool badge */
  .tool-badge {
      display: inline-block;
      background: rgba(210,153,34,0.12); border: 1px solid #d29922;
      color: #d29922; border-radius: 20px;
      padding: 2px 12px; font-size: 0.75rem; font-weight: 600; margin-right: 8px;
  }
  .tool-input {
      color: #8b949e; font-family: monospace;
      font-size: 0.85rem; margin-top: 6px; word-break: break-all;
  }

  /* Agent badge */
  .agent-badge {
      display: inline-block;
      background: rgba(88,166,255,0.12); border: 1px solid #30363d;
      color: #8b949e; border-radius: 20px;
      padding: 1px 10px; font-size: 0.7rem; margin-left: 8px;
  }

  /* Routing banner */
  .routing-banner {
      background: #1a1f35; border: 1px solid #30363d;
      border-radius: 8px; padding: 8px 16px; margin: 8px 0;
      color: #8b949e; font-size: 0.8rem;
  }
  .routing-banner b { color: #58a6ff; }

  /* Sidebar elements */
  .tool-item {
      background: #21262d; border: 1px solid #30363d;
      border-radius: 8px; padding: 10px 14px; margin: 6px 0;
  }
  .tool-name { color: #58a6ff; font-weight: 600; font-size: 0.85rem; }
  .tool-desc { color: #8b949e; font-size: 0.75rem; margin-top: 3px; }

  /* Memory stat cards */
  .mem-stat {
      background: #21262d; border: 1px solid #30363d;
      border-radius: 8px; padding: 10px 14px; margin: 4px 0;
      display: flex; justify-content: space-between; align-items: center;
  }
  .mem-label { color: #8b949e; font-size: 0.8rem; }
  .mem-value { color: #58a6ff; font-weight: 700; font-size: 1rem; }

  /* History */
  .history-item {
      background: #161b22; border: 1px solid #30363d;
      border-radius: 8px; padding: 12px 16px; margin: 6px 0;
  }
  .history-query { color: #e6edf3; font-size: 0.85rem; font-weight: 500; }
  .history-meta  { color: #8b949e; font-size: 0.75rem; margin-top: 4px; }

  .section-divider { border: none; border-top: 1px solid #30363d; margin: 20px 0; }

  .stTextArea textarea {
      background: #161b22 !important; color: #e6edf3 !important;
      border: 1px solid #30363d !important; border-radius: 8px !important;
      font-size: 0.95rem !important;
  }
  .stButton > button { border-radius: 8px !important; font-weight: 600 !important; }
  div[data-testid="stMarkdownContainer"] p { color: #e6edf3; }
</style>
""", unsafe_allow_html=True)


# ── Singleton orchestrator (persists memory across reruns) ────────────────────
@st.cache_resource
def get_orchestrator() -> Orchestrator:
    return Orchestrator()


# ── Render helpers ────────────────────────────────────────────────────────────
def _agent_badge(agent_name: str) -> str:
    return f'<span class="agent-badge">{agent_name}</span>'


def render_plan(plan: str) -> None:
    lines = [l.strip() for l in plan.strip().splitlines() if l.strip()]
    items = "".join(f"<li style='margin:4px 0;color:#e6edf3'>{l}</li>" for l in lines)
    st.markdown(f"""
    <div class="step-card card-plan">
        <div class="card-label label-plan">📋 Execution Plan</div>
        <ol style="margin:8px 0 0 16px;padding:0">{items}</ol>
    </div>""", unsafe_allow_html=True)


def render_routing(agent_name: str) -> None:
    labels = {
        "research_agent": "🔍 Research Agent — web search & Wikipedia",
        "math_agent":     "🧮 Math Agent — calculator specialist",
        "general_agent":  "🤖 General Agent — all tools available",
    }
    st.markdown(f"""
    <div class="routing-banner">
        Routing to &nbsp;<b>{labels.get(agent_name, agent_name)}</b>
    </div>""", unsafe_allow_html=True)


def render_thought(content: str, step: int, agent: str) -> None:
    st.markdown(f"""
    <div class="step-card card-thought">
        <div class="card-label label-thought">
            🧠 Thought &nbsp;·&nbsp; Step {step}{_agent_badge(agent)}
        </div>
        <div class="card-content">{content}</div>
    </div>""", unsafe_allow_html=True)


def render_action(tool: str, tool_input: str, step: int, agent: str) -> None:
    icon = {"tavily_search": "🔍", "wikipedia_search": "📖", "calculator": "🧮"}.get(tool, "⚙️")
    st.markdown(f"""
    <div class="step-card card-action">
        <div class="card-label label-action">
            ⚡ Action &nbsp;·&nbsp; Step {step}{_agent_badge(agent)}
        </div>
        <div class="card-content">
            <span class="tool-badge">{icon} {tool}</span>
            <div class="tool-input">{tool_input}</div>
        </div>
    </div>""", unsafe_allow_html=True)


def render_observation(content: str, step: int, agent: str) -> None:
    preview = content[:700] + ("…" if len(content) > 700 else "")
    st.markdown(f"""
    <div class="step-card card-observation">
        <div class="card-label label-obs">
            📥 Observation &nbsp;·&nbsp; Step {step}{_agent_badge(agent)}
        </div>
        <div class="card-content">{preview}</div>
    </div>""", unsafe_allow_html=True)


def render_final_answer(content: str) -> None:
    st.markdown(f"""
    <div class="card-final">
        <div class="card-label label-final" style="font-size:.85rem">✅ Final Answer</div>
        <div class="card-content" style="font-size:1rem;margin-top:8px">{content}</div>
    </div>""", unsafe_allow_html=True)


def replay_record(record: dict) -> None:
    render_plan(record["plan"])
    for ev in record["steps"]:
        t = ev["type"]
        ag = ev.get("agent", "")
        if t == "routing":
            render_routing(ev["agent"])
        elif t == "thought":
            render_thought(ev["content"], ev["step"], ag)
        elif t == "action":
            render_action(ev["tool"], ev["input"], ev["step"], ag)
        elif t == "observation":
            render_observation(ev["content"], ev["step"], ag)
        elif t == "final_answer":
            render_final_answer(ev["content"])


# ── Session state ─────────────────────────────────────────────────────────────
if "history" not in st.session_state:
    st.session_state.history = []
if "running" not in st.session_state:
    st.session_state.running = False
if "replay_idx" not in st.session_state:
    st.session_state.replay_idx = None

orc = get_orchestrator()
stats = orc.memory_stats()

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🤖 AI Agent")
    st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)

    st.markdown("**Model**")
    st.markdown("""
    <div class="tool-item">
        <div class="tool-name">LLaMA 3.3 70B Versatile</div>
        <div class="tool-desc">via Groq Cloud · Structured tool calling · Retry on failure</div>
    </div>""", unsafe_allow_html=True)

    st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)
    st.markdown("**Tools**")
    for t in tool_info():
        st.markdown(f"""
        <div class="tool-item">
            <div class="tool-name">{t['name']}</div>
            <div class="tool-desc">{t['description'][:80]}…</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)
    st.markdown("**Memory**")
    lt_status = "✅ Active" if stats["long_term_available"] else "⚠️ Offline"
    st.markdown(f"""
    <div class="mem-stat">
        <span class="mem-label">Long-term (ChromaDB)</span>
        <span class="mem-value">{stats['long_term_items']}</span>
    </div>
    <div class="mem-stat">
        <span class="mem-label">Episodes (SQLite)</span>
        <span class="mem-value">{stats['episodes']}</span>
    </div>
    <div class="mem-stat">
        <span class="mem-label">Vector store</span>
        <span class="mem-value" style="font-size:.75rem">{lt_status}</span>
    </div>""", unsafe_allow_html=True)

    st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)
    st.markdown("**Agents**")
    st.markdown("""
    <div style="color:#8b949e;font-size:0.8rem;line-height:1.9">
    🔍 <b style="color:#58a6ff">Research</b> — web + Wikipedia<br>
    🧮 <b style="color:#d29922">Math</b> — calculator only<br>
    🤖 <b style="color:#3fb950">General</b> — all tools (default)
    </div>""", unsafe_allow_html=True)

    if st.session_state.history:
        st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)
        st.markdown(f"**Session** · {len(st.session_state.history)} quer{'y' if len(st.session_state.history)==1 else 'ies'}")
        if st.button("Clear Session History", use_container_width=True):
            st.session_state.history = []
            st.session_state.replay_idx = None
            st.rerun()


# ── Hero ──────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
    <h1>🤖 AI Agent Dashboard</h1>
    <p>Multi-agent · Structured tool calling · Long-term memory · Episodic history</p>
</div>""", unsafe_allow_html=True)


# ── Query input ───────────────────────────────────────────────────────────────
col_in, col_btn = st.columns([5, 1])
with col_in:
    query = st.text_area(
        "query",
        placeholder="Ask anything — e.g. 'What is the GDP of France divided by its population?'",
        height=80,
        label_visibility="collapsed",
    )
with col_btn:
    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
    run_btn = st.button(
        "Run Agent",
        type="primary",
        use_container_width=True,
        disabled=st.session_state.running,
    )

st.markdown("""
<div style="color:#8b949e;font-size:.75rem;margin:-6px 0 18px 0">
  Try: &nbsp;
  <code style="background:#21262d;padding:2px 8px;border-radius:4px;color:#58a6ff">What is the current price of Bitcoin?</code>&nbsp;
  <code style="background:#21262d;padding:2px 8px;border-radius:4px;color:#58a6ff">Calculate factorial(12) + 2**20</code>&nbsp;
  <code style="background:#21262d;padding:2px 8px;border-radius:4px;color:#58a6ff">Who invented the telephone?</code>
</div>""", unsafe_allow_html=True)


# ── Run ───────────────────────────────────────────────────────────────────────
if run_btn and query.strip():
    st.session_state.running = True
    st.session_state.replay_idx = None

    record = {"query": query, "plan": "", "steps": [], "final_answer": None}
    final_answer = None
    status = st.empty()

    for event in orc.run_stream(query):
        etype = event["type"]
        record["steps"].append(event)

        if etype == "plan":
            record["plan"] = event["content"]
            render_plan(event["content"])
            st.markdown(
                "<p style='color:#8b949e;font-size:.8rem;font-weight:600;"
                "text-transform:uppercase;letter-spacing:.1em;margin:16px 0 4px'>Agent Trace</p>",
                unsafe_allow_html=True,
            )

        elif etype == "routing":
            render_routing(event["agent"])

        elif etype == "thought":
            status.markdown(
                f"<p style='color:#8b949e;font-size:.8rem'>Step {event['step']} — reasoning…</p>",
                unsafe_allow_html=True,
            )
            if event["content"]:
                render_thought(event["content"], event["step"], event.get("agent", ""))

        elif etype == "action":
            render_action(event["tool"], event["input"], event["step"], event.get("agent", ""))

        elif etype == "observation":
            render_observation(event["content"], event["step"], event.get("agent", ""))

        elif etype == "final_answer":
            status.empty()
            final_answer = event["content"]
            record["final_answer"] = final_answer

        elif etype == "max_steps_reached":
            status.warning("Agent reached the step limit without producing a final answer.")

        elif etype == "error":
            st.error(f"Step {event.get('step','?')}: {event['content']}")

    if final_answer:
        st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)
        render_final_answer(final_answer)
        st.code(final_answer, language=None)

    st.session_state.history.append(record)
    st.session_state.running = False


# ── Session history ───────────────────────────────────────────────────────────
if st.session_state.history:
    st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)
    with st.expander(f"Session History  ({len(st.session_state.history)} queries)"):
        for idx, rec in enumerate(reversed(st.session_state.history)):
            real_idx = len(st.session_state.history) - 1 - idx
            n_steps = sum(1 for s in rec["steps"] if s["type"] == "thought")
            answered = "✅ Answered" if rec["final_answer"] else "⚠️ No answer"
            agent_used = next(
                (s["agent"] for s in rec["steps"] if s["type"] == "routing"), "—"
            )
            c1, c2 = st.columns([5, 1])
            with c1:
                st.markdown(f"""
                <div class="history-item">
                    <div class="history-query">Q: {rec['query']}</div>
                    <div class="history-meta">{n_steps} step(s) · {answered} · {agent_used}</div>
                </div>""", unsafe_allow_html=True)
            with c2:
                if st.button("View", key=f"view_{real_idx}"):
                    st.session_state.replay_idx = real_idx
                    st.rerun()


# ── Episodic memory viewer ─────────────────────────────────────────────────────
recent = orc.recent_episodes(6)
if recent:
    st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)
    with st.expander(f"Episodic Memory  ({stats['episodes']} total sessions)"):
        for ep in recent:
            tools_str = ", ".join(ep["tools"]) if ep["tools"] else "none"
            st.markdown(f"""
            <div class="history-item">
                <div class="history-query">Q: {ep['query']}</div>
                <div class="history-meta">
                    {ep['timestamp']} · {ep['agent']} · tools: {tools_str}
                </div>
                { f"<div style='color:#8b949e;font-size:.8rem;margin-top:6px'>{ep['answer'][:200]}…</div>" if ep['answer'] else "" }
            </div>""", unsafe_allow_html=True)


# ── Replay ────────────────────────────────────────────────────────────────────
if st.session_state.replay_idx is not None:
    rec = st.session_state.history[st.session_state.replay_idx]
    st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)
    st.markdown(f"**Replaying:** {rec['query']}")
    replay_record(rec)
    if rec["final_answer"]:
        st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)
        render_final_answer(rec["final_answer"])
    if st.button("Close Replay"):
        st.session_state.replay_idx = None
        st.rerun()
