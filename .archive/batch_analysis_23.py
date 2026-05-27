"""批量分析23场新比赛——框架v3.4零样本迁移测试"""
import sys; sys.stdout.reconfigure(encoding='utf-8')
import os, re
sys.path.insert(0, os.path.dirname(__file__))
from framework_v3 import analyze_match

base = r'D:\足彩\2026.5.24'
folders = sorted(os.listdir(base))

# 联赛映射 + 默认参数
league_map = {
    '日职': '日职', '英甲': '英甲', '瑞超': '瑞超', '意甲': '意甲',
    '挪超': '挪超', '英超': '英超', '西甲': '西甲'
}

# 结果提取: 从文件夹名解析实际比分
def parse_result(fname):
    # 模式: "哈马比 1.2 索尔纳" → 主队1-2客队 → 客胜
    # 模式: "博尔顿 4.1 斯托克港" → 主队4-1 → 主胜
    # 模式: "利物浦 1.1 布伦特" → 1-1 → 平局
    scores = re.findall(r'\b(\d+)\.(\d+)\b', fname)
    if scores:
        home_goals = int(scores[-1][0])
        away_goals = int(scores[-1][1])
        if home_goals > away_goals: return '主胜'
        elif home_goals == away_goals: return '平局'
        else: return '客胜'
    return '?'

def get_league(fname):
    for key in league_map:
        if key in fname: return league_map[key]
    return '其他'

# 预设已知联赛数据(web搜索可获取)
# 英超: 主场优势~15%, 平局率~26%
# 意甲: 主场优势~12%, 平局率~28%
# 西甲: 主场优势~15%, 平局率~25%
# 日职: 主场优势~10%, 平局率~27%
# 英甲: 主场优势~15%, 平局率~27%
# 已注入到framework_v3的LEAGUE_PARAMS或使用默认

print('=' * 75)
print('  批量分析 23 场新比赛 — 框架 v3.4 零样本迁移')
print('  已知联赛: 挪超+瑞超+德甲 | 新联赛: 日职+英甲+意甲+英超+西甲')
print('=' * 75)

results = []
for f in folders:
    full = os.path.join(base, f)
    if not os.path.isdir(full): continue

    lg = get_league(f)
    actual = parse_result(f)

    try:
        result = analyze_match(full, lg)
    except Exception as e:
        results.append((f[:50], lg, actual, 'ERROR', str(e)[:30], '—'))
        continue

    d = result['decision']
    pt = result.get('pick_type', '?')
    layers = '→'.join(result['layers'])

    # 判断对错
    if ('单选主胜' in d and actual == '主胜') or ('单选平局' in d and actual == '平局') or ('单选非主胜' in d and actual == '客胜'):
        ok = '✓'
    elif '双选主不败' in d and actual in ['主胜','平局']:
        ok = '✓'
    elif '双选客不败' in d and actual in ['客胜','平局']:
        ok = '✓'
    elif '跳过' in d:
        ok = '—'
    else:
        ok = '✗'

    results.append((f[:50], lg, actual, pt, d[:40], ok, layers))

# 输出
singles = 0; doubles = 0; skips = 0; correct = 0; wrong = 0
print(f'\n{"场次":<6}{"联赛":<6}{"实际":<6}{"类型":<6}{"决策":<42}{"结果":<6}')
print('─'*75)
for r in results:
    name, lg, actual, pt, decision, ok, layers = r
    if 'ERROR' in pt:
        print(f'  {name[:40]:<40} {lg} ❌{decision}')
        continue
    if pt == '单选': singles += 1
    elif pt == '双选': doubles += 1
    else: skips += 1
    if ok == '✓': correct += 1
    elif ok == '✗': wrong += 1
    # 简化展示
    short_name = name.split('周日')[-1][:35] if '周日' in name else name[:35]
    print(f'  {short_name:<40} {lg:<6} {actual:<6} {pt:<6} {decision:<42} {ok:<6}')

total = len([r for r in results if 'ERROR' not in r[3]])
print(f'\n{"─"*75}')
print(f'  总计: {total}场 | 单选{singles} | 双选{doubles} | 跳过{skips}')
print(f'  正确: {correct} | 错误: {wrong} | 跳过: {skips}')
if correct + wrong > 0:
    print(f'  准确率: {correct}/{correct+wrong} ({100*correct//(correct+wrong)}%)')
print(f'{"="*75}')
