# -*- coding: utf-8 -*-
"""L3搜索桥接 — 管道与Claude WebSearch之间的桥梁
用法:
  # 生成搜索任务 (在分析管道中调用)
  python l3_search_bridge.py --generate "D:/足彩/2026.5.25"

  # 保存搜索结果 (Claude执行WebSearch后调用)
  python l3_search_bridge.py --save "斯达 vs 瓦勒伦加" 挪超 \
    --home-form "主场1胜3平" --injuries "无" --h2h "近3次交手2平1负"

  # 查看哪些比赛缺少搜索数据
  python l3_search_bridge.py --missing "D:/足彩/2026.5.25"

  # 导出为 framework_v4 search_data 参数
  python l3_search_bridge.py --export "斯达 vs 瓦勒伦加" 挪超
"""
import sys, os, re, json, time

CACHE_DIR = os.path.join(os.path.dirname(__file__), '.search_cache')
os.makedirs(CACHE_DIR, exist_ok=True)


def make_key(home, away, league):
    """生成缓存键"""
    raw = f'{league}_{home}_{away}'
    return re.sub(r'[<>:"/\\|?*\s]+', '_', raw)[:80]


def generate_task(match_info):
    """为一场比赛生成搜索任务"""
    home = match_info.get('home', '?')
    away = match_info.get('away', '?')
    league = match_info.get('league', '?')
    mid = match_info.get('serial', match_info.get('id', '?'))

    return {
        'match_id': mid,
        'league': league,
        'home': home,
        'away': away,
        'cache_key': make_key(home, away, league),
        'queries': {
            'home_form': f'{home} {league} 最近5场 主场战绩 2026',
            'away_form': f'{away} {league} 最近5场 客场战绩 2026',
            'injuries': f'{home} {away} {league} 伤病 停赛 缺阵 2026',
            'h2h': f'{home} vs {away} 历史交锋 战绩',
            'league_draw': f'{league} 2026赛季 主场胜率 平局率 统计',
        },
        'extract_instructions': {
            'home_form': '提取主队最近5个主场比赛的胜/平/负场数, 例如: 主场3胜1平1负',
            'away_form': '提取客队最近5个客场比赛的胜/平/负场数, 例如: 客场1胜2平2负',
            'injuries': '列出所有伤缺/停赛球员名字, 例如: ["球员A","球员B"]',
            'h2h': '提取近3-5次历史交锋结果, 例如: 主队1胜2平2负',
            'league_draw': '提取联赛本赛季的平局率百分比, 例如: 28%',
        }
    }


def save_search_result(home, away, league, **kwargs):
    """保存搜索结果到缓存"""
    key = make_key(home, away, league)
    cache_file = os.path.join(CACHE_DIR, f'{key}.json')

    # 加载已有缓存 (如果有)
    existing = {}
    if os.path.exists(cache_file):
        with open(cache_file, 'r', encoding='utf-8') as f:
            existing = json.load(f)

    # 合并新数据
    existing.update(kwargs)
    existing['updated_at'] = time.strftime('%Y-%m-%d %H:%M')
    existing['match_name'] = f'{home} vs {away} ({league})'

    with open(cache_file, 'w', encoding='utf-8') as f:
        json.dump(existing, f, ensure_ascii=False, indent=2)

    return cache_file


def export_search_data(home, away, league):
    """导出为 framework_v4 的 search_data 格式"""
    key = make_key(home, away, league)
    cache_file = os.path.join(CACHE_DIR, f'{key}.json')

    if not os.path.exists(cache_file):
        return None

    with open(cache_file, 'r', encoding='utf-8') as f:
        cached = json.load(f)

    # 构建 search_data
    search_data = {
        'home_form': cached.get('home_form', ''),
        'away_form': cached.get('away_form', ''),
        'injuries': [],
        'home_draw_rate': 0,
        'away_draw_rate': 0,
    }

    # 解析伤病
    injuries_raw = cached.get('injuries', '')
    if isinstance(injuries_raw, list):
        search_data['injuries'] = injuries_raw
    elif isinstance(injuries_raw, str) and injuries_raw:
        # 尝试解析: "球员A, 球员B, 球员C" 或 "球员A(伤缺), 球员B(停赛)"
        names = re.split(r'[,，、；;]', injuries_raw)
        for n in names:
            n = re.sub(r'[（(][^)）]*[)）]', '', n).strip()
            if n and len(n) > 1:
                search_data['injuries'].append(n)

    # 解析主场战绩
    hf = cached.get('home_form', '')
    if hf:
        search_data['home_form'] = hf
        wm = re.findall(r'(\d+)胜', hf)
        dm = re.findall(r'(\d+)平', hf)
        lm = re.findall(r'(\d+)负', hf)
        w = int(wm[0]) if wm else 0
        d = int(dm[0]) if dm else 0
        l = int(lm[0]) if lm else 0
        total = w + d + l
        if total > 0:
            search_data['home_win_rate'] = w / total
            search_data['home_draw_rate'] = d / total

    # 解析客场战绩 (用于客队平局率)
    af = cached.get('away_form', '')
    if af:
        search_data['away_form'] = af
        dm = re.findall(r'(\d+)平', af)
        wm = re.findall(r'(\d+)胜', af)
        lm = re.findall(r'(\d+)负', af)
        w = int(wm[0]) if wm else 0
        d = int(dm[0]) if dm else 0
        l = int(lm[0]) if lm else 0
        total = w + d + l
        if total > 0:
            search_data['away_draw_rate'] = d / total

    # 联赛平局率
    draw_rate = cached.get('draw_rate', 0) or cached.get('league_draw_rate', 0)
    if isinstance(draw_rate, str):
        drm = re.findall(r'(\d+)', draw_rate)
        draw_rate = int(drm[0]) / 100 if drm else 0
    if draw_rate and draw_rate < 1:
        search_data['league_draw_rate'] = draw_rate

    return search_data


