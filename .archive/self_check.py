"""强制执行的自查脚本 — 跑不过不许汇报"""
import sys; sys.stdout.reconfigure(encoding='utf-8')
import os, json, subprocess

PASS, FAIL = 0, 0

def check(name, condition, detail=""):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  [PASS] {name}")
    else:
        FAIL += 1
        print(f"  [FAIL] {name} — {detail}")

print("=" * 50)
print("系统自查")
print("=" * 50)

# 1. 必备文件
print("\n1. 必备文件")
required_files = {
    '全量分析': 'd:/gas-station/full_analysis.py',
    '数据解析': 'd:/gas-station/parse_odds.py',
    '验证门禁': 'd:/gas-station/verify_checklist.py',
    '数据库模块': 'd:/gas-station/match_db.py',
    '数据库文件': 'd:/gas-station/match-db.json',
    '问题追踪': 'd:/gas-station/issues-tracker.md',
    '六维框架': 'd:/gas-station/.claude/evolution/football-framework-v2.md',
    '公司档案': 'd:/gas-station/.claude/evolution/company-profiles.md',
    '检查清单': 'd:/gas-station/.claude/evolution/analysis-checklist.md',
    '校准追踪': 'd:/gas-station/.claude/evolution/calibration.md',
    '审计报告': 'd:/gas-station/.claude/evolution/framework-audit-report.md',
    '实战工作流': 'd:/gas-station/.claude/evolution/combat-workflow.md',
    '比赛数据库文档': 'd:/gas-station/.claude/evolution/match-database.md',
}
for name, path in required_files.items():
    check(name, os.path.exists(path), f"文件不存在: {path}")

# 2. 代码可执行
print("\n2. 代码可执行")
for mod in ['parse_odds','match_db']:
    r = subprocess.run(['python3','-c',f'import {mod}'], capture_output=True, text=True)
    check(f"import {mod}", r.returncode == 0, r.stderr[:100])

# 3. 代码与框架一致性
print("\n3. 代码-框架一致")
with open('d:/gas-station/full_analysis.py','r',encoding='utf-8') as f: code = f.read()
with open('d:/gas-station/.claude/evolution/football-framework-v2.md','r',encoding='utf-8') as f: fw = f.read()

checks = [
    ('D5 K>1.1阈值', 'k_hi_11' in code and '1.1' in fw),
    ('D2 水位幅度', 'water_jump' in code and '水位幅度' in fw),
    ('D2 时间分段', 'time_segments' in code and '时间分段' in fw),
    ('D4 欧亚交叉', 'eur_asia_conflict' in code and '欧亚交叉' in fw),
    ('D6 |gap|>0.20', 'abs(gap) > 0.20' in code and '0.20' in fw),
]
for name, cond in checks:
    check(name, cond)

# 4. 检查清单铁律
print("\n4. 检查清单铁律")
with open('d:/gas-station/.claude/evolution/analysis-checklist.md','r',encoding='utf-8') as f: cl = f.read()
iron_rules = {
    '禁止heredoc': '禁止 heredoc' in cl,
    '禁止说庄家错了': '禁止说"庄家错了"' in cl,
    '数据一致性优先': '数据一致性优先于固定规则' in cl,
    '知识积累': '知识持续积累' in cl,
    '命令前自查': '任何命令执行前必须自查' in cl,
    '每日思维进化': '每日思维进化' in cl,
}
total_iron = len(iron_rules)
present = sum(1 for v in iron_rules.values() if v)
for name, present_flag in iron_rules.items():
    check(name, present_flag, "铁律缺失")

# 5. 记忆规则
print("\n5. 记忆规则")
mem = r'C:\Users\51095\.claude\projects\d--gas-station\memory'
if os.path.exists(mem):
    rules = os.listdir(mem)
    core = ['bookmaker_not_wrong','no_shortcuts','data_first','knowledge_evolution',
            'certain_answers','dont_give_up','no_guessing','speak_up','which_page',
            'exact_paths','timetable','self_check','thinking_evolution']
    for r in core:
        check(f"规则:{r}", any(r in f for f in rules), "缺失")

# 6. 数据库
print("\n6. 数据库")
if os.path.exists('d:/gas-station/match-db.json'):
    with open('d:/gas-station/match-db.json','r',encoding='utf-8') as f: db = json.load(f)
    n = len(db.get('matches',[]))
    check(f'比赛数量', n >= 5, f'仅{n}场')
else:
    check('数据库文件', False, '不存在')

# 7. 问题追踪
print("\n7. 问题追踪")
if os.path.exists('d:/gas-station/issues-tracker.md'):
    with open('d:/gas-station/issues-tracker.md','r',encoding='utf-8') as f: it = f.read()
    open_issues = [l for l in it.split('\n') if '进行中' in l and '已解决' not in l]
    check('问题清零', len(open_issues) == 0, f'{len(open_issues)}条进行中')

# ==== 汇总 ====
print(f"\n{'='*50}")
print(f"结果: {PASS}通过 / {FAIL}失败")
if FAIL == 0:
    print("自查通过。可以汇报。")
else:
    print(f"自查未通过！{FAIL}项失败，必须修复后再汇报。")
