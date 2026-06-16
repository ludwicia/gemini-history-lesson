import sys
import re
import os
import urllib.request
import urllib.parse

def extract_doc_id(url):
    # Matches /document/d/DOC_ID/
    match = re.search(r'/document/d/([a-zA-Z0-9-_]+)', url)
    if match:
        return match.group(1)
    return None

def fetch_gdoc_html(doc_id):
    export_url = f"https://docs.google.com/document/d/{doc_id}/export?format=html"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    req = urllib.request.Request(export_url, headers=headers)
    try:
        with urllib.request.urlopen(req) as response:
            return response.read().decode('utf-8')
    except Exception as e:
        print(f"Error fetching Google Doc: {e}")
        return None

def clean_filename(name):
    # Remove characters that are invalid in Windows filenames
    return re.sub(r'[\\/*?:"<>|]', "", name).strip()

def format_citations(text):
    # Split body and bibliography to avoid changing bibliography index numbers.
    bib_pattern = r'(\r?\n##+\s+(?:引記的著作|引用的著作|引用來源|參考文獻|參考資料|Bibliography|References)\s*\r?\n)'
    parts = re.split(bib_pattern, text, maxsplit=1, flags=re.IGNORECASE)
    
    if len(parts) == 3:
        body = parts[0]
        bib = parts[1] + parts[2]
    else:
        body = text
        bib = ""
        
    # Pattern for citation numbers
    # We first un-escape brackets for citations if markdownify escaped them: \[1\] -> [1]
    body = re.sub(r'\\\[(\d{1,2})\\\]', r'[\1]', body)
    
    # Then format [\d+] into <sup>[\1]</sup> only if not already in sup
    body = re.sub(r'(?<!<sup>)\[(\d{1,2})\](?!</sup>)', r'<sup>[\1]</sup>', body)
    
    # And handle raw numbers that might be just superscripted without brackets (supporting optional spaces before them)
    pattern = r'([\u4e00-\u9fff》）』」a-zA-Z*])\s*(\d{1,2})(?!\s*(?:次|個|件|年|月|日|萬|億|元|位|歲|分|秒|px|em|rem|%))(?=[\s。，；、：：！!？\?』」）\)\]\]〕〉》|]|$|<])'
    body = re.sub(pattern, r"\1<sup>[\2]</sup>", body)
    
    return body + bib

def clean_google_redirects(text):
    def repl(match):
        import urllib.parse
        url = match.group(0)
        parsed = urllib.parse.urlparse(url)
        qs = urllib.parse.parse_qs(parsed.query)
        if 'q' in qs:
            return qs['q'][0]
        return url
    return re.sub(r'https?://www\.google\.com/url\?[^\s)\]">]+', repl, text)

def make_urls_clickable(text):
    # Match standard HTTP/HTTPS URLs not already inside a markdown link
    # This avoids double-wrapping [http...](http...)
    def repl(match):
        url = match.group(0)
        return f"[{url}]({url})"
    
    # Temporarily hide valid markdown links
    links = []
    def hide_link(m):
        links.append(m.group(0))
        return f"__MD_LINK_{len(links)-1}__"
    
    text = re.sub(r'\[[^\]]+\]\([^)]+\)', hide_link, text)
    
    url_pattern = r'(?<![("<=])(https?://[a-zA-Z0-9\-._~:/?#@!$&\'*+,;=%]+)'
    text = re.sub(url_pattern, repl, text)
    
    # Restore markdown links
    for i, link in enumerate(links):
        text = text.replace(f"__MD_LINK_{i}__", link)
        
    # Clean up redundant self-referencing markdown links if any
    text = re.sub(r'\[\[(https?://.*?)\]\(\1\)\]\(\1\)', r'[\1](\1)', text)
    return text

