"""园中园足彩9场深度分析——三遍交叉验证+思维博弈"""
import sys; sys.stdout.reconfigure(encoding='utf-8')
import os, parse_odds
from probability_engine import oo_epc_convert, correct_fl_bias, kelly_fraction

base = r'C:\Users\51095\Desktop\足彩'

league_profiles = {
    '挪超': {'home_boost': 0.18, 'draw_rate': 0.23, 'note': '进球偏多主场+15-25%胜率，庄家常高估排名低估主客场分化'},
    '瑞超': {'home_boost': 0.12, 'draw_rate': 0.42, 'note': '防守优先平局偏多(37-50%)，赫根8轮不败埃尔夫斯堡慢热'},
    '德甲': {'home_boost': 0.10, 'draw_rate': 0.28, 'note': '升降级附加赛市场效率最高抽水最低'},
}

matches = [
    ('001','挪超','斯达 vs 瓦勒伦加','2-0 (主胜)'),
    ('002','挪超','汉坎 vs 利勒斯特罗姆','2-0 (主胜)'),
    ('003','挪超','特罗姆瑟 vs 奥勒松','1-1 (平局)'),
    ('004','挪超','KFUM奥斯陆 vs 罗森博格','2-0 (主胜)'),
    ('005','挪超','萨普斯堡 vs 莫尔德','2-1 (主胜)'),
    ('006','瑞超','哥德堡 vs 米亚尔比','1-1 (平局)'),
    ('007','瑞超','埃夫斯堡 vs 赫根','1-1 (平局)'),
    ('008','挪超','桑纳菲 vs 腓特烈','1-1 (平局)'),
    ('009','德甲','帕德博恩 vs 沃夫斯堡','1-1 (平局)'),
]

