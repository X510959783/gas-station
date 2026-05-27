# -*- coding: utf-8 -*-
"""赛果自动获取器 — 从500.com比赛页面提取最终比分
用法:
  python fetch_results.py <match_id>              # 单个比赛
  python fetch_results.py --batch <lock_file>    # 批量: 从预测文件提取所有结果
  python fetch_results.py --verify <lock_file>   # 获取结果并自动验证
"""
import sys, os, re, json, time, urllib.request
import proxy_config

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'text/html,application/xhtml+xml',
}


def fetch_match_page(match_id):
    """获取比赛页面HTML"""
    url = f'https://odds.500.com/fenxi/ouzhi-{match_id}.shtml'
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=30) as resp:
        raw = resp.read()
    for enc in ['gb2312', 'gbk', 'utf-8', 'gb18030']:
        try:
            return raw.decode(enc)
        except (UnicodeDecodeError, LookupError):
            continue
    return raw.decode('utf-8', errors='replace')


def extract_score(html):
    """从HTML中提取最终比分
    500.com赛后页面结构:
      <div class='...game...'>比赛时间2026-05-25 20:30</p>
      <p class='odds_hd_bf'><strong>2:0</strong></p></div>
    返回: (主队进球, 客队进球) 或 (None, None)
    """
    # 方法1: class='odds_hd_bf' 中的比分 (最精确)
    bf_match = re.search(
        r"class=['\"]odds_hd_bf['\"][^>]*>\s*<strong>\s*(\d+)\s*:\s*(\d+)\s*</strong>",
        html)
    if bf_match:
        return int(bf_match.group(1)), int(bf_match.group(2))

    # 方法2: 在 div.game 区域内找 strong 标签中的比分
    game_section = re.search(
        r"class=['\"][^'\"]*game[^'\"]*['\"][^>]*>(.*?)</div>",
        html, re.DOTALL)
    if game_section:
        gs = game_section.group(1)
        strong_score = re.search(r'<strong>\s*(\d+)\s*:\s*(\d+)\s*</strong>', gs)
        if strong_score:
            return int(strong_score.group(1)), int(strong_score.group(2))

    # 方法3: 纯文本中搜索 比赛时间...分数:分数
    text = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'&nbsp;', ' ', text)
    text = re.sub(r'\s+', ' ', text)

    # 比赛时间后面跟的比分
    time_score = re.search(
        r'比赛时间\s*\d{4}-\d{2}-\d{2}\s+\d{1,2}:\d{2}\s+(\d+)\s*:\s*(\d+)',
        text)
    if time_score:
        return int(time_score.group(1)), int(time_score.group(2))

    return None, None


def score_to_result(home_goals, away_goals):
    """比分转赛果"""
    if home_goals is None:
        return '?'
    if home_goals > away_goals:
        return '主胜'
    elif home_goals == away_goals:
        return '平局'
    else:
        return '客胜'


def verify_predictions(lock_file):
    """自动验证预测 vs 实际"""
    with open(lock_file, 'r', encoding='utf-8') as f:
        lock = json.load(f)

    results = []
    correct = wrong = skip = no_result = 0

    print(f'自动验证 {len(lock["predictions"])} 场比赛...')
    print()

    for i, pred in enumerate(lock['predictions']):
        # 从 match 字段提取比赛ID (如果有的话)
        match_name = pred.get('match', '')
        # 尝试提取 match_info.json 中的 ID
        # 对于没有ID的老数据，显示需要手动输入
        mid = pred.get('match_id', None)

        if not mid:
            no_result += 1
            results.append({
                **pred,
                'actual': '?',
                'result': 'no_id',
                'verdict': '?'
            })
            print(f'  [{i+1}] {pred["league"]} {match_name[:30]} → 无match_id, 需手动输入')
            continue

        # 获取赛果
        try:
            html = fetch_match_page(mid)
            hg, ag = extract_score(html)
            time.sleep(0.5)  # 礼貌延迟
        except Exception as e:
            no_result += 1
            results.append({
                **pred,
                'actual': '?',
                'result': f'error: {str(e)[:30]}',
                'verdict': '?'
            })
            print(f'  [{i+1}] {match_name[:30]} → 获取失败: {e}')
            continue

        if hg is None:
            no_result += 1
            results.append({
                **pred,
                'actual': '?',
                'result': 'no_score',
                'verdict': '?'
            })
            print(f'  [{i+1}] {match_name[:30]} → 未提取到比分 (比赛可能未开始)')
            continue

        actual = score_to_result(hg, ag)
        decision = pred.get('decision', '')

        # 判断对错
        ok = False
        if '单选主胜' in decision and actual == '主胜': ok = True
        elif '单选平局' in decision and actual == '平局': ok = True
        elif '单选客胜' in decision and actual == '客胜': ok = True
        elif '跳过' in decision:
            skip += 1
            ok = None

        verdict = '✓' if ok else ('✗' if ok is False else '—')
        if ok: correct += 1
        elif ok is False: wrong += 1

        results.append({
            **pred,
            'actual': actual,
            'score': f'{hg}-{ag}',
            'verdict': verdict,
        })

        print(f'  [{i+1}] {match_name[:30]} → {hg}-{ag} ({actual}) vs {decision} {verdict}')

    # 更新准确率
    rated = correct + wrong
    accuracy = round(100 * correct / rated, 1) if rated > 0 else 0

    print()
    print(f'  总场次: {len(results)}')
    print(f'  正确: {correct} | 错误: {wrong} | 跳过: {skip} | 无结果: {no_result}')
    if rated > 0:
        print(f'  准确率: {correct}/{rated} = {accuracy}%')

    # 更新锁定文件
    lock['verified_at'] = time.strftime('%Y-%m-%d %H:%M:%S')
    lock['results'] = results
    lock['accuracy'] = accuracy
    lock['correct'] = correct
    lock['wrong'] = wrong
    lock['no_result'] = no_result

    verified_file = lock_file.replace('.json', '_verified.json')
    with open(verified_file, 'w', encoding='utf-8') as f:
        json.dump(lock, f, ensure_ascii=False, indent=2)

    print(f'  验证结果已保存: {verified_file}')
    return lock


# ========== 主入口 ==========
if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')

    if len(sys.argv) < 2:
        print('用法:')
        print('  python fetch_results.py <match_id>')
        print('  python fetch_results.py --verify <lock_file>')
        sys.exit(0)

    if sys.argv[1] == '--verify':
        lock_file = sys.argv[2] if len(sys.argv) > 2 else 'betting-lock.json'
        if not os.path.exists(lock_file):
            print(f'锁定文件不存在: {lock_file}')
            sys.exit(1)
        verify_predictions(lock_file)

    elif sys.argv[1] == '--batch':
        lock_file = sys.argv[2] if len(sys.argv) > 2 else 'betting-lock.json'
        verify_predictions(lock_file)

    else:
        # 单场模式
        mid = sys.argv[1]
        print(f'获取比赛 {mid} 赛果...')
        html = fetch_match_page(mid)
        hg, ag = extract_score(html)
        if hg is not None:
            result = score_to_result(hg, ag)
            print(f'  比分: {hg}-{ag}')
            print(f'  赛果: {result}')
        else:
            print('  未提取到比分 (比赛可能未开始或页面结构已变)')
