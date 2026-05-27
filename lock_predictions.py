# -*- coding: utf-8 -*-
"""预测锁定器 — 独立于bash, 直接生成 betting-lock.json
用法: python lock_predictions.py <数据目录> [--fast]
"""
import sys, os, re, json, time
sys.path.insert(0, os.path.dirname(__file__))

from framework_v4 import analyze_match
from config_loader import load as load_config


def detect_league(fname):
    for lg in ['挪超', '瑞超', '德甲', '英超', '意甲', '西甲', '日职', '英甲']:
        if lg in fname:
            return lg
    return '其他'


def extract_teams(folder_name):
    """从文件夹名提取主客队名
    支持格式:
    - '斯达 vs 瓦勒伦加'
    - '周一001挪超斯达 2-0 瓦勒伦加...'
    - '周日004瑞超05-24 20.00哈马比 1.2 索尔纳'
    """
    name = folder_name.strip()

    # 方式1: VS/vs 分割
    for sep in [' VS ', ' vs ', 'VS', 'vs']:
        if sep in name:
            parts = name.split(sep)
            h = __import__('re').sub(r'\s*\d+[\.\-:：]\d+\s*$', '', parts[0]).strip()
            a = __import__('re').sub(r'^\d+[\.\-:：]\d+\s*', '', parts[1]).strip()
            if h and a:
                return clean_team_name(h), clean_team_name(a)

    # 方式2: 比分模式分割
    # 去掉日期时间避免误匹配 (05-26, 20.30, 01.15 等)
    cleaned = __import__('re').sub(
        r'\d{2}[\.\-:：]\d{2}\s+(?:\d{2}[\.:：]\d{2})?', ' ', name)
    cleaned = __import__('re').sub(r'\[\d+\]', '', cleaned)
    cleaned = __import__('re').sub(r'已入库', '', cleaned)
    # 找比分: 数字 分隔符 数字 (比分通常是一位或两位数字)
    score_match = __import__('re').search(
        r'([^\d])(\d{1,2})\s*[\.\-:：]?\s*(\d{1,2})([^\d])', cleaned)
    if not score_match:
        # 尝试"11"型(两数字紧邻中间只有空格): 找空格包围的两个数字
        score_match = __import__('re').search(
            r'\s+(\d)\s+(\d)\s+', cleaned)
    if score_match:
        left = name[:score_match.start()].strip()
        right = name[score_match.end():].strip()

        # 左边去掉编号前缀、联赛名、日期时间、排名
        h = clean_team_name(left)
        a = clean_team_name(right)

        # 从左边提取最后的连续文字作为主队名
        # 例如: '周一001挪超斯达' → '斯达'
        h_chars = __import__('re').findall(r'[一-鿿\w]+', h)
        if h_chars:
            h = h_chars[-1]  # 取最后一段中文
        a_chars = __import__('re').findall(r'[一-鿿\w]+', a)
        if a_chars:
            a = a_chars[0]  # 取第一段中文

        if h and a and len(h) > 0 and len(a) > 0:
            return h, a

    return '?', '?'


def clean_team_name(raw):
    """清理队名: 去掉编号、联赛名、日期、排名、比分"""
    s = raw.strip()
    # 去掉周xNNN 编号
    s = __import__('re').sub(r'^周[一二三四五六日]\d+', '', s).strip()
    # 去掉纯数字开头
    s = __import__('re').sub(r'^\d+\s*', '', s).strip()
    # 去掉日期 05-25
    s = __import__('re').sub(r'\d{2}[\.\-:：]\d{2}\s*', '', s).strip()
    # 去掉时间 20.30
    s = __import__('re').sub(r'\d{2}[\.:：]\d{2}', '', s).strip()
    # 去掉联赛名 (用完整匹配而非子串)
    leagues = ['挪超', '瑞超', '德甲', '英超', '意甲', '西甲', '日职', '英甲',
               '法甲', '荷甲', '葡超', '巴甲', '阿甲', '美职', '日乙', '韩职',
               '澳超', '俄超', '欧冠', '欧联', '欧协联', '解放者杯', '德丙联', '法乙',
               '瑞典超', '日职联']
    for lg in leagues:
        if s.startswith(lg):
            s = s[len(lg):].strip()
        elif lg in s:
            # 联赛名通常在开头或中间
            idx = s.find(lg)
            if idx < 5:  # 联赛名靠近开头则去掉
                s = s[idx + len(lg):].strip()
    # 去掉方括号排名 [14]
    s = __import__('re').sub(r'\[\d+\]', '', s).strip()
    # 去掉比分 2-0 / 1.1 等
    s = __import__('re').sub(r'\d+[\.\-:：]\d+\s*', '', s).strip()
    # 去掉后缀 '已入库'
    s = s.replace('已入库', '').strip()
    return s


