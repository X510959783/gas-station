# -*- coding: utf-8 -*-
"""Elo评分引擎 + 滚动战绩 + H2H特征
基于2025研究: 特征工程是准确率最大杠杆
"""
import sys, os, json, math

CACHE_FILE = os.path.join(os.path.dirname(__file__), '.elo_ratings.json')


def compute_elo(home_elo, away_elo, home_goals, away_goals, k=32):
    """更新Elo评分"""
    # 预期胜率
    dr = home_elo - away_elo
    expected_home = 1.0 / (1.0 + math.pow(10, -dr / 400.0))
    expected_away = 1.0 - expected_home

    # 实际结果 (1=主胜, 0.5=平, 0=客胜)
    if home_goals > away_goals:
        actual = 1.0
    elif home_goals == away_goals:
        actual = 0.5
    else:
        actual = 0.0

    # 进球差调整K值 (大胜→更大Elo变化)
    goal_diff = abs(home_goals - away_goals)
    if goal_diff >= 3:
        k_adj = k * 1.5
    elif goal_diff == 2:
        k_adj = k * 1.25
    else:
        k_adj = k

    new_home = home_elo + k_adj * (actual - expected_home)
    new_away = away_elo + k_adj * ((1 - actual) - expected_away)

    return round(new_home), round(new_away)


def build_elo_ratings(matches_db_file):
    """从历史比赛数据库构建Elo评分
    返回: {team_name: elo_rating, ...}
    """
    with open(matches_db_file, 'r', encoding='utf-8') as f:
        db = json.load(f)

    elo = {}  # team_name -> current elo
    START_ELO = 1500

    for m in sorted(db['matches'], key=lambda x: x.get('date', '')):
        home = m.get('home', '')
        away = m.get('away', '')
        if not home or not away:
            continue
        # 提取比分
        score = m.get('score', '')
        parts = score.split('-')
        if len(parts) != 2:
            continue
        try:
            hg, ag = int(parts[0]), int(parts[1])
        except ValueError:
            continue

        if home not in elo:
            elo[home] = START_ELO
        if away not in elo:
            elo[away] = START_ELO

        elo[home], elo[away] = compute_elo(
            elo[home], elo[away], hg, ag)

    return elo


def get_elo_signal(home_team, away_team, elo_ratings):
    """获取Elo相关信号: elo_diff, home_win_prob"""
    home_elo = elo_ratings.get(home_team, 1500)
    away_elo = elo_ratings.get(away_team, 1500)
    diff = home_elo - away_elo
    prob = 1.0 / (1.0 + math.pow(10, -diff / 400.0))
    return {
        'elo_home': home_elo,
        'elo_away': away_elo,
        'elo_diff': diff,
        'elo_home_prob': round(prob, 3),
    }


def compute_rolling_form(all_matches, team_name, n=5):
    """计算球队近N场滚动战绩"""
    team_matches = []
    for m in all_matches:
        home = m.get('home', '')
        away = m.get('away', '')
        if home != team_name and away != team_name:
            continue
        score = m.get('score', '')
        parts = score.split('-')
        if len(parts) != 2:
            continue
        try:
            hg, ag = int(parts[0]), int(parts[1])
        except ValueError:
            continue

        is_home = (home == team_name)
        gf = hg if is_home else ag
        ga = ag if is_home else hg
        result = 'W' if gf > ga else ('D' if gf == ga else 'L')

        team_matches.append({
            'date': m.get('date', ''),
            'is_home': is_home,
            'goals_for': gf,
            'goals_against': ga,
            'result': result,
            'opponent': away if is_home else home,
            'league': m.get('league', ''),
        })

    team_matches.sort(key=lambda x: x['date'], reverse=True)
    recent = team_matches[:n]

    if len(recent) < 3:
        return None

    w = sum(1 for r in recent if r['result'] == 'W')
    d = sum(1 for r in recent if r['result'] == 'D')
    l = sum(1 for r in recent if r['result'] == 'L')
    avg_gf = sum(r['goals_for'] for r in recent) / len(recent)
    avg_ga = sum(r['goals_against'] for r in recent) / len(recent)

    # 只统计主场/客场
    home_m = [r for r in recent if r['is_home']]
    away_m = [r for r in recent if not r['is_home']]
    hw = sum(1 for r in home_m if r['result'] == 'W')
    hd = sum(1 for r in home_m if r['result'] == 'D')
    aw = sum(1 for r in away_m if r['result'] == 'W')
    ad = sum(1 for r in away_m if r['result'] == 'D')

    return {
        'recent_w': w, 'recent_d': d, 'recent_l': l,
        'recent_ppg': round((w * 3 + d) / len(recent), 2),
        'recent_avg_gf': round(avg_gf, 1),
        'recent_avg_ga': round(avg_ga, 1),
        'home_win_rate': round(hw / len(home_m), 2) if home_m else 0,
        'away_win_rate': round(aw / len(away_m), 2) if away_m else 0,
        'home_draw_rate': round(hd / len(home_m), 2) if home_m else 0,
        'away_draw_rate': round(ad / len(away_m), 2) if away_m else 0,
        'n_matches': len(recent),
    }


