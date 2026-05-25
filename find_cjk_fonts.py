#!/usr/bin/env python3
"""Diagnose CJK font availability on the server."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from web.pdf_export import _find_cjk_font_paths, _try_load_font, _download_cjk_font

print("=" * 70)
print("CJK Font Diagnosis")
print("=" * 70)

paths = _find_cjk_font_paths()
print(f"\nFound {len(paths)} candidate font(s):")
for p in paths:
    print(f"  {p}")

print("\nTesting each font with fpdf2:")
for p in paths:
    ok = _try_load_font(p)
    status = "OK" if ok else "FAIL"
    print(f"  [{status}] {p}")

print("\nTrying auto-download:")
result = _download_cjk_font()
if result:
    print(f"  Downloaded to: {result}")
    ok = _try_load_font(result)
    print(f"  Load test: {'OK' if ok else 'FAIL'}")
else:
    print("  Download failed - server may not have internet access")
    print("  Manual fix: download NotoSansSC-Regular.otf and save to:")
    print(f"  {Path.home() / '.tradingagents' / 'fonts' / 'NotoSansSC-Regular.otf'}")

print("\n" + "=" * 70)
