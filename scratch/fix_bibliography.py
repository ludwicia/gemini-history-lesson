import re

file_path = r"c:\Users\USER\gemini的簡單歷史課\course\中世紀巡行王權的權力運作、制度體系與社會實態：以奧圖一世九五五年巡行與戰事為核心之歷史學考察.md"

with open(file_path, "r", encoding="utf-8") as f:
    text = f.read()

# Find the references section
parts = text.split("#### 引用的著作\n")
if len(parts) == 2:
    header = parts[0] + "#### 引用的著作\n\n"
    bib = parts[1].strip()
    
    # Replace N. with newline N.
    # We match spaces, a number, a period, and another space/link.
    # e.g., ' 2. ' -> '\n2. '
    formatted_bib = re.sub(r'\s+(\d+\.)\s+', r'\n\1 ', bib)
    
    # Save back
    new_text = header + formatted_bib + "\n"
    with open(file_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(new_text)
    print("Successfully formatted bibliography!")
else:
    print("Could not find bibliography section header.")
