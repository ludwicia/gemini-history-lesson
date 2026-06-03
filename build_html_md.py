import markdown
import re
import os
import subprocess
from datetime import datetime

# Helper to get the last update date of a file from Git or filesystem
def get_file_last_update_date(file_path):
    try:
        res = subprocess.run(
            ['git', 'log', '-1', '--format=%ad', '--date=format:%Y-%m-%d', file_path],
            capture_output=True, text=True, check=True
        )
        date_str = res.stdout.strip()
        if date_str:
            # Check if file has unstaged or staged changes
            diff_res = subprocess.run(['git', 'diff', '--quiet', file_path])
            if diff_res.returncode == 0:
                diff_staged = subprocess.run(['git', 'diff', '--cached', '--quiet', file_path])
                if diff_staged.returncode == 0:
                    return date_str
    except Exception:
        pass

    try:
        mtime = os.path.getmtime(file_path)
        return datetime.fromtimestamp(mtime).strftime('%Y-%m-%d')
    except Exception:
        return datetime.now().strftime('%Y-%m-%d')

# Helper to process and format a markdown lesson
def process_markdown(file_path, image_replacements, content_version, main_img_html=None):
    update_date = get_file_last_update_date(file_path)
    with open(file_path, 'r', encoding='utf-8') as f:
        text = f.read()

    # Clean Voyager/Gemini footer source info if present
    text = text.split('Source: https://gemini')[0].strip(' -\n')

    # Preprocess markdown to fix MS Word style paragraph breaks (single newlines)
    lines = text.split('\n')
    new_lines = []
    for i, line in enumerate(lines):
        new_lines.append(line)
        if i < len(lines) - 1:
            next_line = lines[i+1]
            if line.strip() and next_line.strip():
                # If neither line is a list item, table row, or heading
                if not re.match(r'^[\-\*\#\|]', line.lstrip()) and not re.match(r'^\d+\.', line.lstrip()):
                    if not re.match(r'^[\-\*\#\|]', next_line.lstrip()) and not re.match(r'^\d+\.', next_line.lstrip()):
                        new_lines.append('')

    text = '\n'.join(new_lines)
    html_body = markdown.markdown(text, extensions=['tables', 'toc'])

    # Add content version badge and update date badge
    version_badge = f'<div style="text-align: center; color: #718096; margin-top: -15px; margin-bottom: 25px; font-size: 0.95rem; font-weight: 600; display: flex; align-items: center; justify-content: center; gap: 8px;"><span style="background-color: #ebf8ff; color: #2b6cb0; padding: 3px 8px; border-radius: 4px; font-size: 0.8rem; border: 1px solid #bee3f8;">內容版本：{content_version}</span><span style="background-color: #f0fff4; color: #38a169; padding: 3px 8px; border-radius: 4px; font-size: 0.8rem; border: 1px solid #c6f6d5;">最近更新：{update_date}</span></div>\n'

    # Insert version badge and main image under first H1
    header_insert = version_badge
    if main_img_html:
        header_insert += main_img_html

    html_body = re.sub(r'(<h1.*?>.*?</h1>)', r'\1\n' + header_insert, html_body, count=1)

    # Substitute specific headings with images for high-end text wrap
    for pattern, url, caption in image_replacements:
        img_html = f'\n<figure class="image-left"><img src="{url}" alt="{caption}" loading="lazy"><figcaption class="caption">{caption}</figcaption></figure>\n'
        html_body = re.sub(pattern, r'\1' + img_html, html_body, count=1)

    return html_body

def process_3col_document(file_path, content_version):
    update_date = get_file_last_update_date(file_path)
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
    except Exception as e:
        return f"<p>Error loading document: {e}</p>"

    blocks = [b.strip() for b in text.split('---') if b.strip()]
    if not blocks:
        return ""
        
    title_block = blocks[0]
    # Clean up double title if present
    lines = title_block.split('\n')
    cleaned_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped == "金璽詔書(德)" and not stripped.startswith('#'):
            continue # skip the redundant plain first line
        cleaned_lines.append(line)
    cleaned_title_block = '\n'.join(cleaned_lines)
    
    title_html = markdown.markdown(cleaned_title_block)
    
    html = f'''
    <div style="text-align: center; color: #718096; margin-top: 10px; margin-bottom: 10px; font-size: 0.95rem; font-weight: 600; display: flex; align-items: center; justify-content: center; gap: 8px;">
        <span style="background-color: #ebf8ff; color: #2b6cb0; padding: 3px 8px; border-radius: 4px; font-size: 0.8rem; border: 1px solid #bee3f8;">內容版本：{content_version}</span>
        <span style="background-color: #f0fff4; color: #38a169; padding: 3px 8px; border-radius: 4px; font-size: 0.8rem; border: 1px solid #c6f6d5;">最近更新：{update_date}</span>
    </div>
    <div class="doc-title-section">
        {title_html}
    </div>
    <div class="doc-3col-container">
        <div class="doc-3col-header">
            <div class="doc-col-title">原文 (德文)</div>
            <div class="doc-col-title">譯文 (中文)</div>
            <div class="doc-col-title">解釋 (筆記)</div>
        </div>
    '''
    
    for block in blocks[1:]:
        block = block.strip()
        if not block: continue
        
        if "**原文**" in block and "**譯文**" in block:
            parts = block.split("**譯文**")
            original_part = parts[0].replace("**原文**", "").strip()
            
            # Check if there is an **解釋** block
            if "**解釋**" in parts[1]:
                sub_parts = parts[1].split("**解釋**")
                translated_part = sub_parts[0].strip()
                explanation_part = sub_parts[1].strip()
            else:
                translated_part = parts[1].strip()
                explanation_part = ""
            
            original_text = markdown.markdown(original_part)
            translated_text = markdown.markdown(translated_part)
            explanation_text = markdown.markdown(explanation_part) if explanation_part else ""
            
            html += f'''
            <div class="doc-3col-row">
                <div class="doc-col doc-original">{original_text}</div>
                <div class="doc-col doc-translation">{translated_text}</div>
                <div class="doc-col doc-explanation">{explanation_text}</div>
            </div>
            '''
        else:
            html += f'''
            <div class="doc-3col-row full-width-row" style="grid-template-columns: 1fr;">
                <div class="doc-col" style="grid-column: 1 / -1;">{markdown.markdown(block)}</div>
            </div>
            '''
            
    html += "</div>"
    return html

# Page 1 (Holland) Config
file_p1 = r'帝國海洋、金融先驅與當代政治僵局：荷蘭建國史、東印度公司興衰與當代地緣政經轉型研究報告.md'
map_p1 = '<figure class="image-left" style="width: 38%; margin-bottom: 20px;"><img src="images/img_12_960px-Seven_United_Netherlands_Janssonius_1658.jpg" alt="1658 Map" loading="lazy"><figcaption class="caption">1658年聯省共和國地圖，清晰可見當時的須德海與低地國錯綜複雜的水路地貌</figcaption></figure>\n'
images_p1 = [
    (r'(<h2.*?>1\..*?</h2>)', 'images/img_00_Map_of_Seventeen_Provinces_of_Low_German.jpg', '十六世紀的低地十七省地圖，描繪了當時受哈布斯堡王朝統治的疆域'),
    (r'(<h2.*?>2\..*?</h2>)', 'images/img_16_960px-Flag_of_the_Dutch_East_India_Company.svg.png', '荷蘭東印度公司（VOC）旗幟，象徵金融革命與全球貿易擴張'),
    (r'(<h2.*?>3\..*?</h2>)', 'images/img_14_960px-Fort_Zeelandia__Anping_District__T.jpg', '荷蘭統治台灣時期的熱蘭遮城 (Fort Zeelandia)'),
    (r'(<h2.*?>4\..*?</h2>)', 'images/img_15_960px-La_ronda_de_noche__por_Rembrandt_v.jpg', '林布蘭名作《夜巡》，荷蘭黃金時代藝術巔峰'),
    (r'(<h2.*?>5\..*?</h2>)', 'images/img_03_960px-Joannes_van_Deutecum_-_Leo_Belgicu.jpg', '低地國家的獅子地圖 (Leo Belgicus)，象徵早期與神聖羅馬帝國的地緣淵源'),
    (r'(<h2.*?>6\..*?</h2>)', 'images/img_08_960px-Sint_Eustatius_from_ISS.jpg', '聖尤斯特歇斯島，美國獨立戰爭期間最重要的軍火走私樞紐'),
    (r'(<h2.*?>7\..*?</h2>)', 'images/img_07_960px-Johan_Heinrich_Neuman_-_Johan_Rudo.jpg', '約翰·魯道夫·托爾貝克（1848年憲法起草者，荷蘭民主奠基人）'),
    (r'(<h2.*?>8\..*?</h2>)', 'images/img_05_960px-Bundesarchiv_Bild_146-2005-0003__R.jpg', '1940年遭德軍殘酷轟炸摧毀的鹿特丹'),
    (r'(<h2.*?>9\..*?</h2>)', 'images/img_09_960px-Friedenspalast_Den_Haag__100MP_.jpg', '位於海牙的和平宮，象徵當代荷蘭作為全球國際司法之都'),
    (r'(<h2.*?>10\..*?</h2>)', 'images/img_01_960px-Den_Haag_Binnenhof_02.jpg', '荷蘭國會大廈 (Binnenhof)，象徵高度協商與妥協的政治文化')
]

# Page 2 (USA) Config
file_p2 = r'第一階段：三個世界的交會與前哥倫布時期的美洲（1607年以前）.md'
map_p2 = '<figure class="image-left" style="width: 38%; margin-bottom: 20px;"><img src="images/img_10_960px-Cahokia_Monks_Mound.jpg" alt="Cahokia Mounds" loading="lazy"><figcaption class="caption">卡霍基亞莫恩克斯土丘（Monks Mound）遠眺，前哥倫布時期繁榮的密西西比河流域社會核心遺跡</figcaption></figure>\n'
images_p2 = [
    (r'(<h2.*?>一、.*?</h2>)', 'images/img_04_Cliff_Palace_-_Mesa_Verde_National_Park.jpg', '梅薩維德國家公園的懸崖宮殿，展現普韋布洛人高超的石造建築技術'),
    (r'(<h2.*?>二、.*?</h2>)', 'images/img_06_Caravela_Redonda.jpg', '大航海時代的葡萄牙輕快帆船（Caravel），支撐起遠洋探索的技術革命'),
    (r'(<h2.*?>三、.*?</h2>)', 'images/img_02_Landing_of_Columbus.jpg', '哥倫布登陸美洲想像圖，開啟了改變全球生態與人類社會結構的哥倫布大交換'),
    (r'(<h3.*?>2\..*?</h3>)', 'images/img_17_960px-Castillo_de_San_Marcos_Fort_Panorama.jpg', '位於佛羅里達的聖馬科斯城堡，北美洲最古老的歐洲磚石要塞，象徵西班牙的早期霸權'),
    (r'(<h3.*?>3\..*?</h3>)', 'images/img_11_John_White_-_La_Virginea_Pars__map_of_th.jpg', '約翰·懷特約於1585年繪製的北美海岸地圖《La Virginea Pars》，記錄了早期對北美地理的探索與拓荒'),
    (r'(<h3.*?>4\..*?</h3>)', 'images/img_13_960px-Elizabeth_I__Armada_Portrait_.jpg', '伊麗莎白一世著名的「無敵艦隊畫像」（Armada Portrait），象徵擊敗西班牙霸權的地緣政治重大轉折點')
]

