"""TradingAgents A股分析 — Streamlit Web UI."""

from __future__ import annotations

import sys
import textwrap
import time
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

load_dotenv(_PROJECT_ROOT / ".env")

from tradingagents.default_config import DEFAULT_CONFIG  # noqa: E402

from web.components.progress_panel import render_progress  # noqa: E402
from web.components.report_viewer import render_report  # noqa: E402
from web.components.sidebar import render_sidebar  # noqa: E402
from web.history import extract_signal, get_history, load_analysis  # noqa: E402
from web.progress import ProgressTracker  # noqa: E402
from web.runner import run_analysis_in_thread  # noqa: E402

# ── Page config ──────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="A股AI投研系统",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ───────────────────────────────────────────────────────────────

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;900&display=swap');

    #MainMenu, footer, div[data-testid="stDecoration"] { display: none !important; }

    /* Ensure sidebar toggle button is visible and high-contrast */
    button[data-testid="collapsedControl"],
    button[aria-label="Expand sidebar"] {
        display: flex !important;
        color: #ff5a1f !important;
    }

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, sans-serif;
    }
    .stApp {
        background: #0a0a0a;
    }
    section[data-testid="stSidebar"] {
        background: #0f0f0f;
        border-right: 1px solid #1a1a1a;
    }

    .stMetric label { color: #888 !important; font-size: 0.8rem !important; }
    .stMetric [data-testid="stMetricValue"] {
        color: #ff5a1f !important;
        font-weight: 700 !important;
    }
    .stProgress > div > div > div {
        background: linear-gradient(90deg, #ff5a1f, #ff8c42) !important;
    }
    button[kind="primary"] {
        background: linear-gradient(135deg, #ff5a1f, #ff8c42) !important;
        border: none !important;
        font-weight: 700 !important;
        letter-spacing: 0.05em !important;
        box-shadow: 0 4px 15px rgba(255,90,31,0.3) !important;
        transition: all 0.2s ease !important;
    }
    button[kind="primary"]:hover {
        background: linear-gradient(135deg, #e04d15, #ff5a1f) !important;
        box-shadow: 0 6px 20px rgba(255,90,31,0.4) !important;
        transform: translateY(-1px) !important;
    }
    button[kind="secondary"] {
        background: #161616 !important;
        border: 1px solid #2a2a2a !important;
        color: #ccc !important;
        transition: all 0.2s ease !important;
    }
    button[kind="secondary"]:hover {
        background: #1e1e1e !important;
        border-color: #ff5a1f !important;
        color: #ff5a1f !important;
    }
    .stExpander {
        border: 1px solid #222 !important;
        border-radius: 8px !important;
    }
    .stTabs [data-baseweb="tab"] {
        color: #888 !important;
    }
    .stTabs [aria-selected="true"] {
        color: #ff5a1f !important;
        border-bottom-color: #ff5a1f !important;
    }
    div[data-testid="stDownloadButton"] button {
        background: #1a1a2e !important;
        border: 1px solid #ff5a1f !important;
        color: #ff5a1f !important;
    }
    input[data-testid="stTextInputRootElement"] input,
    .stTextInput input {
        background: #161616 !important;
        border-color: #2a2a2a !important;
        color: #f5f1eb !important;
    }
    .stTextInput input:focus {
        border-color: #ff5a1f !important;
        box-shadow: 0 0 0 1px #ff5a1f !important;
    }
    .stDateInput input {
        background: #161616 !important;
        border-color: #2a2a2a !important;
        color: #f5f1eb !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ── Build config ─────────────────────────────────────────────────────────────

def _build_config() -> dict:
    config = DEFAULT_CONFIG.copy()
    return config


# ── Sidebar ──────────────────────────────────────────────────────────────────

with st.sidebar:
    render_sidebar()


# ── Handle "Start Analysis" trigger ──────────────────────────────────────────

start_req = st.session_state.pop("start_analysis", None)
if start_req:
    tracker = ProgressTracker(
        ticker=start_req["ticker"],
        trade_date=start_req["trade_date"],
    )
    st.session_state["tracker"] = tracker
    run_analysis_in_thread(
        ticker=start_req["ticker"],
        trade_date=start_req["trade_date"],
        config=_build_config(),
        tracker=tracker,
    )


# ── Main area state machine ─────────────────────────────────────────────────

tracker: ProgressTracker | None = st.session_state.get("tracker")
viewing_history: str | None = st.session_state.get("viewing_history")

if viewing_history:
    try:
        state = load_analysis(viewing_history)
        signal = extract_signal(state)
        ticker = Path(viewing_history).parent.parent.name
        trade_date = Path(viewing_history).stem.replace("full_states_log_", "")
        render_report(state, ticker, trade_date, signal)
    except Exception as exc:
        st.error(f"加载失败: {exc}")

elif tracker and tracker.is_running:
    render_progress(tracker)
    time.sleep(2)
    st.rerun()

elif tracker and tracker.is_complete:
    render_report(
        tracker.final_state,
        tracker.ticker,
        tracker.trade_date,
        tracker.signal,
        elapsed=tracker.elapsed,
    )

elif tracker and tracker.error:
    st.error(f"分析失败: {tracker.error}")
    if st.button("重试"):
        st.session_state.pop("tracker", None)
        st.rerun()

else:
    welcome_html = textwrap.dedent("""
        <div style="
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            min-height: 30vh;
            text-align: center;
        ">
            <div style="font-size: 3rem; margin-bottom: 0.8rem;">📈</div>
            <div style="font-size: 2.2rem; font-weight: 900; margin-bottom: 0.4rem;">
                <span style="color: #ff5a1f;">A股AI</span><span style="color: #f5f1eb;">投研系统</span>
            </div>
            <div style="color: #888; font-size: 1rem; max-width: 500px; line-height: 1.6;">
                7位AI分析师 → 质量门控 → 多空辩论 → 风控评估 → 最终决策
            </div>
            <div style="
                margin-top: 1.2rem;
                padding: 0.6rem 1.5rem;
                border: 1px solid #222;
                border-radius: 10px;
                color: #666;
                font-size: 0.85rem;
            ">
                ← 在左侧输入股票代码，开始分析
            </div>
        </div>
    """).strip()
    st.markdown(welcome_html, unsafe_allow_html=True)

    history = get_history()
    if history:
        st.markdown(
            textwrap.dedent('<div style="margin:1.5rem 0 0.8rem; font-size:0.8rem; color:#666; text-transform:uppercase; letter-spacing:1px;">历史记录</div>'),
            unsafe_allow_html=True,
        )
        cols_per_row = 4
        for i in range(0, min(len(history), 12), cols_per_row):
            row = history[i:i + cols_per_row]
            cols = st.columns(len(row))
            for col, entry in zip(cols, row):
                t, d = entry["ticker"], entry["date"]
                card_html = textwrap.dedent(f"""
                    <div style="
                        background: #111;
                        border: 1px solid #2a2a2a;
                        border-radius: 8px;
                        padding: 12px;
                        text-align: center;
                    ">
                        <div style="font-size:1rem; font-weight:700; color:#f5f1eb;">{t}</div>
                        <div style="font-size:0.75rem; color:#666; margin-top:4px;">{d}</div>
                    </div>
                """).strip()
                col.markdown(card_html, unsafe_allow_html=True)
                if col.button("查看", key=f"hist_{t}_{d}", use_container_width=True):
                    st.session_state["viewing_history"] = entry["path"]
                    st.session_state["start_analysis"] = None

    st.markdown("")
