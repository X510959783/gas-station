# -*- coding: utf-8 -*-
"""赛季数据采集器 — 自动收集指定联赛整个赛季的全部比赛
用法:
  python season_collector.py --league 挪超          # 采集挪超当前赛季
  python season_collector.py --league 英超 --season 2025  # 指定赛季
  python season_collector.py --all-calibrated        # 采集全部8个校准联赛
  python season_collector.py --status               # 查看已采集数据统计

数据流:
  500.com联赛页 → 轮次列表 → 每轮比赛ID → 下载欧赔+亚盘HTML → 赛后自动获取比分
"""
import sys, os, re, json, time, urllib.request
import proxy_config

BASE_DIR = r'D:\足彩'
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

# 联赛名 → 500.com联赛ID (从liansai.500.com提取)
LEAGUE_IDS = {
    '挪超': '9080',    # Eliteserien
    '瑞超': '9110',    # Allsvenskan (待验证)
    '德甲': '9124',    # Bundesliga (待验证)
    '英超': '9117',    # Premier League (待验证)
    '意甲': '9118',    # Serie A (待验证)
    '西甲': '9080',    # 不确定, 需要验证
    '日职': None,      # 需要查找
    '英甲': None,      # 需要查找
}

# 先用已验证的联赛ID
VERIFIED_IDS = {
    '挪超': '9080',
}


def fetch_page(url, encodings=['gb2312', 'gbk', 'utf-8', 'gb18030']):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=30) as resp:
        raw = resp.read()
    for enc in encodings:
        try:
            return raw.decode(enc)
        except (UnicodeDecodeError, LookupError):
            continue
    return raw.decode('utf-8', errors='replace')


def discover_league_id(league_name):
    """从500.com搜索联赛ID"""
    # 从已知映射返回
    if league_name in VERIFIED_IDS:
        return VERIFIED_IDS[league_name]

    # 搜索联赛
    search_url = f'https://liansai.500.com/search?keyword={league_name}'
    try:
        html = fetch_page(search_url)
        ids = re.findall(r'/zuqiu-(\d+)/', html)
        if ids:
            return ids[0]
    except Exception:
        pass
    return None


def get_season_rounds(league_id):
    """获取当前赛季所有轮次的比赛"""
    url = f'https://liansai.500.com/zuqiu-{league_id}/'
    html = fetch_page(url)

    matches = []

    # 找赛程表格: class="ldata" 或包含比分的行
    rows = re.findall(r'<tr[^>]*>(.*?)</tr>', html, re.DOTALL)
    for row in rows:
        # 找比赛链接 ouzhi-{id}.shtml
        match_id = re.search(r'ouzhi-(\d+)\.shtml', row)
        if not match_id:
            continue

        mid = match_id.group(1)
        tds = re.findall(r'<td[^>]*>(.*?)</td>', row, re.DOTALL)
        texts = []
        for td in tds:
            clean = re.sub(r'<[^>]+>', '', td).strip()
            clean = re.sub(r'\s+', ' ', clean)
            if clean:
                texts.append(clean)

        if len(texts) < 4:
            continue

        # 格式: [轮次, 日期, 时间, 主队, 比分, 客队, ...]
        match_info = {
            'id': mid,
            'round': texts[0] if len(texts) > 0 else '',
            'date': texts[1] if len(texts) > 1 else '',
            'time': texts[2] if len(texts) > 2 else '',
            'home': '',
            'away': '',
            'score': '',
        }

        # 找主客队和比分
        for i, t in enumerate(texts):
            if t == 'VS' or t == 'vs':
                if i > 0:
                    match_info['home'] = texts[i-1]
                if i + 1 < len(texts):
                    match_info['away'] = texts[i+1]
                # 比分可能在主队前或客队后
                for j in range(max(0, i-2), min(len(texts), i+3)):
                    score_match = re.search(r'(\d+)\s*[-:：]\s*(\d+)', texts[j])
                    if score_match:
                        match_info['score'] = texts[j]
                break

        matches.append(match_info)

    return matches


def collect_season(league_name, data_dir=None):
    """采集一个联赛的整个赛季数据"""
    if data_dir is None:
        data_dir = os.path.join(BASE_DIR, f'season_{league_name}')

    league_id = discover_league_id(league_name)
    if not league_id:
        print(f'未找到联赛ID: {league_name}')
        return None

    print(f'联赛: {league_name} (ID: {league_id})')
    print(f'数据目录: {data_dir}')

    matches = get_season_rounds(league_id)
    print(f'找到 {len(matches)} 场比赛')

    if not matches:
        print('  未找到比赛数据 (页面结构可能已变)')
        return None

    os.makedirs(data_dir, exist_ok=True)

    # 保存元数据
    meta = {
        'league': league_name,
        'league_id': league_id,
        'collected_at': time.strftime('%Y-%m-%d %H:%M:%S'),
        'total_matches': len(matches),
        'matches': matches,
    }
    with open(os.path.join(data_dir, 'season_meta.json'), 'w', encoding='utf-8') as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    # 打印摘要
    has_results = sum(1 for m in matches if m.get('score'))
    upcoming = len(matches) - has_results
    print(f'  已完赛: {has_results} | 未开始: {upcoming}')
    print(f'  元数据已保存: {data_dir}/season_meta.json')

    return meta


def get_collection_status():
    """查看已采集数据统计"""
    print('=' * 50)
    print('  数据采集状态')
    print('=' * 50)

    total = 0
    for d in sorted(os.listdir(BASE_DIR)):
        full = os.path.join(BASE_DIR, d)
        if not os.path.isdir(full):
            continue

        # 统计比赛文件夹数
        match_dirs = [f for f in os.listdir(full)
                      if os.path.isdir(os.path.join(full, f))]
        n = len(match_dirs)
        total += n

        # 检查是否有赛季元数据
        meta_file = os.path.join(full, 'season_meta.json')
        if os.path.exists(meta_file):
            with open(meta_file, 'r', encoding='utf-8') as f:
                meta = json.load(f)
            print(f'  {d}: {meta["total_matches"]}场 ({meta["league"]})')
        else:
            if n > 0:
                print(f'  {d}: {n}场 (日数据)')

    print(f'  总计: {total} 场比赛目录')
    return total


# ========== 主入口 ==========
if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')

    if len(sys.argv) < 2 or sys.argv[1] == '--status':
        get_collection_status()
        sys.exit(0)

    if sys.argv[1] == '--league':
        league = sys.argv[2] if len(sys.argv) > 2 else '挪超'
        collect_season(league)
    elif sys.argv[1] == '--all-calibrated':
        for lg in VERIFIED_IDS:
            print(f'\n{"="*40}')
            collect_season(lg)
            time.sleep(2)
    elif sys.argv[1] == '--discover':
        lg = sys.argv[2] if len(sys.argv) > 2 else '英超'
        lid = discover_league_id(lg)
        if lid:
            print(f'{lg} -> 500.com ID: {lid}')
            # 试采集一轮
            matches = get_season_rounds(lid)
            print(f'当前页面有 {len(matches)} 场比赛')
            for m in matches[:5]:
                print(f'  {m}')
        else:
            print(f'未找到: {lg}')
    else:
        print('用法:')
        print('  python season_collector.py --status')
        print('  python season_collector.py --league 挪超')
        print('  python season_collector.py --discover 英超')
        print('  python season_collector.py --all-calibrated')