# Page 3 (Hussite Wars) Config
file_p3 = r'信仰衝突、軍事變革與波希米亞國家認同：胡斯戰爭的歷史脈絡、演進特徵與深遠影響研究報告.md'
map_p3 = '<figure class="image-left" style="width: 38%; margin-bottom: 20px;"><img src="images/hussite_wars_main.png" alt="Hussite Wars" loading="lazy"><figcaption class="caption">捷克歷史藝術家 Luděk Marold 著名巨作《利帕尼戰役全景圖》（Maroldovo panorama bitvy u Lipan），生動重現了這場終結激進派的史詩決戰</figcaption></figure>\n'
images_p3 = [
    (r'(<h2.*?>一、.*?</h2>)', 'images/jan_hus_preaching.png', '1563年布拉格印製的《胡斯講道集》（Postilla）中極具歷史意義的木刻版畫，記錄了揚·胡斯向波希米亞平民大眾宣教的經典場景'),
    (r'(<\/p>\s*<p>1414年，神聖羅馬帝國國王西吉斯蒙德)', 'images/jan_hus_execution.jpg', '歷史文獻插圖：上方描繪揚·胡斯在康斯坦茨被戴上寫有「異端首領」主教冠押赴火刑，下方描繪信徒用手推車收集其骨灰撒入萊茵河以防遺骨成為聖物，出自著名的《康斯坦茨公會議編年史》（Chronik des Konstanzer Konzils）'),
    (r'(<h2.*?>三、.*?</h2>)', 'images/hussite_crusade_battle.png', '源自15世紀末捷克國寶級手稿《耶拿法典》（Jena Codex）的著名插圖，展現高舉聖杯紅旗前仆後繼、行軍禦敵的胡斯派戰士們'),
    (r'(<h2.*?>四、.*?</h2>)', 'images/hussite_wagenburg.png', '歷史文獻中記載的經典「戰車壘」（Wagenburg）野戰工事與早期火炮協同防禦防線的精細還原圖')
]

# Page 5 (Hirsau Abbey) Config
file_p5 = r'希爾紹修道院研究報告：雙軌解析.md'
map_p5 = '<figure class="image-left" style="width: 38%; margin-bottom: 20px;"><img src="images/hirsau_main_wilhelm.jpg" alt="Wilhelm von Hirsau" loading="lazy"><figcaption class="caption">威廉大院長肖像，十一世紀下半葉領導希爾紹修道院走向改革黃金時代的靈魂人物</figcaption></figure>\n'
images_p5 = [
    (r'(<h3.*?>十一世紀前夕的教會亂象與世俗糾葛</h3>)', 'images/hirsau_st_aurelius.jpg', '聖奧雷利烏斯教堂外觀，見證了十世紀中葉由教宗良九世指示、卡爾夫伯爵阿達爾貝特主導的第二次重建歷史'),
    (r'(<h3.*?>爭取絕對獨立與教宗的豁免特權</h3>)', 'images/hirsau_interior_historical.jpg', '聖奧雷利烏斯教堂歷史剖面圖，描繪了在敘任權之爭爆發前夕，希爾紹修道院所呈現的經典早期羅馬式空間佈局'),
    (r'(<h3.*?>九年戰爭與梅拉克將軍的焦土政策</h3>)', 'images/hirsau_ruins_overview.jpg', '今日希爾紹修道院（聖彼得與保羅修道院）宏偉的廢墟全景，1692年九年戰爭中遭法國將軍梅拉克的焦土政策付之一炬'),
    (r'(<h3.*?>報告二：文化、建築與藝術的深遠遺產</h3>)', 'images/hirsau_bausubstanz_map.jpg', '希爾紹修道院大教堂建築年代與地基結構分佈圖，完美體現了威廉大院長將幾何比例與宇宙秩序無縫轉化為石造空間的卓越才華'),
    (r'(<h2.*?>第二章：「希爾紹建築學派」的羅馬式巔峰</h2>)', 'images/hirsau_cubic_capitals.jpg', '聖奧雷利烏斯教堂內的羅馬式骰子柱頭，其上帶有希爾紹建築學派極具代表性的「希爾紹鼻」角狀突起特徵'),
    (r'(<h3.*?>神學隱喻與核心特徵</h3>)', 'images/hirsau_interior_gesims.jpg', '聖奧雷利烏斯教堂内牆的羅馬式石雕橫飾帶（Gesims），呈現出精確的幾何對稱與極簡紋飾，完美契合克呂尼改革倡導的禁慾美學'),
    (r'(<h3.*?>建築學派的廣泛傳播與後期演變</h3>)', 'images/hirsau_kreuzgang.jpg', '聖彼得與保羅修道院的雙層迴廊（Kreuzgang），其結構佈局緊密圍繞中殿，反映了修道院空間為數百名修士的日常靈修與盛大禮拜儀式所做的精密規劃'),
    (r'(<h2.*?>第三章：文藝復興狩獵小屋的興建：權力的世俗化展示</h2>)', 'images/hirsau_hunting_lodge.jpg', '文藝復興式狩獵小屋與門塔廢墟，由符騰堡公爵在16世紀末建造，展現了世俗新教權力對前天主教修道院教產的接管與主權宣示'),
    (r'(<h3.*?>宗教空間的修復與現代藝術</h3>)', 'images/hirsau_modern_madonna.jpg', '修復後的聖奧雷利烏斯教堂內部，將古老的木雕聖母像與現代空間元素並置，展現了戰後廢墟中宗教空間與現代藝術完美交融的重生魅力')
]

# Page 7 (Ottonian System) Config
file_p7 = r'奧托-薩利安帝國教會體制.md'
map_p7 = '<figure class="image-left" style="width: 38%; margin-bottom: 20px;"><img src="images/ottonian_hre_map.svg" alt="Ottonian HRE Map" loading="lazy"><figcaption class="caption">西元1000年左右奧托-薩利安王朝時期的神聖羅馬帝國地圖，呈現德意志各部落公爵領與主教區錯綜複雜的疆域分佈</figcaption></figure>\n'
images_p7 = [
    (r'(<h2.*?>關鍵歷史人物與王權的神聖化重塑</h2>)', 'images/ottonian_otto1.jpg', '德國馬格德堡著名雕塑《馬格德堡騎馬人》（Magdeburger Reiter），生動展現了神聖羅馬帝國皇帝奧托一世的威嚴之姿'),
    (r'(<p>在奧托一世的統治後期，其胞弟科隆大主教布魯諾)', 'images/ottonian_bruno.jpg', '科隆聖潘塔萊翁修道院大教堂外的布魯諾大主教雕像，他將教會改革、宮廷教堂人才培養與國家行政體系進行了深度的歷史性融合'),
    (r'(<h3.*?>巡迴朝廷與空間動態治理</h3>)', 'images/ottonian_goslar.jpg', '宏偉的戈斯拉爾帝國皇室行宮（Kaiserpfalz Goslar），由皇帝亨利三世建造，是薩利安王朝巡迴朝廷與政治中樞的核心後勤與行政基地之一'),
    (r'(<h2.*?>內部矛盾：政教合一的內耗與改革運動的興起</h2>)', 'images/ottonian_canossa.jpg', '德國歷史畫家 Eduard Schwoiser 經典油畫巨作《亨利前進卡諾莎》（Heinrich vor Canossa），生動再現了皇帝亨利四世向教宗格列高利七世低頭乞求赦免的史詩場景')
]

# Page 8 (Concordat of Worms) Config
file_p8 = r'沃姆斯協約.md'

# Page 9 (Pippin's Donation) Config
file_p9 = r'丕平獻土的地緣政治體系研究：背景、權力機制、法理偽造與深遠歷史影響.md'
map_p9 = '<figure class="image-left" style="width: 38%; margin-bottom: 20px;"><img src="images/pippin_donation_main.jpg" alt="Pippin Coronation Main" loading="lazy"><figcaption class="caption">法國畫家 François Dubois 於1837年所繪的名作《教宗斯德望二世在聖但尼修道院為丕平加冕》，現藏於凡爾賽宮。</figcaption></figure>\n'
images_p9 = [
    (r'(<h2.*?>三、.*?</h2>)', 'images/pippin_donation_map.png', '西元750年代倫巴底擴張前夕的義大利半島地緣版圖。丕平獻土徹底打破了拜占庭、倫巴底與羅馬聖座之間的三方平衡。'),
    (r'(<h2.*?>五、.*?</h2>)', 'images/pippin_ricci_fresco.jpg', '梵蒂岡祕密檔案館壁畫：描繪法蘭克聖但尼修道院院長富拉德代表國王丕平，實地向教宗斯德望二世呈交收復的22座城市鑰匙與獻土詔書。'),
    (r'(<h2.*?>四、.*?</h2>)', 'images/donation_of_constantine.jpg', '梵蒂岡拉斐爾畫室著名濕壁畫《君士坦丁的贈禮》（Donation of Constantine），描繪君士坦丁大帝將世俗統治權讓渡給教宗西爾維斯特一世。')
]

# Page 10 (Carolingian Education) Config
file_p10 = r'聖神統治與知識復興：卡洛林王朝教育基建、制度體系及其深遠歷史遺產之研究.md'
map_p10 = '<figure class="image-left" style="width: 38%; margin-bottom: 20px;"><img src="images/carolingian_main.jpg" alt="Carolingian Minuscule" loading="lazy"><figcaption class="caption">八世紀末《達古爾夫詩篇》（Dagulf Psalter）之手抄頁面，以優美典雅的卡洛林小寫體金字書寫，展現了早期帝國書寫標準化的極致美學。</figcaption></figure>\n'
images_p10 = [
    (r'(<h2.*?>一、.*?</h2>)', 'images/carolingian_alcuin.jpg', 'Jean-Victor Schnetz 1830年名作《查理曼與阿爾琴》，描繪校長阿爾琴向查理曼大帝及其高級廷臣展示由修士手抄之聖經文獻，象徵神聖王權與知識基建之交匯。'),
    (r'(<h2.*?>二、.*?</h2>)', 'images/carolingian_stgall.jpg', '公元九世紀初著名的《聖加侖修道院理想平面圖》（St. Galler Klosterplan）局部，圖中明確規劃了專屬的圖書館（Library）與手抄室（Scriptorium）空間，展現出高度系統化的學術基建思維。'),
    (r'(<h2.*?>三、.*?</h2>)', 'images/carolingian_lorsch.jpg', '著名的卡洛林晚期傑作——洛爾施修道院門樓（Königshalle），是極少數完整存世的卡洛林帝國時期地標建築，展現了早期文藝復興的建築工程美學與古典柱頭裝飾。'),
    (r'(<h2.*?>四、.*?</h2>)', 'images/carolingian_majesty.jpg', '現藏於維多利亞與阿爾伯特博物館的十一世紀早期《洛爾施福音書》（Lorsch Gospels）象牙浮雕封面，描繪「基督登基在天」（Christ in Majesty），象徵宗教神權與卡洛林神學宇宙秩序的高度統一。')
]

