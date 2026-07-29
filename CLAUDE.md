# CLAUDE.md (歷史專案專屬 AI 協作守則) 🏛️

本專案是「Gemini 的簡單歷史課」自動化網頁生成專案。為確保每次網頁設計更新、文章修訂都符合專案架構並維持優雅排版，請遵循以下 AI 協作守則。

## 🛠️ 專案基礎指令 (Commands)
* **完整發布流程（首選，2026-07-21 起）**：`python run_build.py`
  一次完成「建置 → 資料切片 → Firestore 同步 → 索引驗證 → 完整驗證」，任一環節失敗即中止。
  **勿再分別執行 `build_html_md.py` + `build_static_chunks.py` + `verify_project.py`**，
  那樣會重複建置（歷史問題：`build_static_chunks.py` 的 `import build_html_md` 會觸發整份重跑）。
* **僅重建網頁**：`python build_html_md.py` (只改排版、想快速看結果時使用)
* **部署上線**：
  ```bash
  git add .
  git commit -m "發布或優化：[填寫具體變更]"
  git push
  ```

## 🎨 雙軌獨立版本號規範 (Versioning Rules)
本專案採用**雙軌獨立版本號**以區分排版變更與文章修訂，修改時請嚴格遵守：
1. **版面設計版本 (Layout & Design Version)**：
   * **升級時機**：變更 CSS 樣式、JavaScript 互動、網頁結構或底層轉換腳本邏輯時。
   * **修改位置**：`index_db.html` 與 `template.html` 內版權卡片的「`版面設計：X.X`」（以文字搜尋定位，勿依賴行號）。兩檔皆需同步修改。
2. **內容版本 (Content Version)**：
   * **升級時機**：修改歷史文章內容、史實勘誤、錯字修正或段落補充時。
   * **修改位置**：各文章傳入 `process_markdown()` / `process_3col_document()` 的版本參數（如 `"1.1"`），該值由 `version_badge`（`build_html_md.py` 約第 98 行）渲染為頁面上的「內容版本」徽章。同時同步更新 `course_config.json` 中對應文章的 `ver` 欄位。

## 📝 程式碼與編輯規範 (Development Guidelines)
1. **編碼前先研究 (Think & Verify)**：
   * 專案內的歷史長文（.md 檔）內容較大，在讀取或修改內文時，必須精確讀取對應的段落，切勿自行胡亂假設史實，亦不可擅自截斷內容。
   * 調整視覺設計時，必須保持**響應式佈局**的完整性：
     * **桌機版 (Width > 1200px)**：三欄式（左目錄 TOC、中主內文、右搜尋與版本卡片）。
     * **平板/窄螢幕 (Width 800px ~ 1200px)**：兩欄式，右側邊欄轉為底部懸浮欄。
     * **手機版 (Width < 800px)**：單欄式，左側目錄隱藏，中間 H2 章節轉為點擊摺疊展開，右側轉為底部懸浮摺疊欄。
2. **精準修改與文繞圖 (Surgical Changes & Image Wrap)**：
   * 修改 `build_html_md.py` 時，應使用精準修改工具，只調整必要代碼，保留原有的 Markdown 預處理邏輯（Word 單行換行修復機制）。
   * 若新增歷史圖片，應將圖片與圖說登錄於相關列表中，並確保圖片套用 `<figure class="image-left">` 浮動樣式以維持高質感文繞圖（Text Wrap）效果。
   * **本地圖片優先**：新增圖片時，應將原圖下載存放至 `images/` 資料夾中，並使用相對路徑載入（且務必加上 `loading="lazy"`）。嚴禁直接外部連結（Hotlinking）Wikimedia 或其他圖庫的高畫質原圖，以免使用者載入網頁時觸發 HTTP 429 請求過多限制導致破圖。
   * **入庫前必須壓縮**（2026-07-21 新增）：任何圖片存入 `images/` 前，長邊縮至 **1600px 以內**、照片類存 **JPEG 品質 82**（`optimize` + `progressive`），單檔以 500 KB 為警戒線。詳細規格與 Pillow 範例見 `skills/03_add_images.md`。
3. **極簡優先 (Simplicity First)**：
   * 堅持使用 Vanilla JavaScript 與 Vanilla CSS 進行開發，除非使用者要求，否則不引入外部繁重的框架或程式庫。
