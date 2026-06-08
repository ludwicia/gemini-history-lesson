import re

input_file = r"course/收到你的內容了，以下是我的翻譯：.md"
output_file = r"course/4.金璽詔書.md"

with open(input_file, 'r', encoding='utf-8') as f:
    lines = f.readlines()

blocks = []
current_block = {"original": [], "translated": [], "explanation": []}
state = None

for line in lines:
    line_stripped = line.strip()
    if line_stripped.startswith("原文："):
        if current_block["original"] or current_block["translated"]:
            blocks.append(current_block)
            current_block = {"original": [], "translated": [], "explanation": []}
        state = "original"
        current_block["original"].append(line_stripped[3:].strip())
    elif line_stripped.startswith("譯文："):
        state = "translated"
        current_block["translated"].append(line_stripped[3:].strip())
    elif line_stripped.startswith("### 歷史專有名詞"):
        state = "explanation"
    elif line_stripped.startswith("#") or line_stripped.startswith("## 第"):
        continue  # skip headers
    else:
        if state and line_stripped:
            current_block[state].append(line_stripped)
        elif state and not line_stripped:
            current_block[state].append("") # preserve empty lines if any

if current_block["original"] or current_block["translated"]:
    blocks.append(current_block)

# append to 4.金璽詔書.md
with open(output_file, 'a', encoding='utf-8') as f:
    for block in blocks:
        f.write("\n---\n\n")
        f.write("**原文**\n\n")
        f.write("\n".join(block["original"]).strip() + "\n\n")
        f.write("**譯文**\n\n")
        f.write("\n".join(block["translated"]).strip() + "\n\n")
        
        explanation_text = "\n".join(block["explanation"]).strip()
        if explanation_text:
            f.write("**解釋**\n\n")
            # The explanation list items might start with `* `, replace them with `- ` for consistency
            explanation_text = explanation_text.replace("* ", "- ")
            f.write(explanation_text + "\n\n")

print(f"Appended {len(blocks)} blocks to {output_file}")
