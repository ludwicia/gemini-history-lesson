import json
import re
import os

html_path = r"c:\Users\USER\gemini的簡單歷史課\characters_database.html"
config_path = r"c:\Users\USER\gemini的簡單歷史課\course_config.json"

with open(html_path, "r", encoding="utf-8") as f:
    html_content = f.read()

# Extract rawCharacters
match = re.search(r'const\s+rawCharacters\s*=\s*(\[\s*\{.*?\n\s*\]);', html_content, re.DOTALL)
if not match:
    print("Failed to find rawCharacters JSON")
    exit(1)

json_str = match.group(1)
try:
    characters = json.loads(json_str)
    print(f"Total existing characters in database: {len(characters)}")
except Exception as e:
    print("JSON parse error:", e)
    exit(1)

with open(config_path, "r", encoding="utf-8") as f:
    config = json.load(f)

articles = config.get("articles", {})
categories = config.get("categories", [])

# European categories filter
# Exclude us (page02, page13), qing (page36), novel (page42, page43)
non_europe_categories = {"us", "qing", "novel"}
europe_pages = {}

for cat in categories:
    if cat["key"] not in non_europe_categories:
        for page_id in cat["pages"]:
            if page_id in articles:
                europe_pages[page_id] = articles[page_id]

print(f"Total European articles count: {len(europe_pages)}")
for pid, info in europe_pages.items():
    print(f"  {pid}: {info['title']} ({info['file_path']})")
