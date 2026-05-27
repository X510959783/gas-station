# -*- coding: utf-8 -*-
"""终极进化: 三条路同时走 — 全特征 + 拣选 + ML集成
特征: Elo + 赔率 + 球队战绩 + H2H交锋 + 联赛编码
策略: Elo差>40直接判 + XGBoost处理势均力敌比赛
"""
import sys, os, re, json, math, time
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))

BASE = r'D:/足彩'


def collect_all_matches():
    """收集所有比赛的基础信息"""
    import parse_odds
    from probability_engine import oo_epc_convert, correct_fl_bias
    from elo_engine import get_elo_signal

    matches = []
    for date_dir in sorted(os.listdir(BASE)):
        date_path = os.path.join(BASE, date_dir)
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
            actual = 'H' if hg > ag else ('D' if hg == ag else 'A')
            lg = folder.split('_')[0] if '_' in folder else '其他'

            # 队名
            home = ''; away = ''
            for fname in sorted(os.listdir(folder_path)):
                if fname.endswith('.html'):
                    with open(os.path.join(folder_path, fname), 'r',
                              encoding='utf-8', errors='replace') as fh:
                        html = fh.read(1000)
                    title = re.search(r'<title>(.*?)</title>', html)
                    if title:
                        vs = re.search(r'(.+?)VS(.+?)[(（]', title.group(1))
                        if vs:
                            home = vs.group(1).strip()
                            away = vs.group(2).strip()
                    break
            if not home: continue

            # 赔率
            try:
                data = parse_odds.parse_folder(folder_path)
                companies = list(data['euro_odds']['companies'].values())
            except:
                continue
            all_iw = [c['odds']['instant'][0] for c in companies[:30]
                      if c['odds']['instant'][0] > 0]
            all_iw_init = [c['odds']['init'][0] for c in companies[:30]
                          if c['odds']['init'][0] > 0]
            odds_list = [(c['odds']['instant'][0], c['odds']['instant'][1],
                         c['odds']['instant'][2])
                         for c in companies[:30]
                         if len(c.get('odds', {}).get('instant', [])) >= 3
                         and c['odds']['instant'][0] > 0]
            if len(odds_list) < 5: continue
            probs = oo_epc_convert(odds_list)
            ph = correct_fl_bias(probs['home'])
            pd = correct_fl_bias(probs['draw'])
            pa = correct_fl_bias(probs['away'])
            w_range = max(all_iw) - min(all_iw) if len(all_iw) > 1 else 0
            avg_ho = sum(all_iw) / len(all_iw) if all_iw else 0
            avg_ao = 0
            ao_n = 0
            for c in companies[:30]:
                inst = c.get('odds', {}).get('instant', [])
                if len(inst) >= 3 and inst[2] > 0:
                    avg_ao += inst[2]; ao_n += 1
            avg_ao = avg_ao / max(1, ao_n)
            up = sum(1 for i in range(min(len(all_iw), len(all_iw_init)))
                     if all_iw[i] > all_iw_init[i] + 0.02)
            down = sum(1 for i in range(min(len(all_iw), len(all_iw_init)))
                       if all_iw[i] < all_iw_init[i] - 0.02)

            # Pinnacle
            pin_dir = 'N'
            for seq, c in data['euro_odds']['companies'].items():
                if 'Pi' in c.get('name', ''):
                    pi, pn = c['odds']['instant'][0], c['odds']['init'][0]
                    if pi < pn - 0.02: pin_dir = 'F'
                    elif pi > pn + 0.02: pin_dir = 'A'
                    break

            # Elo
            elo_sig = get_elo_signal(lg, home, away)

            match = {
                'date': date_dir, 'lg': lg,
                'home': home, 'away': away,
                'actual': actual,
                'hg': hg, 'ag': ag,
                'ph': ph, 'pd': pd, 'pa': pa,
                'w_range': w_range, 'avg_ho': avg_ho, 'avg_ao': avg_ao,
                'up': up, 'down': down, 'pin_dir': pin_dir,
                'folder': folder_path,
            }
            if elo_sig:
                match['elo_h'] = elo_sig['elo_home']
                match['elo_a'] = elo_sig['elo_away']
                match['elo_diff'] = elo_sig['elo_diff']
                match['elo_abs'] = elo_sig['elo_abs_diff']
            matches.append(match)

    return matches


