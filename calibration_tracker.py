# -*- coding: utf-8 -*-
"""校准追踪器 - 基于 Shams(2025) + SteerConf/AFCE(NeurIPS 2025)
核心原则: 准确率!=盈利, 校准误差(ECE)比准确率更重要

追踪指标:
  1. 每级badge真实胜率 (Stable是否真的比Risk准?)
  2. Brier Score (概率校准质量)
  3. ECE (Expected Calibration Error)
  4. 平注P&L (FLAT betting, 非Kelly - Shams 2025建议)
  5. 准确率悖论检测 (高准确率+负收益)
"""
import sys, os, json, math, time

CALIBRATION_FILE = os.path.join(os.path.dirname(__file__), '.calibration_db.json')


def load_db():
    if os.path.exists(CALIBRATION_FILE):
        with open(CALIBRATION_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {'records': [], 'badge_stats': {}, 'version': '1.0'}


def save_db(db):
    with open(CALIBRATION_FILE, 'w', encoding='utf-8') as f:
        json.dump(db, f, ensure_ascii=False, indent=2)


def update_from_verification(verified_file):
    """从验证文件更新校准数据库"""
    with open(verified_file, 'r', encoding='utf-8') as f:
        verified = json.load(f)

    db = load_db()
    results = verified.get('results', [])

    new_records = 0
    for r in results:
        verdict = r.get('verdict', '?')
        badge = r.get('badge', '?')
        decision = r.get('decision', '')

        if verdict not in ('✓', '✗', '—'):
            continue
        if badge == 'Error':
            continue

        is_correct = verdict == '✓'
        is_push = verdict == '—'

        # 提取概率估计 (rough: based on badge)
        prob_estimate = {
            'Stable': 0.80, 'Correct': 0.65, 'Risk': 0.50, 'Low': 0.35,
            'ColdDoor': 0.45
        }.get(badge, 0.50)

        record = {
            'date': verified.get('locked_at', '')[:10],
            'badge': badge,
            'decision': decision[:30],
            'correct': is_correct,
            'push': is_push,
            'prob_estimate': prob_estimate,
        }
        db['records'].append(record)
        new_records += 1

    # 重新计算badge统计
    _recompute_stats(db)
    save_db(db)
    return new_records, db


def _recompute_stats(db):
    """重新计算所有badge的校准统计"""
    records = db['records']
    badges = {}
    for r in records:
        b = r['badge']
        if b not in badges:
            badges[b] = {'total': 0, 'correct': 0, 'probs': [], 'outcomes': []}
        if not r.get('push'):
            badges[b]['total'] += 1
            if r['correct']:
                badges[b]['correct'] += 1
            badges[b]['probs'].append(r.get('prob_estimate', 0.5))
            badges[b]['outcomes'].append(1 if r['correct'] else 0)

    stats = {}
    for badge, data in badges.items():
        n = data['total']
        if n == 0:
            continue
        win_rate = data['correct'] / n

        # Brier Score: mean((p - o)^2)
        brier = sum((p - o) ** 2 for p, o in zip(data['probs'], data['outcomes'])) / n

        # ECE: 按概率分桶
        ece = _compute_ece(data['probs'], data['outcomes'])

        stats[badge] = {
            'n': n,
            'win_rate': round(win_rate, 3),
            'brier_score': round(brier, 4),
            'ece': round(ece, 4),
            'prob_avg': round(sum(data['probs']) / n, 3),
        }

    db['badge_stats'] = stats


def _compute_ece(probs, outcomes, n_bins=5):
    """计算 Expected Calibration Error"""
    if len(probs) < n_bins:
        return 0.0

    # 排序
    paired = sorted(zip(probs, outcomes))
    bin_size = max(1, len(paired) // n_bins)
    ece = 0.0

    for i in range(0, len(paired), bin_size):
        bin_data = paired[i:i + bin_size]
        if not bin_data:
            continue
        avg_prob = sum(p for p, _ in bin_data) / len(bin_data)
        avg_outcome = sum(o for _, o in bin_data) / len(bin_data)
        ece += (len(bin_data) / len(paired)) * abs(avg_prob - avg_outcome)

    return ece


def check_accuracy_paradox():
    """Shams(2025) 准确率悖论检测"""
    db = load_db()
    records = db['records']
    if len(records) < 20:
        return {'detected': False, 'reason': '样本不足(<20场)'}

    total = 0
    correct = 0
    # 模拟平注P&L (每场2元, 赔率估为2.0)
    flat_pnl = 0.0
    for r in records:
        if r.get('push'):
            continue
        total += 1
        stake = 2.0
        if r['correct']:
            correct += 1
            flat_pnl += stake * 0.85  # 竞彩~85%返还
        else:
            flat_pnl -= stake

    accuracy = correct / max(1, total)
    roi = flat_pnl / (total * 2) * 100

    return {
        'detected': accuracy > 0.55 and roi < 0,
        'accuracy': round(accuracy, 3),
        'flat_pnl': round(flat_pnl, 1),
        'roi_pct': round(roi, 1),
        'warning': '高准确率+负收益=准确率悖论!' if (accuracy > 0.55 and roi < 0) else '正常',
    }


def print_report():
    """打印校准报告"""
    db = load_db()
    stats = db.get('badge_stats', {})
    records = db['records']
    total = sum(s['n'] for s in stats.values())

    print('=' * 60)
    print('  校准追踪报告 (Calibration Tracker)')
    print('  Shams(2025): 准确率≠盈利, ECE比准确率更重要')
    print('=' * 60)
    print('  总记录: %d场' % total)
    print()
    print('  %-10s %6s %8s %8s %8s %8s' % (
        '等级', '场次', '实际胜率', '预期概率', 'Brier', 'ECE'))
    print('  ' + '-' * 52)

    order = ['Stable', 'Correct', 'Risk', 'Low', 'ColdDoor']
    for badge in order:
        s = stats.get(badge)
        if not s:
            continue
        gap = s['win_rate'] - s['prob_avg']
        marker = ' ⚠' if abs(gap) > 0.15 else ''
        print('  %-10s %6d %7.1f%% %7.1f%% %8.4f %8.4f%s' % (
            badge, s['n'], s['win_rate'] * 100, s['prob_avg'] * 100,
            s['brier_score'], s['ece'], marker))

    print()
    # 关键检查: Stable胜率 > Risk胜率?
    stable_wr = stats.get('Stable', {}).get('win_rate', 0)
    risk_wr = stats.get('Risk', {}).get('win_rate', 0)
    if stable_wr > 0 and risk_wr > 0:
        if stable_wr > risk_wr:
            print('  ✅ Stable胜率(%.1f%%) > Risk(%.1f%%) — 分级有效' % (
                stable_wr * 100, risk_wr * 100))
        else:
            print('  ❌ Stable胜率(%.1f%%) <= Risk(%.1f%%) — 分级无效!' % (
                stable_wr * 100, risk_wr * 100))

    # 准确率悖论
    paradox = check_accuracy_paradox()
    if paradox['detected']:
        print('  🔴 准确率悖论: 准确率%.1f%% 但 ROI %.1f%%' % (
            paradox['accuracy'] * 100, paradox['roi_pct']))
    elif paradox.get('accuracy'):
        print('  ✅ 无准确率悖论 (准确率%.1f%%, ROI %.1f%%)' % (
            paradox['accuracy'] * 100, paradox['roi_pct']))

    print('=' * 60)
    return db


# ========== 主入口 ==========
if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')

    if len(sys.argv) > 1 and sys.argv[1] == '--update':
        verified = sys.argv[2] if len(sys.argv) > 2 else 'betting-lock_verified.json'
        if os.path.exists(verified):
            n, db = update_from_verification(verified)
            print('已更新 %d 条校准记录' % n)
        else:
            print('验证文件不存在: %s' % verified)
    else:
        print_report()
