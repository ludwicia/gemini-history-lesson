import markdown
import re
import os
import subprocess
from datetime import datetime

# Helper to automatically format raw http/https links as markdown links
def make_urls_clickable(text):
    # Match standard HTTP/HTTPS URLs not already inside a markdown link or HTML attribute
    # Negative lookbehind: (?<![("<=])
    # URL pattern: https?://[a-zA-Z0-9\-._~:/?#\[\]@!$&'()*+,;=%]+
    url_pattern = r'(?<![("<=])(https?://[a-zA-Z0-9\-._~:/?#\[\]@!$&\'()*+,;=%]+)'
    return re.sub(url_pattern, r'[\1](\1)', text)

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
    text = make_urls_clickable(text)

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

    # Automatically convert standard markdown images to the custom figure layout
    # Match: <p><img alt="caption" src="url" /></p>
    md_img_pattern = r'<p>\s*<img\s+alt="([^"]*)"\s+src="([^"]*)"\s*/>\s*</p>'
    figure_replacement = r'<figure class="image-left"><img src="\2" alt="\1" loading="lazy"><figcaption class="caption">\1</figcaption></figure>'
    html_body = re.sub(md_img_pattern, figure_replacement, html_body)

    return html_body

def process_3col_document(file_path, content_version):
    update_date = get_file_last_update_date(file_path)
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
        text = make_urls_clickable(text)
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
file_p1 = r'course/帝國海洋、金融先驅與當代政治僵局：荷蘭建國史、東印度公司興衰與當代地緣政經轉型研究報告.md'
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
file_p2 = r'course/第一階段：三個世界的交會與前哥倫布時期的美洲（1607年以前）.md'
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
file_p3 = r'course/信仰衝突、軍事變革與波希米亞國家認同：胡斯戰爭的歷史脈絡、演進特徵與深遠影響研究報告.md'
map_p3 = '<figure class="image-left" style="width: 38%; margin-bottom: 20px;"><img src="images/hussite_wars_main.png" alt="Hussite Wars" loading="lazy"><figcaption class="caption">捷克歷史藝術家 Luděk Marold 著名巨作《利帕尼戰役全景圖》（Maroldovo panorama bitvy u Lipan），生動重現了這場終結激進派的史詩決戰</figcaption></figure>\n'
images_p3 = [
    (r'(<h2.*?>一、.*?</h2>)', 'images/jan_hus_preaching.png', '1563年布拉格印製的《胡斯講道集》（Postilla）中極具歷史意義的木刻版畫，記錄了揚·胡斯向波希米亞平民大眾宣教的經典場景'),
    (r'(<\/p>\s*<p>1414年，神聖羅馬帝國國王西吉斯蒙德)', 'images/jan_hus_execution.jpg', '歷史文獻插圖：上方描繪揚·胡斯在康斯坦茨被戴上寫有「異端首領」主教冠押赴火刑，下方描繪信徒用手推車收集其骨灰撒入萊茵河以防遺骨成為聖物，出自著名的《康斯坦茨公會議編年史》（Chronik des Konstanzer Konzils）'),
    (r'(<h2.*?>三、.*?</h2>)', 'images/hussite_crusade_battle.png', '源自15世紀末捷克國寶級手稿《耶拿法典》（Jena Codex）的著名插圖，展現高舉聖杯紅旗前仆後繼、行軍禦敵的胡斯派戰士們'),
    (r'(<h2.*?>四、.*?</h2>)', 'images/hussite_wagenburg.png', '歷史文獻中記載的經典「戰車壘」（Wagenburg）野戰工事與早期火炮協同防禦防線的精細還原圖')
]