4. **目標驅動 (Goal-Driven)**：
   * 每次修改完腳本或文章後，必須立刻本機運行 `python build_html_md.py`，驗證生成出的 `index.html` 結構是否完整、標籤是否閉合、搜尋引擎是否運作正常，再向使用者回報。
5. **溝通與修改授權原則 (Communication & Modification Consent)**：
   * **先解釋、後詢問、再執行**：當在代碼或文章中發現疑似非功能性冗餘（例如第三方工具的自動頁尾、生成時間戳記）、元數據，或者不確定是否需要保留的歷史遺留文字時，**嚴禁直接私自刪除**。
   * **標準作業流程**：AI 必須「先向使用者解釋該內容的來源、用途與潛在影響」，接著「明確詢問使用者是否同意刪除或修改」，在獲得使用者明示的回覆同意後，方可執行代碼修改或檔案刪除。
6. **Google Docs 連結處理規範 (Google Docs Link Handling)**：
   * 當使用者提供 Google Docs 連結（包含 `docs.google.com/document/`）並要求讀取、分析或新增為新課程時，AI **必須使用本機的 `import_gdoc.py` 腳本（或其相同的匯出邏輯）來獲取清潔的 Markdown 內文**，嚴禁使用外部網頁讀取工具或直接爬取，以確保每次獲取之內文格式、一級標題、段落與引註表現完全一致。
   * 範例指令：`python import_gdoc.py "https://docs.google.com/document/d/[DOC_ID]/edit"`（建議使用 Windows 系統上的全域 Python 3.13 執行，以確保套件完整性）。

## 🔍 SEO 優化守則 (SEO Checklist for New Content)
每次新增或修改歷史專題頁面時，**必須同步完成以下 SEO 項目**：

> **⚠️ 2026-07-21 架構更新**：本節與舊版差異甚大。SEO 描述的**唯一真實來源是
> `course_config.json` 的 `seo_desc`**；靜態文章頁與 sitemap 由 `build_html_md.py`
> 自動產生，勿再手動維護。歷史教訓：desc 曾同時寫在 `template.html` 與
> `index_db.html` 的 `pageSEO` 而分岔，導致多篇文章線上只剩通用備援文案。

1. **`course_config.json` 註冊（最重要，取代舊的 pageSEO desc 流程）**：
   * 新增文章的 `seo_title`（格式：`[頁面主題] — Ludwica 的簡單歷史課`）與
     `seo_desc`（50–160 字的精確內容摘要）。
   * 靜態文章頁 `pages/pageXX.html` 的 meta description、og、twitter、canonical、
     Article JSON-LD **全部由 build 從此處自動產生**。

2. **靜態 Meta Tags 同步更新（首頁層級）**：
   * 更新首頁 `<title>`、`<meta name="description">`、`<meta name="keywords">`，
     以及 `og:*`、`twitter:*`，涵蓋新增主題。

3. **JSON-LD 結構化資料更新**：
   * 在首頁 `CollectionPage` JSON-LD 的 `hasPart` 陣列新增對應 `Article` 條目。

4. **JavaScript 註冊（`template.html` 與 `index_db.html` 兩處同步）**：
   * `pageSEO` 物件：註冊 `title`（desc 以 course_config.json 為準，兩處如有出入以 config 為正）。
   * `initGlobalSearchIndex()` 的 `pages` 陣列：新增 `{ id: 'pageXX', name: '頁面名稱' }`。
   * `courseInfo` 物件：新增版本、生成來源與工程資訊。

5. **自動產生項目（勿手動維護，但必須驗證）**：
   * `sitemap.xml`、`robots.txt`、`pages/pageXX.html` 靜態文章頁、首頁「全站文章索引」
     均由 `python build_html_md.py` 自動產生。網址一律使用**無 .html 的正規形式**
     （Cloudflare Pages 會將 .html 301 轉址）。
   * build 後執行 `python verify_project.py`，四項檢查全數 `[OK]`；
     build 輸出的任何 `[WARNING]`（seo_desc 缺漏、文章未入首頁索引、正文為空）都不可忽略。
   * ⚠️ `run_build.py` 第 4 步為驗證非複製；嚴禁在 build 之後再手動
     `copy index_db.html index.html`，否則會覆蓋掉已注入的全站文章索引。
