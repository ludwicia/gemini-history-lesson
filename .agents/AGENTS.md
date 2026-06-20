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

3. **雙軌編譯同步義務**：
   * 每次調整文章 HTML 結構、CSS 樣式或新增嵌入圖表後，**必須同時執行以下兩條指令**：
     * `python build_html_md.py` (重新生成靜態入口 `index.html`)
     * `python build_static_chunks.py` (重新切片生成動態 API Chunks)
   * 嚴禁只執行單一編譯，以防止入口網站與 SPA 動態頁面顯示不一致。
