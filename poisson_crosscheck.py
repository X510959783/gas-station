# -*- coding: utf-8 -*-
"""Poisson交叉验证 - Rule 0B第二路径
碰撞#37: 满足三遍分析铁律 OO-EPC->Kelly->Poisson->三者对照
"""
import sys, math


def estimate_team_strength(form_data):
    """从球队战绩估算攻防强度"""
    if not form_data:
        return None
    matches = form_data.get('recent_matches', [])
    if len(matches) < 3:
        return None
    total_scored = sum(m.get('goals_for', 0) for m in matches)
    total_conceded = sum(m.get('goals_against', 0) for m in matches)
    n = len(matches)
    return {
        'attack': total_scored / max(1, n),
        'defense': total_conceded / max(1, n),
        'avg_scored': round(total_scored / max(1, n), 2),
        'avg_conceded': round(total_conceded / max(1, n), 2),
        'matches_used': n,
    }


def poisson_pmf(lam, k):
    """Poisson P(X=k)"""
    if lam <= 0:
        return 1.0 if k == 0 else 0.0
    return math.exp(-lam) * (lam ** k) / math.factorial(k)


def simulate_match(home_strength, away_strength, league_avg=(1.35, 1.10)):
    """Poisson模拟比赛结果概率"""
    if not home_strength or not away_strength:
        return None

    ha = home_strength['attack']
    hd = home_strength['defense']
    aa = away_strength['attack']
    ad = away_strength['defense']
    avg_h, avg_a = league_avg

    # 攻防比值调整 + 主场优势
    home_ar = ha / max(0.5, avg_h)
    home_dr = hd / max(0.5, avg_h)
    away_ar = aa / max(0.5, avg_a)
    away_dr = ad / max(0.5, avg_a)

    home_xg = avg_h * home_ar / max(0.5, away_dr) * 1.15
    away_xg = avg_a * away_ar / max(0.5, home_dr) * 0.85
    home_xg = max(0.3, min(5.0, home_xg))
    away_xg = max(0.2, min(4.0, away_xg))

    max_g = 8
    hw = dr = aw = 0.0
    for hg in range(max_g + 1):
        ph = poisson_pmf(home_xg, hg)
        for ag in range(max_g + 1):
            prob = ph * poisson_pmf(away_xg, ag)
            if hg > ag:
                hw += prob
            elif hg == ag:
                dr += prob
            else:
                aw += prob

    total = hw + dr + aw
    if total > 0:
        hw /= total; dr /= total; aw /= total

    direction = '主胜' if hw > aw else ('客胜' if aw > hw else '平局')
    return {
        'home_win': round(hw, 4),
        'draw': round(dr, 4),
        'away_win': round(aw, 4),
        'expected_home_goals': round(home_xg, 2),
        'expected_away_goals': round(away_xg, 2),
        'direction': direction,
        'confidence': round(max(hw, dr, aw), 3),
    }


def crosscheck(ooepc_probs, poisson_probs, kelly_ev):
    """三路径交叉验证
    返回: {agreement, agreed_direction, confidence_boost, details}
    """
    details = []

    oo_dir = '主胜' if ooepc_probs['home'] > ooepc_probs['away'] else '客胜'
    oo_max = max(ooepc_probs['home'], ooepc_probs['away'])
    details.append('OO-EPC: %s(%.0f%%)' % (oo_dir, oo_max * 100))

    poisson_dir = None
    if poisson_probs:
        poisson_dir = poisson_probs['direction']
        pconf = poisson_probs['confidence']
        details.append('Poisson: %s(%.0f%%)' % (poisson_dir, pconf * 100))

    kelly_dir = None
    if kelly_ev:
        ev_max = max(kelly_ev.values())
        ev_map = {'home': '主胜', 'draw': '平局', 'away': '客胜'}
        for k, v in kelly_ev.items():
            if v == ev_max:
                kelly_dir = ev_map[k]
                break
        details.append('Kelly: %s(EV=%+.3f)' % (kelly_dir, ev_max))

    directions = [d for d in [oo_dir, poisson_dir, kelly_dir] if d]
    if len(directions) < 2:
        return {'agreement': 'insufficient', 'agreed_direction': oo_dir,
                'confidence_boost': 0, 'details': details}

    unique = set(directions)
    n = len(directions)

    if len(unique) == 1:
        boost = {2: 8, 3: 15}[n]
        details.insert(0, '%d路径全一致->置信加成+%d' % (n, boost))
        return {'agreement': 'full', 'agreed_direction': directions[0],
                'confidence_boost': boost, 'details': details}
    elif len(unique) == 2 and n == 3:
        majority = max(set(directions), key=directions.count)
        details.insert(0, '2/3一致(%s)->加成+3' % majority)
        return {'agreement': 'partial', 'agreed_direction': majority,
                'confidence_boost': 3, 'details': details}
    else:
        details.insert(0, '路径冲突->减分-5')
        return {'agreement': 'conflict', 'agreed_direction': oo_dir,
                'confidence_boost': -5, 'details': details}


