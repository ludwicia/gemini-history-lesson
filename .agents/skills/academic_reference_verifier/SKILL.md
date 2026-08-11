---
name: academic_reference_verifier
description: Verifies, normalizes, and searches academic reference links (Google Books, Internet Archive, JSTOR, CCEL, Oxford/Cambridge Core) for history articles, ensuring zero plain-text references and 100% valid clickable URLs.
---

# 學術文獻引用與外鏈查核工作流

本技能規範在編寫、校對或擴充 `course/` 歷史專題文章時，如何確保文末「引用著作 / References」清單符合 [`AGENTS.md`](file:///c:/Users/USER/gemini%E7%9A%84%E7%B0%A1%E5%96%AE%E6%AD%B7%E5%8F%B2%E8%AA%B2/.agents/AGENTS.md) 所規定的學術嚴謹性與可查證性。

---

## 核心準則與規範

1. **嚴禁純文字引用**：
   * 所有學術引用項目**必須**以 Markdown 超連結格式封裝：`[文獻名稱、作者與描述](URL)`。
   * 不得留存如 `Peter Heather, The Fall of the Roman Empire, 2005` 這樣的無連結純文字項目。
2. **連結必須真實且對大眾可點擊**：
   * 優先採用對公眾可讀、可檢索或具備預覽的正規數位學術平台。
   * **嚴禁**虛構網址、Placeholder 網址（如 `https://example.com` 或 `TODO_URL`）或已失效的 404 連結。

---

## 優先引用來源策略

當尋找學術文獻的真實網址時，依下列優先權進行檢索與包裝：

| 來源類型 | 平台與網址特徵 | 適用對象 |
|---|---|---|
| **數位圖書館 / 公開存檔** | **Internet Archive** (`https://archive.org/details/...`) | 絕版歷史專著、近代學術經典、全書可借閱影本 |
| **圖書預覽與索引** | **Google Books** (`https://books.google.com/books?id=...` 或 `/books/about/...`) | 當代主流歷史學專著（如 Oxford, Cambridge, Routledge 出版品） |
| **古典初級史料數據庫** | **CCEL** (`ccel.org`), **Tertullian Project** (`tertullian.org`), **Perseus Digital Library** (`perseus.tufts.edu`), **LacusCurtius** | 古羅馬與拜占庭原始文獻（如 Ammianus Marcellinus, Procopius, Zosimus） |
| **頂級學術出版商** | **Cambridge Core** (`cambridge.org/core/...`), **Oxford Academic** (`academic.oup.com/...`), **Brill** | 權威劍橋古代史系列（CAH）與同行評審論文集 |

---

## 查核與轉換作業流程

### 步驟一：掃描文章引用區塊

1. 檢查 `course/*.md` 檔案結尾的 `## 參考文獻`、`## 引用著作` 或 `## References` 區塊。
2. 識別出所有尚未加上超連結的純文字書目。

### 步驟二：檢索真實學術連結

1. 對每一筆純文書目提取「作者姓名 + 書名 + 出版年份」進行 Web 搜尋。
2. 取得精確指向該書/該文獻的持久性 URL（避免使用暫時性的搜尋結果頁 Session 網址）。

### 步驟三：標準化 Markdown 超連結替換

範例轉換格式：

* **錯誤（純文字）**：
  `- Heather, Peter. The Fall of the Roman Empire: A New History of Rome and the Barbarians. Oxford University Press, 2005.`
* **正確（超連結封裝）**：
  `- [Heather, Peter. *The Fall of the Roman Empire: A New History of Rome and the Barbarians*. Oxford University Press, 2005.](https://books.google.com/books?id=01jR4lPZ2D0C)`

### 步驟四：發布前自動化檢驗

在執行 `python run_build.py` 之前：

1. 確保所有 `[` 與 `]`、`(` 與 `)` 均有正確閉合，無語法截斷。
2. 確保沒有殘留的死鏈或測試字元。
