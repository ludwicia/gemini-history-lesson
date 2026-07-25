import os
import re
import sys
import filecmp
import json

def check_files_exist():
    print("Checking referenced markdown files...")
    if not os.path.exists('course_config.json'):
        print("[ERROR] course_config.json is missing.")
        return False
    with open('course_config.json', 'r', encoding='utf-8') as f:
        config = json.load(f)

    checked_count = 0
    articles = config.get("articles", {})
    for pid, art in articles.items():
        file_path = art.get("file_path")
        if file_path:
            if not os.path.exists(file_path):
                print(f"[ERROR] File {file_path} referenced in {pid} does not exist!")
                return False
            checked_count += 1
        file_path_en = art.get("file_path_en")
        if file_path_en:
            if not os.path.exists(file_path_en):
                print(f"[ERROR] English file {file_path_en} referenced in {pid} does not exist!")
                return False
            checked_count += 1
    print(f"[OK] All {checked_count} referenced markdown files exist.")
    return True

def check_images_exist():
    print("Checking referenced images...")
    if not os.path.exists('course_config.json'):
        print("[ERROR] course_config.json is missing.")
        return False
    with open('course_config.json', 'r', encoding='utf-8') as f:
        config = json.load(f)

    config_images = set()
    articles = config.get("articles", {})

    # Gather all images from config
    for pid, art in articles.items():
        img_path = art.get("img")
        if img_path and img_path.startswith("images/"):
            config_images.add(img_path)

        map_html = art.get("map_html")
        if map_html:
            for img_match in re.findall(r'src=["\'](images/[^"\']+)["\']', map_html):
                config_images.add(img_match)

        repls = art.get("image_replacements", [])
        for item in repls:
            u = item.get("url")
            if u and u.startswith("images/"):
                config_images.add(u)

    # Gather category images
    for cat in config.get("categories", []):
        c_img = cat.get("img")
        if c_img and c_img.startswith("images/"):
            config_images.add(c_img)

    # Gather images from markdown files
    md_images = set()
    for pid, art in articles.items():
        for path_key in ["file_path", "file_path_en"]:
            file_path = art.get(path_key)
            if file_path and os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                # Match standard md images: ![alt](path)
                for img_match in re.findall(r'!\[.*?\]\((images/[^)]+)\)', content):
                    md_images.add(img_match)
                # Match HTML img tags: <img src="path" ...>
                for img_match in re.findall(r'<img\s+[^>]*src=["\'](images/[^"\']+)["\']', content):
                    md_images.add(img_match)

    all_referenced_images = config_images.union(md_images)
    missing_images = []

    for img in all_referenced_images:
        normalized_path = img.replace('/', os.sep)
        if not os.path.exists(normalized_path):
            missing_images.append(img)

    if missing_images:
        print(f"[ERROR] Found {len(missing_images)} missing images:")
        for img in missing_images:
            print(f"   - {img}")
        return False

    print(f"[OK] All {len(all_referenced_images)} referenced images exist in filesystem.")
    return True

