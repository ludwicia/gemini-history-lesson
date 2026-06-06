import re

file_path = 'build_html_md.py'
with open(file_path, 'r', encoding='utf-8') as f:
    code = f.read()

# 1. Add python var definitions after page 14
page15_defs = """
# Page 15 Config
file_p15 = r'course/聖職與婚娶：基督宗教神職人員生育、婚姻與財產繼承的歷史演變與政權博弈.md'
images_p15 = []
"""
code = re.sub(r"(# Page 14 \(British Constitution\) Config.*?\]\n)", r"\1" + page15_defs, code, flags=re.DOTALL)

# 2. Add html_body processing after page 14
process15 = """
print("Processing Page 15 (Clergy Marriage)...")
html_body_p15 = process_markdown(file_p15, images_p15, "1.0", None)
"""
code = re.sub(r"(print\(\"Processing Page 14.*?html_body_p14 = process_markdown\(.*?map_p14\)\n)", r"\1" + process15, code, flags=re.DOTALL)

# 3. Add to JSON-LD Articles array
json_ld15 = """,
        {"@type": "Article", "name": "聖職與婚娶", "url": "https://ludwicia.github.io/ludwica-history-lesson/#page15"}"""
code = re.sub(r'(        \{"@type": "Article", "name": "英國的憲法", "url": "https://ludwicia.github.io/ludwica-history-lesson/#page14"\})', r'\1' + json_ld15, code)

# 4. Add to Nav Button
nav_btn15 = """                    <a href="#page15" id="nav-btn-page15" class="nav-tab-btn" style="text-decoration: none;">聖職與婚娶</a>\n"""
code = re.sub(r'(                    <a href="#page14".*?英國的憲法</a>\n)', r'\1' + nav_btn15, code)

# 5. Add to HTML Body container
div15 = """        <div id="course-page15" class="course-page" style="display: none;">
            {html_body_p15}
        </div>\n"""
code = re.sub(r'(        <div id="course-page14".*?</div>\n)', r'\1' + div15, code, flags=re.DOTALL)

# 6. Add to JS pageData object
pagedata15 = ",\n        page15: `{toc_p15}`"
code = re.sub(r'(        page14: `\{toc_p14\}`)', r'\1' + pagedata15, code)

# 7. Add to pageMeta map
pagemeta15 = """,
        'page15': { title: '聖職與婚娶：歷史演變與政權博弈 — Ludwica 的簡單歷史課', desc: '深入探討基督宗教神職人員生育、婚姻與財產繼承的歷史演變與政權博弈。' }"""
code = re.sub(r"(\s*'page14': \{ title: '英國的憲法.*? \})", r"\1" + pagemeta15, code)

# 8. Add to searchIndex array
searchidx15 = """,
            { id: 'page15', name: '聖職與婚娶' }"""
code = re.sub(r"(            \{ id: 'page14', name: '英國的憲法' \})", r"\1" + searchidx15, code)

# 9. Add to matchedPage array
code = re.sub(r"('page14')", r"\1, 'page15'", code)

# 10. Add to format call for python string template
format15 = ",\n    html_body_p15=html_body_p15,\n    toc_p15=markdown.markdown(\"[TOC]\\n\" + open(file_p15, 'r', encoding='utf-8').read(), extensions=['toc'])"
code = re.sub(r'(    toc_p14=markdown\.markdown\(\"\[TOC\]\\\\n\" \+ open\(file_p14, \'r\', encoding=\'utf-8\'\)\.read\(\), extensions=\[\'toc\'\]\))', r'\1' + format15, code)

# 11. Add to sitemap
sitemap15 = """  <url>
    <loc>https://ludwicia.github.io/ludwica-history-lesson/#page15</loc>
    <lastmod>{today}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.8</priority>
  </url>\n"""
code = re.sub(r'(  <url>\s*<loc>https://ludwicia\.github\.io/ludwica-history-lesson/#page14</loc>.*?</url>\n)', r'\1' + sitemap15, code, flags=re.DOTALL)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(code)

print("build_html_md.py patched successfully.")
