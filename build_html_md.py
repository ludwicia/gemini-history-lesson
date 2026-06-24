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

def get_share_bar_html(page_id):
    if not page_id:
        return ""
    return f'''
<div class="share-bar">
    <span class="share-bar-title">分享文章：</span>
    <button class="share-btn share-btn-fb" onclick="shareTo('facebook', '{page_id}')">
        <svg viewBox="0 0 24 24"><path d="M22 12c0-5.52-4.48-10-10-10S2 6.48 2 12c0 4.84 3.44 8.87 8 9.8V15H8v-3h2V9.5C10 7.57 11.57 6 13.5 6H16v3h-2c-.55 0-1 .45-1 1v2h3v3h-3v6.95c4.56-.93 8-4.96 8-9.75z"/></svg>
        <span class="share-text">Facebook</span>
    </button>
    <button class="share-btn share-btn-line" onclick="shareTo('line', '{page_id}')">
        <svg viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 5.82 2 10.53c0 2.75 1.51 5.2 3.93 6.75-.15.54-.53 1.95-.6 2.22-.09.33.1.32.22.24.26-.16 4.04-2.67 4.6-3.05.6.11 1.22.17 1.85.17 5.52 0 10-3.82 10-8.53C22 5.82 17.52 2 12 2z"/></svg>
        <span class="share-text">LINE</span>
    </button>
    <button class="share-btn share-btn-x" onclick="shareTo('twitter', '{page_id}')">
        <svg viewBox="0 0 24 24"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/></svg>
        <span class="share-text">X (Twitter)</span>
    </button>
    <button class="share-btn share-btn-copy" onclick="shareTo('copy', '{page_id}')">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>
        <span class="share-text">複製連結</span>
    </button>
</div>
'''

# Helper to process and format a markdown lesson
def process_markdown(file_path, image_replacements, content_version, main_img_html=None, page_id=None):
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

    # Insert version badge, sharing buttons, and main image under first H1
    header_insert = version_badge
    if page_id:
        header_insert += get_share_bar_html(page_id)
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
    def img_replace(match):
        alt = match.group(1)
        src = match.group(2)
        if "ad_calendar_eq_" in src:
            return f'\n<figure class="image-center" style="width: 100%; max-width: 520px; float: none; margin: 25px auto; padding: 0; box-shadow: none; border: none; background: none;"><img src="{src}" alt="{alt}" loading="lazy" style="box-shadow: 0 4px 12px rgba(0,0,0,0.04); border: 1px solid #e2e8f0; border-radius: 8px; width: 100%; height: auto;"></figure>\n'
        return f'<figure class="image-left"><img src="{src}" alt="{alt}" loading="lazy"><figcaption class="caption">{alt}</figcaption></figure>'
    html_body = re.sub(md_img_pattern, img_replace, html_body)

    if page_id:
        html_body += get_share_bar_html(page_id)

    return html_body