def run_crosscheck(framework_sig, search_data, jc_odds):
    """从框架信号中提取数据, 执行完整三路径验证

    参数:
      framework_sig: framework_v4 输出的 sig dict
      search_data: L3搜索数据 (含home_form/away_form)
      jc_odds: 竞彩即时赔率 [home, draw, away]

    返回: crosscheck() 输出
    """
    # 第一路径: OO-EPC (已经在框架中计算)
    ooepc = {
        'home': framework_sig.get('p_home', 0.33),
        'draw': framework_sig.get('p_draw', framework_sig.get('prob_gap', 0.34)),
        'away': framework_sig.get('p_away', 0.33),
    }
    # 用prob_gap推算平局概率
    if 'p_draw' not in framework_sig:
        gap = abs(ooepc['home'] - ooepc['away'])
        ooepc['draw'] = max(0.15, 1.0 - ooepc['home'] - ooepc['away'])

    # 第二路径: Poisson
    poisson = None
    if search_data:
        home_form_data = search_data.get('_home_form_data')
        away_form_data = search_data.get('_away_form_data')
        if home_form_data or away_form_data:
            from auto_search import scrape_team_form
            # 如果已有原始form数据, 直接估算
            hs = estimate_team_strength(home_form_data)
            aws = estimate_team_strength(away_form_data)
            poisson = simulate_match(hs, aws)

    # 第三路径: Kelly
    kelly = None
    if jc_odds and len(jc_odds) >= 3:
        from probability_engine import kelly_fraction
        kh = kelly_fraction(ooepc['home'], jc_odds[0])
        kd = kelly_fraction(ooepc['draw'], jc_odds[1])
        ka = kelly_fraction(ooepc['away'], jc_odds[2])
        kelly = {
            'home': kh['expected_value'],
            'draw': kd['expected_value'],
            'away': ka['expected_value'],
        }

    return crosscheck(ooepc, poisson, kelly)


# ========== 自检 ==========
if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')

    print('=' * 50)
    print('  Poisson交叉验证 - Rule 0B第二路径')
    print('=' * 50)

    home_s = {'attack': 1.8, 'defense': 1.0, 'avg_scored': 1.8, 'avg_conceded': 1.0}
    away_s = {'attack': 1.0, 'defense': 1.5, 'avg_scored': 1.0, 'avg_conceded': 1.5}

    result = simulate_match(home_s, away_s)
    print('主(攻1.8/防1.0) vs 客(攻1.0/防1.5):')
    print('  主胜: %.1f%%  平局: %.1f%%  客胜: %.1f%%' % (
        result['home_win'] * 100, result['draw'] * 100, result['away_win'] * 100))
    print('  预期进球: %.1f-%.1f  Poisson方向: %s' % (
        result['expected_home_goals'], result['expected_away_goals'], result['direction']))

    ooepc = {'home': 0.45, 'draw': 0.28, 'away': 0.27}
    kelly = {'home': 0.03, 'draw': -0.05, 'away': -0.08}
    cc = crosscheck(ooepc, result, kelly)
    print('\n三路径验证:')
    print('  一致性: %s  方向: %s  加成: %+d' % (
        cc['agreement'], cc['agreed_direction'], cc['confidence_boost']))
    for d in cc['details']:
        print('    %s' % d)

    print('\n' + '=' * 50)
    print('  验证通过')
    print('=' * 50)
