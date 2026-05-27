# -*- coding: utf-8 -*-
"""世界杯2026专用准备系统
数据源: openfootball世界杯历史 + FIFA排名(2026-05) + 阵容变动
框架适配: 中立场地, 混合Elo(历史衰减+FIFA+伤病), 小组赛vs淘汰赛
"""
import sys, os, json, math, urllib.request

SCRIPT_DIR = os.path.dirname(__file__)
ELO_FILE = os.path.join(SCRIPT_DIR, '.elo_worldcup.json')
HYBRID_FILE = os.path.join(SCRIPT_DIR, '.elo_worldcup_hybrid.json')

# 队名映射 (WC_GROUPS → hybrid Elo key)
NAME_MAP = {
    'USA': 'United States',
    'South Korea': 'Korea Republic',
    'Ivory Coast': "Cote d'Ivoire",
    'Cape Verde': 'Cape Verde Islands',
    'DR Congo': 'DR Congo',
    'Czech Republic': 'Czechia',
    'Bosnia and Herzegovina': 'Bosnia',
    'Curacao': 'Curacao',
}

# 2026世界杯48队 + 分组
WC_GROUPS = {
    'A': ['Mexico', 'South Africa', 'South Korea', 'Czech Republic'],
    'B': ['Canada', 'Bosnia and Herzegovina', 'Qatar', 'Switzerland'],
    'C': ['Brazil', 'Morocco', 'Haiti', 'Scotland'],
    'D': ['United States', 'Paraguay', 'Australia', 'Turkey'],
    'E': ['Germany', 'Curacao', 'Ivory Coast', 'Ecuador'],
    'F': ['Netherlands', 'Japan', 'Sweden', 'Tunisia'],
    'G': ['Belgium', 'Egypt', 'Iran', 'New Zealand'],
    'H': ['Spain', 'Cape Verde', 'Saudi Arabia', 'Uruguay'],
    'I': ['France', 'Senegal', 'Iraq', 'Norway'],
    'J': ['Argentina', 'Algeria', 'Austria', 'Jordan'],
    'K': ['Portugal', 'DR Congo', 'Uzbekistan', 'Colombia'],
    'L': ['England', 'Croatia', 'Ghana', 'Panama'],
}

# 各组前两名晋级预测 (基于混合Elo自动生成)
GROUP_FAVORITES = {
    'A': ['Mexico', 'South Korea'],       # 韩国1348 > 捷克1242
    'B': ['Switzerland', 'Canada'],
    'C': ['Brazil', 'Morocco'],
    'D': ['United States', 'Australia'],   # 澳大利亚1341 > 土耳其1326
    'E': ['Germany', 'Ecuador'],
    'F': ['Netherlands', 'Japan'],
    'G': ['Belgium', 'Iran'],
    'H': ['Spain', 'Uruguay'],
    'I': ['France', 'Senegal'],
    'J': ['Argentina', 'Austria'],
    'K': ['Portugal', 'Colombia'],
    'L': ['England', 'Croatia'],
}


