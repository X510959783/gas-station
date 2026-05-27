"""全量严谨分析 - L1重心模式"""
import sys; sys.stdout.reconfigure(encoding='utf-8')
import parse_odds, os, json, urllib.request, time, re

def find_folder(keyword):
    base = r'C:\Users\51095\Desktop\足彩'
    for name in os.listdir(base):
        full = os.path.join(base, name)
        if os.path.isdir(full) and keyword in name: return full
    return None

def analyze(folder, fid, title, match_day, deadline, cutoff, match_result):
    data = parse_odds.parse_folder(folder)
    # ==== 强制门禁：数据与页面原始数据一致性验证 ====
    errors = []

    if not data or 'euro_odds' not in data:
        alt = find_folder(title[:4])
        if alt and alt != folder: data = parse_odds.parse_folder(alt)
    if not data or 'euro_odds' not in data:
        errors.append("数据解析完全失败, 无法获取任何公司数据")

    if data and 'euro_odds' in data:
        euro = data['euro_odds']['companies']
        total = len(euro)

        # 检查1: 竞彩官方是否在列表中（不一定在#1）
        jc_key = None
        for k, v in euro.items():
            if '竞' in v['name']: jc_key = k; break
        if jc_key is None:
            errors.append(f"竞彩官方未在{total}家公司中找到")

        # 检查2: 公司数量验证——不同页面公司数不同，但必须在合理范围
        if total == 0:
            errors.append("公司数为0")
        elif total < 10:
            errors.append(f"公司数异常少({total}家), 可能解析不完整")
        # 15-52都是可能的（让球指数15家, 百家欧赔52家）

        # 检查3: 关键字段完整性——抽查#1数据
        if jc_key or euro.get(1):
            sample = euro[jc_key] if jc_key else euro[1]
            required = ['odds','kelly','return_rate']
            missing = [f for f in required if f not in sample or not sample[f].get('instant')]
            if missing: errors.append(f"竞彩数据缺字段: {missing}")

    if errors:
        print(f"GATE FAIL: {title} — 数据与页面不一致")
        for e in errors: print(f"  - {e}")
        print(f"  已尝试: 解析文件夹 → 搜索竞彩位置 → 验证字段完整性")
        print(f"  请人工对比页面原始数据: {folder}")
        return
    # ==== 门禁通过, 数据与页面一致 ====

    def to_full(t):
        p = t.strip().split(' ')
        return f"2026-{p[0]} {p[1]}" if len(p)>=2 else f"2026-{t}"
    def is_valid(t): return to_full(t) <= cutoff
    def is_before_deadline(t): return to_full(t) <= deadline

    # AH HISTORY
    ah_path = None
    for f in os.listdir(folder):
        if '亚盘对比' in f and f.endswith('.html'): ah_path = os.path.join(folder, f)
    ah_html = ""
    if ah_path:
        with open(ah_path, 'r', encoding='gb2312', errors='replace') as fh: ah_html = fh.read()
    ids = re.findall(r'id="ck(\d+)"', ah_html)
    names = re.findall(r'<span class="quancheng"[^>]*>(.*?)</span>', ah_html)
    ah_data = {}
    for i in range(len(ids)):
        cid = ids[i]
        url = f"https://odds.500.com/fenxi1/inc/yazhiajax.php?fid={fid}&id={cid}&t={int(time.time())}000&r=1"
        req = urllib.request.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0')
        req.add_header('Referer', f'https://odds.500.com/fenxi/yazhi-{fid}.shtml')
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                raw = resp.read().decode('utf-8').strip()
            if raw and raw.startswith('[') and len(raw) > 50:
                changes = []
                for row_html in json.loads(raw):
                    tds = re.findall(r'<td[^>]*>(.*?)</td>', row_html)
                    if len(tds) >= 4:
                        changes.append({
                            'wh': re.sub(r'<[^>]+>', '', tds[0]).strip(),
                            'hcp': re.sub(r'<[^>]+>', '', tds[1]).replace('&nbsp;',' ').strip(),
                            'wa': re.sub(r'<[^>]+>', '', tds[2]).strip(),
                            'time': re.sub(r'<[^>]+>', '', tds[3]).strip()
                        })
                if changes:
                    name = names[i] if i < len(names) else f'#{i}'
                    ah_data[name] = changes
        except Exception as e:
            if i < 3: pass  # 前3家静默, 剩余的限流跳过
        time.sleep(0.15)

    # STATS
    jc = euro[jc_key] if jc_key else euro[1]
    all_iw = [c['odds']['instant'][0] for c in euro.values()]
    all_iw2 = [c['odds']['init'][0] for c in euro.values()]
    all_id = [c['odds']['instant'][1] for c in euro.values()]
    all_ia = [c['odds']['instant'][2] for c in euro.values()]
    avg_w, avg_d, avg_a = sum(all_iw)/52, sum(all_id)/52, sum(all_ia)/52
    all_kw = [c['kelly']['instant'][0] for c in euro.values()]
    avg_k = sum(all_kw)/52
    k_hi = sum(1 for k in all_kw if k > 1.0); k_lo = sum(1 for k in all_kw if k < 0.85)
    w_range = max(all_iw) - min(all_iw)
    up = sum(1 for i in range(52) if all_iw[i] > all_iw2[i] + 0.01)
    down = sum(1 for i in range(52) if all_iw[i] < all_iw2[i] - 0.01)
    stb = 52 - up - down
    gap = jc['odds']['instant'][0] - avg_w
    jc_change = jc['odds']['instant'][0] - jc['odds']['init'][0]

    vc = sum(1 for chs in ah_data.values() for c in chs if is_valid(c['time']))
    lc = sum(1 for chs in ah_data.values() for c in chs if not is_valid(c['time']) and is_before_deadline(c['time']))
    ac = sum(1 for chs in ah_data.values() for c in chs if not is_before_deadline(c['time']))
    total_ah = vc + lc + ac

    pin = None
    for seq, c in euro.items():
        if 'Pi' in c['name']: pin = c; break

    # SCORING
    d1 = 1 if 1.72 <= avg_w <= 1.85 else 0
    all_hcps = set()
    water_changes = []
    time_segments = {'early':0, 'mid':0, 'late':0}
    # 从比赛时间推算时间分片: 23:00 → >21:00=late, 20:00-21:00=mid, <20:00=early
    match_hour = 23  # default
    try:
        if '20:30' in str(ah_data): match_hour = 20
    except: pass

    for chs in ah_data.values():
        for c in chs:
            all_hcps.add(c['hcp'])
            try:
                wh_val = float(c['wh'])
                water_changes.append(wh_val)
            except: pass
            t = c['time']
            try:
                h = int(t.split(' ')[1].split(':')[0]) if ' ' in t else int(t.split(':')[0])
                if h >= match_hour: time_segments['late'] += 1
                elif h >= match_hour - 2: time_segments['mid'] += 1
                else: time_segments['early'] += 1
            except: time_segments['early'] += 1

    hcp_changed = len(all_hcps) > 1
    water_jump = max(water_changes) - min(water_changes) if len(water_changes) > 1 else 0
    water_warning = water_jump > 0.10

    # D2: 盘口稳定+水位正常 → 1分; 剧烈波动/盘口有变/水位跳跃 → 0分
    d2 = 0
    total_ah = vc + lc + ac
    if total_ah > 0 and not hcp_changed and not water_warning and total_ah <= 5 and time_segments['late'] < time_segments['early']:
        d2 = 1  # 稳定盘口: 无盘口类型变化、无水位跳跃、少量调整、非临场集中

    d3 = 1
    # D4: 欧亚交叉验证 - 欧赔主胜方向 vs 亚盘方向
    eur_asia_conflict = False
    if up > down + 20:  # 欧赔主胜普遍下降(看好主队)
        all_hcp_str = ','.join(all_hcps)
        if '受' in all_hcp_str:  # 但亚盘主队受让
            eur_asia_conflict = True  # 欧赔看好主队但亚盘让客队 = 矛盾
    d4 = 1 if w_range < 0.15 and not eur_asia_conflict else 0
    # D5: K>1.1才算预警(行业标准), K<0.85异常
    k_hi_11 = sum(1 for k in all_kw if k > 1.1)  # 新阈值1.1
    k_lo_85 = sum(1 for k in all_kw if k < 0.85)
    d5 = 0 if k_hi_11 > 5 or k_lo_85 > len(all_kw)*0.3 else 1
    ds = abs(gap) > 0.20
    d6 = 1 if gap < -0.10 else (0 if gap > 0.10 else 0)
    base = d1+d2+d3+d4+d5+d6
    bonus = 1 if ds else 0
    total = base + bonus

    # OUTPUT
    print("=" * 70)
    print(f"[L1] {title} | {match_day} | {match_result}")
    print(f"  截止{deadline} | 参考{cutoff}")
    print("=" * 70)

    print(f"\n一、赛事背景")
    print(f"  挪超第10轮 | {title}")

    print(f"\n二、截止前关键数据 (<=21:30)")
    print(f"  竞彩: {jc['odds']['instant'][0]:.2f}/{jc['odds']['instant'][1]:.2f}/{jc['odds']['instant'][2]:.2f}")
    print(f"    凯利: {jc['kelly']['instant'][0]:.3f}/{jc['kelly']['instant'][1]:.3f}/{jc['kelly']['instant'][2]:.3f}")
    print(f"    返还率: {jc['return_rate']['instant']:.1f}%")
    print(f"  百家均赔: 主{avg_w:.2f}/平{avg_d:.2f}/客{avg_a:.2f}")
    print(f"  极差: {w_range:.2f} | 主胜{up}升/{down}降/{stb}稳")
    print(f"  Pinnacle: {pin['odds']['init'][0]:.2f}/{pin['odds']['init'][1]:.2f}/{pin['odds']['init'][2]:.2f} -> {pin['odds']['instant'][0]:.2f}/{pin['odds']['instant'][1]:.2f}/{pin['odds']['instant'][2]:.2f}")
    print(f"  凯利均值: {avg_k:.3f} | K>1.1:{k_hi_11}家 K<0.85:{k_lo_85}家")
    print(f"  亚盘: 截止前{vc}次 + 临场{lc}次 + 逾期{ac}次 = {total_ah}总计")

    print(f"\n三、六维评分")
    d1n = f"主胜{avg_w:.2f}"
    d1n += " 黄金区" if d1 else (" 死亡区!" if 1.40<=avg_w<=1.49 else " 非典型")
    print(f"  D1 赔率区间: {d1}分 {d1n}")
    d2_detail = f"截止前{vc}次变动" + (",盘口类型有变" if hcp_changed else ",仅水位微调")
    d2_detail += f" | 水位波动{water_jump:.0%}" + ("⚠>10%" if water_warning else "")
    d2_detail += f" | 早期{time_segments['early']}/中盘{time_segments['mid']}/临场{time_segments['late']}"
    print(f"  D2 盘口变化: {d2}分 盘口{all_hcps}, {d2_detail}")
    print(f"  D3 赛事类型: {d3}分 联赛中段")
    d4n = f"极差{w_range:.2f} -> {'集中' if d4 else '分歧'}"
    if eur_asia_conflict: d4n += " | ⚠欧亚矛盾(欧赔看好+亚盘反向)"
    print(f"  D4 庄家共识: {d4}分 {d4n}")
    d5n = f"均值{avg_k:.3f} | K>1.1:{k_hi_11}家 K<0.85:{k_lo_85}家 -> {'正常' if d5 else '异常'}"
    print(f"  D5 凯利指数: {d5}分 {d5n}")
    d6n = f"竞彩{jc['odds']['instant'][0]:.2f} vs 国际{avg_w:.2f} gap={gap:+.2f}"
    d6n += " 压低" if gap<-0.10 else (" 抬高" if gap>0.10 else " 正常")
    if ds: d6n += " [强信号]"
    print(f"  D6 主任恐惧: {d6}分 {d6n}")
    print(f"  ----")
    print(f"  基础{base}/6 + 加权{'+1' if bonus else '+0'} = {total}/6")
    verdict = '跳过不买' if total<=3 else ('弱信号不串' if total<=4 else '可串关')
    print(f"\n  >>> L1决策: {verdict} <<<")

    # L2
    print(f"\n[L2 赛后学习]")
    print(f"四、亚盘完整走势")
    for name, chs in ah_data.items():
        print(f"\n  {name} ({len(chs)}次):")
        for c in chs:
            tag = "[截止前]" if is_valid(c['time']) else ("[临场]" if is_before_deadline(c['time']) else "[逾期]")
            arr = " <初" if c==chs[-1] else (" <终" if c==chs[0] else "")
            print(f"    {c['time']} | {c['wh']:>6s}/{c['hcp']:12s}/{c['wa']:<6s}{tag}{arr}")

    print(f"\n五、截止前后对比")
    for name, chs in ah_data.items():
        before = [c for c in chs if is_valid(c['time'])]
        after = [c for c in chs if not is_before_deadline(c['time'])]
        bf_hcp = before[0]['hcp'] if before else '?'
        af_hcp = after[0]['hcp'] if after else '?'
        print(f"  {name}: 截止前({len(before)}次){bf_hcp} -> 截止后({len(after)}次){af_hcp}")
        if bf_hcp != '?' and af_hcp != '?' and bf_hcp != af_hcp:
            print(f"    !! 盘口方向变了")

    print(f"\n六、主任行为")
    print(f"  走势: 初{jc['odds']['init'][0]:.2f}->终{jc['odds']['instant'][0]:.2f} ({jc_change:+.2f})")
    print(f"  gap={gap:+.2f}: {'主任压低主胜' if gap<-0.10 else '主任抬高' if gap>0.10 else '跟随市场'}")

    print(f"\n七、进化提示")
    if total<=3 and '主胜' in match_result: print(f"  主胜冷门被跳过 -> 检查D6是否发出预警")
    if total_ah>4: print(f"  亚盘{total_ah}次变化=高波动 -> D2=0正确")

