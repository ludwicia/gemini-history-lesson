/**
 * Firestore Data Service
 * Ludwica 的簡單歷史課 — Firestore 資料讀取服務
 *
 * 所有從 Firestore 讀取文章、分類、搜尋索引的函式。
 * 提供 fallback 到本地 /api/ JSON 的雙軌模式。
 */

import { db } from './firebase-config.js';
import {
    collection,
    doc,
    getDocs,
    getDoc,
    query,
    orderBy
} from 'https://www.gstatic.com/firebasejs/12.15.0/firebase-firestore.js';

// ============================================================
// 快取層 — 避免重複讀取 Firestore
// ============================================================
const cache = {
    catalog: null,       // 文章元資料列表
    categories: null,    // 分類列表
    worklog: null,       // 更新日誌 HTML
    searchIndex: null,   // 搜尋索引
    articles: {},        // 單篇文章全文快取 (keyed by pageId)
    siteConfig: null     // 網站設定
};

// ============================================================
// 文章元資料（首頁用 — 不含 content_html）
// ============================================================
export async function getArticlesCatalog() {
    if (cache.catalog) return cache.catalog;

    try {
        // 嘗試從 Firestore 讀取
        const articlesRef = collection(db, 'articles');
        const snapshot = await getDocs(articlesRef);

        if (!snapshot.empty) {
            const articles = [];
            snapshot.forEach((doc) => {
                const data = doc.data();
                articles.push({
                    id: doc.id,
                    title: data.title,
                    ver: data.ver,
                    last_updated: data.last_updated,
                    category: data.category,
                    img: data.img,
                    is_doc: data.is_doc
                });
            });
            cache.catalog = articles;
            console.log(`🔥 Firestore: 成功載入 ${articles.length} 篇文章元資料`);
            return articles;
        }
    } catch (e) {
        console.warn('⚠️ Firestore 讀取失敗，嘗試 fallback 到本地 API:', e.message);
    }

    // Fallback: 從本地 /api/articles.json 讀取
    try {
        const res = await fetch(`/api/articles.json?_t=${Date.now()}`);
        if (res.ok) {
            const data = await res.json();
            cache.catalog = data.articles;
            console.log('📁 Fallback: 從本地 API 載入文章元資料');
            return data.articles;
        }
    } catch (e) {
        console.error('❌ 本地 API 也無法讀取:', e.message);
    }

    return [];
}

// ============================================================
// 分類列表
// ============================================================
export async function getCategories() {
    if (cache.categories) return cache.categories;

    try {
        const catRef = collection(db, 'categories');
        const q = query(catRef, orderBy('order', 'asc'));
        const snapshot = await getDocs(q);

        if (!snapshot.empty) {
            const categories = [];
            snapshot.forEach((doc) => {
                categories.push({ id: doc.id, ...doc.data() });
            });
            cache.categories = categories;
            console.log(`🔥 Firestore: 成功載入 ${categories.length} 個分類`);
            return categories;
        }
    } catch (e) {
        console.warn('⚠️ Firestore 分類讀取失敗，嘗試 fallback:', e.message);
    }

    // Fallback
    try {
        const res = await fetch(`/api/articles.json?_t=${Date.now()}`);
        if (res.ok) {
            const data = await res.json();
            cache.categories = data.categories;
            return data.categories;
        }
    } catch (e) {
        console.error('❌ 分類 fallback 失敗:', e.message);
    }

    return [];
}

