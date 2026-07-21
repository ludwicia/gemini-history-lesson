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

   > **⚠️ 2026-07-21 架構更新**：SEO 描述（seo_desc）的**唯一真實來源是 `course_config.json`**。
   > 嚴禁把新文章的 desc 只寫進 `template.html` 或 `index_db.html` 的 `pageSEO` 物件——
   > 過去雙軌各寫一份導致兩邊分岔（41 筆 vs 39 筆、多篇線上只剩通用備援文案），
   > 已於 2026-07-19 整併完畢，不可回退。

   **A. 修改 `course_config.json`（SEO 與文章元資料的單一真實來源）**
   - 在 `articles` 中新增 `pageXX` 條目，**必填 `seo_desc`**（50–160 字的內容摘要）與 `seo_title`。
   - 若遺漏 `seo_desc`，`python build_html_md.py` 會印出
     `[WARNING] ... missing seo_desc in course_config.json`，該頁的靜態文章頁
     （`pages/pageXX.html`）將退回通用備援文案。看到此警示必須立即補上。

   **B. 修改 `build_html_md.py` (後台編譯邏輯)**
   - **Python 變數區**：定義 `file_pXX`、`images_pXX` 與 `html_body_pXX`。
   - **首頁網格卡片**：在 `article_cards_html` 組合邏輯中，新增一張這篇文章的首頁卡片。
   - **Python HTML 組裝區**：補上 `__HTML_BODY_PAGEXX__` 與 `__PAGEXX_DATE__` 的取代邏輯。
   - **分類與歸類**：在 `categories` 列表對應的分類中加入 `'pageXX'`。
     **此步驟同時決定首頁「全站文章索引」是否包含這篇文章**——若文章不屬於任何分類
     （例如三欄文獻頁），build 會印出 `[WARNING] ... missing from the static article index`，
     搜尋引擎將無法從首頁爬到該篇。三欄文獻頁（doc=True）會自動歸入「歷史文獻對照」區塊。
   - 注意：`build_static_chunks.py` 以 `import build_html_md` 的副作用讀取上述
     `pages_data`、`html_body_pXX`、`file_pXX` 變數來產生 `api/` JSON，變數命名必須完全一致。

   **C. 修改 `template.html` 與 `index_db.html` (前端版面)**
   - **內文 HTML 容器**（僅 template.html）：`<div id="course-pageXX" class="course-page" ...>`。
   - **SEO JSON-LD**：`hasPart` 陣列加入新文章網址。
   - **JavaScript 左側資訊 (courseInfo)**、**搜尋索引 (searchIndex)**、
     **路由判定 (handleHashRouting)**：照現有格式各補一筆。
   - `pageSEO` 物件中的 `title` 仍需註冊（供 SPA 切換頁面時更新分頁標題），
     但 **desc 以 `course_config.json` 為準**，兩處如有出入以 config 為正。

4. **重新編譯、資料切片與驗證**
   - **執行靜態編譯**：`python build_html_md.py`。此步驟會：
     複製 `index_db.html` → `index.html` 並**注入「全站文章索引」**（44+ 個靜態連結，
     這是搜尋引擎發現文章的主要途徑）；產出 `pages/pageXX.html` **完整正文靜態頁**
     （含 canonical、Article JSON-LD，網址使用無 .html 的正規形式）；更新 sitemap.xml。
   - **執行資料切片**：`python build_static_chunks.py`，生成 `api/` 底下的 JSON 檔案。**（⚠️此步驟極為重要，否則本機伺服器將看不到新文章）**。
   - **執行完整驗證**：`python verify_project.py`，四項檢查全數 `[OK]` 才可進入部署。
     特別注意 build 輸出中的任何 `[WARNING]`（seo_desc 缺漏、文章未入索引、正文為空）都不可忽略。
   - **排版健康度檢查 (本地查驗)**：在執行 Git 提交前，AI 必須在本地對生成的 `index.html` 進行排版抽查，特別是確認新加入的文章中：
     - 沒有未被渲染的 LaTeX 公式（無 `\text{` 或 `span_` 等控制碼）。
     - 表格有被正常解析為 HTML `<table>` 結構（而非一長串的 Markdown 單行純文字）。
     - 參考文獻列表有被正確分割並超連結化。
   - **解決瀏覽器快取 (Local Cache)**：
     - 本機伺服器 (Port 8000) 傳輸 JSON 檔案時常被 Chrome 等瀏覽器過度快取。我們已在 `index_db.html` 的 `fetch` 載入邏輯中對 API 請求添加時間戳記防快取（`?_t=Date.now()`）。
     - 若在本機預覽時仍未看見更新，必須引導使用者在瀏覽器按 **`Ctrl + F5`** 強制重新整理以清除殘留快取。

5. **推送上線 (部署)**
   - 執行命令：`git add .`（確保切片生成的 `api/` 底下 JSON 檔案也一起 staging）
   - 執行命令：`git commit -m "發布：[文章標題] (版面 X.X, 內容 X.X)"`
     （commit 訊息格式依 CLAUDE.md 規範使用中文前綴「發布：」「修復：」「優化：」「校對：」，
     並附上雙軌版本號；勿使用英文 `feat:`/`docs:` 前綴。）
   - 執行命令：`git push`
   - 向使用者回報部署成功，請其至線上確認。部署由 Cloudflare Pages 自動觸發（約 1–2 分鐘）。
     線上正規網址為無副檔名形式（如 `/pages/page09`），`.html` 會被 301 轉址，屬正常現象。
