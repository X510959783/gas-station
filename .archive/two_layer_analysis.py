"""双层分析脚本"""
import json, subprocess, re, urllib.request, time, os

def to_full_time(time_str):
    """把 '05-25 22:39' 转成 '2026-05-25 22:39'"""
    parts = time_str.strip().split(' ')
    if len(parts) >= 2:
        md = parts[0]  # '05-25'
        tm = ' '.join(parts[1:])  # '22:39'
        return f"2026-{md} {tm}"
    return f"2026-{time_str}"

def is_valid(time_str, cutoff):
    return to_full_time(time_str) <= cutoff

def is_before_deadline(time_str, deadline):
    return to_full_time(time_str) <= deadline

def fetch_ah_history(html, fid):
    ids = re.findall(r'id="ck(\d+)"', html)
    names = re.findall(r'<span class="quancheng"[^>]*>(.*?)</span>', html)
    results = {}
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
                rows = json.loads(raw)
                changes = []
                for row_html in rows:
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
                    results[name] = changes
        except: pass
        time.sleep(0.2)
    return results

# ===== 主分析函数 =====
def find_folder(keyword):
    base = r'C:\Users\51095\Desktop\足彩'
    for name in os.listdir(base):
        full = os.path.join(base, name)
        if os.path.isdir(full) and keyword in name:
            return full
    return None

