# AI 專屬工作技能 (Skills SOP)

## 技能名稱：發布新文章上線與更新內容 (Publish / Update Article)

### 觸發條件
當使用者要求將新匯入的 Markdown 文章「推送上線」、更新現有文章內容、或是將新文章加入首頁選單時。

### 執行流程
1. **編輯或新增 Markdown 檔案**
   - 針對使用者的要求修改現有 `.md` 檔案，或是將全新的 `.md` 檔案放入 `course/` 或是 `skills/` 資料夾中。

2. **撰寫更新日誌 (worklog.md)**
   - 在 `worklog.md` 檔案最上方新增一筆更新紀錄（格式：`#### YYYY-MM-DD (標題)`），並條列更新重點（使用 `- ` 作為開頭）。

3. **註冊新文章 (若是全新文章，才需要執行此步驟)**
   由於專案架構已經將版面 (template.html) 與邏輯 (build_html_md.py) 分離，必須在以下兩個檔案精準插入新文章的設定：

   **A. 修改 `build_html_md.py`**
   - **Python 變數區**：定義 `file_pXX`、`images_pXX` 與 `html_body_pXX`。
   - **首頁網格卡片**：在 `article_cards_html` 組合邏輯中，新增一張這篇文章的首頁卡片（包含 `<div class="article-card" ...>` 與點擊跳轉事件）。
   - **Python HTML 組裝區**：在腳本最尾端補上 `final_html = final_html.replace('__HTML_BODY_PAGEXX__', html_body_pXX)` 與 `__PAGEXX_DATE__` 的取代邏輯。
   - **Sitemap.xml 區塊**：在 `sitemap_content` 中加入新的 `<url>` 區塊。

   **B. 修改 `template.html`**
   - **內文 HTML 容器**：在 `<main>` 區塊內新增 `<div id="course-pageXX" class="course-page" style="display: none;">__HTML_BODY_PAGEXX__</div>`。
   - **SEO JSON-LD**：在 `<script type="application/ld+json">` 的 `hasPart` 陣列中加入新文章網址。
   - **JavaScript 左側資訊 (courseInfo)**：在 JS 內精準新增 `pageXX: { ... }` 包含更新日期、版本等 HTML 字串。
   - **JavaScript 網頁 Meta (pageSEO)**：在 JS 內新增 `pageXX: { title: '...', desc: '...' }`。
   - **JavaScript 搜尋索引 (searchIndex)**：在陣列中推入 `{ id: 'pageXX', name: '...' }`。
   - **JavaScript 路由判定 (matchedPage)**：在 `handleHashRouting` 陣列中補上 `'pageXX'`。

4. **重新編譯與驗證**
   - 執行命令：`python build_html_md.py`。
   - 確保終端機沒有報錯，且順利產生乾淨無語法錯誤的 `index.html`。

5. **推送上線 (部署)**
   - 執行命令：`git add .`
   - 執行命令：`git commit -m "feat/docs: update or add article [文章標題]"`
   - 執行命令：`git push`
   - 向使用者回報部署成功，請其至線上確認。
