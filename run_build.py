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

    # 4. Synchronize index_db.html to index.html (cross-platform copy)
    print(f"\n==========================================")
    print(f"Copying index_db.html to index.html (cross-platform)")
    print(f"==========================================")
    try:
        shutil.copyfile("index_db.html", "index.html")
        print("[OK] Successfully synchronized index_db.html -> index.html")
    except Exception as e:
        print(f"[ERROR] Failed to copy file: {e}")
        sys.exit(1)

    print("\n[SUCCESS] PIPELINE COMPLETED SUCCESSFULLY!")
    print("===========================================================")

if __name__ == '__main__':
    main()
