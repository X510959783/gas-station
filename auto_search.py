# -*- coding: utf-8 -*-
"""自主L3搜索 — 从500.com直接抓取球队情报, 无需Claude WebSearch
用法:
  python auto_search.py <match_id>              # 单个比赛
  python auto_search.py --inject <数据目录>     # 批量: 为目录下所有比赛注入L3缓存
来源:
  - liansai.500.com/team/{id}/  球队近期战绩
  - odds.500.com/fenxi/ouzhi-{id}.shtml  比赛页(提取球队ID)
"""
import sys, os, re, json, time, urllib.request
import proxy_config

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
}

CACHE_DIR = os.path.join(os.path.dirname(__file__), '.search_cache')
os.makedirs(CACHE_DIR, exist_ok=True)


def fetch_page(url, encodings=['gb2312', 'gbk', 'utf-8', 'gb18030']):
    """获取页面, 自动处理编码"""
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=30) as resp:
        raw = resp.read()
    for enc in encodings:
        try:
            return raw.decode(enc)
        except (UnicodeDecodeError, LookupError):
            continue
    return raw.decode('utf-8', errors='replace')


def extract_team_ids(match_id):
    """从比赛页面提取主客队ID (保持出现顺序=主队先)"""
    url = f'https://odds.500.com/fenxi/ouzhi-{match_id}.shtml'
    html = fetch_page(url)
    # 保持出现顺序: 第一个是主队ID, 第二个是客队ID
    ids = re.findall(r'liansai\.500\.com/team/(\d+)/', html)
    # 去重但保持顺序
    seen = set()
    ordered = []
    for tid in ids:
        if tid not in seen:
            seen.add(tid)
            ordered.append(tid)
    if len(ordered) >= 2:
        return ordered[0], ordered[1]
    return None, None


def scrape_team_form(team_id, num_matches=5):
    """抓取球队近期战绩
    返回: {team_name, matches: [{date, league, opponent, score, result, venue}, ...],
           home_form: '主场X胜Y平Z负', away_form: '客场X胜Y平Z负',
           home_draw_rate, away_draw_rate}
    """
    url = f'https://liansai.500.com/team/{team_id}/'
    try:
        html = fetch_page(url)
    except Exception:
        return None

    # 提取球队名
    title = re.search(r'<title>(.*?)[_ ]', html)
    team_name = title.group(1) if title else f'Team{team_id}'

    # 提取比赛行
    rows = re.findall(r'<tr[^>]*>(.*?)</tr>', html, re.DOTALL)
    matches = []

    for row in rows:
        tds = re.findall(r'<td[^>]*>(.*?)</td>', row, re.DOTALL)
        if len(tds) < 8:
            continue

        # 清理文本
        texts = []
        for td in tds:
            clean = re.sub(r'<[^>]+>', '', td).strip()
            clean = re.sub(r'&nbsp;', ' ', clean)
            clean = re.sub(r'\s+', ' ', clean).strip()
            if clean:
                texts.append(clean)

        if len(texts) < 7:
            continue

        # 解析: [联赛, 日期, 主队, 比分, 客队, 结果, ...]
        league = texts[0] if len(texts) > 0 else ''
        date = texts[1] if len(texts) > 1 else ''
        home = texts[2] if len(texts) > 2 else ''
        score = texts[3] if len(texts) > 3 else ''
        away = texts[4] if len(texts) > 4 else ''
        result = texts[5] if len(texts) > 5 else ''

        # 验证: 结果必须是 胜/平/负
        if result not in ('胜', '平', '负'):
            continue

        # 判断主客场
        venue = '主' if team_name in home else '客'

        # 解析比分
        score_match = re.search(r'(\d+)\s*:\s*(\d+)', score)
        if not score_match:
            continue

        home_goals = int(score_match.group(1))
        away_goals = int(score_match.group(2))

        matches.append({
            'date': date,
            'league': league,
            'opponent': away if venue == '主' else home,
            'score': f'{home_goals}-{away_goals}',
            'result': result,
            'venue': venue,
            'goals_for': home_goals if venue == '主' else away_goals,
            'goals_against': away_goals if venue == '主' else home_goals,
        })

        if len(matches) >= num_matches * 2:  # 多取一些以覆盖主客场
            break

    if not matches:
        return None

    recent = matches[:num_matches]

    # 统计近N场主客场
    home_matches = [m for m in matches if m['venue'] == '主'][:num_matches]
    away_matches = [m for m in matches if m['venue'] == '客'][:num_matches]

    def count_form(m_list):
        w = sum(1 for m in m_list if m['result'] == '胜')
        d = sum(1 for m in m_list if m['result'] == '平')
        l = sum(1 for m in m_list if m['result'] == '负')
        total = w + d + l
        return w, d, l, total

    hw, hd, hl, ht = count_form(home_matches)
    aw, ad, al, at = count_form(away_matches)

    # 最近总体战绩
    rw, rd, rl, rt = count_form(recent)

    return {
        'team_name': team_name,
        'team_id': team_id,
        'recent_matches': recent,
        'recent_form': f'近{rt}场{rw}胜{rd}平{rl}负',
        'home_form': f'主场{hw}胜{hd}平{hl}负' if ht > 0 else '',
        'away_form': f'客场{aw}胜{ad}平{al}负' if at > 0 else '',
        'home_draw_rate': round(hd / ht, 2) if ht > 0 else 0,
        'away_draw_rate': round(ad / at, 2) if at > 0 else 0,
        'home_win_rate': round(hw / ht, 2) if ht > 0 else 0,
        'away_win_rate': round(aw / at, 2) if at > 0 else 0,
    }


