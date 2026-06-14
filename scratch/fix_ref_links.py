import sys
import os
sys.path.append('course')
from import_gdoc import format_reference_links

def main():
    filepath = 'course/使徒信經的歷史演變與神學建構：從早期羅馬洗禮宣誓到西方大公信仰奠基的學術研究報告.md'
    with open(filepath, 'r', encoding='utf-8') as f:
        text = f.read()

    fixed_text = format_reference_links(text)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(fixed_text)

    print("Fixed bibliography reference links successfully!")

if __name__ == '__main__':
    main()
