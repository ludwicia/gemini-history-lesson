# build_v5.py - 智慧博物館風格 (V5 試作版) 靜態網頁生成器
import json
import os
import re

def main():
    print("=== 開始構建 Smart Museum V5 試作版網頁 (preview_v5.html) ===")

    # 讀取 course_config.json
    with open("course_config.json", "r", encoding="utf-8") as f:
        config = json.load(f)

    categories = config.get("categories", [])
    articles = config.get("articles", {})

    print(f"找到 {len(categories)} 個主題類別，{len(articles)} 篇註冊文章。")

    # 建立頁面 HTML
    html_content = f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Ludwica 的簡單歷史課 — 智慧博物館 V5 試作版</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Cinzel:wght@600;800&family=Noto+Serif+TC:wght@500;700&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="style_v5.css">
</head>
<body>

  <!-- 頂部導覽列 -->
  <header class="v5-header">
    <div class="v5-nav">
      <div class="v5-logo" onclick="window.scrollTo({{top: 0, behavior: 'smooth'}})">
        <div class="v5-logo-sparkle"></div>
        Ludwica 的簡單歷史課 <span style="font-size:0.75rem; opacity:0.7; font-family:var(--font-sans); color:var(--gold-accent);">V5 智慧博物館版</span>
      </div>
      <nav class="v5-tabs">
        <button class="v5-tab-btn active" onclick="filterCategory('all', this)">🏛️ 全館總覽</button>
        <button class="v5-tab-btn" onclick="filterCategory('rome-medieval', this)">⚔️ 羅馬與中世紀演變</button>
        <button class="v5-tab-btn" onclick="filterCategory('new-world', this)">⛵ 大航海與新大陸</button>
        <button class="v5-tab-btn" onclick="filterCategory('east', this)">🐉 遠東與專題</button>
      </nav>
    </div>
  </header>

  <!-- 英雄主區塊 -->
  <section class="v5-hero">
    <div class="v5-badge">🏛️ 智慧歷史講堂 • V5 設計試作</div>
    <h1>探索歐洲秩序的演變：<span>從羅馬霸權到中世紀誕生</span></h1>
    <p>
      匯聚全站 47 篇深度學術研究報告、120 幅典藏歷史地圖與人物畫像。以極致的深色漸層光暈與博物館卡片樣式，為你呈現古今歷史大事件的全景解構。
    </p>
  </section>

  <!-- 主要內容區 -->
  <main class="v5-container">
"""

    # 針對每個類別生成展區
    category_group_map = {
        "pre-3rd-century-rome": "rome-medieval",
        "rome": "rome-medieval",
        "medieval": "rome-medieval",
        "papal": "rome-medieval",
        "frank": "rome-medieval",
        "hre": "rome-medieval",
        "church": "rome-medieval",
        "trivia": "rome-medieval",
        "us": "new-world",
        "holland": "new-world",
        "qing": "east",
        "novel": "east"
    }

    for cat in categories:
        cat_key = cat["key"]
        cat_title = cat["title"]
        group = category_group_map.get(cat_key, "rome-medieval")
        page_ids = cat.get("pages", [])

        html_content += f"""
    <!-- {cat_title} 展區 -->
    <section class="v5-category-block" data-group="{group}">
      <div class="v5-category-header">
        <span>📜 {cat_title}</span>
      </div>
      <div class="v5-grid">
"""
        for pid in page_ids:
            art = articles.get(pid)
            if not art:
                continue

            title = art.get("title", "未命名文章")
            seo_desc = art.get("seo_desc", "")
            img_path = art.get("img", "history_banner_bg.png")
            ver = art.get("ver", "1.0")
            file_path = art.get("file_path", "")

            # 讀取 MD 檔案內容
            content_html = ""
            if os.path.exists(file_path):
                with open(file_path, "r", encoding="utf-8") as mf:
                    md_text = mf.read()
                    # 簡單轉化標題與段落供模態視窗閱讀
                    clean_md = re.sub(r'#+\s+(.*)', r'<h2 style="color:var(--text-gold); margin-top:1.5rem;">\1</h2>', md_text)
                    clean_md = re.sub(r'\n\n+', '</p><p>', clean_md)
                    content_html = f"<p>{clean_md}</p>"

            # 防護單雙引號與轉義
            escaped_title = title.replace('"', '&quot;').replace("'", "&#39;")

            html_content += f"""
        <div class="v5-card">
          <div class="v5-card-img-wrapper">
            <img src="{img_path}" alt="{escaped_title}" loading="lazy">
            <div class="v5-card-overlay">
              <span class="v5-card-ver">v{ver}</span>
            </div>
          </div>
          <div class="v5-card-content">
            <div>
              <h3 class="v5-card-title">{title}</h3>
              <p class="v5-card-desc">{seo_desc}</p>
            </div>
            <div class="v5-card-footer">
              <span style="font-size:0.8rem; color:var(--text-muted);">專題典藏</span>
              <a href="pages/{pid}.html" target="_blank" class="v5-btn-read">
                📖 閱讀專題全文
              </a>
            </div>
          </div>
        </div>
"""
        html_content += """
      </div>
    </section>
"""

    html_content += """
  </main>

  <footer class="v5-footer">
    <p>Ludwica 的簡單歷史課 &copy; 2026 | 智慧博物館 V5 試做版</p>
  </footer>

  <script>
    function filterCategory(group, btn) {
      document.querySelectorAll('.v5-tab-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');

      const blocks = document.querySelectorAll('.v5-category-block');
      blocks.forEach(block => {
        if (group === 'all' || block.dataset.group === group) {
          block.style.display = 'block';
        } else {
          block.style.display = 'none';
        }
      });
    }
  </script>
</body>
</html>
"""

    with open("preview_v5.html", "w", encoding="utf-8") as out:
        out.write(html_content)

    print("[OK] Successfully generated preview_v5.html without touching index.html!")

if __name__ == "__main__":
    main()
