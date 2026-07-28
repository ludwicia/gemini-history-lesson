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

# Manual filter list for obvious non-persons
non_persons_words = [
    "協定", "同盟", "制度", "責任", "共和國", "殖民地", "協約", "指數", "法案",
    "憲法", "條約", "敕令", "危機", "醜聞", "微影", "資本", "大選", "指令", "公司",
    "大學", "城堡", "紀念日", "聯盟", "法院", "組織", "部隊", "保護區", "運動", "海灣",
    "比喻", "強盜", "莊園", "地主", "保護人", "贊助人", "極刑", "拷問鞭", "三位一體", "神性",
    "世紀", "年代", "戰役", "修道院", "帝國", "王國", "會規", "金璽詔書"
]

all_candidates = []

for pid, info in europe_pages.items():
    fpath = os.path.join(r"c:\Users\USER\gemini的簡單歷史課", info["file_path"])
    if not os.path.exists(fpath):
        continue
    with open(fpath, "r", encoding="utf-8") as f:
        text = f.read()

    # Pattern for names
    matches = re.finditer(r'([\u4e00-\u9fa5·•\s]{2,20})[（\(]([A-Za-z0-9\s\.\,\-\'\:\;\&]{2,40})[）\)]', text)
    for m in matches:
        cn_part = m.group(1).strip()
        en_part = m.group(2).strip()

        words = en_part.split()
        if len(words) > 5:
            continue

        # Check if english name looks like a proper name
        if not all(w[0].isupper() or w in ["de", "van", "von", "the", "of", "and", "la", "der", "du", "d'", "di"] for w in words):
            continue

        if any(w in cn_part for w in non_persons_words):
            continue

        # Clean prefix text like "將領馬略" -> "馬略"
        prefixes = [
            "將領", "皇帝", "教宗", "國王", "親王", "執政官", "總督", "大主教", "修道院長",
            "神父", "神學家", "歷史學家", "學者", "首領", "公爵", "伯爵", "刺客", "哲學家",
            "羅馬將領", "哥德首領", "法蘭克國王", "法官", "起事者", "先驅", "畫家", "教育家",
            "學者", "生物學家", "法學家", "出版家", "物理學家", "天文學家", "長官", "指揮官",
            "領袖", "總督", "聖徒", "使徒", "叛亂者", "副將", "近衛軍長官"
        ]

        cname = cn_part
        for pfix in prefixes:
            if pfix in cname:
                idx = cname.rfind(pfix) + len(pfix)
                if idx < len(cname):
                    cname = cname[idx:].strip()

        cname = re.sub(r'^[與和及同從對在位時的等於到]', '', cname).strip()

        if len(cname) < 2 or len(cname) > 12:
            continue

        if cname in existing_cnames or en_part.lower() in existing_enames:
            continue

        all_candidates.append({
            "cname": cname,
            "ename": en_part,
            "page_id": pid,
            "article_title": info["title"]
        })

# Group candidates
grouped_cand = {}
for item in all_candidates:
    cn = item["cname"]
    if cn not in grouped_cand:
        grouped_cand[cn] = {
            "cname": cn,
            "ename": item["ename"],
            "sources": []
        }
    if not any(s["page_id"] == item["page_id"] for s in grouped_cand[cn]["sources"]):
        grouped_cand[cn]["sources"].append({
            "page_id": item["page_id"],
            "title": item["article_title"]
        })

output_file = r"c:\Users\USER\gemini的簡單歷史課\scratch\candidates_all.json"
os.makedirs(os.path.dirname(output_file), exist_ok=True)
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(grouped_cand, f, ensure_ascii=False, indent=2)

print(f"Successfully saved {len(grouped_cand)} candidates to {output_file}")
