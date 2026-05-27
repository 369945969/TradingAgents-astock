"""Real-time progress display for the analysis pipeline."""

from __future__ import annotations

import streamlit as st

from web.progress import PIPELINE_STAGES, ProgressTracker


def _status_badge(status: str) -> str:
    if status == "done":
        return '<span style="color:#22c55e; font-size:1.1rem;">✓</span>'
    if status == "active":
        return '<span style="color:#ff5a1f; font-size:1.1rem;">◉</span>'
    return '<span style="color:#333; font-size:1.1rem;">○</span>'


def _format_time(seconds: float) -> str:
    m, s = divmod(int(seconds), 60)
    return f"{m}:{s:02d}"


def render_progress(tracker: ProgressTracker) -> None:
    completed = len(tracker.completed_stages)
    total = len(PIPELINE_STAGES)
    pct = completed / total if total else 0

    st.markdown(
        f"""
        <div style="
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            border: 1px solid #2a2a4a;
            border-radius: 14px;
            padding: 1.5rem 2rem;
            margin-bottom: 1.5rem;
        ">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <div>
                    <div style="font-size:0.75rem; color:#666; text-transform:uppercase; letter-spacing:1px;">分析进行中</div>
                    <div style="font-size:1.6rem; font-weight:700; color:#f5f1eb; margin-top:4px;">{tracker.ticker}</div>
                </div>
                <div style="text-align:right;">
                    <div style="font-size:2rem; font-weight:800; color:#ff5a1f;">{completed}/{total}</div>
                    <div style="font-size:0.8rem; color:#888;">{_format_time(tracker.elapsed)}</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.progress(pct)

    analyst_stages = PIPELINE_STAGES[:7]
    post_stages = PIPELINE_STAGES[7:]

    st.markdown(
        '<div style="margin:1rem 0 0.5rem; font-size:0.8rem; color:#666; text-transform:uppercase; letter-spacing:1px;">分析师 (Analysts)</div>',
        unsafe_allow_html=True,
    )

    cols = st.columns(len(analyst_stages))
    for col, stage in zip(cols, analyst_stages):
        status = tracker.stage_status(stage["id"])
        badge = _status_badge(status)
        if status == "done":
            bg = "#0f1a0f"
            border = "#1a3a1a"
            label_color = "#22c55e"
        elif status == "active":
            bg = "#1a1008"
            border = "#3a2a1a"
            label_color = "#ff5a1f"
        else:
            bg = "#111"
            border = "#1a1a1a"
            label_color = "#444"
        col.markdown(
            f"""
            <div style="
                background:{bg};
                border:1px solid {border};
                border-radius:8px;
                padding:10px 6px;
                text-align:center;
            ">
                <div style="font-size:1.2rem;">{stage['icon']}</div>
                <div>{badge}</div>
                <div style="font-size:0.7rem; color:{label_color}; margin-top:2px;">{stage['name']}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        '<div style="margin:1rem 0 0.5rem; font-size:0.8rem; color:#666; text-transform:uppercase; letter-spacing:1px;">流程阶段 (Pipeline)</div>',
        unsafe_allow_html=True,
    )

    cols2 = st.columns(len(post_stages))
    for col, stage in zip(cols2, post_stages):
        status = tracker.stage_status(stage["id"])
        badge = _status_badge(status)
        if status == "done":
            bg = "#0f1a0f"
            border = "#1a3a1a"
            label_color = "#22c55e"
        elif status == "active":
            bg = "#1a1008"
            border = "#3a2a1a"
            label_color = "#ff5a1f"
        else:
            bg = "#111"
            border = "#1a1a1a"
            label_color = "#444"
        col.markdown(
            f"""
            <div style="
                background:{bg};
                border:1px solid {border};
                border-radius:8px;
                padding:10px 6px;
                text-align:center;
            ">
                <div style="font-size:1.2rem;">{stage['icon']}</div>
                <div>{badge}</div>
                <div style="font-size:0.7rem; color:{label_color}; margin-top:2px;">{stage['name']}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("---")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("LLM 调用", tracker.llm_calls)
    c2.metric("工具调用", tracker.tool_calls)
    c3.metric("输入 Tokens", f"{tracker.tokens_in:,}")
    c4.metric("输出 Tokens", f"{tracker.tokens_out:,}")

    if tracker.error:
        st.error(f"错误: {tracker.error}")

    completed_reports = [
        (stage["name"], stage["icon"], tracker.stage_reports[stage["id"]])
        for stage in PIPELINE_STAGES
        if stage["id"] in tracker.stage_reports
    ]

    if completed_reports:
        st.markdown(
            '<div style="margin:0.5rem 0 0.3rem; font-size:0.8rem; color:#666; text-transform:uppercase; letter-spacing:1px;">'
            f"Reports ({len(completed_reports)})</div>",
            unsafe_allow_html=True,
        )
        for name, icon, report in reversed(completed_reports):
            is_latest = (name == completed_reports[-1][0])
            with st.expander(f"{icon} {name}", expanded=is_latest):
                st.markdown(report[:3000])
