import re

file_path = r'c:\Users\USER\gemini的簡單歷史課\course\聖職與婚娶：基督宗教神職人員生育、婚姻與財產繼承的歷史演變與政權博弈.md'

with open(file_path, 'r', encoding='utf-8') as f:
    text = f.read()

# Pattern: match "number. Title, [URL](URL)"
# \d+\.\s+ -> Group 1: list number and space
# (.*?) -> Group 2: The title
# ,\s* -> comma and optional space
# \[(https?://[^\]]+)\]\(\3\) -> The URL as markdown link
pattern = r'(\d+\.\s+)(.*?),\s*\[(https?://[^\]]+)\]\(\3\)'

new_text = re.sub(pattern, r'\1[\2](\3)', text)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(new_text)

print("References formatted successfully!")