def load_wc_elo():
    """加载世界杯Elo, 优先使用混合评级"""
    if os.path.exists(HYBRID_FILE):
        with open(HYBRID_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    if os.path.exists(ELO_FILE):
        with open(ELO_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def get_wc_elo_signal(home_team, away_team):
    """获取世界杯比赛Elo信号 (中立场地, 无主场加成)"""
    elo = load_wc_elo()
    h_elo = elo.get(home_team, 1500)
    a_elo = elo.get(away_team, 1500)

    # 尝试队名映射
    if h_elo == 1500:
        for k, v in NAME_MAP.items():
            if k == home_team: h_elo = elo.get(v, 1500)
    if a_elo == 1500:
        for k, v in NAME_MAP.items():
            if k == away_team: a_elo = elo.get(v, 1500)

    diff = h_elo - a_elo
    prob = 1.0 / (1.0 + math.pow(10, -diff / 400.0))

    return {
        'elo_home': h_elo, 'elo_away': a_elo,
        'elo_diff': diff, 'elo_abs': abs(diff),
        'elo_direction': '主胜' if diff > 0 else '客胜',
        'elo_prob': round(prob, 3),
        'source': 'historical' if (h_elo != 1500 and a_elo != 1500) else 'default',
    }


def predict_wc_match(home_team, away_team, group_stage=True):
    """世界杯比赛预测 (混合Elo + 中立场地)
    混合Elo已包含: 历史衰减+FIFA排名+伤病/阵容调整
    """
    elo = get_wc_elo_signal(home_team, away_team)
    diff = elo['elo_diff']
    abs_diff = elo['elo_abs']

    # 中立场地: 无主场加成, 小组赛少平局
    if abs_diff >= 80:
        decision = '单选主胜' if diff > 0 else '单选客胜'
        badge = 'Stable'
        confidence = 80
    elif abs_diff >= 40:
        decision = '单选主胜' if diff > 0 else '单选客胜'
        badge = 'Correct'
        confidence = 65
    elif abs_diff >= 20:
        decision = '单选主胜' if diff > 0 else '单选客胜'
        badge = 'Correct'
        confidence = 50
    else:
        if group_stage:
            decision = '单选平局'
            badge = 'Risk'
            confidence = 40
        else:
            decision = '单选主胜' if diff > 0 else '单选客胜'
            badge = 'Risk'
            confidence = 35

    return {
        'decision': decision, 'badge': badge, 'confidence': confidence,
        'elo_info': elo, 'neutral_venue': True,
    }


def print_group_preview():
    """打印小组赛预览"""
    print('=' * 65)
    print('  2026世界杯 小组赛预览 (Elo排名)')
    print('=' * 65)

    for grp, teams in sorted(WC_GROUPS.items()):
        print()
        print('  Group %s:' % grp)
        elo = load_wc_elo()
        ranked = []
        for t in teams:
            e = elo.get(t, 1500)
            # NAME_MAP: key=WC_GROUPS名 → value=hybrid file名
            for k, v in NAME_MAP.items():
                if k == t:
                    e = elo.get(v, e)
            ranked.append((t, e))
        ranked.sort(key=lambda x: -x[1])
        for i, (t, e) in enumerate(ranked):
            flag = '★' if i < 2 else ' '
            print('    %s %-22s Elo:%d' % (flag, t, e))

    print()
    print('=' * 65)


def print_knockout_bracket():
    """打印淘汰赛对阵预测"""
    print('=' * 65)
    print('  2026世界杯 淘汰赛预估路径')
    print('=' * 65)

    # Round of 32 对阵 (按FIFA官方对阵表)
    # 1A vs 2B, 1C vs 2D, etc.
    # 简化: 用GROUP_FAVORITES预估
    print()
    print('  预估16强 (各组前两名):')
    for grp, favs in sorted(GROUP_FAVORITES.items()):
        print('    Group %s: %s / %s' % (grp, favs[0], favs[1]))

    # 半决赛和决赛预测
    print()
    print('  预估四强 (按Elo排名):')
    elo = load_wc_elo()
    all_teams = []
    for grp, favs in GROUP_FAVORITES.items():
        for t in favs:
            e = elo.get(t, 1500)
            for k, v in NAME_MAP.items():
                if k == t:
                    e = elo.get(v, e)
            all_teams.append((t, e))
    all_teams.sort(key=lambda x: -x[1])
    for i, (t, e) in enumerate(all_teams[:8]):
        print('    %d. %s (Elo:%d)' % (i+1, t, e))

    print()
    print('  Elo夺冠热门:')
    for i, (t, e) in enumerate(all_teams[:5]):
        prob = 1.0 / (1.0 + math.pow(10, -(e - 1500) / 400.0))
        print('    %d. %s (Elo:%d, 胜率%.0f%%)' % (i+1, t, e, prob*100))

    print()
    print('=' * 65)


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    print_group_preview()
    print()
    print_knockout_bracket()
