import subprocess
import shutil
import sys
import os
import glob

def run_script(script_name):
    print(f"\n==========================================")
    print(f"Running: {script_name}")
    print(f"==========================================")
    try:
        # Use sys.executable to ensure we run under the same Python interpreter
        res = subprocess.run([sys.executable, script_name], check=True)
        if res.returncode == 0:
            print(f"[OK] {script_name} completed successfully.")
            return True
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] {script_name} failed with exit code {e.returncode}!")
        return False
    except Exception as e:
        print(f"[ERROR] Failed to execute {script_name}: {e}")
        return False
    return False

def find_service_account_key():
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

def main():
    print("=== STARTING LUDWICA HISTORY PORTAL COMPILATION PIPELINE ===")

    # 1. Rebuild HTML and sitemaps
    if not run_script("build_html_md.py"):
        sys.exit(1)

    # 2. Rebuild static JSON Chunks for API fallbacks
    if not run_script("build_static_chunks.py"):
        sys.exit(1)

    # 3. Synchronize to Firebase Firestore (if credentials exist)
    key_path = find_service_account_key()
    if key_path:
        print(f"\n[KEY] Found Firebase credentials: {key_path}")
        if not run_script("migrate_to_firestore.py"):
            print("[WARNING] Firestore sync failed, continuing build...")
    else:
        print("\n[WARNING] No Firebase Service Account key found. Skipping Firestore sync.")

    # 4. 驗證 index.html
    #
    # [2026-07-21 修正] 此處原本會再執行一次 shutil.copyfile("index_db.html", "index.html")。
    # 但 build_html_md.py 早已完成「複製 index_db.html -> index.html」並在其後注入
    # 「全站文章索引」的 44 個靜態連結（供搜尋引擎爬行，首頁初始 HTML 原本沒有任何
    # 文章連結）。這裡再複製一次，會把剛注入好的索引整段覆蓋掉，且不會有任何錯誤訊息。
    #
    # 因此改為「驗證」而非「複製」：確認 build_html_md.py 的產出正確，若不正確則明確報錯。
    print(f"\n==========================================")
    print(f"Verifying index.html (article index injection)")
    print(f"==========================================")
    try:
        with open("index.html", "r", encoding="utf-8") as f:
            index_html = f.read()
        link_count = index_html.count('<li><a href="pages/page')
        if link_count == 0:
            print("[ERROR] index.html contains no static article links!")
            print("        Search engines will not be able to discover any article.")
            print("        Please re-run: python build_html_md.py")
            sys.exit(1)
        print(f"[OK] index.html verified ({link_count} static article links present)")
    except FileNotFoundError:
        print("[ERROR] index.html not found. Please run: python build_html_md.py")
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] Failed to verify index.html: {e}")
        sys.exit(1)

    print("\n[SUCCESS] PIPELINE COMPLETED SUCCESSFULLY!")
    print("===========================================================")

if __name__ == '__main__':
    main()
