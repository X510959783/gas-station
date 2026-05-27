# -*- coding: utf-8 -*-
"""世界杯2026混合评级系统
三层数据融合:
  1. 历史世界杯Elo (2018+2022) — 30% 权重, 3.5年时间衰减
  2. 最新FIFA排名 (2026年5月) — 35% 权重
  3. 阵容/伤病调整 — 35% 权重 (实际比赛结果 + 关键球员变动)

核心原理: 国家队4年一届, 人员变动大, 纯历史Elo不可靠。
"""

import json, math, os

SCRIPT_DIR = os.path.dirname(__file__)
ELO_FILE = os.path.join(SCRIPT_DIR, '.elo_worldcup.json')
HYBRID_FILE = os.path.join(SCRIPT_DIR, '.elo_worldcup_hybrid.json')

# ============================================================
# 第1层: 2026年5月 FIFA 排名 → Elo 转换
# 来源: FIFA官方排名 (2026-05-21更新)
# 转换公式: Elo ≈ FIFA_Points - 300
# ============================================================
FIFA_RANKINGS_2026_05 = {
    'France': 1877.32, 'Spain': 1876.40, 'Argentina': 1874.81,
    'England': 1825.97, 'Portugal': 1763.83, 'Brazil': 1761.16,
    'Netherlands': 1757.87, 'Morocco': 1755.87, 'Belgium': 1734.71,
    'Germany': 1730.37, 'Croatia': 1717.07, 'Colombia': 1693.09,
    'Senegal': 1688.99, 'Mexico': 1681.03, 'United States': 1673.13,
    'Uruguay': 1673.07, 'Japan': 1660.43, 'Switzerland': 1649.40,
    'Iran': 1615.30, 'Turkey': 1599.04, 'Ecuador': 1594.78,
    'Austria': 1593.45, 'South Korea': 1588.66, 'Australia': 1580.67,
    'Algeria': 1564.26, 'Egypt': 1563.24, 'Canada': 1556.48,
    'Norway': 1550.94, 'Panama': 1540.64, 'Ivory Coast': 1532.98,
    'Sweden': 1514.77, 'Paraguay': 1503.50, 'Czechia': 1501.38,
    'Scotland': 1498.35, 'Tunisia': 1479.04, 'DR Congo': 1478.35,
    'Uzbekistan': 1465.34, 'Qatar': 1454.96, 'Iraq': 1447.14,
    'South Africa': 1429.73, 'Saudi Arabia': 1421.43, 'Jordan': 1391.45,
    'Bosnia': 1385.84, 'Cape Verde': 1366.13, 'Ghana': 1346.31,
    'Curacao': 1294.65, 'Haiti': 1291.71, 'New Zealand': 1281.57,
}


def fifa_to_elo(fifa_pts):
    """FIFA积分转Elo近似值"""
    return fifa_pts - 300


# ============================================================
# 第2层: 阵容/伤病调整 (2026年5月最新)
# 来源: 多来源交叉验证
# 正值=球队削弱, 负值=球队增强
# ============================================================
SQUAD_ADJUSTMENTS = {
    # --- 重大伤病 ---
    'France': -25,       # Ekitike(跟腱断裂,0.68xG/90)+Camavinga被弃, Mbappe打假9号不熟悉
    'Brazil': -30,       # Rodrygo(伤,核心创造者)+Militão(腿筋手术)+Neymar状态存疑
    'Germany': -15,      # Gnabry(内收肌撕裂,8/10预选赛首发)+Adeyemi被弃
    'Netherlands': -12,  # Xavi Simons(ACL撕裂,4月)
    'England': -10,      # Foden+Palmer+Maguire+TAA被弃用, 图赫尔大刀阔斧
    'Portugal': -5,      # Mateus Fernandes被弃, 但阵容深度仍强

    # --- 阵容增强/稳定 ---
    'Spain': +15,        # 无关键球员损失, 受益于对手伤病
    'Argentina': +8,     # 阵容稳定, 美洲杯冠军班底
    'Morocco': +12,      # 最大积分增长(+19.3), 非洲杯表现强势
    'Sweden': +8,        # 最大排名跃升(+4位,+27.64分)

    # --- 预选赛表现调整 ---
    'Switzerland': -8,   # 预选赛磕磕绊绊
    'Croatia': -8,       # 黄金一代老化, Modric 40岁
    'Belgium': -10,      # 黄金一代退场, 新老交替
    'Uruguay': -5,       # Suarez退役, 新锋线未验证

    # --- 新军/黑马 ---
    'Uzbekistan': +8,    # 首次世界杯, 预选赛表现出色
    'Curacao': +5,       # 首次世界杯, 荷甲球员班底
    'Cape Verde': +5,    # 首次世界杯
}


