"""
Firestore 資料遷移腳本
Ludwica 的簡單歷史課 — 將本地 JSON API 資料上傳到 Firebase Firestore

使用方式:
    python migrate_to_firestore.py

前置條件:
    1. pip install firebase-admin
    2. 將 Firebase Service Account 金鑰 JSON 檔案放在專案目錄中
       （檔名格式類似 ludwica-history-xxxxxxxx.json）
"""

import os
import sys
import json
import glob

# 嘗試匯入 firebase-admin
try:
    import firebase_admin
    from firebase_admin import credentials, firestore
except ImportError:
    print("[ERROR] 請先安裝 firebase-admin:")
    print("   pip install firebase-admin")
    sys.exit(1)


def find_service_account_key():
    """自動尋找專案目錄中的 Service Account 金鑰 JSON 檔案"""
    patterns = [
        "ludwica-history-*.json",
        "serviceAccountKey.json",
        "service-account*.json",
        "*-firebase-adminsdk-*.json"
    ]
    for pattern in patterns:
        matches = glob.glob(pattern)
        if matches:
            return matches[0]
    return None


def init_firestore():
    """初始化 Firebase Admin SDK 和 Firestore"""
    key_path = find_service_account_key()
    if not key_path:
        print("[ERROR] 找不到 Service Account 金鑰 JSON 檔案！")
        print("   請將從 Firebase Console 下載的金鑰放在專案目錄中。")
        print("   檔名通常類似: ludwica-history-xxxxxxxx.json")
        sys.exit(1)

    print(f"Using key: {key_path}")
    cred = credentials.Certificate(key_path)
    firebase_admin.initialize_app(cred)
    return firestore.client()


def migrate_categories(db, catalog_data):
    """上傳分類到 Firestore categories collection"""
    print("\n[INFO] 正在上傳分類...")
    categories = catalog_data.get('categories', [])

    for idx, cat in enumerate(categories):
        doc_id = cat['key']
        doc_data = {
            'title': cat['title'],
            'key': cat['key'],
            'img': cat.get('img', ''),
            'pages': cat.get('pages', []),
            'order': idx  # 用 index 作為排序依據
        }
        db.collection('categories').document(doc_id).set(doc_data)
        print(f"   [OK] {cat['title']} ({doc_id}) — {len(cat.get('pages', []))} 篇文章")

    print(f"   [INFO] 共上傳 {len(categories)} 個分類")


def migrate_articles(db, catalog_data):
    """上傳文章元資料 + 全文到 Firestore articles collection"""
    print("\n[INFO] 正在上傳文章...")
    articles = catalog_data.get('articles', [])
    success_count = 0
    error_count = 0

    for art in articles:
        page_id = art['id']
        article_json_path = f"api/article/{page_id}.json"

        # 基本元資料
        doc_data = {
            'id': page_id,
            'title': art['title'],
            'ver': art.get('ver', '1.0'),
            'last_updated': art.get('last_updated', ''),
            'category': art.get('category', ''),
            'img': art.get('img', ''),
            'is_doc': art.get('is_doc', 0)
        }

        # 讀取文章全文 HTML
        if os.path.exists(article_json_path):
            try:
                with open(article_json_path, 'r', encoding='utf-8') as f:
                    article_detail = json.load(f)
                doc_data['content_html'] = article_detail.get('content_html', '')
            except Exception as e:
                print(f"   [WARNING] 讀取 {article_json_path} 失敗: {e}")
                doc_data['content_html'] = ''
        else:
            print(f"   [WARNING] 找不到 {article_json_path}")
            doc_data['content_html'] = ''

        # 上傳到 Firestore
        try:
            content_size = len(doc_data.get('content_html', ''))
            db.collection('articles').document(page_id).set(doc_data)
            print(f"   [OK] [{page_id}] {art['title']} ({content_size/1024:.1f} KB)")
            success_count += 1
        except Exception as e:
            print(f"   [ERROR] [{page_id}] 上傳失敗: {e}")
            error_count += 1

    print(f"   [INFO] 成功: {success_count}, 失敗: {error_count}")


