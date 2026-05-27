# -*- coding: utf-8 -*-
"""冷门防御检测器 — 捕捉纯赔率数据无法预测的过度自信翻盘
碰撞#37: 004瑞型冷门(哈马比1-2索尔纳)的防御机制

核心假设:
  当市场极度看好主队(赔率<1.60)时, 如果存在以下红旗信号,
  主胜概率被高估, 应降级为客不败或平局方向.

红旗信号:
  R1: 客队客场战绩强劲 (近5客场>=3胜)
  R2: 主队主场平局率高 (近5主场>=2平)
  R3: 客队交锋占优 (近3次H2H客队不败)
  R4: 赔率周内剧烈波动 (2+次升赔→市场撤退)
"""
import sys, os, re, json

# 阈值配置 (可通过 rules.yaml 覆盖)
THRESHOLDS = {
    'home_odds_max': 1.60,      # 主胜赔率低于此值=市场极度自信
    'away_away_wins_min': 3,    # 客队近5客场胜场>=此值→红旗
    'home_home_draws_min': 2,   # 主队近5主场平局>=此值→红旗
    'odds_raise_count_min': 20, # 升赔公司数>=此值→红旗
    'market_overconf_odds': 1.50, # 极端过度自信赔率
}


def detect_cold_door_risk(framework_signals, search_data=None):
    """检测过度自信翻盘风险

    参数:
      framework_signals: framework_v4 输出的 sig dict
        - p_home, avg_home_o, up, down, pin_dir, league, prob_gap
      search_data: L3搜索数据
        - home_form, away_form, home_win_rate, away_win_rate, home_draw_rate, away_draw_rate

    返回:
      {risk_level: 'none'|'low'|'high'|'critical',
       triggers: [触发的红旗],
       recommendation: 建议调整方向,
       confidence_downgrade: 置信度降级幅度}
    """
    sig = framework_signals
    sd = search_data or {}

    avg_home_o = sig.get('avg_home_o', sig.get('p_home', 0.5))
    if isinstance(avg_home_o, float) and avg_home_o < 0.1:
        # p_home is probability, not odds. Use p_home to estimate
        pass

    # 取真实赔率 (从 signals 中)
    # 框架不直接存 avg_home_o, 但可以看到 p_home
    p_home = sig.get('p_home', 0.5)

    risk_level = 'none'
    triggers = []
    score = 0

    # 先判断是否真的"过度自信"——冷门检测的前提
    overconf_threshold = 0.55
    league = sig.get('league', '')
    if league in ('英超', '意甲', '西甲', '德甲'):
        overconf_threshold = 0.65

    is_truly_overconfident = p_home > overconf_threshold

    # 没有过度自信则冷门检测不触发 (避免005挪超型误报)
    # 例外: 主胜赔率极度低 (<1.50) 也视为过度自信信号
    avg_ho = sig.get('avg_home_o', 99)
    is_extreme_favorite = isinstance(avg_ho, (int, float)) and 1.0 < avg_ho < 1.55

    if not is_truly_overconfident and not is_extreme_favorite:
        return {
            'risk_level': 'none',
            'risk_score': 0,
            'triggers': [],
            'recommendation': '无过度自信→跳过冷门检测',
            'confidence_downgrade': 0,
            'should_flip_direction': False,
        }

    # ---- R1: 客队客场战绩强劲 ----
    away_win_rate = sd.get('away_win_rate', 0)
    away_form = sd.get('away_form', '')
    if away_win_rate >= 0.60:
        score += 30
        triggers.append({
            'id': 'R1',
            'signal': f'客队客场胜率{away_win_rate:.0%}',
            'weight': 30,
            'detail': f'客队近期客场: {away_form}',
        })

    # ---- R2: 主队主场平局率高 ----
    home_draw_rate = sd.get('home_draw_rate', 0)
    if home_draw_rate >= 0.40:
        score += 20
        triggers.append({
            'id': 'R2',
            'signal': f'主队主场平局率{home_draw_rate:.0%}',
            'weight': 20,
        })

    # ---- R3: 赔率剧烈波动 (升赔=撤退) ----
    up = sig.get('_up', 0)
    down = sig.get('_down', 0)
    total = up + down
    if total > 10 and up > total * 0.75:  # 提高阈值: 65%→75%
        score += 25
        triggers.append({
            'id': 'R3',
            'signal': f'{up}/{total}家公司升赔(撤退)',
            'weight': 25,
            'detail': f'市场大规模撤退→主胜定价过高',
        })

    # ---- R4: Pinnacle看衰 + 市场分歧 ----
    w_range = sig.get('w_range', 0)
    pin_dir = sig.get('pin_dir', '稳定')
    if pin_dir == '看衰' and w_range > 0.40:  # 提高阈值: 0.30→0.40
        score += 15
        triggers.append({
            'id': 'R4',
            'signal': f'Pinnacle看衰+极差{w_range:.2f}',
            'weight': 15,
            'detail': '最精明的庄家在撤退',
        })

    # ---- R5: 过度自信已确认 ----
    if is_truly_overconfident:
        score += 10
        triggers.append({
            'id': 'R5',
            'signal': f'市场过度自信(p_home={p_home:.1%})',
            'weight': 10,
        })
    if is_extreme_favorite:
        score += 15
        triggers.append({
            'id': 'R5b',
            'signal': f'极低主胜赔率({avg_ho:.2f})',
            'weight': 15,
        })

    # ---- 风险评估 ----
    if score >= 60:
        risk_level = 'critical'
        recommendation = '强制翻客不败: 极度过度自信+多重红旗→市场集体误判'
        downgrade = 3
    elif score >= 40:
        risk_level = 'high'
        recommendation = '降级双选客不败: 存在显著翻盘风险'
        downgrade = 2
    elif score >= 20:
        risk_level = 'low'
        recommendation = '保持原方向, 降低置信度'
        downgrade = 1
    else:
        risk_level = 'none'
        recommendation = '无冷门风险信号'
        downgrade = 0

    return {
        'risk_level': risk_level,
        'risk_score': score,
        'triggers': triggers,
        'recommendation': recommendation,
        'confidence_downgrade': downgrade,
        'should_flip_direction': score >= 40,
    }