# Page 5 (Hirsau Abbey) Config
file_p5 = r'course/希爾紹修道院研究報告：雙軌解析.md'
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
file_p7 = r'course/奧托-薩利安帝國教會體制.md'
map_p7 = '<figure class="image-left" style="width: 38%; margin-bottom: 20px;"><img src="images/ottonian_hre_map.svg" alt="Ottonian HRE Map" loading="lazy"><figcaption class="caption">西元1000年左右奧托-薩利安王朝時期的神聖羅馬帝國地圖，呈現德意志各部落公爵領與主教區錯綜複雜的疆域分佈</figcaption></figure>\n'
images_p7 = [
    (r'(<h2.*?>關鍵歷史人物與王權的神聖化重塑</h2>)', 'images/ottonian_otto1.jpg', '德國馬格德堡著名雕塑《馬格德堡騎馬人》（Magdeburger Reiter），生動展現了神聖羅馬帝國皇帝奧托一世的威嚴之姿'),
    (r'(<p>在奧托一世的統治後期，其胞弟科隆大主教布魯諾)', 'images/ottonian_bruno.jpg', '科隆聖潘塔萊翁修道院大教堂外的布魯諾大主教雕像，他將教會改革、宮廷教堂人才培養與國家行政體系進行了深度的歷史性融合'),
    (r'(<h3.*?>巡迴朝廷與空間動態治理</h3>)', 'images/ottonian_goslar.jpg', '宏偉的戈斯拉爾帝國皇室行宮（Kaiserpfalz Goslar），由皇帝亨利三世建造，是薩利安王朝巡迴朝廷與政治中樞的核心後勤與行政基地之一'),
    (r'(<h2.*?>內部矛盾：政教合一的內耗與改革運動的興起</h2>)', 'images/ottonian_canossa.jpg', '德國歷史畫家 Eduard Schwoiser 經典油畫巨作《亨利前進卡諾莎》（Heinrich vor Canossa），生動再現了皇帝亨利四世向教宗格列高利七世低頭乞求赦免的史詩場景')
]

# Page 8 (Concordat of Worms) Config
file_p8 = r'course/沃姆斯協約.md'

# Page 9 (Pippin's Donation) Config
file_p9 = r'course/丕平獻土的地緣政治體系研究：背景、權力機制、法理偽造與深遠歷史影響.md'
map_p9 = '<figure class="image-left" style="width: 38%; margin-bottom: 20px;"><img src="images/pippin_donation_main.jpg" alt="Pippin Coronation Main" loading="lazy"><figcaption class="caption">法國畫家 François Dubois 於1837年所繪的名作《教宗斯德望二世在聖但尼修道院為丕平加冕》，現藏於凡爾賽宮。</figcaption></figure>\n'
images_p9 = [
    (r'(<h2.*?>三、.*?</h2>)', 'images/pippin_donation_map.png', '西元750年代倫巴底擴張前夕的義大利半島地緣版圖。丕平獻土徹底打破了拜占庭、倫巴底與羅馬聖座之間的三方平衡。'),
    (r'(<h2.*?>五、.*?</h2>)', 'images/pippin_ricci_fresco.jpg', '梵蒂岡祕密檔案館壁畫：描繪法蘭克聖但尼修道院院長富拉德代表國王丕平，實地向教宗斯德望二世呈交收復的22座城市鑰匙與獻土詔書。'),
    (r'(<h2.*?>四、.*?</h2>)', 'images/donation_of_constantine.jpg', '梵蒂岡拉斐爾畫室著名濕壁畫《君士坦丁的贈禮》（Donation of Constantine），描繪君士坦丁大帝將世俗統治權讓渡給教宗西爾維斯特一世。')
]

# Page 10 (Carolingian Education) Config
file_p10 = r'course/聖神統治與知識復興：卡洛林王朝教育基建、制度體系及其深遠歷史遺產之研究.md'
map_p10 = '<figure class="image-left" style="width: 38%; margin-bottom: 20px;"><img src="images/carolingian_main.jpg" alt="Carolingian Minuscule" loading="lazy"><figcaption class="caption">八世紀末《達古爾夫詩篇》（Dagulf Psalter）之手抄頁面，以優美典雅的卡洛林小寫體金字書寫，展現了早期帝國書寫標準化的極致美學。</figcaption></figure>\n'
images_p10 = [
    (r'(<h2.*?>一、.*?</h2>)', 'images/carolingian_alcuin.jpg', 'Jean-Victor Schnetz 1830年名作《查理曼與阿爾琴》，描繪校長阿爾琴向查理曼大帝及其高級廷臣展示由修士手抄之聖經文獻，象徵神聖王權與知識基建之交匯。'),
    (r'(<h2.*?>二、.*?</h2>)', 'images/carolingian_stgall.jpg', '公元九世紀初著名的《聖加侖修道院理想平面圖》（St. Galler Klosterplan）局部，圖中明確規劃了專屬的圖書館（Library）與手抄室（Scriptorium）空間，展現出高度系統化的學術基建思維。'),
    (r'(<h2.*?>三、.*?</h2>)', 'images/carolingian_lorsch.jpg', '著名的卡洛林晚期傑作——洛爾施修道院門樓（Königshalle），是極少數完整存世的卡洛林帝國時期地標建築，展現了早期文藝復興的建築工程美學與古典柱頭裝飾。'),
    (r'(<h2.*?>四、.*?</h2>)', 'images/carolingian_majesty.jpg', '現藏於維多利亞與阿爾伯特博物館的十一世紀早期《洛爾施福音書》（Lorsch Gospels）象牙浮雕封面，描繪「基督登基在天」（Christ in Majesty），象徵宗教神權與卡洛林神學宇宙秩序的高度統一。')
]

