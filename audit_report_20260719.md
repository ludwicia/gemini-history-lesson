# 專案體檢報告：網站外觀與資料結構

日期：2026-07-19｜範圍：`build_html_md.py`、`template.html` / `index*.html`、`style.css`、`api/`、`js/`、`course_config.json`、`images/`

---

## 一、嚴重問題（建議優先處理）

### 1. 建置管線與實際部署頁面「斷開」— 最關鍵

| 檔案 | 角色 | 現況 |
|---|---|---|
| `template.html` | 建置模板（71 KB） | 無 inline `<style>` |
| `index_static.html` | `build_html_md.py` 的輸出（2.0 MB） | **全專案無任何地方引用它** |
| `index_db.html` | 實際的資料庫版首頁（83 KB） | 含 5,330 字元 inline `<style>`，**不是由 template 生成的** |
| `index.html` | 部署頁 | 與 `index_db.html` **逐位元組完全相同**（diff = 0 行） |

`build_html_md.py` 的流程是：讀 `template.html` → 寫出 `index_static.html` → 再把 `index_db.html` 複製成 `index.html`。

也就是說：**跑完 build 產出的 `index_static.html` 沒有人會看到，而真正上線的 `index.html` 來自手工維護的 `index_db.html`**。`index_db.html` 已與 `template.html` 分岔（多出一段 inline CSS、`style.css?v=4.8` vs `?v=4.7`）。

風險：改 `template.html` 不會影響線上外觀；改 `index_db.html` 又會在下次 build 時與模板差距愈拉愈大。CLAUDE.md 寫的「修改後跑 build 驗證 index.html」目前實際上驗證不到版面。

**建議**：擇一為單一真實來源。
- 方案 A（推薦，維持現有 DB 架構）：把 `index_db.html` 正名為模板，`index_static.html` 退場，build 只負責產 `api/*.json` 與 `pages/*.html`。
- 方案 B：把 `index_db.html` 多出的 inline CSS 併回 `template.html` / `style.css`，讓 build 真正生成部署頁。

> **【2026-07-19 更新｜已部分處理】**
> `index_static.html` 已刪除，產出它的程式碼已移除，並加入 `.gitignore`。
>
> **更正**：原本建議「`template.html` 一併退場」是錯的。第 1272 行的 `generate_redirect_pages()`
> 會從 `template.html` 撈 `pageSEO` 描述去填 44 個 `pages/*.html` 的 meta description，
> 刪掉會造成 SEO 退化。該依賴已改為讀 `course_config.json`（見下方第 2 點），
> 但 `template.html` 仍是 `final_html` 組裝流程的模板，**尚不可刪**，
> 待模板單一化重構完成後才能退場。

### 2. `course_config.json`（73 KB）是孤兒 — 兩套並存的設定來源

`course_config.json` 內已完整記錄 44 篇文章的 `file_path` / `ver` / `img` / `seo_title` / `seo_desc` / `map_html`，結構乾淨、與 `pages/`、`api/article/` 完全對得上（無缺漏、無多餘）。

但全專案只有 `verify_project.py` 和 `worklog.md` 讀它——**`build_html_md.py` 完全沒有引用**。

`build_html_md.py` 共 1,332 行，其中約 300 行是 `file_p1`…`file_p45` / `map_pN` / `images_pN` 的硬編碼區塊，再加約 90 行一模一樣的 `print("Processing Page N...")` + `process_markdown(...)` 呼叫。這些資訊與 `course_config.json` 重複。

**建議**：讓 `build_html_md.py` 改為迴圈讀取 `course_config.json`，硬編碼區塊整段刪除。預估腳本可從 1,332 行縮到 300 行以內，且新增文章從「改 6 處程式碼」變成「加一筆 JSON」。這也順帶解決 CLAUDE.md 裡 SEO 守則要求的 6 步同步（可自動化為 1 步）。

> 註：`process_markdown` / `process_3col_document` 兩個核心函式邏輯本身沒問題，保留即可。
>
> **重要前提（後續重構務必注意）**：`build_static_chunks.py` 開頭 `import build_html_md`，
> 是靠 import 的副作用取得模組層變數 `pages_data`、`html_body_pN`、`file_pN`（用 `getattr`
> 動態組名），再生成 `api/articles.json`、`api/article/*.json` 與 `api/search_index.json`。
> 因此那些硬編碼變數目前是**活的**，重構時必須同步改寫 `build_static_chunks.py`，
> 不能只動 `build_html_md.py`。

