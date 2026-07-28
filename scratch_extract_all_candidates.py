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

existing_cnames = set()
existing_enames = set()

for c in characters:
    existing_cnames.add(c["chinese_name"])
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

# Words that indicate non-person entities
exclude_terms = {
    "戰役", "敕令", "條約", "帝國", "王國", "修道院", "教會", "學派", "主義",
    "海峽", "行省", "河流", "山脈", "防線", "協約", "金璽詔書", "會規", "憲法",
    "法案", "宣言", "危機", "叛亂", "歷史", "世紀", "年代", "文獻", "羅馬",
    "哥德", "波斯", "法蘭克", "日耳曼", "薩珊", "近東", "地中海", "萊茵", "多瑙",
    "神學", "哲學", "文化", "藝術", "雕像", "遺址", "城市", "首都", "城堡",
    "教堂", "議會", "公司", "東印度公司", "銀行", "條例", "詔書", "比喻", "法案",
    "首領", "將領", "皇帝", "教宗", "國王", "總督", "騎士", "貴族", "奴隸", "釋奴",
    "強盜", "莊園", "地主", "保護人", "贊助人", "極刑", "拷問鞭", "三位一體", "神性"
}

all_found = []

for pid, info in europe_pages.items():
    fpath = os.path.join(r"c:\Users\USER\gemini的簡單歷史課", info["file_path"])
    if not os.path.exists(fpath):
        continue
    with open(fpath, "r", encoding="utf-8") as f:
        text = f.read()

    # Pattern: 名字 (English Name) or 名字（English Name）
    # Examples: 馬略 (Marius), 腓力斯 (Antonius Felix), 保羅 (Paul the Apostle), 歐瑟伯 (Eusebius)
    pattern = r'([\u4e00-\u9fa5·•a-zA-Z0-9\s-]+)[（\(]([A-Za-z0-9\s\.\,\-\'\:\;\&]+)[）\)]'
    matches = re.finditer(pattern, text)
    for m in matches:
        raw_cname = m.group(1).strip().replace('*', '').replace('`', '')
        raw_ename = m.group(2).strip().replace('*', '').replace('`', '')

        # Clean prefix text if any
        # e.g., "將領馬略" -> "馬略"
        # Find if raw_cname has clean name at the end
        cname = raw_cname
        # Remove common descriptors at start if long
        prefixes = ["將領", "皇帝", "教宗", "總督", "國王", "使徒", "聖人", "執政官", "歷史學家", "學者", "修道院長", "公爵", "伯爵", "大主教", "神父"]
        for pfix in prefixes:
            if cname.startswith(pfix) and len(cname) > len(pfix):
                cname = cname[len(pfix):].strip()

        if not cname or not raw_ename:
            continue

        if any(term in cname for term in exclude_terms):
            continue

        if cname in existing_cnames or raw_ename.lower() in existing_enames:
            continue

        # Check if english name looks like a person's name (starts with Capital, max ~4 words)
        words = raw_ename.split()
        if len(words) > 5 or len(cname) > 15:
            continue

        all_found.append({
            "cname": cname,
            "ename": raw_ename,
            "pid": pid,
            "article_title": info["title"],
            "raw_match": m.group(0)
        })

# Group by candidate cname
grouped = {}
for entry in all_found:
    cn = entry["cname"]
    if cn not in grouped:
        grouped[cn] = {
            "cname": cn,
            "ename": entry["ename"],
            "pages": set(),
            "article_titles": set()
        }
    grouped[cn]["pages"].add(entry["pid"])
    grouped[cn]["article_titles"].add(entry["article_title"])

print(f"Total potential new character candidates: {len(grouped)}\n")
for cn, data in sorted(grouped.items(), key=lambda x: len(x[1]["pages"]), reverse=True):
    print(f"Name: {cn} | Eng: {data['ename']} | Pages: {list(data['pages'])}")
    print(f"  Articles: {', '.join(data['article_titles'])}")
