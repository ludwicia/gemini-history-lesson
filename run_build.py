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

    # ------------------------------------------------------------------
    # [2026-07-21 修正] 步驟 1、2 合併為單一行程，消除重複建置。
    #
    # 原本這兩步各以子行程執行 build_html_md.py 與 build_static_chunks.py。
    # 但 build_static_chunks.py 的第 4 行是 `import build_html_md`，而
    # build_html_md.py 當時沒有 __main__ 保護，整份腳本都在模組層級，
    # 因此那個 import 會「從頭完整重跑一次建置」——44+ 個靜態頁、sitemap.xml、
    # robots.txt、index.html 注入全部寫兩遍，每次發布白白多花一倍時間。
    #
    # 現改為在同一個行程內 import 一次 build_html_md（完成所有文章處理），
    # 呼叫 write_site_outputs() 寫出檔案，再讓 build_static_chunks 沿用
    # 已載入的同一個模組（Python 的 sys.modules 快取保證不會重複執行）。
    # ------------------------------------------------------------------
    print(f"\n==========================================")
    print(f"Building site (single pass)")
    print(f"==========================================")
    try:
        import build_html_md
        build_html_md.write_site_outputs()
        print("[OK] build_html_md completed successfully.")
    except Exception as e:
        print(f"[ERROR] build_html_md failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    print(f"\n==========================================")
    print(f"Slicing static JSON chunks (reusing loaded module)")
    print(f"==========================================")
    try:
        import build_static_chunks
        build_static_chunks.main()
        print("[OK] build_static_chunks completed successfully.")
    except Exception as e:
        print(f"[ERROR] build_static_chunks failed: {e}")
        import traceback
        traceback.print_exc()
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

    # 5. 完整專案驗證
    #
    # [2026-07-21 新增] 把 verify_project.py 併入流程，讓「發布前的檢查」成為
    # 單一指令的一部分，不必再另外執行一次。四項檢查任一失敗即中止，
    # 避免把有問題的產出 commit 上線。
    print(f"\n==========================================")
    print(f"Running full project verification")
    print(f"==========================================")
    if not run_script("verify_project.py"):
        print("\n[FAILED] Verification did not pass. Nothing should be committed.")
        sys.exit(1)

    print("\n[SUCCESS] PIPELINE COMPLETED SUCCESSFULLY!")
    print("  下一步：git add -A && git commit -m \"發布：...\" && git push")
    print("===========================================================")

if __name__ == '__main__':
    main()