def build_search_data(home_id, away_id):
    """获取两队情报并构建 framework_v4 search_data"""
    home_data = scrape_team_form(home_id, 5)
    away_data = scrape_team_form(away_id, 5)

    result = {
        'home_form': '',
        'away_form': '',
        'injuries': [],
        'home_draw_rate': 0,
        'away_draw_rate': 0,
        'home_win_rate': 0,
        'away_win_rate': 0,
        'home_recent_form': '',
        'away_recent_form': '',
    }

    if home_data:
        result['home_form'] = home_data.get('home_form', '')
        result['home_draw_rate'] = home_data.get('home_draw_rate', 0)
        result['home_win_rate'] = home_data.get('home_win_rate', 0)
        result['home_recent_form'] = home_data.get('recent_form', '')

    if away_data:
        result['away_form'] = away_data.get('away_form', '')
        result['away_draw_rate'] = away_data.get('away_draw_rate', 0)
        result['away_win_rate'] = away_data.get('away_win_rate', 0)
        result['away_recent_form'] = away_data.get('recent_form', '')

    return result


def inject_cache(match_id, home_id=None, away_id=None):
    """抓取数据并写入缓存"""
    if not home_id or not away_id:
        home_id, away_id = extract_team_ids(match_id)
        if not home_id:
            return None

    search_data = build_search_data(home_id, away_id)

    # 获取队名用于缓存键
    home_name = 'home'
    away_name = 'away'
    try:
        hd = scrape_team_form(home_id, 1)
        ad = scrape_team_form(away_id, 1)
        if hd: home_name = hd['team_name']
        if ad: away_name = ad['team_name']
    except Exception:
        pass

    # 写入缓存
    from l3_search_bridge import make_key, save_search_result
    key = make_key(home_name, away_name, '')
    save_search_result(home_name, away_name, '', **search_data)

    return search_data


def inject_all(data_dir):
    """批量注入: 扫描目录, 为所有比赛抓取L3数据"""
    total = 0
    for folder in sorted(os.listdir(data_dir)):
        full = os.path.join(data_dir, folder)
        if not os.path.isdir(full):
            continue

        # 读取 match_info.json
        meta_file = os.path.join(full, 'match_info.json')
        if not os.path.exists(meta_file):
            continue

        with open(meta_file, 'r', encoding='utf-8') as f:
            meta = json.load(f)

        mid = meta.get('id', '')
        home = meta.get('home', '')
        away = meta.get('away', '')
        lg = meta.get('league', '')

        if not mid:
            continue

        # 检查是否已有缓存
        from l3_search_bridge import make_key
        key = make_key(home, away, lg)
        cache_file = os.path.join(CACHE_DIR, f'{key}.json')
        if os.path.exists(cache_file):
            continue

        print(f'  抓取: {lg} {home} vs {away} (ID:{mid})')
        try:
            inject_cache(mid)
            total += 1
            time.sleep(0.3)
        except Exception as e:
            print(f'    ✗ {e}')

    print(f'  完成: {total} 场比赛数据已缓存')
    return total


# ========== 主入口 ==========
if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')

    if len(sys.argv) < 2:
        print('用法:')
        print('  python auto_search.py <match_id>          # 单场')
        print('  python auto_search.py --inject <目录>     # 批量注入')
        print('  python auto_search.py --test              # 自检')
        sys.exit(0)

    if sys.argv[1] == '--inject':
        data_dir = sys.argv[2] if len(sys.argv) > 2 else '.'
        print(f'批量注入L3数据: {data_dir}')
        inject_all(data_dir)

    elif sys.argv[1] == '--test':
        print('自检: 1364015 (斯达 vs 瓦勒伦加)')
        home_id, away_id = extract_team_ids('1364015')
        print(f'  球队ID: {home_id}, {away_id}')

        if home_id:
            hd = scrape_team_form(home_id, 5)
            if hd:
                print(f'  主队: {hd["team_name"]}')
                print(f'    {hd["recent_form"]}')
                print(f'    {hd["home_form"]}')
                print(f'    主场平局率: {hd["home_draw_rate"]:.0%}')

        if away_id:
            ad = scrape_team_form(away_id, 5)
            if ad:
                print(f'  客队: {ad["team_name"]}')
                print(f'    {ad["recent_form"]}')
                print(f'    {ad["away_form"]}')
                print(f'    客场胜率: {ad["away_win_rate"]:.0%}')

    else:
        mid = sys.argv[1]
        print(f'获取比赛 {mid} 情报...')
        result = inject_cache(mid)
        if result:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print('  失败')
