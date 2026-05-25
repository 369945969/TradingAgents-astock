#!/usr/bin/env python3
"""Diagnose CJK font availability on the server."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from web.pdf_export import (
    _find_cjk_font_paths,
    _try_load_font,
    _download_cjk_font,
    _CACHED_FONT_REGULAR,
    _CACHED_FONT_BOLD,
)

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

print("\nCached font files:")
print(f"  Regular: {_CACHED_FONT_REGULAR} (exists={_CACHED_FONT_REGULAR.exists()})")
print(f"  Bold:    {_CACHED_FONT_BOLD} (exists={_CACHED_FONT_BOLD.exists()})")

if not _CACHED_FONT_REGULAR.exists():
    print("\nTrying auto-download from GitHub...")
    result = _download_cjk_font()
    if result:
        print(f"  Downloaded to: {result}")
        print(f"  Regular size: {_CACHED_FONT_REGULAR.stat().st_size:,} bytes")
        if _CACHED_FONT_BOLD.exists():
            print(f"  Bold size:    {_CACHED_FONT_BOLD.stat().st_size:,} bytes")
        ok = _try_load_font(result)
        print(f"  Load test: {'OK' if ok else 'FAIL'}")
    else:
        print("  Download failed!")
        print("  Manual fix: run these commands on the server:")
        print(f"    mkdir -p {Path.home() / '.tradingagents' / 'fonts'}")
        print(f"    wget -O {_CACHED_FONT_REGULAR} https://raw.githubusercontent.com/notofonts/noto-cjk/main/Sans/OTF/SimplifiedChinese/NotoSansCJKsc-Regular.otf")
        print(f"    wget -O {_CACHED_FONT_BOLD} https://raw.githubusercontent.com/notofonts/noto-cjk/main/Sans/OTF/SimplifiedChinese/NotoSansCJKsc-Bold.otf")
else:
    print(f"\nCached font already exists ({_CACHED_FONT_REGULAR.stat().st_size:,} bytes)")
    ok = _try_load_font(str(_CACHED_FONT_REGULAR))
    print(f"  Load test: {'OK' if ok else 'FAIL'}")

print("\n" + "=" * 70)