# Page 11 (European Papermaking) Config
file_p11 = r'course/歐洲造紙術的歷史演變、技術革新與物質文明變革研究報告.md'
map_p11 = '<figure class="image-left" style="width: 38%; margin-bottom: 20px;"><img src="images/paper_main.jpg" alt="Jost Amman Papermaker" loading="lazy"><figcaption class="caption">德意志著名藝術家 Jost Amman 於1568年繪製的經典木刻版畫《撈紙工》（Der Papiermacher），生動再現了前工業化時期歐洲水力造紙坊抄紙與壓榨水分的勞動場景。</figcaption></figure>\n'
images_p11 = [
    (r'(<h2.*?>二、.*?</h2>)', 'images/paper_hollander.jpg', '保存於造紙歷史博物館中的經典「荷蘭式打漿機」（Hollander Beater），其藉由旋轉金屬刀片進行碎布纖維的原纖化處理，徹底革新了沿用數百年的槌擊製漿工藝。'),
    (r'(<h2.*?>四、.*?</h2>)', 'images/paper_press.jpg', '近代早期典型的木製手搖印刷機與造紙槽協同車間，造紙與印刷兩大技術的物質相遇，徹底打破了中古教權對知識產權與書籍生產的絕對壟斷。'),
    (r'(<h3.*?>2\..*?</h3>)', 'images/paper_gutenberg.jpg', '紐約公共圖書館珍藏的1455年《古騰堡聖經》（Gutenberg Bible）雙欄手繪頁面，採用了歐洲本土製造的高規格破布手抄紙，為印刷資本主義的擴張提供了最為關鍵的物質載體。')
]

# Page 12 (Catharism) Config
file_p12 = r'course/靈魂的物質禁錮與中世紀權力整肅：卡特里派的興起、神學教義、十字軍聖戰與歷史餘音.md'
map_p12 = '<figure class="image-left" style="width: 38%; margin-bottom: 20px;"><img src="images/catharism_main.jpg" alt="Montsegur Castle" loading="lazy"><figcaption class="caption">今日聳立於南法陡峭岩峰上的蒙塞居爾城堡（Château de Montségur）廢墟，曾是卡特里派最後的軍事與精神堡壘，見證了1244年悲壯的圍城戰與大火刑。</figcaption></figure>\n'
images_p12 = [
    (r'(<h2.*?>二、.*?</h2>)', 'images/catharism_creed.png', '代表朗格多克文化與卡特里派信仰空間的「奧克十字」（Occitan Cross）標誌，象徵南方反抗北法集權與教權威脅的文化精神'),
    (r'(<h2.*?>四、.*?</h2>)', 'images/catharism_perfecti.jpg', '西班牙畫家 Pedro Berruguete 於15世紀末所繪名作《聖多明尼克與阿爾比派》（St Dominic and the Albigenses），描繪正統與異端書籍被投入火中檢驗真偽的傳奇場景'),
    (r'(<h2.*?>五、.*?</h2>)', 'images/catharism_crusade.jpg', '15世紀手稿《Boucicaut大師工坊》插圖，描繪阿爾比十字軍東征期間卡特里派信徒被驅逐出城的悲慘場景'),
    (r'(<h2.*?>六、.*?</h2>)', 'images/catharism_inquisition.jpg', '14世紀道明會士 Bernard Gui 所著《異端裁判所實踐指南》（Practica officii inquisitionis heretice pravitatis）手稿插圖，象徵宗教裁判所官僚化、秘密化的司法清洗')
]

