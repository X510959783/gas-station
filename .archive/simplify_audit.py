# -*- coding: utf-8 -*-
"""简化审计器 — 检测过度建设, 强制模块问责
碰撞#37: 对抗"停不下来建东西"的漏洞

规则:
  1. 生产模块上限: 18个 .py文件
  2. 每超过1个, 必须标记1个待归档
  3. 新模块必须回答: 没有它管道能跑吗? 能→不需要
  4. 每次会话结束前自动运行
"""
import sys, os

SCRIPT_DIR = os.path.dirname(__file__)
MAX_MODULES = 18
CORE_MODULES = {
    'rules.yaml', 'config_loader.py',
    'framework_v4.py', 'probability_engine.py', 'parse_odds.py',
    'fetch_500.py', 'lock_predictions.py',
    'auto_pipeline.sh', 'fetch_results.py',
}


def count_production_modules():
    """统计生产级模块数量 (排除临时/调试/归档文件)"""
    py_files = []
    for f in sorted(os.listdir(SCRIPT_DIR)):
        if not f.endswith('.py'):
            continue
        if f.startswith('tmp_') or f.startswith('.'):
            continue
        path = os.path.join(SCRIPT_DIR, f)
        if not os.path.isfile(path):
            continue
        py_files.append(f)
    return py_files


def audit():
    """运行审计"""
    modules = count_production_modules()
    n = len(modules)

    print('模块审计: %d个.py文件 (上限%d)' % (n, MAX_MODULES))
    print()

    # 分类
    core = [m for m in modules if m in CORE_MODULES]
    support = [m for m in modules if m not in CORE_MODULES]

    print('核心模块 (%d):' % len(core))
    for m in core:
        print('  ✓ %s' % m)

    print()
    print('支撑模块 (%d):' % len(support))
    for m in support:
        justification = get_justification(m)
        print('  ? %s — %s' % (m, justification))

    print()
    if n > MAX_MODULES:
        excess = n - MAX_MODULES
        print('⚠ 超限%d个模块! 请归档最不重要的%d个:' % (excess, excess))
        # 建议归档
        candidates = suggest_archive(modules)
        for c in candidates[:excess]:
            print('  建议归档: %s' % c)
    elif n > MAX_MODULES - 3:
        print('⚡ 接近上限: %d/%d' % (n, MAX_MODULES))
    else:
        print('✅ 模块数健康: %d/%d' % (n, MAX_MODULES))

    return n <= MAX_MODULES


def get_justification(module_name):
    """每个模块必须能解释自己为什么存在"""
    justifications = {
        'auto_search.py': 'L3数据自主抓取(500.com球队页面)',
        'search_intel.py': '搜索查询生成(备用)',
        'l3_search_bridge.py': 'L3搜索缓存桥接',
        'cold_door_detector.py': '过度自信冷门防御',
        'poisson_crosscheck.py': 'Rule 0B三路径验证(第二路径)',
        'devil_advocate.py': '魔鬼代言人(对抗乐观偏差)',
        'shadow_portfolio.py': '影子投注组合(虚拟P&L追踪)',
        'collision_verify.py': '碰撞验证器(YAML修改后回测)',
        'simplify_audit.py': '简化审计器(本模块)',
        'generate_report.py': '分析报告生成(旧)',
        'full_analysis.py': '历史分析脚本(旧)',
        'match_db.py': '比赛数据库管理(旧)',
        'parse_rangqiu.py': '让球指数解析(旧)',
        'prematch_scanner.py': '赛前扫描器(旧)',
        'self_check.py': '自检脚本(旧)',
        'verify_checklist.py': '验证清单(旧)',
        'convert-to-wikilinks.py': '工具脚本(旧)',
    }
    return justifications.get(module_name, '未记录用途!')


def suggest_archive(modules):
    """建议归档的候选"""
    # 标记为"旧"的优先归档
    candidates = []
    for m in modules:
        justification = get_justification(m)
        if '(旧)' in justification:
            candidates.append(m)
    # 加上非核心非新模块
    for m in modules:
        if m not in CORE_MODULES and m not in candidates:
            if m not in ('auto_search.py', 'cold_door_detector.py',
                         'poisson_crosscheck.py', 'devil_advocate.py',
                         'shadow_portfolio.py', 'collision_verify.py',
                         'l3_search_bridge.py', 'search_intel.py'):
                candidates.append(m)
    return candidates


# ========== 主入口 ==========
if __name__ == '__main__':
    ok = audit()
    print()
    if not ok:
        print('🔴 审计不通过——请归档多余模块后重试')
    sys.exit(0 if ok else 1)
