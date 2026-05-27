# -*- coding: utf-8 -*-
"""500.com 全量数据采集 — 下载所有日期、所有比赛、三种赔率页面
从 trade.500.com/jczq/?date= 获取比赛ID → 下载百家欧赔+亚盘对比+让球指数HTML
与用户手动下载格式完全相同
"""
import sys, os, re, json, time, urllib.request
import proxy_config

BASE_DIR = r'D:\足彩'
TRADE_URL = 'https://trade.500.com/jczq/?date={date}'
PAGES = {
    '百家欧赔': 'https://odds.500.com/fenxi/ouzhi-{mid}.shtml',
    '让球指数': 'https://odds.500.com/fenxi/rangqiu-{mid}.shtml',
    '亚盘对比': 'https://odds.500.com/fenxi/yazhi-{mid}.shtml',
}
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Referer': 'https://trade.500.com/jczq/',
}
DELAY = 0.3  # 请求间延迟(秒), 避免被ban


def fetch(url, encodings=['gb2312','gbk','utf-8','gb18030']):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=30) as resp:
        raw = resp.read()
    for enc in encodings:
        try: return raw.decode(enc)
        except: continue
    return raw.decode('utf-8', errors='replace')


def get_daily_match_ids(date_str):
    """获取某日所有比赛ID"""
    try:
        html = fetch(TRADE_URL.format(date=date_str))
        return list(set(re.findall(r'ouzhi-(\d+)\.shtml', html)))
    except Exception:
        return []


def detect_league_from_title(mid):
    """从比赛页面标题检测联赛"""
    try:
        html = fetch(PAGES['百家欧赔'].format(mid=mid))
        title = re.search(r'<title>(.*?)</title>', html)
        if title:
            t = title.group(1)
            for lg in ['挪超','瑞超','德甲','英超','意甲','西甲','日职','英甲',
                       '法甲','荷甲','葡超','巴甲','阿甲','美职','日乙','韩职',
                       '澳超','俄超','欧冠','欧联','欧协联','解放者杯','德乙',
                       '法乙','英冠','英甲','英乙','德丙联','世预赛','欧国联']:
                if lg in t: return lg
    except Exception:
        pass
    return '其他'


def download_match_files(mid, date_dir, league):
    """下载一场比赛的三个赔率页面"""
    folder = os.path.join(date_dir, '%s_%s' % (league, mid))
    os.makedirs(folder, exist_ok=True)

    # 检查是否已完整下载
    existing = os.listdir(folder) if os.path.exists(folder) else []
    if len([f for f in existing if f.endswith('.html')]) >= 3:
        return 'skip'

    downloaded = 0
    for ptype, url_template in PAGES.items():
        try:
            html = fetch(url_template.format(mid=mid))
            # 用比赛标题做文件名
            title = re.search(r'<title>(.*?)</title>', html)
            safe_name = re.sub(r'[<>:\"/\\|?*]', '_', title.group(1) if title else mid)[:80]
            fname = '%s-500彩票网.html' % safe_name
            with open(os.path.join(folder, fname), 'w', encoding='utf-8') as f:
                f.write(html)
            downloaded += 1
            time.sleep(DELAY)
        except Exception:
            pass

    return 'ok' if downloaded >= 2 else 'partial'


def bulk_download(start_date='2026-04-15', end_date=None):
    """全量下载日期范围内的所有比赛"""
    if end_date is None:
        end_date = time.strftime('%Y-%m-%d')

    from datetime import datetime, timedelta
    d = datetime.strptime(start_date, '%Y-%m-%d')
    end = datetime.strptime(end_date, '%Y-%m-%d')

    stats = {'dates': 0, 'matches': 0, 'downloaded': 0, 'skipped': 0, 'failed': 0}
    league_counts = {}

    while d <= end:
        date_str = d.strftime('%Y-%m-%d')
        ids = get_daily_match_ids(date_str)
        d += timedelta(days=1)

        if not ids:
            continue

        stats['dates'] += 1
        stats['matches'] += len(ids)
        date_dir = os.path.join(BASE_DIR, date_str)

        print('%s: %d matches' % (date_str, len(ids)))
        for mid in ids:
            lg = detect_league_from_title(mid)
            league_counts[lg] = league_counts.get(lg, 0) + 1

            result = download_match_files(mid, date_dir, lg)
            if result == 'ok':
                stats['downloaded'] += 1
                print('  %s [%s] OK' % (mid, lg))
            elif result == 'skip':
                stats['skipped'] += 1
            else:
                stats['failed'] += 1
                print('  %s [%s] PARTIAL' % (mid, lg))

        # 每5天打印一次统计
        if stats['dates'] % 5 == 0:
            print('  --- %d/%d dates, %d downloaded, %d skipped ---' % (
                stats['dates'], (end - datetime.strptime(start_date, '%Y-%m-%d')).days + 1,
                stats['downloaded'], stats['skipped']))

    print()
    print('=' * 50)
    print('  全量采集完成')
    print('=' * 50)
    print('  日期: %d' % stats['dates'])
    print('  比赛: %d' % stats['matches'])
    print('  新下载: %d' % stats['downloaded'])
    print('  已存在: %d' % stats['skipped'])
    print('  失败: %d' % stats['failed'])
    print()
    print('  联赛分布:')
    for lg, n in sorted(league_counts.items(), key=lambda x: -x[1]):
        print('    %s: %d' % (lg, n))

    # 保存统计
    with open(os.path.join(BASE_DIR, 'collection_stats.json'), 'w', encoding='utf-8') as f:
        json.dump({'stats': stats, 'leagues': league_counts,
                   'collected_at': time.strftime('%Y-%m-%d %H:%M:%S')},
                  f, ensure_ascii=False, indent=2)


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')

    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('--from', dest='start', default='2026-04-15')
    p.add_argument('--to', dest='end', default=None)
    p.add_argument('--dry-run', action='store_true')
    args = p.parse_args()

    if args.dry_run:
        # 先统计有多少数据
        from datetime import datetime, timedelta
        d = datetime.strptime(args.start, '%Y-%m-%d')
        end = datetime.strptime(args.end, '%Y-%m-%d') if args.end else datetime.now()
        total_ids = 0
        total_dates = 0
        while d <= end:
            ids = get_daily_match_ids(d.strftime('%Y-%m-%d'))
            if ids:
                total_ids += len(ids)
                total_dates += 1
                print('%s: %d matches' % (d.strftime('%Y-%m-%d'), len(ids)))
            d += timedelta(days=1)
        print()
        print('Dry run: %d dates, %d matches, est. %d files, est. %.0f min' % (
            total_dates, total_ids, total_ids * 3, total_ids * 3 * DELAY / 60))
    else:
        bulk_download(args.start, args.end)
