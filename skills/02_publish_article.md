# AI 專屬工作技能 (Skills SOP)

## 技能名稱：發布新文章上線與更新內容 (Publish / Update Article)

### 觸發條件

當使用者要求將新匯入的 Markdown 文章「推送上線」、更新現有文章內容、或是將新文章加入首頁選單時。

### 執行流程

1. **編輯或新增 Markdown 檔案**
   - 針對使用者的要求修改現有 `.md` 檔案，或是將全新的 `.md` 檔案放入 `course/` 或是 `skills/` 資料夾中。
   - **引用文獻格式化規範**：必須確保文章底部的「引用的著作」或參考文獻列表統一格式為 `1. [標題](連結)` 的乾淨超連結形式。需移除任何 `檢索日期：...`、多餘的逗號以及重複展示的 `[http...](http...)` 原網址字串，以保持網底引用列表的極簡與美觀。

2. **撰寫更新日誌 (worklog.md)**
   - 在 `worklog.md` 檔案最上方新增一筆更新紀錄（格式：`#### YYYY-MM-DD (標題)`），並條列更新重點（使用 "-" 作為開頭）。

3. **註冊新文章（唯一設定檔：course_config.json）**

   > **💡 2026-09 重構後：全站唯一真實來源為 `course_config.json`**
   > 底層已全面動態化，**嚴禁修改 `build_html_md.py`**（不需要定義變數），亦**不需要修改 `index_db.html` 或尋找已廢棄的 `template.html`**。

   打開 [`course_config.json`](course_config.json)，僅需完成兩處設定：

   - **A. 在 `articles` 字典中新增 `pageXX` 條目**：

     ```json
     "pageXX": {
       "title": "文章標題",
       "file_path": "course/文章完整檔名.md",
       "ver": "1.0",
       "doc": false,
       "img": "images/配圖檔名.jpg",
       "bg_pos": "center",
       "seo_title": "標題 — Ludwica 的簡單歷史課",
       "seo_desc": "50–160 字的精準內容摘要（必填，供靜態頁、搜尋引擎與社群分享）",
       "map_html": "<figure class=\"image-left\" style=\"width: 38%; margin-bottom: 20px;\"><img src=\"images/配圖檔名.jpg\" alt=\"標題\" loading=\"lazy\"><figcaption class=\"caption\">配圖說明文字</figcaption></figure>\\n",
       "image_replacements": [
         {
           "pattern": "(<h2.*?>章節標題.*?</h2>)",
           "url": "images/內文配圖.jpg",
           "caption": "配圖詳細圖說"
         }
       ]
     }
     ```

   - **B. 在 `categories` 中分配分類歸屬**：
     - 找到文章所屬的分類（如 `hre`, `rome`, `church`, `qing` 等），將 `"pageXX"` 加入其 `"pages"` 陣列中。
     - *注意：若為歷史文獻對照（`doc: true`），則不必加入分類，系統會自動歸入歷史文獻專區。*

4. **重新編譯、資料切片與驗證**

   > **✅ 2026-07-21 起：一個指令即可完成本步驟全部工作**
   >
   > ```bash
   > python run_build.py
   > ```
   >
   > 它依序執行：建置（單次）→ 資料切片 → Firestore 同步（有金鑰時）→
   > index.html 索引驗證 → `verify_project.py` 完整驗證。任一環節失敗即中止。
   > **不需要**再分別執行 `build_html_md.py`、`build_static_chunks.py`、
   > `verify_project.py`——那樣會重複建置、也多耗時間。
   >
   > 以下為各步驟的說明，供除錯時參考。

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
