# Antigravity 專案守則 🏛️

本文件記錄了本專案特有的排版、樣式設計與工程規範。所有在此專案進行開發與內容更新的 AI 夥伴，均必須嚴格遵守以下準則。

---

## 📊 嵌入式互動圖表 (Mermaid / SVG) 樣式與編譯規範

在文章中嵌入互動關係圖或 SVG 圖表時，必須嚴格遵守以下開發守則：

1. **解鎖容器寬度限制**：
   * 互動圖表的定位容器（如 `.diagram-container`）禁止設定為固定的百分比寬度（如 `width: 100%;`）。
   * 必須設定為 `width: auto;` 或 `width: max-content;`，以確保容器能根據 SVG 實際解析度進行自然擴展，避免在縮放時因寬度受限而導致右側內容被瀏覽器剪裁（Clipping）。

2. **防止全域滾動條干擾**：
   * 全域樣式表中的 `pre, code { overflow-x: auto; }` 會套用到圖表的 `<pre class="mermaid">` 標籤，導致縮放時出現微型滾動條。
   * 必須在圖表樣式中，為圖表容器內的 `pre` 和 `.mermaid` 元素強制覆寫樣式：

     ```css
     .diagram-container pre,
     .diagram-container .mermaid {
         overflow: visible !important;
         width: auto !important;
         max-width: none !important;
         background: transparent !important;
         margin: 0 !important;
         padding: 0 !important;
     }
     ```

3. **編譯同步義務（2026-07-21 重大變更：單一指令）**：

   每次調整文章 HTML 結構、CSS 樣式或新增嵌入圖表後，執行**單一指令**：

   ```bash
   python run_build.py
   ```

   它會在同一個行程內依序完成：建置 → `api/` JSON 切片 → Firestore 上傳（有金鑰時）
   → index.html 文章索引驗證 → `verify_project.py` 完整驗證。任一環節失敗即中止。

   * **🚫 嚴禁執行 `copy index_db.html index.html`**（舊守則的步驟，現已作廢且有害）。
     `build_html_md.py` 會先把 `index_db.html` 複製為 `index.html`，**再於其中注入
     「全站文章索引」的 47 個靜態文章連結**。那些連結是搜尋引擎發現文章的主要途徑
     ——首頁其餘內容全由 JavaScript 從 Firestore 載入，初始 HTML 原本可見文字
     僅約 390 字元、0 個 `<h1>`、0 個文章連結，Google Search Console 曾因此顯示
     「已建立索引 0 頁」。事後再複製一次會把索引整段覆蓋，**且不會有任何錯誤訊息**。
     若不慎執行了，重跑 `python run_build.py` 即可修復。

   * **🚫 亦勿再分別執行**那三條指令。`build_static_chunks.py` 第 4 行是
     `import build_html_md`，而 `build_html_md.py` 的輸出段雖已加上 `__main__` 保護，
     分開執行仍會多跑一次完整建置；`run_build.py` 已在單一行程內處理妥當。

   * `index_static.html` **已於 2026-07-19 刪除**（全專案無任何引用），勿再產出或引用。

---

## 🔥 Firebase Firestore 架構說明

本專案的線上版本使用 **Firebase Firestore** 作為資料來源，前端 SPA（`index.html`）從 Firestore 按需讀取文章內容。

* **Firebase 專案**：`ludwica-history`（Firestore 位置：`asia-east1`）
* **Firebase 配置**：`js/firebase-config.js`
* **Firestore 讀取服務**：`js/firestore-service.js`（含 fallback 到本地 `api/` JSON 的雙軌機制）
* **資料遷移腳本**：`migrate_to_firestore.py`（使用 `firebase-admin` Python SDK，需要 Service Account 金鑰）
* **Service Account 金鑰**：`ludwica-history-firebase-adminsdk-*.json`（已在 `.gitignore` 排除，嚴禁提交至 Git）

### Firestore Collections

| Collection | 說明 |
|---|---|
| `articles` | 文章輕量元資料（`id`, `title`, `seo_title`, `seo_desc`, `ver`, `img`, `category`, `is_doc` 等，首頁導覽用），共 47 篇。 |
| `article_contents` | 文章完整 HTML 內容（含 `content_html` 全文與元資料，內頁按需載入），共 47 篇。 |
| `categories` | 全部分類（含 `title`、`key`、`img`、`pages[]` 頁面列表、`order` 排序），共 13 個。 |
| `worklog` | 更新日誌 HTML（document ID: `current`） |
| `search_index` | 全站搜尋索引，按頁面分組（每頁一個 document，含 `blocks[]` 文字段落陣列） |
| `site_config` | 網站設定（document ID: `metadata`） |