# Page 13 (USA Phase 2) Config
file_p13 = r'course/第二階段：殖民地的建立、定居與大西洋世界的形塑（1607年－1754年）.md'
map_p13 = '<figure class="image-left" style="width: 38%; margin-bottom: 20px;"><img src="images/us2_map.jpg" alt="Thirteen Colonies Map" loading="lazy"><figcaption class="caption">北美十三殖民地政區與地理分布圖，展示了新英格蘭、中部及南方三大區域殖民地結構與地緣疆界。</figcaption></figure>\n'
images_p13 = [
    (r'(<h2.*?>一、.*?</h2>)', 'images/us2_mayflower.jpg', '威廉·哈爾薩爾 1882 年名作《普利茅斯港的五月花號》（Mayflower in Plymouth Harbor），描繪清教徒乘坐五月花號抵達新大陸的歷史性場景。'),
    (r'(<h3.*?>2\.\s*中部殖民地.*?</h3>)', 'images/us2_penn_treaty.jpg', '班傑明·韋斯特名作《賓與印地安人的條約》（Penn\'s Treaty with the Indians），描繪貴格會領袖威廉·賓在沙卡馬克森與德拉瓦原住民簽訂土地交易條約的和平場景。'),
    (r'(<h3.*?>1\.\s*1676年「培根叛亂」.*?</h3>)', 'images/us2_bacons_rebellion.jpg', '插畫家霍華德·派爾（Howard Pyle）所繪《詹姆斯鎮的焚毀》，生動描繪了 1676 年培根叛亂中叛軍縱火燒毀弗吉尼亞首府詹姆斯鎮的慘烈場面。'),
    (r'(<h3.*?>1\.\s*新英格蘭地區的.*?</h3>)', 'images/us2_king_philip.jpg', '保羅·里維爾於 1772 年創作的經典銅版畫《蒙特霍普 sachem 菲利普王》，象徵殖民地時期對萬帕諾亞格盟主麥達康（Metacom）的經典想像刻畫。'),
    (r'(<h3.*?>3\.\s*法屬路易斯安那的建立與「密西西比泡沫」.*?</h3>)', 'images/us2_john_law.jpg', '阿列克謝·西蒙·貝爾繪製的《約翰·勞肖像》，他是蘇格蘭金融家與密西西比泡沫的策劃者，其金融泡沫對法屬路易斯安那的命運產生了深遠震盪。')
]
# Page 14 (British Constitution) Config
file_p14 = r'course/英國憲法的歷史演進、修訂機制與憲政奇異性：非法典化體制的理論與實踐研析.md'
map_p14 = '<figure class="image-left" style="width: 38%; margin-bottom: 20px;"><img src="images/uk_constitution_main.png" alt="British Constitution" loading="lazy"><figcaption class="caption">英國憲政主題經典圖畫，展現大憲章羊皮紙、皇家王冠與遠景的西敏寺國會大廈，象徵君主、法律與議會的權力交織。</figcaption></figure>\n'
images_p14 = [
    (r'(<h2.*?>歷史起源與漸進式沿革：從封建契約到議會至上</h2>)', 'images/uk_constitution_magna_carta.png', '西元1215年約翰王在倫德米德草地上被迫於貴族面前簽署《大憲章》的歷史想像圖。'),
    (r'(<h2.*?>英國憲法的奇特之處：政治憲政主義與雙重結構的張力</h2>)', 'images/uk_constitution_glorious_revolution.png', '西元1689年國會向威廉三世與瑪麗二世呈遞《權利法案》以確立國會主權的歷史繪畫。')
]

# Page 15 Config
file_p15 = r'course/聖職與婚娶：基督宗教神職人員生育、婚姻與財產繼承的歷史演變與政權博弈.md'
images_p15 = []


print("Processing Page 1 (Holland)...")
html_body_p1 = process_markdown(file_p1, images_p1, "1.1", map_p1)