def run(folder, fid, title, match_day, deadline, cutoff, match_result):
    # 自动修正路径（防止"文件夹"后缀遗漏或中文编码问题）
    if not os.path.exists(folder):
        folder = find_folder(folder.split('\\')[-1][:4]) or folder

    # 直接用模块导入，绕开 subprocess 中文路径编码问题
    import parse_odds
    data = parse_odds.parse_folder(folder)
    if not data or 'euro_odds' not in data:
        # 回退：尝试搜索文件夹
        for kw in [title[:4], title.split('vs')[0].strip()[:4]]:
            alt = find_folder(kw)
            if alt:
                data = parse_odds.parse_folder(alt)
                if data and 'euro_odds' in data:
                    folder = alt
                    break
    if not data or 'euro_odds' not in data:
        print(f"ERROR: 无法解析 {title} - 路径 {folder}")
        return
    euro = data['euro_odds']['companies']

    # AH HTML
    ah_path = None
    for f in os.listdir(folder):
        if '亚盘对比' in f and f.endswith('.html'):
            ah_path = os.path.join(folder, f)
    with open(ah_path, 'r', encoding='gb2312', errors='replace') as fh:
        ah_html = fh.read()

    # 欧赔 HTML
    oz_path = None
    for f in os.listdir(folder):
        if '百家欧赔' in f and f.endswith('.html'):
            oz_path = os.path.join(folder, f)
    with open(oz_path, 'r', encoding='gb2312', errors='replace') as fh:
        oz_html = fh.read()

    ah_data = fetch_ah_history(ah_html, fid)

    # Stats
    jc = euro[1]
    all_iw = [c['odds']['instant'][0] for c in euro.values()]
    all_iw2 = [c['odds']['init'][0] for c in euro.values()]
    avg_w = sum(all_iw) / len(all_iw)
    all_kw = [c['kelly']['instant'][0] for c in euro.values()]
    avg_k = sum(all_kw) / len(all_kw)
    w_range = max(all_iw) - min(all_iw)
    up = sum(1 for i in range(len(all_iw)) if all_iw[i] > all_iw2[i] + 0.01)
    down = sum(1 for i in range(len(all_iw)) if all_iw[i] < all_iw2[i] - 0.01)
    stb = len(all_iw) - up - down
    gap = jc['odds']['instant'][0] - avg_w

    # ===== HEADER =====
    print("=" * 70)
    print(f"【实战下注决策 L1】{title} | {match_day} | 截止{deadline}")
    print(f"  数据参考截止: {cutoff} | 实际结果: {match_result}")
    print("=" * 70)

    # ============ LAYER 1: 下注决策 ============

    vc = 0; lc = 0; ac = 0
    for chs in ah_data.values():
        for c in chs:
            if is_valid(c['time'], cutoff): vc += 1
            elif is_before_deadline(c['time'], deadline): lc += 1
            else: ac += 1
    print(f"亚盘: 有效{vc}次 | 参考外{lc}次 | 逾期{ac}次")
    print(f"竞彩终盘: {jc['odds']['instant'][0]:.2f}/{jc['odds']['instant'][1]:.2f}/{jc['odds']['instant'][2]:.2f}")
    print(f"百家均赔: 主{avg_w:.2f}")

    # D1-D6 scoring
    d1 = 1 if 1.72 <= avg_w <= 1.85 else 0
    d1n = f"主胜{avg_w:.2f}" + (" 黄金区" if d1 else (" 死亡区" if 1.40<=avg_w<=1.49 else " 非典型"))

    # D2: 盘口变化 — 用走势数据评估市场信心
    d2 = 0
    d2_detail = []
    total_changes = sum(len(chs) for chs in ah_data.values())
    companies_with_changes = len(ah_data)

    # 分析盘口类型变化
    all_hcps = set()
    for chs in ah_data.values():
        for c in chs:
            all_hcps.add(c['hcp'])
    hcp_changed = len(all_hcps) > 1

    if total_changes == 0:
        d2_detail.append("无盘口数据")
    elif total_changes <= 2 and not hcp_changed:
        d2_detail.append(f"盘口稳定({total_changes}次变动,仅水位微调)")
        d2_detail.append("市场对该方向信心强")
    elif total_changes <= 10:
        d2_detail.append(f"盘口有调整({total_changes}次, {companies_with_changes}家公司)")
        if hcp_changed: d2_detail.append("盘口类型有实质变化")
    else:
        d2_detail.append(f"盘口剧烈波动({total_changes}次,{companies_with_changes}家公司)")
        if hcp_changed: d2_detail.append("盘口类型反复切换")
        d2_detail.append("市场极度不确定 → 高风险信号")

    d2n = " | ".join(d2_detail) + f" | 结果: {match_result}"

    d3 = 1
    k_hi = sum(1 for k in all_kw if k > 1.0); k_lo = sum(1 for k in all_kw if k < 0.85)
    d4 = 1 if w_range < 0.20 else 0
    d5 = 0 if k_hi > len(all_kw)*0.3 or k_lo > len(all_kw)*0.5 else 1

    ds = abs(gap) > 0.20
    d6 = 1 if gap < -0.10 else (0 if gap > 0.10 else 0)
    d6n = f"gap={gap:+.2f} {'压低' if gap<-0.10 else '抬高' if gap>0.10 else '正常'}"
    if ds: d6n += " [强信号]"

    base = d1+d2+d3+d4+d5+d6
    bonus = 1 if ds else 0
    total = base + bonus

    print(f"\n  >>> L1决策: {'跳过不买' if total<=3 else '弱信号不串' if total<=4 else '可串关备选' if total==5 else '串关首选'} <<<")

    # ============ LAYER 2: 赛后学习 ============
    print(f"\n{'─'*50}")
    print("【赛后学习 L2】以下数据实战时不可见，仅供框架进化")
    print(f"{'─'*50}")

    print(f"\n[亚盘完整走势]")
    for name, chs in ah_data.items():
        print(f"\n  {name} ({len(chs)}次):")
        for c in chs:
            if is_valid(c['time'], cutoff): tag = "[下注参考]"
            elif is_before_deadline(c['time'], deadline): tag = "[参考外]"
            else: tag = "[逾期]"
            arr = " <终" if c == chs[0] else (" <初" if c == chs[-1] else "")
            print(f"    {c['time']} | {c['wh']:>6s}/{c['hcp']:12s}/{c['wa']:<6s}{tag}{arr}")

    # ===== L2 CLOSING =====
    pre_total = vc
    post_total = lc + ac
    print(f"\n[L2小结] 截止前{pre_total}次变化(可用于L1) + 截止后{post_total}次变化(仅供学习)")
    print(f"  下次L1优化方向: 从L2数据中提取可提前识别的信号")
    print(f"\n[截止前后对比分析]")
    for name, chs in ah_data.items():
        before = [c for c in chs if is_valid(c['time'], cutoff)]
        between = [c for c in chs if not is_valid(c['time'], cutoff) and is_before_deadline(c['time'], deadline)]
        after = [c for c in chs if not is_before_deadline(c['time'], deadline)]

        print(f"\n  {name}:")
        print(f"    截止前(<=21:30): {len(before)}次, 最后盘口: {before[0]['hcp'] if before else '无'}")
        print(f"    临场(21:30-22:00): {len(between)}次")
        print(f"    截止后(>22:00): {len(after)}次, 最后盘口: {after[0]['hcp'] if after else '无'}")

        # 行为变化分析
        if before and after:
            bf_hcp = before[0]['hcp']
            af_hcp = after[0]['hcp']
            if bf_hcp != af_hcp:
                print(f"    >> 盘口方向变化: {bf_hcp} → {af_hcp}")
                print(f"    >> 心理: 截止前庄家维持{bf_hcp}, 截止后改为{af_hcp}")
                print(f"    >> 如果赛前按截止前盘口下注, 无法享受截止后的盘口调整")
            else:
                print(f"    >> 盘口方向不变: 始终{bf_hcp}, 仅水位微调")
        if len(after) > len(before) * 3:
            print(f"    >> 截止后变动激增({len(after)}次 vs 截止前{len(before)}次)")
            print(f"    >> 庄家在临场阶段极度活跃——比赛不确定性极高")

    # 主任行为
    print(f"\n[主任行为分析]")
    jc_changes = jc['odds']['instant'][0] - jc['odds']['init'][0]
    print(f"  竞彩走势: 初{jc['odds']['init'][0]:.2f}→终{jc['odds']['instant'][0]:.2f} ({jc_changes:+.2f})")
    print(f"  国际均赔: {avg_w:.2f}")
    print(f"  gap={gap:+.2f}")
    if gap < -0.10:
        print(f"  >> 主任压低主胜赔付 → 他对主胜有防范")
        if jc_changes < -0.01:
            print(f"  >> 而且他主动在压(初→终{jc_changes:+.2f}) → 不是被动跟随")
    elif gap > 0.10:
        print(f"  >> 主任抬高主胜 → 他不怕主胜打出")
    else:
        print(f"  >> 主任与国际市场方向一致 → 跟随策略")

    # 操作手法汇总
    if ah_data:
        fc = list(ah_data.values())[0]
        uh = set(c['hcp'] for c in fc)
        print(f"\n[操作手法汇总]")
        print(f"  盘口类型: {uh}, 总变动{len(fc)}次")
        if len(fc) > 10: print(f"  >> 极度活跃盘口 — 庄家对比赛判断力不足 — 这场比赛不可预测")
        elif len(fc) > 4: print(f"  >> 频繁变盘 — 庄家对让球深度不确定")
        if len(uh) > 1: print(f"  >> 盘口类型切换 — 市场方向反复 — 庄家没有定论")
        if len(uh) == 1 and len(fc) <= 2: print(f"  >> 盘口稳定 — 庄家对方向有信心")

