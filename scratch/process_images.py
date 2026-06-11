import re
import base64
import os

def main():
    md_file = 'scratch/temp.md'
    out_dir = 'images'
    
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)
        
    with open(md_file, 'r', encoding='utf-8') as f:
        content = f.read()
        
    # Find all base64 images
    # Pattern: ![](data:image/png;base64,...)
    pattern = r'!\[\]\(data:image/png;base64,([a-zA-Z0-9+/=]+)\)'
    
    matches = re.findall(pattern, content)
    print(f"Found {len(matches)} base64 images.")
    
    for i, b64_str in enumerate(matches):
        img_data = base64.b64decode(b64_str)
        img_name = f"ad_calendar_eq_{i+1}.png"
        img_path = os.path.join(out_dir, img_name)
        
        with open(img_path, 'wb') as img_f:
            img_f.write(img_data)
        print(f"Saved {img_path}")
        
        # Replace in content
        target_str = f"![](data:image/png;base64,{b64_str})"
        replacement_str = f"![](images/{img_name})"
        content = content.replace(target_str, replacement_str)
        
    out_file = 'course/西元紀年的確立與演進：從歷史考證、政治妥協到全球數位化時間標準的建構.md'
    with open(out_file, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Saved updated markdown to {out_file}")

if __name__ == '__main__':
    main()
