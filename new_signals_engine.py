# -*- coding: utf-8 -*-
"""新信号引擎 — 接入 datafc + auto_search + 500.com团队数据
给框架追加: 球队排名差、进球率、近期战绩、主场优势
"""
import sys, os, re, json

SCRIPT_DIR = os.path.dirname(__file__)
CACHE_FILE = os.path.join(SCRIPT_DIR, '.new_signals_cache.json')


def get_standings_signal(league_name):
    """从datafc获取联赛积分榜→提取排名和进球数据"""
    # Sofascore tournament IDs
    TOURNAMENT_MAP = {
        '挪超': 20, '英超': 17, '德甲': 35, '意甲': 23,
        '西甲': 8, '法甲': 34, '瑞超': 36, '荷甲': 37,
        '葡超': 32, '解放者杯': 325, '美职': 242,
    }
    tid = TOURNAMENT_MAP.get(league_name)
    if not tid:
        return None

    try:
        from datafc import seasons_data, standings_data
        seasons = seasons_data(tournament_id=tid)
        if len(seasons) == 0:
            return None
        latest = int(seasons.iloc[0]['season_id'])
        st = standings_data(tournament_id=tid, season_id=latest)
        return st
    except Exception:
        return None


def get_team_signals(league_name, home_team, away_team):
    """获取两队的关键统计信号
    返回: {home_rank, away_rank, rank_diff, home_goals_per_game,
           away_goals_per_game, home_form_recent, away_form_recent, ...}
    """
    st = get_standings_signal(league_name)
    if st is None:
        return None

    signals = {}

    # 找主队数据
    home_row = st[st['team_name'].str.contains(
        home_team[:3], case=False, na=False)]
    away_row = st[st['team_name'].str.contains(
        away_team[:3], case=False, na=False)]

    if len(home_row) > 0:
        hr = home_row.iloc[0]
        signals['home_rank'] = int(hr.get('position', 0))
        signals['home_points'] = int(hr.get('points', 0))
        signals['home_goals_for'] = int(hr.get('scores_for', 0))
        signals['home_goals_against'] = int(hr.get('scores_against', 0))
        matches_played = int(hr.get('matches', 1))
        signals['home_goals_per_game'] = round(
            signals['home_goals_for'] / max(1, matches_played), 2)
        signals['home_points_per_game'] = round(
            signals['home_points'] / max(1, matches_played), 2)

    if len(away_row) > 0:
        ar = away_row.iloc[0]
        signals['away_rank'] = int(ar.get('position', 0))
        signals['away_points'] = int(ar.get('points', 0))
        signals['away_goals_for'] = int(ar.get('scores_for', 0))
        signals['away_goals_against'] = int(ar.get('scores_against', 0))
        matches_played = int(ar.get('matches', 1))
        signals['away_goals_per_game'] = round(
            signals['away_goals_for'] / max(1, matches_played), 2)
        signals['away_points_per_game'] = round(
            signals['away_points'] / max(1, matches_played), 2)

    # 排名差 (正=主队排名更高/更差取决于position越小越好)
    if 'home_rank' in signals and 'away_rank' in signals:
        signals['rank_diff'] = signals['away_rank'] - signals['home_rank']
        # 正=主队排名更好

    # 进球差
    if 'home_goals_per_game' in signals and 'away_goals_per_game' in signals:
        signals['goal_rate_diff'] = round(
            signals['home_goals_per_game'] - signals['away_goals_per_game'], 2)

    return signals if len(signals) >= 3 else None


def compute_new_signals(folder_path, league, home_team='', away_team=''):
    """综合新信号: 球队排名 + 进球率 + 近期战绩
    返回: 可直接合并到 framework signals 的 dict
    """
    sig = {}

    # 1. 积分榜信号
    if home_team and away_team:
        team_sig = get_team_signals(league, home_team, away_team)
        if team_sig:
            sig.update(team_sig)

    # 2. 球队近期战绩 (从500.com团队页面)
    if home_team or away_team:
        try:
            from auto_search import scrape_team_form
            # 从match_info.json提取球队ID
            mf = os.path.join(folder_path, 'match_info.json')
            if os.path.exists(mf):
                with open(mf, 'r', encoding='utf-8') as f:
                    meta = json.load(f)
                # 尝试从HTML提取球队ID
                for fname in os.listdir(folder_path):
                    if fname.endswith('.html'):
                        with open(os.path.join(folder_path, fname), 'r',
                                  encoding='utf-8', errors='replace') as fh:
                            html = fh.read(5000)
                        ids = re.findall(r'team/(\d+)/', html)
                        if len(ids) >= 2:
                            hd = scrape_team_form(ids[0], 5)
                            ad = scrape_team_form(ids[1], 5)
                            if hd:
                                sig['home_recent_form'] = hd.get('recent_form', '')
                                sig['home_home_win_rate'] = hd.get('home_win_rate', 0)
                                sig['home_home_draw_rate'] = hd.get('home_draw_rate', 0)
                            if ad:
                                sig['away_recent_form'] = ad.get('recent_form', '')
                                sig['away_away_win_rate'] = ad.get('away_win_rate', 0)
                                sig['away_away_draw_rate'] = ad.get('away_draw_rate', 0)
                            break
        except Exception:
            pass

    return sig


def enhance_framework_prediction(folder_path, league, framework_result):
    """用新信号增强框架预测: 调整置信度, 检测矛盾信号
    返回: {confidence_adj, warning, ...}
    """
    sig = framework_result.get('signals', {})
    decision = framework_result.get('decision', '')
    new = compute_new_signals(folder_path, league)

    adj = {'confidence_adj': 0, 'warnings': []}

    if not new:
        return adj

    # 排名信号 vs 框架方向
    rank_diff = new.get('rank_diff', 0)
    if rank_diff > 5 and '客胜' in decision:
        adj['warnings'].append('主队排名远高于客队但框架选客胜')
        adj['confidence_adj'] -= 10
    elif rank_diff < -5 and '主胜' in decision:
        adj['warnings'].append('客队排名远高于主队但框架选主胜')
        adj['confidence_adj'] -= 10
    elif rank_diff > 5 and '主胜' in decision:
        adj['confidence_adj'] += 5  # 排名与框架一致
    elif rank_diff < -5 and '客胜' in decision:
        adj['confidence_adj'] += 5

    # 进球率信号
    goal_diff = new.get('goal_rate_diff', 0)
    if goal_diff > 0.5 and '主胜' in decision:
        adj['confidence_adj'] += 5
    elif goal_diff < -0.5 and '客胜' in decision:
        adj['confidence_adj'] += 5

    # 近期战绩信号
    hwr = new.get('home_home_win_rate', 0)
    awr = new.get('away_away_win_rate', 0)
    if hwr > 0.6 and '主胜' in decision:
        adj['confidence_adj'] += 5
    if awr > 0.5 and '客胜' in decision:
        adj['confidence_adj'] += 5

    return adj


# ========== 自检 ==========
if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')

    print('测试: 挪超球队统计信号')
    sig = get_team_signals('挪超', 'Bodo', 'Viking')
    if sig:
        for k, v in sorted(sig.items()):
            print('  %s: %s' % (k, v))
    else:
        print('  未能获取信号 (datafc API或网络问题)')
