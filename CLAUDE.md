# CLAUDE.md (歷史專案專屬 AI 協作守則) 🏛️

本專案是「Gemini 的簡單歷史課」自動化網頁生成專案。為確保每次網頁設計更新、文章修訂都符合專案架構並維持優雅排版，請遵循以下 AI 協作守則。

## 🛠️ 專案基礎指令 (Commands)
* **網頁生成**：`python build_html_md.py` (每次修改 Markdown 或 Python 腳本後，必須在本機執行此指令以覆寫 `index.html` 並檢查排版)
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
   * **修改位置**：`build_html_md.py` 內 HTML 模板中的版權卡片（約第 496 行：`<div>版面設計：X.X</div>`）。
2. **內容版本 (Content Version)**：
   * **升級時機**：修改歷史文章內容、史實勘誤、錯字修正或段落補充時。
   * **修改位置**：`build_html_md.py` 中的 `version_badge` 變數（約第 39 行：`內容版本：X.X`）。

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

1. **靜態 Meta Tags 同步更新**：
   * 更新 `<title>` 標籤，確保涵蓋所有現存主題名稱。
   * 更新 `<meta name="description">` 內容，納入新增主題的簡要描述。
   * 更新 `<meta name="keywords">`，補充新主題相關的中文關鍵字。
   * 同步更新 `og:title`、`og:description`、`twitter:title`、`twitter:description`。

2. **JSON-LD 結構化資料更新**：
   * 在 `<head>` 中的 `CollectionPage` JSON-LD 區塊，於 `hasPart` 陣列中新增對應的 `Article` 條目（含 name 和 url）。

3. **動態 SEO (`pageSEO`) 更新**：
   * 在 JavaScript 的 `pageSEO` 物件中，新增對應頁面的 `title` 和 `desc` 欄位。
   * 確保 title 格式為：`[頁面主題] — Ludwica 的簡單歷史課`。
   * 確保 desc 為 50-160 字的精確內容摘要。

4. **搜尋索引 (`initGlobalSearchIndex`) 註冊**：
   * 在 `initGlobalSearchIndex()` 函式中的 `pages` 陣列新增對應的 `{ id: 'pageXX', name: '頁面名稱' }` 條目。

5. **Sitemap 更新**：
   * 在 `build_html_md.py` 底部的 `sitemap_content` 中，新增對應頁面的 `<url>` 條目（使用 hash 路由格式 `#pageXX`）。

6. **`courseInfo` 元資料更新**：
   * 在 JavaScript 的 `courseInfo` 物件中，新增對應頁面的版本、生成來源與工程資訊。
