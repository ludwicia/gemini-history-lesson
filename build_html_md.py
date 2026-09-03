import markdown
import re
import os
import json
import subprocess
from datetime import datetime
from functools import lru_cache

# Helper to automatically format raw http/https links as markdown links
def make_urls_clickable(text):
    # Match standard HTTP/HTTPS URLs not already inside a markdown link or HTML attribute
    # Negative lookbehind: (?<![("<=])
    # URL pattern: https?://[a-zA-Z0-9\-._~:/?#\[\]@!$&'()*+,;=%]+
    url_pattern = r'(?<![("<=])(https?://[a-zA-Z0-9\-._~:/?#\[\]@!$&\'()*+,;=%]+)'
    return re.sub(url_pattern, r'[\1](\1)', text)

# Helper to get the last update date of a file from Git or filesystem
# [2026-07-19 優化] 加上 lru_cache：本函式對每個 .md 檔會發出 3 次 git 子行程
# （log / diff / diff --cached，實測合計約 0.7 秒），而同一個檔案在建置過程中
# 會被查詢兩次（process_markdown 內一次、產生版權卡片日期時再一次），
# 44 篇文章即浪費約 30 秒。單次建置期間檔案日期不會變動，故可安全快取。
@lru_cache(maxsize=None)
def get_file_last_update_date(file_path):
    try:
        res = subprocess.run(
            ['git', 'log', '-1', '--format=%ad', '--date=format:%Y-%m-%d', file_path],
            capture_output=True, text=True, check=True
        )
        date_str = res.stdout.strip()
        if date_str:
            # Check if file has unstaged or staged changes
            diff_res = subprocess.run(['git', 'diff', '--quiet', file_path])
            if diff_res.returncode == 0:
                diff_staged = subprocess.run(['git', 'diff', '--cached', '--quiet', file_path])
                if diff_staged.returncode == 0:
                    return date_str
    except Exception:
        pass

    try:
        mtime = os.path.getmtime(file_path)
        return datetime.fromtimestamp(mtime).strftime('%Y-%m-%d')
    except Exception:
        return datetime.now().strftime('%Y-%m-%d')

def get_share_bar_html(page_id):
    if not page_id:
        return ""
    return f'''
<div class="share-bar">
    <span class="share-bar-title">分享文章：</span>
    <button class="share-btn share-btn-fb" onclick="shareTo('facebook', '{page_id}')">
        <svg viewBox="0 0 24 24"><path d="M22 12c0-5.52-4.48-10-10-10S2 6.48 2 12c0 4.84 3.44 8.87 8 9.8V15H8v-3h2V9.5C10 7.57 11.57 6 13.5 6H16v3h-2c-.55 0-1 .45-1 1v2h3v3h-3v6.95c4.56-.93 8-4.96 8-9.75z"/></svg>
        <span class="share-text">Facebook</span>
    </button>
    <button class="share-btn share-btn-line" onclick="shareTo('line', '{page_id}')">
        <svg viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 5.82 2 10.53c0 2.75 1.51 5.2 3.93 6.75-.15.54-.53 1.95-.6 2.22-.09.33.1.32.22.24.26-.16 4.04-2.67 4.6-3.05.6.11 1.22.17 1.85.17 5.52 0 10-3.82 10-8.53C22 5.82 17.52 2 12 2z"/></svg>
        <span class="share-text">LINE</span>
    </button>
    <button class="share-btn share-btn-x" onclick="shareTo('twitter', '{page_id}')">
        <svg viewBox="0 0 24 24"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/></svg>
        <span class="share-text">X (Twitter)</span>
    </button>
    <button class="share-btn share-btn-copy" onclick="shareTo('copy', '{page_id}')">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>
        <span class="share-text">複製連結</span>
    </button>
</div>
'''

