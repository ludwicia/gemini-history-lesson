import re
import urllib.parse

def check_title(title, url):
    if not title:
        parsed_url = urllib.parse.urlparse(url)
        if 'wikipedia.org' in parsed_url.netloc:
            path_parts = parsed_url.path.strip('/').split('/')
            if len(path_parts) >= 2 and path_parts[0] == 'wiki':
                wiki_title = urllib.parse.unquote(path_parts[1]).replace('_', ' ')
                title = f"{wiki_title} - Wikipedia"
            else:
                title = "Wikipedia"
        else:
            domain = parsed_url.netloc.replace('www.', '')
            title = f"Reference link on {domain}"
    return title

def test():
    lines = [
        "1. Historical trajectory of the Apostles' Creed | Theologia est doctrina Deo vivendi per Christum, 檢索日期：6月 14, 2026， [https://deovivendiperchristum.wordpress.com/2013/10/20/historical-trajectory-of-the-apostles-creed/](https://deovivendiperchristum.wordpress.com/2013/10/20/historical-trajectory-of-the-apostles-creed/)",
        "2. Apostles' Creed; The - International Standard Bible Encyclopedia, 檢索日期：6月 14, 2026， [https://www.internationalstandardbible.com/A/apostles-creed-the.html](https://www.internationalstandardbible.com/A/apostles-creed-the.html)",
        "3. Apostles' Creed - Grokipedia, 檢索日期：6月 14, 2026， [https://grokipedia.com/page/Apostles'\\_Creed](https://grokipedia.com/page/Apostles'_Creed)",
        "10. 檢索日期：6月 14, 2026， [https://en.wikipedia.org/wiki/Old\\_Roman\\_Symbol#:~:text=The%20Old%20Roman%20Symbol%20(Latin,writers%20as%20Tertullian%20and%20Irenaeus.](https://en.wikipedia.org/wiki/Old_Roman_Symbol#:~:text=The%20Old%20Roman%20Symbol%20(Latin,writers%20as%20Tertullian%20and%20Irenaeus.)"
    ]
    
    for line in lines:
        stripped = line.strip()
        m_standard = re.match(r'^(\d+\.\s+)\[([^\]]+)\]\(([^)]+)\)$', stripped)
        m_unformatted_with_date = re.match(
            r'^(\d+\.\s+)(.*?)(?:(?:,\s*|，\s*)?檢索日期：.*?(?:，|,)?\s*)?\[(https?://[^\s\]]+)\]\((https?://[^\s)]+)\)$',
            stripped
        )
        
        if m_standard:
            print(f"STANDARD: {m_standard.group(1)} [{m_standard.group(2)}]({m_standard.group(3)})")
        elif m_unformatted_with_date:
            index = m_unformatted_with_date.group(1)
            title = m_unformatted_with_date.group(2).replace('\\', '').strip(',， ')
            url = m_unformatted_with_date.group(4).replace('\\', '').strip()
            title = check_title(title, url)
            print(f"UNFORMATTED: {index} [{title}]({url})")
        else:
            print(f"FAIL: {line}")

if __name__ == '__main__':
    test()
