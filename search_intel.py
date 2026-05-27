# -*- coding: utf-8 -*-
"""L3搜索情报模块 — 赛前自动搜集球队情报
用法:
  python search_intel.py "主队 vs 客队" 联赛       # 生成搜索提示
  python search_intel.py --batch "D:/足彩/2026-05-27"  # 批量处理
  python search_intel.py --cache show                 # 查看缓存
输出: 结构化JSON, 供 framework_v4 的 search_data 参数使用
"""
import sys, os, re, json, time

CACHE_DIR = os.path.join(os.path.dirname(__file__), '.search_cache')
os.makedirs(CACHE_DIR, exist_ok=True)

# 搜索模板
SEARCH_TEMPLATES = {
    'home_form': '{home} {league} 最近5场战绩 主场',
    'away_form': '{away} {league} 最近5场战绩 客场',
    'injuries': '{home} {away} {league} 伤病 停赛 缺阵',
    'h2h': '{home} vs {away} 历史交锋 战绩',
    'league_info': '{league} 2026赛季 主场胜率 平局率',
}


def generate_queries(home, away, league):
    """生成搜索查询列表"""
    queries = {}
    for key, template in SEARCH_TEMPLATES.items():
        queries[key] = template.format(home=home, away=away, league=league)
    return queries


def parse_search_result(query_type, text):
    """从搜索文本中提取结构化数据
    返回: {home_form, away_form, injuries, home_draw_rate, away_draw_rate, ...}
    """
    result = {
        'home_form': '',
        'away_form': '',
        'injuries': [],
        'home_draw_rate': 0,
        'away_draw_rate': 0,
        'h2h_summary': '',
        'raw_text': text[:500] if text else '',
    }

    if not text:
        return result

    # 提取伤病信息
    injury_patterns = [
        r'([^\s,，]+)\s*[（(]?\s*(伤缺|受伤|停赛|红牌|黄牌累计|禁赛|缺席)\s*[）)]?',
        r'(伤缺|缺阵|无缘)[：:]\s*([^。，,\n]+)',
    ]
    for pat in injury_patterns:
        found = re.findall(pat, text)
        for f in found:
            name = f[0] if isinstance(f, tuple) and len(f) > 0 else str(f)
            if name and len(name) > 1:
                result['injuries'].append(name.strip())

    # 提取主场战绩
    home_win_match = re.search(r'主场\s*(\d+)胜\s*(\d+)平\s*(\d+)负', text)
    if home_win_match:
        w, d, l = int(home_win_match.group(1)), int(home_win_match.group(2)), int(home_win_match.group(3))
        total = w + d + l
        result['home_form'] = f'主场{w}胜{d}平{l}负'
        if total > 0:
            result['home_win_rate'] = round(w / total, 2)
            result['home_draw_rate'] = round(d / total, 2)

    # 提取客场战绩 (可能是对手的客场)
    away_win_match = re.search(r'客场\s*(\d+)胜\s*(\d+)平\s*(\d+)负', text)
    if away_win_match:
        w, d, l = int(away_win_match.group(1)), int(away_win_match.group(2)), int(away_win_match.group(3))
        total = w + d + l
        result['away_form'] = f'客场{w}胜{d}平{l}负'
        if total > 0:
            result['away_draw_rate'] = round(d / total, 2)

    # 提取平局率
    draw_rate_match = re.search(r'平局率\s*[:：]?\s*(\d+)%', text)
    if draw_rate_match:
        result['draw_rate_from_search'] = int(draw_rate_match.group(1)) / 100

    return result


def cache_result(match_key, intel_data):
    """缓存搜索结果"""
    cache_file = os.path.join(CACHE_DIR, f'{match_key}.json')
    intel_data['cached_at'] = time.strftime('%Y-%m-%d %H:%M')
    with open(cache_file, 'w', encoding='utf-8') as f:
        json.dump(intel_data, f, ensure_ascii=False, indent=2)


