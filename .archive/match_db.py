"""比赛数据库 — L1/L2快照存储与对比"""
import json, os
from datetime import datetime

DB_PATH = 'd:/gas-station/match-db.json'

def load_db():
    if os.path.exists(DB_PATH):
        with open(DB_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {'matches': [], 'stats': {}}

def save_db(db):
    with open(DB_PATH, 'w', encoding='utf-8') as f:
        json.dump(db, f, ensure_ascii=False, indent=2)

def save_match(match_id, match_name, match_day, match_result, deadline, cutoff, verdict, scores, details):
    """保存一场比赛的双层快照"""
    db = load_db()

    entry = {
        'id': match_id,
        'name': match_name,
        'day': match_day,
        'result': match_result,
        'deadline': deadline,
        'cutoff': cutoff,
        'saved_at': datetime.now().isoformat(),
        'verdict': verdict,
        'scores': scores,
        'details': details,
        'calibrated': False,
    }

    # 检查是否已存在，存在则更新
    existing = [i for i, m in enumerate(db['matches']) if m['id'] == match_id]
    if existing:
        db['matches'][existing[0]] = entry
    else:
        db['matches'].append(entry)

    # 更新统计
    update_stats(db)
    save_db(db)
    return entry

def update_stats(db):
    matches = db['matches']
    if not matches: return

    total = len(matches)
    skipped = sum(1 for m in matches if m.get('verdict') == '跳过')
    correct = 0
    for m in matches:
        result = m.get('result', '')
        v = m.get('verdict', '')
        # 跳过 = 正确（不买不输）
        if v == '跳过':
            correct += 1
        # 以后可以加更精细的判定

    db['stats'] = {
        'total': total,
        'skipped': skipped,
        'correct': correct,
        'skip_rate': f'{skipped/total:.0%}',
        'last_updated': datetime.now().isoformat(),
    }

def compare_latest(n=3):
    """对比最近N场比赛"""
    db = load_db()
    recent = db['matches'][-n:]

    print(f"\n{'='*60}")
    print(f"最近 {len(recent)} 场对比")
    print(f"{'='*60}")

    for m in recent:
        print(f"\n{m['name']} | {m['result']}")
        s = m['scores']
        print(f"  D1:{s['D1']} D2:{s['D2']} D3:{s['D3']} D4:{s['D4']} D5:{s['D5']} D6:{s['D6']} +{s['D6_bonus']} = {s['total']}/{s['max']}")
        print(f"  判定: {m['verdict']}")

    # 统计
    print(f"\n{db['stats']}")

def add_calibration(match_id, actual_result, notes=''):
    """赛后校准"""
    db = load_db()
    for m in db['matches']:
        if m['id'] == match_id:
            m['calibrated'] = True
            m['actual_result'] = actual_result
            m['calibration_notes'] = notes
            m['calibrated_at'] = datetime.now().isoformat()
            break
    update_stats(db)
    save_db(db)

# ===== 从两份快照保存匹配记录 =====
if __name__ == '__main__':
    # 检查是否有已保存的三场分析
    db = load_db()
    print(f"当前数据库: {len(db['matches'])} 场比赛")
    print(f"统计: {db['stats']}")
    if db['matches']:
        compare_latest(3)