def format_reference_links(text):
    """
    Finds the bibliography section, parses and formats each reference line
    to 'index. [Title](URL)' (e.g. '1. [Title](http...)'), cleans backslashes,
    and returns the updated document text.
    """
    # Find the bibliography header
    parts = re.split(r'(\r?\n##+\s+(?:引記的著作|引用的著作|引用來源|參考文獻|參考資料|Bibliography|References)\s*\r?\n)', text, maxsplit=1, flags=re.IGNORECASE)
    
    if len(parts) < 3:
        # If no explicit bibliography header, try to fallback to regex replacement on the whole text
        pattern = r'(\d+\.\s+)(.*?),\s*\[(https?://[^\]]+)\]\(\3\)'
        return re.sub(pattern, r'\1[\2](\3)', text)
        
    body = parts[0]
    header = parts[1]
    bib = parts[2]
    
    # Pre-process bib to split inline references (e.g., "1. Ref 2. Ref") onto separate lines
    bib = re.sub(r'(?<=\.|\)|\])\s+(\d{1,3}\.\s+)', r'\n\1', bib)
    lines = bib.split('\n')
    new_lines = []
    
    for line in lines:
        stripped = line.strip()
        if not stripped:
            new_lines.append(line) # keep original indentation/newlines
            continue
            
        # Match standard link: 1. [Title](URL)
        m_standard = re.match(r'^(\d+\.\s+)\[([^\]]+)\]\(([^)]+)\)$', stripped)
        
        # Match unformatted link with optional retrieval date: 1. Title, 檢索日期：... [URL](URL)
        m_unformatted = re.match(
            r'^(\d+\.\s+)(.*?)(?:(?:,\s*|，\s*)?檢索日期：.*?(?:，|,)?\s*)?\[(https?://[^\s\]]+)\]\((https?://[^\s)]+)\)$',
            stripped
        )

        # Match link button: 1. Title, [連結](URL)
        m_link_button = re.match(
            r'^(\d+\.\s+)(.*?)(?:(?:,\s*|，\s*)?)\s*\[(?:連結|Link|link)\]\((https?://.+)\)$',
            stripped
        )
        
        if m_standard:
            index = m_standard.group(1)
            title = m_standard.group(2).strip()
            url = m_standard.group(3).strip()
        elif m_unformatted:
            index = m_unformatted.group(1)
            title = m_unformatted.group(2).strip()
            url = m_unformatted.group(4).strip() # use actual href
            
            # Clean up empty titles by parsing them from the URL if possible
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
        elif m_link_button:
            index = m_link_button.group(1)
            title = m_link_button.group(2).strip().replace('*', '').strip('_，, ')
            url = m_link_button.group(3).strip()
        else:
            new_lines.append(line)
            continue
            
        # Clean backslashes in URL and title, and trim trailing commas
        url = url.replace('\\', '').strip()
        title = title.replace('\\', '').strip(',， ')
        
        formatted_line = f"{index}[{title}]({url})"
        new_lines.append(formatted_line)
        
    return body + header + '\n'.join(new_lines)

def ensure_markdownify():
    try:
        import markdownify
        return markdownify
    except ImportError:
        print("Installing required package 'markdownify'...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "markdownify", "beautifulsoup4"])
        import markdownify
        return markdownify

def main():
    if len(sys.argv) < 2:
        print("Usage: python import_gdoc.py <google_doc_url> [output_filename.md]")
        sys.exit(1)
        
    url = sys.argv[1]
    doc_id = extract_doc_id(url)
    
    if not doc_id:
        print("Error: Could not extract Document ID from the provided URL.")
        print("Please ensure it is a valid Google Docs link (e.g. https://docs.google.com/document/d/.../edit)")
        sys.exit(1)
        
    print(f"Detected Google Doc ID: {doc_id}")
    print("Fetching HTML content...")
    html_text = fetch_gdoc_html(doc_id)
    
    if not html_text:
        print("Error: Failed to retrieve content. Make sure the document link sharing is set to 'Anyone with the link' (public).")
        sys.exit(1)
        
    print("Converting to Markdown...")
    markdownify = ensure_markdownify()
    text = markdownify.markdownify(html_text, heading_style="ATX", escape_asterisks=False)
    
    # Clean BOM character globally, non-breaking spaces, and unescape underscores
    text = text.replace('\ufeff', '').replace('\xa0', ' ').replace(r'\_', '_')
    
    # Extract title from the first non-empty line to use as filename if not specified
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    output_filename = None
    if len(sys.argv) >= 3:
        output_filename = sys.argv[2]
        if not output_filename.endswith('.md'):
            output_filename += '.md'
    else:
        if lines:
            title = lines[0]
            # Strip markdown heading symbols if the user already formatted it as # Title
            title = title.lstrip('#').strip()
            output_filename = clean_filename(title) + ".md"
        else:
            output_filename = "imported_document.md"
            
    # Check if the title line in the text is formatted as # H1, if not add it
    if text.strip() and not text.strip().startswith('#'):
        # Find first non-empty line index and insert #
        raw_lines = text.split('\n')
        for i, line in enumerate(raw_lines):
            if line.strip():
                raw_lines[i] = f"# {line.strip()}"
                break
        text = '\n'.join(raw_lines)
        
    # Run formatting cleanups
    text = clean_google_redirects(text)
    text = format_citations(text)
    text = make_urls_clickable(text)
    text = format_reference_links(text)
        
    # Write to file
    with open(output_filename, 'w', encoding='utf-8') as f:
        f.write(text)
        
    print(f"Success! Document successfully imported and saved as:")
    print(f"  {os.path.abspath(output_filename)}")
    print(f"You can now run 'python build_html_md.py' to compile it.")

if __name__ == "__main__":
    main()
