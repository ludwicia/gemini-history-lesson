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
characters = json.loads(match.group(1))

# Extract all names currently in database
existing_names_map = {}
for c in characters:
    cname = c["chinese_name"]
    existing_names_map[cname] = c
    clean = re.sub(r'（.*?）|\(.*?\)', '', cname).strip()
    existing_names_map[clean] = c
    if c.get("english_name"):
        existing_names_map[c["english_name"].strip().lower()] = c

print(f"Total current database characters: {len(characters)}")

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

# Scan all markdown texts for person names
# We extract all instances of name matches and human titles
candidates_dict = {}

title_keywords = [
    "皇帝", "將領", "教宗", "國王", "親王", "執政官", "總督", "大主教", "修道院長",
    "神父", "神學家", "歷史學家", "學者", "首領", "公爵", "伯爵", "刺客", "哲學家",
    "將領", "羅馬將領", "哥德首領", "法蘭克國王", "法官", "起事者"
]

for pid, info in europe_pages.items():
    fpath = os.path.join(r"c:\Users\USER\gemini的簡單歷史課", info["file_path"])
    if not os.path.exists(fpath):
        continue
    with open(fpath, "r", encoding="utf-8") as f:
        text = f.read()

    # Find patterns like Name (EngName) or Title Name (EngName)
    matches = re.finditer(r'([\u4e00-\u9fa5·•\s]+)[（\(]([A-Za-z0-9\s\.\,\-\'\:\;\&]+)[）\)]', text)
    for m in matches:
        cn_part = m.group(1).strip()
        en_part = m.group(2).strip()

        # Check if en_part is capitalized like a name (e.g. John Doe, Flavius Victor)
        words = en_part.split()
        if not words or len(words) > 5:
            continue
        # If words look like acronyms or non-capitalized terms, skip
        if not all(w[0].isupper() or w in ["de", "van", "von", "the", "of", "and", "la", "der", "du", "d'"] for w in words):
            continue

        # Clean cn_part: extract title and actual name
        name_clean = cn_part
        found_title = ""
        for tk in title_keywords:
            if tk in name_clean:
                found_title = tk
                idx = name_clean.rfind(tk) + len(tk)
                if idx < len(name_clean):
                    name_clean = name_clean[idx:].strip()

        name_clean = re.sub(r'^[與和及同從對在位時的等於到]', '', name_clean).strip()

        if len(name_clean) < 2 or len(name_clean) > 12:
            continue

        # Check if already in database
        if name_clean in existing_names_map or en_part.lower() in existing_names_map:
            continue

        if name_clean not in candidates_dict:
            candidates_dict[name_clean] = {
                "chinese_name": name_clean,
                "english_name": en_part,
                "title_hint": found_title,
                "occurrences": []
            }
        candidates_dict[name_clean]["occurrences"].append({
            "page_id": pid,
            "title": info["title"],
            "raw": m.group(0)
        })

print(f"\nExtracted {len(candidates_dict)} potential new person candidates from markdown parens:\n")
for name, data in candidates_dict.items():
    pids = list({occ["page_id"] for occ in data["occurrences"]})
    titles = list({occ["title"] for occ in data["occurrences"]})
    raw_sample = data["occurrences"][0]["raw"]
    print(f"Candidate: {name} | Eng: {data['english_name']} | Pages: {pids}")
    print(f"  Raw Match: {raw_sample}")
    print(f"  Articles: {', '.join(titles)}\n")
