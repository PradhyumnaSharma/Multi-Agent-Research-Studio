"""
Multi-Agent Research Studio - Streamlit Application
A comprehensive research automation system using LangGraph and multiple AI agents.
"""
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime
from typing import Dict, Any, Optional

# Import our modules
from graph.research_graph import ResearchGraph
from utils.state import create_initial_state, ResearchStatus
from utils.analytics import (
    calculate_research_metrics,
    get_research_timeline,
    get_quality_breakdown,
    prepare_analytics_dataframe,
)
from utils.exporters import export_report
import config as app_config  # renamed to avoid shadowing

# ──────────────────────────────────────────────────────────────────────
# Page configuration
# ──────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Multi-Agent Research Studio",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .main-header {
        font-size: 2.8rem;
        font-weight: bold;
        background: linear-gradient(90deg, #1f77b4, #764ba2);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 1.5rem;
    }
    .status-box {
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .status-researching { background-color: #fff3cd; border-left: 4px solid #ffc107; }
    .status-reviewing   { background-color: #d1ecf1; border-left: 4px solid #17a2b8; }
    .status-awaiting    { background-color: #f8d7da; border-left: 4px solid #dc3545; }
    .status-completed   { background-color: #d4edda; border-left: 4px solid #28a745; }
    .status-writing     { background-color: #cce5ff; border-left: 4px solid #007bff; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ──────────────────────────────────────────────────────────────────────
# Session helpers
# ──────────────────────────────────────────────────────────────────────

def _init_session():
    defaults = {
        "thread_id": f"thread_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "research_graph": None,
        "current_state": None,
        "research_history": [],
        "is_running": False,
        "interrupted": False,
        "export_data": None,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


def _graph_config() -> dict:
    """Return the LangGraph config dict (thread-aware)."""
    return {"configurable": {"thread_id": st.session_state.thread_id}}


# ──────────────────────────────────────────────────────────────────────
# Status / metric helpers
# ──────────────────────────────────────────────────────────────────────

def _status_class(status: str) -> str:
    s = status.lower()
    if "research" in s:
        return "status-researching"
    if "review" in s:
        return "status-reviewing"
    if "await" in s or "approval" in s:
        return "status-awaiting"
    if "writing" in s:
        return "status-writing"
    if "complete" in s:
        return "status-completed"
    return ""


def _display_status(state: Dict[str, Any]):
    status = str(state.get("status", "unknown"))
    st.markdown(
        f"""
        <div class="status-box {_status_class(status)}">
            <h3>Status: {status.upper().replace('_', ' ')}</h3>
            <p>Quality: {state.get('quality_score', 0.0):.2f} &nbsp;|&nbsp;
               Iteration: {state.get('research_iteration', 0)} &nbsp;|&nbsp;
               Sources: {len(state.get('sources', []))} &nbsp;|&nbsp;
               Notes: {len(state.get('research_notes', []))}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _display_metrics(state: Dict[str, Any]):
    m = calculate_research_metrics(state)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Quality Score", f"{m.get('quality_score', 0.0):.2f}")
    c2.metric("Sources", m.get("total_sources", 0))
    c3.metric("Research Notes", m.get("total_notes", 0))
    c4.metric("Duration", f"{m.get('research_duration_seconds', 0):.1f}s")


# ──────────────────────────────────────────────────────────────────────
# Research log / sources / analytics
# ──────────────────────────────────────────────────────────────────────

def _display_log(state: Dict[str, Any]):
    st.subheader("📋 Research Activity Log")
    actions = state.get("agent_actions", [])
    if not actions:
        st.info("No activity yet.")
        return
    for a in actions[-15:]:
        try:
            ts = datetime.fromisoformat(a.get("timestamp", "")).strftime("%H:%M:%S")
        except Exception:
            ts = a.get("timestamp", "")
        st.markdown(f"**{ts}** — *{a.get('agent')}*: {a.get('action')}")
        if a.get("details"):
            with st.expander("Details", expanded=False):
                st.json(a["details"])


def _display_sources(state: Dict[str, Any]):
    st.subheader("📚 Research Sources")
    sources = state.get("sources", [])
    if not sources:
        st.info("No sources collected yet.")
        return
    for i, src in enumerate(sources, 1):
        with st.expander(f"{i}. {src.get('title', 'Untitled')}"):
            st.write(f"**URL:** {src.get('url') or 'N/A'}")
            st.write(f"**Type:** {src.get('source_type', 'web')}")
            st.write(f"**Snippet:** {src.get('snippet', '')[:300]}")


def _display_analytics(state: Dict[str, Any]):
    st.subheader("📊 Research Analytics")
    m = calculate_research_metrics(state)
    qb = get_quality_breakdown(state)

    if qb:
        fig = px.pie(values=list(qb.values()), names=list(qb.keys()),
                     title="Quality Score Breakdown")
        st.plotly_chart(fig, use_container_width=True)

    tl = get_research_timeline(state)
    if tl:
        st.subheader("Timeline")
        df = pd.DataFrame(tl)
        if not df.empty:
            st.dataframe(df[["timestamp", "event", "type"]], use_container_width=True)

    aa = m.get("agent_activity", {})
    if aa:
        fig3 = px.bar(x=list(aa.keys()), y=list(aa.values()),
                       title="Agent Activity", labels={"x": "Agent", "y": "Actions"})
        st.plotly_chart(fig3, use_container_width=True)


# ──────────────────────────────────────────────────────────────────────
# Core workflow functions
# ──────────────────────────────────────────────────────────────────────

def run_research(topic: str, depth: str, template: str, model: str):
    """Kick off the research graph until the interrupt point."""
    if st.session_state.research_graph is None:
        st.session_state.research_graph = ResearchGraph(model_name=model)

    graph = st.session_state.research_graph.get_graph()
    initial = create_initial_state(
        topic=topic,
        research_depth=depth,
        template_type=template,
        model_name=model,
    )
    cfg = _graph_config()

    try:
        print(f"\n[App] Starting run_research for topic: '{topic}' with model: '{model}'")
        st.session_state.is_running = True
        st.session_state.interrupted = False

        # Stream until the graph pauses (interrupt_before="human_approval")
        print("[App] Streaming graph events...")
        for event in graph.stream(initial, cfg, stream_mode="updates"):
            for node_name, node_output in event.items():
                print(f"[App] Received event from node: '{node_name}' | Status: {node_output.get('status', 'unknown')}")
                st.session_state.current_state = node_output

        # After streaming ends, check if we're sitting at an interrupt
        print("[App] Streaming ended. Checking interrupt status...")
        snapshot = graph.get_state(cfg)
        if snapshot and snapshot.values:
            st.session_state.current_state = snapshot.values

        if snapshot and snapshot.next and "human_approval" in snapshot.next:
            st.session_state.interrupted = True
            st.session_state.is_running = False
        else:
            st.session_state.is_running = False
            st.session_state.interrupted = False

    except Exception as e:
        # Even on error, check if we reached interrupt
        try:
            snapshot = graph.get_state(cfg)
            if snapshot and snapshot.next and "human_approval" in snapshot.next:
                st.session_state.current_state = snapshot.values
                st.session_state.interrupted = True
                st.session_state.is_running = False
                st.rerun()
                return
        except Exception:
            pass
        st.error(f"Error during research: {e}")
        print(f"[App] Error caught in run_research: {e}")
        st.session_state.is_running = False
        st.session_state.interrupted = False

    st.rerun()


def approve_and_continue():
    """Resume the graph after human approval."""
    if st.session_state.research_graph is None:
        st.error("No research graph initialised.")
        return

    graph = st.session_state.research_graph.get_graph()
    cfg = _graph_config()

    try:
        print("\n[App] Function approve_and_continue triggered. Resuming graph...")
        st.session_state.is_running = True
        st.session_state.interrupted = False

        # Properly update checkpoint state with approval flag
        graph.update_state(cfg, {"is_approved": True, "status": "writing"})
        print("[App] State updated to approved.")

        # Resume from interrupt
        for event in graph.stream(None, cfg, stream_mode="updates"):
            for node_name, node_output in event.items():
                print(f"[App] Resumed event loop received from node: '{node_name}'")
                st.session_state.current_state = node_output

        # Read final checkpoint
        final = graph.get_state(cfg)
        if final and final.values:
            st.session_state.current_state = final.values

        st.session_state.is_running = False
        st.session_state.interrupted = False
        st.rerun()

    except Exception as e:
        st.error(f"Error continuing research: {e}")
        st.session_state.is_running = False


# ──────────────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────────────

def main():
    _init_session()

    st.markdown('<div class="main-header">🔬 Multi-Agent Research Studio</div>',
                unsafe_allow_html=True)

    # ── Sidebar ──
    with st.sidebar:
        st.header("⚙️ Configuration")

        model_name = st.selectbox(
            "LLM Model",
            [
                "llama-3.3-70b-versatile",
                "gpt-oss-20b",
                "meta-llama/llama-4-scout-17b-16e-instruct"
            ],
            index=0,
            help="Select the LLM model",
        )
        research_depth = st.selectbox(
            "Research Depth",
            ["quick", "standard", "comprehensive"],
            index=2,
        )
        template_type = st.selectbox(
            "Report Template",
            list(app_config.RESEARCH_TEMPLATES.keys()),
            index=0,
        )

        st.divider()
        st.subheader("Session Info")
        st.code(st.session_state.thread_id, language=None)
        if st.session_state.current_state:
            st.write(f"Status: **{st.session_state.current_state.get('status', '—')}**")

        st.divider()
        if st.button("🔄 New Research Session", use_container_width=True):
            st.session_state.thread_id = f"thread_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            st.session_state.research_graph = None
            st.session_state.current_state = None
            st.session_state.is_running = False
            st.session_state.interrupted = False
            st.rerun()

    # ── Tabs ──
    tab_res, tab_analytics, tab_src, tab_report, tab_export = st.tabs(
        ["🏠 Research", "📊 Analytics", "📚 Sources", "📝 Report", "💾 Export"]
    )

    # ──────────── Research Tab ────────────
    with tab_res:
        st.header("Start New Research")
        topic = st.text_input("Research Topic", placeholder="Enter a topic to research…")

        c1, _ = st.columns([1, 4])
        with c1:
            start = st.button("🚀 Start Research", type="primary",
                              disabled=st.session_state.is_running)

        cur = st.session_state.current_state
        if cur:
            _display_status(cur)
            _display_metrics(cur)

            # Approval UI when interrupted
            if st.session_state.interrupted:
                st.divider()
                st.subheader("📋 Generated Outline")
                outline = cur.get("outline", "")
                if outline:
                    st.markdown(outline)
                    st.divider()
                    a1, a2 = st.columns(2)
                    with a1:
                        if st.button("✅ Approve & Write Report", type="primary",
                                     use_container_width=True):
                            approve_and_continue()
                    with a2:
                        if st.button("❌ Reject & Refine", use_container_width=True):
                            st.session_state.interrupted = False
                            st.session_state.is_running = False
                            st.rerun()
                else:
                    st.warning("No outline generated yet.")

            _display_log(cur)

        if start and topic:
            with st.spinner("🔍 Researching… this takes a moment."):
                run_research(topic, research_depth, template_type, model_name)

        if st.session_state.is_running:
            st.info("🔄 Research in progress…")

    # ──────────── Analytics Tab ────────────
    with tab_analytics:
        if st.session_state.current_state:
            _display_analytics(st.session_state.current_state)
        else:
            st.info("Start a research session to see analytics.")

    # ──────────── Sources Tab ────────────
    with tab_src:
        if st.session_state.current_state:
            _display_sources(st.session_state.current_state)
        else:
            st.info("Start a research session to see sources.")

    # ──────────── Report Tab ────────────
    with tab_report:
        cur = st.session_state.current_state
        if cur:
            st.header(f"Research Report: {cur.get('topic', 'Untitled')}")
            report = cur.get("final_report")
            if report:
                st.markdown(report)
                meta = cur.get("report_metadata")
                if meta:
                    with st.expander("Report Metadata"):
                        st.json(meta)
            elif cur.get("outline"):
                st.subheader("Outline (report not yet generated)")
                st.markdown(cur["outline"])
                st.info("Approve the outline to generate the final report.")
            else:
                st.info("Research in progress. Report will appear here when ready.")
        else:
            st.info("Start a research session to generate a report.")

    # ──────────── Export Tab ────────────
    with tab_export:
        st.header("Export Research")
        cur = st.session_state.current_state
        if cur:
            fmt = st.selectbox("Export Format", app_config.EXPORT_FORMATS, index=0)
            if st.button("📥 Export Report", type="primary"):
                try:
                    content, binary = export_report(cur, fmt)
                    if fmt == "pdf":
                        st.download_button("Download PDF", binary,
                                           f"report_{datetime.now():%Y%m%d_%H%M%S}.pdf",
                                           "application/pdf")
                    else:
                        ext = {"markdown": ".md", "html": ".html", "json": ".json"}.get(fmt, ".txt")
                        st.download_button(
                            f"Download {fmt.upper()}", content,
                            f"report_{datetime.now():%Y%m%d_%H%M%S}{ext}",
                            "text/plain" if fmt == "markdown" else f"text/{fmt}",
                        )
                except Exception as e:
                    st.error(f"Export error: {e}")
                    if fmt == "pdf":
                        st.info("PDF export requires 'weasyprint' or 'reportlab'.")
        else:
            st.info("Complete a research session to export.")


if __name__ == "__main__":
    main()