# Helper to process and format a markdown lesson
def process_markdown(file_path, image_replacements, content_version, main_img_html=None, page_id=None):
    update_date = get_file_last_update_date(file_path)
    with open(file_path, 'r', encoding='utf-8') as f:
        text = f.read()
    text = make_urls_clickable(text)

    # Clean Voyager/Gemini footer source info if present
    text = text.split('Source: https://gemini')[0].strip(' -\n')

    # Preprocess markdown to fix MS Word style paragraph breaks (single newlines)
    lines = text.split('\n')
    new_lines = []
    for i, line in enumerate(lines):
        new_lines.append(line)
        if i < len(lines) - 1:
            next_line = lines[i+1]
            if line.strip() and next_line.strip():
                # If neither line is a list item, table row, or heading
                if not re.match(r'^[\-\*\#\|]', line.lstrip()) and not re.match(r'^\d+\.', line.lstrip()):
                    if not re.match(r'^[\-\*\#\|]', next_line.lstrip()) and not re.match(r'^\d+\.', next_line.lstrip()):
                        new_lines.append('')

    text = '\n'.join(new_lines)
    html_body = markdown.markdown(text, extensions=['tables', 'toc'])

    # Add content version badge and update date badge
    version_badge = f'<div style="text-align: center; color: #718096; margin-top: -15px; margin-bottom: 25px; font-size: 0.95rem; font-weight: 600; display: flex; align-items: center; justify-content: center; gap: 8px;"><span style="background-color: #ebf8ff; color: #2b6cb0; padding: 3px 8px; border-radius: 4px; font-size: 0.8rem; border: 1px solid #bee3f8;">內容版本：{content_version}</span><span style="background-color: #f0fff4; color: #38a169; padding: 3px 8px; border-radius: 4px; font-size: 0.8rem; border: 1px solid #c6f6d5;">最近更新：{update_date}</span></div>\n'

    # Insert version badge, sharing buttons, and main image under first H1
    header_insert = version_badge
    if page_id:
        header_insert += get_share_bar_html(page_id)
    if main_img_html:
        header_insert += main_img_html

    html_body = re.sub(r'(<h1.*?>.*?</h1>)', r'\1\n' + header_insert, html_body, count=1)

    # Substitute specific headings with images for high-end text wrap
    for pattern, url, caption in image_replacements:
        img_html = f'\n<figure class="image-left"><img src="{url}" alt="{caption}" loading="lazy"><figcaption class="caption">{caption}</figcaption></figure>\n'
        html_body = re.sub(pattern, r'\1' + img_html, html_body, count=1)

    # Automatically convert standard markdown images to the custom figure layout
    # Match: <p><img alt="caption" src="url" /></p>
    md_img_pattern = r'<p>\s*<img\s+alt="([^"]*)"\s+src="([^"]*)"\s*/>\s*</p>'
    def img_replace(match):
        alt = match.group(1)
        src = match.group(2)
        if "ad_calendar_eq_" in src:
            return f'\n<figure class="image-center" style="width: 100%; max-width: 520px; float: none; margin: 25px auto; padding: 0; box-shadow: none; border: none; background: none;"><img src="{src}" alt="{alt}" loading="lazy" style="box-shadow: 0 4px 12px rgba(0,0,0,0.04); border: 1px solid #e2e8f0; border-radius: 8px; width: 100%; height: auto;"></figure>\n'
        return f'<figure class="image-left"><img src="{src}" alt="{alt}" loading="lazy"><figcaption class="caption">{alt}</figcaption></figure>'
    html_body = re.sub(md_img_pattern, img_replace, html_body)

    if page_id:
        html_body += get_share_bar_html(page_id)

    return html_body

