# -*- coding: utf-8 -*-
"""v5预测引擎 - Elo原生 + 极限碰撞
一条思路: Elo方向决定win/loss, 瑞超倾向平局, 伤病检测平局
目标: 全量90%+
"""
import sys, os, re, json, math

SCRIPT_DIR = os.path.dirname(__file__)
sys.path.insert(0, SCRIPT_DIR)
from elo_engine import get_elo_signal, load_elo_db


def predict(league, home_team, away_team, extra_signals=None):
    """统一预测函数 - 一条思路
    返回: {decision, badge, confidence, direction, elo_info}
    """
    elo = get_elo_signal(league, home_team, away_team)
    extra = extra_signals or {}

    if not elo:
        # 无Elo: Pinnacle > 市场方向 > 默认主不败
        ph = extra.get('p_home', 0.5)
        pa = extra.get('p_away', 0.5)
        pin = extra.get('pin_dir', 'N')
        w_range = extra.get('w_range', 0.5)
        up = extra.get('up', 0)
        down = extra.get('down', 0)

        # Pinnacle明确方向
        if pin == '看好':
            direction = '主不败'
            decision = '单选主胜'
        elif pin == '看衰':
            direction = '客不败'
            decision = '单选客胜'
        # 市场方向 + 多数公司同向
        elif down > up and ph > 0.40:
            direction = '主不败'
            decision = '单选主胜'
        elif up > down and pa > 0.40:
            direction = '客不败'
            decision = '单选客胜'
        # 市场概率方向
        elif ph > pa:
            direction = '主不败'
            decision = '单选主胜'
        else:
            direction = '客不败'
            decision = '单选客胜'

        return {
            'decision': decision, 'badge': 'Low', 'confidence': 15,
            'direction': direction, 'rule': 'no_elo_fallback',
        }

    diff = elo['elo_diff']
    abs_diff = elo['elo_abs_diff']
    elo_dir = elo['elo_direction']
    direction = '主不败' if elo_dir == '主胜' else '客不败'

    # === 碰撞#40终极规则 ===

    # 规则1: 伤缺 >= 3 → 单选平局 (最强独立信号)
    injuries = extra.get('injuries', 0)
    if injuries >= 3:
        return {
            'decision': '单选平局', 'badge': 'Stable', 'confidence': 80,
            'direction': direction, 'rule': 'injuries',
        }

    # 规则2: 瑞超 + Elo差距小 → 单选平局
    if league == '瑞超' and abs_diff < 30:
        return {
            'decision': '单选平局', 'badge': 'Correct', 'confidence': 55,
            'direction': direction, 'rule': 'sweden_draw',
        }

    # 规则3: Elo差距极大 (>80) → 单选win, 最高置信
    if abs_diff >= 80:
        return {
            'decision': '单选主胜' if elo_dir == '主胜' else '单选客胜',
            'badge': 'Stable', 'confidence': 85,
            'direction': direction, 'rule': 'elo_very_high',
        }

    # 规则4: Elo差距大 (>40) → 单选win, 高置信
    if abs_diff >= 40:
        return {
            'decision': '单选主胜' if elo_dir == '主胜' else '单选客胜',
            'badge': 'Stable', 'confidence': 75,
            'direction': direction, 'rule': 'elo_high',
        }

    # 规则5: Elo差距中等 (>20) → 单选win, 中置信
    if abs_diff >= 20:
        return {
            'decision': '单选主胜' if elo_dir == '主胜' else '单选客胜',
            'badge': 'Correct', 'confidence': 55,
            'direction': direction, 'rule': 'elo_medium',
        }

    # 规则6: Elo接近 (<=20) → 倾向平局, 低置信
    return {
        'decision': '单选平局',
        'badge': 'Risk', 'confidence': 35,
        'direction': direction, 'rule': 'elo_close_draw',
    }


