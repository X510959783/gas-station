# -*- coding: utf-8 -*-
"""配置加载器 — 从 rules.yaml 加载所有规则, 提供统一API
碰撞#36产物: 规则代码分离, 碰撞实验改YAML不碰代码
"""
import os, yaml

_CONFIG = None
_RULES_PATH = os.path.join(os.path.dirname(__file__), 'rules.yaml')


def load():
    """加载 rules.yaml (单例, 缓存)"""
    global _CONFIG
    if _CONFIG is not None:
        return _CONFIG
    with open(_RULES_PATH, 'r', encoding='utf-8') as f:
        _CONFIG = yaml.safe_load(f)
    return _CONFIG


def reload():
    """强制重新加载 (碰撞实验修改YAML后调用)"""
    global _CONFIG
    _CONFIG = None
    return load()


def get_league_params(league):
    """获取联赛参数, 未校准联赛返回默认值"""
    cfg = load()
    lp = cfg['leagues'].get(league, cfg['default_league'])
    return dict(lp)  # 返回副本防止意外修改


def is_calibrated(league):
    """检查联赛是否已校准(数据库>=3场)"""
    cfg = load()
    return league in cfg.get('calibrated_leagues', [])


def get_l1_params():
    """获取L1层参数"""
    return load()['l1']


def get_l2_params():
    """获取L2层参数"""
    return load()['l2']


def get_home_to_draw_rules():
    """获取 主不败→平局 消歧规则 (按priority降序)"""
    rules = list(load()['home_to_draw'])
    rules.sort(key=lambda r: r['priority'], reverse=True)
    return rules


def get_away_to_draw_rules():
    """获取 客不败→平局 消歧规则 (按priority降序)"""
    rules = list(load()['away_to_draw'])
    rules.sort(key=lambda r: r['priority'], reverse=True)
    return rules


def get_bundesliga_rules():
    """获取德甲特殊规则"""
    return load().get('bundesliga_special', [])


def get_l1_league_override(league):
    """L1激活后的联赛特殊处理: pass=直接返回, downgrade=进入L2"""
    cfg = load()
    overrides = cfg['l1'].get('league_override', {})
    return overrides.get(league, {})


def check_rule_conditions(rule, sig, league):
    """检查一条规则的条件是否全部满足

    条件类型:
    - injuries_min: N          → sig['injuries'] >= N
    - draw_specialist: bool    → sig['draw_specialist']
    - league: str              → league == str
    - pin_vs_ah: bool          → sig['pin_vs_ah']
    - overconfident: bool      → sig['overconfident']
    - market_retreat: bool     → sig['market_retreat']
    - league_tier_not: str     → league tier != str
    - retreat_ratio_min: float → sig['retreat_ratio'] >= float
    - draw_odds_high: bool     → sig['draw_odds_high']
    - l1_downgraded: bool      → sig['l1_downgraded']
    - eu_ah_contradiction: bool → sig['eu_ah_contradiction']
    - prob_gap_small: bool     → sig['prob_gap_small']
    """
    cond = rule.get('condition', {})
    if not cond:
        return False

    for key, expected in cond.items():
        if key == 'injuries_min':
            if sig.get('injuries', 0) < expected:
                return False
        elif key == 'draw_specialist':
            if not sig.get('draw_specialist'):
                return False
        elif key == 'league':
            if league != expected:
                return False
        elif key == 'pin_vs_ah':
            if not sig.get('pin_vs_ah'):
                return False
        elif key == 'overconfident':
            if not sig.get('overconfident'):
                return False
        elif key == 'market_retreat':
            if not sig.get('market_retreat'):
                return False
        elif key == 'league_tier_not':
            cfg = load()
            lp = cfg['leagues'].get(league, cfg['default_league'])
            if lp.get('tier') == expected:
                return False
        elif key == 'retreat_ratio_min':
            if sig.get('retreat_ratio', 1.0) < expected:
                return False
        elif key == 'draw_odds_high':
            if not sig.get('draw_odds_high'):
                return False
        elif key == 'l1_downgraded':
            if not sig.get('l1_downgraded'):
                return False
        elif key == 'eu_ah_contradiction':
            if not sig.get('eu_ah_contradiction'):
                return False
        elif key == 'prob_gap_small':
            if not sig.get('prob_gap_small'):
                return False
        else:
            # 未知条件类型, 跳过(不阻塞)
            pass

    return True