### 前端入口

| 檔案 | 說明 |
|---|---|
| `index.html` | **主入口**（動態版，從 Firestore 按需載入文章）。由 build 從 `index_db.html` 複製後**再注入全站文章索引**而成，故**與 `index_db.html` 並不相同**（多出約 110 行靜態文章連結）。**只能由 `python run_build.py` 產生，嚴禁手動複製覆蓋。** |
| `index_db.html` | 動態版原始檔。要修改版面請改此檔，然後重新 build（不要手動複製到 index.html）。其中的 `STATIC_ARTICLE_INDEX_START/END` 標記是索引注入的錨點，**請勿刪除**。 |
| `pages/pageXX.html` | 含**完整正文**的靜態文章頁（非跳轉頁），由 build 自動產生，各自帶 canonical 與 Article JSON-LD。這是 Google 實際索引的對象。 |
| `index_static.html` | **已於 2026-07-19 刪除**（全專案無引用，僅造成混淆）。勿再產出。 |

---

## ✍️ 小說子專案 (Novel Subproject) 與歷史研究雙軌協作守則

本專案包含了一個文學改編子專案「《鐵劍與托加》歷史小說」，存放於 `novel_workspace/` 目錄下。所有協作 AI 在處理本專案時，必須嚴格遵守以下雙軌互動流程：

1. **研究回溯義務 (Research Fallback)**：
   * 當在 `novel_workspace/` 下撰寫或修改小說大綱、草稿（如 `chapter1_draft.md`、`《鐵劍與托加》：第一章.md`）時，AI **必須主動檢索** `course/` 目錄下的歷史研究論文（如 `course/阿德里安堡戰役.md`、`course/阿拉里克與哥德大遷徙...md`）或利用網路搜尋，確保小說中的歷史細節（如兵制、官制、地理環境、風俗）準確無誤。
   * 如果發現某段情節所需的歷史事實尚未被研究或記錄，應提醒作者或主動在 `course/` 中建立相關歷史研究。

2. **靈感雙向回饋機制 (Inspiration Loop)**：
   * 當在 `course/` 中編輯、校對或新增歷史研究文章時，AI 應敏銳挖掘具備戲劇張力、衝突點或感人情節的冷門歷史知識。
   * AI 應主動將這些發現作為小說創作靈感，記錄到 [character_timeline_bridge.md](file:///c:/Users/USER/gemini%E7%9A%84%E7%B0%A1%E5%96%AE%E6%AD%B7%E5%8F%B2%E8%AA%B2/novel_workspace/character_timeline_bridge.md) 的「靈感提取與文學化示例」或「未來的靈感待填補區」，並主動向作者提議如何融入對應的小說章節中。

3. **術語與人名一致性 (Terminology Alignment)**：
   * 小說中的人物姓名、事件譯名、專有名詞（如 Arianism 譯為「阿里烏派」或「亞利烏派」、Fritigern 譯為「弗里蒂根」、Athanaric 譯為「阿薩納里克」）必須與 `course/` 歷史學術論文及 `characters_database.html` 保持高度一致，以防混淆。
   * 寫作時應隨時參考 [character_timeline_bridge.md](file:///c:/Users/USER/gemini%E7%9A%84%E7%B0%A1%E5%96%AE%E6%AD%B7%E5%8F%B2%E8%AA%B2/novel_workspace/character_timeline_bridge.md) 的對照表。

---

## 🔗 引用著作之學術超連結規範

為了便於讀者與學生進行史料交叉查證，所有課程文章（`course/`）的引用著作列表（References）必須遵守以下規範：

1. **超連結之有效性與可點擊性**：
   * 嚴禁使用純文字（Plain Text）記錄學術文獻。所有新替換或修改的學術引用，必須使用 Markdown 超連結語法 `[文獻名稱與描述](URL)` 進行包裝。
   * 超連結的指向必須是真實、有效且對大眾可點擊訪問的網頁，例如該圖書的 Google Books 頁面、Internet Archive 的數位圖書館存檔、知名學術出版社官網（如 Cambridge Core、Oxford Academic）或公認可靠的古籍電子版（如 CCEL、Tertullian Project 等）。
   * 嚴禁包含失效連結、Placeholder 網址或虛構網址。
