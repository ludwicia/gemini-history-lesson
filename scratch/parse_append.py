import re

input_path = r"C:\Users\USER\.gemini\antigravity\brain\f6c3b057-537b-4b9b-8f1c-679746ff23fe\.system_generated\steps\23\content.md"
output_path = r"scratch/formatted_chapters.md"

with open(input_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

blocks = []
in_glossary = False
glossary_lines = []

# Explanations mapping text
exp_non_appellando = """- **Privilegium de non appellando（不准上訴特權 / 司法獨立權）**：第十一章的核心精髓。此特權免除了選帝侯領地內子民被傳喚至帝國外部法庭受審的義務，且原則上禁止彼等向帝國最高法院提起上訴（除非面臨極端的「拒絕賦予正義」Justizverweigerung）。這確立了選帝侯在其領地內的最高司法主權。"""

exp_land_friede = """- **Land-Friede（地方和平 / 帝國公共和平）**：第十五章中提到的重要例外。在中世紀，皇帝會頒布「地方和平令」以限制私鬥。本詔書雖然嚴厲禁止城市 or 個人私自結盟，但如果是為了共同維護帝國法律所建立的「地方和平維護同盟」，則屬於合法。"""

exp_pfalburger = """- **Pfalburger / Pfahlbürger（外來市民 / 柵欄市民）**：第十六章的打擊對象。指那些實際上仍居住在封建諸侯領地或鄉村中、卻透過金錢或依附關係向附近的「帝國自由市」購買了市民權的農民或小貴族。他們以此逃避地方領主的租稅與司法管轄。查理四世在此明令禁止此種行為，以維護諸侯的封建基石。"""

exp_absagung = """- **Absagung（宣戰通知 / 私戰聲明）**：第十七章規範了中世紀德意志傳統的「私戰（Fehde）」。合法私戰不是暗殺，必須在開戰整整三天前（drey Tage）向對方送達正式的宣戰書並由可靠證人見證，否則將被視為可恥的背叛與謀殺。"""

exp_pertinentien = """- **Pertinentien / Pertinenz（法定附屬物 / 附屬權益）**：第二十章借用自羅馬法的法律術語。指在法律上與某一主體財產（此處指選帝侯領地）不可分割地綁定在一起的附屬權利、采邑、關稅或官職。"""

exp_gewehre = """- **Gewehre / Gewere（實際占有 / 權利控制）**：日耳曼法特有的核心物權概念。指領主對土地或某項特權（如選舉權）具備實質的、排他的、公眾認可的控制與享有狀態。"""

for line in lines:
    line_stripped = line.strip()
    if not line_stripped:
        continue
    
    # Check if we reached the glossary at the end
    if "歷史專有名詞與近代早期德語法律詞彙說明" in line_stripped or "歷史專有名詞" in line_stripped:
        in_glossary = True
        glossary_lines.append("### 歷史專有名詞與近代早期德語法律詞彙說明\n")
        continue
        
    if in_glossary:
        if line_stripped.startswith("*") or line_stripped.startswith("-"):
            item = line_stripped.lstrip("*- ").strip()
            glossary_lines.append(f"- {item}")
        else:
            glossary_lines.append(line_stripped)
        continue

    # Skip lines like "﻿收到你的內容了，以下是我的翻譯：" or chapter headers that are followed by "原文："
    if re.match(r"^第[一二三四五六七八九十]+章：", line_stripped):
        continue
        
    if line_stripped.startswith("原文："):
        parts = line_stripped.split("譯文：")
        original = parts[0].replace("原文：", "").strip()
        translated = parts[1].strip() if len(parts) > 1 else ""
        
        explanation = []
        
        # Check matching keywords to add explanations inline
        if "Mäyntz / Cölln oder Trier" in original and "§.1." in original:
            explanation.append(exp_non_appellando)
        if "Land-Frieden" in original:
            explanation.append(exp_land_friede)
        if "Pfalburger" in original and "§.1." in original:
            explanation.append(exp_pfalburger)
        if "Absagung" in original and "§.1." in original:
            explanation.append(exp_absagung)
        if "pertinentien" in original:
            explanation.append(exp_pertinentien)
        if "gewehr" in original:
            explanation.append(exp_gewehre)
            
        blocks.append({
            "original": original,
            "translated": translated,
            "explanation": "\n".join(explanation) if explanation else ""
        })

# Format the blocks into markdown matching course/4.金璽詔書.md
formatted_output = []
for block in blocks:
    formatted_output.append("---")
    formatted_output.append("")
    formatted_output.append("**原文**")
    formatted_output.append("")
    formatted_output.append(block["original"])
    formatted_output.append("")
    formatted_output.append("**譯文**")
    formatted_output.append("")
    formatted_output.append(block["translated"])
    formatted_output.append("")
    if block["explanation"]:
        formatted_output.append("**解釋**")
        formatted_output.append("")
        formatted_output.append(block["explanation"])
        formatted_output.append("")

# Append the glossary at the end as a full-width block
if glossary_lines:
    formatted_output.append("---")
    formatted_output.append("")
    formatted_output.extend(glossary_lines)
    formatted_output.append("")

with open(output_path, "w", encoding="utf-8") as f_out:
    f_out.write("\n".join(formatted_output))

print(f"Successfully formatted {len(blocks)} blocks and wrote to {output_path}")
print("Glossary lines count:", len(glossary_lines))
