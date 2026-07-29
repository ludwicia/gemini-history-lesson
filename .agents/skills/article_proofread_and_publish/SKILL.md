---
name: article_proofread_and_publish
description: Handles the step-by-step workflow for importing, auditing, proofreading, and publishing history articles from Google Docs or raw drafts.
---

# 歷史課專題文章：審核、校對與發布工作流

當使用者提供新的歷史文章（無論是 Google Docs 連結或直接輸入的草稿）時，必須嚴格遵循以下「先審核校對、後確認發布」的雙階段工作流。

## 階段一：導入、審核與校對（暫不發布）

當接收到文章時，**絕對不要直接發布**，應先執行以下步驟：

1. **內文導入**：
   * 若為 Google Docs 連結，必須使用 `python course/import_gdoc.py "<Google_Doc_URL>"` 腳本導入清潔的 Markdown 內文。
   * 若為直接輸入之草稿，直接進行下一步。

2. **史實與用語審核**：
   * **史實勘誤**：利用搜尋或專業知識，核對文章中的年代、人物、戰役、地理名稱及事件因果關係，找出事實性錯誤或時空錯亂（例如在五世紀出現十四世紀才建造的米蘭大教堂）。
   * **錯別字與翻譯修正**：找出文章中的打字錯誤、語句不通順、以及生硬的英文直譯（如 half-sister 直譯為「半妹」）。
   * **不正式現代流行語過濾**：特別注意過濾任何與嚴肅歷史體裁不符的**現代科技/資料庫黑話**（如 sharding、rollback、root權限、格式化、代碼等）及**網路/遊戲流行語**（如對線、外掛、蹭飯、斷線擺爛等）。

3. **生成修正草稿並回報**：
   * 將校對並修正後的 Markdown 內文寫入至臨時檔案中（例如 `<appDataDir>\brain\<conversation-id>\proofread_article_draft.md`）。
   * 在對話中向使用者回報：
     1. 列出審核出的「史實錯誤」、「錯別字與翻譯偏差」與「不當現代流行語/俚語」清單及修正理由。
     2. 提供修正後草稿檔案的 Markdown 連結供使用者審閱。
     3. **停止動作並等待使用者回覆**，詢問是否同意發布以及應歸類於哪個分類。

---

## 階段二：確認發布與自動化部署

一旦使用者審閱完草稿並**明示同意發布**後，執行以下發布流程：

1. **確定分類與配置頁面號**：
   * 根據使用者的指示，確定文章分類（例如「中世紀諸民族記」、「三世紀危機後的羅馬帝國」等）。
   * 檢查當前已有頁面（如 `page01` 至 `pageXX`），為新文章分配下一個順序的頁面 ID（如 `page(XX+1)`）。
   * 將修正後的 Markdown 檔案以規範名稱存入 `course/` 目錄中。

2. **生成高質感配圖**：
   * 使用 `generate_image` 工具繪製一張符合該歷史主題、具備 premium 質感的油畫風格或歷史插圖。
   * 將生成出的圖片複製或移動至 `images/` 目錄，命名為適當的英文名稱，並於前台載入時使用相對路徑與 `loading="lazy"` 屬性。

3. **註冊網頁路由與元數據**：
   * **修改 `build_html_md.py`**：
     * 定義新頁面的 `file_pXX`、`map_pXX`（Banner 及圖說）與 `images_pXX` 變數。
     * 新增其 `process_markdown` 調用，設定內容版本為 `1.0`。
     * 在 `pages_data` 中新增該頁面的標題、封面圖、版本與 doc 標記。
     * 在 `categories` 陣列中，將頁面 ID 新增至對應的分類下。
     * 在 HTML 生成替換部分，新增 `__HTML_BODY_PAGE[XX]__` 與 `__PAGE[XX]_DATE__` 的取代邏輯。
   * **修改 `course_config.json`**（SEO 描述的唯一真實來源，2026-07-19 起）：
     * 新增該頁面的 `seo_title` 與 `seo_desc`（50–160 字的精準內容摘要）。
     * `pages/pageXX.html` 的 meta description、og、twitter、canonical 與 Article
       JSON-LD **全部由 build 從此處自動產生**。若遺漏，build 會印出
       `[WARNING] ... missing seo_desc`，該頁將退回通用備援文案。
   * **修改 `index_db.html`**（動態版 SPA 入口）：
     * 在 `pageSEO` 物件中新增該頁面的 `title`（**desc 以 `course_config.json` 為準**，
       勿只寫在此處——雙軌各寫一份曾導致兩邊分岔、多篇文章線上只剩通用文案）。
     * 在 `<head>` 的 JSON-LD 結構化資料 `hasPart` 陣列中新增對應的 `Article` 項目。

