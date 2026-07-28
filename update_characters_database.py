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

raw_json_str = match.group(1)
existing_chars = json.loads(raw_json_str)
print(f"Original characters count: {len(existing_chars)}")

# Helper to get PID number
def get_pid_num(s):
    m = re.search(r'\d+', s["page_id"])
    return int(m.group(0)) if m else 999

# Helper to find existing char
def find_char(name):
    for c in existing_chars:
        if c["chinese_name"] == name:
            return c
        if re.sub(r'（.*?）|\(.*?\)', '', c["chinese_name"]).strip() == name:
            return c
    return None

# 1. Missing sources update map
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

updated_sources_count = 0
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
            updated_sources_count += 1

print(f"Updated missing sources for {updated_sources_count} existing characters.")

# 2. New characters list
new_characters = [
    {
        "chinese_name": "馬略",
        "english_name": "Gaius Marius",
        "birth_death": "前 157 - 前 86",
        "epithet": "第三位羅馬救星",
        "noble_title": "羅馬共和國執政官 / 將領 (馬略改革)",
        "image_url": None,
        "sources": [{"page_id": "page33", "title": "一世紀羅馬行省治權與社會"}],
        "birth_year_num": -157,
        "category": "roman"
    },
    {
        "chinese_name": "安提帕特",
        "english_name": "Antipater the Idumean",
        "birth_death": "前 113 - 前 43",
        "epithet": "無",
        "noble_title": "以東裔政治家 / 猶大行政官 (大希律王之父)",
        "image_url": None,
        "sources": [{"page_id": "page33", "title": "一世紀羅馬行省治權與社會"}],
        "birth_year_num": -113,
        "category": "others"
    },
    {
        "chinese_name": "安提柯",
        "english_name": "Antigonus II Mattathias",
        "birth_death": "前 80 - 前 37",
        "epithet": "無",
        "noble_title": "哈斯蒙尼王朝最後一位猶太國王",
        "image_url": None,
        "sources": [{"page_id": "page33", "title": "一世紀羅馬行省治權與社會"}],
        "birth_year_num": -80,
        "category": "others"
    },
    {
        "chinese_name": "法薩伊",
        "english_name": "Phasael",
        "birth_death": "前 73 - 前 40",
        "epithet": "無",
        "noble_title": "耶路撒冷總督 / 猶大分封王 (大希律王之兄)",
        "image_url": None,
        "sources": [{"page_id": "page33", "title": "一世紀羅馬行省治權與社會"}],
        "birth_year_num": -73,
        "category": "others"
    },
    {
        "chinese_name": "龐提烏斯·彼拉多",
        "english_name": "Pontius Pilate",
        "birth_death": "活躍於 1 世紀 (約 26 - 36 在任)",
        "epithet": "無",
        "noble_title": "羅馬猶太行省第五任總督",
        "image_url": None,
        "sources": [{"page_id": "page33", "title": "一世紀羅馬行省治權與社會"}],
        "birth_year_num": 26,
        "category": "roman"
    },
    {
        "chinese_name": "迦流",
        "english_name": "Lucius Junius Gallio Annaean",
        "birth_death": "約 前 5 - 65",
        "epithet": "無",
        "noble_title": "羅馬亞該亞行省執政官 (哲學家塞內卡之兄)",
        "image_url": None,
        "sources": [{"page_id": "page33", "title": "一世紀羅馬行省治權與社會"}],
        "birth_year_num": -5,
        "category": "roman"
    },
    {
        "chinese_name": "腓力斯",
        "english_name": "Antonius Felix",
        "birth_death": "活躍於 1 世紀 (約 52 - 60 在任)",
        "epithet": "無",
        "noble_title": "羅馬騎士級猶太行省總督",
        "image_url": None,
        "sources": [{"page_id": "page33", "title": "一世紀羅馬行省治權與社會"}],
        "birth_year_num": 52,
        "category": "roman"
    },
    {
        "chinese_name": "非斯都",
        "english_name": "Porcius Festus",
        "birth_death": "活躍於 1 世紀 (約 60 - 62 在任)",
        "epithet": "無",
        "noble_title": "羅馬猶太行省總督",
        "image_url": None,
        "sources": [{"page_id": "page33", "title": "一世紀羅馬行省治權與社會"}],
        "birth_year_num": 60,
        "category": "roman"
    },
    {
        "chinese_name": "阿里亞里克",
        "english_name": "Ariaric",
        "birth_death": "活躍於 4 世紀早期 (約 332 前後)",
        "epithet": "無",
        "noble_title": "特爾文吉哥德人國王/首領",
        "image_url": None,
        "sources": [{"page_id": "page46", "title": "阿薩納里克家族與特爾文吉哥德人的統治演變"}],
        "birth_year_num": 332,
        "category": "germanic"
    },
    {
        "chinese_name": "奧里克",
        "english_name": "Aoric",
        "birth_death": "活躍於 4 世紀中期",
        "epithet": "無",
        "noble_title": "特爾文吉哥德人首領 (阿薩納里克之父)",
        "image_url": None,
        "sources": [{"page_id": "page46", "title": "阿薩納里克家族與特爾文吉哥德人的統治演變"}],
        "birth_year_num": 340,
        "category": "germanic"
    },
    {
        "chinese_name": "阿米阿努斯·馬爾塞利努斯",
        "english_name": "Ammianus Marcellinus",
        "birth_death": "約 330 - 400",
        "epithet": "無",
        "noble_title": "羅馬帝國晚期著名歷史學家 / 軍官",
        "image_url": None,
        "sources": [
            {"page_id": "page27", "title": "羅馬晚期地理斷裂與冷河戰役"},
            {"page_id": "page40", "title": "萊茵河－多瑙河地緣戰略"},
            {"page_id": "page47", "title": "瓦倫斯陣亡至迪奧多西接掌君士坦丁堡"}
        ],
        "birth_year_num": 330,
        "category": "roman"
    },
    {
        "chinese_name": "普羅柯比",
        "english_name": "Procopius",
        "birth_death": "326 - 366",
        "epithet": "無",
        "noble_title": "羅馬將領 / 帝位篡奪者 (君士坦丁王朝親族)",
        "image_url": None,
        "sources": [{"page_id": "page46", "title": "阿薩納里克家族與特爾文吉哥德人的統治演變"}],
        "birth_year_num": 326,
        "category": "roman"
    },
    {
        "chinese_name": "老狄奧多西",
        "english_name": "Theodosius the Elder",
        "birth_death": "卒於 376",
        "epithet": "無",
        "noble_title": "西羅馬步兵大元帥 / 狄奧多西一世之父",
        "image_url": None,
        "sources": [
            {"page_id": "page45", "title": "費爾穆斯叛亂與北非防務危機"},
            {"page_id": "page47", "title": "瓦倫斯陣亡至迪奧多西接掌君士坦丁堡"}
        ],
        "birth_year_num": 320,
        "category": "roman"
    },
    {
        "chinese_name": "阿爾比亞·多米尼卡",
        "english_name": "Albia Dominica",
        "birth_death": "約 337 - 380",
        "epithet": "無",
        "noble_title": "東羅馬帝國皇后 (瓦倫斯皇帝之妻 / 阿德里安堡戰後攝政)",
        "image_url": None,
        "sources": [{"page_id": "page47", "title": "瓦倫斯陣亡至迪奧多西接掌君士坦丁堡"}],
        "birth_year_num": 337,
        "category": "roman"
    },
    {
        "chinese_name": "鮑托",
        "english_name": "Flavius Bauto",
        "birth_death": "卒於 約 388",
        "epithet": "無",
        "noble_title": "法蘭克裔羅馬大元帥 / 執政官",
        "image_url": None,
        "sources": [{"page_id": "page47", "title": "瓦倫斯陣亡至迪奧多西接掌君士坦丁堡"}],
        "birth_year_num": 340,
        "category": "germanic"
    },
    {
        "chinese_name": "莫達雷斯",
        "english_name": "Modares",
        "birth_death": "活躍於 4 世紀晚期 (約 379 - 382)",
        "epithet": "無",
        "noble_title": "哥德王室貴族 / 羅馬將領",
        "image_url": None,
        "sources": [{"page_id": "page47", "title": "瓦倫斯陣亡至迪奧多西接掌君士坦丁堡"}],
        "birth_year_num": 345,
        "category": "germanic"
    },
    {
        "chinese_name": "沙普爾三世",
        "english_name": "Shapur III",
        "birth_death": "卒於 388 (383 - 388 在位)",
        "epithet": "無",
        "noble_title": "波斯薩珊王朝萬王之王",
        "image_url": None,
        "sources": [
            {"page_id": "page39", "title": "斯提里科與晚期羅馬瓦解"},
            {"page_id": "page44", "title": "羅馬與波斯地緣關係"}
        ],
        "birth_year_num": 350,
        "category": "others"
    },
    {
        "chinese_name": "魯菲努斯",
        "english_name": "Flavius Rufinus",
        "birth_death": "約 335 - 395",
        "epithet": "無",
        "noble_title": "東羅馬近衛牧首 / 執政官",
        "image_url": None,
        "sources": [{"page_id": "page39", "title": "斯提里科與晚期羅馬瓦解"}],
        "birth_year_num": 335,
        "category": "roman"
    },
    {
        "chinese_name": "克勞狄安",
        "english_name": "Claudian",
        "birth_death": "約 370 - 404",
        "epithet": "無",
        "noble_title": "西羅馬帝國宮廷詩人 / 斯提里科之頌詩作者",
        "image_url": None,
        "sources": [{"page_id": "page39", "title": "斯提里科與晚期羅馬瓦解"}],
        "birth_year_num": 370,
        "category": "roman"
    },
    {
        "chinese_name": "拉達蓋蘇斯",
        "english_name": "Radagaisus",
        "birth_death": "卒於 406",
        "epithet": "無",
        "noble_title": "哥德/日耳曼王公 (率軍入侵義大利)",
        "image_url": None,
        "sources": [
            {"page_id": "page39", "title": "斯提里科與晚期羅馬瓦解"},
            {"page_id": "page41", "title": "君士坦丁三世與五世紀初邊疆危機"}
        ],
        "birth_year_num": 360,
        "category": "germanic"
    },
    {
        "chinese_name": "哥迪吉塞爾",
        "english_name": "Godigisel",
        "birth_death": "359 - 406",
        "epithet": "無",
        "noble_title": "阿斯丁汪達爾人國王",
        "image_url": None,
        "sources": [{"page_id": "page40", "title": "萊茵河－多瑙河地緣戰略"}],
        "birth_year_num": 359,
        "category": "germanic"
    },
    {
        "chinese_name": "薩魯斯",
        "english_name": "Sarus the Goth",
        "birth_death": "卒於 412",
        "epithet": "無",
        "noble_title": "哥德貴族 / 巴爾提王朝成員 / 羅馬將領",
        "image_url": None,
        "sources": [
            {"page_id": "page38", "title": "阿陶爾夫與哥德大遷徙"},
            {"page_id": "page39", "title": "斯提里科與晚期羅馬瓦解"}
        ],
        "birth_year_num": 365,
        "category": "germanic"
    },
    {
        "chinese_name": "埃多比庫斯",
        "english_name": "Edobichus",
        "birth_death": "卒於 411",
        "epithet": "無",
        "noble_title": "法蘭克裔將領 / 篡位者君士坦丁三世之軍事統帥",
        "image_url": None,
        "sources": [{"page_id": "page41", "title": "君士坦丁三世與五世紀初邊疆危機"}],
        "birth_year_num": 370,
        "category": "germanic"
    },
    {
        "chinese_name": "康斯坦斯二世",
        "english_name": "Constans II",
        "birth_death": "卒於 411",
        "epithet": "無",
        "noble_title": "共治皇帝 / 篡位者君士坦丁三世之子",
        "image_url": None,
        "sources": [{"page_id": "page41", "title": "君士坦丁三世與五世紀初邊疆危機"}],
        "birth_year_num": 385,
        "category": "roman"
    },
    {
        "chinese_name": "喬維努斯",
        "english_name": "Jovinus",
        "birth_death": "卒於 413",
        "epithet": "無",
        "noble_title": "高盧羅馬貴族 / 帝位篡奪者",
        "image_url": None,
        "sources": [{"page_id": "page38", "title": "阿陶爾夫與哥德大遷徙"}],
        "birth_year_num": 370,
        "category": "roman"
    },
    {
        "chinese_name": "赫拉克利安",
        "english_name": "Heraclian",
        "birth_death": "卒於 413",
        "epithet": "無",
        "noble_title": "西羅馬非洲軍事伯爵 / 執政官",
        "image_url": None,
        "sources": [
            {"page_id": "page38", "title": "阿陶爾夫與哥德大遷徙"},
            {"page_id": "page39", "title": "斯提里科與晚期羅馬瓦解"}
        ],
        "birth_year_num": 370,
        "category": "roman"
    },
    {
        "chinese_name": "沙拉頓",
        "english_name": "Charaton",
        "birth_death": "活躍於 5 世紀初 (約 412 前後)",
        "epithet": "無",
        "noble_title": "匈人帝國王公/首領",
        "image_url": None,
        "sources": [{"page_id": "page34", "title": "匈人的登場與晚期羅馬地緣政治"}],
        "birth_year_num": 380,
        "category": "others"
    },
    {
        "chinese_name": "佐西姆斯",
        "english_name": "Zosimus",
        "birth_death": "活躍於 5 世紀末 - 6 世紀初",
        "epithet": "無",
        "noble_title": "東羅馬帝國官吏 / 異教歷史學家 (《新史》作者)",
        "image_url": None,
        "sources": [{"page_id": "page47", "title": "瓦倫斯陣亡至迪奧多西接掌君士坦丁堡"}],
        "birth_year_num": 460,
        "category": "roman"
    },
    {
        "chinese_name": "路易·埃爾塞維爾",
        "english_name": "Louis Elzevir",
        "birth_death": "約 1540 - 1617",
        "epithet": "無",
        "noble_title": "荷蘭著名出版家 / 埃爾塞維爾出版社創辦人",
        "image_url": None,
        "sources": [{"page_id": "page01", "title": "荷蘭建國與地緣政經"}],
        "birth_year_num": 1540,
        "category": "dutch"
    },
    {
        "chinese_name": "雨果·格老秀斯",
        "english_name": "Hugo Grotius",
        "birth_death": "1583 - 1645",
        "epithet": "國際法之父",
        "noble_title": "荷蘭法學家 / 思想家 (《海洋自由論》作者)",
        "image_url": None,
        "sources": [{"page_id": "page01", "title": "荷蘭建國與地緣政經"}],
        "birth_year_num": 1583,
        "category": "dutch"
    },
    {
        "chinese_name": "腓特烈·亨利",
        "english_name": "Frederick Henry, Prince of Orange",
        "birth_death": "1584 - 1647",
        "epithet": "無",
        "noble_title": "奧蘭治親王 / 荷蘭聯省共和國執政",
        "image_url": None,
        "sources": [{"page_id": "page01", "title": "荷蘭建國與地緣政經"}],
        "birth_year_num": 1584,
        "category": "dutch"
    },
    {
        "chinese_name": "哈爾斯",
        "english_name": "Frans Hals",
        "birth_death": "約 1582 - 1666",
        "epithet": "無",
        "noble_title": "荷蘭黃金時代肖像畫家",
        "image_url": None,
        "sources": [{"page_id": "page01", "title": "荷蘭建國與地緣政經"}],
        "birth_year_num": 1582,
        "category": "dutch"
    },
    {
        "chinese_name": "威廉·布萊德福",
        "english_name": "William Bradford",
        "birth_death": "1590 - 1657",
        "epithet": "無",
        "noble_title": "清教徒移民領袖 / 普利茅斯殖民地總督",
        "image_url": None,
        "sources": [{"page_id": "page01", "title": "荷蘭建國與地緣政經"}],
        "birth_year_num": 1590,
        "category": "british"
    },
    {
        "chinese_name": "夸美紐斯",
        "english_name": "Jan Amos Comenius",
        "birth_death": "1592 - 1670",
        "epithet": "現代教育學之父",
        "noble_title": "捷克教育家 / 哲學家 / 摩拉維亞弟兄會主教",
        "image_url": None,
        "sources": [{"page_id": "page01", "title": "荷蘭建國與地緣政經"}],
        "birth_year_num": 1592,
        "category": "others"
    },
    {
        "chinese_name": "林布蘭",
        "english_name": "Rembrandt van Rijn",
        "birth_death": "1606 - 1669",
        "epithet": "光影大師",
        "noble_title": "荷蘭黃金時代畫家 / 蝕刻版畫家",
        "image_url": None,
        "sources": [{"page_id": "page01", "title": "荷蘭建國與地緣政經"}],
        "birth_year_num": 1606,
        "category": "dutch"
    },
    {
        "chinese_name": "揆一",
        "english_name": "Frederick Coyett",
        "birth_death": "1615 - 1687",
        "epithet": "無",
        "noble_title": "最後一任荷屬台灣長官 (《被遺誤的台灣》作者)",
        "image_url": None,
        "sources": [{"page_id": "page01", "title": "荷蘭建國與地緣政經"}],
        "birth_year_num": 1615,
        "category": "dutch"
    },
    {
        "chinese_name": "揚·范·里貝克",
        "english_name": "Jan van Riebeeck",
        "birth_death": "1619 - 1677",
        "epithet": "開普殖民地奠基者",
        "noble_title": "荷蘭東印度公司殖民官員 / 開普敦開闢者",
        "image_url": None,
        "sources": [{"page_id": "page01", "title": "荷蘭建國與地緣政經"}],
        "birth_year_num": 1619,
        "category": "dutch"
    },
    {
        "chinese_name": "克里斯蒂安·惠更斯",
        "english_name": "Christiaan Huygens",
        "birth_death": "1629 - 1695",
        "epithet": "無",
        "noble_title": "荷蘭物理學家 / 天天文學家 / 擺鐘發明者",
        "image_url": None,
        "sources": [{"page_id": "page01", "title": "荷蘭建國與地緣政經"}],
        "birth_year_num": 1629,
        "category": "dutch"
    },
    {
        "chinese_name": "斯賓諾莎",
        "english_name": "Baruch Spinoza",
        "birth_death": "1632 - 1677",
        "epithet": "理性主義大師",
        "noble_title": "荷蘭猶太裔哲學家 (《倫理學》作者)",
        "image_url": None,
        "sources": [{"page_id": "page01", "title": "荷蘭建國與地緣政經"}],
        "birth_year_num": 1632,
        "category": "dutch"
    },
    {
        "chinese_name": "維梅爾",
        "english_name": "Johannes Vermeer",
        "birth_death": "1632 - 1675",
        "epithet": "無",
        "noble_title": "荷蘭黃金時代風俗畫家",
        "image_url": None,
        "sources": [{"page_id": "page01", "title": "荷蘭建國與地緣政經"}],
        "birth_year_num": 1632,
        "category": "dutch"
    },
    {
        "chinese_name": "安東尼·凡·雷文霍克",
        "english_name": "Antonie van Leeuwenhoek",
        "birth_death": "1632 - 1723",
        "epithet": "微生物學之父",
        "noble_title": "荷蘭顯微鏡學家 / 生物學家",
        "image_url": None,
        "sources": [{"page_id": "page01", "title": "荷蘭建國與地緣政經"}],
        "birth_year_num": 1632,
        "category": "dutch"
    },
    {
        "chinese_name": "皮埃爾·貝爾",
        "english_name": "Pierre Bayle",
        "birth_death": "1647 - 1706",
        "epithet": "無",
        "noble_title": "法國哲學家 / 啟蒙運動先驅 (《歷史批判辭典》作者)",
        "image_url": None,
        "sources": [{"page_id": "page01", "title": "荷蘭建國與地緣政經"}],
        "birth_year_num": 1647,
        "category": "others"
    },
    {
        "chinese_name": "約翰內斯·德·格拉夫",
        "english_name": "Johannes de Graaf",
        "birth_death": "1729 - 1813",
        "epithet": "無",
        "noble_title": "荷屬聖尤斯特歇斯島總督 (首位向美國國旗鳴砲致敬者)",
        "image_url": None,
        "sources": [{"page_id": "page01", "title": "荷蘭建國與地緣政經"}],
        "birth_year_num": 1729,
        "category": "dutch"
    },
    {
        "chinese_name": "額我略七世",
        "english_name": "Pope Gregory VII",
        "birth_death": "1015 - 1085",
        "epithet": "無",
        "noble_title": "羅馬教宗 (發動額我略改革與敘任權鬥爭)",
        "image_url": None,
        "sources": [
            {"page_id": "page05", "title": "希爾紹修道院研究報告"},
            {"page_id": "page07", "title": "奧托-薩利安帝國教會體制"}
        ],
        "birth_year_num": 1015,
        "category": "papal"
    },
    {
        "chinese_name": "亨利四世 (神聖羅馬帝國)",
        "english_name": "Henry IV, Holy Roman Emperor",
        "birth_death": "1050 - 1106",
        "epithet": "卡諾莎之行者",
        "noble_title": "薩利安王朝神聖羅馬帝國皇帝",
        "image_url": None,
        "sources": [
            {"page_id": "page05", "title": "希爾紹修道院研究報告"},
            {"page_id": "page07", "title": "奧托-薩利安帝國教會體制"}
        ],
        "birth_year_num": 1050,
        "category": "hre"
    },
    {
        "chinese_name": "約翰 (無地王)",
        "english_name": "John, King of England",
        "birth_death": "1166 - 1216",
        "epithet": "無地王",
        "noble_title": "英格蘭金雀花王朝國王 (簽署《大憲章》)",
        "image_url": None,
        "sources": [{"page_id": "page14", "title": "英國憲法"}],
        "birth_year_num": 1166,
        "category": "british"
    },
    {
        "chinese_name": "西蒙·德·孟福爾",
        "english_name": "Simon de Montfort",
        "birth_death": "1208 - 1265",
        "epithet": "議會之父",
        "noble_title": "第 6 代萊斯特伯爵 (召集第一屆英格蘭議會)",
        "image_url": None,
        "sources": [{"page_id": "page14", "title": "英國憲法"}],
        "birth_year_num": 1208,
        "category": "british"
    },
    {
        "chinese_name": "愛德華一世",
        "english_name": "Edward I of England",
        "birth_death": "1239 - 1307",
        "epithet": "長腿王 / 蘇格蘭人之錘",
        "noble_title": "英格蘭金雀花王朝國王 (建立模範議會)",
        "image_url": None,
        "sources": [{"page_id": "page14", "title": "英國憲法"}],
        "birth_year_num": 1239,
        "category": "british"
    },
    {
        "chinese_name": "揚·齊斯卡",
        "english_name": "Jan Žižka",
        "birth_death": "1360 - 1424",
        "epithet": "獨眼將軍 / 不敗戰神",
        "noble_title": "波希米亞胡斯派軍事名將 / 戰車陣創始人",
        "image_url": None,
        "sources": [{"page_id": "page21", "title": "信仰衝突與波希米亞國家認同：胡斯戰爭"}],
        "birth_year_num": 1360,
        "category": "hussite"
    }
]

# Check existing for new_characters to avoid duplicate
added_new_count = 0
for nc in new_characters:
    if not find_char(nc["chinese_name"]):
        existing_chars.append(nc)
        added_new_count += 1
    else:
        print(f"Already exists: {nc['chinese_name']}")

print(f"Added {added_new_count} new characters.")

# Sort all characters by birth_year_num
existing_chars.sort(key=lambda x: x.get("birth_year_num", 9999))

print(f"Total characters after update: {len(existing_chars)}")

# Format JSON nicely
new_json_str = json.dumps(existing_chars, ensure_ascii=False, indent=4)

# Replace in html content
new_html_content = re.sub(
    r'const\s+rawCharacters\s*=\s*\[\s*\{.*?\n\s*\];',
    f'const rawCharacters = {new_json_str};',
    html_content,
    flags=re.DOTALL
)

with open(html_path, "w", encoding="utf-8") as f:
    f.write(new_html_content)

print(f"Successfully updated {html_path}!")
