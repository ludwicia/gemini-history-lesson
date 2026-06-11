with open("course/4.金璽詔書.md", "r", encoding="utf-8") as f:
    content = f.read()

# Find all headers like "# 金璽詔書", "Capitel", "CAP.", "章："
lines = content.split("\n")
output = []
for idx, line in enumerate(lines):
    if line.startswith("#") or "Capitel" in line or "CAP." in line or "章：" in line:
        output.append(f"Line {idx+1}: {line}")

with open("scratch/chapters_out.txt", "w", encoding="utf-8") as f_out:
    f_out.write("\n".join(output))

print("Done")