def migrate_worklog(db, catalog_data):
    """上傳更新日誌到 Firestore worklog collection"""
    print("\n[INFO] 正在上傳更新日誌...")
    worklog_html = catalog_data.get('worklog', '')

    if worklog_html:
        db.collection('worklog').document('current').set({
            'html': worklog_html
        })
        print(f"   [OK] 更新日誌已上傳 ({len(worklog_html)/1024:.1f} KB)")
    else:
        print("   [WARNING] 沒有找到更新日誌")


def migrate_search_index(db):
    """上傳搜尋索引到 Firestore search_index collection"""
    print("\n[INFO] 正在上傳搜尋索引...")

    search_index_path = "api/search_index.json"
    if not os.path.exists(search_index_path):
        print(f"   [WARNING] 找不到 {search_index_path}")
        return

    with open(search_index_path, 'r', encoding='utf-8') as f:
        search_entries = json.load(f)

    # 按 pageId 分組（每個 page 一個 document，避免太多小 documents）
    grouped = {}
    for entry in search_entries:
        pid = entry['pageId']
        if pid not in grouped:
            grouped[pid] = []
        grouped[pid].append(entry['text'])

    for page_id, blocks in grouped.items():
        try:
            db.collection('search_index').document(page_id).set({
                'pageId': page_id,
                'blocks': blocks
            })
            print(f"   [OK] [{page_id}] {len(blocks)} 個搜尋段落")
        except Exception as e:
            print(f"   [ERROR] [{page_id}] 搜尋索引上傳失敗: {e}")

    print(f"   [INFO] 共上傳 {len(grouped)} 個頁面的搜尋索引 (總計 {len(search_entries)} 段落)")


def migrate_site_config(db):
    """上傳網站設定到 Firestore site_config collection"""
    print("\n[INFO] 正在上傳網站設定...")

    config = {
        'layout_version': '6.6',
        'publish_date': '2026-07-07',
        'site_name': 'Ludwica 的簡單歷史課',
        'site_url': 'https://ludwica-history-lesson.pages.dev/',
        'description': '深度歷史專題研究與報告'
    }

    db.collection('site_config').document('metadata').set(config)
    print(f"   [OK] 網站設定已上傳")


def main():
    print("=" * 60)
    print("Ludwica 歷史課 — Firestore 資料遷移工具")
    print("=" * 60)

    # 確認 API 資料存在
    catalog_path = "api/articles.json"
    if not os.path.exists(catalog_path):
        print(f"[ERROR] 找不到 {catalog_path}")
        print("   請先執行 python build_static_chunks.py 生成 API 資料")
        sys.exit(1)

    # 讀取文章目錄
    with open(catalog_path, 'r', encoding='utf-8') as f:
        catalog_data = json.load(f)

    articles_count = len(catalog_data.get('articles', []))
    categories_count = len(catalog_data.get('categories', []))
    print(f"\n[INFO] 本地資料: {articles_count} 篇文章, {categories_count} 個分類")

    # 初始化 Firestore
    db = init_firestore()
    print("[OK] Firestore 連線成功！")

    # 執行遷移
    migrate_categories(db, catalog_data)
    migrate_articles(db, catalog_data)
    migrate_worklog(db, catalog_data)
    migrate_search_index(db)
    migrate_site_config(db)

    print("\n" + "=" * 60)
    print("資料遷移完成！")
    print("=" * 60)
    print(f"   文章: {articles_count} 篇")
    print(f"   分類: {categories_count} 個")
    print(f"   搜尋索引: 已上傳")
    print(f"   更新日誌: 已上傳")
    print(f"   網站設定: 已上傳")
    print("\n   下一步: 在瀏覽器中測試 index.html")


if __name__ == '__main__':
    main()