for num, league, title, result in matches:
    folder = None
    for d in os.listdir(base):
        full = os.path.join(base, d)
        if os.path.isdir(full) and num in d: folder = full; break
    if not folder: continue

    try:
        data = parse_odds.parse_folder(folder)
        if not data or 'euro_odds' not in data: continue
    except: continue

    euro = data['euro_odds']['companies']
    jc = None; jc_name = ''
    for k, v in euro.items():
        if '竞' in v.get('name', ''): jc = v; jc_name = v['name']; break
    if not jc: jc = list(euro.values())[0]

    companies = list(euro.values())[:30]
    all_iw = [c['odds']['instant'][0] for c in companies if c['odds']['instant'][0] > 0]
    all_iw_init = [c['odds']['init'][0] for c in companies if c['odds']['init'][0] > 0]

    pin = None; pin_name = ''
    for seq, c in euro.items():
        if 'Pi' in c.get('name',''): pin = c; pin_name = c['name']; break

    odds_list = [(c['odds']['instant'][0], c['odds']['instant'][1], c['odds']['instant'][2])
                 for c in companies if len(c.get('odds',{}).get('instant',[])) >= 3 and c['odds']['instant'][0] > 0]
    probs = oo_epc_convert(odds_list) if odds_list else {'home':0.33,'draw':0.34,'away':0.33,'overround':0}

    lp = league_profiles.get(league, {'home_boost': 0.10, 'draw_rate': 0.25, 'note': ''})
    p_home_raw = correct_fl_bias(probs['home'])
    p_draw_raw = correct_fl_bias(probs['draw'])
    p_away_raw = correct_fl_bias(probs['away'])

    # 联赛校正
    p_home_adj = min(p_home_raw * (1 + lp['home_boost']), 0.75)
    p_away_adj = p_away_raw * (1 - lp['home_boost'] * 0.5)
    total = p_home_adj + p_draw_raw + p_away_adj
    p_home_adj /= total; p_draw_adj = p_draw_raw / total; p_away_adj /= total

    jc_odds = jc.get('odds', {}).get('instant', [1,1,1])
    jc_init = jc.get('odds', {}).get('init', [1,1,1])
    jc_rr = jc.get('return_rate', {}).get('instant', 0)

    k_home_raw = kelly_fraction(p_home_raw, jc_odds[0])
    k_home_adj = kelly_fraction(p_home_adj, jc_odds[0])
    k_draw_raw = kelly_fraction(p_draw_raw, jc_odds[1])

    up = sum(1 for i in range(min(len(all_iw), len(all_iw_init))) if all_iw[i] > all_iw_init[i] + 0.02)
    down = sum(1 for i in range(min(len(all_iw), len(all_iw_init))) if all_iw[i] < all_iw_init[i] - 0.02)
    stable = len(all_iw) - up - down
    avg_w = sum(all_iw)/len(all_iw) if all_iw else 0
    w_range = max(all_iw) - min(all_iw) if len(all_iw) > 1 else 0

    pin_dir = ''; pin_move = ''
    if pin:
        pi_i, pi_f = pin['odds']['init'][0], pin['odds']['instant'][0]
        pin_move = f'{pi_i:.2f}->{pi_f:.2f}'
        if pi_f < pi_i - 0.05: pin_dir = '看好主队'
        elif pi_f > pi_i + 0.05: pin_dir = '看衰主队'
        else: pin_dir = '稳定'

    home_win = '主胜' in result
    is_draw = '平局' in result or '1-1' in result

    print(f'\n{"="*75}')
    print(f'  周一{num} {league} | {title} | 实际: {result}')
    print(f'{"="*75}')

    # 第一遍
    print(f'\n  ── 第一遍: 市场原始信号 ──')
    print(f'  百家均赔主{avg_w:.2f} 极差{w_range:.2f} | {up}升/{down}降/{stable}稳')
    print(f'  竞彩({jc_name}): {jc_init[0]:.2f}/{jc_init[1]:.2f}/{jc_init[2]:.2f} -> {jc_odds[0]:.2f}/{jc_odds[1]:.2f}/{jc_odds[2]:.2f} 返还率{jc_rr:.1f}%')
    if pin: print(f'  Pinnacle({pin_name}): {pin_move} {pin_dir}')
    print(f'  OO-EPC概率: 主{p_home_raw:.1%} 平{p_draw_raw:.1%} 客{p_away_raw:.1%} 抽水{probs["overround"]:.2%}')
    if p_away_raw > p_home_raw + 0.05:
        print(f'  市场解读: 共识倾向客队')
    elif p_home_raw > p_away_raw + 0.05:
        print(f'  市场解读: 共识倾向主队')
    else:
        print(f'  市场解读: 势均力敌(差{abs(p_home_raw-p_away_raw):.1%})')
    if down > up:
        print(f'  赔率趋势: {down}家降主胜赔->市场在向主队倾斜')
    elif up > down:
        print(f'  赔率趋势: {up}家升主胜赔->市场在向客队倾斜')

    # 第二遍
    print(f'\n  ── 第二遍: 联赛特性校正 ──')
    print(f'  {league}特征: {lp["note"]}')
    print(f'  校正前: 主{p_home_raw:.1%} 平{p_draw_raw:.1%} 客{p_away_raw:.1%}')
    print(f'  校正后: 主{p_home_adj:.1%} 平{p_draw_adj:.1%} 客{p_away_adj:.1%}')
    print(f'  Kelly(校正前): 主胜EV={k_home_raw["expected_value"]:+.4f} f*={k_home_raw["full_kelly"]:.4f}')
    print(f'  Kelly(校正后): 主胜EV={k_home_adj["expected_value"]:+.4f} f*={k_home_adj["full_kelly"]:.4f}')
    print(f'  联赛平局率参考: {lp["draw_rate"]:.0%} (vs OO-EPC预测{p_draw_raw:.1%})')

    # 第三遍: 多信号交叉验证
    print(f'\n  ── 第三遍: 多信号交叉验证 ──')
    signals = []
    # 信号1: OO-EPC原始
    if k_home_raw['expected_value'] > 0.02: signals.append(('OO-EPC', '投主胜', 1))
    else: signals.append(('OO-EPC', '跳过', -1))
    # 信号2: 联赛校正
    if k_home_adj['expected_value'] > 0.02: signals.append(('联赛校正', '投主胜', 1))
    else: signals.append(('联赛校正', '跳过', -1))
    # 信号3: 赔率趋势
    if down > up + 5: signals.append(('赔率趋势', '看好主队', 1))
    elif up > down + 5: signals.append(('赔率趋势', '看衰主队', -1))
    else: signals.append(('赔率趋势', '方向不明', 0))
    # 信号4: Pinnacle
    if pin and '看好主队' in pin_dir: signals.append(('Pinnacle', '看好主队', 1))
    elif pin and '看衰主队' in pin_dir: signals.append(('Pinnacle', '看衰主队', -1))
    else: signals.append(('Pinnacle', '中性', 0))
    # 信号5: 盘口共识
    if w_range < 0.20: signals.append(('盘口共识', '高度一致', 1))
    elif w_range > 0.50: signals.append(('盘口共识', '严重分歧', -1))
    else: signals.append(('盘口共识', '中等分歧', 0))
    # 信号6: 平局风险
    if lp['draw_rate'] > 0.30 and p_draw_raw < 0.30:
        signals.append(('平局风险', f'联赛{lp["draw_rate"]:.0%}vs模型{p_draw_raw:.1%}→低估', -1))
    else:
        signals.append(('平局风险', '正常', 0))

    pos = sum(s[2] for s in signals)
    for s in signals: print(f'  [{s[2]:+d}] {s[0]}: {s[1]}')

    if pos >= 2: verdict = '可考虑主胜方向'
    elif pos >= 0: verdict = '弱信号——观望'
    else: verdict = '信号不足——跳过'
    print(f'  综合得分: {pos:+d} -> {verdict}')

    # 赛后博弈
    print(f'\n  ── 赛后思维博弈 ──')
    if home_win and pos < 0:
        print(f'  ❌ 偏差: 主胜实际发生但决策偏保守(得分{pos:+d})')
        if down > up:
            print(f'  追问: {down}家降赔为何被忽略?')
            print(f'  回答: Kelly负EV的权重压过了赔率趋势信号')
            print(f'  正确路径: 赔率趋势+联赛主场校正联合权重应>Kelly点估计')
        if p_home_raw < 0.35:
            print(f'  追问: {league}主场优势(+{lp["home_boost"]:.0%})为何没计入?')
            print(f'  回答: OO-EPC是市场均值不含联赛校正')
            print(f'  正确路径: 先联赛校正->再Kelly->再综合多信号')
        print(f'  教训: 不要把竞彩定价导致的负EV当成"比赛不会发生"的证据')

    elif not home_win and pos >= 0:
        print(f'  ❌ 偏差: 决策偏主胜(得分{pos:+d})但实际{result}')
        if is_draw:
            print(f'  追问: {league}平局率{lp["draw_rate"]:.0%}为何被忽视?')
            print(f'  回答: 注意力集中在主胜信号上,平局风险被边缘化')
            print(f'  正确路径: {league}平局率>30%->强制将平局纳入决策框架')
            print(f'  教训: 高平局率联赛中"跳过主胜"不等于"比赛无价值"')

    elif home_win and pos >= 0:
        print(f'  ✅ 方向正确(得分{pos:+d}预测主胜方向,实际主胜)')
        print(f'  验证: 多信号交叉验证的有效性需要更多场次确认')
    else:
        print(f'  ✅ 决策正确(跳过非主胜)')
        if is_draw:
            print(f'  注意: {league}实际平局率{lp["draw_rate"]:.0%}>模型{p_draw_raw:.1%}')

    # 本场教训
    print(f'\n  本场核心教训:')
    lessons = []
    if home_win and p_home_raw < 0.40:
        lessons.append(f'{league}主场优势被市场低估——低概率不等于不会发生')
    if is_draw and p_draw_raw < 0.30:
        lessons.append(f'平局概率被低估({p_draw_raw:.1%}vs联赛{lp["draw_rate"]:.0%})——需联赛特定校正')
    if down > 5 and pos < 0:
        lessons.append(f'{down}家降赔信号被Kelly压制——多信号系统中赔率趋势权重应提升')
    if w_range > 0.40:
        lessons.append(f'公司分歧大({w_range:.2f})->任何单方向预测都不可靠')
    for l in lessons: print(f'  -> {l}')
    if not lessons: print(f'  -> 本场推理链经受住验证,无需调整')
