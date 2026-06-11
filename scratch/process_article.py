import os
import re
import base64
import shutil

# Paths
workspace_dir = r"c:\Users\USER\gemini的簡單歷史課"
input_md_path = os.path.join(workspace_dir, "帝國重塑、信仰博弈與權力終局：《米蘭敕令》時代的羅馬政治、君士坦丁宗教策略與李錫尼覆滅研究.md")
output_md_path = os.path.join(workspace_dir, "course", "帝國重塑、信仰博弈與權力終局：《米蘭敕令》時代的羅馬政治、君士坦丁宗教策略與李錫尼覆滅研究.md")
images_dir = os.path.join(workspace_dir, "images")
brain_dir = r"C:\Users\USER\.gemini\antigravity\brain\180997b5-74ef-4289-bdec-1c2a497f4c41"

def main():
    print("Reading markdown file...")
    with open(input_md_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Find base64 image pattern
    # Example: ![](data:image/png;base64,iVBORw0KGgo...)
    base64_pattern = r'!\[\]\(data:image/png;base64,([a-zA-Z0-9+/= \r\n\t]+)\)'
    match = re.search(base64_pattern, content)
    
    if match:
        print("Found base64 image. Decoding...")
        base64_data = match.group(1).replace(" ", "").replace("\r", "").replace("\n", "").replace("\t", "")
        img_bytes = base64.b64decode(base64_data)
        
        # Save image
        img_output_path = os.path.join(images_dir, "double_testimony_law.png")
        with open(img_output_path, 'wb') as img_f:
            img_f.write(img_bytes)
        print(f"Decoded image saved to: {img_output_path}")
        
        # Replace in markdown
        content = re.sub(base64_pattern, r'![雙重證人制度與主教聽審權](images/double_testimony_law.png)', content)
        print("Updated markdown content with local image link.")
    else:
        print("No base64 image found.")

    # Save the updated markdown in the course directory
    os.makedirs(os.path.dirname(output_md_path), exist_ok=True)
    with open(output_md_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Saved updated markdown to: {output_md_path}")

    # Remove the original file from root
    if os.path.exists(input_md_path):
        os.remove(input_md_path)
        print("Removed original markdown file from root.")

    # Copy the generated illustrations
    illustrations = {
        "milan_edict_main": "milan_edict_main.png",
        "forty_martyrs_sebaste": "forty_martyrs_sebaste.png",
        "battle_adrianople": "battle_adrianople.png"
    }

    for key, filename in illustrations.items():
        # Find matching generated files in brain directory
        matched_file = None
        for f in os.listdir(brain_dir):
            if f.startswith(key) and f.endswith(".png"):
                matched_file = os.path.join(brain_dir, f)
                break
        
        if matched_file:
            dest_path = os.path.join(images_dir, filename)
            shutil.copy(matched_file, dest_path)
            print(f"Copied {matched_file} -> {dest_path}")
        else:
            print(f"Warning: Could not find generated file for {key} in brain directory.")

if __name__ == "__main__":
    main()