def evaluate(all_matches):
    """评估预测准确率"""
    results = {'correct': 0, 'wrong': 0}
    by_rule = {}
    by_badge = {'Stable': [0,0], 'Correct': [0,0], 'Risk': [0,0], 'Low': [0,0]}
    by_league = {}

    for m in all_matches:
        lg = m['lg']
        home = m['home']
        away = m['away']
        actual = m['actual']

        pred = predict(lg, home, away, {
            'p_home': m.get('ph', 0.5),
            'p_away': m.get('pa', 0.5),
            'injuries': 0,
        })

        decision = pred['decision']
        ok = ('主胜' in decision and actual == 'H') or \
             ('平局' in decision and actual == 'D') or \
             ('客胜' in decision and actual == 'A')

        if ok: results['correct'] += 1
        else: results['wrong'] += 1

        rule = pred.get('rule', '?')
        badge = pred.get('badge', '?')
        if rule not in by_rule: by_rule[rule] = [0,0]
        by_rule[rule][1] += 1
        if ok: by_rule[rule][0] += 1

        if badge in by_badge:
            by_badge[badge][1] += 1
            if ok: by_badge[badge][0] += 1

        if lg not in by_league: by_league[lg] = [0,0]
        by_league[lg][1] += 1
        if ok: by_league[lg][0] += 1

    return results, by_rule, by_badge, by_league


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    import parse_odds
    from probability_engine import oo_epc_convert, correct_fl_bias

    # 收集比赛
    base = r'D:/足彩'
    all_matches = []
    for date_dir in sorted(os.listdir(base)):
        date_path = os.path.join(base, date_dir)
        if not os.path.isdir(date_path): continue
        for folder in sorted(os.listdir(date_path)):
            folder_path = os.path.join(date_path, folder)
            if not os.path.isdir(folder_path): continue
            mf = os.path.join(folder_path, 'match_info.json')
            if not os.path.exists(mf): continue
            with open(mf, 'r', encoding='utf-8') as f:
                meta = json.load(f)
            score = meta.get('score', '')
            if not score: continue
            parts = score.split('-')
            if len(parts) != 2: continue
            try: hg, ag = int(parts[0]), int(parts[1])
            except: continue
            actual = 'H' if hg > ag else ('D' if hg == ag else 'A')
            lg = folder.split('_')[0] if '_' in folder else 'O'

            home = away = ''
            for fname in sorted(os.listdir(folder_path)):
                if fname.endswith('.html'):
                    with open(os.path.join(folder_path, fname), 'r',
                              encoding='utf-8', errors='replace') as fh:
                        html = fh.read(1000)
                    title = re.search(r'<title>(.*?)</title>', html)
                    if title:
                        vs = re.search(r'(.+?)VS(.+?)[(（]', title.group(1))
                        if vs:
                            home = vs.group(1).strip()
                            away = vs.group(2).strip()
                    break
            if not home: continue

            try:
                data = parse_odds.parse_folder(folder_path)
                companies = list(data['euro_odds']['companies'].values())
            except: continue
            all_iw = [c['odds']['instant'][0] for c in companies[:30]
                      if c['odds']['instant'][0] > 0]
            odds_list = [(c['odds']['instant'][0], c['odds']['instant'][1],
                         c['odds']['instant'][2])
                         for c in companies[:30]
                         if len(c.get('odds', {}).get('instant', [])) >= 3
                         and c['odds']['instant'][0] > 0]
            if len(odds_list) < 5: continue
            probs = oo_epc_convert(odds_list)
            ph = correct_fl_bias(probs['home'])
            pa = correct_fl_bias(probs['away'])
            all_matches.append({
                'lg': lg, 'home': home, 'away': away,
                'actual': actual, 'ph': ph, 'pa': pa,
            })

    print('比赛: %d' % len(all_matches))

    # 评估
    r, by_rule, by_badge, by_league = evaluate(all_matches)
    total = r['correct'] + r['wrong']
    acc = 100*r['correct']//total

    print()
    print('=' * 55)
    print('  v5 Elo原生引擎: %d场 | %d/%d = %d%%' % (
        total, r['correct'], total, acc))
    print('=' * 55)

    print('\n按规则:')
    for rule, (c, t) in sorted(by_rule.items(), key=lambda x: -x[1]):
        print('  %s: %d/%d = %d%%' % (rule, c, t, 100*c//t if t else 0))

    print('\n按置信度:')
    for b in ['Stable', 'Correct', 'Risk', 'Low']:
        c, t = by_badge[b]
        if t > 0:
            print('  %s: %d/%d = %d%% (%d场)' % (b, c, t, 100*c//t, t))

    print('\n按联赛 (>=5场的):')
    for lg, (c, t) in sorted(by_league.items(), key=lambda x: -x[1]):
        if t >= 5:
            print('  %s: %d/%d = %d%%' % (lg, c, t, 100*c//t))
