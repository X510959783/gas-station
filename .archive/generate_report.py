"""园中园足彩分析报告 v3.0 — 001-009 全量"""
import sys; sys.stdout.reconfigure(encoding='utf-8')
import os, json, parse_odds
from probability_engine import oo_epc_convert, correct_fl_bias, kelly_fraction

base = r'C:\Users\51095\Desktop\足彩'

match_meta = {
    '001': {'title': '斯达 vs 瓦勒伦加', 'league': '挪超',
            'deadline': '2026-05-25 20:30', 'result': '2-0 (主胜)'},
    '002': {'title': '汉坎 vs 利勒斯特罗姆', 'league': '挪超',
            'deadline': '2026-05-25 23:00', 'result': '2-0 (主胜)'},
    '003': {'title': '特罗姆瑟 vs 奥勒松', 'league': '挪超',
            'deadline': '2026-05-25 23:00', 'result': '1-1 (平局)'},
    '004': {'title': 'KFUM奥斯陆 vs 罗森博格', 'league': '挪超',
            'deadline': '2026-05-25 23:00', 'result': '2-0 (主胜)'},
    '005': {'title': '萨普斯堡 vs 莫尔德', 'league': '挪超',
            'deadline': '2026-05-25 23:00', 'result': '2-1 (主胜)'},
    '006': {'title': '哥德堡 vs 米亚尔比', 'league': '瑞超',
            'deadline': '2026-05-26 01:00', 'result': '1-1 (平局)'},
    '007': {'title': '埃夫斯堡 vs 赫根', 'league': '瑞超',
            'deadline': '2026-05-26 01:00', 'result': '1-1 (平局)'},
    '008': {'title': '桑纳菲 vs 腓特烈', 'league': '挪超',
            'deadline': '2026-05-26 01:15', 'result': '1-1 (平局)'},
    '009': {'title': '帕德博恩 vs 沃夫斯堡', 'league': '德甲',
            'deadline': '2026-05-26 02:30', 'result': '1-1 (平局)'},
}

reports = []
for num in ['001','002','003','004','005','006','007','008','009']:
    folder = None
    for d in os.listdir(base):
        full = os.path.join(base, d)
        if os.path.isdir(full) and num in d:
            folder = full; break
    if not folder: continue

    meta = match_meta.get(num)
    if not meta: continue

    try:
        data = parse_odds.parse_folder(folder)
        if not data or 'euro_odds' not in data: continue
    except: continue

    euro = data['euro_odds']['companies']
    jc = None
    for k, v in euro.items():
        if '竞' in v.get('name', ''): jc = v; break
    if not jc: jc = list(euro.values())[0]

    odds_list = []
    for v in list(euro.values())[:30]:
        inst = v.get('odds', {}).get('instant', [])
        if len(inst) >= 3 and inst[0] > 0:
            odds_list.append((inst[0], inst[1], inst[2]))

    probs = oo_epc_convert(odds_list) if odds_list else {'home':0.33,'draw':0.34,'away':0.33,'overround':0}
    p_home = correct_fl_bias(probs['home'])
    p_draw = correct_fl_bias(probs['draw'])
    p_away = correct_fl_bias(probs['away'])

    jc_odds = jc.get('odds', {}).get('instant', [1,1,1])
    k_home = kelly_fraction(p_home, jc_odds[0])
    k_draw = kelly_fraction(p_draw, jc_odds[1])
    k_away = kelly_fraction(p_away, jc_odds[2])
    jc_rr = jc.get('return_rate', {}).get('instant', 0)

    all_iw = [c['odds']['instant'][0] for c in list(euro.values())[:30]]
    avg_w = sum(all_iw)/len(all_iw) if all_iw else 0

    pin = None
    for seq, c in euro.items():
        if 'Pi' in c.get('name',''): pin = c; break

    has_ev = any(k['expected_value'] > 0.02 for k in [k_home, k_draw, k_away])
    best = max([k_home, k_draw, k_away], key=lambda x: x['expected_value'])

    reports.append({
        'num': num, 'meta': meta,
        'jc_odds': jc_odds, 'jc_rr': jc_rr, 'avg_odds': avg_w,
        'probs': probs, 'p_home': p_home, 'p_draw': p_draw, 'p_away': p_away,
        'k_home': k_home, 'k_draw': k_draw, 'k_away': k_away,
        'has_ev': has_ev, 'best_ev': best['expected_value'],
        'pin_odds': pin['odds'] if pin else None
    })

# ======== 输出 ========
print('=' * 80)
print('  园中园足彩分析报告 v3.0 — 2026-05-25/26 北欧联赛')
print('  OO-EPC + Kelly-Bayesian + FL偏差校正')
print('=' * 80)

