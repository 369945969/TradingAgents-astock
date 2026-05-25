#!/usr/bin/env python3
"""Test PDF generation with CJK font support - uses the actual pdf_export module."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from web.pdf_export import generate_pdf, _CJK_FONT_PATH

print(f"CJK Font: {_CJK_FONT_PATH}")

final_state = {
    "market_report": """## 技术指标分析

### 移动平均线
- MA5: 245.30 元，当前价格在MA5上方
- MA10: 243.80 元，当前价格在MA10上方
- MA20: 241.50 元，当前价格在MA20上方

### MACD 指标
MACD柱状图为正值，DIF线在DEA线上方，显示多头趋势。

### RSI 指标
RSI(14) = 62.5，处于中性偏多区域。

| 指标 | 数值 | 信号 |
|------|------|------|
| MA5 | 245.30 | 看多 |
| MA10 | 243.80 | 看多 |
| RSI | 62.5 | 中性 |

**总结**: 技术面整体偏多，短期趋势向好。

1. 第一条要点：均线多头排列
2. 第二条要点：MACD金叉确认
3. 第三条要点：成交量放大

---
以上为技术分析报告。
""",
    "sentiment_report": "市场情绪偏多，融资余额持续增加，北向资金净流入。",
    "news_report": "近期新闻以正面为主，公司发布业绩预增公告。",
    "fundamentals_report": "市盈率 25.3，市净率 4.2，ROE 18.5%，营收同比增长 35%。",
    "investment_debate_state": {
        "bull_history": "多方认为技术面和基本面均支持上涨",
        "bear_history": "空方认为估值偏高，存在回调风险",
        "judge_decision": "综合判断偏多，建议逢低布局",
    },
    "investment_plan": "建议在 240-245 区间分批建仓，止损位 235，目标位 260。",
    "risk_debate_state": {
        "aggressive_history": "激进观点：可重仓参与",
        "conservative_history": "保守观点：建议轻仓观望",
        "neutral_history": "中性观点：适度配置",
        "judge_decision": "风控建议：仓位控制在 30% 以内",
    },
    "final_trade_decision": "买入，仓位 30%，止损 235，目标 260",
}

try:
    pdf_bytes = generate_pdf(final_state, "300750", "2026-05-25", "BUY")
    output_path = Path(__file__).resolve().parent / "test_pdf_output.pdf"
    output_path.write_bytes(pdf_bytes)
    print(f"[OK] PDF generated: {output_path}")
    print(f"[OK] File size: {len(pdf_bytes)} bytes")
except Exception as e:
    print(f"[FAIL] {e}")
    import traceback
    traceback.print_exc()
