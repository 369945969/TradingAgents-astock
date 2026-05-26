"""Render the completed analysis report with tab-based layout and PDF download."""

from __future__ import annotations

import re
import textwrap
from typing import Any

import streamlit as st

from web.pdf_export import generate_pdf


def _strip_think(text: str) -> str:
    return re.sub(r"<think>.*?</think>\s*", "", text, flags=re.DOTALL).strip()


def _clean_html(html: str) -> str:
    """Remove newlines and collapse whitespace to prevent Markdown code block interpretation."""
    html = html.replace("\n", " ")
    return re.sub(r"\s+", " ", html).strip()


def _signal_style(signal: str) -> tuple[str, str]:
    s = signal.upper()
    if "BUY" in s:
        return "#22c55e", "买入"
    if "OVERWEIGHT" in s:
        return "#4ade80", "增持"
    if "SELL" in s:
        return "#ef4444", "卖出"
    if "UNDERWEIGHT" in s:
        return "#f87171", "减持"
    return "#fbbf24", "持有"


_ANALYST_SECTIONS = [
    ("market_report", "📊 技术分析", "技术指标、趋势、支撑/阻力"),
    ("sentiment_report", "💬 市场情绪", "投资者情绪与市场氛围"),
    ("news_report", "📰 新闻舆情", "近期新闻与舆论分析"),
    ("fundamentals_report", "📋 基本面", "财务数据与估值分析"),
    ("policy_report", "🏛️ 政策分析", "行业政策与监管动态"),
    ("hot_money_report", "🔥 游资追踪", "主力资金与游资动向"),
    ("lockup_report", "🔒 解禁/减持", "限售解禁与减持计划"),
]


def _render_signal_card(signal: str, ticker: str, trade_date: str, elapsed: float | None = None) -> None:
    color, cn_signal = _signal_style(signal)

    stats_html = ""
    if elapsed is not None:
        m, s = divmod(int(elapsed), 60)
        stats_html = f'<div style="font-size:0.85rem; color:#888; margin-top:0.3rem;">耗时 {m}:{s:02d}</div>'

    html = _clean_html(f"""
        <div style="
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            border: 1px solid #2a2a4a;
            border-radius: 16px;
            padding: 1.8rem 2rem;
            margin-bottom: 1.5rem;
        ">
            <div style="display:flex; align-items:center; justify-content:space-between;">
                <div style="flex:1;">
                    <div style="font-size:0.7rem; color:#666; text-transform:uppercase; letter-spacing:2px;">Trading Signal</div>
                    <div style="font-size:3rem; font-weight:900; color:{color}; margin:0.2rem 0; line-height:1.1;">
                        {signal.upper()}
                    </div>
                    <div style="font-size:1rem; color:#aaa;">
                        {ticker} · {trade_date}
                    </div>
                    {stats_html}
                </div>
                <div style="
                    width: 80px; height: 80px;
                    border-radius: 50%;
                    border: 3px solid {color};
                    display: flex; align-items: center; justify-content: center;
                    font-size: 1.4rem; font-weight: 800; color: {color};
                ">
                    {cn_signal}
                </div>
            </div>
        </div>
    """)
    st.markdown(html, unsafe_allow_html=True)


def _render_analyst_grid(final_state: dict[str, Any]) -> None:
    row1 = _ANALYST_SECTIONS[:4]
    row2 = _ANALYST_SECTIONS[4:]

    for row in (row1, row2):
        cols = st.columns(len(row))
        for col, (key, title, desc) in zip(cols, row):
            content = final_state.get(key, "")
            has_content = bool(content)
            if has_content:
                bg = "#111"
                border = "#2a2a2a"
                icon_color = "#f5f1eb"
            else:
                bg = "#0a0a0a"
                border = "#1a1a1a"
                icon_color = "#333"
            col_html = _clean_html(f"""
                <div style="
                    background:{bg};
                    border:1px solid {border};
                    border-radius:10px;
                    padding:14px;
                    min-height:80px;
                ">
                    <div style="font-size:0.9rem; font-weight:600; color:{icon_color};">{title}</div>
                    <div style="font-size:0.7rem; color:#555; margin-top:2px;">{desc}</div>
                    <div style="font-size:0.7rem; color:#22c55e; margin-top:8px;">{'✓ 已完成' if has_content else '—'}</div>
                </div>
            """)
            col.markdown(col_html, unsafe_allow_html=True)

    st.markdown("---")

    for key, title, _ in _ANALYST_SECTIONS:
        content = final_state.get(key, "")
        if not content:
            continue
        with st.expander(title, expanded=False):
            st.markdown(_strip_think(str(content)))


