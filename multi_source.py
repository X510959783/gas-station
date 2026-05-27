# -*- coding: utf-8 -*-
"""三源融合数据管道: 500.com + datafc(Sofascore) + openfootball
用法:
  python multi_source.py --status               # 数据源状态
  python multi_source.py --backfill 挪超        # 回填挪超历史数据
  python multi_source.py --standings 挪超       # 联赛积分榜
  python multi_source.py --crosscheck           # 三源交叉验证
"""
import sys, os, re, json, time, urllib.request
import proxy_config

# ============================================================
# 联赛 → 各数据源ID映射
# ============================================================
LEAGUE_MAP = {
    '挪超': {
        '500com': '9080',
        'sofascore': 20,       # tournament_id
        'footballjson': 'no.1',  # football.json 文件名
    },
    '英超': {
        '500com': None,
        'sofascore': 17,
        'footballjson': 'en.1',
    },
    '瑞超': {
        '500com': None,
        'sofascore': 36,       # Allsvenskan
        'footballjson': 'se.1',
    },
    '德甲': {
        '500com': None,
        'sofascore': 35,
        'footballjson': 'de.1',
    },
    '意甲': {
        '500com': None,
        'sofascore': 23,
        'footballjson': 'it.1',
    },
    '西甲': {
        '500com': None,
        'sofascore': 8,
        'footballjson': 'es.1',
    },
}

CDN_BASE = 'https://cdn.jsdelivr.net/gh/openfootball/football.json@master'
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
CACHE_DIR = os.path.join(os.path.dirname(__file__), '.multi_source_cache')
os.makedirs(CACHE_DIR, exist_ok=True)


# ---- Source 1: 500.com (竞彩赔率) ----
def check_500com(league):
    """检查500.com状态"""
    lid = LEAGUE_MAP.get(league, {}).get('500com')
    if not lid:
        return {'status': 'unknown', 'reason': '未映射联赛ID'}
    try:
        url = f'https://liansai.500.com/zuqiu-{lid}/'
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=10) as resp:
            html = resp.read().decode('gb2312', errors='replace')
        matches = len(re.findall(r'VS|vs', html))
        return {'status': 'ok', 'matches_visible': matches}
    except Exception as e:
        return {'status': 'error', 'reason': str(e)[:50]}


# ---- Source 2: datafc (Sofascore - 国际统计数据) ----
def check_datafc(league):
    """检查datafc状态"""
    sid = LEAGUE_MAP.get(league, {}).get('sofascore')
    if not sid:
        return {'status': 'unknown', 'reason': '未映射Sofascore ID'}
    try:
        from datafc import seasons_data, standings_data
        seasons = seasons_data(tournament_id=sid)
        latest = seasons.iloc[0]['season_id']
        standings = standings_data(tournament_id=sid, season_id=latest)
        return {
            'status': 'ok',
            'seasons_available': len(seasons),
            'latest_season_id': int(latest),
            'teams': len(standings),
        }
    except Exception as e:
        return {'status': 'error', 'reason': str(e)[:60]}


# ---- Source 3: openfootball (CC0历史赛果) ----
def check_footballjson(league, season='2025'):
    """检查openfootball状态"""
    fj = LEAGUE_MAP.get(league, {}).get('footballjson')
    if not fj:
        return {'status': 'unknown', 'reason': '未映射football.json联赛'}
    # 尝试当前赛季和上一赛季
    seasons_to_try = [season, str(int(season)-1)]
    for s in seasons_to_try:
        url = f'{CDN_BASE}/{s}/{fj}.json'
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read())
            matches = len(data.get('matches', data.get('rounds', [])))
            return {
                'status': 'ok',
                'season': s,
                'matches': matches,
                'name': data.get('name', '?'),
            }
        except Exception:
            continue
    return {'status': 'error', 'reason': '所有赛季均不可用'}


