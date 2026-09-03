# -*- coding: utf-8 -*-
"""
Script to update characters_database.html with characters from characters_data.json
"""
import json
import re
import sys
import os

sys.stdout.reconfigure(encoding='utf-8')

def update_html():
    data_file = 'characters_data.json'
    html_file = 'characters_database.html'
    if not os.path.exists(data_file):
        print(f'Error: {data_file} not found!')
        return False

    with open(data_file, 'r', encoding='utf-8') as f:
        chars = json.load(f)

    with open(html_file, 'r', encoding='utf-8') as f:
        content = f.read()

    json_str = json.dumps(chars, ensure_ascii=False, indent=4)
    replacement = 'const rawCharacters = ' + json_str + ';'
    new_content, count = re.subn(
        r'const\s+rawCharacters\s*=\s*\[.*?\];',
        replacement,
        content,
        flags=re.DOTALL
    )
    if count == 0:
        print('Error: Could not find rawCharacters array in HTML!')
        return False

    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(new_content)

    print(f'Successfully updated {html_file} with {len(chars)} characters!')
    return True

if __name__ == '__main__':
    update_html()
