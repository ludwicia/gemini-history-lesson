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

3. **註冊網頁路由與元數據（唯一設定檔：course_config.json）**：
   * **修改 `course_config.json`**（全站唯一真實來源，2026-09 全面動態化）：
     * 在 `articles` 新增 `pageXX` 條目，設定 `title`, `file_path`, `ver: "1.0"`, `img`, `seo_title`, `seo_desc`（50–160 字內容摘要）, `map_html`, `image_replacements`。
     * 在 `categories` 找到對應分類，將 `"pageXX"` 加入其 `"pages"` 陣列中。
     * `pages/pageXX.html` 的正文、meta description、og、twitter、canonical、Article JSON-LD 以及首頁索引 **全部由 build 從此處自動產生**。
   * **🚫 嚴禁修改 `build_html_md.py`**（底層已動態化，無需定義變數）。
   * **🚫 無需修改 `index_db.html` 或尋找 `template.html`**（SPA 路由與結構全自動動態載入）。

4. **更新日誌與版本宣告**：
   * 在專案根目錄的 `worklog.md` 頂部插入今日的發布日誌（格式：`#### YYYY-MM-DD (標題)`），條列更新重點（使用 "-" 開頭）。
   * *注意：單純發布文章或修訂內容時，僅需維護文章自身的內容版本（`ver: "1.0"`），不需要遞增 `index_db.html` 的「版面設計」版本號（版面版本僅在修改全站 CSS/JS 結構時才升級）。*

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

     部署完畢後向使用者報告網站已成功更新。

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
