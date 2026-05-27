"""碰撞实验: 001 vs 002"""
import sys; sys.stdout.reconfigure(encoding='utf-8')
import os, parse_odds
from probability_engine import oo_epc_convert, correct_fl_bias

base = r'C:\Users\51095\Desktop\足彩'

def extract(num):
    folder = None
    for d in os.listdir(base):
        full = os.path.join(base, d)
        if os.path.isdir(full) and num in d: folder = full; break
    if not folder: return None
    data = parse_odds.parse_folder(folder)
    euro = data['euro_odds']['companies']
    companies = list(euro.values())
    jc = None
    for k, v in euro.items():
        if '竞' in v.get('name', ''): jc = v; break
    if not jc: jc = companies[0]
    pin = None
    for seq, c in euro.items():
        if 'Pi' in c.get('name', ''): pin = c; break
    all_iw = [c['odds']['instant'][0] for c in companies[:30] if c['odds']['instant'][0] > 0]
    all_iw_init = [c['odds']['init'][0] for c in companies[:30] if c['odds']['init'][0] > 0]
    up = sum(1 for i in range(min(len(all_iw), len(all_iw_init))) if all_iw[i] > all_iw_init[i] + 0.02)
    down = sum(1 for i in range(min(len(all_iw), len(all_iw_init))) if all_iw[i] < all_iw_init[i] - 0.02)
    odds_list = [(c['odds']['instant'][0], c['odds']['instant'][1], c['odds']['instant'][2])
                 for c in companies[:30] if len(c.get('odds',{}).get('instant',[])) >= 3 and c['odds']['instant'][0] > 0]
    probs = oo_epc_convert(odds_list)
    changes = []
    for i in range(min(len(all_iw), len(all_iw_init))):
        if all_iw_init[i] > 0: changes.append((all_iw[i] - all_iw_init[i]) / all_iw_init[i])
    kelly_data = [c.get('kelly',{}).get('instant',[0,0,0]) for c in companies[:30]]
    return {
        'avg_w': sum(all_iw)/len(all_iw),
        'w_range': max(all_iw) - min(all_iw),
        'up': up, 'down': down, 'stable': len(all_iw)-up-down,
        'avg_change': sum(changes)/len(changes) if changes else 0,
        'jc_init': jc['odds']['init'], 'jc_inst': jc['odds']['instant'],
        'pin_init': pin['odds']['init'][0] if pin else 0,
        'pin_inst': pin['odds']['instant'][0] if pin else 0,
        'pin_move': (pin['odds']['instant'][0] - pin['odds']['init'][0]) if pin else 0,
        'probs': (correct_fl_bias(probs['home']), correct_fl_bias(probs['draw']), correct_fl_bias(probs['away'])),
        'overround': probs['overround'],
        'k_hi': sum(1 for k in kelly_data if k[0] > 1.0),
        'k_lo': sum(1 for k in kelly_data if k[0] < 0.85),
    }

r1, r2 = extract('001'), extract('002')

print('碰撞实验 #1: 001 斯达2-0 vs 002 汉坎2-0')
print('相同: 挪超/主场/2-0/市场看衰主队')
print('核心: 为什么001的信号方向对，002全错？')
print()
print(f'{"指标":<25} {"001斯达":>12} {"002汉坎":>12} {"差异":>10}')
print('-'*62)
print(f'{"百家均赔主胜":<25} {r1["avg_w"]:>12.2f} {r2["avg_w"]:>12.2f} {r2["avg_w"]-r1["avg_w"]:>+10.2f}')
print(f'{"极差":<25} {r1["w_range"]:>12.2f} {r2["w_range"]:>12.2f} {r2["w_range"]-r1["w_range"]:>+10.2f}')
print(f'{"升/降/稳":<25} {r1["up"]}/{r1["down"]}/{r1["stable"]:>8} {r2["up"]}/{r2["down"]}/{r2["stable"]:>8}')
print(f'{"平均变化幅度":<25} {r1["avg_change"]:>+11.2%} {r2["avg_change"]:>+11.2%}')
print(f'{"Pinnacle初→终":<25} {r1["pin_init"]:.2f}→{r1["pin_inst"]:.2f} {r2["pin_init"]:.2f}→{r2["pin_inst"]:.2f}')
print(f'{"Pinnacle方向":<25} {"↓看好主队":>12} {"↑看衰主队":>12} {"相反!!!":>10}')
print(f'{"OO-EPC主/平/客":<25} {r1["probs"][0]:.1%}/{r1["probs"][1]:.1%}/{r1["probs"][2]:.1%} {r2["probs"][0]:.1%}/{r2["probs"][1]:.1%}/{r2["probs"][2]:.1%}')
print(f'{"K>1.0/K<0.85":<25} {r1["k_hi"]}/{r1["k_lo"]:>12} {r2["k_hi"]}/{r2["k_lo"]:>12}')

print(f'''
╔══════════════════════════════════════════════════════════════╗
║ 碰撞追问: Pinnacle在002为什么错了？                        ║
╚══════════════════════════════════════════════════════════════╝

Pinnacle 001: {r1["pin_init"]:.2f}→{r1["pin_inst"]:.2f} (降{r1["pin_init"]-r1["pin_inst"]:.2f}) → 看好 → 主队赢 ✓
Pinnacle 002: {r2["pin_init"]:.2f}→{r2["pin_inst"]:.2f} (升{r2["pin_inst"]-r2["pin_init"]:.2f}) → 看衰 → 主队赢 ✗

关键线索: 002极差0.91是9场最大。27家公司升赔，仅2家降赔。
这不是"Pinnacle看错了"——这是整个市场在集体逃离主队。

为什么？因为利勒斯特罗姆排名第3、客场防守极强(5场仅失3球)。
市场在用排名和客场防守数据定价——汉坎排名低，不配当热门。

但汉坎主场4胜1负。市场没有充分计入这个数据。

碰撞结论:
  001分歧中等(0.54)，Pinnacle的方向代表信息优势 → 正确
  002分歧极大(0.91)，Pinnacle的方向代表资金流逃离 → 错误
  → Pinnacle不是预言家，是资金流探测器
  → 分歧越大，Pinnacle的信号越不可靠
  → 分歧最大的比赛，反而是模型最可能出错的地方
  → 也是价值最大的地方——因为所有人都在逃离，价格被压到最低

修正: Pinnacle仅在极差<0.50时作为方向信号。
      极差>0.50时，Pinnacle的方向可能是反向指标。
      极差越大，越应该考虑"市场集体错误"的可能性。
''')
