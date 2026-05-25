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

def parse_rating(text, default="Hold"):
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

test_cases = [
    ("**Rating**: Underweight", "Underweight"),
    ("**Rating**: Sell", "Sell"),
    ("**Rating**: Overweight", "Overweight"),
    ("**Rating**: Buy", "Buy"),
    ("**Rating**: Hold", "Hold"),
    ("Rating: **Underweight**", "Underweight"),
    ("rating - Underweight", "Underweight"),
    ("建议减持，仓位控制在30%", "Underweight"),
    ("建议卖出清仓", "Sell"),
    ("建议买入加仓", "Overweight"),
    ("建议持有观望", "Hold"),
    ("The hold position is recommended", "Hold"),
    ("We should hold for now but consider selling later", "Hold"),
    ("减持该股票", "Underweight"),
    ("建议减仓规避风险", "Underweight"),
    ("建议清仓止损", "Sell"),
    ("建议增持该标的", "Overweight"),
]

print("Testing parse_rating:")
print("=" * 70)
for text, expected in test_cases:
    result = parse_rating(text)
    status = "PASS" if result == expected else "FAIL"
    print(f"  [{status}] Input: {text[:50]:50s} => {result:15s} (expected: {expected})")

print()
print("Testing regex directly:")
for text, _ in test_cases:
    for line in text.splitlines():
        m = _RATING_LABEL_RE.search(line)
        if m:
            in_set = m.group(1).lower() in _RATING_SET
            print(f"  Regex: '{line[:40]}' => '{m.group(1)}' in_set={in_set}")
