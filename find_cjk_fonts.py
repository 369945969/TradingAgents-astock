import sys
from pathlib import Path

search_dirs = ["/usr/share/fonts", "/usr/local/share/fonts"]
cjk_keywords = ("cjk", "sans-sc", "pingfang", "heiti", "songti", "wqy", "wenquanyi", "droid", "notosanssc", "notoserifsc")

print("Searching for CJK fonts...")
print("=" * 80)

found = []
for search_dir in search_dirs:
    search_path = Path(search_dir)
    if not search_path.exists():
        print(f"  [SKIP] {search_dir} does not exist")
        continue
    for ext in ("*.ttf", "*.ttc", "*.otf"):
        for f in search_path.rglob(ext):
            name_lower = f.name.lower()
            is_cjk = any(kw in name_lower for kw in cjk_keywords)
            if is_cjk:
                found.append(str(f))
                print(f"  [CJK]  {f}")
            elif "noto" in name_lower:
                print(f"  [NOTO] {f}  (not CJK)")

if not found:
    print("\nNo CJK fonts found! Checking all available fonts:")
    for search_dir in search_dirs:
        search_path = Path(search_dir)
        if not search_path.exists():
            continue
        for ext in ("*.ttf", "*.ttc", "*.otf"):
            for f in sorted(search_path.rglob(ext)):
                print(f"  {f}")
else:
    print(f"\nFound {len(found)} CJK font(s)")
