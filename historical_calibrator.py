# -*- coding: utf-8 -*-
"""历史数据校准器 — 用 Football-Data.co.uk 历史赔率数据校准框架参数
每个赛季300-380场比赛+Pinnacle赔率+赛果 → 真正的统计校准
"""
import sys, os, re, csv, json, math, urllib.request
import proxy_config
from io import StringIO

# Football-Data.co.uk 联赛代码
FD_LEAGUES = {
    '英超': 'E0', '德甲': 'D1', '意甲': 'I1', '西甲': 'SP1',
    '法甲': 'F1', '英冠': 'E1', '荷甲': 'N1', '葡超': 'P1',
}
CACHE_DIR = os.path.join(os.path.dirname(__file__), '.historical_cache')
os.makedirs(CACHE_DIR, exist_ok=True)
HEADERS = {'User-Agent': 'Mozilla/5.0'}


def download_season(league_code, season='2425'):
    """下载一个赛季的CSV"""
    cache_file = os.path.join(CACHE_DIR, '%s_%s.csv' % (league_code, season))
    if os.path.exists(cache_file):
        with open(cache_file, 'r', encoding='utf-8') as f:
            return f.read()

    url = 'https://www.football-data.co.uk/mmz4281/%s/%s.csv' % (season, league_code)
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=30) as resp:
        raw = resp.read()
    text = raw.decode('utf-8-sig', errors='replace')

    with open(cache_file, 'w', encoding='utf-8') as f:
        f.write(text)
    return text


def parse_matches(csv_text):
    """解析CSV, 提取每场比赛的 Pinnacle赔率+赛果"""
    reader = csv.DictReader(StringIO(csv_text))
    matches = []
    for row in reader:
        try:
            ftr = row.get('FTR', '').strip()
            if ftr not in ('H', 'D', 'A'):
                continue

            # Pinnacle closing odds (最接近截止时间)
            psh = float(row.get('PSCH', row.get('PSH', 0)) or 0)
            psd = float(row.get('PSCD', row.get('PSD', 0)) or 0)
            psa = float(row.get('PSCA', row.get('PSA', 0)) or 0)

            # Bet365 closing odds (备选)
            b365h = float(row.get('B365CH', row.get('B365H', 0)) or 0)
            b365d = float(row.get('B365CD', row.get('B365D', 0)) or 0)
            b365a = float(row.get('B365CA', row.get('B365A', 0)) or 0)

            # 如果没有Pinnacle, 用Bet365
            if psh == 0 and b365h > 0:
                psh, psd, psa = b365h, b365d, b365a

            if psh == 0:
                continue

            # 隐含概率 (去掉overround)
            total = 1/psh + 1/psd + 1/psa
            p_home = (1/psh) / total
            p_draw = (1/psd) / total
            p_away = (1/psa) / total

            matches.append({
                'date': row.get('Date', ''),
                'home': row.get('HomeTeam', ''),
                'away': row.get('AwayTeam', ''),
                'h_goals': int(row.get('FTHG', 0)),
                'a_goals': int(row.get('FTAG', 0)),
                'result': ftr,
                'result_cn': {'H': '主胜', 'D': '平局', 'A': '客胜'}[ftr],
                'ps_h': psh, 'ps_d': psd, 'ps_a': psa,
                'p_home': round(p_home, 4),
                'p_draw': round(p_draw, 4),
                'p_away': round(p_away, 4),
            })
        except (ValueError, KeyError):
            continue
    return matches


