#!/usr/bin/env python3
"""Diagnose fpdf2 font loading failure."""

import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import fpdf
print(f"fpdf2 version: {fpdf.__version__}")

otf_path = Path.home() / ".tradingagents" / "fonts" / "NotoSansCJKsc-Regular.otf"
print(f"\nFont file: {otf_path}")
print(f"Exists: {otf_path.exists()}")
print(f"Size: {otf_path.stat().st_size:,} bytes")

print("\n--- Test 1: add_font with OTF ---")
try:
    pdf = fpdf.FPDF()
    pdf.add_font("CJK", "", str(otf_path), uni=True)
    print("add_font Regular: OK")
except Exception as e:
    print(f"add_font Regular: FAILED")
    traceback.print_exc()

print("\n--- Test 2: add_font with uni=True ---")
try:
    pdf2 = fpdf.FPDF()
    pdf2.add_font("TestFont", "", str(otf_path))
    print("add_font without uni: OK")
except Exception as e:
    print(f"add_font without uni: FAILED")
    traceback.print_exc()

print("\n--- Test 3: Check if font is CFF or TrueType ---")
try:
    with open(otf_path, "rb") as f:
        header = f.read(4)
        print(f"File header bytes: {header.hex()}")
        if header == b'OTTO':
            print("Font type: CFF-based OpenType (OTF) - may not be supported by older fpdf2")
        elif header[:2] == b'\x00\x01':
            print("Font type: TrueType")
        elif header == b'ttcf':
            print("Font type: TrueType Collection (TTC)")
        else:
            print(f"Font type: Unknown ({header})")
except Exception as e:
    print(f"Header check failed: {e}")

print("\n--- Test 4: Try wqy-zenhei.ttc ---")
wqy_path = Path("/usr/share/fonts/wqy-zenhei-fonts/wqy-zenhei.ttc")
if wqy_path.exists():
    try:
        pdf3 = fpdf.FPDF()
        pdf3.add_font("WQY", "", str(wqy_path), uni=True)
        print(f"add_font wqy-zenhei.ttc: OK")
    except Exception as e:
        print(f"add_font wqy-zenhei.ttc: FAILED - {e}")
else:
    print("wqy-zenhei.ttc not found")

print("\n" + "=" * 70)