# ===== RUN =====
if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        # Single match mode
        folder, fid, name, day, deadline, cutoff, result = sys.argv[1:8]
        run(folder, fid, name, day, deadline, cutoff, result)
    else:
        # ALL matches
        matches = [
            (r'C:\Users\51095\Desktop\足彩\周一004挪超05-25 23.00[14]奥斯KFUM 2.0 罗森博格[15]',
             '1364084', 'KFUM奥斯陆 vs 罗森博格', '周一', '2026-05-25 22:00', '2026-05-25 21:30', '2-0'),
            (r'C:\Users\51095\Desktop\足彩\周一003挪超05-25 23.00[2]特罗姆瑟 1.1 奥勒松[12]',
             '1363965', '特罗姆瑟 vs 奥勒松', '周一', '2026-05-25 22:00', '2026-05-25 21:30', '1-1'),
            (r'C:\Users\51095\Desktop\足彩\汉坎 2-0 利勒斯特罗姆05-25.23.00',
             '1363692', '汉坎 vs 利勒斯特罗姆', '周一', '2026-05-25 22:00', '2026-05-25 21:30', '2-0'),
            (r'C:\Users\51095\Desktop\足彩\斯达 2-0 瓦勒伦加05-25.20.30',
             '1364015', '斯达 vs 瓦勒伦加', '周一', '2026-05-25 22:00', '2026-05-25 21:30', '2-0'),
        ]
        for m in matches:
            run(*m)
            print("\n\n")
