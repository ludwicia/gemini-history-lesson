import urllib.request
import zipfile
import io

url = 'https://docs.google.com/document/d/1uDz2TQAiKfASZ7hGOLJ1ltCtWOv6Pnm1Nk_LDktTYbY/export?format=docx'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
try:
    with urllib.request.urlopen(req) as resp:
        data = resp.read()
        print("Downloaded docx size:", len(data))
        # open as zip
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            for info in z.infolist():
                print(f"{info.filename}: {info.file_size} bytes")
except Exception as e:
    print("Error:", e)