def find_missing(data_dir):
    """扫描目录, 找到缺少搜索缓存的比赛"""
    missing = []
    for folder in sorted(os.listdir(data_dir)):
        full = os.path.join(data_dir, folder)
        if not os.path.isdir(full):
            continue

        # 尝试从 match_info.json 读取
        meta_file = os.path.join(full, 'match_info.json')
        if os.path.exists(meta_file):
            with open(meta_file, 'r', encoding='utf-8') as f:
                match = json.load(f)
            home = match.get('home', '?')
            away = match.get('away', '?')
            league = match.get('league', '?')
        else:
            # 从文件夹名解析
            parts = folder.replace('vs', 'VS').split('VS')
            if len(parts) < 2:
                continue
            home = parts[0].strip()[-20:]
            away = parts[1].strip()[:20]
            league = '未知'

        key = make_key(home, away, league)
        cache_file = os.path.join(CACHE_DIR, f'{key}.json')
        if not os.path.exists(cache_file):
            task = generate_task({'home': home, 'away': away, 'league': league})
            missing.append(task)

    return missing


# ========== 主入口 ==========
if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')

    if len(sys.argv) < 2:
        print('用法:')
        print('  python l3_search_bridge.py --generate <数据目录>')
        print('  python l3_search_bridge.py --missing <数据目录>')
        print('  python l3_search_bridge.py --save "主队 vs 客队" 联赛 --injuries "..." --home-form "..."')
        print('  python l3_search_bridge.py --export "主队 vs 客队" 联赛')
        sys.exit(0)

    if sys.argv[1] == '--generate':
        data_dir = sys.argv[2] if len(sys.argv) > 2 else '.'
        tasks = []
        for folder in sorted(os.listdir(data_dir)):
            full = os.path.join(data_dir, folder)
            if not os.path.isdir(full):
                continue
            meta_file = os.path.join(full, 'match_info.json')
            if os.path.exists(meta_file):
                with open(meta_file, 'r', encoding='utf-8') as f:
                    match = json.load(f)
            else:
                match = {'home': '?', 'away': '?', 'league': '?', 'serial': folder[:10]}
            tasks.append(generate_task(match))

        # 输出搜索任务 (Claude 可执行格式)
        print(f'# L3搜索任务 — {len(tasks)}场比赛')
        print(f'# 请逐场执行 WebSearch, 然后用 --save 保存结果\n')
        for i, task in enumerate(tasks):
            print(f'## [{i+1}/{len(tasks)}] {task["league"]} {task["home"]} vs {task["away"]}')
            for qtype, query in task['queries'].items():
                print(f'  [{qtype}] {query}')
            print(f'  缓存键: {task["cache_key"]}')
            print()

    elif sys.argv[1] == '--missing':
        data_dir = sys.argv[2] if len(sys.argv) > 2 else '.'
        missing = find_missing(data_dir)
        print(f'缺少搜索数据: {len(missing)}/{len(os.listdir(data_dir))} 场')
        for task in missing:
            print(f'  {task["league"]} {task["home"]} vs {task["away"]}')
            for qtype, query in task['queries'].items():
                print(f'    [{qtype}] {query}')

    elif sys.argv[1] == '--save':
        match_str = sys.argv[2] if len(sys.argv) > 2 else ''
        league = sys.argv[3] if len(sys.argv) > 3 else '未知'

        parts = re.split(r'\s*vs\s*', match_str, flags=re.IGNORECASE)
        home = parts[0].strip() if len(parts) > 0 else '?'
        away = parts[1].strip() if len(parts) > 1 else '?'

        # 解析命名参数
        kwargs = {}
        i = 4
        while i < len(sys.argv):
            arg = sys.argv[i]
            if arg.startswith('--'):
                key = arg[2:].replace('-', '_')
                if i + 1 < len(sys.argv) and not sys.argv[i + 1].startswith('--'):
                    kwargs[key] = sys.argv[i + 1]
                    i += 2
                else:
                    kwargs[key] = True
                    i += 1
            else:
                i += 1

        cache_file = save_search_result(home, away, league, **kwargs)
        print(f'搜索结果已保存: {cache_file}')
        print(f'键: {make_key(home, away, league)}')

    elif sys.argv[1] == '--export':
        match_str = sys.argv[2] if len(sys.argv) > 2 else ''
        league = sys.argv[3] if len(sys.argv) > 3 else '未知'

        parts = re.split(r'\s*vs\s*', match_str, flags=re.IGNORECASE)
        home = parts[0].strip() if len(parts) > 0 else '?'
        away = parts[1].strip() if len(parts) > 1 else '?'

        sd = export_search_data(home, away, league)
        if sd:
            print(json.dumps(sd, ensure_ascii=False, indent=2))
        else:
            print('{}  # 无缓存数据')