def compute_h2h(all_matches, home_team, away_team, n=5):
    """计算两队历史交锋记录"""
    h2h_matches = []
    for m in all_matches:
        home = m.get('home', '')
        away = m.get('away', '')
        if not ((home == home_team and away == away_team) or
                (home == away_team and away == home_team)):
            continue
        score = m.get('score', '')
        parts = score.split('-')
        if len(parts) != 2:
            continue
        try:
            hg, ag = int(parts[0]), int(parts[1])
        except ValueError:
            continue

        is_home_team = (home == home_team)
        gf = hg if is_home_team else ag
        ga = ag if is_home_team else hg
        result = 'W' if gf > ga else ('D' if gf == ga else 'L')

        h2h_matches.append({
            'date': m.get('date', ''),
            'venue': 'H' if is_home_team else 'A',
            'goals_for': gf,
            'goals_against': ga,
            'result': result,
        })

    h2h_matches.sort(key=lambda x: x['date'], reverse=True)
    recent = h2h_matches[:n]

    if len(recent) < 2:
        return None

    w = sum(1 for r in recent if r['result'] == 'W')
    d = sum(1 for r in recent if r['result'] == 'D')
    l = sum(1 for r in recent if r['result'] == 'L')

    return {
        'h2h_w': w, 'h2h_d': d, 'h2h_l': l,
        'h2h_ppg': round((w * 3 + d) / len(recent), 2),
        'h2h_dominance': round((w - l) / len(recent), 2),
        'h2h_n': len(recent),
    }


def build_all_features(matches_db_file):
    """从数据库构建所有特征
    返回: {features, elo_ratings, all_matches}
    """
    with open(matches_db_file, 'r', encoding='utf-8') as f:
        db = json.load(f)

    all_matches = db['matches']
    elo = build_elo_ratings(matches_db_file)

    # 为每场有赛果的比赛构建特征
    features = []
    for m in all_matches:
        score = m.get('score', '')
        if not score:
            continue
        parts = score.split('-')
        if len(parts) != 2:
            continue
        try:
            hg, ag = int(parts[0]), int(parts[1])
        except ValueError:
            continue

        home = m.get('home', m.get('name', '').split('VS')[0]
                     if 'VS' in m.get('name', '') else '?')
        away = m.get('away', m.get('name', '').split('VS')[1]
                     if 'VS' in m.get('name', '') else '?')

        # Elo
        elo_sig = get_elo_signal(home, away, elo)

        # 滚动战绩
        home_form = compute_rolling_form(all_matches, home)
        away_form = compute_rolling_form(all_matches, away)

        # H2H
        h2h = compute_h2h(all_matches, home, away)

        feature_row = {
            'date': m.get('date', ''),
            'league': m.get('league', ''),
            'home': home, 'away': away,
            'hg': hg, 'ag': ag,
            'result': '主胜' if hg > ag else ('平局' if hg == ag else '客胜'),
            # 赔率特征
            'p_home': m.get('p_home', 0),
            'p_draw': m.get('p_draw', 0),
            'p_away': m.get('p_away', 0),
            'avg_home_odds': m.get('avg_home_odds', 0),
            'w_range': m.get('w_range', 0),
            'prob_gap': m.get('prob_gap', 0),
            'pin_dir': m.get('pin_dir', ''),
            # Elo特征
            'elo_home': elo_sig['elo_home'],
            'elo_away': elo_sig['elo_away'],
            'elo_diff': elo_sig['elo_diff'],
            'elo_home_prob': elo_sig['elo_home_prob'],
        }

        # 滚动战绩特征
        if home_form:
            feature_row.update({
                'h_recent_ppg': home_form['recent_ppg'],
                'h_recent_avg_gf': home_form['recent_avg_gf'],
                'h_recent_avg_ga': home_form['recent_avg_ga'],
                'h_home_win_rate': home_form['home_win_rate'],
                'h_home_draw_rate': home_form['home_draw_rate'],
            })
        if away_form:
            feature_row.update({
                'a_recent_ppg': away_form['recent_ppg'],
                'a_recent_avg_gf': away_form['recent_avg_gf'],
                'a_recent_avg_ga': away_form['recent_avg_ga'],
                'a_away_win_rate': away_form['away_win_rate'],
                'a_away_draw_rate': away_form['away_draw_rate'],
            })
        # H2H
        if h2h:
            feature_row.update({
                'h2h_ppg': h2h['h2h_ppg'],
                'h2h_dominance': h2h['h2h_dominance'],
                'h2h_n': h2h['h2h_n'],
            })

        features.append(feature_row)

    return features, elo


# ========== 自检 ==========
if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    db_file = os.path.join(os.path.dirname(__file__), 'match_db_full.json')

    print('构建Elo特征...')
    features, elo = build_all_features(db_file)
    print('特征数: %d' % len(features))

    if features:
        f = features[0]
        print('样例特征:')
        for k, v in sorted(f.items()):
            print('  %s: %s' % (k, v))

    # 简单验证: Elo_diff对结果的影响
    correct = 0
    total = 0
    for f in features:
        elo_pred = '主胜' if f['elo_diff'] > 0 else '客胜'
        if elo_pred == f['result']:
            correct += 1
        total += 1
    print()
    print('Elo方向准确率: %d/%d = %.0f%%' % (correct, total, 100*correct//total))
