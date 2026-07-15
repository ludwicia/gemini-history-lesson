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

3. **三軌編譯同步義務**：
   * 每次調整文章 HTML 結構、CSS 樣式或新增嵌入圖表後，**必須同時依序執行以下三條指令**：
     * `python build_html_md.py` (重新生成靜態備份 `index_static.html` 及 SEO 頁面)
     * `python build_static_chunks.py` (重新切片生成動態 API Chunks)
     * `python migrate_to_firestore.py` (將所有資料上傳至 Firebase Firestore 雲端資料庫)
   * 編譯完成後必須同步主入口：`copy index_db.html index.html`
   * 嚴禁只執行單一編譯，以防止靜態備份、API Chunks 與 Firestore 雲端資料庫三者之間內容不一致。

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
| `articles` | 33 篇文章（含 `content_html` 全文、`title`、`ver`、`img` 等元資料） |
| `categories` | 10 個分類（含 `title`、`key`、`pages[]` 頁面列表、`order` 排序） |
| `worklog` | 更新日誌 HTML（document ID: `current`） |
| `search_index` | 全站搜尋索引，按頁面分組（每頁一個 document，含 `blocks[]` 文字段落陣列） |
| `site_config` | 網站設定（document ID: `metadata`） |

### 前端入口

| 檔案 | 說明 |
|---|---|
| `index.html` | **主入口**（~68KB 動態版，從 Firestore 按需載入文章） |
| `index_db.html` | 動態版原始檔（與 index.html 內容相同，修改時應修改此檔再複製） |
| `index_static.html` | 靜態備份（~1.6MB，全部文章內嵌，僅作為 fallback） |

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