# Page 11 (European Papermaking) Config
file_p11 = r'歐洲造紙術的歷史演變、技術革新與物質文明變革研究報告.md'
map_p11 = '<figure class="image-left" style="width: 38%; margin-bottom: 20px;"><img src="images/paper_main.jpg" alt="Jost Amman Papermaker" loading="lazy"><figcaption class="caption">德意志著名藝術家 Jost Amman 於1568年繪製的經典木刻版畫《撈紙工》（Der Papiermacher），生動再現了前工業化時期歐洲水力造紙坊抄紙與壓榨水分的勞動場景。</figcaption></figure>\n'
images_p11 = [
    (r'(<h2.*?>二、.*?</h2>)', 'images/paper_hollander.jpg', '保存於造紙歷史博物館中的經典「荷蘭式打漿機」（Hollander Beater），其藉由旋轉金屬刀片進行碎布纖維的原纖化處理，徹底革新了沿用數百年的槌擊製漿工藝。'),
    (r'(<h2.*?>四、.*?</h2>)', 'images/paper_press.jpg', '近代早期典型的木製手搖印刷機與造紙槽協同車間，造紙與印刷兩大技術的物質相遇，徹底打破了中古教權對知識產權與書籍生產的絕對壟斷。'),
    (r'(<h3.*?>2\..*?</h3>)', 'images/paper_gutenberg.jpg', '紐約公共圖書館珍藏的1455年《古騰堡聖經》（Gutenberg Bible）雙欄手繪頁面，採用了歐洲本土製造的高規格破布手抄紙，為印刷資本主義的擴張提供了最為關鍵的物質載體。')
]

# Page 12 (Catharism) Config
file_p12 = r'靈魂的物質禁錮與中世紀權力整肅：卡特里派的興起、神學教義、十字軍聖戰與歷史餘音.md'
map_p12 = '<figure class="image-left" style="width: 38%; margin-bottom: 20px;"><img src="images/catharism_main.jpg" alt="Montsegur Castle" loading="lazy"><figcaption class="caption">今日聳立於南法陡峭岩峰上的蒙塞居爾城堡（Château de Montségur）廢墟，曾是卡特里派最後的軍事與精神堡壘，見證了1244年悲壯的圍城戰與大火刑。</figcaption></figure>\n'
images_p12 = [
    (r'(<h2.*?>二、.*?</h2>)', 'images/catharism_creed.png', '代表朗格多克文化與卡特里派信仰空間的「奧克十字」（Occitan Cross）標誌，象徵南方反抗北法集權與教權威脅的文化精神'),
    (r'(<h2.*?>四、.*?</h2>)', 'images/catharism_perfecti.jpg', '西班牙畫家 Pedro Berruguete 於15世紀末所繪名作《聖多明尼克與阿爾比派》（St Dominic and the Albigenses），描繪正統與異端書籍被投入火中檢驗真偽的傳奇場景'),
    (r'(<h2.*?>五、.*?</h2>)', 'images/catharism_crusade.jpg', '15世紀手稿《Boucicaut大師工坊》插圖，描繪阿爾比十字軍東征期間卡特里派信徒被驅逐出城的悲慘場景'),
    (r'(<h2.*?>六、.*?</h2>)', 'images/catharism_inquisition.jpg', '14世紀道明會士 Bernard Gui 所著《異端裁判所實踐指南》（Practica officii inquisitionis heretice pravitatis）手稿插圖，象徵宗教裁判所官僚化、秘密化的司法清洗')
]

print("Processing Page 1 (Holland)...")
html_body_p1 = process_markdown(file_p1, images_p1, "1.1", map_p1)

print("Processing Page 2 (USA)...")
html_body_p2 = process_markdown(file_p2, images_p2, "1.0", map_p2)

print("Processing Page 3 (Hussite)...")
html_body_p3 = process_markdown(file_p3, images_p3, "1.0", map_p3)

print("Processing Page 4 (Golden Bull)...")
file_p4 = r'4.金璽詔書.md'
html_body_p4 = process_3col_document(file_p4, "1.5")

print("Processing Page 5 (Hirsau Abbey)...")
html_body_p5 = process_markdown(file_p5, images_p5, "1.0", map_p5)

print("Processing Page 6 (Benedict Rule)...")
file_p6 = r'5.聖本篤會規.md'
html_body_p6 = process_3col_document(file_p6, "2.0")

print("Processing Page 7 (Ottonian System)...")
html_body_p7 = process_markdown(file_p7, images_p7, "1.0", map_p7)

print("Processing Page 8 (Concordat of Worms)...")
html_body_p8 = process_3col_document(file_p8, "1.0")

print("Processing Page 9 (Pippin Donation)...")
html_body_p9 = process_markdown(file_p9, images_p9, "1.0", map_p9)

print("Processing Page 10 (Carolingian Education)...")
html_body_p10 = process_markdown(file_p10, images_p10, "1.0", map_p10)

print("Processing Page 11 (European Papermaking)...")
html_body_p11 = process_markdown(file_p11, images_p11, "1.0", map_p11)

print("Processing Page 12 (Cathar Crusade)...")
html_body_p12 = process_markdown(file_p12, images_p12, "1.0", map_p12)

