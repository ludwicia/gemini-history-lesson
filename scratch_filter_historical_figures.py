import json
import re
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open(r"c:\Users\USER\gemini的簡單歷史課\scratch\candidates_all.json", "r", encoding="utf-8") as f:
    candidates = json.load(f)

print(f"Total candidates to review: {len(candidates)}")

# Filter candidates by checking whether ename looks like person name and not terms/locations/edicts
non_person_keywords = [
    "battle", "edict", "treaty", "monastery", "church", "edict", "act", "rebellion", "crisis",
    "reformation", "charter", "code", "pax", "via", "lex", "bull", "rule", "syndicate", "company",
    "republic", "empire", "kingdom", "duchy", "county", "province", "strait", "river", "mountain",
    "sea", "ocean", "bank", "scandal", "lithography", "crisis", "house of", "dynasty", "order of",
    "society of", "union of", "pacification of", "relief", "assembly", "parliament", "council",
    "synod", "league", "confederation", "state", "city", "island", "port", "castle", "fort"
]

valid_persons = []

for cn, data in candidates.items():
    ename_lower = data["ename"].lower()
    if any(kw in ename_lower for kw in non_person_keywords):
        continue

    # Exclude chinese terms that end with Non-person words
    if any(cn.endswith(w) for w in ["國", "城", "島", "海", "河", "山", "派", "會", "社", "黨", "院", "館", "寺", "路", "門", "港", "洲", "堡", "省", "條約", "敕令", "憲法"]):
        continue

    valid_persons.append(data)

print(f"Filtered candidate persons count: {len(valid_persons)}\n")

# Display candidate persons by page_id for human review
by_page = {}
for p in valid_persons:
    for s in p["sources"]:
        pid = s["page_id"]
        if pid not in by_page:
            by_page[pid] = []
        by_page[pid].append((p["cname"], p["ename"], s["title"]))

for pid, items in sorted(by_page.items()):
    print(f"=== {pid} ({items[0][2]}) ===")
    for cn, en, title in items:
        print(f"  - {cn} ({en})")