def load_search_cache(home, away, league):
    """加载缓存的L3搜索数据"""
    if home == '?' or away == '?':
        return None
    cache_dir = os.path.join(os.path.dirname(__file__), '.search_cache')
    key = f'{league}_{home}_{away}'
    key = re.sub(r'[<>:"/\\|?*\s]+', '_', key)[:80]
    cache_file = os.path.join(cache_dir, f'{key}.json')
    if os.path.exists(cache_file):
        from l3_search_bridge import export_search_data
        return export_search_data(home, away, league)
    return None


def run_pipeline(data_dir, fast_mode=False):
    """主管道: 扫描→分析→锁定"""
    cfg = load_config()

    predictions = []
    singles = doubles = skips = 0

    for folder in sorted(os.listdir(data_dir)):
        full = os.path.join(data_dir, folder)
        if not os.path.isdir(full):
            continue

        lg = detect_league(folder)

        # 提取主客队名
        home, away = '?', '?'
        meta_file = os.path.join(full, 'match_info.json')
        if os.path.exists(meta_file):
            with open(meta_file, 'r', encoding='utf-8') as f:
                meta = json.load(f)
            home = meta.get('home', '?')
            away = meta.get('away', '?')
            lg = meta.get('league', lg)
        else:
            home, away = extract_teams(folder)

        search_data = load_search_cache(home, away, lg)

        # 碰撞#37: 如果无缓存, 尝试从500.com自动抓取球队战绩
        if not search_data and meta_file and os.path.exists(meta_file):
            with open(meta_file, 'r', encoding='utf-8') as f:
                meta = json.load(f)
            mid = meta.get('id', '')
            if mid:
                try:
                    from auto_search import inject_cache
                    inject_cache(mid)
                    search_data = load_search_cache(home, away, lg)
                except Exception:
                    pass  # 静默失败, 继续用 None

        try:
            result = analyze_match(full, lg, search_data)
        except Exception as e:
            predictions.append({
                'match': folder[:50],
                'league': lg,
                'decision': f'错误: {str(e)[:40]}',
                'pick_type': '错误',
                'badge': 'Error'
            })
            skips += 1
            continue

        pick_type = result.get('pick_type', '跳过')
        badge = result.get('badge', '?')
        confidence = result.get('confidence', 40)

        # 碰撞#37: Poisson交叉验证 (Rule 0B第二路径)
        # 仅在非L1激活时运行 (L1=Stable, 不需要交叉验证)
        if badge != 'Stable':
            try:
                from poisson_crosscheck import run_crosscheck
                sig = result.get('signals', {})
                cc = run_crosscheck(sig, search_data, None)
                confidence += cc.get('confidence_boost', 0)
                if cc.get('agreement') == 'full':
                    badge = 'Stable' if confidence >= 70 else 'Correct'
            except Exception:
                pass

        # 碰撞#37: 冷门防御检测
        cold_door_warning = None
        if pick_type == '单选' and '主胜' in result.get('decision', ''):
            try:
                from cold_door_detector import detect_cold_door_risk
                sig = result.get('signals', {})
                cd_result = detect_cold_door_risk(sig, search_data)
                if cd_result.get('should_flip_direction'):
                    badge = 'ColdDoor'
                    cold_door_warning = cd_result
                    # 翻方向: 主胜 → 客不败
                    result['decision'] = result['decision'].replace(
                        '主胜', '冷门预警-客不败')
                    cd_score = cd_result['risk_score']
                    result['thought_chain'].append(
                        'CD: 风险评分%d->翻客不败' % cd_score)
            except Exception:
                pass

        # 最终置信度: 保留L1的Stable, 其他按分值重新分级
        if badge == 'Stable':
            final_badge = 'Stable'  # L1激活不受后处理影响
        elif badge == 'ColdDoor':
            final_badge = 'ColdDoor'
        elif confidence >= 70:
            final_badge = 'Stable'
        elif confidence >= 45:
            final_badge = 'Correct'
        elif confidence >= 20:
            final_badge = 'Risk'
        else:
            final_badge = 'Low'

        if pick_type == '单选': singles += 1
        elif pick_type == '双选': doubles += 1
        else: skips += 1

        predictions.append({
            'match': folder[:60],
            'league': lg,
            'decision': result['decision'],
            'pick_type': pick_type,
            'badge': final_badge,
            'confidence': confidence,
            'layers': '→'.join(result.get('layers', [])),
            'has_search_data': search_data is not None,
            'cold_door_risk': (
                cold_door_warning['risk_level'] if cold_door_warning else None),
        })

    # 生成锁定文件
    lock = {
        'locked_at': time.strftime('%Y-%m-%d %H:%M:%S'),
        'pipeline_version': cfg.get('version', '4.0'),
        'mode': 'fast' if fast_mode else 'normal',
        'total_matches': len(predictions),
        'singles': singles,
        'doubles': doubles,
        'skips': skips,
        'predictions': predictions,
    }

    lock_file = os.path.join(os.path.dirname(__file__), 'betting-lock.json')
    with open(lock_file, 'w', encoding='utf-8') as f:
        json.dump(lock, f, ensure_ascii=False, indent=2)

    return lock