# Full Portal HTML Template
portal_template = """<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="google-site-verification" content="lueGudczLbvVhtRPh-JU6w8b3eu_yu5XCguU6RvfMxY" />
    <title>Ludwica 的簡單歷史課 — 荷蘭建國史、胡斯戰爭、金璽詔書、聖本篤會規等歷史專題研究</title>
    <meta name="description" content="Ludwica 的簡單歷史課：涵蓋荷蘭建國史與東印度公司、前哥倫布時期美洲、胡斯戰爭、金璽詔書德中對照、希爾紹修道院、聖本篤會規三欄解析、奧托-薩利安帝國教會體制。專為深度歷史專題研究打造的學術級長文網站。">
    <meta name="keywords" content="歷史, 歷史課, 荷蘭史, 東印度公司, 美國史, 前哥倫布時期, 宗教戰爭, 胡斯戰爭, 揚胡斯, 捷克歷史, 大航海時代, 金璽詔書, 神聖羅馬帝國, 選帝侯, 希爾紹修道院, 克呂尼改革, 聖本篤會規, 修道院制度, 奧托王朝, 薩利安王朝, 帝國教會體制, 敘任權之爭, Ludwica, 歷史專題">
    <link rel="canonical" href="https://ludwicia.github.io/ludwica-history-lesson/">
    <meta property="og:title" content="Ludwica 的簡單歷史課 — 荷蘭建國史、胡斯戰爭、金璽詔書、聖本篤會規等歷史專題研究">
    <meta property="og:description" content="涵蓋荷蘭建國史與東印度公司、前哥倫布時期美洲、胡斯戰爭、金璽詔書德中對照、希爾紹修道院、聖本篤會規三欄解析、奧托-薩利安帝國教會體制。專為深度歷史專題研究打造的學術級長文網站。">
    <meta property="og:type" content="website">
    <meta property="og:url" content="https://ludwicia.github.io/ludwica-history-lesson/">
    <meta property="og:image" content="https://ludwicia.github.io/ludwica-history-lesson/history_banner_bg.png">
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="Ludwica 的簡單歷史課 — 歷史專題研究">
    <meta name="twitter:description" content="涵蓋荷蘭建國史、胡斯戰爭、金璽詔書、聖本篤會規等七大歷史專題的學術級深度研究網站。">
    <meta name="twitter:image" content="https://ludwicia.github.io/ludwica-history-lesson/history_banner_bg.png">
    <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;600;700&family=Inter:wght@400;600;700&display=swap" rel="stylesheet">
    <script type="application/ld+json">
    {
      "@context": "https://schema.org",
      "@type": "WebSite",
      "name": "Ludwica 的簡單歷史課",
      "url": "https://ludwicia.github.io/ludwica-history-lesson/",
      "description": "深度歷史專題研究與報告，涵蓋荷蘭建國史、胡斯戰爭、金璽詔書、聖本篤會規等主題",
      "inLanguage": "zh-TW",
      "publisher": {
        "@type": "Person",
        "name": "Ludwica"
      }
    }
    </script>
    <script type="application/ld+json">
    {
      "@context": "https://schema.org",
      "@type": "CollectionPage",
      "name": "Ludwica 的簡單歷史課",
      "url": "https://ludwicia.github.io/ludwica-history-lesson/",
      "description": "涵蓋七大歷史專題的深度學術研究網站",
      "hasPart": [
        {"@type": "Article", "name": "荷蘭建國史與東印度公司興衰", "url": "https://ludwicia.github.io/ludwica-history-lesson/#page01"},
        {"@type": "Article", "name": "三個世界的交會與前哥倫布時期的美洲", "url": "https://ludwicia.github.io/ludwica-history-lesson/#page02"},
        {"@type": "Article", "name": "胡斯戰爭：信仰衝突、軍事變革與波希米亞國家認同", "url": "https://ludwicia.github.io/ludwica-history-lesson/#page03"},
        {"@type": "Article", "name": "神聖羅馬帝國：金璽詔書德中對照翻譯", "url": "https://ludwicia.github.io/ludwica-history-lesson/#page04"},
        {"@type": "Article", "name": "希爾紹修道院研究報告", "url": "https://ludwicia.github.io/ludwica-history-lesson/#page05"},
        {"@type": "Article", "name": "聖本篤會規三欄解析", "url": "https://ludwicia.github.io/ludwica-history-lesson/#page06"},
        {"@type": "Article", "name": "奧托-薩利安帝國教會體制", "url": "https://ludwicia.github.io/ludwica-history-lesson/#page07"},
        {"@type": "Article", "name": "沃姆斯協約", "url": "https://ludwicia.github.io/ludwica-history-lesson/#page08"}
      ]
    }
    </script>
    <style>
        :root { 
            --primary-color: #0055A4; 
            --secondary-color: #AE1C28; 
            --bg-color: #f4f7f6; 
            --text-color: #2d3748; 
            --card-bg: #ffffff; 
            --border-color: #e2e8f0; 
        }
        .desktop-only {
            display: inline;
        }
        body { 
            font-family: 'Inter', 'Noto Sans TC', sans-serif; 
            background-color: var(--bg-color); 
            color: var(--text-color); 
            line-height: 1.8; 
            margin: 0; 
            padding: 0; 
        }
        
        /* Premium Sticky Navigation Bar */
        .top-nav {
            position: sticky;
            top: 0;
            width: 100%;
            height: 70px;
            background: rgba(255, 255, 255, 0.85);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border-bottom: 1px solid rgba(226, 232, 240, 0.8);
            z-index: 1000;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.04);
            box-sizing: border-box;
        }
        .nav-container {
            max-width: 1600px;
            height: 100%;
            margin: 0 auto;
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0 30px;
            box-sizing: border-box;
        }
        .nav-brand {
            font-size: 1.3rem;
            font-weight: 700;
            color: var(--primary-color);
            text-decoration: none;
            display: flex;
            align-items: center;
            gap: 10px;
            letter-spacing: 1px;
        }
        .nav-links {
            display: flex;
            gap: 12px;
        }
        .nav-tab-btn {
            background: transparent;
            border: 2px solid transparent;
            border-radius: 8px;
            color: #4a5568;
            padding: 8px 16px;
            font-size: 0.95rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            outline: none;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .nav-tab-btn:hover {
            color: var(--primary-color);
            background: rgba(0, 85, 164, 0.05);
        }
        .nav-tab-btn.active {
            color: white;
            background: var(--primary-color);
            border-color: var(--primary-color);
            box-shadow: 0 4px 12px rgba(0, 85, 164, 0.2);
        }
        
        /* Dropdown Styles */
        .nav-group {
            position: relative;
            display: flex;
            align-items: center;
        }
        .nav-group-title {
            color: #4a5568;
            font-weight: 600;
            padding: 8px 16px;
            cursor: pointer;
            border-radius: 8px;
            transition: all 0.3s ease;
            display: flex;
            align-items: center;
            gap: 6px;
        }
        .nav-group-title:hover {
            color: var(--primary-color);
            background: rgba(0, 85, 164, 0.05);
        }
        .dropdown-arrow {
            font-size: 0.7em;
            transition: transform 0.3s ease;
        }
        .nav-group:hover .dropdown-arrow {
            transform: rotate(180deg);
        }
        
        @media (min-width: 801px) {
            .nav-dropdown {
                position: absolute;
                top: 100%;
                left: 0;
                background: #ffffff;
                min-width: 220px;
                box-shadow: 0 10px 25px rgba(0,0,0,0.15);
                border: 1px solid rgba(0,0,0,0.05);
                border-radius: 8px;
                padding: 10px;
                display: flex;
                flex-direction: column;
                gap: 5px;
                opacity: 0;
                visibility: hidden;
                transform: translateY(10px);
                transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
                z-index: 1000;
                box-sizing: border-box;
                height: auto;
                min-height: min-content;
            }
            .nav-group:hover .nav-dropdown {
                opacity: 1;
                visibility: visible;
                transform: translateY(5px);
            }
            .nav-dropdown .nav-tab-btn {
                width: 100%;
                text-align: left;
                justify-content: flex-start;
            }
        }
        
        /* Banner Styles */
        .site-banner {
            width: 100%;
            height: 260px;
            background: linear-gradient(rgba(10, 25, 47, 0.75), rgba(10, 25, 47, 0.9)), url('history_banner_bg.png');
            background-size: cover;
            background-position: center;
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 10px 30px rgba(0,0,0,0.15);
            position: relative;
            overflow: hidden;
        }
        .banner-content {
            text-align: center;
            color: #ffffff;
            animation: fadeIn 1.2s ease-in-out;
            z-index: 1;
        }
        .banner-subtitle {
            font-size: 1.1rem;
            letter-spacing: 6px;
            text-transform: uppercase;
            color: #cbd5e0;
            margin-bottom: 12px;
            font-weight: 600;
        }
        .banner-title {
            font-size: 3rem;
            font-weight: 700;
            text-shadow: 2px 2px 10px rgba(0,0,0,0.5);
            margin: 0;
            background: linear-gradient(45deg, #fbd38d, #ffffff);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(15px); }
            to { opacity: 1; transform: translateY(0); }
        }

        /* Three column layout */
        .layout {
            display: grid;
            grid-template-columns: 280px 1fr 300px;
            gap: 30px;
            max-width: 1600px;
            margin: 0 auto;
            padding: 30px 20px;
            min-height: 100vh;
            box-sizing: border-box;
        }

        /* Sidebars */
        .sidebar-left, .sidebar-right {
            background: var(--card-bg);
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.02);
            position: sticky;
            top: 100px;
            height: calc(100vh - 130px);
            overflow-y: auto;
            box-sizing: border-box;
            border: 1px solid var(--border-color);
        }
        
        .footer-header {
            display: none; /* Hidden on desktop */
        }
        
        #searchResults {
            max-height: calc(100vh - 280px);
            overflow-y: auto;
            margin-top: 10px;
        }
        
        .sidebar-title {
            font-size: 1.15rem;
            font-weight: 700;
            color: var(--primary-color);
            margin-bottom: 15px;
            border-bottom: 2px solid var(--primary-color);
            padding-bottom: 8px;
        }

        /* Table of Contents */
        .toc-item {
            display: block;
            color: #4a5568;
            text-decoration: none;
            padding: 6px 0;
            font-size: 0.92rem;
            border-bottom: 1px solid var(--border-color);
            transition: all 0.2s;
            line-height: 1.5;
        }
        .toc-item:hover { color: var(--primary-color); padding-left: 5px; }
        .toc-h3 { padding-left: 15px; font-size: 0.83rem; color: #718096; border-bottom: none; }

        /* Main Content */
        .content-middle {
            background-color: var(--card-bg);
            padding: 40px 50px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.03);
            border-radius: 12px;
            border: 1px solid var(--border-color);
            box-sizing: border-box;
            min-width: 0; /* Prevents flexbox/grid blowout */
        }
        
        .course-page {
            animation: fadeIn 0.4s ease;
        }
        
        /* 3-Column Document Layout */
        .layout.doc-mode {
            grid-template-columns: 1fr !important;
            max-width: 1400px;
        }
        .layout.doc-mode .sidebar-left { display: none !important; }
        /* Display sidebar-right at the bottom of the page in doc-mode on desktop */
        @media (min-width: 1201px) {
            .layout.doc-mode .sidebar-right {
                display: block !important;
                position: relative !important;
                top: 0 !important;
                height: auto !important;
                width: 100% !important;
                margin-top: 40px !important;
                box-shadow: 0 4px 15px rgba(0,0,0,0.02) !important;
            }
        }
        
        .doc-3col-container {
            display: flex;
            flex-direction: column;
            gap: 15px;
            width: 100%;
        }
        .doc-3col-header {
            display: grid;
            grid-template-columns: 1.2fr 1.2fr 0.6fr;
            gap: 20px;
            font-weight: 700;
            color: var(--primary-color);
            border-bottom: 2px solid var(--primary-color);
            padding-bottom: 10px;
            position: sticky;
            top: 70px;
            background: var(--card-bg);
            z-index: 10;
            font-size: 1.05rem;
            text-align: center;
        }
        .doc-3col-row {
            display: grid;
            grid-template-columns: 1.2fr 1.2fr 0.6fr;
            gap: 20px;
            border-bottom: 1px dashed #e2e8f0;
            padding-bottom: 15px;
        }
        .doc-col {
            font-size: 0.95rem;
            line-height: 1.6;
            color: #2d3748;
        }
        .doc-original {
            background: #f7fafc;
            padding: 12px;
            border-radius: 8px;
            font-family: 'Times New Roman', serif;
            border-left: 3px solid #a0aec0;
        }
        .doc-translation {
            padding: 12px;
        }
        .doc-explanation {
            background: #fffdf5;
            padding: 10px;
            border-radius: 8px;
            border: 1px dashed #ecc94b;
            font-size: 0.8rem;
        }
        
        /* Collapsible Explanation Accordion Styles inside a single unified card */
        .doc-explanation ul {
            list-style-type: none;
            padding-left: 0;
            margin: 0;
        }
        .explanation-details {
            margin-bottom: 6px;
            border-bottom: 1px dashed rgba(229, 196, 75, 0.3);
            background: transparent;
            transition: all 0.2s ease;
        }
        .explanation-details:last-child {
            border-bottom: none;
            margin-bottom: 0;
        }
        .explanation-summary {
            padding: 5px 0;
            font-weight: 600;
            color: #2d3748;
            cursor: pointer;
            outline: none;
            user-select: none;
            display: flex;
            align-items: center;
            list-style: none;
            font-size: 0.78rem;
        }
        .explanation-summary::-webkit-details-marker {
            display: none;
        }
        .explanation-summary::before {
            content: "▶";
            display: inline-block;
            margin-right: 6px;
            font-size: 0.65rem;
            color: #ecc94b;
            transition: transform 0.2s ease;
        }
        .explanation-details[open] .explanation-summary::before {
            transform: rotate(90deg);
        }
        .explanation-summary:hover {
            color: #b7791f;
        }
        .explanation-content {
            padding: 6px 10px;
            background: rgba(255, 255, 240, 0.5);
            color: #4a5568;
            font-size: 0.75rem;
            line-height: 1.5;
            border-radius: 4px;
            margin-bottom: 6px;
        }
        .explanation-term strong {
            color: #2d3748;
        }
        
        @keyframes contentFadeIn {
            from { opacity: 0; transform: translateY(8px); }
            to { opacity: 1; transform: translateY(0); }
        }

        /* Search Box */
        .search-box input {
            width: 100%;
            padding: 10px 14px;
            border: 1px solid var(--border-color);
            border-radius: 8px;
            font-size: 0.95rem;
            margin-bottom: 15px;
            box-sizing: border-box;
            outline: none;
            transition: border-color 0.2s;
        }
        .search-box input:focus { border-color: var(--primary-color); }
        
        .search-result-item {
            background: #f7fafc;
            padding: 10px 12px;
            border-radius: 6px;
            margin-bottom: 8px;
            font-size: 0.83rem;
            cursor: pointer;
            border-left: 3px solid var(--primary-color);
            transition: background 0.2s;
            line-height: 1.5;
        }
        .search-result-item:hover { background: #edf2f7; }
        mark { background-color: #fbd38d; color: #000; padding: 0 2px; border-radius: 2px; }

        /* Typography */
        h1 { font-size: 2.1rem; color: var(--primary-color); text-align: center; border-bottom: 3px solid var(--secondary-color); padding-bottom: 20px; margin-bottom: 30px; margin-top: 0; clear: both; line-height: 1.4; }
        h2 { font-size: 1.55rem; color: var(--primary-color); border-left: 5px solid var(--secondary-color); padding-left: 15px; margin-top: 45px; scroll-margin-top: 90px; clear: both; line-height: 1.4; }
        h3 { font-size: 1.25rem; color: #4a5568; margin-top: 25px; scroll-margin-top: 90px; line-height: 1.4; }
        p { font-size: 1.02rem; margin-bottom: 20px; text-align: justify; }
        
        figure.image-left {
            float: left;
            width: 35%;
            margin: 10px 25px 15px 0;
            background: var(--card-bg);
            padding: 10px;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.06);
            box-sizing: border-box;
            border: 1px solid var(--border-color);
        }
        figure.image-left img {
            width: 100%;
            height: auto;
            border-radius: 6px;
            display: block;
        }
        figure.image-left figcaption {
            text-align: center;
            font-size: 0.83rem;
            color: #718096;
            margin-top: 10px;
            line-height: 1.4;
        }

        table { width: 100%; border-collapse: collapse; margin: 30px 0; font-size: 0.92rem; box-shadow: 0 4px 6px rgba(0,0,0,0.02); clear: both; }
        th, td { padding: 10px 12px; text-align: left; border: 1px solid var(--border-color); }
        th { background-color: var(--primary-color); color: white; }
        tr:nth-child(even) { background-color: #f7fafc; }
        ul, ol { font-size: 1.02rem; line-height: 1.8; }
        a { color: var(--primary-color); text-decoration: none; }
        a:hover { text-decoration: underline; }

        /* ===== Document Title Section Style Adjustments ===== */
        .doc-title-section {
            text-align: left;
            margin-bottom: 30px;
        }
        .doc-title-section h1 {
            text-align: center;
        }
        .doc-title-section h2 {
            text-align: left;
        }
        .doc-title-section p {
            text-align: justify;
        }
        .doc-title-section ul, .doc-title-section ol {
            text-align: left;
            padding-left: 25px;
            margin-bottom: 20px;
        }
        .doc-title-section li {
            text-align: left;
        }
        .doc-title-section blockquote {
            text-align: left;
        }

        /* ===== Responsive Media Queries ===== */
        @media (max-width: 1200px) {
            .layout { grid-template-columns: 280px 1fr; }
            
            /* Sidebar transitions to floating bottom card */
            .sidebar-right {
                position: fixed;
                bottom: 0;
                left: 0;
                right: 0;
                width: 100%;
                height: 280px;
                top: auto;
                background: rgba(255, 255, 255, 0.96);
                backdrop-filter: blur(10px);
                -webkit-backdrop-filter: blur(10px);
                box-shadow: 0 -10px 30px rgba(0,0,0,0.12);
                border-top: 3px solid var(--primary-color);
                border-radius: 16px 16px 0 0;
                z-index: 1000;
                margin: 0;
                padding: 0;
                overflow: hidden;
                display: flex;
                flex-direction: column;
                transition: transform 0.35s cubic-bezier(0.4, 0, 0.2, 1);
            }
            
            /* Collapsed State */
            .sidebar-right.collapsed-footer {
                transform: translateY(calc(100% - 48px));
            }
            
            /* Show controls header */
            .footer-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                min-height: 48px;
                height: 48px;
                background: linear-gradient(135deg, var(--primary-color), #0a252f);
                color: white;
                padding: 0 20px;
                cursor: pointer;
                user-select: none;
                flex-shrink: 0;
            }
            
            .footer-header-title {
                font-weight: 700;
                font-size: 0.92rem;
                letter-spacing: 1px;
            }
            
            .footer-toggle-btn {
                background: rgba(255, 255, 255, 0.2);
                border: none;
                color: white;
                padding: 4px 12px;
                border-radius: 20px;
                font-size: 0.78rem;
                font-weight: 600;
                cursor: pointer;
                transition: background 0.2s;
            }
            
            .footer-toggle-btn:hover {
                background: rgba(255, 255, 255, 0.3);
            }
            
            /* Grid inside floating footer */
            .footer-main-content {
                display: grid;
                grid-template-columns: 260px 1fr 240px;
                gap: 25px;
                padding: 20px 25px;
                height: calc(100% - 48px);
                box-sizing: border-box;
                overflow: hidden;
            }
            
            .footer-search-col {
                display: flex;
                flex-direction: column;
            }
            
            .footer-search-col .sidebar-title {
                margin-top: 0;
                margin-bottom: 12px;
                font-size: 1.05rem;
                border-bottom: 2px solid var(--primary-color);
                padding-bottom: 6px;
            }
            
            .footer-search-col .search-box input {
                margin-bottom: 0;
            }
            
            .footer-results-col {
                display: flex;
                flex-direction: column;
                overflow: hidden;
                border-left: 1px solid var(--border-color);
                border-right: 1px solid var(--border-color);
                padding: 0 20px;
            }
            
            #searchResults {
                flex: 1;
                max-height: 100%;
                overflow-y: auto;
                margin-top: 0;
                padding-right: 5px;
            }
            
            .footer-version-col {
                display: flex;
                align-items: flex-start;
                justify-content: center;
                overflow-y: auto;
                padding-right: 5px;
            }
            
            .version-card {
                background: #f7fafc;
                border-radius: 8px;
                padding: 12px;
                width: 100%;
                box-sizing: border-box;
                font-size: 0.78rem;
                color: #4a5568;
                text-align: center;
                border-top: 3px solid var(--primary-color);
                box-shadow: 0 2px 8px rgba(0,0,0,0.01);
            }
        }
        .nav-mobile-header { display: none; }
        @media (max-width: 800px) {
            .nav-mobile-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                width: 100%;
                padding-bottom: 5px;
                border-bottom: 1px solid rgba(0,0,0,0.05);
            }
            .nav-mobile-title {
                font-weight: 700;
                color: var(--primary-color);
                font-size: 1.05rem;
                display: flex;
                align-items: center;
                gap: 8px;
            }
            .nav-mobile-toggle {
                background: var(--primary-color);
                border: none;
                color: white;
                padding: 4px 12px;
                border-radius: 20px;
                font-size: 0.78rem;
                font-weight: 600;
                cursor: pointer;
            }
            .top-nav {
                height: auto;
                padding: 10px 0;
            }
            .nav-container {
                flex-direction: column;
                gap: 10px;
                padding: 0 15px;
            }
            .nav-links {
                display: flex;
                flex-direction: column;
                width: 100%;
                gap: 15px;
                align-items: flex-start;
            }
            .nav-links.collapsed {
                display: none;
            }
            .nav-group {
                flex-direction: column;
                width: 100%;
                align-items: flex-start;
            }
            .nav-group-title {
                padding-left: 0;
                color: var(--primary-color);
                border-bottom: 2px solid var(--secondary-color);
                width: 100%;
                border-radius: 0;
                margin-bottom: 8px;
                padding-bottom: 5px;
            }
            .nav-group-title:hover { background: none; }
            .dropdown-arrow { display: none; }
            .nav-dropdown {
                display: flex;
                flex-wrap: wrap;
                width: 100%;
                gap: 8px;
            }
            .nav-tab-btn {
                padding: 6px 12px;
                font-size: 0.82rem;
                text-align: left;
                white-space: nowrap;
                justify-content: flex-start;
                box-sizing: border-box;
                flex: 0 0 calc(50% - 4px);
            }
            .desktop-only {
                display: none;
            }

            .layout { display: flex; flex-direction: column; padding: 15px; padding-bottom: 60px; }
            .site-banner { height: 180px; }
            .banner-title { font-size: 2rem; }
            .banner-subtitle { font-size: 0.85rem; letter-spacing: 3px; }
            .sidebar-left { display: none; }
            
            .sidebar-right {
                height: 340px;
            }
            .sidebar-right.collapsed-footer {
                transform: translateY(calc(100% - 48px));
            }
            .footer-main-content {
                display: flex;
                flex-direction: column;
                gap: 12px;
                padding: 15px 15px;
                height: calc(100% - 48px);
                overflow-y: auto;
            }
            .footer-search-col .sidebar-title {
                display: none;
            }
            .footer-results-col {
                border-left: none;
                border-right: none;
                padding: 0;
            }
            #searchResults {
                max-height: none;
                overflow-y: visible;
            }
            .footer-version-col {
                display: block;
                margin-top: 15px;
                border-top: 1px solid #e2e8f0;
                padding-top: 15px;
            }
            
            .content-middle { padding: 25px 18px; }
            figure.image-left { width: 100% !important; float: none !important; margin: 0 0 20px 0 !important; }
            h1 { font-size: 1.6rem; }
            
            /* Mobile Collapsible Heading Style */
            .content-middle h2 {
                cursor: pointer;
                position: relative;
                padding-right: 40px;
                padding-top: 12px;
                padding-bottom: 12px;
                margin-top: 25px;
                background-color: #f7fafc;
                border-radius: 6px;
                border-left: 5px solid var(--secondary-color);
                padding-left: 15px;
                font-size: 1.25rem;
                transition: background-color 0.2s, color 0.2s;
            }
            .content-middle h2:hover {
                background-color: #edf2f7;
            }
            .content-middle h2::after {
                content: '▲';
                position: absolute;
                right: 15px;
                top: 50%;
                transform: translateY(-50%);
                font-size: 0.75rem;
                color: var(--primary-color);
                transition: transform 0.3s ease;
            }
            .content-middle h2.collapsed::after {
                transform: translateY(-50%) rotate(180deg);
            }
            
            th, td { padding: 6px 8px; font-size: 0.8rem; }
            
            /* Mobile 3-Column Document Layout */
            .doc-3col-header { display: none; }
            .doc-3col-row {
                grid-template-columns: 1fr !important;
                gap: 12px;
                border-bottom: 2px solid var(--primary-color);
                padding-bottom: 20px;
                margin-bottom: 10px;
            }
            .doc-original::before { content: "原文："; font-weight: bold; color: var(--primary-color); display: block; margin-bottom: 8px; font-family: sans-serif; }
            .doc-translation::before { content: "譯文："; font-weight: bold; color: var(--secondary-color); display: block; margin-bottom: 8px; }
            .doc-explanation::before { content: "解釋筆記："; font-weight: bold; color: #d69e2e; display: block; margin-bottom: 12px; }
        }
    </style>
</head>
<body>

<!-- Glassmorphism 置頂導覽列 -->
<nav class="top-nav">
    <div class="nav-container">
        <div class="nav-mobile-header">
            <div class="nav-mobile-title">🏛️ 歷史課程導覽</div>
            <button class="nav-mobile-toggle" id="navMobileToggle">展開 ▼</button>
        </div>
        <div class="nav-links collapsed" id="navLinks">
            <!-- 歷史專題 -->
            <div class="nav-group">
                <div class="nav-group-title">歷史專題 <span class="dropdown-arrow">▼</span></div>
                <div class="nav-dropdown">
                    <a href="#page01" id="nav-btn-page01" class="nav-tab-btn active" style="text-decoration: none;">荷蘭建國與地緣政經</a>
                    <a href="#page02" id="nav-btn-page02" class="nav-tab-btn" style="text-decoration: none;">美國的誕生(一)</a>
                    <a href="#page03" id="nav-btn-page03" class="nav-tab-btn" style="text-decoration: none;">宗教戰爭(一)：胡斯戰爭</a>
                    <a href="#page12" id="nav-btn-page12" class="nav-tab-btn" style="text-decoration: none;">宗教戰爭(二)：卡特里派</a>
                    <a href="#page05" id="nav-btn-page05" class="nav-tab-btn" style="text-decoration: none;">希爾紹修道院</a>
                    <a href="#page07" id="nav-btn-page07" class="nav-tab-btn" style="text-decoration: none;">奧托-薩利安帝國教會體制</a>
                    <a href="#page09" id="nav-btn-page09" class="nav-tab-btn" style="text-decoration: none;">丕平獻土與教皇國誕生</a>
                    <a href="#page10" id="nav-btn-page10" class="nav-tab-btn" style="text-decoration: none;">卡洛林教育基建與知識復興</a>
                    <a href="#page11" id="nav-btn-page11" class="nav-tab-btn" style="text-decoration: none;">歐洲造紙術的歷史演變</a>
                </div>
            </div>
            
            <!-- 歷史文件 -->
            <div class="nav-group">
                <div class="nav-group-title">歷史文件 <span class="dropdown-arrow">▼</span></div>
                <div class="nav-dropdown">
                    <a href="#page04" id="nav-btn-page04" class="nav-tab-btn" style="text-decoration: none;">神聖羅馬帝國：金璽詔書</a>
                    <a href="#page06" id="nav-btn-page06" class="nav-tab-btn" style="text-decoration: none;">修道院制度：聖本篤會規</a>
                    <a href="#page08" id="nav-btn-page08" class="nav-tab-btn" style="text-decoration: none;">敘任權之爭：沃姆斯協約</a>
                </div>
            </div>
        </div>
    </div>
</nav>

<!-- Beautiful Hero Banner -->
<div class="site-banner">
    <div class="banner-content">
        <div class="banner-subtitle">Ludwica's History Series</div>
        <div class="banner-title">Ludwica 的簡單歷史課</div>
    </div>
</div>

<div class="layout">
    <!-- Left Sidebar: TOC -->
    <aside class="sidebar-left">
        <div class="sidebar-title">章節目錄</div>
        <div id="toc"></div>
    </aside>

    <!-- Middle Column: Main Content -->
    <main class="content-middle" id="main-content">
        <!-- 課堂一：荷蘭建國史 -->
        <div id="course-page01" class="course-page">
            __HTML_BODY_PAGE01__
        </div>

        <!-- 課堂二：美國早期史 -->
        <div id="course-page02" class="course-page" style="display: none;">
            __HTML_BODY_PAGE02__
        </div>

        <!-- 課堂三：宗教戰爭(一)：胡斯戰爭 -->
        <div id="course-page03" class="course-page" style="display: none;">
            __HTML_BODY_PAGE03__
        </div>

        <!-- 歷史文件一：金璽詔書 -->
        <div id="course-page04" class="course-page" style="display: none;">
            __HTML_BODY_PAGE04__
        </div>

        <!-- 課堂四：希爾紹修道院研究 -->
        <div id="course-page05" class="course-page" style="display: none;">
            __HTML_BODY_PAGE05__
        </div>

        <!-- 課堂五：奧托-薩利安帝國教會體制 -->
        <div id="course-page07" class="course-page" style="display: none;">
            __HTML_BODY_PAGE07__
        </div>
        <div id="course-page08" class="course-page" style="display: none;">
            __HTML_BODY_PAGE08__
        </div>

        <!-- 課堂六：丕平獻土地緣政治研究 -->
        <div id="course-page09" class="course-page" style="display: none;">
            __HTML_BODY_PAGE09__
        </div>

        <!-- 課堂七：卡洛林教育基建 -->
        <div id="course-page10" class="course-page" style="display: none;">
            __HTML_BODY_PAGE10__
        </div>

        <!-- 課堂八：歐洲造紙術演變 -->
        <div id="course-page11" class="course-page" style="display: none;">
            __HTML_BODY_PAGE11__
        </div>

        <!-- 課堂九：宗教戰爭(二)：卡特里派 -->
        <div id="course-page12" class="course-page" style="display: none;">
            __HTML_BODY_PAGE12__
        </div>

        <!-- 歷史文件二：聖本篤會規 -->
        <div id="course-page06" class="course-page" style="display: none;">
            __HTML_BODY_PAGE06__
        </div>
    </main>

    <!-- Right Sidebar / Floating Footer: Search & Version -->
    <aside class="sidebar-right collapsed-footer" id="sidebarRight">
        <!-- Footer Header (Visible only when it behaves as mobile floating footer) -->
        <div class="footer-header" id="footerHeader">
            <span class="footer-header-title">🔍 快捷關鍵字搜尋與版本宣告</span>
            <button class="footer-toggle-btn" id="footerToggleBtn">展開 ▲</button>
        </div>
        
        <div class="footer-main-content">
            <!-- Col 1: Search Input -->
            <div class="footer-search-col">
                <div class="sidebar-title">關鍵字查詢</div>
                <div class="search-box">
                    <input type="text" id="searchInput" placeholder="輸入關鍵字 (例如: VOC, 印尼, 玉米)...">
                </div>
            </div>
            
            <!-- Col 2: Search Results -->
            <div class="footer-results-col">
                <div id="searchResults">
                    <div style="color:#a0aec0; text-align:center; margin-top:30px; font-size: 0.9rem;">
                        輸入關鍵字以尋找內文段落
                    </div>
                </div>
            </div>
            
            <!-- Col 3: Version Info -->
            <div class="footer-version-col">
                <div class="version-card">
                    <div style="font-weight: 600; margin-bottom: 8px; color: var(--primary-color);">📝 版本與課堂宣告</div>
                    <div style="font-weight: 500; margin-bottom: 6px;">版面設計：3.7 (新增「卡洛林教育基建」與「歐洲造紙術演變」歷史專題)</div>
                    <div style="color: #718096; font-size: 0.75rem;">發布日期：2026-06-02</div>
                    <hr style="border: none; border-top: 1px dashed #cbd5e0; margin: 8px 0;">
                    <div id="dynamic-course-info" style="text-align: left; font-size: 0.8rem; line-height: 1.5;">
                        <!-- Dynamic metadata loaded by JS -->
                    </div>
                    <hr style="border: none; border-top: 1px dashed #cbd5e0; margin: 8px 0;">
                    <div style="font-size: 0.7rem; color: #a0aec0; text-align: left; line-height: 1.6;">
                        ⚠️ 本文由 AI 生成，可能包含事實性錯誤，請讀者自行查證。<br>
                        🖼️ 文中圖片來源：<a href="https://commons.wikimedia.org/" target="_blank" style="color: #718096;">Wikimedia Commons</a>。<br>
                        📜 本文採用 <a href="https://creativecommons.org/licenses/by-sa/4.0/deed.zh-hant" target="_blank" style="color: #718096;">CC BY-SA 4.0</a> 授權。
                    </div>
                    <hr style="border: none; border-top: 1px dashed #cbd5e0; margin: 8px 0;">
                    <div style="font-size: 0.7rem; color: #718096; text-align: left; line-height: 1.6; display: flex; flex-direction: column; gap: 4px;">
                        <span>👁️ 本站總瀏覽量：<span id="busuanzi_value_site_pv" style="font-weight: 600; color: var(--primary-color);">--</span> 次</span>
                        <span>👤 本站總訪客數：<span id="busuanzi_value_site_uv" style="font-weight: 600; color: var(--primary-color);">--</span> 人</span>
                    </div>
                </div>
            </div>
        </div>
    </aside>
</div>

<script>
    // 1. Dynamic Course Metadata
    const courseInfo = {
        'page01': `
            <div style="color: #4a5568;">
                <b>📚 當前課堂：</b>荷蘭建國史與地緣政經<br>
                <b>🏷️ 內容版本：</b>1.1<br>
                <b>📅 更新日期：</b>__PAGE01_DATE__<br>
                <b>👤 內容生成：</b>AI 深度研究<br>
                <b>🛠️ 網頁工程：</b>Antigravity 協作
            </div>
        `,
        'page02': `
            <div style="color: #4a5568;">
                <b>📚 當前課堂：</b>美國的誕生(一)<br>
                <b>🏷️ 內容版本：</b>1.0<br>
                <b>📅 更新日期：</b>__PAGE02_DATE__<br>
                <b>👤 內容生成：</b>AI 深度研究<br>
                <b>🛠️ 網頁工程：</b>Antigravity 協作
            </div>
        `,
        'page03': `
            <div style="color: #4a5568;">
                <b>📚 當前課堂：</b>宗教戰爭(一)：胡斯戰爭<br>
                <b>🏷️ 內容版本：</b>1.0<br>
                <b>📅 更新日期：</b>__PAGE03_DATE__<br>
                <b>👤 內容生成：</b>AI 深度研究<br>
                <b>🛠️ 網頁工程：</b>Antigravity 協作
            </div>
        `,
        page04: `
            <div style="font-size: 0.85rem; color: #4a5568; line-height: 1.6;">
                <b>📚 當前文件：</b>神聖羅馬帝國：金璽詔書<br>
                <b>🏷️ 內容版本：</b>1.5<br>
                <b>📅 更新日期：</b>__PAGE04_DATE__<br>
                <b>👤 內容生成：</b>AI 深度研究<br>
                <b>🛠️ 網頁工程：</b>Antigravity 協作
            </div>
        `,
        page05: `
            <div style="color: #4a5568;">
                <b>📚 當前課堂：</b>希爾紹修道院<br>
                <b>🏷️ 內容版本：</b>1.0<br>
                <b>📅 更新日期：</b>__PAGE05_DATE__<br>
                <b>👤 內容生成：</b>AI 深度研究<br>
                <b>🛠️ 網頁工程：</b>Antigravity 協作
            </div>
        `,
        page07: `
            <div style="color: #4a5568;">
                <b>📚 當前課堂：</b>奧托-薩利安帝國教會體制<br>
                <b>🏷️ 內容版本：</b>1.0<br>
                <b>📅 更新日期：</b>__PAGE07_DATE__<br>
                <b>👤 內容生成：</b>AI 深度研究<br>
                <b>🛠️ 網頁工程：</b>Antigravity 協作
            </div>
        `,
        page08: `
            <div style="color: #4a5568;">
                <b>📚 當前課堂：</b>沃姆斯協約<br>
                <b>🏷️ 內容版本：</b>1.0<br>
                <b>📅 更新日期：</b>__PAGE08_DATE__<br>
                <b>👤 內容生成：</b>AI 深度研究<br>
                <b>🛠️ 網頁工程：</b>Antigravity 協作
            </div>
        `,
        page09: `
            <div style="color: #4a5568;">
                <b>📚 當前課堂：</b>丕平獻土的地緣政治體系研究<br>
                <b>🏷️ 內容版本：</b>1.0<br>
                <b>📅 更新日期：</b>__PAGE09_DATE__<br>
                <b>👤 內容生成：</b>AI 深度研究<br>
                <b>🛠️ 網頁工程：</b>Antigravity 協作
            </div>
        `,
        page10: `
            <div style="color: #4a5568;">
                <b>📚 當前課堂：</b>卡洛林王朝教育基建與知識復興<br>
                <b>🏷️ 內容版本：</b>1.0<br>
                <b>📅 更新日期：</b>__PAGE10_DATE__<br>
                <b>👤 內容生成：</b>AI 深度研究<br>
                <b>🛠️ 網頁工程：</b>Antigravity 協作
            </div>
        `,
        page11: `
            <div style="color: #4a5568;">
                <b>📚 當前課堂：</b>歐洲造紙術的歷史演變與技術革新<br>
                <b>🏷️ 內容版本：</b>1.0<br>
                <b>📅 更新日期：</b>__PAGE11_DATE__<br>
                <b>👤 內容生成：</b>AI 深度研究<br>
                <b>🛠️ 網頁工程：</b>Antigravity 協作
            </div>
        `,
        page12: `
            <div style="color: #4a5568;">
                <b>📚 當前課堂：</b>中世紀南法卡特里派的興起與整肅<br>
                <b>🏷️ 內容版本：</b>1.0<br>
                <b>📅 更新日期：</b>__PAGE12_DATE__<br>
                <b>👤 內容生成：</b>AI 深度研究<br>
                <b>🛠️ 網頁工程：</b>Antigravity 協作
            </div>
        `,
        page06: `
            <div style="font-size: 0.85rem; color: #4a5568; line-height: 1.6;">
                <b>📚 當前文件：</b>修道院制度：聖本篤會規<br>
                <b>🏷️ 內容版本：</b>1.0<br>
                <b>📅 更新日期：</b>__PAGE06_DATE__<br>
                <b>👤 內容生成：</b>AI 深度研究<br>
                <b>🛠️ 網頁工程：</b>Antigravity 協作
            </div>
        `
    };

    // 2. SEO Dynamic Meta Tags (per-page title & description)
    const pageSEO = {
        'page01': { title: '荷蘭建國史與東印度公司興衰 — Ludwica 的簡單歷史課', desc: '深入解析荷蘭從低地十七省到聯省共和國的建國歷程、東印度公司的全球貿易帝國、黃金時代的藝術巅峰與當代政經轉型。' },
        'page02': { title: '前哥倫布時期美洲與三個世界的交會 — Ludwica 的簡單歷史課', desc: '探索1607年以前美洲原住民的文明成就、大航海時代的技術革命、哥倫布大交換，以及西班牙、法國、英國的早期殖民衝突。' },
        'page03': { title: '胡斯戰爭：信仰衝突與波希米亞國家認同 — Ludwica 的簡單歷史課', desc: '揚·胡斯的宗教改革先驅運動、波希米亞的宗教衝突與軍事變革、戰車壘戰術革新，以及對歐洲宗教格局的深遠影響。' },
        'page04': { title: '金璽詔書：神聖羅馬帝國德中對照翻譯 — Ludwica 的簡單歷史課', desc: '1356年《金璽詔書》全文德文原文、中文翻譯與學術註解三欄對照，解析選帝侯制度與帝國憲政體制的基石文件。' },
        'page05': { title: '希爾紹修道院研究報告 — Ludwica 的簡單歷史課', desc: '希爾紹修道院的千年歷史、威廉大院長的改革運動、希爾紹建築學派的羅馬式美學巅峰，以及九年戰爭後的廢墟重生。' },
        'page06': { title: '聖本篤會規三欄解析 — Ludwica 的簡單歷史課', desc: '公元6世紀西方隱修制度基石《聖本篤會規》德文原文、中文翻譯與專業學術註釋三欄並列解析。' },
        'page07': { title: '奧托-薩利安帝國教會體制 — Ludwica 的簡單歷史課', desc: '奧托王朝與薩利安王朝的帝國教會體制、政教合一的運作機制、巡迴朝廷制度，以及敘任權之爭的歷史根源。' },
        'page08': { title: '沃姆斯協約 — Ludwica 的簡單歷史課', desc: '結束敘任權之爭的歷史性協約，區分神權與世俗權力，奠定中古世紀政教關係新局。' },
        'page09': { title: '丕平獻土的地緣政治體系研究 — Ludwica 的簡單歷史課', desc: '深入研究西元八世紀中葉丕平獻土的地緣政治背景、卡洛林與教廷的權力交換機制、《君士坦丁贈禮》的法理偽造陰謀，以及對中世紀西歐政教關係的深遠歷史影響。' },
        'page10': { title: '卡洛林王朝教育基建與知識復興 — Ludwica 的簡單歷史課', desc: '探討卡洛林王朝教育基建與宗教變革、手抄室與卡洛林小草體書寫革命、跨國學者網絡、基督教化七藝與課堂實踐，以及文明火種對後世中世紀大學的深遠影響。' },
        'page11': { title: '歐洲造紙術的歷史演變與技術革新 — Ludwica 的簡單歷史課', desc: '研究歐洲造紙術的地中海傳播、法布里亞諾技術革命、荷蘭式打漿機與長網造紙機機械化，以及紙張作為物質中介對近代官僚體制、宗教改革與古騰堡印刷術的歷史重塑。' },
        'page12': { title: '中世紀卡特里派的興起、教義、十字軍聖戰與歷史餘音 — Ludwica 的簡單歷史課', desc: '深入研究中世紀南法阿爾比十字軍東征、卡特里派（阿爾比派）二元論神學與禁慾實踐、宗教裁判所的官僚化清洗，以及《富尼埃登記簿》與微觀歷史學《蒙塔尤》的思想異質性。' }
    };

    function updatePageSEO(pageId) {
        const seo = pageSEO[pageId];
        if (seo) {
            document.title = seo.title;
            const descMeta = document.querySelector('meta[name="description"]');
            if (descMeta) descMeta.setAttribute('content', seo.desc);
            const ogTitle = document.querySelector('meta[property="og:title"]');
            if (ogTitle) ogTitle.setAttribute('content', seo.title);
            const ogDesc = document.querySelector('meta[property="og:description"]');
            if (ogDesc) ogDesc.setAttribute('content', seo.desc);
        }
    }

    // 3. Navigation Page Switching & Dynamic SEO
    let activePageId = null;
    let searchableElements = [];

    function switchPage(pageId) {
        activePageId = pageId;
        
        // Handle full-width doc mode
        const layout = document.querySelector('.layout');
        if (pageId === 'page04' || pageId === 'page06' || pageId === 'page08') {
            layout.classList.add('doc-mode');
        } else {
            layout.classList.remove('doc-mode');
        }
        
        // Update active tab buttons
        document.querySelectorAll('.nav-tab-btn').forEach(btn => btn.classList.remove('active'));
        const activeBtn = document.getElementById('nav-btn-' + pageId);
        if (activeBtn) activeBtn.classList.add('active');
        
        // Show/hide course content blocks
        document.querySelectorAll('.course-page').forEach(page => page.style.display = 'none');
        const activePage = document.getElementById('course-' + pageId);
        if (activePage) activePage.style.display = 'block';
        
        // Re-generate TOC for the active page
        generateTOC(pageId);
        
        // Clear search inputs & results when manually switching tabs
        document.getElementById('searchInput').value = '';
        document.getElementById('searchResults').innerHTML = '<div style="color:#a0aec0; text-align:center; margin-top:30px; font-size: 0.9rem;">輸入關鍵字以尋找內文段落</div>';
        
        // Update copyright / details card
        const infoDiv = document.getElementById('dynamic-course-info');
        if (infoDiv && courseInfo[pageId]) {
            infoDiv.innerHTML = courseInfo[pageId];
        }
        
        // Re-init mobile collapsible headers
        initMobileCollapseForPage(pageId);

        // Smooth scroll to top of page/content
        if (window.scrollY > 280) {
            window.scrollTo({top: 260, behavior: 'smooth'});
        }
        
        // Update URL hash state
        const currentHash = window.location.hash.substring(1);
        if (!currentHash.startsWith(pageId)) {
            window.history.pushState(null, null, '#' + pageId);
        }

        // Update dynamic SEO meta tags
        updatePageSEO(pageId);
    }

    // 4. Generate Table of Contents on the Fly
    function generateTOC(pageId) {
        const tocContainer = document.getElementById('toc');
        tocContainer.innerHTML = '';
        
        const activePage = document.getElementById('course-' + pageId);
        if (!activePage) return;
        
        const headings = activePage.querySelectorAll('h2, h3');
        headings.forEach((h, index) => {
            // Always prefix with pageId to avoid cross-page collision and enable hash routing
            h.id = pageId + '-heading-' + index;
            const link = document.createElement('a');
            link.href = '#' + h.id;
            link.innerText = h.innerText;
            link.className = 'toc-item toc-' + h.tagName.toLowerCase();
            tocContainer.appendChild(link);
        });
    }

    // 5. Global Search Indexing
    function initGlobalSearchIndex() {
        searchableElements = [];
        const pages = [
            { id: 'page01', name: '荷蘭建國與地緣政經' },
            { id: 'page02', name: '美國的誕生(一)' },
            { id: 'page03', name: '宗教戰爭(一)：胡斯戰爭' },
            { id: 'page04', name: '神聖羅馬帝國：金璽詔書' },
            { id: 'page05', name: '希爾紹修道院' },
            { id: 'page06', name: '修道院制度：聖本篤會規' },
            { id: 'page07', name: '奧托-薩利安帝國教會體制' },
            { id: 'page08', name: '敘任權之爭：沃姆斯協約' },
            { id: 'page09', name: '丕平獻土與教皇國誕生' },
            { id: 'page10', name: '卡洛林教育基建與知識復興' },
            { id: 'page11', name: '歐洲造紙術的歷史演變' },
            { id: 'page12', name: '宗教戰爭(二)：卡特里派' }
        ];
        
        pages.forEach(p => {
            const pageEl = document.getElementById('course-' + p.id);
            if (pageEl) {
                const elements = pageEl.querySelectorAll('p, h2, h3, li, td');
                elements.forEach((el, index) => {
                    if (!el.id) el.id = p.id + '-search-match-' + index;
                    searchableElements.push({
                        element: el,
                        pageId: p.id,
                        pageName: p.name,
                        text: el.innerText
                    });
                });
            }
        });
    }

    // 6. Keyword Search Engine (Global Cross-Page Search)
    const searchInput = document.getElementById('searchInput');
    const searchResults = document.getElementById('searchResults');

    searchInput.addEventListener('input', (e) => {
        const keyword = e.target.value.trim().toLowerCase();
        searchResults.innerHTML = '';
        
        if (!keyword) {
            searchResults.innerHTML = '<div style="color:#a0aec0; text-align:center; margin-top:30px; font-size: 0.9rem;">輸入關鍵字以尋找內文段落</div>';
            return;
        }

        let count = 0;
        searchableElements.forEach((item) => {
            const text = item.text;
            if (text.toLowerCase().includes(keyword)) {
                count++;
                if (count > 50) return; // Cap results to prevent lag
                
                const res = document.createElement('div');
                res.className = 'search-result-item';
                
                const idx = text.toLowerCase().indexOf(keyword);
                const start = Math.max(0, idx - 25);
                const end = Math.min(text.length, idx + 25);
                let snippet = text.substring(start, end);
                if (start > 0) snippet = '...' + snippet;
                if (end < text.length) snippet = snippet + '...';
                
                // Highlight keyword
                const regex = new RegExp('(' + keyword + ')', 'gi');
                snippet = snippet.replace(regex, '<mark>$1</mark>');
                
                const el = item.element;
                
                // Prepend with the page name to show where the result belongs
                res.innerHTML = `<span style="font-size: 0.72rem; display: block; font-weight: 600; color: var(--primary-color); margin-bottom: 3px;">📌 ${item.pageName}</span>` + snippet;
                
                res.onclick = () => {
                    // Switch to the target page if it is not the active page
                    if (activePageId !== item.pageId) {
                        switchPage(item.pageId);
                    }
                    
                    // Mobile auto-expand collapsed heading if hidden inside one
                    if (window.innerWidth <= 800) {
                        const parentH2 = getParentH2(el);
                        if (parentH2 && parentH2.classList.contains('collapsed')) {
                            parentH2.click();
                        }
                    }
                    
                    // Close floating drawer on mobile / tablets
                    const sidebarRight = document.getElementById('sidebarRight');
                    const footerToggleBtn = document.getElementById('footerToggleBtn');
                    if (window.innerWidth <= 1200) {
                        if (sidebarRight && !sidebarRight.classList.contains('collapsed-footer')) {
                            sidebarRight.classList.add('collapsed-footer');
                            if (footerToggleBtn) footerToggleBtn.innerText = '展開 ▲';
                        }
                    }
                    
                    setTimeout(() => {
                        el.scrollIntoView({behavior: 'smooth', block: 'center'});
                        const originalBg = el.style.backgroundColor;
                        el.style.transition = 'background-color 0.3s';
                        el.style.backgroundColor = '#fbd38d';
                        setTimeout(() => { el.style.backgroundColor = originalBg; }, 2000);
                    }, window.innerWidth <= 800 ? 50 : 0);
                };
                searchResults.appendChild(res);
            }
        });
        
        if (count === 0) {
            searchResults.innerHTML = '<div style="color:#e53e3e; text-align:center; margin-top:30px; font-size: 0.95rem;">找不到包含「' + e.target.value + '」的內容</div>';
        } else if (count > 50) {
            const note = document.createElement('div');
            note.style = "color:#718096; text-align:center; margin-top:10px; font-size: 0.8rem;";
            note.innerText = `找到超過 50 筆結果，僅顯示前 50 筆`;
            searchResults.appendChild(note);
        }
    });

    // 7. Mobile Collapse Utilities
    function getParentH2(element) {
        let prev = element.previousElementSibling;
        while (prev) {
            if (prev.tagName === 'H2') {
                return prev;
            }
            prev = prev.previousElementSibling;
        }
        return null;
    }

    function initMobileCollapseForPage(pageId) {
        const isMobile = window.innerWidth <= 800;
        const activePage = document.getElementById('course-' + pageId);
        if (!activePage) return;
        
        const h2s = activePage.querySelectorAll('h2');
        h2s.forEach(h2 => {
            // Find related siblings to collapse/expand
            if (!h2._contentElements) {
                const contentElements = [];
                let next = h2.nextElementSibling;
                while (next && next.tagName !== 'H2') {
                    contentElements.push(next);
                    next = next.nextElementSibling;
                }
                h2._contentElements = contentElements;
                
                // Bind click toggle
                h2.addEventListener('click', () => {
                    if (window.innerWidth <= 800) {
                        const isCollapsed = h2.classList.toggle('collapsed');
                        h2._contentElements.forEach(el => {
                            el.style.display = isCollapsed ? 'none' : '';
                        });
                    }
                });
            }
            
            // Set initial state - Default to EXPANDED on all devices
            h2.classList.remove('collapsed');
            h2._contentElements.forEach(el => el.style.display = '');
        });
    }

    // Handles window resizing collapse resets
    let wasMobile = window.innerWidth <= 800;
    window.addEventListener('resize', () => {
        const isMobile = window.innerWidth <= 800;
        if (isMobile !== wasMobile) {
            wasMobile = isMobile;
            initMobileCollapseForPage(activePageId);
        }
    });

    // 8. Mobile Floating Drawer Collapse Toggle
    const sidebarRight = document.getElementById('sidebarRight');
    const footerHeader = document.getElementById('footerHeader');
    const footerToggleBtn = document.getElementById('footerToggleBtn');

    if (footerHeader && sidebarRight && footerToggleBtn) {
        const toggleFooter = () => {
            const isCollapsed = sidebarRight.classList.toggle('collapsed-footer');
            footerToggleBtn.innerText = isCollapsed ? '展開 ▲' : '收合 ▼';
        };
        footerHeader.addEventListener('click', toggleFooter);
    }

    // 8.5 Mobile Top Nav Toggle
    const navMobileToggle = document.getElementById('navMobileToggle');
    const navLinks = document.getElementById('navLinks');
    if (navMobileToggle && navLinks) {
        navMobileToggle.addEventListener('click', () => {
            const isCollapsed = navLinks.classList.toggle('collapsed');
            navMobileToggle.innerText = isCollapsed ? '展開 ▼' : '收合 ▲';
        });
        
        // Auto-close menu when a link is clicked on mobile
        document.querySelectorAll('.nav-tab-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                if (window.innerWidth <= 800 && !navLinks.classList.contains('collapsed')) {
                    navLinks.classList.add('collapsed');
                    navMobileToggle.innerText = '展開 ▼';
                }
            });
        });
    }

    // 9. Collapsible Explanations Accordion Transform
    function makeExplanationsCollapsible() {
        document.querySelectorAll('.doc-explanation ul').forEach(ul => {
            ul.querySelectorAll('li').forEach(li => {
                const strong = li.querySelector('strong');
                if (strong) {
                    const termHtml = strong.outerHTML;
                    
                    // Clone and remove strong element to get explanation content
                    const clone = li.cloneNode(true);
                    const cloneStrong = clone.querySelector('strong');
                    if (cloneStrong) cloneStrong.remove();
                    
                    let contentHtml = clone.innerHTML.trim();
                    
                    // Clean up leading colons or spacing
                    if (contentHtml.startsWith('：') || contentHtml.startsWith(':')) {
                        contentHtml = contentHtml.substring(1).trim();
                    }
                    
                    // Construct beautiful collapsible details structure
                    li.innerHTML = `
                        <details class="explanation-details">
                            <summary class="explanation-summary">
                                <span class="explanation-term">${termHtml}</span>
                            </summary>
                            <div class="explanation-content">${contentHtml}</div>
                        </details>
                    `;
                }
            });
        });
    }

    if (document.readyState === 'loading') {
        window.addEventListener('DOMContentLoaded', makeExplanationsCollapsible);
    } else {
        makeExplanationsCollapsible();
    }

    // 10. Hash routing listener
    function handleHashRouting() {
        const hash = window.location.hash.substring(1);
        
        if (!hash) {
            if (activePageId !== 'page01') switchPage('page01');
            return;
        }

        const matchedPage = ['page01', 'page02', 'page03', 'page04', 'page05', 'page06', 'page07', 'page08', 'page09', 'page10', 'page11', 'page12'].find(p => hash.startsWith(p));
        if (matchedPage) {
            if (activePageId !== matchedPage) {
                switchPage(matchedPage);
                setTimeout(() => {
                    const target = document.getElementById(hash);
                    if (target) target.scrollIntoView();
                }, 50);
            }
        } else {
            if (activePageId !== 'page01') switchPage('page01');
        }
    }
    
    window.addEventListener('hashchange', handleHashRouting);
    window.addEventListener('DOMContentLoaded', () => {
        initGlobalSearchIndex();
        handleHashRouting();
    });
</script>

<script async src="//busuanzi.ibruce.info/busuanzi/2.3/busuanzi.pure.mini.js"></script>
</body>
</html>"""