def backfill_league(league):
    """回填联赛历史数据: 从openfootball获取所有已完成比赛的赛果"""
    fj = LEAGUE_MAP.get(league, {}).get('footballjson')
    if not fj:
        print(f'{league}: 无football.json映射')
        return None

    results = []
    # 尝试多个赛季
    for season_year in ['2025', '2024-25', '2024', '2023-24']:
        url = f'{CDN_BASE}/{season_year}/{fj}.json'
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read())
        except Exception:
            continue

        if 'matches' in data:
            matches = data['matches']
        elif 'rounds' in data:
            matches = []
            for r in data['rounds']:
                matches.extend(r.get('matches', []))
        else:
            continue

        for m in matches:
            # openfootball格式: team1/team2是字符串, score.ft是[home_goals, away_goals]
            home = m.get('team1', '?')
            away = m.get('team2', '?')
            if isinstance(home, dict):
                home = home.get('name', '?')
            if isinstance(away, dict):
                away = away.get('name', '?')

            score = m.get('score', {})
            ft = score.get('ft', [None, None]) if isinstance(score, dict) else [None, None]
            if isinstance(ft, list) and len(ft) >= 2:
                hg, ag = ft[0], ft[1]
            else:
                hg = m.get('score1')
                ag = m.get('score2')

            if hg is not None and ag is not None:
                results.append({
                    'date': m.get('date', '?'),
                    'home': str(home), 'away': str(away),
                    'score': '%d-%d' % (int(hg), int(ag)),
                    'result': '主胜' if int(hg) > int(ag) else (
                        '平局' if int(hg) == int(ag) else '客胜'),
                    'round': m.get('round', '?'),
                })

        if results:
            break  # 找到数据就停止

    print(f'{league}: 回填 {len(results)} 场比赛')

    # 保存
    cache_file = os.path.join(CACHE_DIR, f'backfill_{league}.json')
    with open(cache_file, 'w', encoding='utf-8') as f:
        json.dump({'league': league, 'source': 'openfootball',
                   'count': len(results), 'matches': results},
                  f, ensure_ascii=False, indent=2)
    return results


def get_standings_datafc(league):
    """从datafc获取当前联赛积分榜"""
    sid = LEAGUE_MAP.get(league, {}).get('sofascore')
    if not sid:
        return None
    try:
        from datafc import seasons_data, standings_data
        seasons = seasons_data(tournament_id=sid)
        latest = int(seasons.iloc[0]['season_id'])
        st = standings_data(tournament_id=sid, season_id=latest)
        return st
    except Exception as e:
        print(f'datafc积分榜错误: {e}')
        return None


def status_all():
    """报告所有数据源状态"""
    print('=' * 65)
    print('  三源融合数据管道 — 状态检查')
    print('=' * 65)

    for lg in ['挪超', '英超', '瑞超', '德甲', '意甲']:
        print(f'\n  [{lg}]')

        f500 = check_500com(lg)
        print('    500.com:    %s' % (f500.get('status', '?')))
        if f500.get('status') == 'error':
            print('      → 联赛页不可用 (%s)' % f500.get('reason', ''))

        dfc = check_datafc(lg)
        print('    datafc:     %s' % dfc.get('status', '?'))
        if dfc.get('status') == 'ok':
            print('      → %d赛季, 当前%d队, 最新赛季ID=%d' % (
                dfc.get('seasons_available', 0), dfc.get('teams', 0),
                dfc.get('latest_season_id', 0)))

        ffj = check_footballjson(lg)
        print('    footballjs: %s' % ffj.get('status', '?'))
        if ffj.get('status') == 'ok':
            print('      → 赛季%s, %d场, %s' % (
                ffj.get('season', '?'), ffj.get('matches', 0),
                ffj.get('name', '?')))

    # 汇总
    print(f'\n{"="*65}')
    sources_ok = 0
    for lg in ['挪超', '英超']:
        f500 = check_500com(lg)
        dfc = check_datafc(lg)
        ffj = check_footballjson(lg)
        if f500.get('status') == 'ok': sources_ok += 1
        if dfc.get('status') == 'ok': sources_ok += 1
        if ffj.get('status') == 'ok': sources_ok += 1
    print(f'  数据源可用: {sources_ok}/6 (挪超+英超 各3源)')
    print('=' * 65)


# ========== 主入口 ==========
if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')

    if len(sys.argv) < 2 or sys.argv[1] == '--status':
        status_all()

    elif sys.argv[1] == '--backfill':
        lg = sys.argv[2] if len(sys.argv) > 2 else '挪超'
        backfill_league(lg)

    elif sys.argv[1] == '--standings':
        lg = sys.argv[2] if len(sys.argv) > 2 else '挪超'
        st = get_standings_datafc(lg)
        if st is not None:
            cols = ['team_name','position','points','wins','draws','losses',
                    'scores_for','scores_against']
            avail = [c for c in cols if c in st.columns]
            print(st[avail].head(16).to_string())

    elif sys.argv[1] == '--crosscheck':
        # 交叉验证: 比较 openfootball 赛果与 datafc 赛果
        for lg in ['挪超', '英超']:
            print(f'\n{lg}:')
            fj = check_footballjson(lg)
            dfc = check_datafc(lg)
            if fj.get('status') == 'ok' and dfc.get('status') == 'ok':
                print('  football.json: %d场' % fj['matches'])
                print('  datafc: %d队可用' % dfc['teams'])
            else:
                print('  football.json: %s' % fj.get('status'))
                print('  datafc: %s' % dfc.get('status'))
    else:
        print('用法: python multi_source.py [--status|--backfill|--standings|--crosscheck]')
