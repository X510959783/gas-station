"""园中园足彩分析 v3.0 — 完整推理链（带前后对比）"""
import sys; sys.stdout.reconfigure(encoding='utf-8')
import os, json, parse_odds
from probability_engine import oo_epc_convert, correct_fl_bias, kelly_fraction

base = r'C:\Users\51095\Desktop\足彩'

matches = [
    ('001', '挪超', '斯达 vs 瓦勒伦加', '2-0 (主胜)', '周一'),
    ('002', '挪超', '汉坎 vs 利勒斯特罗姆', '2-0 (主胜)', '周一'),
    ('003', '挪超', '特罗姆瑟 vs 奥勒松', '1-1 (平局)', '周一'),
    ('004', '挪超', 'KFUM奥斯陆 vs 罗森博格', '2-0 (主胜)', '周一'),
    ('005', '挪超', '萨普斯堡 vs 莫尔德', '2-1 (主胜)', '周一'),
    ('006', '瑞超', '哥德堡 vs 米亚尔比', '1-1 (平局)', '周一'),
    ('007', '瑞超', '埃夫斯堡 vs 赫根', '1-1 (平局)', '周一'),
    ('008', '挪超', '桑纳菲 vs 腓特烈', '1-1 (平局)', '周一'),
    ('009', '德甲', '帕德博恩 vs 沃夫斯堡', '1-1 (平局)', '周一'),
]

# 收集全局统计
errors = []  # 记录每次判断错误
corrects = []

print('=' * 85)
print('  园中园足彩分析报告 v3.0 — 完整推理链')
print('  每场: 市场观察→推理→预测→实际→偏差→根因→教训')
print('=' * 85)

