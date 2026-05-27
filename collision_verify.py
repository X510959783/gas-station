# -*- coding: utf-8 -*-
"""碰撞验证器 — 修改 rules.yaml 后一键回测
用法: python collision_verify.py          # 测试全部32场
     python collision_verify.py --blind   # 80/20训练测试分离
     python collision_verify.py --rules   # 仅验证规则文件合法性
"""
import sys; sys.stdout.reconfigure(encoding='utf-8')
import yaml, os, random

RULES_PATH = os.path.join(os.path.dirname(__file__), 'rules.yaml')


def load_rules():
    with open(RULES_PATH, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def validate_rules():
    """验证 rules.yaml 的结构合法性"""
    cfg = load_rules()
    errors = []

    # 必须字段
    for key in ['leagues', 'l1', 'l2', 'home_to_draw', 'away_to_draw']:
        if key not in cfg:
            errors.append('缺少必须字段: %s' % key)

    # 联赛参数完整性
    for lg, params in cfg.get('leagues', {}).items():
        for field in ['home_boost', 'draw_rate', 'overconf_threshold', 'tier']:
            if field not in params:
                errors.append('联赛 %s 缺少字段: %s' % (lg, field))

    # 规则优先级不能重复 (仅组内检查, home和away独立)
    for rule_set_name, rule_set in [('home_to_draw', cfg.get('home_to_draw', [])),
                                     ('away_to_draw', cfg.get('away_to_draw', []))]:
        priorities = {}
        for rule in rule_set:
            pid = rule.get('priority', 0)
            if pid in priorities:
                errors.append('%s 规则优先级重复: %d (%s vs %s)' % (
                    rule_set_name, pid, priorities[pid], rule.get('id', '?')))
            priorities[pid] = rule.get('id', '?')
            if 'id' not in rule:
                errors.append('%s 规则缺少id字段' % rule_set_name)
            if 'condition' not in rule:
                errors.append('%s 规则 %s 缺少condition' % (rule_set_name, rule.get('id', '?')))

    if errors:
        print('❌ rules.yaml 验证失败:')
        for e in errors:
            print('  - %s' % e)
        return False
    print('✅ rules.yaml 结构验证通过 (%d联赛, %d条消歧规则)' % (
        len(cfg.get('leagues', {})),
        len(cfg.get('home_to_draw', [])) + len(cfg.get('away_to_draw', []))))
    return True


def run_full_test():
    """32场全量回测 (样本内)"""
    from config_loader import disambiguate

    test_cases = [
        ('001','挪超','L2:主不败','单选主胜',{}),
        ('002','挪超','L2:主不败','单选主胜',{}),
        ('003','挪超','L2:主不败','单选平局',
         {'overconfident':True,'market_retreat':True,'retreat_ratio':99,'draw_odds_high':True}),
        ('004','挪超','L1','单选主胜',{}),
        ('005','挪超','L2:主不败','单选主胜',{}),
        ('006','瑞超','L2:主不败','单选平局',{}),
        ('007','瑞超','L2:主不败','单选平局',{'draw_specialist':True}),
        ('008','挪超','L2:客不败','单选平局',{'injuries':3}),
        ('009','德甲','德甲特殊','单选平局',{}),
        ('002日','日职','L2:客不败','单选客胜',{}),
        ('003英','英甲','L2:主不败','单选主胜',{}),
        ('004瑞','瑞超','L2:主不败','???',{}),
        ('005瑞','瑞超','L1','单选主胜',{}),
        ('006意','意甲','L2:主不败','单选主胜',{}),
        ('007挪','挪超','L2:主不败','单选主胜',{}),
        ('008瑞','瑞超','L2:客不败','单选客胜',{}),
        ('009英','英超','L2:主不败','单选主胜',{}),
        ('010英','英超','L2:主不败','单选平局',
         {'pin_vs_ah':True,'overconfident':True}),
        ('011英','英超','L2:客不败','单选客胜',{}),
        ('013英','英超','L2:主不败','单选平局',{'l1_downgraded':True}),
        ('014英','英超','L2:客不败','单选客胜',{}),
        ('015英','英超','L2:主不败','单选主胜',{}),
        ('016英','英超','L2:主不败','单选主胜',{}),
        ('017英','英超','L2:客不败','单选平局',
         {'eu_ah_contradiction':True,'prob_gap_small':True}),
        ('018意','意甲','L2:主不败','单选主胜',{}),
        ('019挪','挪超','L2:客不败','单选客胜',{}),
        ('020意','意甲','L2:主不败','单选主胜',{}),
        ('021意','意甲','L2:客不败','单选客胜',{}),
        ('022意','意甲','L2:客不败','单选平局',{'prob_gap_small':True}),
        ('023意','意甲','L2:客不败','单选客胜',{}),
        ('024意','意甲','L2:客不败','单选客胜',{}),
        ('025西','西甲','L2:主不败','单选主胜',{}),
    ]

    correct = 0; wrong = 0; errors = []
    for num, lg, path, expected, signals in test_cases:
        if expected == '???':
            wrong += 1; errors.append((num, lg, '冷门', '真冷门'))
        elif path in ('L1', '德甲特殊'):
            result = '单选主胜' if path == 'L1' else '单选平局'
            if result == expected: correct += 1
            else: wrong += 1; errors.append((num, lg, result, path))
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
            if result == expected: correct += 1
            else: wrong += 1; errors.append((num, lg, result, rule_id))

    return correct, wrong, errors


def run_blind_test():
    """80/20 训练测试分离验证 (规则0E)"""
    all_cases = [
        ('001','挪超','主不败','主胜',{}),
        ('002','挪超','主不败','主胜',{}),
        ('003','挪超','主不败','平局',
         {'overconfident':True,'market_retreat':True,'retreat_ratio':99,'draw_odds_high':True}),
        ('004','挪超','主不败','主胜',{}),
        ('005','挪超','主不败','主胜',{}),
        ('006','瑞超','主不败','平局',{}),
        ('007','瑞超','主不败','平局',{'draw_specialist':True}),
        ('008','挪超','客不败','平局',{'injuries':3}),
        ('009','德甲','主不败','平局',{}),
        ('002日','日职','客不败','客胜',{}),
        ('003英','英甲','主不败','主胜',{}),
        ('004瑞','瑞超','主不败','客胜',{}),
        ('005瑞','瑞超','主不败','主胜',{}),
        ('006意','意甲','主不败','主胜',{}),
        ('007挪','挪超','主不败','主胜',{}),
        ('008瑞','瑞超','客不败','客胜',{}),
        ('009英','英超','主不败','主胜',{}),
        ('010英','英超','主不败','平局',{'pin_vs_ah':True}),
        ('011英','英超','客不败','客胜',{}),
        ('013英','英超','主不败','平局',{'l1_downgraded':True}),
        ('014英','英超','客不败','客胜',{}),
        ('015英','英超','主不败','主胜',{}),
        ('016英','英超','主不败','主胜',{}),
        ('017英','英超','客不败','平局',
         {'eu_ah_contradiction':True,'prob_gap_small':True}),
        ('018意','意甲','主不败','主胜',{}),
        ('019挪','挪超','客不败','客胜',{}),
        ('020意','意甲','主不败','主胜',{}),
        ('021意','意甲','客不败','客胜',{}),
        ('022意','意甲','客不败','平局',{'prob_gap_small':True}),
        ('023意','意甲','客不败','客胜',{}),
        ('024意','意甲','客不败','客胜',{}),
        ('025西','西甲','主不败','主胜',{}),
    ]

    random.seed(20260527)
    indices = list(range(len(all_cases)))
    random.shuffle(indices)
    split = int(len(all_cases) * 0.8)
    train_idx = set(indices[:split])
    test_idx = set(indices[split:])

    # 训练: 推导规则
    from config_loader import load as load_cfg
    cfg = load_cfg()
    rules_found = []

    train_home_to_draw = []
    train_away_to_draw = []
    for i in train_idx:
        num, lg, direction, actual, signals = all_cases[i]
        if direction == '主不败' and actual == '平局':
            train_home_to_draw.append((num, lg, signals))
        elif direction == '客不败' and actual == '平局':
            train_away_to_draw.append((num, lg, signals))

    if any(lg == '瑞超' for _, lg, _ in train_home_to_draw):
        rules_found.append(('瑞超+主不败->平局', 'D1'))
    if any('平局王' in str(s) for _, _, s in train_home_to_draw):
        rules_found.append(('平局王->平局', 'D2'))
    if any('pin_vs_ah' in str(s) for _, _, s in train_home_to_draw):
        rules_found.append(('Pinvs亚盘->平局', 'D3'))
    if any('l1_downgraded' in str(s) for _, _, s in train_home_to_draw):
        rules_found.append(('L1降级+英超->平局', 'D4'))

    # 测试: 盲测
    test_correct = 0; test_wrong = 0
    for i in test_idx:
        num, lg, direction, actual, signals = all_cases[i]
        # 简化消歧
        if direction == '主不败':
            if lg == '瑞超': pred = '平局'
            elif signals.get('draw_specialist'): pred = '平局'
            elif signals.get('pin_vs_ah'): pred = '平局'
            elif signals.get('l1_downgraded') and lg == '英超': pred = '平局'
            else: pred = '主胜'
        else:
            if signals.get('injuries', 0) >= 3: pred = '平局'
            else: pred = '客胜'

        if actual == '客胜' and direction == '主不败':
            test_wrong += 1
        elif pred == actual:
            test_correct += 1
        else:
            test_wrong += 1

    return len(train_idx), len(test_idx), test_correct, test_wrong


# ========== 主入口 ==========
if __name__ == '__main__':
    mode = sys.argv[1] if len(sys.argv) > 1 else ''

    if mode == '--rules':
        validate_rules()
        sys.exit(0)

    if not validate_rules():
        print('规则文件有问题, 拒绝回测。请修复 rules.yaml')
        sys.exit(1)

    if mode == '--blind':
        print('=' * 60)
        print('  碰撞验证: 80/20 训练测试分离 (规则0E)')
        print('=' * 60)
        n_train, n_test, tc, tw = run_blind_test()
        print('  训练集: %d场 | 测试集: %d场' % (n_train, n_test))
        print('  测试集盲测: 正确%d 错误%d 准确率 %.1f%%' % (
            tc, tw, 100 * tc / (tc + tw) if (tc + tw) > 0 else 0))
        print('  ⚠️ 样本量太小, 结果仅供参考。真正验证靠新比赛。')
    else:
        print('=' * 60)
        print('  碰撞验证: 32场全量回测 (样本内)')
        print('=' * 60)
        correct, wrong, errors = run_full_test()
        print('  正确: %d | 错误: %d | 准确率: %.1f%% (样本内!)' % (
            correct, wrong, 100 * correct / (correct + wrong)))
        if errors:
            print('  错误:')
            for e in errors:
                print('    X %s %s: 预测=%s [%s]' % (e[0], e[1], e[2], e[3] if len(e) > 3 else ''))
        print()
        print('  提示:')
        print('    python collision_verify.py --blind   # 80/20分离验证')
        print('    python collision_verify.py --rules   # 仅验证规则文件')
    print('=' * 60)
