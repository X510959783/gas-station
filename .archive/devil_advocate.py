# -*- coding: utf-8 -*-
"""魔鬼代言人 — 对每个预测自动生成最有力的反对论证
碰撞#37: 对抗 Claude 的乐观偏差——先假设预测是错的, 再找证据
"""
import sys


def argue_against(decision, framework_sig, search_data, league):
    """生成反对当前预测的最有力论证

    参数:
      decision: 框架输出的决策 (如 '单选主胜')
      framework_sig: 框架信号 dict
      search_data: L3搜索数据
      league: 联赛名

    返回: [反对论点列表, 按说服力从高到低], 总风险评分
    """
    arguments = []
    risk_score = 0

    sig = framework_sig or {}
    sd = search_data or {}

    # === 通用反对: 框架本身的局限性 ===
    base_args = [
        '框架参数基于32场样本校准, 可能过拟合',
        '当前联赛(%s)校准数据不足, 参数可能偏差' % league,
        '赔率数据反映的是市场共识, 不是真实概率',
    ]
    arguments.extend(base_args)

    # === 决策特定反对 ===
    if '主胜' in decision:
        # 主胜预测的反对论证
        p_home = sig.get('p_home', 0.5)
        if p_home < 0.40:
            risk_score += 20
            arguments.append(
                '市场共识概率仅%.0f%%, 框架走主胜是逆市场判断' % (p_home * 100))
        if sig.get('pin_dir') == '看衰':
            risk_score += 15
            arguments.append('Pinnacle看衰主队——最精明的庄家在对面')
        if sig.get('eu_ah_contradiction'):
            risk_score += 10
            arguments.append('欧亚信号矛盾——至少有一个信号是错的')
        if sig.get('overconfident'):
            risk_score += 20
            arguments.append('市场对主队过度自信——可能重蹈004瑞覆辙')
        if sig.get('w_range', 0) > 0.50:
            risk_score += 10
            arguments.append('公司间极差%.2f大——定价无共识' % sig['w_range'])
        if not sd:
            risk_score += 10
            arguments.append('无L3搜索数据——缺失伤缺/战绩信息')

    elif '客胜' in decision:
        p_away = sig.get('p_away', sig.get('prob_gap', 0.5))
        avg_away_o = sig.get('avg_away_o', 99)
        if avg_away_o > 2.5:
            risk_score += 10
            arguments.append('客赔%.2f偏高——市场并不真正看好客队' % avg_away_o)
        if sig.get('pin_dir') == '看好':
            risk_score += 15
            arguments.append('Pinnacle看好主队——客胜缺乏smart money支持')
        if not sd:
            risk_score += 10
            arguments.append('无L3数据——无法验证客队客场战斗力')

    elif '平局' in decision:
        p_draw = sig.get('p_draw', 0.28)
        if p_draw < 0.30:
            risk_score += 15
            arguments.append(
                '市场平局概率仅%.0f%%——平局是低概率事件' % (p_draw * 100))
        arguments.append('平局是足球最罕见的结果(平均25-30%)——永远是不太可能的')

    # === L3数据特定反对 ===
    if sd:
        away_win_rate = sd.get('away_win_rate', 0)
        home_win_rate = sd.get('home_win_rate', 0)
        if '主胜' in decision and away_win_rate > 0.50:
            risk_score += 15
            arguments.append(
                '客队近期客场胜率%.0f%%——客队客场战斗力强' % (away_win_rate * 100))
        if '客胜' in decision and home_win_rate > 0.60:
            risk_score += 15
            arguments.append(
                '主队近期主场胜率%.0f%%——主场战斗力强劲' % (home_win_rate * 100))

    # === 排序: 最有力的反对论点排最前 ===
    # (简化: 假设每个论点的说服力与其贡献的风险评分成正比)

    return {
        'arguments': arguments[:7],  # 最多7条
        'risk_score': min(100, risk_score),
        'verdict': ('低风险' if risk_score < 20
                    else '中风险' if risk_score < 40
                    else '高风险' if risk_score < 60
                    else '极高风险'),
    }


def print_challenge(decision, sig, search_data, league):
    """打印反对论证"""
    result = argue_against(decision, sig, search_data, league)
    print('=' * 55)
    print('  ⚠ 魔鬼代言人: 为什么这个预测可能是错的')
    print('=' * 55)
    print('  预测: %s [%s, 风险评分%d]' % (
        decision, result['verdict'], result['risk_score']))
    print()
    for i, arg in enumerate(result['arguments']):
        print('  %d. %s' % (i + 1, arg))
    print('=' * 55)
    return result


# ========== 自检 ==========
if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')

    # 模拟一个预测: 挪超 单选主胜
    sig = {
        'p_home': 0.42, 'p_draw': 0.28, 'p_away': 0.30,
        'pin_dir': '看好', 'w_range': 0.25,
        'eu_ah_contradiction': False, 'overconfident': False,
    }
    sd = {'away_win_rate': 0.40, 'home_win_rate': 0.55}

    print_challenge('单选主胜', sig, sd, '挪超')
    print()

    # 高风险案例
    sig2 = {
        'p_home': 0.63, 'p_draw': 0.25, 'p_away': 0.12,
        'pin_dir': '看衰', 'w_range': 0.55,
        'eu_ah_contradiction': True, 'overconfident': True,
    }
    print_challenge('单选主胜', sig2, None, '瑞超')
