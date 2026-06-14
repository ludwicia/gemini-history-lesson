import urllib.request
import json
import urllib.parse
import os

def get_wikimedia_image_urls(filenames):
    titles = "|".join([f"File:{name}" for name in filenames])
    url = f"https://commons.wikimedia.org/w/api.php?action=query&titles={urllib.parse.quote(titles)}&prop=imageinfo&iiprop=url&format=json"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode('utf-8'))
            pages = data.get('query', {}).get('pages', {})
            urls = {}
            for page_id, page_data in pages.items():
                title = page_data.get('title', '')
                imageinfo = page_data.get('imageinfo', [])
                if imageinfo:
                    urls[title] = imageinfo[0].get('url')
            return urls
    except Exception as e:
        print(f"Error fetching from Wikimedia API: {e}")
        return {}

def download_image(url, output_path):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req) as response:
            with open(output_path, 'wb') as f:
                f.write(response.read())
        print(f"Successfully downloaded to {output_path}")
        return True
    except Exception as e:
        print(f"Error downloading {url}: {e}")
        return False

def main():
    images_to_fetch = [
        "Detail of Apostles' Creed from Compost et calendrier des bergers.jpg",
        "Arian Baptistry ceiling mosaic - Ravenna.jpg",
        "Hornbacher Sakramentar fol. 8v.jpg"
    ]
    
    urls = get_wikimedia_image_urls(images_to_fetch)
    print("Found URLs:")
    for title, url in urls.items():
        print(f"  {title} -> {url}")
        
    download_mapping = {
        "File:Detail of Apostles' Creed from Compost et calendrier des bergers.jpg": "creed_main.jpg",
        "File:Arian Baptistry ceiling mosaic - Ravenna.jpg": "creed_baptism.jpg",
        "File:Hornbacher Sakramentar fol. 8v.jpg": "creed_pirminius.jpg"
    }
    
    workspace_images_dir = r"c:\Users\USER\gemini的簡單歷史課\images"
    os.makedirs(workspace_images_dir, exist_ok=True)
    
    for title, url in urls.items():
        if title in download_mapping and url:
            out_filename = os.path.join(workspace_images_dir, download_mapping[title])
            download_image(url, out_filename)

if __name__ == '__main__':
    main()
