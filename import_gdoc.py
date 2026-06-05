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

def fetch_gdoc_text(doc_id):
    export_url = f"https://docs.google.com/document/d/{doc_id}/export?format=txt"
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
    # Look for H2/H3 headings that contain "引用的著作", "引用來源", "參考文獻", "參考資料", "bibliography", or "references".
    bib_pattern = r'(\r?\n##+\s+(?:引記的著作|引用的著作|引用來源|參考文獻|參考資料|Bibliography|References)\s*\r?\n)'
    parts = re.split(bib_pattern, text, maxsplit=1, flags=re.IGNORECASE)
    
    if len(parts) == 3:
        body = parts[0]
        bib = parts[1] + parts[2]
    else:
        body = text
        bib = ""
        
    # Pattern for citation numbers: 1-2 digits
    # Preceded by Chinese characters, letters, closing brackets, or asterisks
    # Followed by punctuation (。，；、』」）), space, pipe (|), or end of line/cell
    pattern = r'(?<=[\u4e00-\u9fff》）』」a-zA-Z*])(\d{1,2})(?=[\s。，；、』」）|]|$)'
    body_replaced = re.sub(pattern, r"<sup>[\1]</sup>", body)
    
    return body_replaced + bib

def fix_table_margins(text):
    lines = text.split('\n')
    new_lines = []
    in_table = False
    
    for line in lines:
        stripped = line.strip()
        # A markdown table row starts and ends with '|' and contains columns
        is_table_row = stripped.startswith('|') and stripped.endswith('|') and len(stripped) > 1
        
        if is_table_row:
            in_table = True
        elif in_table:
            # We just exited a table. If the current line is not empty, add a blank line.
            if stripped != "":
                new_lines.append("")
            in_table = False
            
        new_lines.append(line)
        
    return '\n'.join(new_lines)

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
    print("Fetching content...")
    text = fetch_gdoc_text(doc_id)
    
    if not text:
        print("Error: Failed to retrieve content. Make sure the document link sharing is set to 'Anyone with the link' (public).")
        sys.exit(1)
        
    # Clean BOM character globally
    text = text.replace('\ufeff', '')
    
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
    text = format_citations(text)
    text = fix_table_margins(text)
        
    # Write to file
    with open(output_filename, 'w', encoding='utf-8') as f:
        f.write(text)
        
    print(f"Success! Document successfully imported and saved as:")
    print(f"  {os.path.abspath(output_filename)}")
    print(f"You can now run 'python build_html_md.py' to compile it.")

if __name__ == "__main__":
    main()
