#!/usr/bin/env python3
"""Test PDF generation with CJK font support."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from fpdf import FPDF


def find_cjk_font():
    candidates = [
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/STHeiti Light.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansSC-Regular.ttf",
        "/usr/share/fonts/noto-cjk/NotoSansCJKsc-Regular.otf",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/google-noto-cjk/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/noto-sans-cjk/NotoSansCJK-Regular.ttc",
    ]
    for path in candidates:
        if Path(path).exists():
            print(f"[OK] Found CJK font: {path}")
            return path
    for search_dir in ["/usr/share/fonts", "/usr/local/share/fonts", "/System/Library/Fonts"]:
        search_path = Path(search_dir)
        if not search_path.exists():
            continue
        for ext in ("*.ttf", "*.ttc", "*.otf"):
            for f in search_path.rglob(ext):
                name_lower = f.name.lower()
                if any(kw in name_lower for kw in ("cjk", "noto", "sans-sc", "pingfang", "heiti", "songti", "wqy", "wenquanyi", "droid")):
                    print(f"[OK] Found CJK font (search): {f}")
                    return str(f)
    print("[WARN] No CJK font found!")
    return None


def test_pdf():
    font_path = find_cjk_font()
    has_cjk = font_path is not None

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=20)

    if has_cjk:
        pdf.add_font("CJK", "", font_path, uni=True)
        pdf.add_font("CJK", "B", font_path, uni=True)

    def use_font(style="", size=10):
        if has_cjk:
            pdf.set_font("CJK", style, size)
        else:
            pdf.set_font("Helvetica", style, size)

    # Page 1: Cover
    pdf.add_page()
    pdf.ln(60)
    use_font("B", 24)
    pdf.set_text_color(255, 90, 31)
    pdf.cell(0, 12, "A股多Agent投研分析报告", align="C")
    pdf.ln(20)

    use_font("B", 36)
    pdf.set_text_color(30, 30, 30)
    pdf.cell(0, 18, "300750", align="C")
    pdf.ln(16)

    use_font("", 14)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 10, "分析日期: 2026-05-25", align="C")
    pdf.ln(8)
    pdf.cell(0, 10, "生成时间: 2026-05-25 21:30", align="C")
    pdf.ln(20)

    use_font("B", 40)
    pdf.set_text_color(34, 197, 94)
    pdf.cell(0, 20, "BUY", align="C")
    pdf.ln(20)

    use_font("", 9)
    pdf.set_text_color(120, 120, 120)
    pdf.multi_cell(
        0, 5,
        "免责声明: 本报告由 AI 多 Agent 系统自动生成, 仅供学习研究与技术演示, "
        "不构成任何投资建议。投资决策请咨询持牌专业机构。"
        "使用本报告所产生的任何损失由使用者自行承担。",
        align="C",
    )

    # Page 2: Section with markdown content
    pdf.add_page()
    use_font("B", 16)
    pdf.set_text_color(255, 90, 31)
    pdf.cell(0, 10, "技术分析报告")
    pdf.ln(12)

    test_content = """## 技术指标分析

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
"""

    lines = test_content.split("\n")
    for line in lines:
        stripped = line.strip()
        if not stripped:
            pdf.ln(3)
            continue
        if stripped.startswith("###"):
            use_font("B", 11)
            pdf.set_text_color(50, 50, 50)
            pdf.multi_cell(0, 7, stripped.lstrip("#").strip())
            pdf.ln(4)
        elif stripped.startswith("##"):
            use_font("B", 13)
            pdf.set_text_color(40, 40, 40)
            pdf.multi_cell(0, 8, stripped.lstrip("#").strip())
            pdf.ln(4)
        elif stripped.startswith("#"):
            use_font("B", 14)
            pdf.set_text_color(255, 90, 31)
            pdf.multi_cell(0, 9, stripped.lstrip("#").strip())
            pdf.ln(4)
        elif stripped in ("---", "***", "___"):
            pdf.set_draw_color(180, 180, 180)
            y = pdf.get_y() + 2
            pdf.line(10, y, pdf.w - 10, y)
            pdf.ln(6)
        elif stripped.startswith("|") and stripped.endswith("|"):
            import re
            if re.match(r"^\|[-:\s|]+\|$", stripped):
                continue
            use_font("", 8)
            pdf.set_text_color(60, 60, 60)
            cells = [c.strip() for c in stripped.strip("|").split("|")]
            row_text = "  |  ".join(cells)
            pdf.multi_cell(0, 4.5, row_text)
        elif stripped.startswith("- ") or stripped.startswith("* "):
            use_font("", 10)
            pdf.set_text_color(40, 40, 40)
            pdf.multi_cell(0, 5.5, "  •  " + stripped[2:].strip())
        elif len(stripped) > 2 and stripped[0].isdigit() and ". " in stripped[:5]:
            use_font("", 10)
            pdf.set_text_color(40, 40, 40)
            pdf.multi_cell(0, 5.5, "  " + stripped)
        else:
            use_font("", 10)
            pdf.set_text_color(40, 40, 40)
            pdf.multi_cell(0, 5.5, stripped)
            pdf.ln(2)

    output_path = Path(__file__).resolve().parent / "test_pdf_output.pdf"
    pdf.output(str(output_path))
    print(f"[OK] PDF generated: {output_path}")
    print(f"[OK] File size: {output_path.stat().st_size} bytes")


if __name__ == "__main__":
    test_pdf()
