# -*- coding: utf-8 -*-
"""碰撞#36: 样本外盲测验证 — 训练/测试分离
规则0E首次执行: 训练集推导规则 -> 测试集一次性盲测
"""
import sys; sys.stdout.reconfigure(encoding='utf-8')
import random

# 32场比赛按实际结果和关键信号编码
# (编号, 联赛, 方向, 实际单选, 信号特征)
all_matches = [
    # 第一批9场
    ('001','挪超','主不败','主胜','pin看好,共识倾向客'),
    ('002','挪超','主不败','主胜','极端极差0.91,L3主场80%'),
    ('003','挪超','主不败','平局','过度自信62%,21升撤退'),
    ('004','挪超','主不败','主胜','L1激活:极差0.25'),
    ('005','挪超','主不败','主胜','势均力敌,主场+20%'),
    ('006','瑞超','主不败','平局','瑞超41%平局,30家降赔'),
    ('007','瑞超','主不败','平局','平局王44%+50%,瑞超'),
    ('008','挪超','客不败','平局','3伤缺,Pin升赔看衰'),
    ('009','德甲','主不败','平局','极差0.75,升降级附加赛'),
    # 第二批23场
    ('002日','日职','客不败','客胜','27家全降极端一致反向'),
    ('003英','英甲','主不败','主胜','欧亚矛盾,信号混乱'),
    ('004瑞','瑞超','主不败','客胜','✗真冷门:主胜1.46客翻盘'),
    ('005瑞','瑞超','主不败','主胜','L1激活:极差0.24'),
    ('006意','意甲','主不败','主胜','极差0.60,L2综合'),
    ('007挪','挪超','主不败','主胜','过度自信71%但真强队'),
    ('008瑞','瑞超','客不败','客胜','欧亚矛盾,瑞超41%'),
    ('009英','英超','主不败','主胜','势均力敌0.8%'),
    ('010英','英超','主不败','平局','Pin看衰vs亚盘看好'),
    ('011英','英超','客不败','客胜','过度自信65%,Pin看衰'),
    ('013英','英超','主不败','平局','L1降级+英超'),
    ('014英','英超','客不败','客胜','客赔1.87明牌'),
    ('015英','英超','主不败','主胜','55.5%<英超65%阈值'),
    ('016英','英超','主不败','主胜','欧亚矛盾泛型'),
    ('017英','英超','客不败','平局','极差0.60+矛盾+低概率'),
    ('018意','意甲','主不败','主胜','过度自信61%+顶级强队'),
    ('019挪','挪超','客不败','客胜','客赔1.50极低'),
    ('020意','意甲','主不败','主胜','L1激活+意甲'),
    ('021意','意甲','客不败','客胜','极差2.00+客强'),
    ('022意','意甲','客不败','平局','尤文客场,都灵德比'),
    ('023意','意甲','客不败','客胜','极差1.65+客强'),
    ('024意','意甲','客不败','客胜','过度自信67%'),
    ('025西','西甲','主不败','主胜','势均力敌强强对话'),
]

# 固定随机种子保证可复现
random.seed(20260527)
indices = list(range(len(all_matches)))
random.shuffle(indices)

# 80/20 分割: 26场训练 + 6场测试
split = int(len(all_matches) * 0.8)
train_idx = set(indices[:split])
test_idx = set(indices[split:])

print('=' * 72)
print('  碰撞#36: 样本外盲测验证 (规则0E首次执行)')
print('  训练集 %d场 | 测试集 %d场 | 80/20分割' % (len(train_idx), len(test_idx)))
print('=' * 72)

# === 阶段1: 只在训练集上推导消歧规则 ===
print('\n【阶段1】仅在训练集上推导规则...\n')

train_matches = [all_matches[i] for i in range(len(all_matches)) if i in train_idx]
test_matches = [all_matches[i] for i in range(len(all_matches)) if i in test_idx]

# 统计训练集中的模式
home_to_draw_train = []
home_to_win_train = []
away_to_draw_train = []
away_to_win_train = []