def print_summary(lock):
    """打印预测摘要"""
    print('=' * 60)
    print('  预测锁定完成')
    print('=' * 60)
    print(f'  锁定时间: {lock["locked_at"]}')
    print(f'  总场次: {lock["total_matches"]}')
    print(f'  单选: {lock["singles"]} | 双选: {lock["doubles"]} | 跳过: {lock["skips"]}')
    print()

    for i, p in enumerate(lock['predictions']):
        has_sd = '🔍' if p.get('has_search_data') else '  '
        print(f'  [{i+1}] {p["league"]} {p["match"][:35]}')
        print(f'      {has_sd} {p["decision"]} [{p["badge"]}]')

    # 2串1推荐
    singles = [p for p in lock['predictions'] if p['pick_type'] == '单选']
    n = len(singles)

    print(f'\n--- 2串1组合 ({n}场单选, {n*(n-1)//2}种组合, 每种2元) ---')
    if n >= 2:
        badge_order = {'Stable': 0, 'Correct': 1, 'Risk': 2, 'Error': 99}
        singles.sort(key=lambda p: badge_order.get(p['badge'], 99))

        shown = 0
        for i in range(min(6, n)):
            for j in range(i+1, min(6, n)):
                if shown >= 10:
                    break
                a, b = singles[i], singles[j]
                print(f'  [{a["badge"]}+{b["badge"]}] 2元 | '
                      f'{a["decision"]} × {b["decision"]} | '
                      f'{a["match"][:20]} + {b["match"][:20]}')
                shown += 1
            if shown >= 10:
                break
        print(f'  显示 {shown}/{(n*(n-1)//2)} 组, 全部投注需 {shown*2} 元')
    else:
        print('  单选不足2场, 无法组2串1')
    print('=' * 60)


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')

    data_dir = sys.argv[1] if len(sys.argv) > 1 else None
    fast_mode = '--fast' in sys.argv

    if not data_dir:
        print('用法: python lock_predictions.py <数据目录> [--fast]')
        sys.exit(1)

    if not os.path.isdir(data_dir):
        print(f'目录不存在: {data_dir}')
        sys.exit(1)

    lock = run_pipeline(data_dir, fast_mode)
    print_summary(lock)
