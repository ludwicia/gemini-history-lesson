import os
import re
import sys
import filecmp

# Add root dir to sys.path so we can import build_html_md
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import build_html_md (which triggers page building and writes static file to index.html)
import build_html_md

# Immediately restore index.html from index_db.html source of truth
with open('index_db.html', 'rb') as _f_src:
    _db_content = _f_src.read()
with open('index.html', 'wb') as _f_dst:
    _f_dst.write(_db_content)

def check_files_exist():
    print("Checking referenced markdown files...")
    import build_html_md
    checked_count = 0
    for name, val in vars(build_html_md).items():
        if name.startswith('file_p') and isinstance(val, str):
            if not os.path.exists(val):
                print(f"[ERROR] File {val} referenced as {name} does not exist!")
                return False
            checked_count += 1
    print(f"[OK] All {checked_count} referenced markdown files exist.")
    return True

def check_images_exist():
    print("Checking referenced images...")
    import build_html_md

    # 1. Gather all images from config variables
    config_images = set()
    for name, val in vars(build_html_md).items():
        # check map_pXX strings
        if name.startswith('map_p') and isinstance(val, str):
            for img_match in re.findall(r'src=["\'](images/[^"\']+)["\']', val):
                config_images.add(img_match)
        # check images_pXX lists of tuples
        if name.startswith('images_p') and isinstance(val, list):
            for item in val:
                if isinstance(item, tuple) and len(item) >= 2:
                    img_path = item[1]
                    if img_path.startswith('images/'):
                        config_images.add(img_path)

    # 2. Gather images from markdown files themselves
    md_images = set()
    for name, val in vars(build_html_md).items():
        if name.startswith('file_p') and isinstance(val, str) and os.path.exists(val):
            with open(val, 'r', encoding='utf-8') as f:
                content = f.read()
            # Match standard md images: ![alt](path)
            for img_match in re.findall(r'!\[.*?\]\((images/[^)]+)\)', content):
                md_images.add(img_match)
            # Match HTML img tags: <img src="path" ...>
            for img_match in re.findall(r'<img\s+[^>]*src=["\'](images/[^"\']+)["\']', content):
                md_images.add(img_match)

    all_referenced_images = config_images.union(md_images)
    missing_images = []

    for img in all_referenced_images:
        # Normalize path
        normalized_path = img.replace('/', os.sep)
        if not os.path.exists(normalized_path):
            missing_images.append(img)

    if missing_images:
        print(f"[ERROR] Found {len(missing_images)} missing images:")
        for img in missing_images:
            print(f"   - {img}")
        return False

    print(f"[OK] All {len(all_referenced_images)} referenced images exist in filesystem.")
    return True

def check_index_sync():
    print("Checking if index.html is synchronized with index_db.html...")
    if not os.path.exists('index.html') or not os.path.exists('index_db.html'):
        print("[ERROR] index.html or index_db.html is missing.")
        return False

    if not filecmp.cmp('index.html', 'index_db.html', shallow=False):
        print("[ERROR] index.html is OUT OF SYNC with index_db.html!")
        print("   If you just rebuilt the site, please copy the dynamic version back to index.html:")
        print("   cmd: copy index_db.html index.html")
        return False

    print("[OK] index.html is in sync with index_db.html.")
    return True

def main():
    print("=== Running Ludwica Project Verification ===\n")
    success = True

    if not check_files_exist():
        success = False
    print()

    if not check_images_exist():
        success = False
    print()

    if not check_index_sync():
        success = False
    print()

    if not success:
        print("[FAIL] Project verification FAILED.")
        sys.exit(1)

    print("[SUCCESS] Project verification PASSED successfully!")
    sys.exit(0)

if __name__ == '__main__':
    main()
