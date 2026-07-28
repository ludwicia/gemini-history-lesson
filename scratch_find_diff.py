import json
import re
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

html_path = r"c:\Users\USER\gemini的簡單歷史課\characters_database.html"
config_path = r"c:\Users\USER\gemini的簡單歷史課\course_config.json"

with open(html_path, "r", encoding="utf-8") as f:
    html_content = f.read()

match = re.search(r'const\s+rawCharacters\s*=\s*(\[\s*\{.*?\n\s*\]);', html_content, re.DOTALL)
if not match:
    print("Error: rawCharacters not found")
    sys.exit(1)

characters = json.loads(match.group(1))

with open(config_path, "r", encoding="utf-8") as f:
    config = json.load(f)

articles = config.get("articles", {})
categories = config.get("categories", [])

non_europe_categories = {"us", "qing", "novel"}
europe_pages = {}

for cat in categories:
    if cat["key"] not in non_europe_categories:
        for page_id in cat["pages"]:
            if page_id in articles:
                europe_pages[page_id] = articles[page_id]

# Load markdown files content
article_texts = {}
for pid, info in europe_pages.items():
    fpath = os.path.join(r"c:\Users\USER\gemini的簡單歷史課", info["file_path"])
    if os.path.exists(fpath):
        with open(fpath, "r", encoding="utf-8") as f:
            article_texts[pid] = {
                "title": info["title"],
                "file_path": info["file_path"],
                "content": f.read()
            }
    else:
        print(f"Warning: File not found {fpath}")

print(f"Loaded {len(article_texts)} European article files.")

# Step 1: Check source completeness for existing characters
missing_sources_count = 0
updated_characters = []

for char in characters:
    c_name = char["chinese_name"]
    # Handle names with parens or aliases if needed, e.g. "君士坦丁一世" vs "君士坦丁"
    # Basic search name variants
    search_names = [c_name]
    # Remove parenthetical epithets/titles if present, e.g., "奧托一世（大帝）" -> "奧托一世", "奧托"
    clean_name = re.sub(r'（.*?）|\(.*?\)', '', c_name).strip()
    if clean_name != c_name:
        search_names.append(clean_name)

    # Also if name has multi-part like "蓋烏斯·儒略·凱撒", extract "凱撒" or "儒略·凱撒"
    parts = clean_name.split('·')

    current_source_ids = {s["page_id"] for s in char.get("sources", [])}
    new_sources = list(char.get("sources", []))

    for pid, a_info in article_texts.items():
        if pid in current_source_ids:
            continue
        text = a_info["content"]
        # Check if any search_name is in text
        found = False
        for sname in search_names:
            if sname in text:
                found = True
                break

        # If not found directly, for names like "弗里蒂根 (Fritigern)", check english_name
        if not found and char.get("english_name"):
            eng = char["english_name"].strip()
            if len(eng) > 3 and eng in text:
                found = True

        if found:
            new_sources.append({
                "page_id": pid,
                "title": a_info["title"]
            })
            missing_sources_count += 1
            print(f"[Missing Source Found] Character '{c_name}' appears in {pid} ({a_info['title']})")

    # Sort sources by page_id number if possible
    def get_pid_num(s):
        m = re.search(r'\d+', s["page_id"])
        return int(m.group(0)) if m else 999
    new_sources.sort(key=get_pid_num)
    char["sources"] = new_sources

print(f"\nTotal missing sources references auto-detected: {missing_sources_count}")
