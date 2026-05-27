"""从历史数据库计算赛前战绩+H2H特征, 并测试混合策略"""
import sys, os, re, json, math
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(__file__))
from elo_engine import get_elo_signal
import parse_odds
from probability_engine import oo_epc_convert, correct_fl_bias

base = r'D:/足彩'
all_matches = []

print('收集比赛数据...')
for date_dir in sorted(os.listdir(base)):
    date_path = os.path.join(base, date_dir)
    if not os.path.isdir(date_path): continue
    for folder in sorted(os.listdir(date_path)):
        folder_path = os.path.join(date_path, folder)
        if not os.path.isdir(folder_path): continue
        mf = os.path.join(folder_path, 'match_info.json')
        if not os.path.exists(mf): continue
        with open(mf, 'r', encoding='utf-8') as f:
            meta = json.load(f)
        score = meta.get('score', '')
        if not score: continue
        parts = score.split('-')
        if len(parts) != 2: continue
        try: hg, ag = int(parts[0]), int(parts[1])
        except: continue
        actual = 'H' if hg > ag else ('D' if hg == ag else 'A')
        lg = folder.split('_')[0] if '_' in folder else 'other'
        home = away = ''
        for fname in sorted(os.listdir(folder_path)):
            if fname.endswith('.html'):
                with open(os.path.join(folder_path, fname), 'r',
                          encoding='utf-8', errors='replace') as fh:
                    html = fh.read(1000)
                title = re.search(r'<title>(.*?)</title>', html)
                if title:
                    vs = re.search(r'(.+?)VS(.+?)[(]', title.group(1))
                    if vs: home = vs.group(1).strip(); away = vs.group(2).strip()
                break
        if not home: continue
        try:
            data = parse_odds.parse_folder(folder_path)
            companies = list(data['euro_odds']['companies'].values())
        except: continue
        all_iw = [c['odds']['instant'][0] for c in companies[:30]
                  if c['odds']['instant'][0] > 0]
        odds_list = [(c['odds']['instant'][0], c['odds']['instant'][1],
                     c['odds']['instant'][2])
                     for c in companies[:30]
                     if len(c.get('odds', {}).get('instant', [])) >= 3
                     and c['odds']['instant'][0] > 0]
        if len(odds_list) < 5: continue
        probs = oo_epc_convert(odds_list)
        ph = correct_fl_bias(probs['home'])
        pa = correct_fl_bias(probs['away'])
        elo_sig = get_elo_signal(lg, home, away)
        all_matches.append({
            'date': date_dir, 'lg': lg,
            'home': home, 'away': away,
            'actual': actual, 'hg': hg, 'ag': ag,
            'ph': ph, 'pa': pa,
            'elo_diff': elo_sig['elo_diff'] if elo_sig else 0,
            'elo_abs': elo_sig['elo_abs_diff'] if elo_sig else 0,
        })

all_matches.sort(key=lambda m: m['date'])
print('%d 场比赛' % len(all_matches))

# 计算赛前战绩特征
print('计算战绩+H2H...')
for i, m in enumerate(all_matches):
    prev = all_matches[:i]
    home = m['home']; away = m['away']; lg = m['lg']

    # 主队近期(所有比赛)
    h_all = sorted([p for p in prev
                    if (p['home'] == home or p['away'] == home)
                    and p['lg'] == lg],
                   key=lambda x: x['date'])[-5:]
    # 客队近期
    a_all = sorted([p for p in prev
                    if (p['home'] == away or p['away'] == away)
                    and p['lg'] == lg],
                   key=lambda x: x['date'])[-5:]

    if len(h_all) >= 3:
        hw = sum(1 for p in h_all
                 if (p['home'] == home and p['hg'] > p['ag'])
                 or (p['away'] == home and p['ag'] > p['hg']))
        hd = sum(1 for p in h_all if p['hg'] == p['ag'])
        m['h_form_ppg'] = round((hw * 3 + hd) / len(h_all), 2)

    if len(a_all) >= 3:
        aw = sum(1 for p in a_all
                 if (p['home'] == away and p['hg'] > p['ag'])
                 or (p['away'] == away and p['ag'] > p['hg']))
        ad2 = sum(1 for p in a_all if p['hg'] == p['ag'])
        m['a_form_ppg'] = round((aw * 3 + ad2) / len(a_all), 2)

    # H2H
    h2h = [p for p in prev
           if (p['home'] == home and p['away'] == away)
           or (p['home'] == away and p['away'] == home)]
    if len(h2h) >= 2:
        h2h_w = sum(1 for p in h2h
                    if (p['home'] == home and p['hg'] > p['ag'])
                    or (p['away'] == home and p['ag'] > p['hg']))
        h2h_d = sum(1 for p in h2h if p['hg'] == p['ag'])
        h2h_l = len(h2h) - h2h_w - h2h_d
        m['h2h_n'] = len(h2h)
        m['h2h_dom'] = round((h2h_w - h2h_l) / len(h2h), 2)