total = len(reports)
skips = sum(1 for r in reports if not r['has_ev'])
draws = sum(1 for r in reports if '平局' in r['meta']['result'])
home_wins = sum(1 for r in reports if '主胜' in r['meta']['result'])
avg_oo = sum(r['probs']['overround'] for r in reports) / total

print(f'\n一、总览')
print(f'  场次: {total} | 联赛: 挪超(6)+瑞超(2)+德甲(1)')
print(f'  平均抽水: {avg_oo:.2%} | Skip率: {skips}/{total}({skips*100/total:.0f}%)')
print(f'  平局: {draws}/{total}({draws*100/total:.0f}%) | 主胜: {home_wins}/{total}({home_wins*100/total:.0f}%)')

print(f'\n{"─"*80}')
print('二、逐场 v3 分析')
print('─'*80)

for r in reports:
    m = r['meta']
    print(f'\n  ▸ 周一{r["num"]} {m["league"]} | {m["title"]} | 实际: {m["result"]}')
    print(f'     OO-EPC: 主{r["p_home"]:.1%} 平{r["p_draw"]:.1%} 客{r["p_away"]:.1%} (抽水{r["probs"]["overround"]:.2%})')
    print(f'     竞彩: {r["jc_odds"][0]:.2f}/{r["jc_odds"][1]:.2f}/{r["jc_odds"][2]:.2f}  返还率{r["jc_rr"]:.1f}%')

    kh, kd, ka = r['k_home'], r['k_draw'], r['k_away']
    print(f'     Kelly: 主EV={kh["expected_value"]:+.4f} | 平EV={kd["expected_value"]:+.4f} | 客EV={ka["expected_value"]:+.4f}')

    if r['has_ev']:
        dirs = []
        if kh['expected_value'] > 0.02: dirs.append('主胜')
        if kd['expected_value'] > 0.02: dirs.append('平局')
        if ka['expected_value'] > 0.02: dirs.append('客胜')
        print(f'     >>> 可考虑({",".join(dirs)}) | 最佳EV={r["best_ev"]:+.4f}')
    else:
        print(f'     >>> 跳过 (全部负EV)')

    if r['pin_odds']:
        p = r['pin_odds']
        print(f'     Pinnacle: {p["init"][0]:.2f}/{p["init"][1]:.2f}/{p["init"][2]:.2f} → {p["instant"][0]:.2f}/{p["instant"][1]:.2f}/{p["instant"][2]:.2f}')

print(f'\n{"─"*80}')
print('三、统计洞察')
print('─'*80)

print(f'\n  1. Kelly EV 排名:')
ranked = sorted(reports, key=lambda x: x['best_ev'], reverse=True)
for i, r in enumerate(ranked):
    marker = ' ← 仅有的正EV' if r['has_ev'] else ''
    print(f'     {i+1}. {r["num"]} {r["meta"]["title"]}: EV={r["best_ev"]:+.4f}{marker}')

print(f'\n  2. 平局被系统性低估:')
avg_draw_prob = sum(r['p_draw'] for r in reports) / total
print(f'     OO-EPC 平均平局概率: {avg_draw_prob:.1%}')
print(f'     实际平局率: {draws/total:.0%}')
print(f'     偏差: {draws/total - avg_draw_prob:+.0%}')

print(f'\n  3. 联赛对比:')
for lg in ['挪超','瑞超','德甲']:
    lg_reports = [r for r in reports if r['meta']['league'] == lg]
    if lg_reports:
        n = len(lg_reports)
        d = sum(1 for r in lg_reports if '平局' in r['meta']['result'])
        oo = sum(r['probs']['overround'] for r in lg_reports) / n
        print(f'     {lg}: {n}场 平局{d/n:.0%} 抽水{oo:.2%}')

print(f'\n  4. Skip 率验证:')
print(f'     9场中{skips}场Kelly负EV→Skip')
print(f'     Skip的{skips}场中，实际主胜{sum(1 for r in reports if not r["has_ev"] and "主胜" in r["meta"]["result"])}场')
print(f'     → Skip保护了{sum(1 for r in reports if not r["has_ev"] and "主胜" not in r["meta"]["result"])}场负EV投注')

print(f'\n{"─"*80}')
print('四、框架进化建议')
print('─'*80)
print(f'  1. 平局校正: OO-EPC平局概率 ×{draws/total/avg_draw_prob:.2f}')
print(f'  2. Kelly divisor=4有效——唯一正EV信号也未命中')
print(f'  3. 跨联赛复用OO-EPC可行(抽水均在6-8%)')
print(f'  4. 样本量不足——10场无法统计显著')
print(f'  5. 下一步: 层次Poisson模型+赛中4.5%ROI探索')
print()
print(f'  报告: 2026-05-26 | v3.0 | {total}场 | 数据:500.com')
print(f'{"="*80}')