def _render_debate(final_state: dict[str, Any]) -> None:
    inv_plan = final_state.get("investment_plan", "")
    if inv_plan:
        st.markdown("#### 👔 最终投资建议")
        plan_html = _clean_html(f"""
            <div style="
                background: #111;
                border: 1px solid #2a2a2a;
                border-radius: 10px;
                padding: 1.2rem;
                margin-bottom: 1rem;
            ">
                {_strip_think(str(inv_plan))}
            </div>
        """)
        st.markdown(plan_html, unsafe_allow_html=True)

    debate = final_state.get("investment_debate_state")
    if debate and isinstance(debate, dict):
        st.markdown("#### ⚔️ 多空辩论")
        tab_bull, tab_bear, tab_judge = st.tabs(["🟢 多方", "🔴 空方", "⚖️ 研究经理"])
        with tab_bull:
            st.markdown(_strip_think(debate.get("bull_history", "") or "无数据"))
        with tab_bear:
            st.markdown(_strip_think(debate.get("bear_history", "") or "无数据"))
        with tab_judge:
            st.markdown(_strip_think(debate.get("judge_decision", "") or "无数据"))

    trader_decision = final_state.get("trader_investment_decision") or final_state.get("trader_investment_plan")
    if trader_decision:
        st.markdown("#### 💹 交易员决策")
        trader_html = _clean_html(f"""
            <div style="
                background: #111;
                border: 1px solid #2a2a2a;
                border-radius: 10px;
                padding: 1.2rem;
            ">
                {_strip_think(str(trader_decision))}
            </div>
        """)
        st.markdown(trader_html, unsafe_allow_html=True)


def _render_risk(final_state: dict[str, Any]) -> None:
    risk = final_state.get("risk_debate_state")
    if risk and isinstance(risk, dict):
        st.markdown("#### 🛡️ 风控评估")
        tab_agg, tab_con, tab_neu, tab_rj = st.tabs(["🔥 激进", "🧊 保守", "⚖️ 中性", "📋 风控决策"])
        with tab_agg:
            st.markdown(_strip_think(risk.get("aggressive_history", "") or "无数据"))
        with tab_con:
            st.markdown(_strip_think(risk.get("conservative_history", "") or "无数据"))
        with tab_neu:
            st.markdown(_strip_think(risk.get("neutral_history", "") or "无数据"))
        with tab_rj:
            st.markdown(_strip_think(risk.get("judge_decision", "") or "无数据"))

    dqs = final_state.get("data_quality_summary", "")
    if dqs:
        st.markdown("#### ✅ 数据质量")
        st.markdown(str(dqs))


def _render_export(final_state: dict[str, Any], ticker: str, trade_date: str) -> None:
    st.markdown("#### 📥 导出报告")

    try:
        pdf_bytes = generate_pdf(final_state, ticker, trade_date, "")
        st.download_button(
            "📥 下载 PDF 报告",
            data=pdf_bytes,
            file_name=f"TradingAgents-Astock_{ticker}_{trade_date}.pdf",
            mime="application/pdf",
            use_container_width=True,
        )
    except Exception as e:
        st.caption("📄 PDF 生成不可用")
        with st.expander("查看详情"):
            st.code(str(e))

    dqs = final_state.get("data_quality_summary", "")
    if dqs:
        with st.expander("✅ 数据质量报告", expanded=False):
            st.markdown(str(dqs))


def render_report(
    final_state: dict[str, Any],
    ticker: str,
    trade_date: str,
    signal: str,
    elapsed: float | None = None,
) -> None:
    _render_signal_card(signal, ticker, trade_date, elapsed)

    tab_analysts, tab_debate, tab_risk, tab_export = st.tabs(
        ["📊 分析师报告", "⚔️ 辩论与决策", "🛡️ 风控评估", "📥 导出"]
    )

    with tab_analysts:
        _render_analyst_grid(final_state)

    with tab_debate:
        _render_debate(final_state)

    with tab_risk:
        _render_risk(final_state)

    with tab_export:
        _render_export(final_state, ticker, trade_date)
