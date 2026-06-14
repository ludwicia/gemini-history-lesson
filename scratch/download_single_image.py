import urllib.request
import time

url = 'https://upload.wikimedia.org/wikipedia/commons/b/b8/Hornbacher_Sakramentar_fol._8v.jpg'
path = 'images/creed_pirminius.jpg'

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5'
}

req = urllib.request.Request(url, headers=headers)

for attempt in range(5):
    try:
        print(f"Attempt {attempt+1}: Downloading to {path}...")
        with urllib.request.urlopen(req, timeout=15) as response:
            with open(path, 'wb') as f:
                f.write(response.read())
        print("Success!")
        break
    except Exception as e:
        print(f"Attempt {attempt+1} failed: {e}")
        time.sleep(3)