for num, lg, direction, actual, signals in train_matches:
    if direction == '主不败':
        if actual == '平局': home_to_draw_train.append((num, lg, signals))
        else: home_to_win_train.append((num, lg, signals))
    elif direction == '客不败':
        if actual == '平局': away_to_draw_train.append((num, lg, signals))
        else: away_to_win_train.append((num, lg, signals))

print('训练集 主不败->平局 (%d场):' % len(home_to_draw_train))
for n, lg, sig in home_to_draw_train:
    print('  %s %s: %s' % (n, lg, sig[:50]))

print('\n训练集 主不败->主胜 (%d场):' % len(home_to_win_train))
for n, lg, sig in home_to_win_train:
    print('  %s %s: %s' % (n, lg, sig[:50]))

print('\n训练集 客不败->平局 (%d场):' % len(away_to_draw_train))
for n, lg, sig in away_to_draw_train:
    print('  %s %s: %s' % (n, lg, sig[:50]))

print('\n训练集 客不败->客胜 (%d场):' % len(away_to_win_train))
for n, lg, sig in away_to_win_train:
    print('  %s %s: %s' % (n, lg, sig[:50]))

# 从训练集推导规则
rules_found = []

# 主不败->平局 模式检测
print('\n--- 训练集规则推导 ---')
if any('瑞超' in sig for _, lg, sig in home_to_draw_train):
    rules_found.append('D1:瑞超+主不败->平局')
    print('发现 D1: 瑞超+主不败 -> 平局')
if any('平局王' in sig for _, _, sig in home_to_draw_train):
    rules_found.append('D2:平局王->平局')
    print('发现 D2: 平局王相遇 -> 平局')
if any('Pin看衰vs亚盘看好' in sig or 'Pin vs 亚盘' in sig for _, _, sig in home_to_draw_train):
    rules_found.append('D3:Pinvs亚盘->平局')
    print('发现 D3: Pinvs亚盘明确对立 -> 平局')
if any('L1降级' in sig or ('L1' in sig and '英超' in sig) for _, _, sig in home_to_draw_train):
    rules_found.append('D4:L1降级+英超->平局')
    print('发现 D4: L1降级+英超 -> 平局')
if any('撤退' in sig or '过度自信' in sig for _, _, sig in home_to_draw_train):
    rules_found.append('D5:过度自信+撤退->平局')
    print('发现 D5: 过度自信+全线撤退 -> 平局')
if any('伤缺' in sig or '伤' in sig for _, _, sig in home_to_draw_train + away_to_draw_train):
    rules_found.append('A1/D6:伤缺->平局')
    print('发现 A1/D6: 伤缺>=3 -> 平局')

# 客不败->平局
away_draw_signals = [(n, lg, sig) for n, lg, sig in away_to_draw_train]
if any('德比' in sig or ('意甲' in lg and '势均' in sig) for _, lg, sig in away_draw_signals):
    rules_found.append('A3:意甲德比->平局')
    print('发现 A3: 意甲德比 -> 平局')
if any('矛盾' in sig and '低概率' in sig for _, _, sig in away_draw_signals):
    rules_found.append('A2:矛盾+低概率->平局')
    print('发现 A2: 矛盾+低概率 -> 平局')

print('\n训练集推导的规则: %d条' % len(rules_found))
for r in rules_found:
    print('  -', r)

# === 阶段2: 在测试集上一次性盲测 ===
print('\n' + '=' * 72)
print('【阶段2】测试集盲测 (一次性,不可回头修改规则)')
print('=' * 72)

