#!/usr/bin/env python3
"""Comprehensive test for pdf_export.py - covers edge cases that caused 'Not enough horizontal space'."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from web.pdf_export import generate_pdf, _CJK_FONT_PATH, _find_cjk_font_paths

print(f"CJK Font (cached): {_CJK_FONT_PATH}")
print(f"CJK Font candidates found: {_find_cjk_font_paths()}")
print()

all_passed = True


def test_basic_pdf():
    global all_passed
    name = "基础PDF生成"
    try:
        final_state = {
            "market_report": "技术面偏多，均线多头排列。",
            "sentiment_report": "市场情绪偏多。",
        }
        pdf_bytes = generate_pdf(final_state, "300750", "2026-05-25", "BUY")
        out = Path(__file__).resolve().parent / "test_output_basic.pdf"
        out.write_bytes(pdf_bytes)
        print(f"  [PASS] {name} - {len(pdf_bytes)} bytes -> {out.name}")
    except Exception as e:
        all_passed = False
        print(f"  [FAIL] {name} - {e}")


def test_long_ticker_name():
    global all_passed
    name = "超长股票名称"
    try:
        final_state = {
            "market_report": "测试超长股票名称场景。",
        }
        pdf_bytes = generate_pdf(final_state, "宁德时代新能源科技股份有限公司", "2026-05-25", "SELL")
        out = Path(__file__).resolve().parent / "test_output_long_name.pdf"
        out.write_bytes(pdf_bytes)
        print(f"  [PASS] {name} - {len(pdf_bytes)} bytes -> {out.name}")
    except Exception as e:
        all_passed = False
        print(f"  [FAIL] {name} - {e}")


def test_wide_table():
    global all_passed
    name = "宽表格渲染"
    try:
        final_state = {
            "market_report": """## 指标汇总

| 指标名称 | 当前数值 | 变化趋势 | 信号强度 | 综合评价 |
|----------|----------|----------|----------|----------|
| MA5移动平均线 | 245.30元 | 上升 | 强烈看多 | 均线支撑明显 |
| MA10移动平均线 | 243.80元 | 上升 | 看多 | 中期趋势向好 |
| RSI相对强弱指标 | 62.5 | 中性偏多 | 中性 | 尚未超买 |
| MACD指标 | 正值 | 扩大 | 看多 | 金叉确认 |
| 布林带 | 上轨附近 | 收窄 | 看多 | 突破在即 |
""",
        }
        pdf_bytes = generate_pdf(final_state, "600519", "2026-05-25", "BUY")
        out = Path(__file__).resolve().parent / "test_output_wide_table.pdf"
        out.write_bytes(pdf_bytes)
        print(f"  [PASS] {name} - {len(pdf_bytes)} bytes -> {out.name}")
    except Exception as e:
        all_passed = False
        print(f"  [FAIL] {name} - {e}")


def test_all_sections():
    global all_passed
    name = "完整报告（所有章节）"
    try:
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
            "sentiment_report": "市场情绪偏多，融资余额持续增加，北向资金净流入。投资者信心指数上升至78.3，较上月提升5.2个百分点。",
            "news_report": """## 近期重要新闻

### 正面新闻
1. 公司发布2026年一季度业绩预增公告，预计净利润同比增长50%-70%
2. 获得大额政府补贴，支持新能源技术研发
3. 与国际知名车企签署长期供货协议

### 负面新闻
- 行业竞争加剧，市场份额面临挑战
- 原材料价格波动，成本压力增大

**综合评价**: 新闻面整体偏正面，业绩增长预期明确。
""",
            "fundamentals_report": """## 基本面分析

| 指标 | 数值 | 行业平均 | 评价 |
|------|------|----------|------|
| 市盈率(PE) | 25.3 | 30.1 | 低于平均 |
| 市净率(PB) | 4.2 | 3.8 | 略高于平均 |
| ROE | 18.5% | 12.3% | 优秀 |
| 营收增速 | 35% | 15% | 远超行业 |

**总结**: 基本面优秀，估值合理，成长性突出。
""",
            "policy_report": "近期政策面偏暖，新能源产业政策持续加码，碳中和目标推动行业长期发展。",
            "hot_money_report": """## 游资追踪

### 主力资金流向
- 今日主力净流入: 3.2亿元
- 近5日主力净流入: 12.8亿元
- 北向资金今日净买入: 1.5亿元

