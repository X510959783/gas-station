# -*- coding: utf-8 -*-
"""影子投注组合 — 追踪虚拟P&L, 让我面对预测的真实后果
碰撞#37: 对抗"无皮肤在游戏里"的漏洞——每个预测都有虚拟资金后果

用法:
  python shadow_portfolio.py --init 1000     # 初始化1000元虚拟资金
  python shadow_portfolio.py --bet <lock_file>  # 根据预测锁定投注
  python shadow_portfolio.py --settle <verified_file>  # 赛后结算
  python shadow_portfolio.py --report        # 查看组合报告
"""
import sys, os, json, time

PORTFOLIO_FILE = os.path.join(os.path.dirname(__file__), '.shadow_portfolio.json')


def init_portfolio(bankroll=1000):
    """初始化虚拟资金"""
    portfolio = {
        'created_at': time.strftime('%Y-%m-%d %H:%M:%S'),
        'initial_bankroll': bankroll,
        'current_bankroll': bankroll,
        'total_bets': 0,
        'total_won': 0,
        'total_lost': 0,
        'total_pushes': 0,
        'total_staked': 0,
        'total_returned': 0,
        'roi': 0.0,
        'max_drawdown': 0.0,
        'peak_bankroll': bankroll,
        'history': [],
    }
    save_portfolio(portfolio)
    print('虚拟资金初始化: %.2f元' % bankroll)
    return portfolio