def load_cache(match_key):
    """加载缓存的搜索结果"""
    cache_file = os.path.join(CACHE_DIR, f'{match_key}.json')
    if os.path.exists(cache_file):
        with open(cache_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None


def make_match_key(home, away, league):
    """生成比赛缓存键"""
    return re.sub(r'[<>:"/\\|?*\s]', '_', f'{league}_{home}_{away}')[:60]


def build_search_data(intel_results):
    """将多个搜索结果合并为 framework_v4 的 search_data 格式"""
    data = {
        'home_form': '',
        'away_form': '',
        'injuries': [],
        'home_draw_rate': 0,
        'away_draw_rate': 0,
    }

    for r in intel_results.values():
        if isinstance(r, dict):
            if r.get('home_form'):
                data['home_form'] = r['home_form']
            if r.get('away_form'):
                data['away_form'] = r['away_form']
            if r.get('injuries'):
                data['injuries'].extend(r['injuries'])
            if r.get('home_draw_rate', 0) > data['home_draw_rate']:
                data['home_draw_rate'] = r['home_draw_rate']
            if r.get('away_draw_rate', 0) > data['away_draw_rate']:
                data['away_draw_rate'] = r['away_draw_rate']

    # 去重伤病
    data['injuries'] = list(set(data['injuries']))[:10]
    return data


# ========== 主入口 ==========
if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')

    if len(sys.argv) < 2:
        print('用法:')
        print('  python search_intel.py "主队 vs 客队" 联赛')
        print('  python search_intel.py --batch "D:/足彩/2026-05-27"')
        print('  python search_intel.py --cache show')
        print('  python search_intel.py --export "主队 vs 客队" 联赛')
        sys.exit(0)

    if sys.argv[1] == '--cache':
        if len(sys.argv) > 2 and sys.argv[2] == 'show':
            caches = os.listdir(CACHE_DIR)
            print(f'缓存 {len(caches)} 条:')
            for c in caches:
                with open(os.path.join(CACHE_DIR, c), 'r', encoding='utf-8') as f:
                    data = json.load(f)
                print(f'  {c}: {data.get("cached_at", "?")} — {data.get("match_name", "?")}')
        else:
            print(f'缓存目录: {CACHE_DIR}')
            print(f'缓存数量: {len(os.listdir(CACHE_DIR))}')
        sys.exit(0)

    if sys.argv[1] == '--batch':
        # 批量模式: 扫描目录, 为每场比赛生成搜索查询
        data_dir = sys.argv[2] if len(sys.argv) > 2 else '.'
        print(f'批量生成搜索查询: {data_dir}')
        for folder in sorted(os.listdir(data_dir)):
            full = os.path.join(data_dir, folder)
            if not os.path.isdir(full):
                continue
            meta_file = os.path.join(full, 'match_info.json')
            if os.path.exists(meta_file):
                with open(meta_file, 'r', encoding='utf-8') as f:
                    match = json.load(f)
                home = match.get('home', '?')
                away = match.get('away', '?')
                league = match.get('league', '?')
            else:
                # 从文件夹名解析
                parts = folder.split('_')
                if len(parts) >= 3:
                    league = parts[1]
                    home_away = parts[2] if len(parts) > 2 else folder
                    ha_parts = home_away.split('_')
                    home = ha_parts[0] if len(ha_parts) > 0 else '?'
                    away = ha_parts[1] if len(ha_parts) > 1 else '?'
                else:
                    continue

            queries = generate_queries(home, away, league)
            print(f'\n{league} {home} vs {away}:')
            for qtype, query in queries.items():
                print(f'  [{qtype}] {query}')
        sys.exit(0)

    if sys.argv[1] == '--export':
        # 导出为 framework_v4 可用的 search_data 格式
        match_str = sys.argv[2] if len(sys.argv) > 2 else ''
        league = sys.argv[3] if len(sys.argv) > 3 else '未知'

        parts = re.split(r'\s*vs\s*', match_str, flags=re.IGNORECASE)
        home = parts[0].strip() if len(parts) > 0 else '?'
        away = parts[1].strip() if len(parts) > 1 else '?'

        mkey = make_match_key(home, away, league)
        cached = load_cache(mkey)
        if cached:
            sd = cached.get('search_data', {})
            print(json.dumps(sd, ensure_ascii=False, indent=2))
            print(f'\n# 来源: 缓存 ({cached.get("cached_at")})', file=sys.stderr)
        else:
            queries = generate_queries(home, away, league)
            print('# 无缓存, 请先搜索以下内容:\n', file=sys.stderr)
            for qtype, query in queries.items():
                print(f'#   [{qtype}] {query}', file=sys.stderr)
            # 输出空的 search_data 模板
            sd = build_search_data({})
            print(json.dumps(sd, ensure_ascii=False, indent=2))
        sys.exit(0)

    # 单场模式: 输出搜索查询
    match_str = sys.argv[1]
    league = sys.argv[2] if len(sys.argv) > 2 else '未知'

    parts = re.split(r'\s*vs\s*', match_str, flags=re.IGNORECASE)
    home = parts[0].strip() if len(parts) > 0 else '?'
    away = parts[1].strip() if len(parts) > 1 else '?'

    print(f'联赛: {league}  主队: {home}  客队: {away}')
    print()
    queries = generate_queries(home, away, league)
    for qtype, query in queries.items():
        print(f'  [{qtype}] {query}')

    print()
    print('--- 复制以下内容让 Claude 搜索 ---')
    print()
    for qtype, query in queries.items():
        print(f'请搜索: {query}')
        print(f'提取: {qtype} 相关的结构化数据')
        print()
    print('搜索完成后, 将结果保存为:')
    mkey = make_match_key(home, away, league)
    print(f'  JSON 文件: {CACHE_DIR}/{mkey}.json')