print("Processing Page 2 (USA)...")
html_body_p2 = process_markdown(file_p2, images_p2, "1.0", map_p2)

print("Processing Page 3 (Hussite)...")
html_body_p3 = process_markdown(file_p3, images_p3, "1.0", map_p3)

print("Processing Page 4 (Golden Bull)...")
file_p4 = r'course/4.金璽詔書.md'
html_body_p4 = process_3col_document(file_p4, "1.7")

print("Processing Page 5 (Hirsau Abbey)...")
html_body_p5 = process_markdown(file_p5, images_p5, "1.0", map_p5)

print("Processing Page 6 (Benedict Rule)...")
file_p6 = r'course/5.聖本篤會規.md'
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

print("Processing Page 13 (USA Phase 2)...")
html_body_p13 = process_markdown(file_p13, images_p13, "1.0", map_p13)

print("Processing Page 14 (British Constitution)...")
html_body_p14 = process_markdown(file_p14, images_p14, "1.0", map_p14)

print("Processing Page 15 (Clergy Marriage)...")
html_body_p15 = process_markdown(file_p15, images_p15, "1.0", None)

# Parse worklog.md for the latest 10 updates
worklog_html = ""
try:
    with open('worklog.md', 'r', encoding='utf-8') as f:
        worklog_lines = f.readlines()
    
    updates = []
    current_update = None
    
    for line in worklog_lines:
        if line.startswith('#### '):
            if current_update:
                updates.append(current_update)
                if len(updates) >= 10:
                    break
            current_update = {'title': line[5:].strip(), 'items': []}
        elif line.startswith('- ') and current_update is not None:
            html_item = line[2:].strip()
            html_item = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', html_item)
            current_update['items'].append(html_item)
    
    if current_update and len(updates) < 10:
        updates.append(current_update)
        
    for update in updates:
        worklog_html += f'<div class="update-entry"><div class="update-date">{update["title"]}</div><ul class="update-list">'
        for item in update['items']:
            worklog_html += f'<li>{item}</li>'
        worklog_html += '</ul></div>'
except Exception as e:
    worklog_html = f"<p>Error loading worklog: {e}</p>"

