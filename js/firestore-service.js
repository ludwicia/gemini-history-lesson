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
// 常數
// ============================================================
const APP_VERSION = '8.0';
const MAX_CACHED_ARTICLES = 10;

// ============================================================
// 快取層 — 避免重複讀取 Firestore
// ============================================================
const cache = {
    catalog: null,       // 文章元資料列表
    categories: null,    // 分類列表
    worklog: null,       // 更新日誌 HTML
    searchIndex: null,   // 搜尋索引
    articles: {},        // 單篇文章全文快取 (keyed by pageId)
    siteConfig: null,    // 網站設定
    _pending: {}         // 進行中的請求 Promise（防止重複請求）
};

// LRU 文章存取順序追蹤
const _articleAccessOrder = [];

// ============================================================
// 文章元資料（首頁用 — 不含 content_html）
// ============================================================
export async function getArticlesCatalog() {
    if (cache.catalog) return cache.catalog;
    if (cache._pending.catalog) return cache._pending.catalog;

    cache._pending.catalog = (async () => {
        try {
            const articlesRef = collection(db, 'articles');
            const snapshot = await getDocs(articlesRef);

            if (!snapshot.empty) {
                const articles = [];
                snapshot.forEach((docSnap) => {
                    const data = docSnap.data();
                    articles.push({
                        id: docSnap.id,
                        title: data.title,
                        seo_title: data.seo_title || `${data.title} — Ludwica 的簡單歷史課`,
                        seo_desc: data.seo_desc || data.desc || data.title,
                        ver: data.ver,
                        last_updated: data.last_updated,
                        category: data.category,
                        img: data.img,
                        is_doc: data.is_doc
                    });
                });
                cache.catalog = articles;
                return articles;
            }
        } catch (e) {
            console.warn('⚠️ Firestore 讀取失敗，嘗試 fallback 到本地 API:', e.message);
        }

        // Fallback: 從本地 /api/articles.json 讀取
        try {
            const res = await fetch(`/api/articles.json?v=${APP_VERSION}`);
            if (res.ok) {
                const data = await res.json();
                cache.catalog = data.articles;
                return data.articles;
            }
        } catch (e) {
            console.error('❌ 本地 API 也無法讀取:', e.message);
        }

        return [];
    })();

    try { return await cache._pending.catalog; } finally { delete cache._pending.catalog; }
}

// ============================================================
// 分類列表
// ============================================================
export async function getCategories() {
    if (cache.categories) return cache.categories;
    if (cache._pending.categories) return cache._pending.categories;

    cache._pending.categories = (async () => {
        try {
            const catRef = collection(db, 'categories');
            const q = query(catRef, orderBy('order', 'asc'));
            const snapshot = await getDocs(q);

            if (!snapshot.empty) {
                const categories = [];
                snapshot.forEach((docSnap) => {
                    categories.push({ id: docSnap.id, ...docSnap.data() });
                });
                cache.categories = categories;
                return categories;
            }
        } catch (e) {
            console.warn('⚠️ Firestore 分類讀取失敗，嘗試 fallback:', e.message);
        }

        // Fallback
        try {
            const res = await fetch(`/api/articles.json?v=${APP_VERSION}`);
            if (res.ok) {
                const data = await res.json();
                cache.categories = data.categories;
                return data.categories;
            }
        } catch (e) {
            console.error('❌ 分類 fallback 失敗:', e.message);
        }

        return [];
    })();

    try { return await cache._pending.categories; } finally { delete cache._pending.categories; }
}

// ============================================================
// 單篇文章全文（按需載入，LRU 快取上限 10 篇）
// ============================================================
export async function getArticleById(pageId) {
    // LRU: 更新存取順序
    if (cache.articles[pageId]) {
        const idx = _articleAccessOrder.indexOf(pageId);
        if (idx > -1) _articleAccessOrder.splice(idx, 1);
        _articleAccessOrder.push(pageId);
        return cache.articles[pageId];
    }
    if (cache._pending[`article_${pageId}`]) return cache._pending[`article_${pageId}`];

    cache._pending[`article_${pageId}`] = (async () => {
        try {
            const docRef = doc(db, 'article_contents', pageId);
            const docSnap = await getDoc(docRef);

            if (docSnap.exists()) {
                const article = { id: docSnap.id, ...docSnap.data() };
                _cacheArticle(pageId, article);
                return article;
            }
        } catch (e) {
            console.warn(`⚠️ Firestore 文章 [${pageId}] 讀取失敗，嘗試 fallback:`, e.message);
        }

        // Fallback
        try {
            const res = await fetch(`/api/article/${pageId}.json?v=${APP_VERSION}`);
            if (res.ok) {
                const article = await res.json();
                _cacheArticle(pageId, article);
                return article;
            }
        } catch (e) {
            console.error(`❌ 文章 [${pageId}] fallback 也失敗:`, e.message);
        }

        return null;
    })();

    try { return await cache._pending[`article_${pageId}`]; } finally { delete cache._pending[`article_${pageId}`]; }
}

