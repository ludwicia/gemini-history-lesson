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
   * **修改 `index_db.html`**（動態版 SPA 入口）：
     * 在 `pageSEO` 物件中新增該頁面的自訂標題與 50-160 字的精準 SEO 描述。
     * 在 `<head>` 的 JSON-LD 結構化資料 `hasPart` 陣列中新增對應的 `Article` 項目。

4. **更新日誌與版本宣告**：
   * 在 `index_db.html` 中，將 `版面設計` 版本號手動遞增（如 4.7 升級至 4.8），並更新發布日期。
   * 在專案根目錄的 `worklog.md` 頂部插入今日的發布日誌，詳細說明發布的文章、修正的史實、新增的插圖與路由調整。

5. **三軌編譯、Firestore 上傳與 Git 部署**：
   * 在本機依序執行以下三條編譯指令：
     ```bash
     python build_html_md.py           # 重新生成靜態備份 index_static.html 及 SEO 頁面
     python build_static_chunks.py     # 重新切片生成 api/ JSON Chunks
     python migrate_to_firestore.py    # 將所有資料上傳至 Firebase Firestore
     ```
   * 編譯及上傳無誤後，同步更新主入口：
     ```bash
     copy index_db.html index.html     # 將動態版同步至主入口
     ```
   * 最後執行 Git 命令部署上線：
     ```bash
     git add .
     git commit -m "發布：新增[專題名稱]專題 (版面 X.X, 內容 1.0)"
     git push
     ```
   * 部署完畢後向使用者報告網站已成功更新。

---

## 重要注意事項

* **主入口為 `index.html`**（由 `index_db.html` 複製而來的動態 Firestore 版本，約 68KB），它從 Firebase Firestore 按需載入文章。
* **靜態備份 `index_static.html`**（約 1.6MB，全部文章內嵌）僅作為 fallback 保留，不作為主要入口。
* **Firebase 配置**位於 `js/firebase-config.js`，Firestore 讀取服務位於 `js/firestore-service.js`。
* **Service Account 金鑰**（`ludwica-history-firebase-adminsdk-*.json`）已在 `.gitignore` 中排除，嚴禁提交至 Git。
* **圖片**仍然存放在本地 `images/` 目錄，由 Cloudflare Pages 靜態託管，不上傳至 Firebase Storage。
