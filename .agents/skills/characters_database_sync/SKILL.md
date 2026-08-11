---
name: characters_database_sync
description: Manages and synchronizes the European historical characters database (characters_database.html, update_characters_database.py, character_relationship.html) and novel character bridges.
---

# 歷史人物資料庫管理與同步工作流

本技能規範如何對「歐洲歷史人物資料庫」（[`characters_database.html`](file:///c:/Users/USER/gemini%E7%9A%84%E7%B0%A1%E5%96%AE%E6%AD%B7%E5%8F%B2%E8%AA%B2/characters_database.html)）、人物關係圖（[`character_relationship.html`](file:///c:/Users/USER/gemini%E7%9A%84%E7%B0%A1%E5%96%AE%E6%AD%B7%E5%8F%B2%E8%AA%B2/character_relationship.html)）以及小說對照表（[`character_timeline_bridge.md`](file:///c:/Users/USER/gemini%E7%9A%84%E7%B0%A1%E5%96%AE%E6%AD%B7%E5%8F%B2%E8%AA%B2/novel_workspace/character_timeline_bridge.md)）進行安全、一致且標準化的增修與維護。

---

## 核心觸發情境

1. **新文章引入新人物**：當在 `course/` 中發布或校對新文章時，發現具有重要歷史定位的君王、將領、主教、哲學家或蠻族領袖尚未收錄於人物庫。
2. **人物資料修訂**：修正生卒年、陣營、歷史事件、頭銜或世系親族關係。
3. **小說角色對照同步**：當小說《鐵劍與托加》引入真實歷史人物時，確保人物代碼、陣營與背景一致。

---

## 標準維護工作流程

### 步驟一：人物資料標準化結構提取

在新增或更新人物前，必須按照以下標準 JSON 欄位提取並整理資料：

```json
{
  "id": "person_unique_id",
  "name_zh": "中文規範譯名（如：瓦倫提尼安一世）",
  "name_en": "Latin / English Name (e.g., Valentinian I)",
  "title": "官方頭銜 / 稱號（如：羅馬帝國西部皇帝）",
  "years": "生卒年（如：321 – 375）",
  "faction": "陣營分類代碼（如：roman_empire, gothic_tribes, church_fathers, sassanid 等）",
  "dynasty_or_group": "所屬王朝或部族（如：瓦倫提尼安王朝 / 德勒溫吉哥德人）",
  "bio": "100-250 字的生平精要與歷史評價（繁體中文，保持學術客觀）",
  "related_articles": ["pageXX", "pageYY"],
  "relations": [
    { "target_id": "valens", "relation_type": "brother", "label": "弟弟" },
    { "target_id": "gratian", "relation_type": "child", "label": "長子" }
  ]
}
```

### 步驟二：譯名與年代跨模組核對

1. **譯名統一性**：
   * 繁體中文譯名必須與 `course/` 文章、`characters_database.html`、`character_timeline_bridge.md` 保持完全一致（例如：`Stilicho` 統一為「斯提里科」，`Fritigern` 統一為「弗里蒂根」）。
2. **年代相容性**：
   * 檢查生卒年與重大事件年份（如即位、戰役）是否符合公認史學共識，避免出現時空倒錯。

### 步驟三：更新資料庫與生成腳本

1. **維護 `update_characters_database.py`**：
   * 檢查資料提取腳本中的人物列表與解析邏輯，確保新增人物具備完整屬性。
2. **維護 `characters_database.html`**：
   * 人物卡片必須包含：頭像/圖示占位、中英文雙名、生卒年標籤、陣營標籤、生平簡述、相關歷史課頁面跳轉連結。
3. **維護 `character_relationship.html` 關係圖拓撲**：
   * 若有增刪人物，必須同時檢查關係圖中的節點（Node）與邊（Edge）。
   * 嚴禁留下指向不存在 `target_id` 的無效邊（懸空指標）。

### 步驟四：驗證與本地測試

1. 在終端執行相關更新腳本（若有）：

   ```powershell
   python update_characters_database.py
   ```

2. 檢查 `characters_database.html` 檔案語法完整性，確保前端搜尋篩選（按陣營、按世紀、按關鍵字）與關聯彈窗能正常運作。
3. 確保改動不會破壞純 Vanilla JS/CSS 的極簡規範。