def calibrate_league(league_name, seasons=None):
    """用历史数据校准联赛参数: draw_rate, home_win_rate, overconf_threshold"""
    code = FD_LEAGUES.get(league_name)
    if not code:
        print('%s: 不在Football-Data.co.uk覆盖范围' % league_name)
        return None

    if seasons is None:
        seasons = ['2425', '2324', '2223']

    all_matches = []
    for s in seasons:
        try:
            csv_text = download_season(code, s)
            matches = parse_matches(csv_text)
            all_matches.extend(matches)
            print('  %s赛季: %d场' % (s, len(matches)))
        except Exception as e:
            print('  %s赛季: 失败 (%s)' % (s, str(e)[:40]))

    if not all_matches:
        return None

    n = len(all_matches)

    # 实际统计
    home_wins = sum(1 for m in all_matches if m['result'] == 'H')
    draws = sum(1 for m in all_matches if m['result'] == 'D')
    away_wins = sum(1 for m in all_matches if m['result'] == 'A')

    # 不同置信度水平的Pinnacle准确率
    # 按隐含概率分桶
    bins = [(0, 0.40), (0.40, 0.50), (0.50, 0.60), (0.60, 0.70), (0.70, 1.0)]
    bin_stats = []
    for lo, hi in bins:
        bucket = [m for m in all_matches if lo <= m['p_home'] < hi]
        if len(bucket) < 5:
            continue
        correct = sum(1 for m in bucket
                      if (m['p_home'] > m['p_away'] and m['result'] == 'H')
                      or (m['p_home'] < m['p_away'] and m['result'] == 'A'))
        bin_stats.append({
            'range': '%.0f-%.0f%%' % (lo*100, hi*100),
            'n': len(bucket),
            'accuracy': round(correct / len(bucket), 3),
            'home_win_rate': round(sum(1 for m in bucket if m['result']=='H')/len(bucket), 3),
            'draw_rate': round(sum(1 for m in bucket if m['result']=='D')/len(bucket), 3),
        })

    # 找出过度自信阈值: 哪个概率以上准确率反而下降
    overconf_candidates = []
    for bs in bin_stats:
        if bs['n'] >= 10:
            overconf_candidates.append((float(bs['range'].split('-')[0])/100, bs['accuracy']))

    # 过度自信阈值 = 准确率开始下降的点
    threshold = 0.65
    for i in range(len(overconf_candidates)-1):
        if overconf_candidates[i+1][1] < overconf_candidates[i][1] - 0.03:
            threshold = overconf_candidates[i][0]
            break

    result = {
        'league': league_name,
        'total_matches': n,
        'seasons': seasons,
        'home_win_rate': round(home_wins / n, 3),
        'draw_rate': round(draws / n, 3),
        'away_win_rate': round(away_wins / n, 3),
        'overconf_threshold': round(threshold, 2),
        'bin_stats': bin_stats,
        'calibrated_at': __import__('time').strftime('%Y-%m-%d %H:%M'),
    }

    return result


def print_calibration(result):
    """打印校准结果"""
    if not result:
        return
    print('=' * 55)
    print('  %s 历史校准 (%d场, %s)' % (
        result['league'], result['total_matches'],
        '+'.join(result['seasons'])))
    print('=' * 55)
    print('  主胜: %.1f%%  平局: %.1f%%  客胜: %.1f%%' % (
        result['home_win_rate']*100, result['draw_rate']*100,
        result['away_win_rate']*100))
    print('  过度自信阈值: %.0f%%' % (result['overconf_threshold']*100))
    print()
    print('  分桶统计:')
    print('  %10s %6s %8s %8s %8s' % ('概率区间','场次','准确率','主胜率','平局率'))
    for bs in result['bin_stats']:
        print('  %10s %6d %7.1f%% %7.1f%% %7.1f%%' % (
            bs['range'], bs['n'], bs['accuracy']*100,
            bs['home_win_rate']*100, bs['draw_rate']*100))
    print('=' * 55)


# ========== 主入口 ==========
if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')

    if len(sys.argv) < 2:
        print('用法: python historical_calibrator.py <联赛> [赛季]')
        print('  python historical_calibrator.py 英超')
        print('  python historical_calibrator.py 英超 2425')
        print('  python historical_calibrator.py --all')
        sys.exit(0)

    if sys.argv[1] == '--all':
        for lg in ['英超', '德甲', '意甲', '西甲']:
            print()
            r = calibrate_league(lg)
            print_calibration(r)
    else:
        lg = sys.argv[1]
        seasons = [sys.argv[2]] if len(sys.argv) > 2 else None
        r = calibrate_league(lg, seasons)
        print_calibration(r)