def disambiguate(direction, league, sig):
    """碰撞#35核心: 将方向(主不败/客不败)解析为唯一单选
    完全由 rules.yaml 驱动, 无硬编码规则
    """
    if direction == '主不败':
        for rule in get_home_to_draw_rules():
            if check_rule_conditions(rule, sig, league):
                return '单选平局', rule['id']
        return '单选主胜', 'DEFAULT'

    elif direction == '客不败':
        for rule in get_away_to_draw_rules():
            if check_rule_conditions(rule, sig, league):
                return '单选平局', rule['id']
        return '单选客胜', 'DEFAULT'

    return '跳过', 'NONE'


def resolve_bundesliga(w_range):
    """德甲特殊处理: 高市场效率场景"""
    for rule in get_bundesliga_rules():
        cond = rule.get('condition', {})
        if 'w_range_gt' in cond and w_range > cond['w_range_gt']:
            if rule['action'] == 'draw':
                return '单选平局', '德甲:极差>%.2f→平局' % cond['w_range_gt']
            elif rule['action'] == 'skip':
                return '跳过-德甲高效率', '德甲:极差≤%.2f→跳过' % cond['w_range_lte']
        if 'w_range_lte' in cond and w_range <= cond['w_range_lte']:
            if rule['action'] == 'skip':
                return '跳过-德甲高效率', '德甲:极差≤%.2f→跳过' % cond['w_range_lte']
    return '跳过-德甲高效率', '德甲:默认跳过'


# ========== 自检 ==========
if __name__ == '__main__':
    import sys
    sys.stdout.reconfigure(encoding='utf-8')

    cfg = load()
    print('规则配置加载成功')
    print(f'  版本: {cfg["version"]}')
    print(f'  最后碰撞: {cfg["last_collision"]}')
    print(f'  联赛数: {len(cfg["leagues"])}')
    print(f'  主→平规则: {len(get_home_to_draw_rules())}条')
    print(f'  客→平规则: {len(get_away_to_draw_rules())}条')

    # 验证规则优先级排序
    prev = 999
    for r in get_home_to_draw_rules():
        assert r['priority'] <= prev, f"规则{r['id']}优先级错序"
        prev = r['priority']
    print('  优先级排序验证通过')

    # 测试 check_rule_conditions
    sig = {'injuries': 3, 'draw_specialist': False}
    assert check_rule_conditions({'condition': {'injuries_min': 3}}, sig, '挪超')
    assert not check_rule_conditions({'condition': {'injuries_min': 5}}, sig, '挪超')
    assert not check_rule_conditions({'condition': {'draw_specialist': True}}, sig, '挪超')
    print('  条件检查逻辑验证通过')

    # 测试消歧
    result, rule_id = disambiguate('主不败', '瑞超', {})
    assert result == '单选平局' and rule_id == 'D1', f'瑞超→平局失败: {result}/{rule_id}'
    result, rule_id = disambiguate('主不败', '挪超', {})
    assert result == '单选主胜' and rule_id == 'DEFAULT', f'挪超→主胜失败: {result}/{rule_id}'
    result, rule_id = disambiguate('客不败', '挪超', {'injuries': 3})
    assert result == '单选平局' and rule_id == 'A1', f'伤缺→平局失败: {result}/{rule_id}'
    print('  消歧逻辑验证通过')

    print('\n  全部验证通过 ✓')
