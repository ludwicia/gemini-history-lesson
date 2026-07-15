import os
import re
import sys
import filecmp
import json

def check_files_exist():
    print("Checking referenced markdown files...")
    if not os.path.exists('course_config.json'):
        print("[ERROR] course_config.json is missing.")
        return False
    with open('course_config.json', 'r', encoding='utf-8') as f:
        config = json.load(f)

    checked_count = 0
    articles = config.get("articles", {})
    for pid, art in articles.items():
        file_path = art.get("file_path")
        if file_path:
            if not os.path.exists(file_path):
                print(f"[ERROR] File {file_path} referenced in {pid} does not exist!")
                return False
            checked_count += 1
        file_path_en = art.get("file_path_en")
        if file_path_en:
            if not os.path.exists(file_path_en):
                print(f"[ERROR] English file {file_path_en} referenced in {pid} does not exist!")
                return False
            checked_count += 1
    print(f"[OK] All {checked_count} referenced markdown files exist.")
    return True

def check_images_exist():
    print("Checking referenced images...")
    if not os.path.exists('course_config.json'):
        print("[ERROR] course_config.json is missing.")
        return False
    with open('course_config.json', 'r', encoding='utf-8') as f:
        config = json.load(f)

    config_images = set()
    articles = config.get("articles", {})

    # Gather all images from config
    for pid, art in articles.items():
        img_path = art.get("img")
        if img_path and img_path.startswith("images/"):
            config_images.add(img_path)

        map_html = art.get("map_html")
        if map_html:
            for img_match in re.findall(r'src=["\'](images/[^"\']+)["\']', map_html):
                config_images.add(img_match)

        repls = art.get("image_replacements", [])
        for item in repls:
            u = item.get("url")
            if u and u.startswith("images/"):
                config_images.add(u)

    # Gather category images
    for cat in config.get("categories", []):
        c_img = cat.get("img")
        if c_img and c_img.startswith("images/"):
            config_images.add(c_img)

    # Gather images from markdown files
    md_images = set()
    for pid, art in articles.items():
        for path_key in ["file_path", "file_path_en"]:
            file_path = art.get(path_key)
            if file_path and os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
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
