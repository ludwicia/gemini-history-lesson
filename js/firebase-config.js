/**
 * Firebase Configuration & Initialization
 * Ludwica 的簡單歷史課 — Firebase Firestore Integration
 *
 * 初始化 Firebase App 和 Firestore 資料庫連線。
 * 使用 Firebase SDK v12 ESM CDN 模式。
 */

import { initializeApp } from 'https://www.gstatic.com/firebasejs/12.15.0/firebase-app.js';
import { getFirestore } from 'https://www.gstatic.com/firebasejs/12.15.0/firebase-firestore.js';

// Firebase 專案配置 — ludwica-history
const firebaseConfig = {
    apiKey: "AIzaSyBhV2fFj7WFMrOz8OFGzzn8xRveJmgCtzY",
    authDomain: "ludwica-history.firebaseapp.com",
    projectId: "ludwica-history",
    storageBucket: "ludwica-history.firebasestorage.app",
    messagingSenderId: "131084017287",
    appId: "1:131084017287:web:6af26d60564fb30ba86222"
};

// 初始化 Firebase（含錯誤處理）
let db = null;
try {
    const app = initializeApp(firebaseConfig);
    db = getFirestore(app);
} catch (e) {
    console.error('Firebase 初始化失敗:', e);
}

export { db };