/** LRU 快取文章，超過上限時淘汰最舊的 */
function _cacheArticle(pageId, article) {
    cache.articles[pageId] = article;
    const idx = _articleAccessOrder.indexOf(pageId);
    if (idx > -1) _articleAccessOrder.splice(idx, 1);
    _articleAccessOrder.push(pageId);

    // 淘汰最舊的快取
    while (_articleAccessOrder.length > MAX_CACHED_ARTICLES) {
        const oldest = _articleAccessOrder.shift();
        delete cache.articles[oldest];
    }
}

// ============================================================
// 更新日誌
// ============================================================
export async function getWorklog() {
    if (cache.worklog) return cache.worklog;
    if (cache._pending.worklog) return cache._pending.worklog;

    cache._pending.worklog = (async () => {
        try {
            const docRef = doc(db, 'worklog', 'current');
            const docSnap = await getDoc(docRef);

            if (docSnap.exists()) {
                cache.worklog = docSnap.data().html;
                return cache.worklog;
            }
        } catch (e) {
            console.warn('⚠️ Firestore 更新日誌讀取失敗:', e.message);
        }

        // Fallback: 從 articles.json 的 worklog 欄位
        try {
            const res = await fetch(`/api/articles.json?v=${APP_VERSION}`);
            if (res.ok) {
                const data = await res.json();
                cache.worklog = data.worklog;
                return data.worklog;
            }
        } catch (e) {
            console.error('❌ 更新日誌 fallback 失敗:', e.message);
        }

        return '';
    })();

    try { return await cache._pending.worklog; } finally { delete cache._pending.worklog; }
}

// ============================================================
// 全站搜尋索引
// ============================================================
export async function getSearchIndex() {
    if (cache.searchIndex) return cache.searchIndex;
    if (cache._pending.searchIndex) return cache._pending.searchIndex;

    cache._pending.searchIndex = (async () => {
        // 優先讀取本地 /api/search_index.json 快取（節省 Firestore 讀取量並加快搜尋速度）
        try {
            const res = await fetch('/api/search_index.json?v=' + APP_VERSION);
            if (res.ok) {
                const searchIndex = await res.json();
                cache.searchIndex = searchIndex;
                return searchIndex;
            }
        } catch (e) {
            console.warn('⚠️ 本地搜尋索引讀取失敗，嘗試 Firestore 雲端讀取:', e.message);
        }

        // Fallback 到 Firestore 雲端
        try {
            const indexRef = collection(db, 'search_index');
            const snapshot = await getDocs(indexRef);

            if (!snapshot.empty) {
                const searchIndex = [];
                snapshot.forEach((docSnap) => {
                    const data = docSnap.data();
                    // 每個 document 包含一個 pageId 和該頁的所有搜尋段落
                    if (data.blocks && Array.isArray(data.blocks)) {
                        data.blocks.forEach(text => {
                            searchIndex.push({ pageId: data.pageId, text });
                        });
                    }
                });
                cache.searchIndex = searchIndex;
                return searchIndex;
            }
        } catch (e) {
            console.error('❌ Firestore 搜尋索引讀取失敗:', e.message);
        }

        return [];
    })();

    try { return await cache._pending.searchIndex; } finally { delete cache._pending.searchIndex; }
}

// ============================================================
// 網站設定
// ============================================================
export async function getSiteConfig() {
    if (cache.siteConfig) return cache.siteConfig;
    if (cache._pending.siteConfig) return cache._pending.siteConfig;

    cache._pending.siteConfig = (async () => {
        try {
            const docRef = doc(db, 'site_config', 'metadata');
            const docSnap = await getDoc(docRef);

            if (docSnap.exists()) {
                cache.siteConfig = docSnap.data();
                return cache.siteConfig;
            }
        } catch (e) {
            console.warn('⚠️ Firestore 網站設定讀取失敗:', e.message);
        }

        // Default config
        cache.siteConfig = {
            layout_version: APP_VERSION,
            publish_date: new Date().toISOString().split('T')[0]
        };
        return cache.siteConfig;
    })();

    try { return await cache._pending.siteConfig; } finally { delete cache._pending.siteConfig; }
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
    cache._pending = {};
    _articleAccessOrder.length = 0;
}
