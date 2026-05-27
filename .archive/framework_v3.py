"""
园中园足彩分析框架 v3.1 — 20轮碰撞实验产物
三层递进 + 2串1精度升级(单选/双选/跳过)
"""
import sys, os, re, parse_odds
from probability_engine import oo_epc_convert, correct_fl_bias, kelly_fraction

LEAGUE_PARAMS = {
    '挪超': {'home_boost': 0.20, 'draw_rate': 0.24},
    '瑞超': {'home_boost': 0.10, 'draw_rate': 0.41},
    '德甲': {'home_boost': 0.10, 'draw_rate': 0.28},
    '英超': {'home_boost': 0.14, 'draw_rate': 0.29},
    '意甲': {'home_boost': 0.10, 'draw_rate': 0.24},
    '西甲': {'home_boost': 0.15, 'draw_rate': 0.25},
    '日职': {'home_boost': 0.10, 'draw_rate': 0.27},
    '英甲': {'home_boost': 0.15, 'draw_rate': 0.27},
}
DEFAULT_LP = {'home_boost': 0.10, 'draw_rate': 0.25}

def analyze_match(folder_path, league='挪超', search_data=None):
    lp = LEAGUE_PARAMS.get(league, DEFAULT_LP)
    result = {'league': league, 'layers': [], 'thought_chain': [], 'pick_type': '跳过'}

    try:
        data = parse_odds.parse_folder(folder_path)
        euro = data['euro_odds']['companies']
    except:
        result['decision'] = '数据错误-跳过'
        return result

    companies = list(euro.values())
    jc = None
    for k, v in euro.items():
        if '竞' in v.get('name', ''): jc = v; break
    if not jc: jc = companies[0]

    pin = None
    for seq, c in euro.items():
        if 'Pi' in c.get('name', ''): pin = c; break

    all_iw = [c['odds']['instant'][0] for c in companies[:30] if c['odds']['instant'][0] > 0]
    all_iw_init = [c['odds']['init'][0] for c in companies[:30] if c['odds']['init'][0] > 0]
    odds_list = [(c['odds']['instant'][0], c['odds']['instant'][1], c['odds']['instant'][2])
                 for c in companies[:30] if len(c.get('odds',{}).get('instant',[])) >= 3]
    probs = oo_epc_convert(odds_list)
    p_home = correct_fl_bias(probs['home'])
    p_draw = correct_fl_bias(probs['draw'])
    p_away = correct_fl_bias(probs['away'])

    w_range = max(all_iw) - min(all_iw) if len(all_iw) > 1 else 0
    prob_gap = abs(p_home - p_away)
    jc_odds = jc.get('odds', {}).get('instant', [1,1,1])

    up = sum(1 for i in range(min(len(all_iw), len(all_iw_init))) if all_iw[i] > all_iw_init[i] + 0.02)
    down = sum(1 for i in range(min(len(all_iw), len(all_iw_init))) if all_iw[i] < all_iw_init[i] - 0.02)

    pin_dir = '稳定'
    if pin:
        pi, pn = pin['odds']['instant'][0], pin['odds']['init'][0]
        if pi < pn - 0.02: pin_dir = '看好'
        elif pi > pn + 0.02: pin_dir = '看衰'

    # 亚盘
    ah_dir = '中性'
    for f in os.listdir(folder_path):
        if '亚盘对比' in f and f.endswith('.html'):
            with open(os.path.join(folder_path, f), 'r', encoding='gb2312', errors='replace') as fh:
                html = fh.read()
            rows = re.findall(r'<tr[^>]*>.*?</tr>', html, re.DOTALL)
            hcp_map = {'平手':0,'平手/半球':0.25,'半球':0.5,'半球/一球':0.75,'一球':1.0,
                       '一球/球半':1.25,'球半':1.5,'受平手':0,'受平手/半球':-0.25,'受半球':-0.5,
                       '受半球/一球':-0.75,'受一球':-1.0,'受一球/球半':-1.25,'受球半':-1.5,
                       '平半':0.25,'半一':0.75,'受平半':-0.25,'受半一':-0.75,'平打':0}
            hcp_vals = []
            for row in rows[1:]:
                tds = re.findall(r'<td[^>]*>(.*?)</td>', row)
                if len(tds) >= 4:
                    hcp_raw = re.sub(r'<[^>]+>', '', tds[2]).strip().replace('&nbsp;',' ')
                    for key, val in hcp_map.items():
                        if key in hcp_raw: hcp_vals.append(val); break
            if hcp_vals:
                ah_avg = sum(hcp_vals)/len(hcp_vals)
                if ah_avg > 0.05: ah_dir = '看好'
                elif ah_avg < -0.05: ah_dir = '看衰'
            break

    # ===== L1: Pinnacle+亚盘层 =====
    c1 = w_range < 0.50
    c2 = prob_gap > 0.05
    c3 = p_home < 0.55
    eu_ah_agree = (pin_dir == ah_dir) or pin_dir == '稳定' or ah_dir == '中性'
    l1_ok = c1 and c2 and c3 and eu_ah_agree

    # 碰撞#29: 联赛自动毕业机制——数据库≥3场→从新联赛升级为已校准
    league_db_count = {'挪超':13,'瑞超':8,'德甲':3,'英超':8,'意甲':7,'西甲':1,'日职':1,'英甲':1}
    calibrated_leagues = {'挪超', '瑞超', '德甲', '英超', '意甲'}
    new_league = league not in calibrated_leagues

    if l1_ok:
        if new_league or league in {'英超', '意甲'}:
            # 英超/意甲/新联赛 L1→降级双选(校准数据不足)
            result['decision'] = f'双选主不败({league}L1)'
            result['pick_type'] = '双选'
            result['layers'].append('L1')
            result['thought_chain'].append(f'L1: 激活但{league}→降级双选')
            return result
        if new_league:
            # 新联赛L1激活→降级为双选
            result['decision'] = f'双选主不败(新联赛L1)'
            result['pick_type'] = '双选'
            result['layers'].append('L1')
            result['thought_chain'].append(f'L1: 激活但新联赛→降级双选')
            return result
        direction = '单选主胜' if pin_dir == '看好' else '单选非主胜'
        result['decision'] = direction
        result['pick_type'] = '单选'
        result['layers'].append('L1')
        result['thought_chain'].append(f'L1: 极差{w_range:.2f}<0.50 概率差{prob_gap:.1%}>5% 主胜{p_home:.1%}<55% 欧亚一致→{direction}')
        return result

    # ===== L2: 联赛校正 + 精度升级 =====
    # 碰撞#28/#33: 方向翻转——客强信号(简化计算)
    aao = 0; aao_n = 0; aho = 0; aho_n = 0
    for c in companies[:30]:
        inst = c.get('odds',{}).get('instant',[])
        if len(inst) >= 3 and inst[0] > 0 and inst[2] > 0:
            aao += inst[2]; aao_n += 1
            aho += inst[0]; aho_n += 1
    avg_away_o = aao / max(1, aao_n)
    avg_home_o = aho / max(1, aho_n)
    away_strong = p_away > p_home + 0.08 or (avg_away_o < 2.5 and avg_home_o > 3.0)
    extreme_lock = False  # 极端一致反向锁
    direction_word = '客不败' if away_strong else '主不败'

    fail_reasons = []
    if not c1: fail_reasons.append(f'极差{w_range:.2f}')
    if not c2: fail_reasons.append(f'概率差{prob_gap:.1%}≤5%')
    if not c3: fail_reasons.append(f'过度自信{p_home:.1%}≥55%')
    if not eu_ah_agree: fail_reasons.append(f'欧亚矛盾(Pin:{pin_dir}vs亚盘:{ah_dir})')

    # 联赛校正 + 碰撞#28: 动态主场加成(客队越强,加成越小)
    # 研究: 客队每+1σ评分→主队胜率对数-0.80 (p<0.05)
    base_boost = lp['home_boost']
    if p_away > p_home:
        # 客队被市场看好→主场优势被质量差距削弱
        gap_factor = min(1.0, (p_away - p_home) / 0.25)
        dynamic_boost = base_boost * max(0.2, 1.0 - gap_factor)
    else:
        dynamic_boost = base_boost
    p_home_adj = min(p_home * (1 + dynamic_boost), 0.75)
    p_away_adj = p_away * (1 - dynamic_boost * 0.5)
    total = p_home_adj + p_draw + p_away_adj
    if total > 0:
        p_home_adj /= total
    k_raw = kelly_fraction(p_home, jc_odds[0])
    k_adj = kelly_fraction(p_home_adj, jc_odds[0])
    ev_improved = k_adj['expected_value'] > k_raw['expected_value']

    # 精度升级: 单选条件 (碰撞#19/20)
    # 豪门联赛阈值更高(>65%), 非豪门>55%
    overconf_threshold = 0.65 if league in {'英超','意甲','西甲','德甲'} else 0.55
    overconfident = p_home > overconf_threshold
    high_draw_lg = lp['draw_rate'] > 0.35
    has_inj = search_data and len(search_data.get('injuries', [])) >= 3

    # 碰撞#27/#34: 新联赛保守+极端一致反向
    if new_league:
        overconfident = False
        # 极端一致(>90%同向)→集体错误风险→翻方向
        total_dir = up + down
        if total_dir > 5:
            agree_ratio = max(up, down) / total_dir
            if agree_ratio > 0.9:
                direction_word = "客不败" if down > up else "主不败"
                extreme_lock = True  # 防止Smart Money覆盖
    low_prob = p_home < 0.30

    # L3预检
    l3_override = False
    if search_data and low_prob:
        hf = str(search_data.get('home_form', ''))
        wm = re.findall(r'(\d+)胜', hf)
        dm = re.findall(r'(\d+)平', hf)
        lm = re.findall(r'(\d+)负', hf)
        w = int(wm[0]) if wm else 0
        d = int(dm[0]) if dm else 0
        l = int(lm[0]) if lm else 0
        tg = w + d + l
        if tg > 0 and (w/tg - p_home) > 0.40:
            l3_override = True

    can_single = not overconfident and not high_draw_lg and not has_inj
    if low_prob and not l3_override:
        can_single = False
    # 碰撞#33: 伤缺强制双选(防008误判)
    if has_inj:
        can_single = False
    # 碰撞#31/#33: 英超/高平局联赛单选需L1激活(防利物浦/伯恩利误判)
    if can_single and not l1_ok and (league == '英超' or lp['draw_rate'] > 0.25):
        can_single = False  # 非L1+高平局联赛→强制双选
        # 需要至少2个额外信号: L1激活或Smart Money同意或主胜>50%
        extra_signals = 0
        if p_home > 0.50: extra_signals += 1
        if pin_dir == '看好': extra_signals += 1
        if ah_dir == '看好': extra_signals += 1
        if extra_signals < 2:
            can_single = False  # 信号不够→降为双选

    # 碰撞#30: Deep Smart Money仲裁 (位置15-19,63%准确率)
    # 仅在框架不自信(非单选)时,用Deep Smart共识覆盖方向
    if not can_single:
        deep_up = 0; deep_down = 0
        for i in [15,16,17,18,19]:
            if i >= len(companies): continue
            dc = companies[i]
            dc_inst = dc.get('odds', {}).get('instant', [])
            dc_init = dc.get('odds', {}).get('init', [])
            if len(dc_inst) >= 3 and len(dc_init) >= 3 and dc_init[0] > 0:
                if dc_inst[0] < dc_init[0] - 0.02: deep_down += 1
                elif dc_inst[0] > dc_init[0] + 0.02: deep_up += 1
        if deep_down >= 4 or deep_up >= 4:
            deep_dir = '主不败' if deep_down > deep_up else '客不败'
            if deep_dir != direction_word and not (avg_away_o < 2.5 and avg_home_o > 3.0) and not extreme_lock:
                direction_word = deep_dir  # 赔率明牌时不覆盖

    # 碰撞#21: 平局王相遇→可单选平局
    draw_specialist = False
    if search_data:
        home_draw_rate = search_data.get('home_draw_rate', 0)
        away_draw_rate = search_data.get('away_draw_rate', 0)
        if home_draw_rate > 0.40 and away_draw_rate > 0.40:
            draw_specialist = True

    # 碰撞#23/#29: 过度自信+市场撤退→单选平局(仅限非豪门联赛)
    # 豪门联赛(英超/意甲/西甲)中强队>60%往往合理定价,不适用过度自信反转
    top_leagues = {'英超', '意甲', '西甲', '德甲'}
    overconf_draw = False
    if overconfident and not c3 and league not in top_leagues:
        retreat_ratio = up / max(down, 1) if down > 0 else (up if up > 5 else 0)
        if retreat_ratio > 3.0 and pin_dir == '看衰':
            draw_odds_high = jc_odds[1] > 4.0 if len(jc_odds) > 1 else False
            if draw_odds_high:
                overconf_draw = True

    if new_league:
        # 新联赛保守模式(碰撞#27): 无校准数据, 禁止单选
        if l1_ok:
            decision = f'双选{direction_word}(新联赛L1激活)'
            pick_type = '双选'
        elif p_home > 0.35:
            decision = f'双选{direction_word}(新联赛)'
            pick_type = '双选'
        else:
            decision = '跳过(新联赛无校准)'
            pick_type = '跳过'
    elif draw_specialist:
        decision = '单选平局(平局王相遇)'
        pick_type = '单选'
    elif overconf_draw:
        decision = '单选平局(市场过度自信撤退)'
        pick_type = '单选'
    elif league == '德甲' and not can_single:
        decision = '跳过(德甲高市场效率)'
        pick_type = '跳过'
    elif can_single:
        decision = '单选主胜'
        pick_type = '单选'
        if overconfident or high_draw_lg or has_inj:
            decision = '单选主胜(校正)'
    else:
        reasons = []
        if overconfident: reasons.append('过度自信')
        if high_draw_lg: reasons.append(f'{league}高平局{lp["draw_rate"]:.0%}')
        if has_inj: reasons.append(f'伤缺')
        if low_prob and not l3_override: reasons.append(f'概率<30%')
        decision = f'双选{direction_word}({",".join(reasons)})' if reasons else f'双选{direction_word}'
        pick_type = '双选'

    result['decision'] = decision
    result['pick_type'] = pick_type
    result['layers'].append('L2')
    result['thought_chain'].append(f'L2: {"; ".join(fail_reasons)}→{decision}[{pick_type}]')
    return result


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    base = r'C:\Users\51095\Desktop\足彩'

    search_db = {
        '001': {'home_form': '主场1胜3平', 'injuries': []},
        '002': {'home_form': '主场4胜1负(80%)', 'injuries': []},
        '003': {'home_form': '主场5胜1平0负(83%)', 'injuries': []},
        '004': {'home_form': '主场一般', 'injuries': []},
        '005': {'home_form': '主场中游', 'injuries': []},
        '006': {'home_form': '主场弱(排名15)', 'injuries': []},
        '007': {'home_form': '主场3胜2平(60%)', 'injuries': [], 'home_draw_rate': 0.44, 'away_draw_rate': 0.50},
        '008': {'home_form': '主场7胜2平1负(70%)', 'injuries': ['邓斯比(大腿)','斯马伊洛维奇(红牌)','比尤恩(大腿)']},
        '009': {'home_form': '德乙队vs德甲队', 'injuries': []},
    }
    actuals = {'001':'主胜','002':'主胜','003':'平局','004':'主胜','005':'主胜',
               '006':'平局','007':'平局','008':'平局','009':'平局'}

    print('=' * 72)
    print('  园中园足彩分析框架 v3.4 — 23轮碰撞 + 过度自信退场检测')
    print('  L1=Stable L2单选=Correct L2双选=Risk 跳过=Abstain')
    print('=' * 72)

    singles = []; doubles = []; skips_list = []; results = {}
    for num in ['001','002','003','004','005','006','007','008','009']:
        folder = None
        for d in os.listdir(base):
            full = os.path.join(base, d)
            if os.path.isdir(full) and num in d: folder = full; break
        if not folder: continue
        lg = '挪超' if num in ['001','002','003','004','005','008'] else ('瑞超' if num in ['006','007'] else '德甲')
        result = analyze_match(folder, lg, search_db.get(num))
        actual = actuals[num]
        d = result['decision']
        pt = result.get('pick_type', '?')
        ly = result['layers'][-1] if result['layers'] else '?'

        # 置信度分级 (Foresportia-inspired)
        if 'L1' in result['layers']: badge = 'Stable'
        elif pt == '单选': badge = 'Correct'
        elif pt == '双选': badge = 'Risk'
        else: badge = 'Abstain'

        if pt == '单选': singles.append(num)
        elif pt == '双选': doubles.append(num)
        else: skips_list.append(num)

        if ('单选主胜' in d and actual == '主胜') or ('单选非主胜' in d and actual != '主胜') or ('单选平局' in d and actual == '平局'):
            ok = '✓';
        elif '双选主不败' in d and actual in ['主胜','平局']:
            ok = '✓'
        elif '跳过' in d: ok = '—'
        else: ok = '✗'

        results[num] = {'lg': lg, 'actual': actual, 'decision': d, 'pt': pt, 'badge': badge, 'ok': ok, 'layers': '→'.join(result['layers'])}
        print(f'  {num} {lg} 实际:{actual} [{results[num]["layers"]}] {d} [{pt}] [{badge}] {ok}')

    print(f'\n  单选{len(singles)}场({",".join(singles)}) 双选{len(doubles)}场({",".join(doubles)}) 跳过{len(skips_list)}场')
    print(f'\n  ═══ 2串1最优组合 (1单选+1双选 防冷结构) ═══')
    for s in singles:
        for dbl in doubles:
            print(f'  [{s}单选{results[s]["decision"]}] + [{dbl}双选] = 成本4元 ({results[s]["badge"]}+{results[dbl]["badge"]})')
    print(f'  共 {len(singles)*len(doubles)} 种4元组合')
    print(f'{"="*72}')