has_form = sum(1 for m in all_matches if 'h_form_ppg' in m)
has_h2h = sum(1 for m in all_matches if 'h2h_n' in m)
print('战绩: %d/%d  H2H: %d/%d' % (has_form, len(all_matches), has_h2h, len(all_matches)))

# 测试
half = len(all_matches) // 2
test = all_matches[half:]

a_c = a_t = b_c = b_t = c_c = c_t = d_c = d_t = 0

for m in test:
    elo_abs = m.get('elo_abs', 0)
    elo_diff = m.get('elo_diff', 0)

    if elo_abs >= 40:
        pred = 'H' if elo_diff > 0 else 'A'
        if pred == m['actual']: a_c += 1
        a_t += 1
    else:
        # 低Elo差 - 尝试多种策略
        # B: 战绩方向
        if 'h_form_ppg' in m and 'a_form_ppg' in m:
            h_ppg = m['h_form_ppg']; a_ppg = m['a_form_ppg']
            gap = abs(h_ppg - a_ppg)
            if gap > 0.6: b_pred = 'H' if h_ppg > a_ppg else 'A'
            else: b_pred = 'D'
            if b_pred == m['actual']: b_c += 1
            b_t += 1

        # C: H2H方向
        if 'h2h_n' in m and m['h2h_n'] >= 2:
            dom = m['h2h_dom']
            if abs(dom) > 0.3: c_pred = 'H' if dom > 0 else 'A'
            else: c_pred = 'D'
            if c_pred == m['actual']: c_c += 1
            c_t += 1

        # D: 市场方向(Pinnacle替代 - 用ph/pa)
        d_pred = 'H' if m['ph'] > m['pa'] else 'A'
        if d_pred == m['actual']: d_c += 1
        d_t += 1

print()
print('=== 混合策略测试 (%d场测试集) ===' % len(test))
print('A (Elo>40):           %d/%d = %.0f%% (覆盖%.0f%%)' % (
    a_c, a_t, 100*a_c//max(1,a_t), 100*a_t//len(test)))
print('B (低Elo+战绩方向):    %d/%d = %.0f%%' % (b_c, b_t, 100*b_c//max(1,b_t)))
print('C (低Elo+H2H方向):     %d/%d = %.0f%%' % (c_c, c_t, 100*c_c//max(1,c_t)))
print('D (低Elo+市场方向):    %d/%d = %.0f%%' % (d_c, d_t, 100*d_c//max(1,d_t)))

# 混合最优
low_best = max(b_c//max(1,b_t), c_c//max(1,c_t), d_c//max(1,d_t))
total_c = a_c + (a_c * low_best // max(1, (a_c//max(1,a_t))))
print()
print('混合(A+低差距最优):   ~%d/%d = ~%.0f%%' % (
    a_c + (len(test)-a_t)*low_best//max(1,(b_t or c_t or d_t)),
    len(test),
    100*(a_c + (len(test)-a_t)*low_best//max(1,(b_t or c_t or d_t)))//len(test)))