4. **更新日誌與版本宣告**：
   * 在 `index_db.html` 中，將 `版面設計` 版本號手動遞增（如 4.7 升級至 4.8），並更新發布日期。
   * 在專案根目錄的 `worklog.md` 頂部插入今日的發布日誌，詳細說明發布的文章、修正的史實、新增的插圖與路由調整。

5. **編譯、Firestore 上傳與 Git 部署**：

   > **⚠️ 2026-07-21 重大變更：改為單一指令，且嚴禁再手動複製 index.html**

   * 在本機執行**單一指令**完成全部編譯與驗證：
     ```bash
     python run_build.py
     ```
     它會依序完成：建置（單次）→ `api/` JSON 切片 → Firestore 上傳（有金鑰時）
     → index.html 文章索引驗證 → `verify_project.py` 完整驗證。任一環節失敗即中止。

   * **嚴禁執行 `copy index_db.html index.html`**（舊版守則要求的步驟，現已作廢）。
     原因：`build_html_md.py` 會先把 `index_db.html` 複製為 `index.html`，
     **再於其中注入「全站文章索引」的 47 個靜態文章連結**。這些連結是搜尋引擎
     發現文章的主要途徑（首頁其餘內容全由 JavaScript 從 Firestore 載入，
     初始 HTML 原本可見文字僅約 390 字元、0 個文章連結，導致整站無法被索引）。
     事後再複製一次會把注入的索引整段覆蓋掉，且**不會有任何錯誤訊息**。
     若不慎執行了，重跑 `python run_build.py` 即可修復。

   * **亦不需要**再分別執行 `build_html_md.py`、`build_static_chunks.py`、
     `migrate_to_firestore.py`。`build_static_chunks.py` 內含 `import build_html_md`，
     單獨執行會使整份建置重跑一次（`run_build.py` 已在單一行程內處理妥當）。

   * 最後執行 Git 命令部署上線：
     ```bash
     git add .
     git commit -m "發布：新增[專題名稱]專題 (版面 X.X, 內容 1.0)"
     git push
     ```
   * 部署完畢後向使用者報告網站已成功更新。

---

## 重要注意事項

* **主入口為 `index.html`**：由 `build_html_md.py` 從 `index_db.html` 複製後**再注入全站文章索引**而成。
  因此 `index.html` 與 `index_db.html` **並不相同**（多出約 110 行的靜態文章連結），
  只能由 build 產生，不可手動複製覆蓋。要修改版面請改 `index_db.html` 再重新 build。
* **`index_static.html` 已於 2026-07-19 刪除**：該檔全專案無任何引用（不在 sitemap、
  不被任何 JS 載入），僅造成混淆。勿再產出或引用它。
* **`pages/pageXX.html` 是含完整正文的靜態文章頁**（非跳轉頁），由 build 自動產生，
  含各自的 canonical 與 Article JSON-LD。canonical 一律使用無 `.html` 的正規網址
  （Cloudflare Pages 會將 `.html` 301 轉址）。
* **Firebase 配置**位於 `js/firebase-config.js`，Firestore 讀取服務位於 `js/firestore-service.js`。
* **Service Account 金鑰**（`ludwica-history-firebase-adminsdk-*.json`）已在 `.gitignore` 中排除，嚴禁提交至 Git。
* **圖片**仍然存放在本地 `images/` 目錄，由 Cloudflare Pages 靜態託管，不上傳至 Firebase Storage。