> **【2026-07-19 更新｜已完成 SEO 描述單一化】**
> `generate_redirect_pages()` 已改讀 `course_config.json` 的 `seo_desc`，
> 並加上缺漏警示（日後新增文章若忘了寫 `seo_desc`，build 會印出 WARNING 而非無聲退回通用文案）。
> `course_config.json` 已合併三方描述成完整 44 筆，詳見下方第 7 點。

### 3. 圖片未經最佳化 — 最直接的使用者體驗傷害

`images/` 目錄共 **181 MB / 123 個檔案**，其中 36 個超過 1 MB：

| 檔案 | 大小 |
|---|---|
| `img_00_Map_of_Seventeen_Provinces_of_Low_German.jpg` | **21 MB** |
| `creed_baptism.jpg` | 14 MB |
| `clergy_luther_bora.jpg` | 13 MB |
| `p17_tetrarchs.jpg` | 12 MB |
| `us2_penn_treaty.jpg` | 8.1 MB |

全站 **0 處使用 `srcset`，0 個 `.webp`**。雖然 `loading="lazy"` 有正確套用，但使用者只要捲到該段落就會下載 21 MB 的原圖。手機使用者幾乎不可能等到。

**建議**：批次轉出長邊 1600px 的 WebP（品質 82），原圖移出 repo 另存。預估 181 MB → 15 MB 以內，Lighthouse LCP 會有數量級改善。這是投報率最高的一項。

---

## 二、中度問題

### 4. Firestore 讀取模式成本偏高

`js/firestore-service.js` 的 `getArticlesCatalog()` 用 `getDocs(collection(db,'articles'))`——**每位訪客首頁載入就是 44 次 document read**。`getSearchIndex()` 同理，再讀 44 份、約 1.6 MB。

Firestore 免費額度 50,000 reads/日，換算約 1,100 位訪客/日就會觸頂；而這些內容其實是完全靜態的。

現行程式是「Firestore 優先、本地 `/api/*.json` 為 fallback」。對一個部署在 Cloudflare Pages 的靜態站來說，這個優先順序是反的——CDN 送靜態 JSON 又快又免費。

**建議**：
- 把優先順序反轉為「本地 JSON 優先、Firestore 作為即時更新的補充」，或
- 在 Firestore 端改存單一彙總 document（`articles/_catalog`），把 44 reads 降為 1 read。

快取層（LRU + `_pending` 去重）寫得很紮實，這部分沒問題。

### 9.〔已修復〕**整站無法被搜尋引擎索引** — 實際上是最嚴重的問題

Google Search Console 顯示：已建立索引 **0** 頁、未建立索引 **1** 頁（原因為「已檢索 — 目前尚未建立索引」）；3 個月內 284 次曝光、0 次點擊，且 6/18 之後曝光歸零。

實測診斷（`index.html` 移除 `<script>`／`<style>` 後）：

| 項目 | 修復前 | 修復後 |
|---|---|---|
| 首頁初始 HTML 可見文字 | **390 字元** | 1,065 字元 |
| 首頁 `<h1>` 數量 | **0** | 0（維持 SPA 設計） |
| 首頁指向文章的連結 | **0** | **44** |
| `pages/*.html` 正文 | 無（純 JS 跳轉空殼，約 2 KB） | 完整正文，平均 16,373 字 |

兩個致命成因：

1. **首頁是空殼**。44 篇文章的標題與正文完全由 `firestore-service.js` 在瀏覽器端載入後才注入 DOM，初始 HTML 只有 390 字導覽文字、0 個 `<h1>`、0 個文章連結。Googlebot 抓回去看到的是一個沒有內容也沒有出口的頁面。
2. **44 篇文章塌縮成 1 個網址**。`pages/*.html` 全是 `window.location.replace("../#pageXX")`，Google 視為跳轉到首頁；而 `#pageXX` 是錨點，不構成獨立網址。加上 `pages/*.html` 完全沒有 canonical，首頁 canonical 又指向網站根目錄。

這完全解釋了「Google 只認識 1 個網址、且判定沒有索引價值」。

修復內容：