# ============================================================
# 第3层: 历史世界杯 Elo (时间衰减)
# 半衰期=4年, 2022世界杯距今3.5年
# decay = 0.5^(3.5/4) ≈ 0.545
# ============================================================
DECAY_FACTOR = 0.5 ** (3.5 / 4)  # ≈ 0.545


def load_historical_elo():
    if os.path.exists(ELO_FILE):
        with open(ELO_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def compute_hybrid_elo():
    """计算48队混合Elo"""
    hist_elo = load_historical_elo()
    hybrid = {}

    for team, fifa_pts in sorted(FIFA_RANKINGS_2026_05.items()):
        # 第1层: FIFA → Elo (35%)
        fifa_e = fifa_to_elo(fifa_pts)

        # 第2层: 历史世界杯Elo, 时间衰减 (30%)
        hist_e = hist_elo.get(team, fifa_e)  # 无历史→用FIFA兜底
        hist_e_decayed = 1500 + (hist_e - 1500) * DECAY_FACTOR

        # 第3层: 阵容调整 (35%)
        squad_adj = SQUAD_ADJUSTMENTS.get(team, 0)

        # 混合公式
        blended = 0.35 * fifa_e + 0.30 * hist_e_decayed + 0.35 * (fifa_e + squad_adj)

        hybrid[team] = round(blended)

    return hybrid


# ============================================================
# 世界杯分组 (与原worldcup_prep.py保持一致)
# ============================================================
WC_GROUPS = {
    'A': ['Mexico', 'South Africa', 'South Korea', 'Czech Republic'],
    'B': ['Canada', 'Bosnia', 'Qatar', 'Switzerland'],
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


def print_hybrid_report():
    """打印完整混合评级报告"""
    hybrid = compute_hybrid_elo()
    hist_elo = load_historical_elo()

    print('=' * 70)
    print('  2026世界杯 48队混合评级 (历史Elo + FIFA + 人员变动)')
    print('  时间衰减系数: %.3f | 阵容调整: 伤病/状态/预选赛' % DECAY_FACTOR)
    print('=' * 70)

    # 按混合Elo排序
    ranked = sorted(hybrid.items(), key=lambda x: -x[1])

    print()
    print('  🏆 夺冠热门 Top 10:')
    for i, (team, elo) in enumerate(ranked[:10]):
        fifa_pts = FIFA_RANKINGS_2026_05.get(team, 0)
        hist_e = hist_elo.get(team, '---')
        adj = SQUAD_ADJUSTMENTS.get(team, 0)
        adj_str = ('%+d' % adj) if adj else '  0'
        print('    %2d. %-20s 混合Elo:%-5d  FIFA:%-6.0f  历史Elo:%-5s  阵容:%s' % (
            i+1, team, elo, fifa_pts, str(hist_e), adj_str))

    # 按小组展示
    print()
    print('=' * 70)
    print('  小组赛预览 (按混合Elo排名)')
    print('=' * 70)

    group_winners = {}
    group_runners_up = {}

    for grp, teams in sorted(WC_GROUPS.items()):
        print()
        print('  Group %s:' % grp)
        ranked_grp = sorted(teams, key=lambda t: -hybrid.get(t, 1400))
        for i, t in enumerate(ranked_grp):
            e = hybrid.get(t, 1400)
            hist = hist_elo.get(t)
            adj = SQUAD_ADJUSTMENTS.get(t, 0)
            flag = '★' if i < 2 else ' '
            hist_str = ' 历史:%d' % hist if hist else ''
            adj_str = ' 阵容%+d' % adj if adj else ''
            print('    %s %-20s 混合Elo:%d%s%s' % (flag, t, e, hist_str, adj_str))
        group_winners[grp] = ranked_grp[0]
        group_runners_up[grp] = ranked_grp[1]

    # 淘汰赛预估
    print()
    print('=' * 70)
    print('  淘汰赛16强预估 (各组前二)')
    print('=' * 70)
    for grp in sorted(WC_GROUPS.keys()):
        print('    Group %s: %s / %s' % (grp, group_winners[grp], group_runners_up[grp]))

    # 四强预测
    print()
    print('  按混合Elo排序的八强:')
    all_16 = list(group_winners.values()) + list(group_runners_up.values())
    top8 = sorted(set(all_16), key=lambda t: -hybrid.get(t, 1400))[:8]
    for i, t in enumerate(top8):
        print('    %d. %s (Elo:%d)' % (i+1, t, hybrid.get(t, 1400)))

    return hybrid


if __name__ == '__main__':
    import sys
    sys.stdout.reconfigure(encoding='utf-8')

    hybrid = print_hybrid_report()

    # 保存
    with open(HYBRID_FILE, 'w', encoding='utf-8') as f:
        json.dump(hybrid, f, ensure_ascii=False, indent=2)
    print()
    print('  已保存到: %s' % HYBRID_FILE)
    print('=' * 70)