def blind_predict(num, lg, direction, signals, rules):
    """用训练集规则盲测——不参考测试集结果"""
    if direction == '主不败':
        if any('瑞超' in r and lg == '瑞超' for r in rules):
            return '平局', 'D1:瑞超'
        if any('平局王' in r and '平局王' in signals for r in rules):
            return '平局', 'D2:平局王'
        if any('Pinvs亚盘' in r and ('Pin看衰vs亚盘看好' in signals or 'Pin vs 亚盘' in signals) for r in rules):
            return '平局', 'D3:Pinvs亚盘'
        if any('伤缺' in r and '伤缺' in signals for r in rules):
            return '平局', 'D6:伤缺'
        return '主胜', '默认'
    elif direction == '客不败':
        if any('伤缺' in r and '伤缺' in signals for r in rules):
            return '平局', 'A1:伤缺'
        if any('德比' in r and ('德比' in signals or lg == '意甲') for r in rules):
            return '平局', 'A3:德比'
        return '客胜', '默认'
    return '跳过', '无规则'

test_correct = 0
test_wrong = 0
test_errors = []

print('\n测试集比赛 (结果对框架隐藏):\n')
print('%-8s %-5s %-7s %-12s %-12s %-10s %s' % ('编号', '联赛', '方向', '盲测预测', '实际结果', '判定', '触发规则'))
print('-' * 70)

for num, lg, direction, actual, signals in test_matches:
    pred, rule = blind_predict(num, lg, direction, signals, rules_found)
    ok = 'V' if pred == actual else ('X' if actual != '客胜' or pred == '平局' else 'X')
    # 简化判定: 004瑞实际是客胜, 但我们方向是主不败...
    # 004瑞方向='主不败',实际='客胜'——方向就错了,消歧也救不了
    if actual == '客胜' and direction == '主不败':
        ok = 'X(方向错)'
        test_wrong += 1
        test_errors.append((num, lg, pred, actual, '方向主不败但实际客胜'))
    elif pred == actual:
        ok = 'V'
        test_correct += 1
    else:
        ok = 'X'
        test_wrong += 1
        test_errors.append((num, lg, pred, actual, '消歧错误'))

    print('%-8s %-5s %-7s %-12s %-12s %-10s %s' % (num, lg, direction, pred, actual, ok, rule))

# === 汇总 ===
train_total = len([m for m in train_matches if m[3] != '客胜' or m[2] != '主不败'])
# 简化: 统计训练集上规则正确数
train_correct = 0
train_wrong_count = 0
for num, lg, direction, actual, signals in train_matches:
    pred, rule = blind_predict(num, lg, direction, signals, rules_found)
    if actual == '客胜' and direction == '主不败':
        train_wrong_count += 1  # 004瑞型方向错误
    elif pred == actual:
        train_correct += 1
    else:
        train_wrong_count += 1

print('\n' + '=' * 72)
print('  碰撞#36 验证结果')
print('=' * 72)
print('  训练集 (%d场): 正确%d 错误%d 准确率 %.1f%%' % (
    len(train_matches), train_correct, train_wrong_count,
    100 * train_correct / (train_correct + train_wrong_count) if (train_correct + train_wrong_count) > 0 else 0))
test_total = test_correct + test_wrong
print('  测试集 (%d场): 正确%d 错误%d 准确率 %.1f%%' % (
    len(test_matches), test_correct, test_wrong,
    100 * test_correct / test_total if test_total > 0 else 0))

gap = abs(100 * train_correct / (train_correct + train_wrong_count) - 100 * test_correct / test_total) if test_total > 0 and (train_correct + train_wrong_count) > 0 else 0
print()
if gap > 10:
    print('  ⚠️ 过拟合警告! 训练-测试差距=%.1f%% > 10%%' % gap)
elif gap > 5:
    print('  ⚡ 轻微过拟合: 训练-测试差距=%.1f%%' % gap)
else:
    print('  ✅ 泛化良好: 训练-测试差距=%.1f%%' % gap)

if test_errors:
    print('\n  测试集错误:')
    for e in test_errors:
        print('    %s %s: 预测=%s 实际=%s [%s]' % e)

print()
print('  核心问题: 训练集%d场够推导可靠的消歧规则吗?' % len(train_matches))
print('  回答: 不够。32场总量就不够做严格的样本外验证。')
print('  真正的验证: 下一批新比赛, 截止前盲测, 赛后比对。')
print('=' * 72)
