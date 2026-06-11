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
    # Unescape markdown-escaped backslashes in URL first
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
    filepath = 'course/西元紀年的確立與演進：從歷史考證、政治妥協到全球數位化時間標準的建構.md'
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        
    parts = content.split('#### 引用的著作')
    if len(parts) < 2:
        parts = content.split('## 引用來源')
    if len(parts) < 2:
        parts = content.split('## 參考文獻')
    if len(parts) < 2:
        print("No bibliography section found!")
        return
        
    body = parts[0]
    bib = parts[1]
    
    lines = bib.strip().split('\n')
    new_lines = []
    
    for line in lines:
        line = line.strip()
        if not line:
            new_lines.append('')
            continue
            
        # Match standard link: 1. [Title](URL)
        m_standard = re.match(r'^(\d+\.\s+)\[([^\]]+)\]\(([^)]+)\)$', line)
        
        # Match unformatted link: 3. Title, [URL](URL)
        m_unformatted = re.match(r'^(\d+\.\s+)(.*?),\s*\[(https?://[^\]]+)\]\(\3\)$', line)
        
        # Match unformatted link with backslashes or slightly mismatching URL: 3. Title, [URL1](URL2)
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
            url = m_mismatch.group(4).strip() # use actual href
        else:
            new_lines.append(line)
            continue
            
        # Unescape markdown backslashes in URL and title
        url = url.replace('\\', '')
        title = title.replace('\\', '')
        
        # Validate link
        status, clean_url = check_link(url)
        try:
            print(f"Checking {index} {title}: Status = {status}")
        except:
            # Bypass print encoding errors silently
            pass
        
        formatted_line = f"{index}[{title}]({clean_url})"
        new_lines.append(formatted_line)
        
    new_bib = '\n'.join(new_lines)
    
    # Write back
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(body + '#### 引用的著作\n\n' + new_bib + '\n')
    print("Done formatting bibliography!")

if __name__ == '__main__':
    main()