- `generate_redirect_pages()` 重寫為 `generate_static_article_pages()`：直接寫入建置過程早已存在於記憶體的 `html_body_pXX` 完整文章 HTML，移除 JS 跳轉，補上各自的 `canonical`、`Article` JSON-LD、`viewport`、上一篇／下一篇導覽，並將 `images/` 相對路徑修正為 `../images/`
- `index_db.html` 底部新增「全站文章索引」footer，建置時由 `build_html_md.py` 依 `categories` 與文獻頁注入 44 個靜態連結（含缺漏警示）
- 新增 `.site-article-index` 響應式樣式（三欄／兩欄／單欄）
- 版面設計版本 7.7 → **7.8**，`style.css?v=4.8` → `4.9`

驗證結果：44 頁全數通過（無殘留 JS 跳轉、canonical 各自唯一、JSON-LD 完整、圖片路徑正確、標籤閉合無誤），首頁 HTML 解析無未閉合標籤，SPA 行為與外觀未受影響。

> **後續仍須你手動處理**：到 GSC 提交 `sitemap.xml`，並用「網址審查」對首頁與幾篇文章要求重新檢索。索引通常需要數天至數週。
>
> 附帶觀察（未改動）：`page06`、`page08`、`page20`、`page42`、`page43` 各有 2 個 `<h1>`，源自三欄文獻頁的「原文＋說明」與小說頁的「中文＋英文」雙標題結構。HTML5 允許，Google 也能處理，屬既有內容結構，未擅自更動。

### 5. `pages/*.html` 是純跳轉頁，SEO 效果打折

44 個 `pages/pageXX.html` 只有 `<title>`、`<meta description>` 和一段 `window.location.replace("../#pageXX")`，body 只有標題與一行說明，**沒有任何正文**。

sitemap.xml 送出的 49 個 URL 中有 44 個指向這些頁面。搜尋引擎爬到的是「即時 JS 跳轉 + 無實質內容」，這在 Google 的判準裡接近 doorway page，可能被降權或不索引。

**建議**：既然 `build_html_md.py` 早就能產出完整文章 HTML（`index_static.html` 裡就有），把該內容直接寫進 `pages/pageXX.html` 的 `<body>`，並拿掉 JS 跳轉（或改為讓使用者自行點擊）。這樣既保留單頁應用體驗，又讓每篇文章有真正可索引的靜態頁。

> **【2026-07-19 更新｜已修復，且嚴重性遠高於原本評估】**
> 經 Search Console 數據佐證，這不是「SEO 打折」，而是整站無法被索引的直接主因之一。
> 完整診斷與修復內容見第 9 點。

### 7.〔已修復〕線上 meta description 殘缺與錯字

`generate_redirect_pages()` 原本只讀 `template.html`，而該檔的 `pageSEO` 與 `index_db.html` 的已分岔（41 筆 vs 39 筆），造成：

- `page42`、`page43`（鐵劍與托加）、`page45` 線上僅有通用備援文案「Ludwica 的簡單歷史課：歷史專題研究與報告。」
- `page05`、`page13`、`page15`、`page21`、`page43`、`page44` 三方描述內容互有出入，且各自帶有錯字

處理方式：以 `course_config.json` 的 `seo_desc` 為單一真實來源，逐頁人工比對三方版本後合併（取用字正確、內容完整者）：

| 頁面 | 處理 |
|---|---|
| page28 / 29 / 31 / 32 | `course_config` 原為通用備援文案 → 採用 `template.html` 的完整描述（25 字 → 66～156 字） |
| page13 | 修正錯字：啟**盟**運動 → 啟**蒙**運動 |
| page15 | 修正錯字：財產繼**展** → 財產繼**承** |
| page21 | 修正錯字：新約**儲**形 → 新約**雛**形 |
| page05 | 修正異體字：美學巅峰 → 美學**巔**峰 |
| page43 | 修正括號破損：《鐵劍與托加**}** → 《鐵劍與托加**》** |
| page44 | 採用較完整的版本（68 字 → 90 字，補回阿奇利塞內和約與高加索防線內容） |

重建後驗證：44 頁**全數有專屬描述，零通用備援文案**，平均 79 字。

仍偏短者（低於 CLAUDE.md 建議的 50 字下限，內容本身正確，未擅自改寫）：`page06`(43)、`page07`(48)、`page08`(37)、`page15`(33)。

### 8.〔已修復〕建置速度：git 日期查詢重複執行

