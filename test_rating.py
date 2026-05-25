import re

RATINGS_5_TIER = ("Buy", "Overweight", "Hold", "Underweight", "Sell")
_RATING_SET = {r.lower() for r in RATINGS_5_TIER}
_RATING_LABEL_RE = re.compile(r"rating.*?[:\-][\s*]*(\w+)", re.IGNORECASE)

_RATING_KEYWORDS_ZH = {
    "买入": "Buy",
    "加仓": "Overweight",
    "增持": "Overweight",
    "持有": "Hold",
    "观望": "Hold",
    "减持": "Underweight",
    "减仓": "Underweight",
    "卖出": "Sell",
    "清仓": "Sell",
}

def parse_rating_new(text, default="Hold"):
    for line in text.splitlines():
        m = _RATING_LABEL_RE.search(line)
        if m and m.group(1).lower() in _RATING_SET:
            return m.group(1).capitalize()
    lines = text.splitlines()
    for line in lines:
        line_lower = line.lower()
        for word in line_lower.split():
            clean = word.strip("*:.,")
            if clean in _RATING_SET:
                return clean.capitalize()
    full_lower = text.lower()
    for zh_keyword, en_rating in _RATING_KEYWORDS_ZH.items():
        if zh_keyword in full_lower:
            return en_rating
    return default

def parse_rating_old(text, default="Hold"):
    for line in text.splitlines():
        m = _RATING_LABEL_RE.search(line)
        if m and m.group(1).lower() in _RATING_SET:
            return m.group(1).capitalize()
    for line in text.splitlines():
        for word in line.lower().split():
            clean = word.strip("*:.,")
            if clean in _RATING_SET:
                return clean.capitalize()
    return default

real_cases = [
    (
        "structured output with Underweight",
        "**Rating**: Underweight\n\n**Executive Summary**: 建议减持，仓位控制在30%\n\n**Investment Thesis**: 综合分析后建议减持",
    ),
    (
        "structured output with Sell",
        "**Rating**: Sell\n\n**Executive Summary**: 建议清仓止损\n\n**Investment Thesis**: 风险较大建议卖出",
    ),
    (
        "free text with 减持",
        "综合分析后，建议减持该股票，仓位控制在30%以下。当前市场环境不佳，应降低风险敞口。",
    ),
    (
        "free text with 卖出",
        "强烈建议卖出该股票，止损离场。当前形势不乐观。",
    ),
    (
        "free text with hold in English context",
        "We recommend to hold the current position and wait for better entry point. The market is uncertain.",
    ),
    (
        "structured with Hold but text says 减持",
        "**Rating**: Hold\n\n**Executive Summary**: 建议减持，降低仓位\n\n**Investment Thesis**: 虽然评级为持有，但建议逐步减仓",
    ),
    (
        "BYD case from log",
        "**Rating**: Hold\n\n**Executive Summary**: 比亚迪002594评级为 Hold。长期配置逻辑成立（前向PE 21.3倍、历史低位；账上757亿现金+经营现金流591亿为硬实力防线；FY2026 EPS CAGR 约25%），但4月销量下滑26%、北向外资系统性撤退、T+1制度下止损机制失效率三大短期风险尚未完全释放，当前99元一线并非理想重仓窗口。建议以不超过20%总仓位建立底仓（等待回踩97-98元支撑确认后轻仓），严格止损设于95元下方；加仓条件：①股价放量突破102元站稳 AND ②月度销量环比改善≥10%；目标价105元（第一目标）/117元（第二目标），持有期6-12个月。\n\n**Investment Thesis**: 多空辩论综合裁决：①估值方向有利（PE 21.3倍/PEG 0.86）但FY2026 EPS预测分歧±43%，不可作为单一锚点；②销量下滑26%已非季节性因素，渗透率红利期结束，结构性价格战压力持续，基本面拐点尚需等待月销环比改善信号确认；③内部人增持（社保/高管）和外资撤退形成资金面对峙，但T+1制度使止损机制在A股高波动环境下实效化，倒逼更保守的初始仓位；④技术面RSI 47处于中性偏低区域而非超卖，MACD仍在零轴下方，均线死叉3次，短期趋势反转条件尚未齐备。综合来看，方向正确但时机未成熟，应以底仓控险+等信号加仓的滚动策略应对，避免在信号不完整时重仓承受T+1隔夜敞口。",
    ),
]

print("=" * 80)
print(f"{'Case':<45} {'OLD':<15} {'NEW':<15}")
print("=" * 80)
for name, text in real_cases:
    old = parse_rating_old(text)
    new = parse_rating_new(text)
    changed = " <-- CHANGED" if old != new else ""
    print(f"  {name:<43} {old:<15} {new:<15}{changed}")