def check_index_sync():
    """
    [2026-07-19 更新] index.html 不再與 index_db.html 完全相同。

    build_html_md.py 會先把 index_db.html 複製為 index.html，再於
    STATIC_ARTICLE_INDEX 標記之間注入「全站文章索引」的靜態連結
    （首頁文章清單原本全由 JavaScript 從 Firestore 載入，初始 HTML
    沒有任何指向文章的連結，導致搜尋引擎無法爬行到任何一篇文章）。

    因此同步檢查改為：把 index.html 標記之間的注入內容清空後，
    必須與 index_db.html 完全一致——確保除了注入區塊以外沒有其他分岔。
    """
    print("Checking if index.html is synchronized with index_db.html...")
    if not os.path.exists('index.html') or not os.path.exists('index_db.html'):
        print("[ERROR] index.html or index_db.html is missing.")
        return False

    with open('index.html', 'r', encoding='utf-8', newline='') as f:
        index_html = f.read()
    with open('index_db.html', 'r', encoding='utf-8', newline='') as f:
        index_db_html = f.read()

    start_marker = '<!-- STATIC_ARTICLE_INDEX_START -->'
    end_marker = '<!-- STATIC_ARTICLE_INDEX_END -->'

    if start_marker not in index_db_html or end_marker not in index_db_html:
        print("[ERROR] STATIC_ARTICLE_INDEX markers are missing from index_db.html!")
        print("   These markers are the anchor for injecting the crawlable article index.")
        return False

    if start_marker not in index_html or end_marker not in index_html:
        print("[ERROR] STATIC_ARTICLE_INDEX markers are missing from index.html!")
        return False

    pattern = re.escape(start_marker) + r'.*?' + re.escape(end_marker)
    placeholder = start_marker + '\n    ' + end_marker

    stripped_index = re.sub(pattern, placeholder, index_html, flags=re.DOTALL).replace('\r\n', '\n')
    stripped_db = re.sub(pattern, placeholder, index_db_html, flags=re.DOTALL).replace('\r\n', '\n')

    if stripped_index != stripped_db:

        print("[ERROR] index.html is OUT OF SYNC with index_db.html (outside the injected index)!")
        print("   Please rebuild the site so index.html is regenerated from index_db.html:")
        print("   cmd: python build_html_md.py")
        return False

    link_count = len(re.findall(r'<li><a href="pages/page\d+\.html">', index_html))
    if link_count == 0:
        print("[ERROR] No static article links were injected into index.html!")
        print("   Search engines will not be able to discover any article. Please rebuild.")
        return False

    print(f"[OK] index.html is in sync with index_db.html ({link_count} static article links injected).")
    return True


def check_static_article_pages():
    """
    [2026-07-19 新增] 確認 pages/ 底下是真正含正文的靜態文章頁。

    這些頁面原為 window.location.replace 跳轉空殼，導致 44 篇文章在
    搜尋引擎眼中塌縮成首頁同一個網址、整站無法被索引。此檢查避免日後
    不慎回退。
    """
    print("Checking static article pages under 'pages/'...")
    if not os.path.isdir('pages'):
        print("[ERROR] 'pages/' directory is missing.")
        return False

    page_files = sorted(f for f in os.listdir('pages') if f.endswith('.html'))
    if not page_files:
        print("[ERROR] No page found under 'pages/'.")
        return False

    problems = []
    for name in page_files:
        path = os.path.join('pages', name)
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()

        if 'window.location.replace' in content:
            problems.append(f"{name}: 仍是 JS 跳轉空殼頁")
        if 'rel="canonical"' not in content:
            problems.append(f"{name}: 缺少 canonical")
        if 'src="images/' in content:
            problems.append(f"{name}: 圖片路徑未修正為 ../images/")
        # 粗估正文長度：移除標籤後的純文字
        body_match = re.search(r'<article[^>]*>(.*?)</article>', content, re.DOTALL)
        body_text = re.sub(r'<[^>]+>', '', body_match.group(1)) if body_match else ''
        if len(body_text.strip()) < 500:
            problems.append(f"{name}: 正文過短（{len(body_text.strip())} 字），可能未寫入內容")

    if problems:
        print(f"[ERROR] Found {len(problems)} problem(s) in static article pages:")
        for p in problems[:20]:
            print(f"   - {p}")
        return False

    print(f"[OK] All {len(page_files)} static article pages contain full content.")
    return True

def main():
    print("=== Running Ludwica Project Verification ===\n")
    success = True

    if not check_files_exist():
        success = False
    print()

    if not check_images_exist():
        success = False
    print()

    if not check_index_sync():
        success = False
    print()

    if not check_static_article_pages():
        success = False
    print()

    if not success:
        print("[FAIL] Project verification FAILED.")
        sys.exit(1)

    print("[SUCCESS] Project verification PASSED successfully!")
    sys.exit(0)

if __name__ == '__main__':
    main()
