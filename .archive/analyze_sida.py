import re, os

folder = 'C:/Users/51095/Desktop/足彩/斯达 2-0 瓦勒伦加05-25.20.30/'
files = os.listdir(folder)
yz_file = oz_file = None
for f in files:
    if f.endswith('.html'):
        full = os.path.join(folder, f)
        if '亚指' in f: yz_file = full
        elif '欧指' in f: oz_file = full

print(f"欧指: {oz_file}")
print(f"亚指: {yz_file}")

# === PARSE 欧指 ===
with open(oz_file, 'r', encoding='utf-8', errors='replace') as f:
    oz_html = f.read()

trs = re.findall(r'<tr[^>]*>(.*?)</tr>', oz_html, re.DOTALL)
oz_data = []
for tr in trs:
    tds = re.findall(r'<td[^>]*>(.*?)</td>', tr, re.DOTALL)
    clean = [re.sub(r'<[^>]+>', '', t).strip().replace('&nbsp;',' ').strip() for t in tds]
    clean = [c for c in clean if c]
    if not clean: continue
    odds = [c for c in clean if re.match(r'^\d+\.\d{2}$', c)]
    if len(odds) >= 3:
        try:
            vals = [float(c) for c in odds[:3]]
            if 1.2 <= vals[0] <= 50:
                oz_data.append(clean)
        except: pass

jcp = None
for row in oz_data:
    if '竞彩官' in ' '.join(row) and '+1' not in ' '.join(row):
        jcp = row
        break

intl_rows = [r for r in oz_data if '竞彩官' not in ' '.join(r)]

def get_odds(row, n=11):
    nums = [float(c) for c in row if re.match(r'^\d+\.\d{2}$', c)]
    return nums[:n] if len(nums) >= n else nums

jcp_odds = get_odds(jcp) if jcp else None

intl_all = []
for r in intl_rows:
    o = get_odds(r)
    if len(o) >= 10:
        intl_all.append(o)

# International stats
intl_home = [o[0] for o in intl_all]
intl_draw = [o[1] for o in intl_all]
intl_away = [o[2] for o in intl_all]
kelly_home = [o[7] for o in intl_all]
ret_rates = [o[6] for o in intl_all]

avg_h = sum(intl_home)/len(intl_home)
avg_d = sum(intl_draw)/len(intl_draw)
avg_a = sum(intl_away)/len(intl_away)
avg_k = sum(kelly_home)/len(kelly_home)
avg_r = sum(ret_rates)/len(ret_rates)

# === PARSE 亚指 ===
with open(yz_file, 'r', encoding='utf-8', errors='replace') as f:
    yz_html = f.read()

yz_trs = re.findall(r'<tr[^>]*>(.*?)</tr>', yz_html, re.DOTALL)
yz_co = []
for tr in yz_trs:
    tds = re.findall(r'<td[^>]*>(.*?)</td>', tr, re.DOTALL)
    clean = [re.sub(r'<[^>]+>', '', t).strip().replace('&nbsp;',' ').strip() for t in tds]
    clean = [c for c in clean if c]
    if not clean: continue
    has_odds = any(re.search(r'\d+\.\d{2}', c) for c in clean)
    has_hcp = any(h in ' '.join(clean) for h in ['球','半','平手','受让'])
    if has_odds and has_hcp and '指数2' not in ' '.join(clean):
        yz_co.append(clean)

# ===== 6D ANALYSIS =====
print("=" * 60)
print("斯达 vs 瓦勒伦加 | 挪超第10轮 | 比分 2-0")
print("=" * 60)

# D1
print(f"\n[D1 赔率区间] 国际均赔 主{avg_h:.2f}/平{avg_d:.2f}/客{avg_a:.2f}")
if 1.72 <= avg_h <= 1.85:
    d1, d1w = 1, f"黄金区({avg_h:.2f}) 正路率73.6%"
elif 1.40 <= avg_h <= 1.49:
    d1, d1w = 0, f"死亡区({avg_h:.2f}) 正路率仅38%"
elif 1.90 <= avg_h <= 2.00:
    d1, d1w = 0, f"死亡区({avg_h:.2f}) 正路率41%"
else:
    d1, d1w = 0, f"非典型区间({avg_h:.2f}) 弱信号"

# D2
print(f"\n[D2 盘口变化] 亚盘{len(yz_co)}行")
# Get main handicap
hcp_set = set()
for row in yz_co[:3]:
    for c in row:
        if any(h in c for h in ['平手','半球','一球','球半','受平','受半','受一']):
            hcp_set.add(c)
