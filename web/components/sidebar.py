"""Sidebar: stock input, config info, and history list."""

from __future__ import annotations

from datetime import date

import streamlit as st

from tradingagents.default_config import DEFAULT_CONFIG
from web.history import get_history

_PROVIDER_NAMES = {
    "deepseek": "DeepSeek",
    "openai": "OpenAI",
    "anthropic": "Anthropic",
    "google": "Google Gemini",
    "xai": "xAI Grok",
    "qwen": "通义千问 Qwen",
    "glm": "智谱 GLM",
    "minimax": "MiniMax",
    "ollama": "Ollama（本地）",
    "openrouter": "OpenRouter",
    "local": "本地模型",
}


def _resolve_user_input(raw: str) -> tuple[str, str | None]:
    """Resolve raw user input to (ticker_code, error_msg).

    Accepts 6-digit codes or Chinese stock names (e.g. '宝光股份').
    Returns (code, None) on success or ("", error_msg) on failure.
    """
    from tradingagents.dataflows.a_stock import resolve_ticker

    try:
        code = resolve_ticker(raw)
        return code, None
    except ValueError as e:
        return "", str(e)


def _render_config_info() -> None:
    """Render current LLM configuration (read from .env)."""
    provider = DEFAULT_CONFIG["llm_provider"]
    provider_name = _PROVIDER_NAMES.get(provider, provider)
    quick_model = DEFAULT_CONFIG["quick_think_llm"]
    deep_model = DEFAULT_CONFIG["deep_think_llm"]

    st.markdown(
        f"""
        <div style="
            background: #1a1a2e;
            border: 1px solid #2a2a4a;
            border-radius: 8px;
            padding: 12px;
            font-size: 0.85rem;
        ">
            <div style="color: #888; margin-bottom: 6px;">当前模型配置</div>
            <div style="color: #f5f1eb; margin-bottom: 4px;">
                <span style="color: #888;">供应商：</span>{provider_name}
            </div>
            <div style="color: #f5f1eb; margin-bottom: 4px;">
                <span style="color: #888;">快速模型：</span>{quick_model}
            </div>
            <div style="color: #f5f1eb;">
                <span style="color: #888;">深度模型：</span>{deep_model}
            </div>
            <div style="color: #555; font-size: 0.75rem; margin-top: 8px;">
                修改 .env 文件后重启生效
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar() -> None:
    """Render the sidebar with input controls and history."""

    st.markdown(
        """
        <div style="text-align:center; margin-bottom:1.5rem;">
            <span style="font-size:2rem; font-weight:800; color:#ff5a1f;">Trading</span><span style="font-size:2rem; font-weight:800; color:#f5f1eb;">Agents</span><span style="font-size:2rem; font-weight:800; color:#f5f1eb;">-</span><span style="font-size:2rem; font-weight:800; color:#ff5a1f;">Astock</span>
            <div style="font-size:0.85rem; color:#888; margin-top:0.2rem;">
                A股多Agent投研系统
            </div>
            <div style="font-size:0.7rem; color:#555; margin-top:0.3rem;">
                by <a href="https://github.com/simonlin1212" style="color:#ff5a1f; text-decoration:none;">simonlin1212</a>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("---")
    st.markdown("#### 新建分析")

    ticker = st.text_input(
        "股票代码",
        placeholder="例: 300750 或 宁德时代",
        key="input_ticker",
        help="输入6位A股代码或中文股票全称",
    )

    trade_date = st.date_input(
        "分析日期",
        value=date.today(),
        key="input_date",
    )

    with st.expander("⚙️ 模型配置", expanded=False):
        _render_config_info()

    tracker = st.session_state.get("tracker")
    is_busy = tracker is not None and tracker.is_running

    if st.button(
        "开始分析" if not is_busy else "分析进行中...",
        use_container_width=True,
        disabled=is_busy or not ticker,
        type="primary",
    ):
        resolved_code, err = _resolve_user_input(ticker)
        if err:
            st.error(f"❌ {err}")
        else:
            if resolved_code != ticker.strip():
                st.success(f"✅ {ticker.strip()} → {resolved_code}")
            st.session_state["start_analysis"] = {
                "ticker": resolved_code,
                "trade_date": trade_date.strftime("%Y-%m-%d"),
            }
            st.session_state["viewing_history"] = None

    st.markdown("---")
    st.markdown("#### 历史记录")

    history = get_history()
    if not history:
        st.caption("暂无历史记录")
        return

    for entry in history[:20]:
        t, d = entry["ticker"], entry["date"]
        label = f"{t}  ·  {d}"
        if st.button(label, key=f"hist_{t}_{d}", use_container_width=True):
            st.session_state["viewing_history"] = entry["path"]
            st.session_state["start_analysis"] = None

    st.markdown("---")
    st.caption("⚠️ 仅供学习研究，不构成投资建议")
