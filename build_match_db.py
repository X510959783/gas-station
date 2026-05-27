# -*- coding: utf-8 -*-
"""全量数据解析: 574场比赛 → 结构化数据库
用法: python build_match_db.py
输出: match_db_full.json (结构化数据库) + calibration_report.json (校准报告)
"""
import sys, os, re, json, time

sys.path.insert(0, os.path.dirname(__file__))
import parse_odds
from probability_engine import oo_epc_convert, correct_fl_bias

BASE_DIR = r'D:\足彩'
OUTPUT_DB = os.path.join(os.path.dirname(__file__), 'match_db_full.json')
OUTPUT_CALIBRATION = os.path.join(os.path.dirname(__file__), 'calibration_report.json')


def parse_single_match(folder_path):
    """解析单场比赛, 提取关键指标"""
    try:
        data = parse_odds.parse_folder(folder_path)
        euro = data['euro_odds']['companies']
    except Exception:
        return None

    companies = list(euro.values())
    if len(companies) < 5:
        return None

    # 基础指标
    all_iw = [c['odds']['instant'][0] for c in companies[:30] if c['odds']['instant'][0] > 0]
    all_iw_init = [c['odds']['init'][0] for c in companies[:30] if c['odds']['init'][0] > 0]

    if len(all_iw) < 5:
        return None

    odds_list = [(c['odds']['instant'][0], c['odds']['instant'][1], c['odds']['instant'][2])
                 for c in companies[:30] if len(c.get('odds', {}).get('instant', [])) >= 3
                 and c['odds']['instant'][0] > 0]

    if len(odds_list) < 5:
        return None

    probs = oo_epc_convert(odds_list)
    p_home = correct_fl_bias(probs['home'])
    p_draw = correct_fl_bias(probs['draw'])
    p_away = correct_fl_bias(probs['away'])

    w_range = max(all_iw) - min(all_iw) if len(all_iw) > 1 else 0
    prob_gap = abs(p_home - p_away)
    avg_home_o = sum(all_iw) / len(all_iw)

    up = sum(1 for i in range(min(len(all_iw), len(all_iw_init)))
             if all_iw[i] > all_iw_init[i] + 0.02)
    down = sum(1 for i in range(min(len(all_iw), len(all_iw_init)))
               if all_iw[i] < all_iw_init[i] - 0.02)

    # Pinnacle方向
    pin = None
    for seq, c in euro.items():
        if 'Pi' in c.get('name', ''):
            pin = c
            break
    pin_dir = '稳定'
    if pin:
        pi, pn = pin['odds']['instant'][0], pin['odds']['init'][0]
        if pi < pn - 0.02: pin_dir = '看好'
        elif pi > pn + 0.02: pin_dir = '看衰'

    # 从文件夹名提取联赛、比分
    league = '其他'
    score = None
    for f in os.listdir(folder_path):
        if f.endswith('.html'):
            # 从文件名提取联赛
            for lg in ['挪超','瑞超','德甲','英超','意甲','西甲','日职','英甲',
                       '法甲','荷甲','葡超','巴甲','阿甲','美职','日乙','韩职',
                       '澳超','俄超','欧冠','欧联','欧协联','解放者杯','德乙',
                       '法乙','英冠','德丙联']:
                if lg in f: league = lg; break
            # 从文件夹名提取比分 (用户手动数据有比分)
            folder_name = os.path.basename(folder_path)
            score_match = re.search(r'(\d+)[\.\-:：](\d+)', folder_name)
            if score_match:
                score = (int(score_match.group(1)), int(score_match.group(2)))
            break

    # 从 match_info.json 获取元数据 (含比分)
    meta_file = os.path.join(folder_path, 'match_info.json')
    match_name = ''
    if os.path.exists(meta_file):
        with open(meta_file, 'r', encoding='utf-8') as f:
            meta = json.load(f)
        match_name = meta.get('name', '')
        if meta.get('league'):
            league = meta['league']
        # 从match_info.json读比分
        if meta.get('score') and not score:
            parts = meta['score'].split('-')
            if len(parts) == 2:
                try:
                    score = (int(parts[0]), int(parts[1]))
                except ValueError:
                    pass

    return {
        'league': league,
        'name': match_name[:80],
        'date': os.path.basename(os.path.dirname(folder_path)),
        'score': '%d-%d' % score if score else None,
        'result': '主胜' if score and score[0] > score[1]
                   else ('平局' if score and score[0] == score[1]
                         else ('客胜' if score else None)),
        'companies': len(companies),
        'p_home': round(p_home, 4),
        'p_draw': round(p_draw, 4),
        'p_away': round(p_away, 4),
        'avg_home_odds': round(avg_home_o, 2),
        'w_range': round(w_range, 2),
        'prob_gap': round(prob_gap, 4),
        'up': up, 'down': down,
        'pin_dir': pin_dir,
        'l1_c1': w_range < 0.50,
        'l1_c2': prob_gap > 0.05,
        'l1_c3': p_home < 0.55,
        'l1_c4': True,  # 简化, 实际需要亚盘数据
    }


