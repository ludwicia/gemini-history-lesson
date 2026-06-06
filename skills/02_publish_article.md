# AI 專屬工作技能 (Skills SOP)

## 技能名稱：發布新文章上線 (修改 build_html_md.py)

### 觸發條件
當使用者要求將新匯入的 Markdown 文章「推送上線」或加入網站選單時。

### 執行流程
1. **精準修改網站生成腳本**
   必須在 `build_html_md.py` 中精準插入新文章（假設為新編號的 page）的設定。**嚴禁使用全域正則表達式取代（Global Regex Replace）**，必須精準定位並手動/精細修改以下 10 個核心區塊，以避免引發 JavaScript SyntaxError 導致全站癱瘓：
   - **Python 變數區**：定義 `file_pXX`、`images_pXX` 與 `html_body_pXX`。
   - **SEO JSON-LD**：在 `<script type="application/ld+json">` 的 `hasPart` 陣列中加入新文章網址。
   - **導覽列按鈕**：在 HTML 的 `<nav>` 區塊新增 `<a href="#pageXX">...</a>`。
   - **內文 HTML 容器**：新增 `<div id="course-pageXX" class="course-page" style="display: none;">__HTML_BODY_PAGEXX__</div>`。
   - **JavaScript 左側資訊 (courseInfo)**：在 JS 內精準新增 `pageXX: { ... }` 包含更新日期、版本等 HTML 字串。
   - **JavaScript 網頁 Meta (pageMeta)**：在 JS 內新增 `pageXX: { title: '...', desc: '...' }`。
   - **JavaScript 搜尋索引 (searchIndex)**：在陣列中推入 `{ id: 'pageXX', name: '...' }`。
   - **JavaScript 路由判定 (matchedPage)**：在判斷陣列中補上 `'pageXX'`。
   - **Python HTML 組裝區**：在腳本最尾端補上 `final_html.replace('__HTML_BODY_PAGEXX__', html_body_pXX)` 與 `__PAGEXX_DATE__` 的取代邏輯。
   - **Sitemap.xml 區塊**：在 `sitemap_content` 中加入新的 `<url>` 區塊。

2. **重新編譯與驗證**
   - 執行命令：`python build_html_md.py`。
   - 確保終端機沒有報錯，且順利產生乾淨無語法錯誤的 `index.html`。

3. **推送上線 (部署)**
   - 執行命令：`git add .`
   - 執行命令：`git commit -m "feat: add article [文章標題]"`
   - 執行命令：`git push`
   - 向使用者回報部署成功，請其至線上確認。
