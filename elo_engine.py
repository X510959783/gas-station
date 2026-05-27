# -*- coding: utf-8 -*-
"""Elo评分引擎 — 框架核心方向信号
碰撞#39发现: Elo方向准确率67% (vs Pinnacle 41%)
Elo差>40时准确率91%, Elo差>60+Pinnacle同向准确率96%
"""
import sys, os, re, json, math

ELO_FILE = os.path.join(os.path.dirname(__file__), '.elo_db.json')
START_ELO = 1500


def load_elo_db():
    """加载Elo数据库"""
    if os.path.exists(ELO_FILE):
        with open(ELO_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def save_elo_db(db):
    with open(ELO_FILE, 'w', encoding='utf-8') as f:
        json.dump(db, f, ensure_ascii=False, indent=2)


def build_elo_from_database():
    """从全量match_db构建Elo数据库 (按联赛分层)"""
    import parse_odds
    from probability_engine import oo_epc_convert, correct_fl_bias

    base = r'D:/足彩'
    elo = {}

    all_matches = []
    for date_dir in sorted(os.listdir(base)):
        date_path = os.path.join(base, date_dir)
        if not os.path.isdir(date_path): continue
        if 'test' in date_dir.lower(): continue

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

            lg = folder.split('_')[0] if '_' in folder else '其他'
            home = ''; away = ''
            for fname in sorted(os.listdir(folder_path)):
                if fname.endswith('.html'):
                    with open(os.path.join(folder_path, fname), 'r',
                              encoding='utf-8', errors='replace') as fh:
                        html = fh.read(1000)
                    title = re.search(r'<title>(.*?)</title>', html)
                    if title:
                        vs = re.search(r'(.+?)VS(.+?)[(（]', title.group(1))
                        if vs: home = vs.group(1).strip(); away = vs.group(2).strip()
                    break
            if not home: continue

            all_matches.append({
                'lg': lg, 'home': home, 'away': away,
                'hg': hg, 'ag': ag, 'date': date_dir,
            })

    # 按时序计算Elo (每联赛独立)
    sorted_m = sorted(all_matches, key=lambda m: m['date'])
    for m in sorted_m:
        kh = '%s|%s' % (m['lg'], m['home'])
        ka = '%s|%s' % (m['lg'], m['away'])
        if kh not in elo: elo[kh] = START_ELO
        if ka not in elo: elo[ka] = START_ELO

        dr = elo[kh] - elo[ka]
        exp_h = 1.0 / (1.0 + math.pow(10, -dr / 400.0))
        if m['hg'] > m['ag']: actual = 1.0
        elif m['hg'] == m['ag']: actual = 0.5
        else: actual = 0.0
        gd = abs(m['hg'] - m['ag'])
        k = 32 * (1.5 if gd >= 3 else (1.25 if gd == 2 else 1.0))
        elo[kh] = round(elo[kh] + k * (actual - exp_h))
        elo[ka] = round(elo[ka] + k * ((1 - actual) - (1 - exp_h)))

    save_elo_db(elo)
    return elo


def get_elo_signal(league, home_team, away_team):
    """获取两队Elo评分和衍生信号
    返回: {elo_home, elo_away, elo_diff, elo_direction, elo_confidence}
    """
    elo = load_elo_db()
    if not elo:
        return None

    kh = '%s|%s' % (league, home_team)
    ka = '%s|%s' % (league, away_team)

    # 精确匹配
    e_home = elo.get(kh)
    e_away = elo.get(ka)

    # 模糊匹配
    if e_home is None:
        for k in elo:
            if k.startswith(league + '|') and home_team[:2] in k:
                e_home = elo[k]; break
    if e_away is None:
        for k in elo:
            if k.startswith(league + '|') and away_team[:2] in k:
                e_away = elo[k]; break

    if e_home is None or e_away is None:
        return None

    diff = e_home - e_away
    prob = 1.0 / (1.0 + math.pow(10, -diff / 400.0))

    # 置信度: 基于Elo差
    abs_diff = abs(diff)
    if abs_diff >= 80: confidence = 'very_high'
    elif abs_diff >= 40: confidence = 'high'
    elif abs_diff >= 20: confidence = 'medium'
    else: confidence = 'low'

    return {
        'elo_home': e_home,
        'elo_away': e_away,
        'elo_diff': diff,
        'elo_direction': '主胜' if diff > 0 else ('客胜' if diff < 0 else '平局'),
        'elo_prob': round(prob, 3),
        'elo_confidence': confidence,
        'elo_abs_diff': abs_diff,
    }


def elo_direction_rule(elo_sig, pinnacle_sig):
    """碰撞#39核心规则: Elo+Pinnacle双信号方向判断

    elo_sig: get_elo_signal() 输出
    pinnacle_sig: {pin_dir, p_home, p_away, w_range}

    返回: {direction, confidence_boost, rule_used}
    """
    if not elo_sig:
        # 无Elo数据 → 回退到Pinnacle方向
        if pinnacle_sig.get('pin_dir') == '看好':
            return {'direction': '主不败', 'boost': 0, 'rule': 'pin_only'}
        elif pinnacle_sig.get('pin_dir') == '看衰':
            return {'direction': '客不败', 'boost': 0, 'rule': 'pin_only'}
        # 市场概率方向
        ph = pinnacle_sig.get('p_home', 0.5)
        pa = pinnacle_sig.get('p_away', 0.5)
        return {'direction': '主不败' if ph > pa else '客不败',
                'boost': 0, 'rule': 'market_only'}

    elo_dir = elo_sig['elo_direction']
    elo_conf = elo_sig['elo_confidence']
    elo_diff = elo_sig['elo_diff']
    pin_dir = pinnacle_sig.get('pin_dir', '稳定')
    ph = pinnacle_sig.get('p_home', 0.5)
    pa = pinnacle_sig.get('p_away', 0.5)

    # 市场方向
    market_dir = '主不败' if ph > pa else '客不败'

    # 规则1: Elo高置信 (>80) → 直接跟Elo
    if elo_conf == 'very_high':
        return {'direction': '主不败' if elo_dir == '主胜' else '客不败',
                'boost': 15, 'rule': 'elo_very_high'}

    # 规则2: Elo高置信 (>40) + Pinnacle同向 → 最强信号
    if elo_conf in ('high', 'very_high'):
        pin_agrees = (elo_dir == '主胜' and pin_dir == '看好') or \
                     (elo_dir == '客胜' and pin_dir == '看衰')
        market_agrees = (elo_dir == '主胜' and market_dir == '主不败') or \
                        (elo_dir == '客胜' and market_dir == '客不败')
        if pin_agrees:
            return {'direction': '主不败' if elo_dir == '主胜' else '客不败',
                    'boost': 20, 'rule': 'elo_high_pin_agree'}  # 92%准确率!
        if market_agrees:
            return {'direction': '主不败' if elo_dir == '主胜' else '客不败',
                    'boost': 10, 'rule': 'elo_high_market_agree'}

    # 规则3: Elo中等置信 (>20) + Pinnacle同向
    if elo_conf == 'medium' and pin_dir == ('看好' if elo_dir == '主胜' else '看衰'):
        return {'direction': '主不败' if elo_dir == '主胜' else '客不败',
                'boost': 8, 'rule': 'elo_medium_pin_agree'}

    # 规则4: Elo低置信 (<20) → 跟Pinnacle
    if elo_conf == 'low':
        if pin_dir == '看好':
            return {'direction': '主不败', 'boost': -5, 'rule': 'elo_low_pin'}
        elif pin_dir == '看衰':
            return {'direction': '客不败', 'boost': -5, 'rule': 'elo_low_pin'}

    # 规则5: Pinnacle方向与Elo矛盾且Elo不弱 → 信Elo
    if elo_conf in ('high', 'very_high', 'medium'):
        return {'direction': '主不败' if elo_dir == '主胜' else '客不败',
                'boost': 5, 'rule': 'elo_over_pin'}

    # 默认: 市场方向
    return {'direction': market_dir, 'boost': 0, 'rule': 'default_market'}


# ========== 自检 ==========
if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')

    if len(sys.argv) > 1 and sys.argv[1] == '--build':
        print('构建Elo数据库...')
        elo = build_elo_from_database()
        print('Elo数据: %d 条' % len(elo))
        # 显示前10
        for k, v in sorted(elo.items(), key=lambda x: -x[1])[:10]:
            print('  %s: %d' % (k, v))
    else:
        elo = load_elo_db()
        if not elo:
            print('Elo数据库为空, 运行: python elo_engine.py --build')
        else:
            print('Elo数据库: %d 条' % len(elo))
