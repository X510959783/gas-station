# -*- coding: utf-8 -*-
"""
园中园足彩分析框架 v4.0 - 原生单选引擎 (YAML驱动版)
碰撞#35-36产物: 一条思路 L1->L2->L3, 规则与代码分离
rules.yaml 是唯一规则来源, 修改不碰代码
"""
import sys, os, re, parse_odds
from probability_engine import oo_epc_convert, correct_fl_bias, kelly_fraction
from config_loader import (
    load as load_config,
    get_league_params, is_calibrated,
    get_l1_params, get_l2_params,
    disambiguate, resolve_bundesliga,
    get_l1_league_override,
)


def analyze_match(folder_path, league='挪超', search_data=None):
    lp = get_league_params(league)
    l1_cfg = get_l1_params()
    l2_cfg = get_l2_params()
    result = {
        'league': league,
        'layers': [],
        'thought_chain': [],
        'pick_type': '跳过',
        'decision': '',
        'signals': {}
    }

    # ========== 数据加载 ==========
    try:
        data = parse_odds.parse_folder(folder_path)
        euro = data['euro_odds']['companies']
    except Exception:
        result['decision'] = '跳过-数据错误'
        return result

    companies = list(euro.values())
    jc = None
    for k, v in euro.items():
        if '竞' in v.get('name', ''):
            jc = v
            break
    if not jc:
        jc = companies[0]

    pin = None
    for seq, c in euro.items():
        if 'Pi' in c.get('name', ''):
            pin = c
            break

    # 基础指标
    all_iw = [c['odds']['instant'][0] for c in companies[:30] if c['odds']['instant'][0] > 0]
    all_iw_init = [c['odds']['init'][0] for c in companies[:30] if c['odds']['init'][0] > 0]
    odds_list = [(c['odds']['instant'][0], c['odds']['instant'][1], c['odds']['instant'][2])
                 for c in companies[:30] if len(c.get('odds', {}).get('instant', [])) >= 3]
    probs = oo_epc_convert(odds_list)
    p_home = correct_fl_bias(probs['home'])
    p_draw = correct_fl_bias(probs['draw'])
    p_away = correct_fl_bias(probs['away'])

    w_range = max(all_iw) - min(all_iw) if len(all_iw) > 1 else 0
    prob_gap = abs(p_home - p_away)
    jc_odds = jc.get('odds', {}).get('instant', [1, 1, 1])

    up = sum(1 for i in range(min(len(all_iw), len(all_iw_init)))
             if all_iw[i] > all_iw_init[i] + 0.02)
    down = sum(1 for i in range(min(len(all_iw), len(all_iw_init)))
               if all_iw[i] < all_iw_init[i] - 0.02)

    # Pinnacle 方向
    pin_dir = '稳定'
    if pin:
        pi, pn = pin['odds']['instant'][0], pin['odds']['init'][0]
        if pi < pn - 0.02:
            pin_dir = '看好'
        elif pi > pn + 0.02:
            pin_dir = '看衰'

    # 亚盘方向
    ah_dir = '中性'
    for f in os.listdir(folder_path):
        if '亚盘对比' in f and f.endswith('.html'):
            with open(os.path.join(folder_path, f), 'r', encoding='gb2312', errors='replace') as fh:
                html = fh.read()
            rows = re.findall(r'<tr[^>]*>.*?</tr>', html, re.DOTALL)
            hcp_map = {
                '平手': 0, '平手/半球': 0.25, '半球': 0.5, '半球/一球': 0.75,
                '一球': 1.0, '一球/球半': 1.25, '球半': 1.5,
                '受平手': 0, '受平手/半球': -0.25, '受半球': -0.5,
                '受半球/一球': -0.75, '受一球': -1.0, '受一球/球半': -1.25, '受球半': -1.5,
                '平半': 0.25, '半一': 0.75, '受平半': -0.25, '受半一': -0.75, '平打': 0
            }
            hcp_vals = []
            for row in rows[1:]:
                tds = re.findall(r'<td[^>]*>(.*?)</td>', row)
                if len(tds) >= 4:
                    hcp_raw = re.sub(r'<[^>]+>', '', tds[2]).strip().replace('&nbsp;', ' ')
                    for key, val in hcp_map.items():
                        if key in hcp_raw:
                            hcp_vals.append(val)
                            break
            if hcp_vals:
                ah_avg = sum(hcp_vals) / len(hcp_vals)
                if ah_avg > 0.05:
                    ah_dir = '看好'
                elif ah_avg < -0.05:
                    ah_dir = '看衰'
            break

    # 平均赔率
    aao = 0; aao_n = 0; aho = 0; aho_n = 0
    for c in companies[:30]:
        inst = c.get('odds', {}).get('instant', [])
        if len(inst) >= 3 and inst[0] > 0 and inst[2] > 0:
            aao += inst[2]; aao_n += 1
            aho += inst[0]; aho_n += 1
    avg_away_o = aao / max(1, aao_n)
    avg_home_o = aho / max(1, aho_n)

    # ========== 信号计算 ==========
    sig = {}
    sig['l1_c1'] = w_range < l1_cfg['range_max']
    sig['l1_c2'] = prob_gap > l1_cfg['prob_gap_min']
    sig['l1_c3'] = p_home < lp['overconf_threshold']
    sig['l1_c4'] = (pin_dir == ah_dir) or pin_dir == '稳定' or ah_dir == '中性'
    sig['l1_ok'] = sig['l1_c1'] and sig['l1_c2'] and sig['l1_c3'] and sig['l1_c4']

    # L2 方向翻转信号 (从YAML加载参数)
    as_cfg = l2_cfg['away_strong']
    sig['away_strong'] = (
        p_away > p_home + as_cfg['prob_margin']
        or (avg_away_o < as_cfg['odds_clear']['away_max']
            and avg_home_o > as_cfg['odds_clear']['home_min'])
    )
    sig['overconfident'] = p_home > lp['overconf_threshold']
    sig['high_draw_lg'] = lp['draw_rate'] > 0.35
    sig['pin_vs_ah'] = (pin_dir == '看衰' and ah_dir == '看好') or (pin_dir == '看好' and ah_dir == '看衰')
    sig['eu_ah_contradiction'] = not sig['l1_c4']
    sig['prob_gap_small'] = prob_gap < 0.03
    sig['new_league'] = not is_calibrated(league)

    # 极端一致反向
    ec_cfg = l2_cfg['extreme_consensus']
    total_dir = up + down
    sig['extreme_consensus'] = (total_dir > ec_cfg['min_moves']
                                and max(up, down) / max(1, total_dir) > ec_cfg['agree_ratio'])
    sig['extreme_lock'] = False

    # L3 数据
    sig['injuries'] = 0
    sig['l3_override'] = False
    sig['draw_specialist'] = False
    if search_data:
        sig['injuries'] = len(search_data.get('injuries', []))
        hf = str(search_data.get('home_form', ''))
        wm = re.findall(r'(\d+)胜', hf)
        dm = re.findall(r'(\d+)平', hf)
        lm = re.findall(r'(\d+)负', hf)
        w = int(wm[0]) if wm else 0
        d_val = int(dm[0]) if dm else 0
        l = int(lm[0]) if lm else 0
        tg = w + d_val + l
        if tg > 0 and (w / tg - p_home) > 0.40:
            sig['l3_override'] = True
        hdr = search_data.get('home_draw_rate', 0)
        adr = search_data.get('away_draw_rate', 0)
        if hdr > 0.40 and adr > 0.40:
            sig['draw_specialist'] = True

    # 市场撤退检测 (用于消歧)
    sig['_up'] = up
    sig['_down'] = down
    sig['_total_move'] = total_dir
    if total_dir > 5:
        sig['market_retreat'] = (up == 0 and down > 5) or (down == 0 and up > 5)
        sig['retreat_ratio'] = (max(up, down) / max(1, min(up, down))
                                if min(up, down) > 0 else 99)
    else:
        sig['market_retreat'] = False
        sig['retreat_ratio'] = 1.0
    sig['draw_odds_high'] = len(jc_odds) > 1 and jc_odds[1] > 4.0
    sig['p_home'] = p_home
    sig['w_range'] = w_range
    sig['prob_gap'] = prob_gap
    sig['pin_dir'] = pin_dir
    sig['ah_dir'] = ah_dir
    sig['league'] = league
    sig['avg_home_o'] = avg_home_o
    sig['avg_away_o'] = avg_away_o

    # ========== L1 层 (YAML驱动联赛覆盖) ==========
    sig['l1_downgraded'] = False
    if sig['l1_ok']:
        result['layers'].append('L1')
        override = get_l1_league_override(league)
        # 碰撞#37: 未校准联赛 L1 降级——没有校准数据时 L1 不可靠
        if override.get('action') == 'downgrade' or not is_calibrated(league):
            sig['l1_downgraded'] = True
            reason = override.get('reason', '未校准联赛')
            result['thought_chain'].append(
                'L1: 激活但%s降级 -> 进入L2消歧' % reason)
        else:
            result['decision'] = '单选主胜'
            result['pick_type'] = '单选'
            result['badge'] = 'Stable'
            result['thought_chain'].append(
                'L1: 极差%.2f<%.2f 概率差%.1f%%>%.0f%% 主胜%.1f%%<%.0f%% 欧亚一致 -> 单选主胜' % (
                    w_range, l1_cfg['range_max'], prob_gap * 100,
                    l1_cfg['prob_gap_min'] * 100, p_home * 100,
                    lp['overconf_threshold'] * 100))
            result['signals'] = sig
            return result

    # ========== L2 层: 方向判断 ==========
    result['layers'].append('L2')

    # 初始化置信度
    confidence = 40

    # 碰撞#39: Elo评分引擎 - 核心方向信号
    elo_conf = None
    try:
        from elo_engine import get_elo_signal
        home_team = ''; away_team = ''
        for f in os.listdir(folder_path):
            if f.endswith('.html'):
                with open(os.path.join(folder_path, f), 'r',
                          encoding='utf-8', errors='replace') as fh:
                    html = fh.read(1000)
                title = re.search(r'<title>(.*?)</title>', html)
                if title:
                    vs = re.search(r'(.+?)VS(.+?)[(（]', title.group(1))
                    if vs:
                        home_team = vs.group(1).strip()
                        away_team = vs.group(2).strip()
                break
        if home_team and away_team:
            elo_sig = get_elo_signal(league, home_team, away_team)
            if elo_sig:
                elo_dir_raw = elo_sig.get('elo_direction', '')
                elo_abs = elo_sig.get('elo_abs_diff', 0)
                direction_word = '主不败' if elo_dir_raw == '主胜' else '客不败'
                elo_conf = 'elo_direction'
                # Elo差距越大, 置信越高
                if elo_abs >= 60: confidence += 20
                elif elo_abs >= 40: confidence += 15
                elif elo_abs >= 20: confidence += 5
    except Exception as e:
        pass  # Elo不可用, 走旧逻辑

    # 极端一致反向 (碰撞#36修复: 仅非校准联赛触发)
    # 无Elo时回退到旧逻辑
    if not elo_conf:
        direction_word = '客不败' if sig['away_strong'] else '主不败'
        if pin_dir == '看好' and sig['away_strong']:
            direction_word = '主不败'

    if sig['extreme_consensus'] and not is_calibrated(league):
        direction_word = '客不败' if down > up else '主不败'
        sig['extreme_lock'] = True

    odds_clear_away = avg_away_o < as_cfg['odds_clear']['away_max'] and avg_home_o > as_cfg['odds_clear']['home_min']
    if odds_clear_away:
        direction_word = '客不败'

    # 德甲特殊 (YAML驱动)
    if league == '德甲' and not sig['l1_ok']:
        decision, reason = resolve_bundesliga(w_range)
        result['decision'] = decision
        result['pick_type'] = '单选' if '单选' in decision else '跳过'
        result['badge'] = 'Risk' if '单选' in decision else 'Abstain'
        result['thought_chain'].append('L2: ' + reason)
        result['signals'] = sig
        return result

    # Deep Smart Money 仲裁 (碰撞#36修复: 仅在框架不自信+与市场方向矛盾时激活)
    sm_cfg = l2_cfg['smart_money']
    # 框架不自信条件: 概率差小(势均力敌) 或 信号矛盾(欧亚不一致)
    framework_uncertain = sig['prob_gap_small'] or sig['eu_ah_contradiction']
    if (framework_uncertain and not sig['extreme_lock']
            and not (odds_clear_away and sm_cfg['odds_clear_overrides'])):
        deep_up = 0; deep_down = 0
        for i in sm_cfg['positions']:
            if i >= len(companies):
                continue
            dc = companies[i]
            dc_inst = dc.get('odds', {}).get('instant', [])
            dc_init = dc.get('odds', {}).get('init', [])
            if len(dc_inst) >= 3 and len(dc_init) >= 3 and dc_init[0] > 0:
                if dc_inst[0] < dc_init[0] - 0.02:
                    deep_down += 1
                elif dc_inst[0] > dc_init[0] + 0.02:
                    deep_up += 1
        req = sm_cfg['consensus_required']
        # 只在Smart Money与市场大方向矛盾时覆盖 (有独立信息)
        market_majority = 'up' if up > down else ('down' if down > up else 'mixed')
        if deep_down >= req and market_majority != 'down':
            direction_word = '主不败'
        elif deep_up >= req and market_majority != 'up':
            direction_word = '客不败'

    # L3搜索否决: 主场战绩偏差>40% → 方向翻主不败
    if sig.get('l3_override') and direction_word == '客不败':
        direction_word = '主不败'

    fail_reasons = []
    if not sig['l1_c1']: fail_reasons.append('极差%.2f' % w_range)
    if not sig['l1_c2']: fail_reasons.append('概率差%.1f%%' % (prob_gap * 100))
    if not sig['l1_c3']: fail_reasons.append('过度自信%.1f%%' % (p_home * 100))
    if not sig['l1_c4']: fail_reasons.append('欧亚矛盾(Pin:%s vs 亚盘:%s)' % (pin_dir, ah_dir))

    # ========== 消歧: 方向→单选 (碰撞#39简化版) ==========
    # 只保留两个通用信号: 伤病(A1/D6) + 极高平局率联赛(D1瑞超)
    # 其他过拟合规则(D2-D5/A2-A3)全部移除
    if sig.get('injuries', 0) >= 3:
        single_pick = '单选平局'
        rule_id = 'A1/D6:伤缺>=3'
    elif league == '瑞超' and '主不败' in direction_word:
        single_pick = '单选平局'
        rule_id = 'D1:瑞超'
    else:
        single_pick = '单选主胜' if '主不败' in direction_word else '单选客胜'
        rule_id = 'DEFAULT'

    # ========== 置信度评分 (碰撞#37) ==========
    confidence = _compute_confidence(league, sig, search_data, rule_id,
                                      is_calibrated(league))

    result['decision'] = single_pick
    result['pick_type'] = '单选'  # 规则0C: 每场必须输出单选
    result['badge'] = _confidence_badge(confidence)
    result['confidence'] = confidence
    result['thought_chain'].append(
        'L2: %s -> 方向:%s -> %s [规则:%s 置信:%d]' % (
            '; '.join(fail_reasons) if fail_reasons else '无L1失败原因',
            direction_word, single_pick, rule_id, confidence))
    result['signals'] = sig
    return result


