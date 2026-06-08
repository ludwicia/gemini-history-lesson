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
    except Exception as e:
        print(f"Error downloading {url}: {e}")

if __name__ == "__main__":
    images_to_fetch = [
        "Michael_Echter_Ungarnschlacht.jpg",
        "Emperor Otto I celebrating Whitsuntide at Quedlingburg, 973 by Moritz von Schwind.jpg",
        "Reisekonig.jpg",
        "Mainzer Hoffest.jpg"
    ]
    urls = get_wikimedia_image_urls(images_to_fetch)
    print("Found URLs:")
    for title, url in urls.items():
        print(f"  {title} -> {url}")
        
    # Download paths
    download_mapping = {
        "File:Michael Echter Ungarnschlacht.jpg": "michael_echter_ungarnschlacht.jpg",
        "File:Emperor Otto I celebrating Whitsuntide at Quedlingburg, 973 by Moritz von Schwind.jpg": "otto_quedlinburg_hoftag.jpg",
        "File:Reisekonig.jpg": "reisekönig_travelling_kings.jpg",
        "File:Mainzer Hoffest.jpg": "mainzer_hoffest_assembly.jpg"
    }
    
    workspace_images_dir = r"c:\Users\USER\gemini的簡單歷史課\images"
    os.makedirs(workspace_images_dir, exist_ok=True)
    for title, url in urls.items():
        if title in download_mapping:
            out_filename = os.path.join(workspace_images_dir, download_mapping[title])
            download_image(url, out_filename)