def process_3col_document(file_path, content_version, page_id=None, lang_orig="德文", cols=3):
    update_date = get_file_last_update_date(file_path)
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
        text = make_urls_clickable(text)
    except Exception as e:
        return f"<p>Error loading document: {e}</p>"

    blocks = [b.strip() for b in text.split('---') if b.strip()]
    if not blocks:
        return ""

    title_block = blocks[0]
    # Clean up double title if present
    lines = title_block.split('\n')
    cleaned_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped == "金璽詔書(德)" and not stripped.startswith('#'):
            continue # skip the redundant plain first line
        cleaned_lines.append(line)
    cleaned_title_block = '\n'.join(cleaned_lines)

    title_html = markdown.markdown(cleaned_title_block)

    html = f'''
    <div style="text-align: center; color: #718096; margin-top: 10px; margin-bottom: 10px; font-size: 0.95rem; font-weight: 600; display: flex; align-items: center; justify-content: center; gap: 8px;">
        <span style="background-color: #ebf8ff; color: #2b6cb0; padding: 3px 8px; border-radius: 4px; font-size: 0.8rem; border: 1px solid #bee3f8;">內容版本：{content_version}</span>
        <span style="background-color: #f0fff4; color: #38a169; padding: 3px 8px; border-radius: 4px; font-size: 0.8rem; border: 1px solid #c6f6d5;">最近更新：{update_date}</span>
    </div>
    '''
    if page_id:
        html += get_share_bar_html(page_id)

    container_class = "doc-3col-container" if cols == 3 else "doc-3col-container doc-2col-container"
    html += f'''
    <div class="doc-title-section">
        {title_html}
    </div>
    <div class="{container_class}">
        <div class="doc-3col-header">
            <div class="doc-col-title">原文 ({lang_orig})</div>
            <div class="doc-col-title">譯文 (中文)</div>
    '''
    if cols == 3:
        html += f'''        <div class="doc-col-title">解釋 (筆記)</div>'''
    html += f'''
        </div>
    '''

    for block in blocks[1:]:
        block = block.strip()
        if not block: continue

        if "**原文**" in block and "**譯文**" in block:
            parts = block.split("**譯文**")
            original_part = parts[0].replace("**原文**", "").strip()

            # Check if there is an **解釋** block
            if "**解釋**" in parts[1]:
                sub_parts = parts[1].split("**解釋**")
                translated_part = sub_parts[0].strip()
                explanation_part = sub_parts[1].strip()
            else:
                translated_part = parts[1].strip()
                explanation_part = ""

            original_text = markdown.markdown(original_part)
            translated_text = markdown.markdown(translated_part)
            explanation_text = markdown.markdown(explanation_part) if explanation_part else ""

            html += f'''
            <div class="doc-3col-row">
                <div class="doc-col doc-original">{original_text}</div>
                <div class="doc-col doc-translation">{translated_text}</div>
            '''
            if cols == 3:
                html += f'''    <div class="doc-col doc-explanation">{explanation_text}</div>'''
            html += f'''
            </div>
            '''
        else:
            html += f'''
            <div class="doc-3col-row full-width-row" style="grid-template-columns: 1fr;">
                <div class="doc-col" style="grid-column: 1 / -1;">{markdown.markdown(block)}</div>
            </div>
            '''

    html += "</div>"
    if page_id:
        html += get_share_bar_html(page_id)
    return html

# 核心資料源：直接動態從 course_config.json 讀取，確保「單一真實來源 (Single Source of Truth)」
with open("course_config.json", "r", encoding="utf-8") as f:
    _course_cfg = json.load(f)

pages_data = _course_cfg.get("articles", {})
categories = _course_cfg.get("categories", [])

# Parse worklog.md for the latest 10 updates
worklog_html = ""
try:
    with open('worklog.md', 'r', encoding='utf-8') as f:
        worklog_lines = f.readlines()

    updates = []
    current_update = None

    for line in worklog_lines:
        if line.startswith('#### '):
            if current_update:
                updates.append(current_update)
                if len(updates) >= 10:
                    break
            current_update = {'title': line[5:].strip(), 'items': []}
        elif line.startswith('- ') and current_update is not None:
            html_item = line[2:].strip()
            html_item = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', html_item)
            current_update['items'].append(html_item)

    if current_update and len(updates) < 10:
        updates.append(current_update)

    for update in updates:
        worklog_html += f'<div class="update-entry"><div class="update-date">{update["title"]}</div><ul class="update-list">'
        for item in update['items']:
            worklog_html += f'<li>{item}</li>'
        worklog_html += '</ul></div>'
