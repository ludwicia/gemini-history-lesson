import json
import re
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

html_path = r"c:\Users\USER\gemini的簡單歷史課\characters_database.html"

with open(html_path, "r", encoding="utf-8") as f:
    html_content = f.read()

match = re.search(r'const\s+rawCharacters\s*=\s*(\[\s*\{.*?\n\s*\]);', html_content, re.DOTALL)
if not match:
    print("Error parsing HTML")
    sys.exit(1)

existing_chars = json.loads(match.group(1))

# Helper to find character by chinese_name or alias
def find_char(name):
    for c in existing_chars:
        if c["chinese_name"] == name:
            return c
        if re.sub(r'（.*?）|\(.*?\)', '', c["chinese_name"]).strip() == name:
            return c
    return None

# List of missing sources to add to existing characters
missing_sources_map = {
    "大希律王": [{"page_id": "page18", "title": "西元紀年的確立與演進"}],
    "蓋塔": [{"page_id": "page29", "title": "阿德里安堡戰役"}, {"page_id": "page34", "title": "匈人的登場與晚期羅馬地緣政治"}],
    "戴克里先": [{"page_id": "page44", "title": "羅馬與波斯地緣關係"}, {"page_id": "page45", "title": "費爾穆斯叛亂與北非防務危機"}],
    "伽列里烏斯": [{"page_id": "page44", "title": "羅馬與波斯地緣關係"}],
    "君士坦丁一世": [
        {"page_id": "page09", "title": "丕平獻土與教宗國誕生"},
        {"page_id": "page26", "title": "阿拉里克與哥德大遷徙"},
        {"page_id": "page40", "title": "萊茵河－多瑙河地緣戰略"},
        {"page_id": "page41", "title": "君士坦丁三世與五世紀初邊疆危機"},
        {"page_id": "page46", "title": "阿薩納里克家族與特爾文吉哥德人的統治演變"}
    ],
    "瓦倫斯": [
        {"page_id": "page44", "title": "羅馬與波斯地緣關係"},
        {"page_id": "page46", "title": "阿薩納里克家族與特爾文吉哥德人的統治演變"},
        {"page_id": "page47", "title": "瓦倫斯陣亡至迪奧多西接掌君士坦丁堡"}
    ],
    "尤利安": [{"page_id": "page44", "title": "羅馬與波斯地緣關係"}, {"page_id": "page45", "title": "費爾穆斯叛亂與北非防務危機"}],
    "狄奧多西一世": [
        {"page_id": "page44", "title": "羅馬與波斯地緣關係"},
        {"page_id": "page45", "title": "費爾穆斯叛亂與北非防務危機"},
        {"page_id": "page46", "title": "阿薩納里克家族與特爾文吉哥德人的統治演變"},
        {"page_id": "page47", "title": "瓦倫斯陣亡至迪奧多西接掌君士坦丁堡"}
    ],
    "奧古斯丁": [{"page_id": "page45", "title": "費爾穆斯叛亂與北非防務危機"}],
    "格拉提安": [
        {"page_id": "page44", "title": "羅馬與波斯地緣關係"},
        {"page_id": "page45", "title": "費爾穆斯叛亂與北非防務危機"},
        {"page_id": "page47", "title": "瓦倫斯陣亡至迪奧多西接掌君士坦丁堡"}
    ],
    "斯提里科": [{"page_id": "page45", "title": "費爾穆斯叛亂與北非防務危機"}],
    "阿拉里克一世": [{"page_id": "page46", "title": "阿薩納里克家族與特爾文吉哥德人的統治演變"}],
    "瓦倫提尼安二世": [
        {"page_id": "page38", "title": "阿陶爾夫與哥德大遷徙"},
        {"page_id": "page45", "title": "費爾穆斯叛亂與北非防務危機"},
        {"page_id": "page47", "title": "瓦倫斯陣亡至迪奧多西接掌君士坦丁堡"}
    ],
    "盧皮奇努斯": [{"page_id": "page44", "title": "羅馬與波斯地緣關係"}],
    "弗里蒂根": [
        {"page_id": "page44", "title": "羅馬與波斯地緣關係"},
        {"page_id": "page46", "title": "阿薩納里克家族與特爾文吉哥德人的統治演變"},
        {"page_id": "page47", "title": "瓦倫斯陣亡至迪奧多西接掌君士坦丁堡"}
    ],
    "阿薩納里克": [
        {"page_id": "page44", "title": "羅馬與波斯地緣關係"},
        {"page_id": "page46", "title": "阿薩納里克家族與特爾文吉哥德人的統治演變"},
        {"page_id": "page47", "title": "瓦倫斯陣亡至迪奧多西接掌君士坦丁堡"}
    ],
    "阿拉修斯": [
        {"page_id": "page44", "title": "羅馬與波斯地緣關係"},
        {"page_id": "page46", "title": "阿薩納里克家族與特爾文吉哥德人的統治演變"},
        {"page_id": "page47", "title": "瓦倫斯陣亡至迪奧多西接掌君士坦丁堡"}
    ],
    "利奧一世": [{"page_id": "page05", "title": "希爾紹修道院研究報告"}],
    "馬爾克揚": [{"page_id": "page25", "title": "羅馬晚期軍制變遷與哥德人崛起"}, {"page_id": "page29", "title": "阿德里安堡戰役"}],
    "阿波加斯特": [{"page_id": "page47", "title": "瓦倫斯陣亡至迪奧多西接掌君士坦丁堡"}],
    "巴庫里烏斯": [{"page_id": "page44", "title": "羅馬與波斯地緣關係"}],
    "吉爾多": [{"page_id": "page45", "title": "費爾穆斯叛亂與北非防務危機"}],
    "薩夫拉克": [
        {"page_id": "page44", "title": "羅馬與波斯地緣關係"},
        {"page_id": "page46", "title": "阿薩納里克家族與特爾文吉哥德人的統治演變"},
        {"page_id": "page47", "title": "瓦倫斯陣亡至迪奧多西接掌君士坦丁堡"}
    ],
    "弗拉維塔": [{"page_id": "page46", "title": "阿薩納里克家族與特爾文吉哥德人的統治演變"}],
    "教宗英諾森一世": [{"page_id": "page12", "title": "宗教戰爭(二)：卡特里派"}],
    "希爾德里克一世": [{"page_id": "page09", "title": "丕平獻土與教宗國誕生"}],
    "額我略五世": [{"page_id": "page05", "title": "希爾紹修道院研究報告"}],
    "亨利三世 (神聖羅馬帝國)": [{"page_id": "page07", "title": "奧托-薩利安帝國教會體制"}, {"page_id": "page14", "title": "英國憲法"}],
    "亨利三世 (英格蘭)": [{"page_id": "page07", "title": "奧托-薩利安帝國教會體制"}, {"page_id": "page14", "title": "英國憲法"}]
}

def get_pid_num(s):
    m = re.search(r'\d+', s["page_id"])
    return int(m.group(0)) if m else 999

updated_existing_count = 0
for name, add_sources in missing_sources_map.items():
    char = find_char(name)
    if char:
        current_pids = {s["page_id"] for s in char.get("sources", [])}
        changed = False
        for s in add_sources:
            if s["page_id"] not in current_pids:
                char.setdefault("sources", []).append(s)
                changed = True
        if changed:
            char["sources"].sort(key=get_pid_num)
            updated_existing_count += 1
            print(f"Updated sources for existing character: {name}")

print(f"\nTotal existing characters updated with missing sources: {updated_existing_count}")
