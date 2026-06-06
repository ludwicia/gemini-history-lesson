import os
import re
import urllib.parse

file_path = 'course/聖職與婚娶：基督宗教神職人員生育、婚姻與財產繼承的歷史演變與政權博弈.md'

with open(file_path, 'r', encoding='utf-8') as f:
    text = f.read()

# 1. First, strip Google tracking URLs from markdown links
def clean_google_url(match):
    url = match.group(0)
    parsed = urllib.parse.urlparse(url)
    qs = urllib.parse.parse_qs(parsed.query)
    if 'q' in qs:
        return qs['q'][0]
    return url

text = re.sub(r'https?://www\.google\.com/url\?[^\s)\]">]+', clean_google_url, text)

# 2. Fix nested links like [[url](url)](url](url))
text = re.sub(r'\[\[(https?://[^\]]+)\]\(\1\)\]\(\1\]\(\1\)\)', r'[\1](\1)', text)
text = re.sub(r'\[\[(https?://[^\]]+)\]\(\1\)\]\(\1\)', r'[\1](\1)', text)

# Just in case there's another level of weirdness
text = re.sub(r'\[\[(https?://[^\]]+)\]\]\(\1\)', r'[\1](\1)', text)

# Any other weird combinations
def clean_weird_nested(match):
    url = match.group(1)
    return f"[{url}]({url})"

text = re.sub(r'\[\[(https?://[^\]]+)\].*?\)(?=\s|$|\))', clean_weird_nested, text)

# Overwrite
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(text)
print("Cleaned!")