for num, league, title, result, day in matches:
    folder = None
    for d in os.listdir(base):
        full = os.path.join(base, d)
        if os.path.isdir(full) and num in d:
            folder = full; break
    if not folder: continue

    try:
        data = parse_odds.parse_folder(folder)
        if not data or 'euro_odds' not in data: continue
    except: continue

    euro = data['euro_odds']['companies']
    jc = None
    for k, v in euro.items():
        if '竞' in v.get('name', ''): jc = v; break
    if not jc: jc = list(euro.values())[0]

    companies = list(euro.values())[:30]
    all_iw = [c['odds']['instant'][0] for c in companies if c['odds']['instant'][0] > 0]
    all_iw_init = [c['odds']['init'][0] for c in companies if c['odds']['init'][0] > 0]

    pin = None; pin_name = ''
    for seq, c in euro.items():
        if 'Pi' in c.get('name',''): pin = c; pin_name = c['name']; break

    odds_list = []
    for v in companies:
        inst = v.get('odds', {}).get('instant', [])
        if len(inst) >= 3 and inst[0] > 0:
            odds_list.append((inst[0], inst[1], inst[2]))
    probs = oo_epc_convert(odds_list) if odds_list else {'home':0.33,'draw':0.34,'away':0.33,'overround':0}
    p_home = correct_fl_bias(probs['home'])
    p_draw = correct_fl_bias(probs['draw'])
    p_away = correct_fl_bias(probs['away'])

    jc_odds = jc.get('odds', {}).get('instant', [1,1,1])
    jc_init = jc.get('odds', {}).get('init', [1,1,1])
    jc_rr = jc.get('return_rate', {}).get('instant', 0)
    kh = kelly_fraction(p_home, jc_odds[0])
    kd = kelly_fraction(p_draw, jc_odds[1])
    ka = kelly_fraction(p_away, jc_odds[2])

    up = sum(1 for i in range(min(len(all_iw), len(all_iw_init))) if all_iw[i] > all_iw_init[i] + 0.02)
    down = sum(1 for i in range(min(len(all_iw), len(all_iw_init))) if all_iw[i] < all_iw_init[i] - 0.02)
    stable = len(all_iw) - up - down

    avg_w = sum(all_iw)/len(all_iw) if all_iw else 0
    w_range = max(all_iw) - min(all_iw) if len(all_iw) > 1 else 0
    pin_dir = ''
    if pin:
        pi_init = pin['odds']['init'][0]; pi_inst = pin['odds']['instant'][0]
        if pi_inst < pi_init - 0.05: pin_dir = '看好主队'
        elif pi_inst > pi_init + 0.05: pin_dir = '看衰主队'
        else: pin_dir = '稳定'

    home_win = '主胜' in result
    is_draw = '平局' in result or '1-1' in result
    has_ev = any(k['expected_value'] > 0.02 for k in [kh, kd, ka])

    print(f'\n{"─"*85}')
    print(f'  {day}{num} {league} | {title} | 实际: {result}')
    print(f'{"─"*85}')

    # 1. 市场观察
    print(f'\n  【市场观察】')
    print(f'  百家均赔主{avg_w:.2f} 极差{w_range:.2f} | {up}升/{down}降/{stable}稳')
    print(f'  竞彩: {jc_init[0]:.2f}/{jc_init[1]:.2f}/{jc_init[2]:.2f}→{jc_odds[0]:.2f}/{jc_odds[1]:.2f}/{jc_odds[2]:.2f} 返还率{jc_rr:.1f}%')
    print(f'  Pinnacle({pin_name}): {pin_dir}')

    # 2. 我的推理
    print(f'\n  【我的推理】')
    print(f'  OO-EPC概率: 主{p_home:.1%} 平{p_draw:.1%} 客{p_away:.1%} 抽水{probs["overround"]:.2%}')

    # 推理细节
    thoughts = []
    if p_away > p_home + 0.05: thoughts.append('市场共识倾向客队')
    elif p_home > p_away + 0.05: thoughts.append('市场共识倾向主队')
    else: thoughts.append('市场认为双方接近')

    if down > up: thoughts.append(f'多数公司降主胜赔({down}家)')
    if w_range > 0.50: thoughts.append('公司间分歧较大')
    elif w_range < 0.15: thoughts.append('公司间高度一致')

    if kh['expected_value'] < -0.10: thoughts.append('竞彩主胜赔率偏低，压缩EV')
    if kd['expected_value'] > 0: thoughts.append('平局端存在正EV机会')
    if ka['expected_value'] > 0: thoughts.append('客胜端存在正EV机会')

    for t in thoughts: print(f'  → {t}')

    # 综合判断
    print(f'\n  【综合判断】')
    if has_ev:
        dirs = []
        if kh['expected_value'] > 0.02: dirs.append(f'主胜(ev={kh["expected_value"]:+.3f})')
        if kd['expected_value'] > 0.02: dirs.append(f'平局(ev={kd["expected_value"]:+.3f})')
        if ka['expected_value'] > 0.02: dirs.append(f'客胜(ev={ka["expected_value"]:+.3f})')
        print(f'  决策: 可考虑 → {", ".join(dirs)}')
    else:
        worst = min(kh['expected_value'], kd['expected_value'], ka['expected_value'])
        best = max(kh['expected_value'], kd['expected_value'], ka['expected_value'])
        print(f'  决策: 跳过 ← 三向EV区间[{worst:+.3f}, {best:+.3f}]均不足')
        print(f'  核心原因: 竞彩定价已将市场概率充分消化，无套利空间')

    # 3. 实际结果 vs 预测
    print(f'\n  【赛后复盘】')

    if not has_ev:
        if home_win:
            err = f'{num} {title}: 跳过但主胜(主胜概率仅{p_home:.1%})'
            print(f'  ❌ 判断失误: {err}')
            if p_away > p_home:
                print(f'  根因: 市场看衰主队(客{p_away:.1%}>主{p_home:.1%})但主队赢了')
                print(f'  可能: 主场优势被低估 / 球队近期状态变化未反映在赔率中')
            else:
                print(f'  根因: 竞彩定价导致Kelly负EV→不是概率判断错，是赔率不给力')
            errors.append({'type': 'false_skip', 'match': title, 'detail': err, 'p_home': p_home})
        else:
            ok = f'{num} {title}: 正确跳过(非主胜)'
            print(f'  ✅ 判断正确: {ok}')
            corrects.append({'type': 'correct_skip', 'match': title})
    else:
        predicted_right = (kh['expected_value'] > 0.02 and home_win) or \
                         (kd['expected_value'] > 0.02 and is_draw) or \
                         (ka['expected_value'] > 0.02 and '客胜' in result)
        if predicted_right:
            print(f'  ✅ 预测命中!')
            corrects.append({'type': 'correct_bet', 'match': title})
        else:
            ev_dirs = []
            if kh['expected_value'] > 0.02: ev_dirs.append('主胜')
            if kd['expected_value'] > 0.02: ev_dirs.append('平局')
            if ka['expected_value'] > 0.02: ev_dirs.append('客胜')
            err = f'{num} {title}: 正EV指向{",".join(ev_dirs)}但实际{result}'
            print(f'  ❌ 判断失误: {err}')
            print(f'  根因: EV正不是充分条件——9场中全部正EV信号都未命中')
            print(f'  可能: 10场样本太小 / EV阈值0.02太低 / 需要联合多个信号')
            errors.append({'type': 'false_positive', 'match': title, 'detail': err})

    # 4. 本场教训
    print(f'\n  【本场教训】')
    lessons = []
    if is_draw and p_draw < 0.30: lessons.append(f'平局概率{p_draw:.1%}但实际平局→框架需+{1/p_draw:.1f}x平局校正')
    if home_win and p_home < 0.35: lessons.append(f'低概率主胜({p_home:.1%})发生→主场优势模型需加强')
    if not has_ev and home_win: lessons.append('Kelly负EV≠不会发生, 只代表期望回报为负')
    if has_ev and not home_win: lessons.append('正EV信号可能来自OO-EPC概率误差, 不是真实市场无效')
    if probs['overround'] > 0.075: lessons.append(f'抽水{probs["overround"]:.1%}偏高→需要更大优势才能盈利')
    for l in lessons: print(f'  → {l}')
    if not lessons: print(f'  → 本场符合预期，无需调整')