def build_features(matches):
    """构建完整特征矩阵"""
    X_rows = []
    y_rows = []
    meta = []

    for m in matches:
        feats = {}

        # 赔率特征
        feats['p_home'] = m.get('ph', 0.5)
        feats['p_draw'] = m.get('pd', 0.28)
        feats['p_away'] = m.get('pa', 0.22)
        feats['prob_gap'] = abs(m.get('ph', 0.5) - m.get('pa', 0.5))
        feats['w_range'] = m.get('w_range', 0)
        feats['avg_home_odds'] = m.get('avg_ho', 2.5)
        feats['avg_away_odds'] = m.get('avg_ao', 3.0)
        feats['up'] = m.get('up', 0)
        feats['down'] = m.get('down', 0)
        feats['up_ratio'] = m.get('up', 0) / max(1, m.get('up', 0) + m.get('down', 0))
        feats['pin_favor'] = 1 if m.get('pin_dir') == 'F' else 0
        feats['pin_against'] = 1 if m.get('pin_dir') == 'A' else 0

        # Elo特征
        feats['elo_home'] = m.get('elo_h', 1500)
        feats['elo_away'] = m.get('elo_a', 1500)
        feats['elo_diff'] = m.get('elo_diff', 0)
        feats['elo_abs'] = m.get('elo_abs', 0)
        feats['elo_home_prob'] = 1.0 / (1.0 + math.pow(10, -feats['elo_diff'] / 400.0))

        # 衍生特征
        feats['elo_pin_agree'] = 1 if (
            (feats['elo_diff'] > 0 and m.get('pin_dir') == 'F') or
            (feats['elo_diff'] < 0 and m.get('pin_dir') == 'A')) else 0
        feats['odds_elo_agree'] = 1 if (
            (feats['elo_diff'] > 0 and feats['p_home'] > feats['p_away']) or
            (feats['elo_diff'] < 0 and feats['p_away'] > feats['p_home'])) else 0
        feats['strong_signal'] = 1 if (
            feats['elo_abs'] >= 40 and feats['elo_pin_agree']) else 0
        feats['very_strong'] = 1 if (
            feats['elo_abs'] >= 60 and feats['elo_pin_agree']) else 0

        # 联赛编码 (top leagues)
        for lg in ['挪超','瑞超','德甲','英超','意甲','西甲','日职','英甲',
                   '解放者杯','法甲','美职','荷甲','葡超']:
            feats['lg_' + lg] = 1 if m.get('lg') == lg else 0

        X_rows.append(feats)
        y_rows.append(m['actual'])
        meta.append(m)

    return X_rows, y_rows, meta


