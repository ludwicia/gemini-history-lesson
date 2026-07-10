import os
import json
import re
import build_html_md

def clean_html_tags(html_content):
    # Strip HTML tags
    text = re.sub(r'<[^>]+>', ' ', html_content)
    # Decode HTML entities
    text = text.replace('&nbsp;', ' ').replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&').replace('&quot;', '"')
    # Normalize spaces
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def main():
    print("\n=== Slicing Articles into Static JSON Chunks ===")
    
    # 1. Create api/ and api/article directories
    os.makedirs('api/article', exist_ok=True)
    print("[OK] Created 'api/article/' folder structures.")
    
    categories = build_html_md.categories
    pages_data = build_html_md.pages_data
    
    # 2. Compile articles catalog metadata (without content_html)
    articles_list = []
    for pid, data in pages_data.items():
        p_num = pid[4:] # e.g. "01" from "page01"
        file_var_name = f"file_p{int(p_num)}"
        file_path = getattr(build_html_md, file_var_name, None)
        last_updated = build_html_md.get_file_last_update_date(file_path) if file_path else ""
        
        category_key = ""
        for cat in categories:
            if pid in cat['pages']:
                category_key = cat['key']
                break
                
        articles_list.append({
            'id': pid,
            'title': data['title'],
            'ver': data['ver'],
            'last_updated': last_updated,
            'category': category_key,
            'img': data.get('img', ''),
            'bg_pos': data.get('bg_pos', 'center'),
            'is_doc': 1 if data.get('doc', False) else 0
        })
        
    # Map pages inside categories dynamically
    for cat in categories:
        cat['pages'] = [art['id'] for art in articles_list if art['category'] == cat['key']]
        
    catalog_json = {
        'categories': categories,
        'articles': articles_list,
        'worklog': getattr(build_html_md, 'worklog_html', '')
    }
    
    with open('api/articles.json', 'w', encoding='utf-8') as f:
        json.dump(catalog_json, f, ensure_ascii=False, indent=2)
    print("[OK] Successfully generated 'api/articles.json'")

    # 3. Compile individual articles detail page JSON chunks
    for pid, data in pages_data.items():
        p_num = pid[4:]
        body_var_name = f"html_body_p{int(p_num)}"
        body_html = getattr(build_html_md, body_var_name, "")
        
        file_var_name = f"file_p{int(p_num)}"
        file_path = getattr(build_html_md, file_var_name, None)
        last_updated = build_html_md.get_file_last_update_date(file_path) if file_path else ""
        
        category_key = ""
        for cat in categories:
            if pid in cat['pages']:
                category_key = cat['key']
                break
                
        article_detail = {
            'id': pid,
            'title': data['title'],
            'content_html': body_html,
            'ver': data['ver'],
            'last_updated': last_updated,
            'category': category_key,
            'img': data.get('img', ''),
            'is_doc': 1 if data.get('doc', False) else 0
        }
        
        with open(f'api/article/{pid}.json', 'w', encoding='utf-8') as f:
            json.dump(article_detail, f, ensure_ascii=False, indent=2)
            
    print(f"[OK] Successfully sliced and saved {len(pages_data)} article JSON chunks under 'api/article/'")

    # 4. Compile static search index file
    search_index = []
    print("[OK] Compiling static search index from article HTML paragraphs...")
    
    for pid, data in pages_data.items():
        p_num = pid[4:]
        body_var_name = f"html_body_p{int(p_num)}"
        body_html = getattr(build_html_md, body_var_name, "")
        
        # Match elements p, h2, h3, li, td
        matches = re.findall(r'<(p|h2|h3|li|td)(?:\s+[^>]*)?>(.*?)</\1>', body_html, re.DOTALL | re.IGNORECASE)
        
        for tag, inner_html in matches:
            plain_text = clean_html_tags(inner_html)
            if plain_text and len(plain_text) > 3:
                search_index.append({
                    'pageId': pid,
                    'text': plain_text
                })
                
    with open('api/search_index.json', 'w', encoding='utf-8') as f:
        json.dump(search_index, f, ensure_ascii=False)
        
    print(f"[OK] Search index created with {len(search_index)} searchable blocks (~{os.path.getsize('api/search_index.json')/1024:.1f} KB).")
    print("=== Compile Static Chunks Complete ===\n")

if __name__ == '__main__':
    main()