// ============================================================
// 單篇文章全文（按需載入）
// ============================================================
export async function getArticleById(pageId) {
    if (cache.articles[pageId]) return cache.articles[pageId];

    try {
        const docRef = doc(db, 'article_contents', pageId);
        const docSnap = await getDoc(docRef);

        if (docSnap.exists()) {
            const article = { id: docSnap.id, ...docSnap.data() };
            cache.articles[pageId] = article;
            console.log(`🔥 Firestore: 成功載入文章 [${pageId}] — ${article.title}`);
            return article;
        }
    } catch (e) {
        console.warn(`⚠️ Firestore 文章 [${pageId}] 讀取失敗，嘗試 fallback:`, e.message);
    }

    // Fallback
    try {
        const res = await fetch(`/api/article/${pageId}.json?_t=${Date.now()}`);
        if (res.ok) {
            const article = await res.json();
            cache.articles[pageId] = article;
            console.log(`📁 Fallback: 從本地 API 載入文章 [${pageId}]`);
            return article;
        }
    } catch (e) {
        console.error(`❌ 文章 [${pageId}] fallback 也失敗:`, e.message);
    }

    return null;
}

// ============================================================
// 更新日誌
// ============================================================
export async function getWorklog() {
    if (cache.worklog) return cache.worklog;

    try {
        const docRef = doc(db, 'worklog', 'current');
        const docSnap = await getDoc(docRef);

        if (docSnap.exists()) {
            cache.worklog = docSnap.data().html;
            console.log('🔥 Firestore: 成功載入更新日誌');
            return cache.worklog;
        }
    } catch (e) {
        console.warn('⚠️ Firestore 更新日誌讀取失敗:', e.message);
    }

    // Fallback: 從 articles.json 的 worklog 欄位
    try {
        const res = await fetch(`/api/articles.json?_t=${Date.now()}`);
        if (res.ok) {
            const data = await res.json();
            cache.worklog = data.worklog;
            return data.worklog;
        }
    } catch (e) {
        console.error('❌ 更新日誌 fallback 失敗:', e.message);
    }

    return '';
}

// ============================================================
// 全站搜尋索引
// ============================================================
export async function getSearchIndex() {
    if (cache.searchIndex) return cache.searchIndex;

    try {
        const indexRef = collection(db, 'search_index');
        const snapshot = await getDocs(indexRef);

        if (!snapshot.empty) {
            const searchIndex = [];
            snapshot.forEach((doc) => {
                const data = doc.data();
                // 每個 document 包含一個 pageId 和該頁的所有搜尋段落
                if (data.blocks && Array.isArray(data.blocks)) {
                    data.blocks.forEach(text => {
                        searchIndex.push({ pageId: data.pageId, text });
                    });
                }
            });
            cache.searchIndex = searchIndex;
            console.log(`🔥 Firestore: 成功載入搜尋索引 (${searchIndex.length} 段落)`);
            return searchIndex;
        }
    } catch (e) {
        console.warn('⚠️ Firestore 搜尋索引讀取失敗，嘗試 fallback:', e.message);
    }

    // Fallback
    try {
        const res = await fetch('/api/search_index.json?_t=' + Date.now());
        if (res.ok) {
            const searchIndex = await res.json();
            cache.searchIndex = searchIndex;
            console.log('📁 Fallback: 從本地 API 載入搜尋索引');
            return searchIndex;
        }
    } catch (e) {
        console.error('❌ 搜尋索引 fallback 失敗:', e.message);
    }

    return [];
}

// ============================================================
// 網站設定
// ============================================================
export async function getSiteConfig() {
    if (cache.siteConfig) return cache.siteConfig;

    try {
        const docRef = doc(db, 'site_config', 'metadata');
        const docSnap = await getDoc(docRef);

        if (docSnap.exists()) {
            cache.siteConfig = docSnap.data();
            console.log('🔥 Firestore: 成功載入網站設定');
            return cache.siteConfig;
        }
    } catch (e) {
        console.warn('⚠️ Firestore 網站設定讀取失敗:', e.message);
    }

    // Default config
    cache.siteConfig = {
        layout_version: '6.0',
        publish_date: new Date().toISOString().split('T')[0]
    };
    return cache.siteConfig;
}

// ============================================================
// 清除快取（用於強制重新載入）
// ============================================================
export function clearCache() {
    cache.catalog = null;
    cache.categories = null;
    cache.worklog = null;
    cache.searchIndex = null;
    cache.articles = {};
    cache.siteConfig = null;
    console.log('🗑️ 快取已清除');
}