def train_and_evaluate(X_rows, y_rows, meta, test_ratio=0.3):
    """时序分割训练+评估 (只用前70%训练, 后30%盲测)"""
    import xgboost as xgb
    from sklearn.preprocessing import LabelEncoder
    from sklearn.metrics import accuracy_score

    n = len(X_rows)
    split = int(n * (1 - test_ratio))

    # 按时序分割
    sorted_idx = sorted(range(n), key=lambda i: meta[i].get('date', ''))
    train_idx = sorted_idx[:split]
    test_idx = sorted_idx[split:]

    # 特征矩阵
    feature_names = sorted(X_rows[0].keys())
    X_train = np.array([[row.get(k, 0) for k in feature_names] for i, row in enumerate(X_rows) if i in train_idx])
    X_test = np.array([[row.get(k, 0) for k in feature_names] for i, row in enumerate(X_rows) if i in test_idx])
    y_train = [y_rows[i] for i in train_idx]
    y_test = [y_rows[i] for i in test_idx]
    test_meta = [meta[i] for i in test_idx]

    # Label encode
    le = LabelEncoder()
    y_train_enc = le.fit_transform(y_train)
    y_test_enc = le.transform(y_test)

    # 策略A: Elo高置信直接判
    elo_mask = np.array([X_test[j][feature_names.index('elo_abs')] >= 40 for j in range(len(X_test))])
    # Elo方向 → 预测标签: H→0, A→2 (但不知道label encoder的映射)
    # 直接用原始标签
    elo_correct = 0
    for j in range(len(test_idx)):
        if not elo_mask[j]:
            continue
        m = test_meta[j]
        elo_pred = 'H' if m.get('elo_diff', 0) > 0 else 'A'
        if elo_pred == y_test[j]:
            elo_correct += 1
    elo_total = int(sum(elo_mask))

    # 策略B: XGBoost处理剩余
    xgb_mask = ~elo_mask
    xgb_correct = 0
    if int(sum(xgb_mask)) >= 10:
        model = xgb.XGBClassifier(
            n_estimators=200, max_depth=6, learning_rate=0.05,
            subsample=0.8, colsample_bytree=0.8,
            objective='multi:softprob', random_state=42)
        model.fit(X_train, y_train_enc)

        X_low = X_test[xgb_mask]
        y_low_raw = [y_test[j] for j in range(len(y_test)) if xgb_mask[j]]
        y_low_enc = le.transform(y_low_raw)
        xgb_preds_enc = model.predict(X_low)
        xgb_preds_raw = le.inverse_transform(xgb_preds_enc)
        xgb_correct = int(sum(xgb_preds_raw == np.array(y_low_raw)))
        xgb_total = len(y_low_raw)
    else:
        xgb_total = 0

    # 策略C: XGBoost全量
    model_full = xgb.XGBClassifier(
        n_estimators=200, max_depth=6, learning_rate=0.05,
        subsample=0.8, colsample_bytree=0.8,
        objective='multi:softprob', random_state=42)
    model_full.fit(X_train, y_train_enc)
    full_preds_enc = model_full.predict(X_test)
    full_preds_raw = le.inverse_transform(full_preds_enc)
    full_correct = int(sum(full_preds_raw == np.array(y_test)))
    full_total = len(y_test)

    # 混合策略: Elo高差距直接判 + XGBoost处理低差距
    hybrid_correct = int(elo_correct + xgb_correct)
    hybrid_total = len(y_test)

    # 结果
    print('特征数: %d | 训练: %d | 测试: %d' % (len(feature_names), len(train_idx), len(test_idx)))
    print()
    print('策略A (Elo>40直接判):   %d/%d = %.0f%% (覆盖%.0f%%)' % (
        elo_correct, elo_total,
        100*elo_correct//max(1,elo_total),
        100*elo_total//len(y_test)))
    print('策略B (XGBoost低差距):   %d/%d = %.0f%% (覆盖%.0f%%)' % (
        xgb_correct, xgb_total,
        100*xgb_correct//max(1,xgb_total),
        100*xgb_total//len(y_test)))
    print('策略C (XGBoost全量):     %d/%d = %.0f%%' % (
        full_correct, full_total, 100*full_correct//full_total))
    print()
    print('混合策略 A+B:            %d/%d = %.0f%%' % (
        hybrid_correct, hybrid_total,
        100*hybrid_correct//hybrid_total))

    # 特征重要性
    importance = sorted(zip(feature_names, model_full.feature_importances_),
                       key=lambda x: -x[1])
    print()
    print('特征重要性 Top 10:')
    for name, imp in importance[:10]:
        print('  %s: %.4f' % (name, imp))

    return hybrid_correct, hybrid_total


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')

    print('收集比赛数据...')
    matches = collect_all_matches()
    print('  %d 场比赛' % len(matches))

    print('构建特征矩阵...')
    X, y, meta = build_features(matches)
    print('  %d 个特征 × %d 行' % (len(X[0]) if X else 0, len(X)))

    print()
    print('=' * 50)
    train_and_evaluate(X, y, meta)
    print('=' * 50)
