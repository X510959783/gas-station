# -*- coding: utf-8 -*-
"""500.com 赔率数据采集器
用法:
  python fetch_500.py                     # 采集今日所有比赛
  python fetch_500.py --date 2026-05-28   # 采集指定日期
  python fetch_500.py --id 1364015        # 采集指定比赛ID
  python fetch_500.py --league 挪超       # 只采集指定联赛
输出: D:/足彩/{date}/ 目录下每个比赛一个文件夹
"""
import sys, os, re, json, time, urllib.request
import proxy_config

BASE_DIR = r'D:\足彩'
INDEX_URL = 'https://odds.500.com/'
OUZHI_URL = 'https://odds.500.com/fenxi/ouzhi-{mid}.shtml'
YAZHI_URL = 'https://odds.500.com/fenxi/yazhi-{mid}.shtml'
RANGQIU_URL = 'https://odds.500.com/fenxi/rangqiu-{mid}.shtml'
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'text/html,application/xhtml+xml',
    'Accept-Language': 'zh-CN,zh;q=0.9',
}

# 联赛关键词 → 标准名
LEAGUE_MAP = {
    '挪超': '挪超', '瑞超': '瑞超', '瑞典超': '瑞超',
    '德甲': '德甲', '英超': '英超', '意甲': '意甲',
    '西甲': '西甲', '日职': '日职', '日职联': '日职',
    '英甲': '英甲', '法甲': '法甲', '荷甲': '荷甲',
    '葡超': '葡超', '巴甲': '巴甲', '阿甲': '阿甲',
    '美职': '美职', '美职联': '美职',
    '欧冠': '欧冠', '欧联': '欧联', '欧协联': '欧协联',
    '解放者杯': '解放者杯', '南美': '南美',
    '世预赛': '世预赛', '欧国联': '欧国联',
    '日乙': '日乙', '韩职': '韩职', 'K联赛': '韩职',
    '澳超': '澳超', '俄超': '俄超',
}


def fetch_page(url, retries=3):
    """下载页面, 自动处理编码"""
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=30) as resp:
                raw = resp.read()
            for enc in ['gb2312', 'gbk', 'utf-8', 'gb18030']:
                try:
                    return raw.decode(enc)
                except (UnicodeDecodeError, LookupError):
                    continue
            return raw.decode('utf-8', errors='replace')
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
            else:
                raise e


def parse_index(html):
    """解析500.com首页, 提取比赛列表
    返回: [{id, serial, league, home, away, time, date}, ...]
    """
    matches = []
    rows = re.findall(r'<tr[^>]*>(.*?)</tr>', html, re.DOTALL)

    for row in rows:
        if 'ouzhi-' not in row:
            continue

        m_id = re.search(r'ouzhi-(\d+)\.shtml', row)
        if not m_id:
            continue
        mid = m_id.group(1)

        # 提取所有 td 纯文本
        tds = re.findall(r'<td[^>]*>(.*?)</td>', row, re.DOTALL)
        texts = []
        for td in tds:
            clean = re.sub(r'<[^>]+>', '', td).strip()
            clean = re.sub(r'\s+', ' ', clean)
            if clean and clean not in ('欧', '亚', '指', 'VS', '走',
                                       'Bet365', 'Crown', 'Macauslot',
                                       '竞', '单', '析', '荐', '走地'):
                # 过滤掉赔率数字和模板变量
                if re.match(r'^[\d.]+$', clean):
                    continue
                if re.match(r'^\{[wdlnr]\d\}$', clean):
                    continue
                texts.append(clean)

        if len(texts) < 5:
            continue

        # 解析字段
        serial = texts[0] if len(texts) > 0 else ''
        league_raw = texts[1] if len(texts) > 1 else ''
        match_name = texts[2] if len(texts) > 2 else ''
        match_time = texts[3] if len(texts) > 3 else ''
        home = texts[4] if len(texts) > 4 else ''

        # 找 VS 后面的队名
        away = ''
        try:
            vs_idx = texts.index('VS') if 'VS' in texts else -1
            if vs_idx > 0 and vs_idx + 1 < len(texts):
                away = texts[vs_idx + 1]
            elif len(texts) > 5:
                away = texts[5]
        except ValueError:
            if len(texts) > 5:
                away = texts[5]

        # 联赛名映射
        league = '其他'
        for key, val in LEAGUE_MAP.items():
            if key in league_raw or key in match_name:
                league = val
                break
        if league == '其他' and league_raw:
            league = league_raw[:10]

        # 解析时间
        date_str = ''
        time_str = match_time
        if '-' in match_time:
            parts = match_time.split(' ')
            date_str = parts[0] if len(parts) > 0 else ''
            time_str = parts[1] if len(parts) > 1 else match_time

        if not date_str:
            date_str = time.strftime('%Y-%m-%d')

        matches.append({
            'id': mid,
            'serial': serial,
            'league': league,
            'league_raw': league_raw,
            'home': home,
            'away': away,
            'time': time_str,
            'date': date_str,
            'full_name': f'{home} vs {away}',
        })

    return matches