print(f"  主要盘口: {hcp_set}")
print(f"  瓦勒伦加让0.25球 → 市场认为客队更强")
print(f"  实际斯达2-0 → 盘口方向完全错误")
d2, d2w = 0, "盘口指向客队→实际主胜→信号反向"

# D3
print(f"\n[D3 赛事类型] 挪超第10轮 → 联赛中段正常")
d3, d3w = 1, "联赛中段"

# D4
home_range = max(intl_home) - min(intl_home)
print(f"\n[D4 庄家共识] {len(intl_all)}家公司 极差{home_range:.2f}")
if home_range < 0.20:
    d4, d4w = 1, f"赔率高度集中(极差{home_range:.2f})→共识强"
else:
    d4, d4w = 0, f"赔率有分歧(极差{home_range:.2f})→共识弱"

# D5
k_over = sum(1 for k in kelly_home if k > 1.0)
k_low = sum(1 for k in kelly_home if k < 0.85)
k_norm = len(kelly_home) - k_over - k_low
print(f"\n[D5 凯利指数] 均值{avg_k:.3f} K>1:{k_over}家 K<0.85:{k_low}家")
if k_over > len(kelly_home)*0.3:
    d5, d5w = 0, f"凯利大面积>1.0({k_over}家)→亏损预警"
elif k_low > len(kelly_home)*0.5:
    d5, d5w = 0, f"凯利大面积<0.85({k_low}家)→异常"
else:
    d5, d5w = 1, f"凯利正常({k_norm}家)"

# D6
print(f"\n[D6 主任恐惧]")
if jcp_odds:
    jcp_h = jcp_odds[0]; jcp_a = jcp_odds[2]; jcp_rr = jcp_odds[6]; jcp_kh = jcp_odds[7]
    gap_h = jcp_h - avg_h
    print(f"  竞彩: 主{jcp_h:.2f}/客{jcp_a:.2f} 返还率{jcp_rr:.1f}% 凯利主{jcp_kh:.3f}")
    print(f"  国际: 主{avg_h:.2f}/客{avg_a:.2f} 返还率{avg_r:.1f}% 凯利主{avg_k:.3f}")
    print(f"  主胜差距: {gap_h:+.2f}")
    print(f"  走势: 主胜 2.95→3.05(+0.10) 客胜 1.97→1.91(-0.06)")

    if gap_h > 0.10:
        d6, d6w = 0, f"竞彩主胜高于国际(+{gap_h:.2f})→主任引诱→信号B"
    elif gap_h < -0.10:
        d6, d6w = 1, f"竞彩主胜低于国际({gap_h:.2f})→主任害怕→信号A"
    else:
        d6, d6w = 0, "差距正常→无信号"

# TOTAL
total = d1 + d2 + d3 + d4 + d5 + d6
print(f"\n{'='*60}")
print(f"六维总分: {total}/6")
print(f"  D1: {d1}分 D2: {d2}分 D3: {d3}分 D4: {d4}分 D5: {d5}分 D6: {d6}分")
print(f"  实际: 斯达 2-0 瓦勒伦加")
print(f"  判定: {'跳过' if total <= 3 else ('弱信号' if total <= 4 else '可串关')}")
print(f"  框架评价: 2-3分=跳过 → 错过主胜 → 框架偏保守")

# ===== DEEP DIVE =====
print(f"\n{'='*60}")
print("主任行为解读")
print(f"{'='*60}")
print(f"""
为什么主任持续抬高主胜赔率？

根本原因: 这是一次"共识误判"，主任没在操纵，他在跟随。

1. 看国际赔率: 所有庄家(365/Pinnacle/澳门)客胜都在1.91-2.26
   客胜是热门方向 → 大量资金压在客队(瓦勒伦加)

2. 主任的困境:
   - 如果客胜打出 → 主任要赔很多(客胜SP 1.91)
   - 他必须吸引资金去主胜方向 → 抬高主胜赔率 → 看起来更"划算"
   - 这是被动风控，不是主动引诱

3. 为什么还是亏了:
   - 他抬主胜确实吸引了一些资金 → 但不改变整体失衡
   - 斯达主场2-0 → 比赛结果本身是冷门
   - 主任亏钱不是因为策略错，是因为"比赛没按剧本走"

4. 和D6框架的关系:
   - D6信号B(引诱)在这场比赛是错的 — 抬高主胜≠主胜不会发生
   - 关键区别: 主任是被动跟随(跟国际同步)还是主动背离(自己反着走)
   - 如果主任跟国际方向一致 → 这是市场共识 → 可能集体错误
   - 如果主任跟国际方向相反 → 这才是"主任恐惧"的真信号
""")