`get_file_last_update_date()` 每次呼叫會發出 3 個 git 子行程（`log` / `diff` / `diff --cached`），實測合計約 0.7 秒；而同一個 `.md` 在單次建置中會被查詢**兩次**（`process_markdown` 內一次、產生版權卡片日期時再一次），44 篇即浪費約 30 秒。

已加上 `@lru_cache`（單次建置期間檔案日期不會變動，可安全快取）。**建置時間從 60 秒以上降到 23 秒。**

### 6. Git repo 體積 253 MB

主因是 181 MB 的高解析度圖片全數納管版控，且歷次替換版本都留在歷史中。圖片最佳化（第 3 點）只能減少「未來」的膨脹，歷史紀錄需 `git filter-repo` 才能瘦身（屬破壞性操作，需另行評估）。

好消息：`.gitignore` 已正確排除 `*-firebase-adminsdk-*.json`，且 `git log --all` 確認**該金鑰從未被提交過**，這點沒有問題。

---

## 三、輕度／清理項目（需您確認後才動）

以下檔案經全專案引用掃描，**目前無任何程式或頁面引用**。依 CLAUDE.md 第 5 條，我先列出並說明來源，等您確認後再處理：

| 檔案 | 大小 | 判斷 |
|---|---|---|
| `index_static.html` | 2.0 MB | build 產物，無人引用（見第 1 點；架構定案後可刪或改為部署目標） |
| `temp_gdoc.html` | 98 KB | `import_gdoc.py` 的中間暫存檔，看來是忘了清 |
| `test_import.md` | 26 KB | 匯入測試殘留 |
| `Universal Images Group via Getty Images.jpg` | 1.1 MB | 根目錄圖，未被引用；檔名顯示為 Getty 版權圖，另有授權疑慮 |
| `licensed-image.jpg` | 694 KB | 根目錄圖，未被引用 |
| `romamap.jpg` | 57 KB | 根目錄圖，未被引用 |
| `4.德意志帝國檔案譯文解析(一).md` | 1 KB | 疑似 `德意志帝國檔案譯文解析(一).md`（27 KB）的殘缺副本 |
| `images/hirsau_eulenturm.jpg` 等 3 檔 | 0.2 MB | 希爾紹修道院圖，曾用後被換掉 |
| `novel_workspace/*_raw.png` × 2 | 1.7 MB | 與非 `_raw` 版 md5 完全相同，純重複 |
| `fact_check_report.md` | 529 KB | 查核產出報告，內容有價值但體積大，建議確認是否要納入版控 |

另：`scratch/` 已在 `.gitignore` 中，但目錄仍留在本機（2 MB），屬正常工作痕跡。

---

## 四、確認沒問題的部分

- `course_config.json` ↔ `pages/` ↔ `api/article/` ↔ `sitemap.xml` 的 44 篇文章 **完全一致，零缺漏零多餘**（`page35` 為刻意跳號）
- Firebase 服務帳戶金鑰從未進入 git 歷史
- HTML 無重複 `id`，JS 無重複函式定義、無明顯未定義呼叫
- `style.css`（145 個選擇器）與 index inline CSS 的選擇器僅 1 處重疊（且屬 media query 情境），CSS 汙染程度低
- 圖片引用完整性高：123 張中 120 張有被引用
- `loading="lazy"` 已依 CLAUDE.md 規範正確套用，無外部圖庫熱連結

---

## 五、進度與後續順序

已完成：

- ✅ 刪除 `index_static.html` 與其產出程式碼
- ✅ SEO 描述統一至 `course_config.json`（44 筆完整，修正 5 處錯字）
- ✅ 建置速度 60 秒以上 → 23 秒（`lru_cache`）
- ✅ **44 篇文章靜態化 + 首頁靜態索引**（解除整站無法索引的問題）

待辦（依建議順序）：

1. **到 GSC 提交 `sitemap.xml` 並要求重新檢索** — 上述修復要生效，這一步是必要的
2. **圖片最佳化（WebP + 尺寸壓縮）** — 181 MB、單張最大 21 MB，使用者感受最直接
3. **確立 `index_db.html` / `template.html` 的單一真實來源** — 後續所有改動的地基
4. **`build_html_md.py` 改讀 `course_config.json`** — 砍掉約 1,000 行重複程式碼（注意需同步改 `build_static_chunks.py`）
5. **Firestore 讀取降為 1 read / 或改本地優先** — 成本與速度
6. 清理第三節的無引用檔案（待您逐項確認）