except Exception as e:
    worklog_html = f"<p>Error loading worklog: {e}</p>"


def render_article_content(pid, data):
    ver = data.get('ver', '1.0')
    if data.get('doc'):
        params = data.get('doc_params', {})
        return process_3col_document(
            data['file_path'],
            ver,
            page_id=pid,
            lang_orig=params.get('lang_orig', '德文'),
            cols=params.get('cols', 3)
        )
    elif data.get('bilingual') and data.get('file_path_en'):
        replacements = [(r['pattern'], r['url'], r['caption']) for r in data.get('image_replacements', [])]
        zh_html = process_markdown(data['file_path'], replacements, ver, None, page_id=pid)
        en_html = process_markdown(data['file_path_en'], replacements, ver, None, page_id=f"{pid}_en")
        return f'''<div class="novel-lang-selector" style="display: flex; justify-content: flex-end; gap: 10px; margin-bottom: 25px; border-bottom: 1px solid #e2e8f0; padding-bottom: 12px; width: 100%;">
  <button id="btn-lang-zh" onclick="switchNovelLang('zh')" style="background-color: #3182ce; color: white; border: 1px solid #3182ce; border-radius: 6px; padding: 6px 16px; font-size: 0.9rem; font-weight: 600; cursor: pointer; transition: all 0.2s; box-shadow: 0 2px 4px rgba(49,130,206,0.15);">中文</button>
  <button id="btn-lang-en" onclick="switchNovelLang('en')" style="background-color: #f7fafc; color: #4a5568; border: 1px solid #cbd5e0; border-radius: 6px; padding: 6px 16px; font-size: 0.9rem; font-weight: 600; cursor: pointer; transition: all 0.2s;">English</button>
</div>

<div id="novel-zh-section">
{zh_html}
</div>
<div id="novel-en-section" style="display: none;">
{en_html}
</div>'''
    else:
        replacements = [(r['pattern'], r['url'], r['caption']) for r in data.get('image_replacements', [])]
        file_path = data.get('file_path', '')
        if not file_path or not os.path.exists(file_path):
            return ""
        return process_markdown(file_path, replacements, ver, data.get('map_html'), page_id=pid)


# 動態渲染所有文章，並建立向後相容的全域變數
articles_html = {}
for pid, data in pages_data.items():
    p_match = re.search(r'\d+', pid)
    p_num = int(p_match.group()) if p_match else 0
    print(f"Processing {pid} ({data.get('title', pid)})...")
    articles_html[pid] = render_article_content(pid, data)

    # 設置向後相容的全域變數 (供外部腳本或舊邏輯使用)
    globals()[f"html_body_p{p_num}"] = articles_html[pid]
    globals()[f"file_p{p_num}"] = data.get('file_path')
    globals()[f"map_p{p_num}"] = data.get('map_html')
    globals()[f"images_p{p_num}"] = [(r['pattern'], r['url'], r['caption']) for r in data.get('image_replacements', [])]