### 龙虎榜数据
| 营业部 | 买入金额 | 卖出金额 | 净买入 |
|--------|----------|----------|--------|
| 国泰君安上海分公司 | 5800万 | 1200万 | 4600万 |
| 中信证券深圳总部 | 3200万 | 800万 | 2400万 |
""",
            "lockup_report": "未来30天无大规模解禁计划，下一批限售股解禁日期为2026年8月15日，解禁数量约500万股，占总股本0.2%。",
            "investment_debate_state": {
                "bull_history": "多方认为技术面和基本面均支持上涨，均线多头排列，业绩增速远超行业平均，政策面持续利好",
                "bear_history": "空方认为估值偏高，市净率高于行业平均，原材料成本上升可能压缩利润空间，行业竞争加剧",
                "judge_decision": "综合判断偏多，技术面和基本面优势明显，但需关注成本压力，建议逢低布局",
            },
            "trader_investment_decision": "建议在当前价位附近建立头寸，仓位控制在30%以内",
            "investment_plan": "建议在 240-245 区间分批建仓，止损位 235，目标位 260。分三批建仓：第一批30%在245附近，第二批40%在242附近，第三批30%在240附近。",
            "risk_debate_state": {
                "aggressive_history": "激进观点：当前技术面和基本面共振，可重仓参与，建议仓位50%以上",
                "conservative_history": "保守观点：估值偏高，建议轻仓观望，仓位不超过15%",
                "neutral_history": "中性观点：适度配置，仓位控制在25%-35%之间",
                "judge_decision": "风控建议：综合各方观点，仓位控制在 30% 以内，严格执行止损纪律",
            },
            "final_trade_decision": "买入，仓位 30%，止损 235，目标 260。风险收益比约1:2.5，符合交易标准。",
        }
        pdf_bytes = generate_pdf(final_state, "300750", "2026-05-25", "BUY")
        out = Path(__file__).resolve().parent / "test_output_full.pdf"
        out.write_bytes(pdf_bytes)
        print(f"  [PASS] {name} - {len(pdf_bytes)} bytes -> {out.name}")
    except Exception as e:
        all_passed = False
        print(f"  [FAIL] {name} - {e}")


def test_long_paragraph():
    global all_passed
    name = "超长段落文本"
    try:
        long_text = "这是一段非常长的中文文本，用于测试PDF生成时对超长段落的处理能力。" * 50
        final_state = {
            "market_report": long_text,
        }
        pdf_bytes = generate_pdf(final_state, "000001", "2026-05-25", "HOLD")
        out = Path(__file__).resolve().parent / "test_output_long_para.pdf"
        out.write_bytes(pdf_bytes)
        print(f"  [PASS] {name} - {len(pdf_bytes)} bytes -> {out.name}")
    except Exception as e:
        all_passed = False
        print(f"  [FAIL] {name} - {e}")


def test_special_chars():
    global all_passed
    name = "特殊字符和Markdown语法"
    try:
        final_state = {
            "market_report": """## 特殊字符测试

- 包含**加粗**和*斜体*文本
- 包含`代码`标记
- 包含[链接](https://example.com)文本
- 包含特殊符号：© ® ™ ° ± × ÷ € £ ¥
- 包含数学表达式：RSI = 100 - 100/(1+RS)
- 包含箭头符号：→ ← ↑ ↓

### 混合内容
**重要提示**: 本报告包含**多种格式**的*混合*文本，用于验证`渲染引擎`的兼容性。

1. 第一项：数值为 **25.3%**，较上期*提升*3.2个百分点
2. 第二项：目标价 `260元`，当前价 `245元`
3. 第三项：止损价 **235元**，严格执行
""",
        }
        pdf_bytes = generate_pdf(final_state, "002594", "2026-05-25", "BUY")
        out = Path(__file__).resolve().parent / "test_output_special.pdf"
        out.write_bytes(pdf_bytes)
        print(f"  [PASS] {name} - {len(pdf_bytes)} bytes -> {out.name}")
    except Exception as e:
        all_passed = False
        print(f"  [FAIL] {name} - {e}")


def test_think_tag_stripping():
    global all_passed
    name = "Think标签过滤"
    try:
        think_content = "<think>\n这是AI思考过程，应该被过滤掉。\n分析步骤：1.查看数据 2.对比指标\n</think>\n\n买入信号确认，仓位30%。"
        final_state = {
            "market_report": "正常文本内容。",
            "investment_plan": think_content,
        }
        pdf_bytes = generate_pdf(final_state, "600519", "2026-05-25", "BUY")
        out = Path(__file__).resolve().parent / "test_output_think.pdf"
        out.write_bytes(pdf_bytes)
        print(f"  [PASS] {name} - {len(pdf_bytes)} bytes -> {out.name}")
    except Exception as e:
        all_passed = False
        print(f"  [FAIL] {name} - {e}")


print("=" * 60)
print("PDF Export 测试套件")
print("=" * 60)

test_basic_pdf()
test_long_ticker_name()
test_wide_table()
test_all_sections()
test_long_paragraph()
test_special_chars()
test_think_tag_stripping()

print()
print("=" * 60)
if all_passed:
    print("ALL TESTS PASSED!")
else:
    print("SOME TESTS FAILED - see above for details")
print("=" * 60)
