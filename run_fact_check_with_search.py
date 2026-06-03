import os, re, json, requests, urllib.parse
from bs4 import BeautifulSoup

ROOT_DIR = r"c:\Users\USER\gemini的簡單歷史課"
REPORT_PATH = os.path.join(ROOT_DIR, "fact_check_report.md")

def is_candidate(sentence):
    patterns = [
        r"\b\d{4}\b",                     # year
        r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b",  # date
        r"\b\d+([.,]\d+)?\b",            # number
        r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\b"  # proper noun (simple)
    ]
    return any(re.search(p, sentence) for p in patterns)

def split_sentences(text):
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]

def search_duckduckgo(query, max_results=3):
    # Simple HTML search – no API key required.
    url = "https://duckduckgo.com/html/"
    params = {"q": query}
    try:
        resp = requests.post(url, data=params, timeout=10)
        resp.raise_for_status()
    except Exception:
        return []
    soup = BeautifulSoup(resp.text, "html.parser")
    links = []
    for a in soup.select('a.result__a')[:max_results]:
        href = a.get('href')
        if href:
            # DuckDuckGo wraps URLs, extract the actual target.
            parsed = urllib.parse.urlparse(href)
            q = urllib.parse.parse_qs(parsed.query).get('uddg')
            if q:
                links.append(q[0])
            else:
                links.append(href)
    return links

with open(REPORT_PATH, "w", encoding="utf-8") as report:
    report.write("# Fact‑Check Report (auto‑search)\n\n")
    report.write("_此報告列出所有可能含有事實性斷言的句子，已嘗試自動搜尋可信來源（維基百科、學術期刊等）。若未取得結果，請自行查證。_\n\n")
    for root, _, files in os.walk(ROOT_DIR):
        for fname in files:
            if not fname.lower().endswith('.md'):
                continue
            if fname == "fact_check_report.md":
                continue
            file_path = os.path.join(root, fname)
            rel_path = os.path.relpath(file_path, ROOT_DIR)
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            sentences = split_sentences(content)
            candidates = [s for s in sentences if is_candidate(s)]
            if not candidates:
                continue
            report.write(f"## 文件: {rel_path}\n\n")
            for s in candidates:
                links = search_duckduckgo(s)
                link_md = ", ".join([f"[URL{i+1}]({ln})" for i, ln in enumerate(links)]) if links else "(無搜尋結果)"
                report.write(f"- **句子**: {s}\n  - 判斷: 待確認\n  - 來源: {link_md}\n\n")
print("Report generated at", REPORT_PATH)