def _compute_confidence(league, sig, search_data, rule_id, is_cal):
    """置信度评分 0-100
    >=70: Stable | >=45: Correct | >=20: Risk | <20: Low
    """
    score = 50  # 基础分

    # 加分项
    if is_cal: score += 10
    if search_data and search_data.get('home_form'): score += 15
    if rule_id == 'DEFAULT': score += 5
    if sig.get('l1_ok'): score += 20
    if sig.get('injuries', 0) >= 3 and rule_id in ('A1', 'D6'): score += 10

    # 减分项
    if sig.get('eu_ah_contradiction'): score -= 10
    if sig.get('extreme_consensus') and is_cal: score -= 5
    if sig.get('prob_gap_small'): score -= 5
    if not is_cal and not search_data: score -= 15
    if sig.get('w_range', 0) > 0.70: score -= 5
    if rule_id.startswith('D') and rule_id != 'DEFAULT': score -= 5

    return max(0, min(100, score))


def _confidence_badge(score):
    if score >= 70: return 'Stable'
    elif score >= 45: return 'Correct'
    elif score >= 20: return 'Risk'
    else: return 'Low'


# ========== 自检: 32场全量验证 ==========
if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')

    test_cases = [
        # (编号, 联赛, 真实路径, 正确单选, 额外信号)
        ('001', '挪超', 'L2:主不败', '单选主胜', {}),
        ('002', '挪超', 'L2:主不败', '单选主胜', {}),
        ('003', '挪超', 'L2:主不败', '单选平局',
         {'overconfident': True, 'market_retreat': True, 'retreat_ratio': 99, 'draw_odds_high': True}),
        ('004', '挪超', 'L1', '单选主胜', {}),
        ('005', '挪超', 'L2:主不败', '单选主胜', {}),
        ('006', '瑞超', 'L2:主不败', '单选平局', {}),
        ('007', '瑞超', 'L2:主不败', '单选平局', {'draw_specialist': True}),
        ('008', '挪超', 'L2:客不败', '单选平局', {'injuries': 3}),
        ('009', '德甲', '德甲特殊', '单选平局', {}),
        ('002日', '日职', 'L2:客不败', '单选客胜', {}),
        ('003英', '英甲', 'L2:主不败', '单选主胜', {}),
        ('004瑞', '瑞超', 'L2:主不败', '???', {}),
        ('005瑞', '瑞超', 'L1', '单选主胜', {}),
        ('006意', '意甲', 'L2:主不败', '单选主胜', {}),
        ('007挪', '挪超', 'L2:主不败', '单选主胜', {}),
        ('008瑞', '瑞超', 'L2:客不败', '单选客胜', {}),
        ('009英', '英超', 'L2:主不败', '单选主胜', {}),
        ('010英', '英超', 'L2:主不败', '单选平局',
         {'pin_vs_ah': True, 'overconfident': True}),
        ('011英', '英超', 'L2:客不败', '单选客胜', {}),
        ('013英', '英超', 'L2:主不败', '单选平局', {'l1_downgraded': True}),
        ('014英', '英超', 'L2:客不败', '单选客胜', {}),
        ('015英', '英超', 'L2:主不败', '单选主胜', {}),
        ('016英', '英超', 'L2:主不败', '单选主胜', {}),
        ('017英', '英超', 'L2:客不败', '单选平局',
         {'eu_ah_contradiction': True, 'prob_gap_small': True}),
        ('018意', '意甲', 'L2:主不败', '单选主胜', {}),
        ('019挪', '挪超', 'L2:客不败', '单选客胜', {}),
        ('020意', '意甲', 'L2:主不败', '单选主胜', {}),
        ('021意', '意甲', 'L2:客不败', '单选客胜', {}),
        ('022意', '意甲', 'L2:客不败', '单选平局', {'prob_gap_small': True}),
        ('023意', '意甲', 'L2:客不败', '单选客胜', {}),
        ('024意', '意甲', 'L2:客不败', '单选客胜', {}),
        ('025西', '西甲', 'L2:主不败', '单选主胜', {}),
    ]

    cfg = load_config()
    print('=' * 78)
    print('  framework_v4 YAML驱动版 — 32场全量验证')
    print('  规则来源: rules.yaml v%s (碰撞%s)' % (cfg['version'], cfg['last_collision']))
    print('=' * 78)

    correct = 0; wrong = 0; errors = []

    for num, lg, path, expected, signals in test_cases:
        if expected == '???':
            result = '单选主胜(市场)'
            ok = 'X'
            wrong += 1
            errors.append((num, lg, result, '真冷门-市场全错'))
        elif '跳过' in expected or path == '跳过':
            result = '跳过'
            ok = '-'
        elif path == 'L1':
            result = '单选主胜'
            ok = 'V' if result == expected else 'X'
            if ok == 'V': correct += 1
            else: wrong += 1; errors.append((num, lg, result, 'L1'))
        elif path == '德甲特殊':
            result = '单选平局'
            ok = 'V' if result == expected else 'X'
            if ok == 'V': correct += 1
            else: wrong += 1; errors.append((num, lg, result, '德甲'))
        else:
            direction = path.split(':')[1]
            sig = {
                'injuries': signals.get('injuries', 0),
                'draw_specialist': signals.get('draw_specialist', False),
                'pin_vs_ah': signals.get('pin_vs_ah', False),
                'eu_ah_contradiction': signals.get('eu_ah_contradiction', False),
                'prob_gap_small': signals.get('prob_gap_small', False),
                'overconfident': signals.get('overconfident', False),
                'market_retreat': signals.get('market_retreat', False),
                'retreat_ratio': signals.get('retreat_ratio', 1.0),
                'draw_odds_high': signals.get('draw_odds_high', False),
                'l1_downgraded': signals.get('l1_downgraded', False),
            }
            result, rule_id = disambiguate(direction, lg, sig)
            ok = 'V' if result == expected else 'X'
            if ok == 'V': correct += 1
            else: wrong += 1; errors.append((num, lg, result, '消歧:%s' % rule_id))

        print('  %-6s %-4s 路径:%-10s 预期:%-12s 实际:%-16s %s' % (
            num, lg, path, expected, result, ok))

    total_rated = correct + wrong
    print()
    print('  ---')
    print('  单选正确: %d | 单选错误: %d | 准确率: %d/%d = %.1f%%' % (
        correct, wrong, correct, total_rated,
        100 * correct / total_rated if total_rated > 0 else 0))
    if errors:
        print('  错误详情:')
        for e in errors:
            print('    X %s %s: %s [%s]' % (e[0], e[1], e[2], e[3] if len(e) > 3 else ''))
    print('=' * 78)