def load_portfolio():
    if os.path.exists(PORTFOLIO_FILE):
        with open(PORTFOLIO_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return init_portfolio()


def save_portfolio(pf):
    with open(PORTFOLIO_FILE, 'w', encoding='utf-8') as f:
        json.dump(pf, f, ensure_ascii=False, indent=2)


def place_bets(lock_file, stake_per_bet=2):
    """根据预测文件下注: 每场单选2元"""
    with open(lock_file, 'r', encoding='utf-8') as f:
        lock = json.load(f)

    pf = load_portfolio()
    bets = []

    for pred in lock.get('predictions', []):
        if pred.get('pick_type') != '单选':
            continue
        decision = pred.get('decision', '')
        if '冷门预警' in decision:
            continue  # 冷门预警不投

        # 确定投注方向
        if '主胜' in decision:
            bet_on = '主胜'
        elif '客胜' in decision:
            bet_on = '客胜'
        elif '平局' in decision:
            bet_on = '平局'
        else:
            continue

        stake = stake_per_bet
        if pf['current_bankroll'] < stake:
            print('资金不足! 当前余额: %.2f' % pf['current_bankroll'])
            break

        pf['current_bankroll'] -= stake
        pf['total_staked'] += stake
        pf['total_bets'] += 1

        bet = {
            'date': time.strftime('%Y-%m-%d'),
            'match': pred.get('match', '')[:40],
            'league': pred.get('league', ''),
            'bet_on': bet_on,
            'stake': stake,
            'odds_estimate': 2.0,  # 竞彩参考赔率(后续可从jc_odds获取)
            'prediction': decision,
            'badge': pred.get('badge', '?'),
            'settled': False,
        }
        bets.append(bet)

    # 追加到历史
    pf['history'].extend(bets)
    save_portfolio(pf)

    if bets:
        print('已下注 %d 场, 共 %.2f元 (余额: %.2f)' % (
            len(bets), len(bets) * stake_per_bet, pf['current_bankroll']))
    else:
        print('无有效投注')
    return pf


def settle_bets(verified_file):
    """赛后结算: 根据验证文件判定输赢"""
    with open(verified_file, 'r', encoding='utf-8') as f:
        verified = json.load(f)

    pf = load_portfolio()
    results = verified.get('results', [])

    settled_count = 0
    for bet in pf['history']:
        if bet.get('settled'):
            continue

        # 匹配验证结果
        for r in results:
            if (r.get('match', '')[:30] == bet.get('match', '')[:30]
                    and r.get('verdict') in ('✓', '✗', '—')):
                actual = r.get('actual', '?')
                verdict = r.get('verdict', '?')

                # 结算逻辑
                if verdict == '✓':
                    # 假设竞彩赔率2.0, 简化计算
                    win_amount = bet['stake'] * bet.get('odds_estimate', 2.0)
                    pf['current_bankroll'] += win_amount
                    pf['total_won'] += 1
                    pf['total_returned'] += win_amount
                    bet['result'] = 'won'
                    bet['return'] = win_amount
                elif verdict == '✗':
                    pf['total_lost'] += 1
                    bet['result'] = 'lost'
                    bet['return'] = 0
                else:
                    pf['total_pushes'] += 1
                    pf['current_bankroll'] += bet['stake']  # 退还本金
                    bet['result'] = 'push'
                    bet['return'] = bet['stake']

                bet['settled'] = True
                bet['actual'] = actual
                settled_count += 1
                break

    # 更新统计
    total_invested = pf['initial_bankroll'] + pf['total_returned'] - pf['total_staked']
    if pf['initial_bankroll'] > 0:
        pf['roi'] = round(
            (pf['current_bankroll'] - pf['initial_bankroll'])
            / pf['initial_bankroll'] * 100, 1)
    if pf['current_bankroll'] > pf['peak_bankroll']:
        pf['peak_bankroll'] = pf['current_bankroll']
    dd = (pf['peak_bankroll'] - pf['current_bankroll']) / max(1, pf['peak_bankroll'])
    pf['max_drawdown'] = round(max(pf['max_drawdown'], dd) * 100, 1)

    save_portfolio(pf)
    print('已结算 %d 场 (%d赢/%d输/%d走)' % (
        settled_count, pf['total_won'], pf['total_lost'], pf['total_pushes']))


def print_report():
    """打印组合报告"""
    pf = load_portfolio()
    print('=' * 45)
    print('  影子投注组合 — 虚拟P&L报告')
    print('=' * 45)
    print('  初始资金: %.2f元' % pf['initial_bankroll'])
    print('  当前余额: %.2f元' % pf['current_bankroll'])
    print('  P&L: %+.2f元 (%.1f%%)' % (
        pf['current_bankroll'] - pf['initial_bankroll'], pf['roi']))
    print('  总投注: %d场, %.2f元' % (pf['total_bets'], pf['total_staked']))
    print('  胜/负/走: %d/%d/%d' % (
        pf['total_won'], pf['total_lost'], pf['total_pushes']))
    if pf['total_won'] + pf['total_lost'] > 0:
        wr = pf['total_won'] / (pf['total_won'] + pf['total_lost']) * 100
        print('  胜率: %.1f%%' % wr)
    print('  最大回撤: %.1f%%' % pf['max_drawdown'])
    print('  高峰余额: %.2f元' % pf['peak_bankroll'])

    # 最近10场
    recent = [h for h in pf['history'] if h.get('settled')][-10:]
    if recent:
        print('\n  最近结算:')
        for b in recent:
            result = b.get('result', '?')
            icon = {'won': '✓', 'lost': '✗', 'push': '—'}.get(result, '?')
            print('    %s %s %s %.2f->%.2f' % (
                icon, b.get('bet_on', '?'),
                b.get('match', '')[:25],
                b['stake'],
                b.get('return', 0)))

    print('=' * 45)


# ========== 主入口 ==========
if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('shadow_portfolio.py --init 1000 | --bet <lock> | --settle <verified> | --report')
        sys.exit(0)

    cmd = sys.argv[1]
    if cmd == '--init':
        amount = float(sys.argv[2]) if len(sys.argv) > 2 else 1000
        init_portfolio(amount)
    elif cmd == '--bet':
        lock = sys.argv[2] if len(sys.argv) > 2 else 'betting-lock.json'
        place_bets(lock)
    elif cmd == '--settle':
        verified = sys.argv[2] if len(sys.argv) > 2 else 'betting-lock_verified.json'
        settle_bets(verified)
    elif cmd == '--report':
        print_report()
    else:
        print('未知命令: %s' % cmd)
