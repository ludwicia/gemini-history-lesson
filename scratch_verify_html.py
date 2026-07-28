import json
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

html_path = r"c:\Users\USER\gemini的簡單歷史課\characters_database.html"

with open(html_path, "r", encoding="utf-8") as f:
    content = f.read()

match = re.search(r'const\s+rawCharacters\s*=\s*(\[\s*\{.*?\n\s*\]);', content, re.DOTALL)
if not match:
    print("Verification Error: rawCharacters array pattern not matched!")
    sys.exit(1)

try:
    chars = json.loads(match.group(1))
    print(f"Verification Success: Successfully parsed JSON with {len(chars)} characters.")
except Exception as e:
    print(f"Verification Error: JSON parse error - {e}")
    sys.exit(1)

# Check required fields for each character
required_fields = ["chinese_name", "english_name", "birth_death", "epithet", "noble_title", "birth_year_num", "category", "sources"]
categories_count = {}
missing_field_count = 0

for idx, c in enumerate(chars):
    for rf in required_fields:
        if rf not in c:
            print(f"Char at index {idx} ({c.get('chinese_name')}) missing field: {rf}")
            missing_field_count += 1
    cat = c.get("category", "unknown")
    categories_count[cat] = categories_count.get(cat, 0) + 1

if missing_field_count == 0:
    print("All characters have complete required fields!")

print("\nCategory Distribution:")
for cat, count in sorted(categories_count.items()):
    print(f"  {cat}: {count} characters")
