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

# Existing names and english names
existing_cnames = set()
existing_enames = set()

for c in characters:
    existing_cnames.add(c["chinese_name"])
    # clean name
    clean = re.sub(r'（.*?）|\(.*?\)', '', c["chinese_name"]).strip()
    existing_cnames.add(clean)
    if c.get("english_name"):
        existing_enames.add(c["english_name"].strip().lower())

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

# Scan patterns in markdown text:
# e.g., 中文名 (English Name) or 名字 followed by years / titles
# Patterns like: `譯名（English Name）`, `譯名 (English Name)`
potential_new = {}

for pid, info in europe_pages.items():
    fpath = os.path.join(r"c:\Users\USER\gemini的簡單歷史課", info["file_path"])
    if not os.path.exists(fpath):
        continue
    with open(fpath, "r", encoding="utf-8") as f:
        text = f.read()

    # Find patterns like Name (EngName) or Name（EngName）
    matches = re.findall(r'([\u4e00-\u9fa5·•a-zA-Z0-9\s-]+)[（\(]([A-Za-z0-9\s\.\,\-\'\:\;\&]+)[）\)]', text)
    for cname, ename in matches:
        cname = cname.strip()
        ename = ename.strip()
        # Clean markdown formatting like ** or *
        cname = cname.replace('*', '').replace('`', '').strip()
        ename = ename.replace('*', '').replace('`', '').strip()

        if not cname or not ename:
            continue

        # Ignore place names, terms, book names, etc.
        # Filter if cname or ename in existing
        if cname in existing_cnames or ename.lower() in existing_enames:
            continue

        # Also filter out obviously non-person terms (e.g. battles, edicts, places, organizations)
        non_person_keywords = [
            '戰役', '敕令', '條約', '帝國', '王國', '修道院', '教會', '派', '學派', '主義',
            '海峽', '行省', '行省治權', '河流', '山脈', '防線', '協約', '金璽詔書', '會規',
            '憲法', '法案', '宣言', '危機', '叛亂', '歷史', '世紀', '年', '代', '文獻',
            '羅馬', '哥德', '波斯', '法蘭克', '日耳曼', '薩珊', '近東', '地中海', '萊茵', '多瑙',
            'Battle', 'Edict', 'Treaty', 'Empire', 'Kingdom', 'Monastery', 'Church', 'Edict',
            'Pax', 'Lex', 'Consul', 'Augustus', 'Caesar', 'Codex', 'Res', 'Via'
        ]

        is_term = False
        for kw in non_person_keywords:
            if kw in cname or kw in ename:
                is_term = True
                break
        if is_term:
            continue

        # Keep track of occurrences
        if cname not in potential_new:
            potential_new[cname] = {
                "chinese_name": cname,
                "english_name": ename,
                "pages": set(),
                "sample_context": []
            }
        potential_new[cname]["pages"].add(pid)

        # Extract a snippet around this occurrence for inspection
        idx = text.find(cname)
        if idx != -1:
            snippet = text[max(0, idx-40):min(len(text), idx+100)].replace('\n', ' ')
            potential_new[cname]["sample_context"].append(snippet)

print(f"Found {len(potential_new)} potential candidate names with English terms in parens.")
print("\nSample potential names:")
count = 0
for cname, item in potential_new.items():
    p_str = ", ".join(item["pages"])
    print(f"Candidate: {cname} | Eng: {item['english_name']} | Pages: {p_str}")
    if item["sample_context"]:
        print(f"  Context: {item['sample_context'][0]}")
    count += 1
    if count >= 60:
        print("... (more entries truncated)")
        break