article_cards_html = f"""
<div class="article-grid">
    <div class="article-card" onclick="location.hash='#page01'">
        <div class="card-image" style="background-image: url('images/img_12_960px-Seven_United_Netherlands_Janssonius_1658.jpg');"></div>
        <div class="card-content">
            <div class="card-title">荷蘭建國與地緣政經</div>
            <div class="card-meta">內容版本：1.1</div>
        </div>
    </div>
    <div class="article-card" onclick="location.hash='#page02'">
        <div class="card-image" style="background-image: url('images/img_10_960px-Cahokia_Monks_Mound.jpg');"></div>
        <div class="card-content">
            <div class="card-title">美國的誕生(一)</div>
            <div class="card-meta">內容版本：1.0</div>
        </div>
    </div>
    <div class="article-card" onclick="location.hash='#page13'">
        <div class="card-image" style="background-image: url('images/us2_map.jpg');"></div>
        <div class="card-content">
            <div class="card-title">美國的誕生(二)</div>
            <div class="card-meta">內容版本：1.0</div>
        </div>
    </div>
    <div class="article-card" onclick="location.hash='#page03'">
        <div class="card-image" style="background-image: url('images/hussite_wars_main.png');"></div>
        <div class="card-content">
            <div class="card-title">宗教戰爭(一)：胡斯戰爭</div>
            <div class="card-meta">內容版本：1.0</div>
        </div>
    </div>
    <div class="article-card" onclick="location.hash='#page12'">
        <div class="card-image" style="background-image: url('images/catharism_main.jpg');"></div>
        <div class="card-content">
            <div class="card-title">宗教戰爭(二)：卡特里派</div>
            <div class="card-meta">內容版本：1.0</div>
        </div>
    </div>
    <div class="article-card" onclick="location.hash='#page05'">
        <div class="card-image" style="background-image: url('images/hirsau_main_wilhelm.jpg');"></div>
        <div class="card-content">
            <div class="card-title">希爾紹修道院</div>
            <div class="card-meta">內容版本：1.0</div>
        </div>
    </div>
    <div class="article-card" onclick="location.hash='#page07'">
        <div class="card-image" style="background-image: url('images/ottonian_hre_map.svg');"></div>
        <div class="card-content">
            <div class="card-title">奧托-薩利安帝國教會體制</div>
            <div class="card-meta">內容版本：1.0</div>
        </div>
    </div>
    <div class="article-card" onclick="location.hash='#page09'">
        <div class="card-image" style="background-image: url('images/pippin_donation_main.jpg');"></div>
        <div class="card-content">
            <div class="card-title">丕平獻土與教皇國誕生</div>
            <div class="card-meta">內容版本：1.0</div>
        </div>
    </div>
    <div class="article-card" onclick="location.hash='#page10'">
        <div class="card-image" style="background-image: url('images/carolingian_main.jpg');"></div>
        <div class="card-content">
            <div class="card-title">卡洛林教育基建與知識復興</div>
            <div class="card-meta">內容版本：1.0</div>
        </div>
    </div>
    <div class="article-card" onclick="location.hash='#page11'">
        <div class="card-image" style="background-image: url('images/paper_main.jpg');"></div>
        <div class="card-content">
            <div class="card-title">歐洲造紙術的歷史演變</div>
            <div class="card-meta">內容版本：1.0</div>
        </div>
    </div>
    <div class="article-card" onclick="location.hash='#page14'">
        <div class="card-image" style="background-image: url('images/uk_constitution_main.png');"></div>
        <div class="card-content">
            <div class="card-title">英國的憲法</div>
            <div class="card-meta">內容版本：1.0</div>
        </div>
    </div>
    <div class="article-card" onclick="location.hash='#page15'">
        <div class="card-image" style="background-color: #e2e8f0;"></div>
        <div class="card-content">
            <div class="card-title">聖職與婚娶</div>
            <div class="card-meta">內容版本：1.0</div>
        </div>
    </div>
    
    <div class="card-section-title" style="grid-column: 1 / -1; margin-top: 20px; font-size: 1.2rem; font-weight: 700; border-bottom: 2px solid #e2e8f0; padding-bottom: 10px;">歷史文件專區</div>
    
    <div class="article-card doc-card" onclick="location.hash='#page04'">
        <div class="card-content">
            <div class="card-title">神聖羅馬帝國：金璽詔書</div>
            <div class="card-meta">內容版本：1.6</div>
        </div>
    </div>
    <div class="article-card doc-card" onclick="location.hash='#page06'">
        <div class="card-content">
            <div class="card-title">修道院制度：聖本篤會規</div>
            <div class="card-meta">內容版本：2.0</div>
        </div>
    </div>
    <div class="article-card doc-card" onclick="location.hash='#page08'">
        <div class="card-content">
            <div class="card-title">敘任權之爭：沃姆斯協約</div>
            <div class="card-meta">內容版本：1.0</div>
        </div>
    </div>
</div>
"""

# Full Portal HTML Template
with open("template.html", "r", encoding="utf-8") as f:
    portal_template = f.read()

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
final_html = final_html.replace('__HTML_BODY_PAGE13__', html_body_p13)
final_html = final_html.replace('__HTML_BODY_PAGE14__', html_body_p14)
final_html = final_html.replace('__HTML_BODY_PAGE15__', html_body_p15)
final_html = final_html.replace('__WORKLOG_HTML__', worklog_html)
final_html = final_html.replace('__ARTICLE_CARDS__', article_cards_html)

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
final_html = final_html.replace('__PAGE13_DATE__', get_file_last_update_date(file_p13))
final_html = final_html.replace('__PAGE14_DATE__', get_file_last_update_date(file_p14))
final_html = final_html.replace('__PAGE15_DATE__', get_file_last_update_date(file_p15))

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
  <url>
    <loc>https://ludwicia.github.io/ludwica-history-lesson/#page13</loc>
    <lastmod>{today}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.8</priority>
  </url>
  <url>
    <loc>https://ludwicia.github.io/ludwica-history-lesson/#page14</loc>
    <lastmod>{today}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.8</priority>
  </url>
  <url>
    <loc>https://ludwicia.github.io/ludwica-history-lesson/#page15</loc>
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

print("Done! Site successfully built as dynamic 14-topic history portal with full SEO.")
