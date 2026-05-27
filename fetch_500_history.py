# -*- coding: utf-8 -*-
"""500.com 历史数据采集器 — 回溯采集完整赔率数据(与用户手动下载同等深度)
发现: trade.500.com/jczq/?date=YYYY-MM-DD 列出任意日期的比赛ID

用法:
  python fetch_500_history.py --from 2026-05-01 --to 2026-05-27
  python fetch_500_history.py --date 2026-05-25
  python fetch_500_history.py --leagues 挪超,瑞超  # 只要挪超/瑞超
"""
import sys, os, re, json, time, urllib.request, urllib.parse
import proxy_config

BASE_DIR = r'D:\足彩'
TRADE_URL = 'https://trade.500.com/jczq/?date={date}'
OUZHI_URL = 'https://odds.500.com/fenxi/ouzhi-{mid}.shtml'
YAZHI_URL = 'https://odds.500.com/fenxi/yazhi-{mid}.shtml'
RANGQIU_URL = 'https://odds.500.com/fenxi/rangqiu-{mid}.shtml'

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Referer': 'https://trade.500.com/jczq/',
}

TARGET_LEAGUES = ['挪超', '瑞超', '德甲', '英超', '意甲', '西甲', '日职', '英甲']


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


def get_match_ids(date_str):
    """从 trade.500.com 获取指定日期的比赛ID列表"""
    url = TRADE_URL.format(date=date_str)
    html = fetch_page(url)

    # 提取比赛ID列表 (trade.500.com页面中联赛名可能在页面上方, 不在每行)
    matches = []
    for mid_match in re.finditer(r'ouzhi-(\d+)\.shtml', html):
        mid = mid_match.group(1)
        matches.append({'id': mid, 'league': '待检测'})

    return matches


def download_match(mid, target_dir, league='其他'):
    """下载单场比赛的三个赔率页面 (与fetch_500.py相同格式)"""
    folder = os.path.join(target_dir, '%s_%s' % (league, mid))
    os.makedirs(folder, exist_ok=True)

    # 先获取比赛名
    try:
        html = fetch_page(OUZHI_URL.format(mid=mid))
        title = re.search(r'<title>(.*?)</title>', html)
        match_name = title.group(1).split('-')[0] if title else mid
    except Exception:
        match_name = mid

    pages = {
        '百家欧赔': OUZHI_URL.format(mid=mid),
        '让球指数': RANGQIU_URL.format(mid=mid),
        '亚盘对比': YAZHI_URL.format(mid=mid),
    }

    success = 0
    for ptype, url in pages.items():
        try:
            html = fetch_page(url)
            safe_name = re.sub(r'[<>:\"/\\|?*]', '_', match_name)[:60]
            fname = '%s-%s-500彩票网.html' % (safe_name, ptype)
            path = os.path.join(folder, fname)
            with open(path, 'w', encoding='utf-8') as f:
                f.write(html)
            success += 1
        except Exception:
            pass
        time.sleep(0.3)

    # 元数据
    with open(os.path.join(folder, 'match_info.json'), 'w', encoding='utf-8') as f:
        json.dump({
            'id': mid, 'name': match_name, 'league': league,
            'downloaded_at': time.strftime('%Y-%m-%d %H:%M:%S'),
        }, f, ensure_ascii=False, indent=2)

    return success == 3


def collect_date_range(start_date, end_date, leagues_filter=None):
    """采集日期范围内的所有比赛"""
    total_downloaded = 0
    total_found = 0

    from datetime import datetime, timedelta
    d = datetime.strptime(start_date, '%Y-%m-%d')
    end = datetime.strptime(end_date, '%Y-%m-%d')

    while d <= end:
        date_str = d.strftime('%Y-%m-%d')
        try:
            matches = get_match_ids(date_str)
        except Exception as e:
            print('%s: 获取失败 (%s)' % (date_str, str(e)[:40]))
            d += timedelta(days=1)
            continue

        # 过滤联赛
        if leagues_filter:
            matches = [m for m in matches if m['league'] in leagues_filter]

        if not matches:
            d += timedelta(days=1)
            continue

        target_dir = os.path.join(BASE_DIR, date_str)
        for m in matches:
            mid = m['id']
            lg = m['league']
            total_found += 1

            # 检查是否已下载
            folder = os.path.join(target_dir, '%s_%s' % (lg, mid))
            if os.path.exists(folder) and os.listdir(folder):
                continue

            print('  [%s] %s ID=%s' % (date_str, lg, mid))
            try:
                if download_match(mid, target_dir, lg):
                    total_downloaded += 1
            except Exception as e:
                print('    FAIL: %s' % str(e)[:40])
            time.sleep(0.5)

        d += timedelta(days=1)

    print('Total: %d found, %d newly downloaded' % (total_found, total_downloaded))
    return total_downloaded


# ========== 主入口 ==========
if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    import argparse

    parser = argparse.ArgumentParser(description='500.com历史数据采集器')
    parser.add_argument('--date', help='单个日期 YYYY-MM-DD')
    parser.add_argument('--from', dest='start', help='起始日期')
    parser.add_argument('--to', dest='end', help='结束日期')
    parser.add_argument('--leagues', help='联赛过滤, 逗号分隔')
    args = parser.parse_args()

    leagues_filter = None
    if args.leagues:
        leagues_filter = [l.strip() for l in args.leagues.split(',')]

    if args.date:
        matches = get_match_ids(args.date)
        if leagues_filter:
            matches = [m for m in matches if m['league'] in leagues_filter]
        print('%s: %d matches' % (args.date, len(matches)))
        for m in matches:
            print('  [%s] ID=%s' % (m['league'], m['id']))
    elif args.start and args.end:
        collect_date_range(args.start, args.end, leagues_filter)
    else:
        print('用法:')
        print('  python fetch_500_history.py --date 2026-05-25')
        print('  python fetch_500_history.py --from 2026-05-01 --to 2026-05-27')
        print('  python fetch_500_history.py --from 2026-04-01 --to 2026-05-27 --leagues 挪超,瑞超')
