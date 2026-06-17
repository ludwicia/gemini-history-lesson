# AI 專屬工作技能 (Skills SOP)

## 技能名稱：發布新文章上線與更新內容 (Publish / Update Article)

### 觸發條件
當使用者要求將新匯入的 Markdown 文章「推送上線」、更新現有文章內容、或是將新文章加入首頁選單時。

### 執行流程
1. **編輯或新增 Markdown 檔案**
   - 針對使用者的要求修改現有 `.md` 檔案，或是將全新的 `.md` 檔案放入 `course/` 或是 `skills/` 資料夾中。
   - **引用文獻格式化規範**：必須確保文章底部的「引用的著作」或參考文獻列表統一格式為 `1. [標題](連結)` 的乾淨超連結形式。需移除任何 `檢索日期：...`、多餘的逗號以及重複展示的 `[http...](http...)` 原網址字串，以保持網底引用列表的極簡與美觀。

2. **撰寫更新日誌 (worklog.md)**
   - 在 `worklog.md` 檔案最上方新增一筆更新紀錄（格式：`#### YYYY-MM-DD (標題)`），並條列更新重點（使用 `- ` 作為開頭）。

3. **註冊與同步新文章 (若是全新文章，才需要執行此步驟)**
   由於專案架構區分為「靜態編譯版 (template.html)」與「本機動態資料庫版 (index_db.html)」，必須在以下檔案精準插入新文章的設定：

   **A. 修改 `build_html_md.py` (後台編譯邏輯)**
   - **Python 變數區**：定義 `file_pXX`、`images_pXX` 與 `html_body_pXX`。
   - **首頁網格卡片**：在 `article_cards_html` 組合邏輯中，新增一張這篇文章的首頁卡片（包含 `<div class="article-card" ...>` 與點擊跳轉事件）。
   - **Python HTML 組裝區**：在腳本最尾端補上 `final_html = final_html.replace('__HTML_BODY_PAGEXX__', html_body_pXX)` 與 `__PAGEXX_DATE__` 的取代邏輯。
   - **分類與歸類**：在 `categories` 列表對應的分類中加入 `'pageXX'`。

   **B. 修改 `template.html` (靜態版版面)**
   - **內文 HTML 容器**：在 `<main>` 區塊內新增 `<div id="course-pageXX" class="course-page" style="display: none;">__HTML_BODY_PAGEXX__</div>`。
   - **SEO JSON-LD**：在 `<script type="application/ld+json">` 的 `hasPart` 陣列中加入新文章網址。
   - **JavaScript 左側資訊 (courseInfo)**：在 JS 內精準新增 `pageXX: { ... }` 包含更新日期、版本等 HTML 字串。
   - **JavaScript 網頁 Meta (pageSEO)**：在 JS 內新增 `pageXX: { title: '...', desc: '...' }`。
   - **JavaScript 搜尋索引 (searchIndex)**：在陣列中推入 `{ id: 'pageXX', name: '...' }`。
   - **JavaScript 路由判定 (matchedPage)**：在 `handleHashRouting` 陣列中補上 `'pageXX'`。

   **C. 修改 `index_db.html` (本機動態版版面)**
   - 同步在 `index_db.html` 中進行與 `template.html` 相同的 **SEO JSON-LD**、**網頁 Meta (pageSEO)** 註冊，以確保雙軌版面同步。

4. **重新編譯、資料切片與驗證**
   - **執行靜態編譯**：`python build_html_md.py`，生成 `index.html`。
   - **執行資料切片**：`python build_static_chunks.py`，將文章與索引切片生成為 `api/` 底下的 JSON 檔案。**（⚠️此步驟極為重要，否則本機伺服器將看不到新文章）**。
   - **排版健康度檢查 (本地查驗)**：在執行 Git 提交前，AI 必須在本地對生成的 `index.html` 進行排版抽查，特別是確認新加入的文章中：
     - 沒有未被渲染的 LaTeX 公式（無 `\text{` 或 `span_` 等控制碼）。
     - 表格有被正常解析為 HTML `<table>` 結構（而非一長串的 Markdown 單行純文字）。
     - 參考文獻列表有被正確分割並超連結化。
   - **解決瀏覽器快取 (Local Cache)**：
     - 本機伺服器 (Port 8000) 傳輸 JSON 檔案時常被 Chrome 等瀏覽器過度快取。我們已在 `index_db.html` 的 `fetch` 載入邏輯中對 API 請求添加時間戳記防快取（`?_t=Date.now()`）。
     - 若在本機預覽時仍未看見更新，必須引導使用者在瀏覽器按 **`Ctrl + F5`** 強制重新整理以清除殘留快取。

5. **推送上線 (部署)**
   - 執行命令：`git add .`（確保切片生成的 `api/` 底下 JSON 檔案也一起 staging）
   - 執行命令：`git commit -m "feat/docs: update or add article [文章標題]"`
   - 執行命令：`git push`
   - 向使用者回報部署成功，請其至線上確認。