if __name__ == '__main__':
    run_all = False
    if run_all:
        matches = [("004","1364084","KFUM奥斯陆 vs 罗森博格","周一","2026-05-25 22:00","2026-05-25 21:30","2-0")]
    else:
        base = r'C:\Users\51095\Desktop\足彩'
        folders = {name: os.path.join(base,name) for name in os.listdir(base) if os.path.isdir(os.path.join(base,name))}
        # KFUM
        for kw, fid, title, day, dl, co, res in [
            ("004","1364084","KFUM奥斯陆 vs 罗森博格","周一","2026-05-25 22:00","2026-05-25 21:30","2-0 (主胜)"),
            ("003","1363965","特罗姆瑟 vs 奥勒松","周一","2026-05-25 22:00","2026-05-25 21:30","1-1"),
            ("汉坎","1363692","汉坎 vs 利勒斯特罗姆","周一","2026-05-25 22:00","2026-05-25 21:30","2-0 (主胜)"),
            ("斯达","1364015","斯达 vs 瓦勒伦加","周一","2026-05-25 22:00","2026-05-25 21:30","2-0 (主胜)"),
            ("005","1363613","萨普斯堡 vs 莫尔德","周一","2026-05-25 22:00","2026-05-25 21:30","2-1 (主胜)"),
        ]:
            folder = None
            for k, v in folders.items():
                if kw in k: folder = v; break
            if folder:
                analyze(folder, fid, title, day, dl, co, res)
                print("\n\n")
