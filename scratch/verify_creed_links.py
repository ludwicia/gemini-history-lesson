import re
import urllib.request
import urllib.parse
import sys

# Set default output encoding to utf-8 if possible
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

def check_link(url):
    url = url.replace('\\', '')
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    # Try with HEAD request first, fallback to GET
    req = urllib.request.Request(url, headers=headers, method='HEAD')
    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            return response.status, url
    except Exception as e:
        # Fallback to GET
        req = urllib.request.Request(url, headers=headers, method='GET')
        try:
            with urllib.request.urlopen(req, timeout=5) as response:
                return response.status, url
        except Exception as e2:
            return f"Error: {e2}", url

def main():
    filepath = '使徒信經的歷史演變與神學建構：從早期羅馬洗禮宣誓到西方大公信仰奠基的學術研究報告.md'
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        
    parts = content.split('## 引用來源')
    if len(parts) < 2:
        parts = content.split('## 參考文獻')
    if len(parts) < 2:
        parts = content.split('## 參考資料')
    if len(parts) < 2:
        # Let's search for the last occurrence of ## or ####
        parts = re.split(r'(\n##+\s+(?:引記的著作|引用的著作|引用來源|參考文獻|參考資料|Bibliography|References)\s*\n)', content, maxsplit=1, flags=re.IGNORECASE)
        if len(parts) >= 3:
            parts = [parts[0], parts[1] + parts[2]]
        else:
            print("No bibliography section found!")
            return
        
    body = parts[0]
    bib = parts[1]
    
    lines = bib.strip().split('\n')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        m_standard = re.match(r'^(\d+\.\s+)\[([^\]]+)\]\(([^)]+)\)$', line)
        m_unformatted = re.match(r'^(\d+\.\s+)(.*?),\s*\[(https?://[^\]]+)\]\(\3\)$', line)
        m_mismatch = re.match(r'^(\d+\.\s+)(.*?),\s*\[(https?://[^\]]+)\]\((https?://[^)]+)\)$', line)
        
        if m_standard:
            index = m_standard.group(1)
            title = m_standard.group(2).strip()
            url = m_standard.group(3).strip()
        elif m_unformatted:
            index = m_unformatted.group(1)
            title = m_unformatted.group(2).strip()
            url = m_unformatted.group(3).strip()
        elif m_mismatch:
            index = m_mismatch.group(1)
            title = m_mismatch.group(2).strip()
            url = m_mismatch.group(4).strip()
        else:
            # Try to find any URL in line
            url_match = re.search(r'(https?://[^\s)\]]+)', line)
            if url_match:
                index = "Unknown"
                title = line[:50]
                url = url_match.group(1)
            else:
                continue
            
        url = url.replace('\\', '')
        status, clean_url = check_link(url)
        print(f"[{index}] {title[:60]}: URL = {url} => STATUS = {status}")

if __name__ == '__main__':
    main()