def process_3col_document(file_path, content_version, page_id=None, lang_orig="德文", cols=3):
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
    '''
    if page_id:
        html += get_share_bar_html(page_id)

    container_class = "doc-3col-container" if cols == 3 else "doc-3col-container doc-2col-container"
    html += f'''
    <div class="doc-title-section">
        {title_html}
    </div>
    <div class="{container_class}">
        <div class="doc-3col-header">
            <div class="doc-col-title">原文 ({lang_orig})</div>
            <div class="doc-col-title">譯文 (中文)</div>
    '''
    if cols == 3:
        html += f'''        <div class="doc-col-title">解釋 (筆記)</div>'''
    html += f'''
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
            '''
            if cols == 3:
                html += f'''    <div class="doc-col doc-explanation">{explanation_text}</div>'''
            html += f'''
            </div>
            '''
        else:
            html += f'''
            <div class="doc-3col-row full-width-row" style="grid-template-columns: 1fr;">
                <div class="doc-col" style="grid-column: 1 / -1;">{markdown.markdown(block)}</div>
            </div>
            '''
            
    html += "</div>"
    if page_id:
        html += get_share_bar_html(page_id)
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
map_p15 = '<figure class="image-left" style="width: 38%; margin-bottom: 20px;"><img src="images/clergy_trent.jpg" alt="The Council of Trent" loading="lazy"><figcaption class="caption">1588年帕斯卡爾·卡蒂繪製的著名壁畫《特倫托公會議》（The Council of Trent），現藏於羅馬聖母大公殿，象徵天主教會在宗教改革浪潮下對神職絕對獨身制與教義純潔性的確認與重申。</figcaption></figure>\n'
images_p15 = [
    (r'(<h2.*?>禁慾主義的先驅背景與早期教會的多元共存</h2>)', 'images/clergy_marriage_main.png', 'AI 歷史模擬示意圖：早期基督教會中與妻子及家人共同生活的已婚司鐸家庭，象徵三世紀前神職人員擁有婚姻與生育生活的多元接納常態（本圖為 AI 繪製示意）。'),
    (r'(<h2.*?>地方公會議的制度化律令與東西方分裂的先聲</h2>)', 'images/clergy_family_medieval.png', 'AI 歷史模擬示意圖：中世紀前期與地方莊園及土地繼承網絡緊密結合的已婚神職家庭，此類普遍存在的司鐸世襲化現象，在後期引發了天主教會極大的財產流失與教權危機（本圖為 AI 繪製示意）。'),
    (r'(<h2.*?>中世紀封建危機下的格列哥里改革與權力重塑</h2>)', 'images/clergy_canossa.jpg', '愛德華·施沃瑟1862年名作《亨利四世在卡諾莎》（Heinrich vor Canossa），描繪了公元1077年神聖羅馬帝國皇帝亨利四世在風雪中向教宗格列哥里七世悔罪的場景，象徵格列哥里改革中教權壓倒世俗王權的關鍵歷史時刻。'),
    (r'(<h2.*?>宗教改革的政治經濟學反叛與天主教會的反擊</h2>)', 'images/clergy_luther_bora.jpg', '路卡斯·克拉納赫1526年創作的《馬丁·路德與卡塔琳娜·馮·博拉雙聯畫》，現藏於瑞典國立博物館，生動描繪了這對倡導並實踐牧師婚姻的新教先驅夫婦，象徵宗教改革對修道院守貞誓言與世俗家庭價值的重構。')
]
# Page 16 Config
file_p16 = r'course/中世紀巡行王權的權力運作、制度體系與社會實態：以奧圖一世九五五年巡行與戰事為核心之歷史學考察.md'
map_p16 = '<figure class="image-left" style="width: 38%; margin-bottom: 20px;"><img src="images/reisekönig_travelling_kings.jpg" alt="Travelling Kings" loading="lazy"><figcaption class="caption">出自《法拉克薩手抄本》（Velaslav\'s Bible）的「旅行中的國王」手稿插圖，生動呈現了中世紀早中期君主與其宮廷在不同莊園行宮間物理性持續移動的「巡行王權」歷史情境。</figcaption></figure>\n'
images_p16 = [
    (r'(<h2.*?>巡行王權的特別之處、政治意義與統治功能</h2>)', 'images/ottonian_goslar.jpg', '宏偉的戈斯拉爾帝國皇室行宮（Kaiserpfalz Goslar），巡行朝廷在薩克森地區的權力象徵與核心行政基地。'),
    (r'(<h3.*?>協商式統治與個人化政治紐帶</h3>)', 'images/otto_quedlinburg_hoftag.jpg', '莫里茲·馮·施溫德所繪《奧圖一世於昆德林堡慶祝五旬節，973年》，生動描繪了君主與世俗、教會貴族齊聚召開帝國大會（Hoftag）的協商共識政治場景。'),
    (r'(<h3.*?>帝國教會體制與 monastic secularization 的張力</h3>)', 'images/ottonian_bruno.jpg', '科隆大主教布魯諾雕像，他作為奧圖一世之弟，將宮廷教堂人才培養與國家行政體系深度結合，成為帝國教會體制的奠基人。'),
    (r'(<h2.*?>奧圖一世九五五年巡行軌跡：歷史重建與戰略轉折</h2>)', 'images/michael_echter_ungarnschlacht.jpg', '麥可·埃希特繪製的歷史名畫《雷希菲爾德戰役》（Lechfeldschlacht），描繪了955年奧圖一世率領德意志聯軍衝鋒，決定性大敗馬扎爾人騎兵的史詩決戰。'),
    (r'(<h3.*?>農業剩餘與高度組織化的實物汲取</h3>)', 'images/mainzer_hoffest_assembly.jpg', '出自《薩克森世界編年史》手稿插圖，描繪了帝國大會期間為皇帝宮廷及各路貴族大軍提供飲食和物資的汲取網絡。')
]

# Page 17 Config
file_p17 = r'course/從戴克里先、君士坦丁到迪奧多西：從皇帝的稱號看歷史背景與政教關係的演變.md'
map_p17 = '<figure class="image-left" style="width: 38%; margin-bottom: 20px;"><img src="images/ambrose_and_theodosius.png" alt="Ambrose and Theodosius" loading="lazy"><figcaption class="caption">聖安波羅修在米蘭大教堂前阻擋皇帝迪奧多西一世的歷史想像圖，象徵世俗權力必須臣服於上帝的屬靈裁判，是政教關係史上的關鍵分水嶺。</figcaption></figure>\n'
images_p17 = [
    (r'(<h2.*?>戴克里先與君主制的創立：從「第一公民」到「君主與神」</h2>)', 'images/p17_tetrarchs.jpg', '威尼斯聖馬可大教堂牆角的「四帝共治」雕像（約公元300年），以四位皇帝互相擁抱象徵帝國的團結與分工，是戴克里先創立四帝共治制度的具體政治宣傳。'),
    (r'(<h2.*?>君士坦丁大帝的雙重神聖：大祭司與「外部事務主教」</h2>)', 'images/p17_constantine_head.jpg', '羅馬卡比托利歐博物館收藏 of 君士坦丁大帝青銅巨像頭部（約公元4世紀），其巨大的雙眼凝視著遠方，展現出晚期羅馬帝國君主超越凡人、神聖不可侵犯的專制權威。'),
    (r'(<h2.*?>格拉提安的信仰抉擇：拒絕「大祭司」與「榮譽祭司」的轉向</h2>)', 'images/p17_curia_julia.jpg', '位於羅馬廣場的庫里亞·朱利亞（羅馬元老院議事堂），格拉提安皇帝曾下令將其中的「勝利女神祭壇」拆除，徹底引發了傳統多神教精英與基督教主教的政論博弈。')
]

# Page 18 Config
file_p18 = r'course/西元紀年的確立與演進：從歷史考證、政治妥協到全球數位化時間標準的建構.md'
map_p18 = '<figure class="image-left" style="width: 38%; margin-bottom: 20px;"><img src="images/ad_calendar_main.png" alt="AD Calendar Main" loading="lazy"><figcaption class="caption">象徵時間流逝與曆法更迭的古典沙漏與天文鐘，折射出人類在時間測量上從神聖天啟走向世俗理性的演進歷程。</figcaption></figure>\n'
images_p18 = [
    (r'(<h2.*?>二、 關鍵歷史人物與行政推手：從修道院計算到國家法典</h2>)', 'images/carolingian_alcuin.jpg', '查理曼大帝的宮廷學者阿爾琴，他建議查理曼在行政詔書中強制實施西元紀年。'),
    (r'(<h2.*?>四、 東西方教會的分裂與對齊阻力：曆法體系的分歧與物理時差</h2>)', 'images/clergy_trent.jpg', '1588年帕斯卡爾·卡蒂繪製的著名壁畫《特倫托公會議》，象徵教會對時間體系的重構與絕對掌控。')
]

# Page 19 Config
file_p19 = r'course/帝國重塑、信仰博弈與權力終局：《米蘭敕令》時代的羅馬政治、君士坦丁宗教策略與李錫尼覆滅研究.md'
map_p19 = '<figure class="image-left" style="width: 38%; margin-bottom: 20px;"><img src="images/milan_edict_main.png" alt="Milan Edict Main" loading="lazy"><figcaption class="caption">君士坦丁與李錫尼於公元313年在米蘭會晤並達成協定，正式確立宗教寬容與信仰自由政策（本圖為 AI 模擬歷史繪畫）。</figcaption></figure>\n'
images_p19 = [
    (r'(<h3.*?>四帝共治制的權力結構與撕裂</h3>)', 'images/p17_tetrarchs.jpg', '威尼斯聖馬可大教堂外牆著名的「四帝共治」雕像（約公元300年），象徵戴克里先時期帝國的權力分工與秩序重塑。'),
    (r'(<h3.*?>塞巴斯蒂四十烈士：軍事整肅與信仰抗爭的微觀縮影</h3>)', 'images/forty_martyrs_sebaste.png', '公元320年冬，塞巴斯蒂四十烈士因拒絕向異教神祇獻祭而被強令站在冰封的湖面上受凍折磨，成為東部帝國著名的殉道史詩（本圖為 AI 模擬歷史繪畫）。'),
    (r'(<h3.*?>第二次內戰與李錫尼的末路（324–325年）</h3>)', 'images/battle_adrianople.png', '公元324年決戰中，君士坦丁的軍隊高舉繪有凱樂符號（Chi-Rho）的帝國軍旗與李錫尼的軍隊激烈交戰，標誌著內戰的最高潮與帝國政教體制的轉型（本圖為 AI 模擬歷史繪畫）。')
]

# Page 20 Config
file_p20 = r'course/米蘭敕令.md'

# Page 21 (Apostles' Creed) Config
file_p21 = r'course/使徒信經的歷史演變與神學建構：從早期羅馬洗禮宣誓到西方大公信仰奠基的學術研究報告.md'
map_p21 = '<figure class="image-left" style="width: 38%; margin-bottom: 20px;"><img src="images/creed_main.jpg" alt="Apostles Creed" loading="lazy"><figcaption class="caption">1493年出版的《牧人曆》（Compost et calendrier des bergers）插圖細節，描繪使徒們與各自創作的信經宣告條款，是中世紀傳統聖傳故事的經典圖解。</figcaption></figure>\n'
images_p21 = [
    (r'(<h3.*?>早期羅馬洗禮儀式與答問式信經的實踐</h3>)', 'images/creed_baptism.jpg', '義大利拉溫納著名的阿利烏派洗禮堂（Arian Baptistery）穹頂馬賽克（五世紀末），中心描繪了施洗約翰在約旦河為基督施行洗禮的場景，是早期答問式洗禮信經實踐的藝術寫照。'),
    (r'(<h3.*?>聖皮爾米紐斯與《備忘錄選集》的文本奠基</h3>)', 'images/creed_pirminius.jpg', '作於十世紀的《霍恩巴赫聖事書》（Hornbacher Sakramentar）插圖，描繪修道院院長阿達爾貝特向修道院創立者聖皮爾米紐斯呈交抄寫的聖經文獻，象徵修道院手抄室對大公信經文本標準化的奠基性貢獻。'),
    (r'(<h3.*?>加洛林王朝的帝國 correctio 運動與禮儀標準化</h3>)', 'images/carolingian_alcuin.jpg', '法國歷史畫家 Jean-Victor Schnetz 名作《查理曼與阿爾琴》，描繪學者阿爾琴向查理曼大帝展示修訂後的拉丁文手抄文獻，是加洛林道德修正運動與禮儀一統化歷史的生動描繪。')
]

# Page 22 (Odoacer) Config
file_p22 = r'course/羅馬秩序的終結與日耳曼王權的奠定：奧多亞賽的崛起、統治策略與政權覆滅.md'
map_p22 = '<figure class="image-left" style="width: 38%; margin-bottom: 20px;"><img src="images/odoacer_fall_rome.jpg" alt="Odoacer Fall of Rome" loading="lazy"><figcaption class="caption">Bernhard Mörlins 於 19 世紀所繪的歷史插圖，描繪西羅馬帝國最後的皇帝羅慕路斯·奧古斯都向日耳曼將領奧多亞賽讓渡皇冠的經典場景。</figcaption></figure>\n'
images_p22 = []

# Page 23 (Clovis) Config
file_p23 = r'course/蠻族崛起的政治重塑：法蘭克人的民族生成、羅馬遺產與克洛維一世的霸權奠基.md'
map_p23 = '<figure class="image-left" style="width: 38%; margin-bottom: 20px;"><img src="images/clovis_main.jpg" alt="Clovis I" loading="lazy"><figcaption class="caption">François-Louis Dejuinne 於 19 世紀所繪的法蘭克國王克洛維一世（Clovis I）畫像，現藏於凡爾賽宮，象徵墨洛溫王權的奠基。</figcaption></figure>\n'
images_p23 = []

# Page 24 (Roman Reforms & Colonate) Config
file_p24 = r'course/從戴克里先到君士坦丁：土地、稅制與兵役改革下的帝國控制與中世紀封建農奴的誕生.md'
map_p24 = '<figure class="image-left" style="width: 38%; margin-bottom: 20px;"><img src="images/roman_colonate_estate.png" alt="Late Roman Agricultural Estate" loading="lazy"><figcaption class="caption">4世紀羅馬帝國晚期莊園（Villa Rustica）示意圖：在剛性稅制與勞動力匱乏下，依附於土地的隸農（Coloni）正在莊園主的地盤上進行耕作，預示著中世紀封建農奴制的萌芽。</figcaption></figure>\n'
images_p24 = [
    (r'(<h2.*?>帝國晚期的多重危機與專制.*?</h2>)', 'images/p17_tetrarchs.jpg', '威尼斯聖馬可大教堂外牆著名的「四帝共治」雕像，以四位皇帝互相擁抱象徵帝國的團結與分工，是戴克里先創立四帝共治制度的具體政治宣傳。')
]

# Page 25 (Goths & Adrianople Battle) Config
file_p25 = r'course/帝國防線的內爆：從羅馬晚期改革、財政軍政演變與社會撕裂看哥德人之崛起.md'
map_p25 = '<figure class="image-left" style="width: 38%; margin-bottom: 20px;"><img src="images/adrianople_battle.png" alt="Battle of Adrianople" loading="lazy"><figcaption class="caption">西元378年阿德里安堡戰役示意圖：哥德人重騎兵發動猛烈衝鋒，徹底撕裂了羅馬帝國主力野戰軍的步兵防線，此戰被視為羅馬軍事史上最慘烈的敗仗之一。</figcaption></figure>\n'
images_p25 = []

# Page 26 (Alaric & Gothic Migrations) Config
file_p26 = r'course/阿拉里克與哥德大遷徙：晚期羅馬帝國的地緣政治坍塌與蠻族同盟的體制化適應（第一卷：永恆之城的終局）.md'
map_p26 = '<figure class="image-left" style="width: 38%; margin-bottom: 20px;"><img src="images/alaric_sack_rome.png" alt="Sack of Rome by Alaric" loading="lazy"><figcaption class="caption">西元410年西哥德人洗劫羅馬示意圖：蠻族國王阿拉里克率軍攻破羅馬城，開啟了西羅馬帝國政治與軍事體系不可逆轉的瓦解進程。</figcaption></figure>\n'
images_p26 = []

# Page 27 (Battle of the Frigidus) Config
file_p27 = r'course/羅馬帝國晚期的地緣政治斷裂與軍事赤字：冷河戰役及其歷史學再闡釋.md'
map_p27 = '<figure class="image-left" style="width: 38%; margin-bottom: 20px;"><img src="images/battle_of_frigidus.png" alt="Battle of the Frigidus" loading="lazy"><figcaption class="caption">冷河戰役（西元394年）想像圖：在極端的「波拉風」暴風肆虐下，東部皇帝狄奧多西一世的軍隊發動反攻，狂風將西軍的箭矢吹回其自身陣中，徹底扭轉了戰局。</figcaption></figure>\n'
images_p27 = []

# Page 28 Config
file_p28 = r'course/薩洛尼卡敕令.md'

# Page 29 Config
file_p29 = r'course/阿德里安堡戰役.md'
map_p29 = '<figure class="image-left" style="width: 38%; margin-bottom: 20px;"><img src="images/battle_of_adrianople.png" alt="Battle of Adrianople" loading="lazy"><figcaption class="caption">阿德里安堡戰役（西元378年）想像圖：哥特戰士與家眷依託環形相接的篷車陣進行防守，隨後大批哥特與阿蘭重騎兵如雷霆般突襲包抄，給予精疲力竭的羅馬軍團致命的一擊。</figcaption></figure>\n'
images_p29 = []

# Page 30 Config
file_p30 = r'course/蓋納斯：東羅馬的哥德野心家與早期拜占庭的蠻族權力危機.md'
map_p30 = '<figure class="image-left" style="width: 38%; margin-bottom: 20px;"><img src="images/gainas_byzantine.png" alt="Gainas Byzantine" loading="lazy"><figcaption class="caption">蓋納斯（Gainas）與拜占庭權力危機：早期東羅馬朝廷中，身披羅馬將領甲冑的哥特統帥蓋納斯與阿卡狄烏斯皇帝在殿前對峙，揭示出蠻族軍事干政與傳統官僚力量之間劍拔弩張的緊張張力。</figcaption></figure>\n'
images_p30 = []

# Page 31 Config
file_p31 = r'course/塞維魯王朝的權力、財政與法制變革：卡拉卡拉與《安東尼努斯敕令》的深度歷史研究.md'
map_p31 = '<figure class="image-left" style="width: 38%; margin-bottom: 20px;"><img src="images/caracalla_edict.png" alt="Caracalla Edict" loading="lazy"><figcaption class="caption">卡拉卡拉與《安東尼努斯敕令》：西元212年，羅馬皇帝卡拉卡拉頒布敕令，授予帝國所有自由民羅馬公民身份，這不僅重塑了羅馬身份認同，也藉此擴大了遺產稅等公民稅收稅基。</figcaption></figure>\n'
images_p31 = []

# Page 32 Config
file_p32 = r'course/安東尼努斯敕令.md'


print("Processing Page 1 (Holland)...")
html_body_p1 = process_markdown(file_p1, images_p1, "1.1", map_p1, page_id="page01")

print("Processing Page 2 (USA)...")
html_body_p2 = process_markdown(file_p2, images_p2, "1.0", map_p2, page_id="page02")

print("Processing Page 3 (Hussite)...")
html_body_p3 = process_markdown(file_p3, images_p3, "1.0", map_p3, page_id="page03")

print("Processing Page 4 (Golden Bull)...")
file_p4 = r'course/4.金璽詔書.md'
html_body_p4 = process_3col_document(file_p4, "1.9", page_id="page04")

print("Processing Page 5 (Hirsau Abbey)...")
html_body_p5 = process_markdown(file_p5, images_p5, "1.0", map_p5, page_id="page05")

print("Processing Page 6 (Benedict Rule)...")
file_p6 = r'course/5.聖本篤會規.md'
html_body_p6 = process_3col_document(file_p6, "2.0", page_id="page06")

print("Processing Page 7 (Ottonian System)...")
html_body_p7 = process_markdown(file_p7, images_p7, "1.0", map_p7, page_id="page07")

print("Processing Page 8 (Concordat of Worms)...")
html_body_p8 = process_3col_document(file_p8, "1.0", page_id="page08")

print("Processing Page 9 (Pippin Donation)...")
html_body_p9 = process_markdown(file_p9, images_p9, "1.1", map_p9, page_id="page09")

print("Processing Page 10 (Carolingian Education)...")
html_body_p10 = process_markdown(file_p10, images_p10, "1.0", map_p10, page_id="page10")

print("Processing Page 11 (European Papermaking)...")
html_body_p11 = process_markdown(file_p11, images_p11, "1.0", map_p11, page_id="page11")

print("Processing Page 12 (Cathar Crusade)...")
html_body_p12 = process_markdown(file_p12, images_p12, "1.0", map_p12, page_id="page12")

print("Processing Page 13 (USA Phase 2)...")
html_body_p13 = process_markdown(file_p13, images_p13, "1.0", map_p13, page_id="page13")

print("Processing Page 14 (British Constitution)...")
html_body_p14 = process_markdown(file_p14, images_p14, "1.0", map_p14, page_id="page14")

print("Processing Page 15 (Clergy Marriage)...")
html_body_p15 = process_markdown(file_p15, images_p15, "1.2", map_p15, page_id="page15")

print("Processing Page 16 (Ambulatory Kingship)...")
html_body_p16 = process_markdown(file_p16, images_p16, "1.0", map_p16, page_id="page16")

print("Processing Page 17 (Ambrose & Theodosius)...")
html_body_p17 = process_markdown(file_p17, images_p17, "1.0", map_p17, page_id="page17")

print("Processing Page 18 (AD Calendar)...")
html_body_p18 = process_markdown(file_p18, images_p18, "1.1", map_p18, page_id="page18")

print("Processing Page 19 (Milan Edict & Licinius)...")
html_body_p19 = process_markdown(file_p19, images_p19, "1.0", map_p19, page_id="page19")

print("Processing Page 20 (Milan Edict Document)...")
html_body_p20 = process_3col_document(file_p20, "1.0", page_id="page20", lang_orig="英文/拉丁文")

print("Processing Page 21 (Apostles' Creed)...")
html_body_p21 = process_markdown(file_p21, images_p21, "1.0", map_p21, page_id="page21")

print("Processing Page 22 (Odoacer)...")
html_body_p22 = process_markdown(file_p22, images_p22, "1.1", map_p22, page_id="page22")

print("Processing Page 23 (Clovis)...")
html_body_p23 = process_markdown(file_p23, images_p23, "1.0", map_p23, page_id="page23")

print("Processing Page 24 (Roman Reforms & Colonate)...")
html_body_p24 = process_markdown(file_p24, images_p24, "1.0", map_p24, page_id="page24")

print("Processing Page 25 (Goths & Adrianople Battle)...")
html_body_p25 = process_markdown(file_p25, images_p25, "1.0", map_p25, page_id="page25")

print("Processing Page 26 (Alaric & Gothic Migrations)...")
html_body_p26 = process_markdown(file_p26, images_p26, "1.1", map_p26, page_id="page26")

print("Processing Page 27 (Battle of the Frigidus)...")
html_body_p27 = process_markdown(file_p27, images_p27, "1.0", map_p27, page_id="page27")

print("Processing Page 28 (Thessalonica Edict Document)...")
html_body_p28 = process_3col_document(file_p28, "1.0", page_id="page28", lang_orig="拉丁文")

print("Processing Page 29 (Battle of Adrianople)...")
html_body_p29 = process_markdown(file_p29, images_p29, "1.0", map_p29, page_id="page29")

print("Processing Page 30 (Gainas Byzantine Crisis)...")
html_body_p30 = process_markdown(file_p30, images_p30, "1.0", map_p30, page_id="page30")

print("Processing Page 31 (Caracalla Edict)...")
html_body_p31 = process_markdown(file_p31, images_p31, "1.0", map_p31, page_id="page31")

print("Processing Page 32 (Constitutio Antoniniana Document)...")
html_body_p32 = process_3col_document(file_p32, "1.0", page_id="page32", lang_orig="英文/拉丁文", cols=2)

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

pages_data = {
    'page01': {'title': '荷蘭建國與地緣政經', 'img': 'images/img_12_960px-Seven_United_Netherlands_Janssonius_1658.jpg', 'ver': '1.1', 'doc': False},
    'page02': {'title': '美國的誕生(一)', 'img': 'images/img_10_960px-Cahokia_Monks_Mound.jpg', 'ver': '1.0', 'doc': False},
    'page13': {'title': '美國的誕生(二)', 'img': 'images/us2_map.jpg', 'ver': '1.0', 'doc': False},
    'page03': {'title': '宗教戰爭(一)：胡斯戰爭', 'img': 'images/hussite_wars_main.png', 'ver': '1.0', 'doc': False},
    'page12': {'title': '宗教戰爭(二)：卡特里派', 'img': 'images/catharism_main.jpg', 'ver': '1.0', 'doc': False},
    'page05': {'title': '希爾紹修道院', 'img': 'images/hirsau_main_wilhelm.jpg', 'ver': '1.0', 'doc': False},
    'page07': {'title': '奧托-薩利安帝國教會體制', 'img': 'images/ottonian_hre_map.svg', 'ver': '1.0', 'doc': False},
    'page09': {'title': '丕平獻土與教皇國誕生', 'img': 'images/pippin_donation_main.jpg', 'ver': '1.1', 'doc': False},
    'page10': {'title': '卡洛林教育基建與知識復興', 'img': 'images/carolingian_main.jpg', 'ver': '1.0', 'doc': False},
    'page11': {'title': '歐洲造紙術的歷史演變', 'img': 'images/paper_main.jpg', 'ver': '1.0', 'doc': False},
    'page14': {'title': '英國的憲法', 'img': 'images/uk_constitution_main.png', 'ver': '1.0', 'doc': False},
    'page15': {'title': '聖職與婚娶', 'img': 'images/clergy_trent.jpg', 'ver': '1.2', 'doc': False},
    'page16': {'title': '中世紀巡行王權的權力運作', 'img': 'images/reisekönig_travelling_kings.jpg', 'ver': '1.0', 'doc': False},
    'page17': {'title': '從皇帝稱號看羅馬政教關係演變', 'img': 'images/ambrose_and_theodosius.png', 'ver': '1.0', 'doc': False},
    'page18': {'title': '西元紀年的確立與演進', 'img': 'images/ad_calendar_main.png', 'ver': '1.1', 'doc': False},
    'page19': {'title': '米蘭敕令時代與李錫尼覆滅', 'img': 'images/milan_edict_main.png', 'ver': '1.0', 'doc': False},
    'page21': {'title': '使徒信經的歷史演變與神學建構', 'img': 'images/creed_main.jpg', 'ver': '1.0', 'doc': False},
    'page22': {'title': '羅馬秩序的終結與日耳曼王權的奠定', 'img': 'images/odoacer_fall_rome.jpg', 'ver': '1.1', 'doc': False},
    'page23': {'title': '蠻族崛起的政治重塑與克洛維霸權', 'img': 'images/clovis_main.jpg', 'ver': '1.0', 'doc': False},
    'page24': {'title': '羅馬晚期改革與農奴制', 'img': 'images/roman_colonate_estate.png', 'ver': '1.0', 'doc': False},
    'page25': {'title': '羅馬晚期軍制變遷與哥德人崛起', 'img': 'images/adrianople_battle.png', 'ver': '1.0', 'doc': False},
    'page26': {'title': '阿拉里克與哥德大遷徙', 'img': 'images/alaric_sack_rome.png', 'ver': '1.1', 'doc': False},
    'page27': {'title': '冷河戰役及其歷史學再闡釋', 'img': 'images/battle_of_frigidus.png', 'ver': '1.0', 'doc': False},
    'page04': {'title': '神聖羅馬帝國：金璽詔書', 'ver': '1.9', 'doc': True},
    'page06': {'title': '修道院制度：聖本篤會規', 'ver': '2.0', 'doc': True},
    'page08': {'title': '敘任權之爭：沃姆斯協約', 'ver': '1.0', 'doc': True},
    'page20': {'title': '羅馬帝國：米蘭敕令', 'ver': '1.0', 'doc': True},
    'page28': {'title': '羅馬帝國：薩洛尼卡敕令', 'ver': '1.0', 'doc': True},
    'page29': {'title': '阿德里安堡戰役', 'img': 'images/battle_of_adrianople.png', 'ver': '1.0', 'doc': False},
    'page30': {'title': '蓋納斯與早期拜占庭蠻族權力危機', 'img': 'images/gainas_byzantine.png', 'ver': '1.0', 'doc': False},
    'page31': {'title': '卡拉卡拉與《安東尼努斯敕令》', 'img': 'images/caracalla_edict.png', 'ver': '1.0', 'doc': False},
    'page32': {'title': '羅馬帝國：安東尼努斯敕令', 'ver': '1.0', 'doc': True},
}

categories = [
    {
        'title': '三世紀危機後的羅馬帝國',
        'key': 'rome',
        'img': 'images/milan_edict_main.png',
        'pages': ['page19', 'page22', 'page24', 'page25', 'page27', 'page30', 'page31']
    },
    {
        'title': '中世紀諸民族記',
        'key': 'medieval',
        'img': 'images/clovis_main.jpg',
        'pages': ['page23', 'page26', 'page29']
    },
    {
        'title': '教宗國記',
        'key': 'papal',
        'img': 'images/pippin_donation_main.jpg',
        'pages': ['page09']
    },
    {
        'title': '法蘭克王國記',
        'key': 'frank',
        'img': 'images/carolingian_main.jpg',
        'pages': ['page10']
    },
    {
        'title': '神聖羅馬帝國記',
        'key': 'hre',
        'img': 'images/reisekönig_travelling_kings.jpg',
        'pages': ['page07', 'page16']
    },
    {
        'title': '基督教與王權',
        'key': 'church',
        'img': 'images/creed_main.jpg',
        'pages': ['page17', 'page21', 'page15', 'page03', 'page12']
    },
    {
        'title': '歐洲小知識',
        'key': 'trivia',
        'img': 'images/paper_main.jpg',
        'pages': ['page14', 'page11', 'page18', 'page05']
    },
    {
        'title': '美國的誕生',
        'key': 'us',
        'img': 'images/us2_map.jpg',
        'pages': ['page02', 'page13']
    },
    {
        'title': '荷蘭的誕生與資本主義',
        'key': 'holland',
        'img': 'images/img_12_960px-Seven_United_Netherlands_Janssonius_1658.jpg',
        'pages': ['page01']
    }
]

def make_card_html(page_id, data):
    if data['doc']:
        return f"""
    <div class="article-card doc-card" onclick="location.hash='#{page_id}'">
        <div class="card-content">
            <div class="card-title">{data['title']}</div>
            <div class="card-meta">內容版本：{data['ver']}</div>
        </div>
    </div>"""
    else:
        return f"""
    <div class="article-card" onclick="location.hash='#{page_id}'">
        <div class="card-image" style="background-image: url('{data['img']}');"></div>
        <div class="card-content">
            <div class="card-title">{data['title']}</div>
            <div class="card-meta">內容版本：{data['ver']}</div>
        </div>
    </div>"""

cards_html_list = []
for cat in categories:
    cat_cards = []
    for pid in cat['pages']:
        if pid in pages_data:
            cat_cards.append(make_card_html(pid, pages_data[pid]))
    
    grid_content = "\n".join(cat_cards)
    cat_section = f"""
<div class="category-section">
    <div class="category-header-card" onclick="toggleCategory('{cat['key']}')">
        <div class="category-header-image" style="background-image: url('{cat['img']}');"></div>
        <div class="category-header-content">
            <span class="category-header-title">{cat['title']}</span>
            <span class="category-header-icon" id="icon-{cat['key']}">▼</span>
        </div>
    </div>
    <div class="category-container" id="cat-{cat['key']}" data-category="{cat['key']}" style="display: none;">
        <div class="article-grid">
            {grid_content}
        </div>
    </div>
</div>
"""
    cards_html_list.append(cat_section)

# Append Historical Documents section at the bottom
doc_pages = ['page04', 'page06', 'page08', 'page20', 'page28', 'page32']
doc_cards = []
for pid in doc_pages:
    if pid in pages_data:
        doc_cards.append(make_card_html(pid, pages_data[pid]))

doc_grid_content = "\n".join(doc_cards)
docs_section = f"""
<div class="card-section-title" style="margin-top: 40px; margin-bottom: 20px; font-size: 1.3rem; font-weight: 700; border-bottom: 2px solid #e2e8f0; padding-bottom: 10px; color: var(--primary-color);">歷史文件專區</div>
<div class="article-grid">
    {doc_grid_content}
</div>
"""
cards_html_list.append(docs_section)

article_cards_html = "\n".join(cards_html_list)


# Full Portal HTML Template
with open("template.html", "r", encoding="utf-8") as f:
    portal_template = f.read()

# Inject test categories style
categories_style = """
<style>
/* New Category Section Styles */
.category-section {
    margin-bottom: 12px;
    animation: fadeIn 0.6s ease;
}
.category-header-card {
    display: flex;
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    overflow: hidden;
    cursor: pointer;
    box-shadow: 0 4px 10px rgba(0,0,0,0.03);
    transition: transform 0.25s ease, box-shadow 0.25s ease, border-color 0.25s ease;
    height: 70px;
    align-items: center;
    width: 100%;
}
.category-header-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 20px rgba(0,85,164,0.08);
    border-color: rgba(0,85,164,0.2);
}
.category-header-image {
    width: 100px;
    height: 100%;
    background-size: cover;
    background-position: center;
    border-right: 1px solid #e2e8f0;
}
.category-header-content {
    flex: 1;
    padding: 0 20px;
    display: flex;
    justify-content: space-between;
    align-items: center;
}
.category-header-title {
    font-size: 1.05rem;
    font-weight: 700;
    color: var(--primary-color);
    letter-spacing: 0.5px;
}
.category-header-icon {
    font-size: 0.85rem;
    color: #718096;
    transition: color 0.2s ease;
}
.category-header-card:hover .category-header-icon {
    color: var(--primary-color);
}
.category-container {
    background: #edf2f7;  /* Soft gray container background as in mockup */
    border: 1px solid #e2e8f0;
    border-radius: 16px;
    padding: 24px;
    box-shadow: inset 0 2px 8px rgba(0,0,0,0.04);
    margin-top: 10px;
    margin-bottom: 20px;
    transition: opacity 0.25s ease;
}
.category-header-card.open {
    border-bottom-left-radius: 0;
    border-bottom-right-radius: 0;
    border-bottom-color: transparent;
    box-shadow: none;
}
.category-container.open {
    border-top-left-radius: 0;
    border-top-right-radius: 0;
    margin-top: 0;
    border-top: none;
}

/* Layout adaptation for document cards in the grids */
.category-container .article-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
    gap: 20px;
}
@media (max-width: 800px) {
    .category-container .article-grid {
        grid-template-columns: repeat(2, 1fr) !important;
        gap: 12px;
    }
}
.category-container .article-card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}
.category-container .article-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 10px 20px rgba(0, 0, 0, 0.08);
    border-color: #cbd5e0;
}
.category-container .article-card.doc-card {
    background: #fafafa;
    border-left: 5px solid #AE1C28; /* document accent color */
}

/* Dynamic Hover Accent Color per Category Container */
.category-container[data-category="rome"] .article-card:hover {
    border-color: #e53e3e;
    box-shadow: 0 10px 20px rgba(229, 62, 62, 0.12);
}
.category-container[data-category="medieval"] .article-card:hover {
    border-color: #319795;
    box-shadow: 0 10px 20px rgba(49, 151, 149, 0.12);
}
.category-container[data-category="papal"] .article-card:hover {
    border-color: #ecc94b;
    box-shadow: 0 10px 20px rgba(236, 201, 75, 0.12);
}
.category-container[data-category="frank"] .article-card:hover {
    border-color: #486581;
    box-shadow: 0 10px 20px rgba(72, 101, 129, 0.12);
}
.category-container[data-category="hre"] .article-card:hover {
    border-color: #e53e3e;
    box-shadow: 0 10px 20px rgba(229, 62, 62, 0.12);
}
.category-container[data-category="church"] .article-card:hover {
    border-color: #805ad5;
    box-shadow: 0 10px 20px rgba(128, 90, 213, 0.12);
}
.category-container[data-category="trivia"] .article-card:hover {
    border-color: #319795;
    box-shadow: 0 10px 20px rgba(49, 151, 149, 0.12);
}
.category-container[data-category="us"] .article-card:hover {
    border-color: #3182ce;
    box-shadow: 0 10px 20px rgba(49, 130, 206, 0.12);
}
.category-container[data-category="holland"] .article-card:hover {
    border-color: #dd6b20;
    box-shadow: 0 10px 20px rgba(221, 107, 32, 0.12);
}
</style>
"""
portal_template = portal_template.replace('</head>', categories_style + '</head>')

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
final_html = final_html.replace('__HTML_BODY_PAGE16__', html_body_p16)
final_html = final_html.replace('__HTML_BODY_PAGE17__', html_body_p17)
final_html = final_html.replace('__HTML_BODY_PAGE18__', html_body_p18)
final_html = final_html.replace('__HTML_BODY_PAGE19__', html_body_p19)
final_html = final_html.replace('__HTML_BODY_PAGE20__', html_body_p20)
final_html = final_html.replace('__HTML_BODY_PAGE21__', html_body_p21)
final_html = final_html.replace('__HTML_BODY_PAGE22__', html_body_p22)
final_html = final_html.replace('__HTML_BODY_PAGE23__', html_body_p23)
final_html = final_html.replace('__HTML_BODY_PAGE24__', html_body_p24)
final_html = final_html.replace('__HTML_BODY_PAGE25__', html_body_p25)
final_html = final_html.replace('__HTML_BODY_PAGE26__', html_body_p26)
final_html = final_html.replace('__HTML_BODY_PAGE27__', html_body_p27)
final_html = final_html.replace('__HTML_BODY_PAGE28__', html_body_p28)
final_html = final_html.replace('__HTML_BODY_PAGE29__', html_body_p29)
final_html = final_html.replace('__HTML_BODY_PAGE30__', html_body_p30)
final_html = final_html.replace('__HTML_BODY_PAGE31__', html_body_p31)
final_html = final_html.replace('__HTML_BODY_PAGE32__', html_body_p32)
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
final_html = final_html.replace('__PAGE16_DATE__', get_file_last_update_date(file_p16))
final_html = final_html.replace('__PAGE17_DATE__', get_file_last_update_date(file_p17))
final_html = final_html.replace('__PAGE18_DATE__', get_file_last_update_date(file_p18))
final_html = final_html.replace('__PAGE19_DATE__', get_file_last_update_date(file_p19))
final_html = final_html.replace('__PAGE20_DATE__', get_file_last_update_date(file_p20))
final_html = final_html.replace('__PAGE21_DATE__', get_file_last_update_date(file_p21))
final_html = final_html.replace('__PAGE22_DATE__', get_file_last_update_date(file_p22))
final_html = final_html.replace('__PAGE23_DATE__', get_file_last_update_date(file_p23))
final_html = final_html.replace('__PAGE24_DATE__', get_file_last_update_date(file_p24))
final_html = final_html.replace('__PAGE25_DATE__', get_file_last_update_date(file_p25))
final_html = final_html.replace('__PAGE26_DATE__', get_file_last_update_date(file_p26))
final_html = final_html.replace('__PAGE27_DATE__', get_file_last_update_date(file_p27))
final_html = final_html.replace('__PAGE28_DATE__', get_file_last_update_date(file_p28))
final_html = final_html.replace('__PAGE29_DATE__', get_file_last_update_date(file_p29))
final_html = final_html.replace('__PAGE30_DATE__', get_file_last_update_date(file_p30))
final_html = final_html.replace('__PAGE31_DATE__', get_file_last_update_date(file_p31))
final_html = final_html.replace('__PAGE32_DATE__', get_file_last_update_date(file_p32))

# Inject JavaScript for toggle function
toggle_js = """
<script>
function toggleCategory(catId) {
    const container = document.getElementById('cat-' + catId);
    const icon = document.getElementById('icon-' + catId);
    if (!container || !icon) return;
    const header = container.previousElementSibling;
    
    if (container.style.display === 'none') {
        container.style.display = 'block';
        container.style.opacity = '0';
        icon.innerText = '▲';
        if (header) header.classList.add('open');
        container.classList.add('open');
        // force reflow
        container.offsetHeight;
        container.style.transition = 'opacity 0.25s ease';
        container.style.opacity = '1';
    } else {
        container.style.display = 'none';
        icon.innerText = '▼';
        if (header) header.classList.remove('open');
        container.classList.remove('open');
    }
}
</script>
"""
final_html = final_html.replace('</body>', toggle_js + '</body>')

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
    <loc>https://ludwica-history-lesson.pages.dev/</loc>
    <lastmod>{today}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>1.0</priority>
  </url>
</urlset>"""

with open(r'sitemap.xml', 'w', encoding='utf-8', newline='\n') as f:
    f.write(sitemap_content)
print("Generated sitemap.xml")

# Generate robots.txt for SEO
robots_content = """User-agent: *
Allow: /

Sitemap: https://ludwica-history-lesson.pages.dev/sitemap.xml
"""

with open(r'robots.txt', 'w', encoding='utf-8') as f:
    f.write(robots_content)
print("Generated robots.txt")

# Generate SEO Redirect HTML files for each page
def generate_redirect_pages():
    print("Generating SEO redirect HTML files in 'pages/' directory...")
    base_site_url = "https://ludwica-history-lesson.pages.dev/"
    
    # Create pages directory if it doesn't exist
    os.makedirs('pages', exist_ok=True)
    
    # Load descriptions from template.html using regex
    descs = {}
    try:
        with open('template.html', 'r', encoding='utf-8') as f:
            t_content = f.read()
        matches = re.findall(r"'(page\d+)':\s*\{\s*title:\s*'(.*?)',\s*desc:\s*'(.*?)'\s*\}", t_content)
        for pid, title, desc in matches:
            descs[pid] = desc
    except Exception as e:
        print(f"Error loading descriptions for redirects: {e}")
        
    for pid, data in pages_data.items():
        title = data['title'] + " — Ludwica 的簡單歷史課"
        desc = descs.get(pid, "Ludwica 的簡單歷史課：歷史專題研究與報告。")
        
        # Determine image URL
        img_path = data.get('img', 'history_banner_bg.png')
        if not img_path:
            img_path = 'history_banner_bg.png'
        image_url = base_site_url + img_path
        page_url = base_site_url + f"pages/{pid}.html"
        
        redirect_html = f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <title>{title}</title>
    <meta name="description" content="{desc}">
    
    <!-- Open Graph Metadata -->
    <meta property="og:title" content="{title}">
    <meta property="og:description" content="{desc}">
    <meta property="og:image" content="{image_url}">
    <meta property="og:type" content="article">
    <meta property="og:url" content="{page_url}">
    
    <!-- Twitter Card Metadata -->
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="{title}">
    <meta name="twitter:description" content="{desc}">
    <meta name="twitter:image" content="{image_url}">
    
    <script>
        window.location.replace("../#" + "{pid}");
    </script>
</head>
<body>
    <h1>{title}</h1>
    <p>{desc}</p>
    <p>正在為您導向至網頁... 如果沒有自動跳轉，請點擊 <a href="../#{pid}">這裡</a>。</p>
</body>
</html>
"""
        with open(os.path.join("pages", f"{pid}.html"), 'w', encoding='utf-8', newline='\n') as f:
            f.write(redirect_html)
            
    print(f"Successfully generated {len(pages_data)} redirect HTML files under 'pages/'.")

generate_redirect_pages()

print("Done! Site successfully built as dynamic 23-topic history portal with full SEO.")