def build_database():
    """遍历所有比赛文件夹, 构建结构化数据库"""
    all_matches = []
    total_folders = 0
    parse_errors = 0

    for date_dir in sorted(os.listdir(BASE_DIR)):
        date_path = os.path.join(BASE_DIR, date_dir)
        if not os.path.isdir(date_path):
            continue

        for folder in sorted(os.listdir(date_path)):
            folder_path = os.path.join(date_path, folder)
            if not os.path.isdir(folder_path):
                continue
            # 跳过 test 目录
            if 'test' in folder.lower():
                continue

            total_folders += 1
            result = parse_single_match(folder_path)
            if result:
                all_matches.append(result)
            else:
                parse_errors += 1

    # 保存
    db = {
        'built_at': time.strftime('%Y-%m-%d %H:%M:%S'),
        'total_folders': total_folders,
        'parsed': len(all_matches),
        'errors': parse_errors,
        'matches': all_matches,
    }
    with open(OUTPUT_DB, 'w', encoding='utf-8') as f:
        json.dump(db, f, ensure_ascii=False, indent=2)

    return db


def calibrate_from_db(db):
    """从数据库校准联赛参数"""
    matches = db['matches']

    # 按联赛分组
    by_league = {}
    for m in matches:
        lg = m['league']
        if lg not in by_league:
            by_league[lg] = []
        by_league[lg].append(m)

    calibration = {}
    for lg, lg_matches in sorted(by_league.items()):
        n = len(lg_matches)
        if n < 5:
            continue

        # 只看有赛果的
        with_result = [m for m in lg_matches if m['result']]
        if len(with_result) < 5:
            continue

        home_wins = sum(1 for m in with_result if m['result'] == '主胜')
        draws = sum(1 for m in with_result if m['result'] == '平局')
        away_wins = sum(1 for m in with_result if m['result'] == '客胜')

        # L1激活的场次和准确率
        l1_matches = [m for m in with_result
                      if m['l1_c1'] and m['l1_c2'] and m['l1_c3'] and m['l1_c4']]
        l1_correct = sum(1 for m in l1_matches if m['result'] == '主胜')

        # Pinnacle方向准确率
        pin_favor = [m for m in with_result if m['pin_dir'] == '看好']
        pin_correct = sum(1 for m in pin_favor if m['result'] == '主胜')
        pin_against = [m for m in with_result if m['pin_dir'] == '看衰']
        pin_against_correct = sum(1 for m in pin_against if m['result'] == '客胜')

        # 概率分桶校准
        bins = [(0, 0.35), (0.35, 0.45), (0.45, 0.55), (0.55, 0.65), (0.65, 1.0)]
        bin_stats = []
        for lo, hi in bins:
            bucket = [m for m in with_result if lo <= m['p_home'] < hi]
            if len(bucket) < 3:
                continue
            correct = sum(1 for m in bucket
                          if (m['p_home'] > m['p_away'] and m['result'] == '主胜')
                          or (m['p_home'] < m['p_away'] and m['result'] == '客胜'))
            bin_stats.append({
                'range': '%.0f-%.0f%%' % (lo*100, hi*100),
                'n': len(bucket),
                'dir_accuracy': round(correct / len(bucket), 3),
                'home_win': round(sum(1 for m in bucket if m['result']=='主胜')/len(bucket), 3),
                'draw': round(sum(1 for m in bucket if m['result']=='平局')/len(bucket), 3),
                'away_win': round(sum(1 for m in bucket if m['result']=='客胜')/len(bucket), 3),
            })

        calibration[lg] = {
            'total': n,
            'with_result': len(with_result),
            'home_win_rate': round(home_wins / len(with_result), 3),
            'draw_rate': round(draws / len(with_result), 3),
            'away_win_rate': round(away_wins / len(with_result), 3),
            'l1_count': len(l1_matches),
            'l1_accuracy': round(l1_correct / len(l1_matches), 3) if l1_matches else 0,
            'pin_accuracy': round(pin_correct / len(pin_favor), 3) if pin_favor else 0,
            'bins': bin_stats,
        }

    # 保存校准报告
    with open(OUTPUT_CALIBRATION, 'w', encoding='utf-8') as f:
        json.dump(calibration, f, ensure_ascii=False, indent=2)

    return calibration


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')

    print('解析全量数据...')
    db = build_database()
    print('文件夹: %d  解析成功: %d  失败: %d' % (
        db['total_folders'], db['parsed'], db['errors']))

    # 联赛分布
    by_league = {}
    for m in db['matches']:
        lg = m['league']
        by_league[lg] = by_league.get(lg, 0) + 1
    print()
    print('联赛分布:')
    for lg, n in sorted(by_league.items(), key=lambda x: -x[1]):
        with_result = sum(1 for m in db['matches']
                         if m['league'] == lg and m['result'])
        print('  %s: %d场 (有赛果: %d)' % (lg, n, with_result))

    # 校准
    print()
    print('校准联赛参数...')
    cal = calibrate_from_db(db)

    for lg, c in sorted(cal.items()):
        print()
        print('%s (%d场有赛果):' % (lg, c['with_result']))
        print('  主胜%.1f%% 平%.1f%% 客胜%.1f%%' % (
            c['home_win_rate']*100, c['draw_rate']*100, c['away_win_rate']*100))
        if c['l1_count'] >= 3:
            print('  L1激活: %d场, 准确率%.1f%%' % (c['l1_count'], c['l1_accuracy']*100))
        print('  Pinnacle看好准确率: %.1f%%' % (c['pin_accuracy']*100))
        for b in c['bins']:
            print('    %s: %d场 方向准确率%.1f%% 平局%.1f%%' % (
                b['range'], b['n'], b['dir_accuracy']*100, b['draw']*100))

    print()
    print('数据库: %s' % OUTPUT_DB)
    print('校准报告: %s' % OUTPUT_CALIBRATION)
