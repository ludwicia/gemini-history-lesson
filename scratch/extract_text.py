import re
from html import unescape

file_path = r"C:\Users\USER\.gemini\antigravity\brain\f6c3b057-537b-4b9b-8f1c-679746ff23fe\.system_generated\steps\6\content.md"

with open(file_path, "r", encoding="utf-8") as f:
    html_content = f.read()

# Let's search for text content. In Google Docs, text is often in script tags or inside span/p elements.
# If Google Docs returned the public view, it might have paragraphs <p class="..."><span>...</span></p>.
# Let's strip tags and see what we get, or look for specific markers.

def clean_html(raw_html):
    # Remove script and style tags
    cleanr = re.compile('<script[^>]*?>.*?</script>', re.DOTALL)
    cleantext = re.sub(cleanr, '', raw_html)
    cleanr = re.compile('<style[^>]*?>.*?</style>', re.DOTALL)
    cleantext = re.sub(cleanr, '', cleantext)
    
    # Replace paragraphs / list items with newlines
    cleantext = re.sub(r'</?(p|li|div|h1|h2|h3|h4|h5|h6)[^>]*?>', '\n', cleantext)
    
    # Strip all other HTML tags
    cleanr = re.compile('<[^>]*?>')
    cleantext = re.sub(cleanr, '', cleantext)
    
    return unescape(cleantext)

text = clean_html(html_content)

# Write to scratch file
output_path = r"c:\Users\USER\gemini的簡單歷史課\scratch\gdoc_text.txt"
with open(output_path, "w", encoding="utf-8") as f:
    f.write(text)

print("Text extracted successfully to", output_path)