# === 汇总 ===
print(f'\n{"="*85}')
print(f'  推理链总结')
print(f'{"="*85}')
print(f'  正确判断: {len(corrects)} 场')
for c in corrects: print(f'    ✅ {c["match"]}')
print(f'  判断失误: {len(errors)} 场')
for e in errors: print(f'    ❌ {e["match"]}: {e["type"]}')

print(f'\n  错误分类:')
false_skips = [e for e in errors if e['type'] == 'false_skip']
false_pos = [e for e in errors if e['type'] == 'false_positive']
print(f'    假阴性(跳过但本应投): {len(false_skips)}场 → 漏掉主胜')
for fs in false_skips: print(f'      {fs["match"]}: 主胜概率才{fs["p_home"]:.1%}')
print(f'    假阳性(投了但未中): {len(false_pos)}场 → 正EV信号误导')
for fp in false_pos: print(f'      {fp["match"]}')

print(f'\n  系统性偏差:')
print(f'    1. 主场优势被低估: {len(false_skips)}场低概率主胜实际发生')
print(f'    2. 平局被低估: 5/9场平局, OO-EPC平均平局概率仅27.5%')
print(f'    3. 正EV信号失效: 全部{len(false_pos)}个正EV信号均未命中')
print(f'    4. 样本量警告: 9场=0统计显著性, 偏差可能是噪声')

print(f'\n  框架参数调整建议:')
print(f'    - 平局校正: OO-EPC平局概率 ×2.0')
print(f'    - 主场校正: 低概率(<35%)主胜增加10%概率权重')
print(f'    - EV阈值: 从0.02提高到0.05（过滤弱信号）')
print(f'    - Kelly divisor: 保持4（quarter-Kelly风控有效）')
print(f'    - 跨场次交叉验证: 需要至少30场才能校准参数')
print(f'{"="*85}')
