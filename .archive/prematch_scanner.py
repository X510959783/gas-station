"""
赛前扫描器 — 拖入比赛文件夹→自动三层分析→输出2串1建议
用法: python3 prematch_scanner.py <文件夹路径> <联赛>
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from framework_v3 import analyze_match

if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    if len(sys.argv) < 2:
        print("用法: python3 prematch_scanner.py <文件夹路径> [联赛:挪超/瑞超/德甲]")
        print("示例: python3 prematch_scanner.py 'C:/Users/51095/Desktop/足彩/周一010挪超...' 挪超")
        sys.exit(1)

    folder = sys.argv[1]
    league = sys.argv[2] if len(sys.argv) > 2 else '挪超'

    if not os.path.isdir(folder):
        print(f'❌ 文件夹不存在: {folder}')
        sys.exit(1)

    print('=' * 60)
    print('  赛前扫描 — 园中园足彩框架 v3.4')
    print(f'  比赛: {os.path.basename(folder)}')
    print(f'  联赛: {league}')
    print('=' * 60)

    result = analyze_match(folder, league)

    print(f'\n  层级: {"→".join(result["layers"])}')
    print(f'  决策: {result["decision"]}')
    print(f'  类型: {result.get("pick_type", "?")}')

    print(f'\n  推理链:')
    for t in result.get('thought_chain', []):
        print(f'    {t}')

    pt = result.get('pick_type', '?')
    if pt == '单选':
        print(f'\n  💰 成本2元 — 可组2串1单选组合')
    elif pt == '双选':
        print(f'\n  ⚠️  成本4元 — 建议与单选场次配对(1单选+1双选)')
    else:
        print(f'\n  🚫 建议跳过')

    print(f'\n{"="*60}')
