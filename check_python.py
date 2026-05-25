#!/usr/bin/env python3
import sys
print(f"Python: {sys.executable}")
print(f"Version: {sys.version}")

try:
    import fpdf
    print(f"fpdf location: {fpdf.__file__}")
    print(f"fpdf version: {fpdf.__version__}")
except Exception as e:
    print(f"fpdf import error: {e}")

try:
    import fpdf2
    print(f"fpdf2: {fpdf2.__file__}")
except ImportError:
    print("fpdf2 package not importable (normal - fpdf2 uses 'fpdf' as import name)")

try:
    from fpdf import FPDF
    pdf = FPDF()
    pdf.add_font("Test", "", "/root/.tradingagents/fonts/NotoSansCJKsc-Regular.otf")
    print("Font load: OK!")
except Exception as e:
    print(f"Font load: FAILED - {e}")
