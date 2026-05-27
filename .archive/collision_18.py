"""碰撞 #18: v2.2 完整框架——亚盘纳入L1"""
import sys; sys.stdout.reconfigure(encoding='utf-8')
import os, re, parse_odds
from probability_engine import oo_epc_convert, correct_fl_bias

base = r'C:\Users\51095\Desktop\足彩'

def extract_ah(num):
    folder = None
    for d in os.listdir(base):
        full = os.path.join(base, d)
        if os.path.isdir(full) and num in d: folder = full; break
    if not folder: return 0, 0
    ah_file = None
    for f in os.listdir(folder):
        if '亚盘对比' in f and f.endswith('.html'):
            ah_file = os.path.join(folder, f); break
    if not ah_file: return 0, 0
    with open(ah_file, 'r', encoding='gb2312', errors='replace') as fh:
        html = fh.read()
    rows = re.findall(r'<tr[^>]*>.*?</tr>', html, re.DOTALL)
    hcp_vals = []
    hcp_map = {
        '平手':0,'平手/半球':0.25,'半球':0.5,'半球/一球':0.75,'一球':1.0,
        '一球/球半':1.25,'球半':1.5,'受平手':0,'受平手/半球':-0.25,'受半球':-0.5,
        '受半球/一球':-0.75,'受一球':-1.0,'受一球/球半':-1.25,'受球半':-1.5,
        '平半':0.25,'半一':0.75,'受平半':-0.25,'受半一':-0.75,'平打':0,
    }
    for row in rows[1:]:
        tds = re.findall(r'<td[^>]*>(.*?)</td>', row)
        if len(tds) >= 4:
            hcp_raw = re.sub(r'<[^>]+>', '', tds[2]).strip().replace('&nbsp;',' ')
            for key, val in hcp_map.items():
                if key in hcp_raw: hcp_vals.append(val); break
    if not hcp_vals: return 0, 0
    return sum(hcp_vals)/len(hcp_vals), max(hcp_vals)-min(hcp_vals)

actuals = {'001':'主胜','002':'主胜','003':'平局','004':'主胜','005':'主胜',
           '006':'平局','007':'平局','008':'平局','009':'平局'}

print('碰撞 #18: v2.2完整框架——亚盘纳入L1(欧亚一致=第四条件)')
print('='*72)
print(f'{"场次":<6}{"实际":<6}{"极差":<7}{"概率差":<8}{"主胜":<7}{"亚盘":<8}{"欧亚一致":<10}{"L1":<10}{"预测":<16}{"结果":<6}')
print('-'*72)

correct = 0; wrong = 0
for num in ['001','002','003','004','005','006','007','008','009']:
    folder = None
    for d in os.listdir(base):
        full = os.path.join(base, d)
        if os.path.isdir(full) and num in d: folder = full; break
    if not folder: continue
    data = parse_odds.parse_folder(folder)
    euro = data['euro_odds']['companies']
    companies = list(euro.values())

    pin = None
    for seq, c in euro.items():
        if 'Pi' in c.get('name',''): pin = c; break

    all_iw = [c['odds']['instant'][0] for c in companies[:30] if c['odds']['instant'][0] > 0]
    odds_list = [(c['odds']['instant'][0], c['odds']['instant'][1], c['odds']['instant'][2])
                 for c in companies[:30] if len(c.get('odds',{}).get('instant',[])) >= 3]
    probs = oo_epc_convert(odds_list) if odds_list else {'home':0.33,'draw':0.34,'away':0.33}
    p_home = correct_fl_bias(probs['home'])
    p_away = correct_fl_bias(probs['away'])

    w_range = max(all_iw) - min(all_iw) if len(all_iw) > 1 else 0
    prob_gap = abs(p_home - p_away)

    pin_dir = '?'
    if pin:
        pi = pin['odds']['instant'][0]; pn = pin['odds']['init'][0]
        if pi < pn - 0.02: pin_dir = '看好'
        elif pi > pn + 0.02: pin_dir = '看衰'
        else: pin_dir = '稳定'

    ah_avg, ah_range = extract_ah(num)
    if ah_avg > 0.05: ah_dir = '看好'
    elif ah_avg < -0.05: ah_dir = '看衰'
    else: ah_dir = '中性'

    actual = actuals[num]
    eu_ah_agree = (pin_dir == ah_dir) or (pin_dir == '稳定') or (ah_dir == '中性')

    c1 = w_range < 0.50
    c2 = prob_gap > 0.05
    c3 = p_home < 0.55
    c4 = eu_ah_agree
    l1_ok = c1 and c2 and c3 and c4

    if l1_ok:
        predict = '主胜方向' if pin_dir == '看好' else '非主胜方向'
        ok = (predict == '主胜方向' and actual == '主胜') or (predict == '非主胜方向' and actual != '主胜')
        if ok: correct += 1; res = '✓'
        else: wrong += 1; res = '✗'
    else:
        predict = 'L2'; res = '—'

    fails = []
    if not c1: fails.append('极差')
    if not c2: fails.append('概率差')
    if not c3: fails.append('过度自信')
    if not c4: fails.append('欧亚矛盾')
    fail_str = ','.join(fails) if fails else 'OK'

    print(f'{num:<6}{actual:<6}{w_range:<7.2f}{prob_gap:<8.1%}{p_home:<7.1%}'
          f'{ah_dir:<8}{"✓" if c4 else "✗":<10}'
          f'{"✓" if l1_ok else fail_str:<10}{predict:<16}{res:<6}')

print(f'\nL1激活准确率: {correct}/{correct+wrong}')
if correct+wrong > 0:
    print(f'欧亚矛盾场次(需L2): {sum(1 for n in ["001"-"009"] if False)}')
