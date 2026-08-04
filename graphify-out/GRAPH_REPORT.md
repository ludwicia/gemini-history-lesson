# Graph Report - .  (2026-07-31)

## Corpus Check
- Large corpus: 497 files · ~3,006,985 words. Semantic extraction will be expensive (many Claude tokens). Consider running on a subfolder.

## Summary
- 113 nodes · 131 edges · 14 communities (12 shown, 2 thin omitted)
- Extraction: 100% EXTRACTED · 0% INFERRED · 0% AMBIGUOUS
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- Core Compilation Pipeline
- Firestore Service Layer
- Character Database & Utilities
- Module Group 3
- Module Group 4
- Module Group 5
- Module Group 6
- Module Group 7
- Module Group 8
- Module Group 10
- Module Group 13

## God Nodes (most connected - your core abstractions)
1. `main()` - 9 edges
2. `main()` - 7 edges
3. `main()` - 5 edges
4. `AdminRequestHandler` - 4 edges
5. `process_markdown()` - 4 edges
6. `process_3col_document()` - 4 edges
7. `init_firestore()` - 4 edges
8. `scripts` - 4 edges
9. `make_urls_clickable()` - 3 edges
10. `get_file_last_update_date()` - 3 edges

## Surprising Connections (you probably didn't know these)
- None detected - all connections are within the same source files.

## Import Cycles
- None detected.

## Communities (14 total, 2 thin omitted)

### Community 0 - "Core Compilation Pipeline"
Cohesion: 0.17
Nodes (16): find_service_account_key(), init_firestore(), main(), migrate_articles(), migrate_categories(), migrate_search_index(), migrate_site_config(), migrate_worklog() (+8 more)

### Community 1 - "Firestore Service Layer"
Cohesion: 0.17
Nodes (5): firebaseConfig, _articleAccessOrder, cache, _cacheArticle(), getArticleById()

### Community 2 - "Character Database & Utilities"
Cohesion: 0.15
Nodes (12): @lhci/cli, markdownlint-cli2, description, devDependencies, @lhci/cli, markdownlint-cli2, name, scripts (+4 more)

### Community 3 - "Module Group 3"
Cohesion: 0.17
Nodes (12): api/articles.json, build_html_md.py, build_static_chunks.py, course_config.json, index.html, index_db.html, js/firebase-config.js, js/firestore-service.js (+4 more)

### Community 4 - "Module Group 4"
Cohesion: 0.29
Nodes (9): get_doc_tab(), get_file_last_update_date(), get_share_bar_html(), make_card_html(), make_urls_clickable(), process_3col_document(), process_markdown(), clean_html_tags() (+1 more)

### Community 5 - "Module Group 5"
Cohesion: 0.33
Nodes (10): clean_filename(), clean_google_redirects(), ensure_markdownify(), extract_doc_id(), fetch_gdoc_html(), format_citations(), format_reference_links(), main() (+2 more)

### Community 6 - "Module Group 6"
Cohesion: 0.39
Nodes (7): check_files_exist(), check_images_exist(), check_index_sync(), check_static_article_pages(), main(), [2026-07-19 更新] index.html 不再與 index_db.html 完全相同。 build_html_md.py 會先把…, [2026-07-19 新增] 確認 pages/ 底下是真正含正文的靜態文章頁。 這些頁面原為 window.location.replace…

### Community 7 - "Module Group 7"
Cohesion: 0.33
Nodes (3): AdminRequestHandler, main(), stop_main_server()

### Community 8 - "Module Group 8"
Cohesion: 0.83
Nodes (3): find_service_account_key(), main(), run_script()

## Knowledge Gaps
- **12 isolated node(s):** `firebaseConfig`, `cache`, `_articleAccessOrder`, `HISTORICAL_PLACES`, `name` (+7 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **2 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What connects `firebaseConfig`, `cache`, `_articleAccessOrder` to the rest of the system?**
  _12 weakly-connected nodes found - possible documentation gaps or missing edges._