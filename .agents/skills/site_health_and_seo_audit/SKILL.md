---
name: site_health_and_seo_audit
description: Comprehensive health, performance, image compression, Firestore sync, and SEO audit workflow for the history course web application.
---

# 全站健康度、性能與 SEO 巡檢工作流

本技能定義「Gemini 的簡單歷史課」專案在進行任何大型發布、版面改動或例行維護時的全面巡檢工作流，確保搜尋引擎索引（SEO）、Firebase Firestore 資料庫、圖片資源載入效能以及各靜態切片的一致性與穩定度。

---

## 核心巡檢維度

```mermaid
graph TD
    Audit[全站巡檢 Audit] --> SEO[1. SEO 與結構化資料 (SSOT)]
    Audit --> IMG[2. 圖片規格與載入優化]
    Audit --> FS[3. Firestore 與 API 切片同動]
    Audit --> Build[4. 單一管線編譯驗證]

    SEO -->|course_config.json| SEO_Desc[檢查 50-160 字 desc & Article JSON-LD]
    IMG -->|Pillow 規範| IMG_Spec[長邊<=1600px, Q82, <500KB]
    FS -->|Firestore / api/| FS_Sync[文章、分類、索引一致性]
    Build -->|run_build.py| Build_Pass[verify_project.py 全數 PASS]
```

---

## 標準巡檢作業清單

### 1. SEO 單一真實來源 (SSOT) 查核

* **唯一配置檔**：[`course_config.json`](file:///c:/Users/USER/gemini%E7%9A%84%E7%B0%A1%E5%96%AE%E6%AD%B7%E5%8F%B2%E8%AA%B2/course_config.json)
* **查核要點**：
  * 每篇文章均有定義 `seo_title`（格式：`[頁面主題] — Ludwica 的簡單歷史課`）。
  * 每篇文章均有定義 `seo_desc`（長度維持在 **50–160 字元** 之精確內容摘要）。
  * 靜態頁面 `pages/pageXX.html` 必須由 build 自動生成 canonical、og/twitter 標籤與 Article JSON-LD，**嚴禁手動散落維護**。

### 2. 本地圖片規格與效能檢查

* **路徑**：[`images/`](file:///c:/Users/USER/gemini%E7%9A%84%E7%B0%A1%E5%96%AE%E6%AD%B7%E5%8F%B2%E8%AA%B2/images/)
* **入庫前壓縮標準**（遵守 `CLAUDE.md` / `skills/03_add_images.md`）：
  * 長邊尺寸：最大 **1600px** 以內。
  * 壓縮格式：照片類使用 JPEG 品質 82（含 `optimize=True`, `progressive=True`）。
  * 檔案大小警戒線：單檔必須小於 **500 KB**。
  * HTML 標籤載入：必須包含 `loading="lazy"` 與適當的 `alt` 說明。

### 3. 編譯與發布管線安全（防呆義務）

* **唯一編譯指令**：

  ```powershell
  python run_build.py
  ```

* **三大禁忌與防呆**：
  * 🚫 **嚴禁執行 `copy index_db.html index.html`**：
    `build_html_md.py` 會在複製後注入「全站文章索引」的 47+ 個靜態文章連結供搜尋引擎爬取；手動覆蓋會導致首頁索引歸零！
  * 🚫 **勿分別呼叫多個建置腳本**：`run_build.py` 已整合單行程循序處理。
  * 🚫 **嚴禁將 Service Account 金鑰提交至 Git**。

### 4. 自動化驗證確認

在完成 `run_build.py` 後，檢視控制台輸出，確保 [`verify_project.py`](file:///c:/Users/USER/gemini%E7%9A%84%E7%B0%A1%E5%96%AE%E6%AD%B7%E5%8F%B2%E8%AA%B2/verify_project.py) 的四項檢驗均顯示 `[OK]`：

1. `[OK]` 靜態文章頁面與 Canonical 正確。
2. `[OK]` JSON-LD 結構化資料完整。
3. `[OK]` `index.html` 包含完整的靜態文章索引連結。
4. `[OK]` `api/` 切片與 Firestore 集合相符。
