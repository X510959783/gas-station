# -*- coding: utf-8 -*-
"""全量回测: 框架 vs 443场真实赛果
终极碰撞: 找出失败模式, 迭代改进直到90%+
"""
import sys, os, json, re
sys.path.insert(0, os.path.dirname(__file__))
from framework_v4 import analyze_match

BASE_DIR = r'D:\足彩'
DB_FILE = os.path.join(os.path.dirname(__file__), 'match_db_full.json')


def run_full_backtest():
    """对所有有赛果的比赛运行框架并比对"""
    with open(DB_FILE, 'r', encoding='utf-8') as f:
        db = json.load(f)

    results = []
    for m in db['matches']:
        if not m.get('result'):
            continue

        # 找对应的文件夹
        date_dir = m['date']
        lg = m['league']
        folder_name = m.get('name', '')
        mid = None

        # 从match_db提取的信息不够——需要原始文件夹路径
        # 遍历找匹配的比赛ID
        folder_path = None
        for root, dirs, files in os.walk(os.path.join(BASE_DIR, date_dir)):
            for d in dirs:
                full = os.path.join(root, d)
                # 检查match_info.json中的ID
                mf = os.path.join(full, 'match_info.json')
                if os.path.exists(mf):
                    with open(mf, 'r', encoding='utf-8') as fh:
                        meta = json.load(fh)
                    if meta.get('id') in folder_name or folder_name in d:
                        folder_path = full
                        mid = meta.get('id', '')
                        break
            if folder_path:
                break

        if not folder_path:
            # 从date_dir和league_xxx格式匹配
            for d in os.listdir(os.path.join(BASE_DIR, date_dir)):
                dp = os.path.join(BASE_DIR, date_dir, d)
                if not os.path.isdir(dp):
                    continue
                # 匹配
                if lg in d or folder_name[:20] in d or d.endswith('_' + folder_name.split('_')[-1]):
                    folder_path = dp
                    break

        if not folder_path:
            continue

        # 运行框架
        try:
            r = analyze_match(folder_path, lg if lg != '其他' else '挪超')
        except Exception:
            continue

        decision = r['decision']
        actual = m['result']
        ok = False
        if '单选主胜' in decision and actual == '主胜': ok = True
        elif '单选平局' in decision and actual == '平局': ok = True
        elif '单选客胜' in decision and actual == '客胜': ok = True

        results.append({
            'date': date_dir,
            'league': lg,
            'name': folder_name[:40],
            'decision': decision,
            'actual': actual,
            'correct': ok,
            'p_home': m.get('p_home', 0),
            'w_range': m.get('w_range', 0),
            'prob_gap': m.get('prob_gap', 0),
            'pin_dir': m.get('pin_dir', ''),
            'badge': r.get('badge', '?'),
            'confidence': r.get('confidence', 0),
            'layers': '->'.join(r.get('layers', [])),
            'thought': r.get('thought_chain', [''])[-1][:100] if r.get('thought_chain') else '',
        })

    return results


def analyze_failures(results):
    """分析失败模式"""
    correct = sum(1 for r in results if r['correct'])
    wrong = sum(1 for r in results if not r['correct'])
    total = len(results)
    acc = correct / max(1, total) * 100

    print('=' * 60)
    print('  全量回测: %d场, 正确%d, 错误%d, 准确率%.1f%%' % (
        total, correct, wrong, acc))
    print('=' * 60)

    # 按联赛
    by_league = {}
    for r in results:
        lg = r['league']
        if lg not in by_league:
            by_league[lg] = {'correct': 0, 'total': 0}
        by_league[lg]['total'] += 1
        if r['correct']:
            by_league[lg]['correct'] += 1

    print('\n按联赛:')
    for lg in sorted(by_league, key=lambda x: -by_league[x]['total']):
        s = by_league[lg]
        if s['total'] < 5: continue
        print('  %s: %d/%d = %.1f%%' % (lg, s['correct'], s['total'],
                                         100*s['correct']/s['total']))

    # 按概率区间
    bins = [(0, 0.35), (0.35, 0.45), (0.45, 0.55), (0.55, 0.65), (0.65, 1.0)]
    print('\n按p_home区间:')
    for lo, hi in bins:
        bucket = [r for r in results if lo <= r['p_home'] < hi]
        if len(bucket) < 5: continue
        c = sum(1 for r in bucket if r['correct'])
        print('  %.0f-%.0f%%: %d/%d = %.1f%%' % (
            lo*100, hi*100, c, len(bucket), 100*c/len(bucket)))

    # 按badge
    print('\n按置信度:')
    for badge in ['Stable', 'Correct', 'Risk', 'Low']:
        bucket = [r for r in results if r['badge'] == badge]
        if not bucket: continue
        c = sum(1 for r in bucket if r['correct'])
        print('  %s: %d/%d = %.1f%%' % (badge, c, len(bucket),
                                         100*c/len(bucket)))

    # 失败案例
    failures = [r for r in results if not r['correct']]
    print('\n失败案例 (前15):')
    for r in failures[:15]:
        print('  [%s] %s %s -> %s (实际:%s) p_home=%.1f%% badge=%s' % (
            r['league'], r['date'], r['decision'], r['thought'][:50],
            r['actual'], r['p_home']*100, r['badge']))

    return results


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    results = run_full_backtest()
    if results:
        analyze_failures(results)
        # 保存回测结果
        with open('backtest_results.json', 'w', encoding='utf-8') as f:
            json.dump({
                'total': len(results),
                'correct': sum(1 for r in results if r['correct']),
                'accuracy': round(sum(1 for r in results if r['correct'])/len(results)*100, 1),
                'results': results
            }, f, ensure_ascii=False, indent=2)
        print('\n回测结果已保存: backtest_results.json')
    else:
        print('回测失败: 无法匹配比赛文件夹')