# Merge compiled markdown contents into template
final_html = portal_template.replace('__HTML_BODY_PAGE01__', html_body_p1)
final_html = final_html.replace('__HTML_BODY_PAGE02__', html_body_p2)
final_html = final_html.replace('__HTML_BODY_PAGE03__', html_body_p3)
final_html = final_html.replace('__HTML_BODY_PAGE04__', html_body_p4)
final_html = final_html.replace('__HTML_BODY_PAGE05__', html_body_p5)
final_html = final_html.replace('__HTML_BODY_PAGE06__', html_body_p6)
final_html = final_html.replace('__HTML_BODY_PAGE07__', html_body_p7)
final_html = final_html.replace('__HTML_BODY_PAGE08__', html_body_p8)
final_html = final_html.replace('__HTML_BODY_PAGE09__', html_body_p9)
final_html = final_html.replace('__HTML_BODY_PAGE10__', html_body_p10)
final_html = final_html.replace('__HTML_BODY_PAGE11__', html_body_p11)
final_html = final_html.replace('__HTML_BODY_PAGE12__', html_body_p12)

# Insert last update dates for each page into the JS metadata
final_html = final_html.replace('__PAGE01_DATE__', get_file_last_update_date(file_p1))
final_html = final_html.replace('__PAGE02_DATE__', get_file_last_update_date(file_p2))
final_html = final_html.replace('__PAGE03_DATE__', get_file_last_update_date(file_p3))
final_html = final_html.replace('__PAGE04_DATE__', get_file_last_update_date(file_p4))
final_html = final_html.replace('__PAGE05_DATE__', get_file_last_update_date(file_p5))
final_html = final_html.replace('__PAGE06_DATE__', get_file_last_update_date(file_p6))
final_html = final_html.replace('__PAGE07_DATE__', get_file_last_update_date(file_p7))
final_html = final_html.replace('__PAGE08_DATE__', get_file_last_update_date(file_p8))
final_html = final_html.replace('__PAGE09_DATE__', get_file_last_update_date(file_p9))
final_html = final_html.replace('__PAGE10_DATE__', get_file_last_update_date(file_p10))
final_html = final_html.replace('__PAGE11_DATE__', get_file_last_update_date(file_p11))
final_html = final_html.replace('__PAGE12_DATE__', get_file_last_update_date(file_p12))