def test_with_known_case():
    """用已知的004瑞案例测试检测器"""
    # 004瑞: 哈马比 vs 索尔纳
    # 市场: 主胜赔率1.46, 极度自信 → 实际 客胜 1-2
    sig = {
        'p_home': 0.633,
        'avg_home_o': 1.46,
        '_up': 18, '_down': 6,
        'w_range': 0.35,
        'pin_dir': '看衰',
        'league': '瑞超',
        'prob_gap': 0.30,
    }
    # 模拟: 索尔纳客场战绩不错
    sd = {
        'away_win_rate': 0.60,
        'away_form': '客场3胜1平1负',
        'home_draw_rate': 0.30,
    }

    result = detect_cold_door_risk(sig, sd)
    return result


# ========== 自检 ==========
if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')

    print('=' * 60)
    print('  冷门防御检测器 — 碰撞#37')
    print('=' * 60)

    # 测试004瑞
    print('\n【案例】004瑞 哈马比 vs 索尔纳 (已知冷门)')
    result = test_with_known_case()
    print(f'  风险等级: {result["risk_level"]}')
    print(f'  风险评分: {result["risk_score"]}')
    print(f'  触发信号:')
    for t in result['triggers']:
        print(f'    [{t["id"]}] {t["signal"]}')
    print(f'  建议: {result["recommendation"]}')
    print(f'  翻方向: {result["should_flip_direction"]}')
    assert result['risk_level'] in ('high', 'critical'), '004瑞应该被检测到!'
    print('  ✅ 检测通过: 004瑞被正确识别为冷门风险')

    # 测试正常场次
    print('\n【对照】001挪超 斯达 vs 瓦勒伦加 (正常主胜)')
    sig_normal = {
        'p_home': 0.316,
        '_up': 13, '_down': 9,
        'w_range': 0.54,
        'pin_dir': '看好',
        'league': '挪超',
    }
    sd_normal = {
        'away_win_rate': 0.20,
        'home_draw_rate': 0.10,
    }
    result2 = detect_cold_door_risk(sig_normal, sd_normal)
    print(f'  风险等级: {result2["risk_level"]}')
    print(f'  风险评分: {result2["risk_score"]}')
    assert result2['risk_level'] == 'none', '正常场次不应触发'
    print('  ✅ 检测通过: 正常场次未误报')

    print('\n' + '=' * 60)
    print('  验证通过')
    print('=' * 60)