def download_match(match, target_dir):
    """下载单场比赛的三个页面"""
    mid = match['id']
    safe_name = f"{match['serial']}_{match['league']}_{match['home']}_{match['away']}"
    safe_name = re.sub(r'[<>:"/\\|?*]', '_', safe_name)[:80]
    folder = os.path.join(target_dir, safe_name)
    os.makedirs(folder, exist_ok=True)

    pages = {
        '百家欧赔': OUZHI_URL.format(mid=mid),
        '让球指数': RANGQIU_URL.format(mid=mid),
        '亚盘对比': YAZHI_URL.format(mid=mid),
    }

    for ptype, url in pages.items():
        try:
            html = fetch_page(url)
            fname = f"{match['home']}VS{match['away']}({match['date'][:4]}{match['league']})-{ptype}-500彩票网.html"
            fname = re.sub(r'[<>:"/\\|?*]', '_', fname)
            path = os.path.join(folder, fname)
            with open(path, 'w', encoding='utf-8') as f:
                f.write(html)
            print(f'  ✓ {ptype}')
        except Exception as e:
            print(f'  ✗ {ptype}: {e}')

    # 写入元数据
    meta_path = os.path.join(folder, 'match_info.json')
    with open(meta_path, 'w', encoding='utf-8') as f:
        json.dump(match, f, ensure_ascii=False, indent=2)

    return folder


def filter_matches(matches, league=None, date=None):
    """过滤比赛列表"""
    result = matches
    if league:
        result = [m for m in result if m['league'] == league]
    if date:
        result = [m for m in result if m['date'] == date]
    return result


# ========== 主入口 ==========
if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    import argparse

    parser = argparse.ArgumentParser(description='500.com赔率数据采集器')
    parser.add_argument('--date', help='指定日期 YYYY-MM-DD')
    parser.add_argument('--id', help='指定比赛ID')
    parser.add_argument('--league', help='只采集指定联赛')
    parser.add_argument('--dry-run', action='store_true', help='只列出不下载')
    args = parser.parse_args()

    if args.id:
        # 单场模式
        print(f'采集单场比赛: {args.id}')
        match = {'id': args.id, 'serial': '单场', 'league': args.league or '未知',
                 'home': '主队', 'away': '客队', 'time': '00:00',
                 'date': args.date or time.strftime('%Y-%m-%d'),
                 'full_name': '单场比赛'}
        today = args.date or time.strftime('%Y-%m-%d')
        target = os.path.join(BASE_DIR, today)
        if not args.dry_run:
            download_match(match, target)
            print(f'\n保存至: {target}')
    else:
        # 批量模式
        print('采集500.com今日比赛列表...')
        html = fetch_page(INDEX_URL)
        matches = parse_index(html)
        matches = filter_matches(matches, args.league, args.date)

        print(f'找到 {len(matches)} 场比赛')
        if args.league:
            print(f'  (已过滤联赛: {args.league})')
        if args.date:
            print(f'  (已过滤日期: {args.date})')

        for m in matches:
            print(f'  [{m["serial"]}] {m["league"]} {m["home"]} vs {m["away"]} ({m["date"]} {m["time"]}) ID:{m["id"]}')

        if args.dry_run:
            print('\n--dry-run 模式, 不下载')
            sys.exit(0)

        if not matches:
            print('没有找到匹配的比赛')
            sys.exit(1)

        today = args.date or time.strftime('%Y-%m-%d')
        target = os.path.join(BASE_DIR, today)

        print(f'\n开始下载到: {target}')
        for i, m in enumerate(matches):
            print(f'\n[{i+1}/{len(matches)}] {m["serial"]} {m["league"]} {m["home"]} vs {m["away"]}')
            try:
                folder = download_match(m, target)
                print(f'  → {folder}')
            except Exception as e:
                print(f'  ✗ 失败: {e}')
            time.sleep(1)  # 礼貌延迟

        print(f'\n完成! {len(matches)}场比赛 → {target}')
        print(f'下一步: bash auto_pipeline.sh "{target}"')
