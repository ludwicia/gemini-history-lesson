import urllib.request
import os
import time

images_to_download = {
    "images/carolingian_main.jpg": "https://upload.wikimedia.org/wikipedia/commons/0/00/Charlemagne_miniscule.jpg",
    "images/carolingian_alcuin.jpg": "https://upload.wikimedia.org/wikipedia/commons/b/b9/Charlemagne_et_Alcuin.jpg",
    "images/carolingian_stgall.jpg": "https://upload.wikimedia.org/wikipedia/commons/5/54/St._Galler_Klosterplan.jpg",
    "images/carolingian_lorsch.jpg": "https://upload.wikimedia.org/wikipedia/commons/f/f1/Torhalle_Lorsch.JPG",
    "images/carolingian_majesty.jpg": "https://upload.wikimedia.org/wikipedia/commons/1/17/Christ_in_majesty_VandA_A.32-1928.jpg",
    "images/paper_main.jpg": "https://upload.wikimedia.org/wikipedia/commons/0/0b/Paper_production.jpg",
    "images/paper_hollander.jpg": "https://upload.wikimedia.org/wikipedia/commons/7/72/Hollander_beater.jpg",
    "images/paper_gutenberg.jpg": "https://upload.wikimedia.org/wikipedia/commons/b/b6/Gutenberg_Bible%2C_Lenox_Copy%2C_New_York_Public_Library%2C_2009._Pic_01.jpg",
    "images/paper_press.jpg": "https://upload.wikimedia.org/wikipedia/commons/b/bf/Printing_press.jpg"
}

# Standard Chrome browser User-Agent works flawlessly on upload.wikimedia.org
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

os.makedirs("images", exist_ok=True)

print("Starting robust download of all 9 images...")
for path, url in images_to_download.items():
    # If the file already exists with a non-zero size, we can skip it to avoid extra requests
    if os.path.exists(path) and os.path.getsize(path) > 0:
        print(f"File {path} already exists. Skipping download.")
        continue

    success = False
    retries = 3
    delay = 4  # 4 seconds initial delay
    
    for attempt in range(retries):
        print(f"Downloading {url} to {path} (Attempt {attempt+1}/{retries})...")
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req) as response:
                with open(path, 'wb') as f:
                    f.write(response.read())
            print(f"Successfully downloaded {path} (Size: {os.path.getsize(path)} bytes)")
            success = True
            break
        except Exception as e:
            print(f"Attempt {attempt+1} failed: {e}")
            if "429" in str(e):
                print(f"Rate limited (429). Waiting {delay * 2} seconds before retrying...")
                time.sleep(delay * 2)
            else:
                time.sleep(delay)
            delay *= 1.5

    if not success:
        print(f"FAILED permanently to download {path}")
    
    # Wait 4 seconds between different file requests to avoid rate limits
    print("Waiting 4 seconds before next download...")
    time.sleep(4)

print("Image download process finished.")
