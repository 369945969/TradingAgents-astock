"""Sidebar: stock input and config info."""

from __future__ import annotations

from datetime import date

import streamlit as st

from tradingagents.default_config import DEFAULT_CONFIG

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
    from tradingagents.dataflows.a_stock import resolve_ticker

    try:
        code = resolve_ticker(raw)
        return code, None
    except ValueError as e:
        return "", str(e)


def render_sidebar() -> None:
    st.markdown(
        """
        <div style="text-align:center; margin-bottom:1.5rem;">
            <span style="font-size:1.8rem; font-weight:800; color:#ff5a1f;">A股AI</span><span style="font-size:1.8rem; font-weight:800; color:#f5f1eb;">投研系统</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    ticker = st.text_input(
        "股票代码",
        placeholder="例: 300750 或 宁德时代",
        key="input_ticker",
        label_visibility="collapsed",
        help="输入6位A股代码或中文股票全称",
    )

    trade_date = st.date_input(
        "分析日期",
        value=date.today(),
        key="input_date",
        label_visibility="collapsed",
    )

    tracker = st.session_state.get("tracker")
    is_busy = tracker is not None and tracker.is_running

    if st.button(
        "🚀 开始分析" if not is_busy else "⏳ 分析进行中...",
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

    provider = DEFAULT_CONFIG["llm_provider"]
    provider_name = _PROVIDER_NAMES.get(provider, provider)
    quick_model = DEFAULT_CONFIG["quick_think_llm"]
    deep_model = DEFAULT_CONFIG["deep_think_llm"]

    st.markdown(
        f"""
        <div style="
            background: #111;
            border: 1px solid #222;
            border-radius: 10px;
            padding: 14px;
            margin-bottom: 1rem;
        ">
            <div style="font-size:0.7rem; color:#666; text-transform:uppercase; letter-spacing:1px; margin-bottom:8px;">
                ⚙️ 模型配置
            </div>
            <div style="font-size:0.82rem; line-height:1.8;">
                <div><span style="color:#888;">供应商</span> <span style="color:#f5f1eb;">{provider_name}</span></div>
                <div><span style="color:#888;">快速模型</span> <span style="color:#f5f1eb;">{quick_model}</span></div>
                <div><span style="color:#888;">深度模型</span> <span style="color:#f5f1eb;">{deep_model}</span></div>
            </div>
            <div style="color:#444; font-size:0.7rem; margin-top:8px;">修改 .env 后重启生效</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