# ============================================================================
# [2026-07-21] 輸出段：寫出 index.html / sitemap.xml / robots.txt / pages/*.html
#
# 這一段原本直接寫在模組層級，而本檔案沒有 __main__ 保護，導致
# `import build_html_md`（build_static_chunks.py 第 4 行、admin_server.py 第 13 行）
# 會完整重跑一次建置並重複寫出所有檔案。run_build.py 因此每次發布都建置兩遍，
# 啟動 admin_server.py 也會意外觸發一次全站建置。
#
# 現收進函式，僅在直接執行本腳本、或由 run_build.py 明確呼叫時才寫出檔案。
# 被 import 時只計算文章資料（pages_data / html_body_pXX / file_pXX），不寫檔。
# ============================================================================
def write_site_outputs():
    # [2026-07-19 移除] 原本此處會寫出 index_static.html。
    # 該檔案全專案無任何引用（不在 sitemap、不被 index_db.html 或任何 JS 載入），
    # 實際部署的 index.html 來自下方的 index_db.html 複製，故停止產出以免混淆。
    # 註：final_html 的組裝邏輯暫時保留，待模板單一化重構時再一併清理。

    # Automatically synchronize index.html with the database-driven index_db.html
    print("Synchronizing index.html with index_db.html...")
    try:
        import shutil
        shutil.copy('index_db.html', 'index.html')
        print("[OK] Synchronized index.html with index_db.html")
    except Exception as e:
        print(f"[WARNING] Failed to sync index.html: {e}")

    # [2026-07-19 新增] 於 index.html 注入靜態文章索引。
    # 首頁文章清單原本完全由 JavaScript 從 Firestore 載入，初始 HTML 中沒有任何指向文章的
    # 連結（實測可見文字僅約 390 字元、0 個 <h1>、0 個文章連結），搜尋引擎因此無從發現
    # 任何一篇文章。此處在 index_db.html 的標記之間注入依分類排列的完整文章連結，
    # 讓 Googlebot 不需執行 JavaScript 就能爬行到全部 44 篇靜態文章頁。
    print("Injecting static article index into index.html...")
    try:
        with open('index.html', 'r', encoding='utf-8') as f:
            _idx_html = f.read()

        _start_marker = '<!-- STATIC_ARTICLE_INDEX_START -->'
        _end_marker = '<!-- STATIC_ARTICLE_INDEX_END -->'

        if _start_marker in _idx_html and _end_marker in _idx_html:
            _blocks = []
            for _cat in categories:
                _links = []
                for _pid in _cat['pages']:
                    if _pid in pages_data and not pages_data[_pid].get('doc'):
                        _links.append(
                            f'            <li><a href="pages/{_pid}.html">{pages_data[_pid]["title"]}</a></li>'
                        )
                if _links:
                    _blocks.append(
                        f'        <div class="article-index-group">\n'
                        f'            <h3>{_cat["title"]}</h3>\n'
                        f'            <ul>\n' + '\n'.join(_links) + '\n            </ul>\n'
                        f'        </div>'
                    )

            # 三欄文獻頁（doc=True）不屬於任何專題分類，首頁是以獨立的「歷史文獻對照」區塊呈現，
            # 這裡集中彙整，確保在靜態索引中擁有專屬區塊並可被爬取。
            _doc_links = []
            for _pid in sorted(pages_data.keys(), key=lambda x: int(re.search(r'\d+', x).group())):
                if pages_data[_pid].get('doc'):
                    _doc_links.append(
                        f'            <li><a href="pages/{_pid}.html">{pages_data[_pid]["title"]}</a></li>'
                    )
            if _doc_links:
                _blocks.append(
                    f'        <div class="article-index-group">\n'
                    f'            <h3>歷史文獻對照</h3>\n'
                    f'            <ul>\n' + '\n'.join(_doc_links) + '\n            </ul>\n'
                    f'        </div>'
                )

            _injected = _start_marker + '\n' + '\n'.join(_blocks) + '\n    ' + _end_marker
            _idx_html = re.sub(
                re.escape(_start_marker) + r'.*?' + re.escape(_end_marker),
                lambda m: _injected,
                _idx_html,
                flags=re.DOTALL
            )

            with open('index.html', 'w', encoding='utf-8', newline='\n') as f:
                f.write(_idx_html)

            _link_count = _injected.count('<li><a href="pages/')
            print(f"[OK] Injected {_link_count} static article links into index.html")

            _missing_from_index = [p for p in pages_data if f'pages/{p}.html' not in _injected]
            if _missing_from_index:
                print(f"[WARNING] {len(_missing_from_index)} page(s) missing from the static article index: {', '.join(sorted(_missing_from_index))}")
        else:
            print("[WARNING] STATIC_ARTICLE_INDEX markers not found in index.html - skipped injection")
    except Exception as e:
        print(f"[WARNING] Failed to inject static article index: {e}")

    # Generate sitemap.xml for SEO
    from datetime import date
    today = date.today().isoformat()
    base_site_url = "https://ludwica-history-lesson.pages.dev/"

    sitemap_urls = []

    # 首頁
    sitemap_urls.append(f"""  <url>
    <loc>{base_site_url}</loc>
    <lastmod>{today}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>1.0</priority>
  </url>""")

    # 獨立功能頁面
    standalone_pages = [
        ("characters_database.html", 0.8),
        ("europe_map.html", 0.8),
        ("character_relationship.html", 0.7),
        ("constitutio_antoniniana_bilingual.html", 0.7),
    ]
    for page_file, priority in standalone_pages:
        if os.path.exists(page_file):
            # 同上：Cloudflare Pages 會把 .html 轉址掉，sitemap 直接列出正規網址，
            # 避免整份 sitemap 的網址全部回報為「含轉址的網頁」。
            sitemap_urls.append(f"""  <url>
    <loc>{base_site_url}{page_file[:-5] if page_file.endswith('.html') else page_file}</loc>
    <lastmod>{today}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>{priority}</priority>
  </url>""")

    # SEO 文章頁面 (pages/)
    for pid in sorted(pages_data.keys(), key=lambda x: int(re.search(r'\d+', x).group())):
        sitemap_urls.append(f"""  <url>
    <loc>{base_site_url}pages/{pid}</loc>
    <lastmod>{today}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.8</priority>
  </url>""")

    sitemap_content = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + '\n'.join(sitemap_urls) + '\n</urlset>\n'

    with open(r'sitemap.xml', 'w', encoding='utf-8', newline='\n') as f:
        f.write(sitemap_content)
    print("Generated sitemap.xml")

    # Generate robots.txt for SEO
    robots_content = """User-agent: *
Allow: /

Sitemap: https://ludwica-history-lesson.pages.dev/sitemap.xml
"""

    with open(r'robots.txt', 'w', encoding='utf-8') as f:
        f.write(robots_content)
    print("Generated robots.txt")

    # [2026-07-19 重寫] 產生 pages/ 底下的靜態文章頁。
    # 原本這裡產生的是「只有 meta 標籤 + window.location.replace 跳轉」的空殼頁，
    # 導致 Google 將 44 篇文章全部視為跳轉到首頁的同一個網址，整站僅 1 個 URL 被檢索
    # 且因內容過少未被索引。現改為直接寫入建置過程已產生的完整文章 HTML
    # （html_body_pXX），使每篇文章成為可獨立索引、內容完整的靜態網頁。
    def generate_static_article_pages():
        print("Generating static article pages in 'pages/' directory...")
        base_site_url = "https://ludwica-history-lesson.pages.dev/"

        # Create pages directory if it doesn't exist
        os.makedirs('pages', exist_ok=True)

        # [2026-07-19 變更] SEO 描述改由 course_config.json 讀取。
        # 原本從 template.html 以正則撈取 pageSEO，但 template.html 與 index_db.html
        # 的 pageSEO 已各自分岔（41 筆 vs 39 筆、其中 4 筆內容不一致），導致
        # page42/43/45 線上只拿到通用備援文案。現統一以 course_config.json
        # 的 seo_desc 為單一真實來源（44 篇完整）。
        descs = {}
        try:
            import json as _json
            with open('course_config.json', 'r', encoding='utf-8') as f:
                _cfg_articles = _json.load(f).get('articles', {})
            for pid, meta in _cfg_articles.items():
                desc = (meta.get('seo_desc') or '').strip()
                if desc:
                    descs[pid] = desc
            print(f"[OK] Loaded {len(descs)} SEO descriptions from course_config.json")
        except Exception as e:
            print(f"Error loading descriptions for redirects: {e}")

        # 缺漏警示：避免日後新增文章時無聲退回通用文案
        _missing = [pid for pid in pages_data if pid not in descs]
        if _missing:
            print(f"[WARNING] {len(_missing)} page(s) missing seo_desc in course_config.json: {', '.join(sorted(_missing))}")

        # 依 pages_data 的順序建立「上一篇／下一篇」導覽，讓搜尋引擎能在文章之間爬行
        ordered_pids = sorted(pages_data.keys(), key=lambda x: int(re.search(r'\d+', x).group()))

        generated = 0
        empty_body = []

        for pid, data in pages_data.items():
            title = data['title'] + " — Ludwica 的簡單歷史課"
            desc = descs.get(pid, "Ludwica 的簡單歷史課：歷史專題研究與報告。")

            # Determine image URL
            img_path = data.get('img', 'history_banner_bg.png')
            if not img_path:
                img_path = 'history_banner_bg.png'
            image_url = base_site_url + img_path
            # [2026-07-19] Cloudflare Pages 會自動將 /pages/pageXX.html 以 301 轉址到
            # /pages/pageXX（去除副檔名），後者才是實際回應 200 的正規網址。
            # canonical 與 og:url 若仍指向 .html，等同宣告「正規網址是一個會轉址的網址」，
            # 與 Google 實際檢索到的網址互相矛盾，因此一律使用無副檔名的形式。
            # 註：頁面之間的相對連結仍保留 .html，以維持本機直接開啟檔案時的可用性；
            #     這些連結會經過一次 301，對索引無實質影響。
            page_url = base_site_url + f"pages/{pid}"

            # 取出建置過程中已產生的完整文章 HTML（articles_html / html_body_pXX）
            p_num = int(pid[4:])
            body_html = articles_html.get(pid) or globals().get(f"html_body_p{p_num}", "")
            if not body_html:
                empty_body.append(pid)

            # 靜態頁位於 pages/ 子目錄，需把 images/ 等相對路徑往上退一層
            body_html = body_html.replace('src="images/', 'src="../images/')
            body_html = body_html.replace("src='images/", "src='../images/")
            body_html = body_html.replace('href="images/', 'href="../images/')

            # 上一篇／下一篇
            idx = ordered_pids.index(pid)
            nav_parts = []
            if idx > 0:
                prev_pid = ordered_pids[idx - 1]
                nav_parts.append(f'<a href="{prev_pid}.html" rel="prev">← {pages_data[prev_pid]["title"]}</a>')
            if idx < len(ordered_pids) - 1:
                next_pid = ordered_pids[idx + 1]
                nav_parts.append(f'<a href="{next_pid}.html" rel="next">{pages_data[next_pid]["title"]} →</a>')
            prev_next_html = '<nav class="static-prevnext">' + ' | '.join(nav_parts) + '</nav>' if nav_parts else ''

            # JSON-LD 結構化資料
            json_ld = json.dumps({
                "@context": "https://schema.org",
                "@type": "Article",
                "headline": data['title'],
                "description": desc,
                "image": image_url,
                "author": {"@type": "Person", "name": "Ludwica"},
                "publisher": {"@type": "Organization", "name": "Ludwica 的簡單歷史課"},
                "mainEntityOfPage": {"@type": "WebPage", "@id": page_url},
                "inLanguage": "zh-TW"
            }, ensure_ascii=False, indent=None)

            article_html = f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <meta name="description" content="{desc}">
    <link rel="canonical" href="{page_url}">

    <!-- Open Graph Metadata -->
    <meta property="og:title" content="{title}">
    <meta property="og:description" content="{desc}">
    <meta property="og:image" content="{image_url}">
    <meta property="og:type" content="article">
    <meta property="og:url" content="{page_url}">

    <!-- Twitter Card Metadata -->
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="{title}">
    <meta name="twitter:description" content="{desc}">
    <meta name="twitter:image" content="{image_url}">

    <link rel="stylesheet" href="../style.css">
    <script type="application/ld+json">{json_ld}</script>
    <style>
        body {{ background: #f7fafc; margin: 0; }}
        .static-wrap {{ max-width: 900px; margin: 0 auto; padding: 24px 20px 60px; }}
        .static-topbar {{ padding: 14px 0; border-bottom: 1px solid #e2e8f0; margin-bottom: 28px; }}
        .static-topbar a {{ color: #2b6cb0; text-decoration: none; font-weight: 600; }}
        .static-article {{ background: #fff; padding: 32px 34px; border-radius: 12px;
                           box-shadow: 0 4px 14px rgba(0,0,0,.04); line-height: 1.9; }}
        .static-prevnext {{ margin-top: 34px; padding-top: 18px; border-top: 1px solid #e2e8f0;
                            font-size: .95rem; }}
        .static-prevnext a {{ color: #2b6cb0; text-decoration: none; }}
        .static-footer {{ margin-top: 26px; font-size: .85rem; color: #718096; line-height: 1.8; }}
        @media (max-width: 800px) {{ .static-article {{ padding: 20px 16px; }} }}
    </style>
</head>
<body>
<div class="static-wrap">
    <div class="static-topbar"><a href="../">← 回到 Ludwica 的簡單歷史課</a></div>
    <article class="static-article">
{body_html}
{prev_next_html}
    </article>
    <div class="static-footer">
        ⚠️ 本文由 AI 生成，可能包含事實性錯誤，請讀者自行查證。<br>
        🖼️ 文中圖片來源：<a href="https://commons.wikimedia.org/" rel="noopener">Wikimedia Commons</a>。
        📜 本文採用 <a href="https://creativecommons.org/licenses/by-sa/4.0/deed.zh-hant" rel="license noopener">CC BY-SA 4.0</a> 授權。
    </div>
</div>
<script>
    // 靜態頁的分享按鈕：以目前網址為分享目標（正文中的 share-bar 會呼叫此函式）
    function shareTo(platform, pageId) {{
        const shareUrl = window.location.href.split('#')[0];
        const pageTitle = document.title;
        if (platform === 'facebook') {{
            window.open('https://www.facebook.com/sharer/sharer.php?u=' + encodeURIComponent(shareUrl), '_blank', 'width=600,height=400');
        }} else if (platform === 'line') {{
            window.open('https://social-plugins.line.me/lineit/share?url=' + encodeURIComponent(shareUrl), '_blank');
        }} else if (platform === 'twitter') {{
            window.open('https://twitter.com/intent/tweet?url=' + encodeURIComponent(shareUrl) + '&text=' + encodeURIComponent(pageTitle), '_blank', 'width=600,height=400');
        }} else if (platform === 'copy') {{
            navigator.clipboard.writeText(shareUrl);
        }}
    }}
</script>
</body>
</html>
"""
            with open(os.path.join("pages", f"{pid}.html"), 'w', encoding='utf-8', newline='\n') as f:
                f.write(article_html)
            generated += 1

        if empty_body:
            print(f"[WARNING] {len(empty_body)} page(s) produced an EMPTY article body: {', '.join(sorted(empty_body))}")
        print(f"Successfully generated {generated} static article pages under 'pages/'.")

    generate_static_article_pages()

    print("Done! Site successfully built as dynamic 23-topic history portal with full SEO.")



if __name__ == '__main__':
    write_site_outputs()