# Write to file
print("Writing build output to index.html...")
with open(r'index.html', 'w', encoding='utf-8') as f:
    f.write(final_html)

# Generate sitemap.xml for SEO
from datetime import date
today = date.today().isoformat()

sitemap_content = f"""\
<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://ludwicia.github.io/ludwica-history-lesson/</loc>
    <lastmod>{today}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>1.0</priority>
  </url>
  <url>
    <loc>https://ludwicia.github.io/ludwica-history-lesson/#page01</loc>
    <lastmod>{today}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.9</priority>
  </url>
  <url>
    <loc>https://ludwicia.github.io/ludwica-history-lesson/#page02</loc>
    <lastmod>{today}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.8</priority>
  </url>
  <url>
    <loc>https://ludwicia.github.io/ludwica-history-lesson/#page03</loc>
    <lastmod>{today}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.8</priority>
  </url>
  <url>
    <loc>https://ludwicia.github.io/ludwica-history-lesson/#page04</loc>
    <lastmod>{today}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.8</priority>
  </url>
  <url>
    <loc>https://ludwicia.github.io/ludwica-history-lesson/#page05</loc>
    <lastmod>{today}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.8</priority>
  </url>
  <url>
    <loc>https://ludwicia.github.io/ludwica-history-lesson/#page06</loc>
    <lastmod>{today}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.8</priority>
  </url>
  <url>
    <loc>https://ludwicia.github.io/ludwica-history-lesson/#page07</loc>
    <lastmod>{today}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.8</priority>
  </url>
  <url>
    <loc>https://ludwicia.github.io/ludwica-history-lesson/#page08</loc>
    <lastmod>{today}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.8</priority>
  </url>
  <url>
    <loc>https://ludwicia.github.io/ludwica-history-lesson/#page09</loc>
    <lastmod>{today}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.8</priority>
  </url>
  <url>
    <loc>https://ludwicia.github.io/ludwica-history-lesson/#page10</loc>
    <lastmod>{today}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.8</priority>
  </url>
  <url>
    <loc>https://ludwicia.github.io/ludwica-history-lesson/#page11</loc>
    <lastmod>{today}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.8</priority>
  </url>
  <url>
    <loc>https://ludwicia.github.io/ludwica-history-lesson/#page12</loc>
    <lastmod>{today}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.8</priority>
  </url>
</urlset>"""

with open(r'sitemap.xml', 'w', encoding='utf-8', newline='\n') as f:
    f.write(sitemap_content)
print("Generated sitemap.xml")

# Generate robots.txt for SEO
robots_content = """User-agent: *
Allow: /

Sitemap: https://ludwicia.github.io/ludwica-history-lesson/sitemap.xml
"""

with open(r'robots.txt', 'w', encoding='utf-8') as f:
    f.write(robots_content)
print("Generated robots.txt")

print("Done! Site successfully built as dynamic 12-topic history portal with full SEO.")
