import os
import re
import json

ROOT_DIR = r"c:\Users\USER\gemini的簡單歷史課"
REPORT_PATH = os.path.join(ROOT_DIR, "fact_check_report.md")

def is_candidate(sentence):
    # Look for years (4 digits), dates with separators, numbers, or capitalized proper nouns (simple heuristic)
    patterns = [
        r"\b\d{4}\b",                     # year
        r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b",  # date like 12/05/2020
        r"\b\d+([.,]\d+)?\b",            # any number
        r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\b"  # multi‑word proper noun
    ]
    for pat in patterns:
        if re.search(pat, sentence):
            return True
    return False

def split_sentences(text):
    # Simple sentence splitter using punctuation.
    # Preserve the delimiter.
    sentences = re.split(r"(?<=[.!?])\s+", text)
    return [s.strip() for s in sentences if s.strip()]

with open(REPORT_PATH, "w", encoding="utf-8") as report:
    report.write("# Fact‑Check Candidate Report\n\n")
    report.write("_此報告列出所有可能含有事實性斷言的句子，標註為「待確認」。每條項目請自行使用可信來源（如各國維基百科、學術期刊）驗證。_\n\n")
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
                report.write(f"- **句子**: {s}\n  - 判斷: 待確認\n  - 來源: (待查證)\n\n")

print(f"Report generated at {REPORT_PATH}")
