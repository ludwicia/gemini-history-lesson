import re

file_path = 'build_html_md.py'

with open(file_path, 'r', encoding='utf-8') as f:
    code = f.read()

# The CSS block starts with <style> and ends with </style>
# We need to find it and extract it.
pattern = r'(    <style>\n.*?\n    </style>)'
match = re.search(pattern, code, flags=re.DOTALL)

if match:
    css_block = match.group(1)
    
    # Write CSS to style.css
    # Remove the surrounding <style> tags and unindent it a bit if possible, or just keep it as is.
    css_content = re.sub(r'^    <style>\n', '', css_block)
    css_content = re.sub(r'\n    </style>$', '', css_content)
    
    with open('style.css', 'w', encoding='utf-8') as f:
        f.write(css_content)
    print("Extracted CSS to style.css!")
    
    # Replace in build_html_md.py
    replacement = '    <link rel="stylesheet" href="style.css">'
    new_code = code.replace(css_block, replacement)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_code)
    print("Updated build_html_md.py!")
else:
    print("Could not find <style> block.")
