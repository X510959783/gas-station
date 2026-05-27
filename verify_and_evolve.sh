#!/usr/bin/env bash
# ============================================================
# verify_and_evolve.sh — 赛后验证闭环
# 用法: bash verify_and_evolve.sh [选项]
#   bash verify_and_evolve.sh                           # 交互式输入赛果
#   bash verify_and_evolve.sh --results results.json    # 从JSON文件加载赛果
#   bash verify_and_evolve.sh --auto                    # 自动从文件夹名解析赛果
# ============================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

LOCK_FILE="$SCRIPT_DIR/betting-lock.json"
EVOLUTION_LOG="$SCRIPT_DIR/.claude/evolution/accuracy-log.json"
MEMORY_DIR="$HOME/.claude/projects/d--gas-station/memory"

echo "=========================================="
echo "  赛后验证闭环 — 园中园足彩 v4.0"
echo "=========================================="

# ---- 检查预测文件 ----
if [ ! -f "$LOCK_FILE" ]; then
  echo "❌ 未找到预测文件: $LOCK_FILE"
  echo "   请先运行 auto_pipeline.sh 锁定预测"
  exit 1
fi

echo ""
echo "【步骤1】加载预测..."

python -c "
import json
with open('$LOCK_FILE') as f:
    data = json.load(f)
print(f'  锁定时间: {data[\"locked_at\"]}')
print(f'  截止时间: {data[\"deadline\"]}')
print(f'  总场次: {data[\"total_matches\"]}')
print(f'  单选: {data[\"singles\"]} | 双选: {data[\"doubles\"]} | 跳过: {data[\"skips\"]}')
print()
for i, p in enumerate(data['predictions']):
    print(f'  [{i+1}] {p[\"league\"]} {p[\"match\"][:40]}')
    print(f'      预测: {p[\"decision\"]} ({p[\"badge\"]})')
" 2>/dev/null

# ---- 获取赛果 ----
echo ""
echo "【步骤2】获取赛果..."

MODE="${1:---interactive}"
RESULTS_JSON=""

if [ "$MODE" = "--auto" ]; then
  # 自动模式: 尝试从文件夹名解析赛果
  echo "  自动模式: 从文件夹名解析赛果..."
  # 查找预测中引用的数据目录
  DATA_HINT=$(python -c "
import json
with open('$LOCK_FILE') as f:
    data = json.load(f)
# 从第一个预测中推断
if data['predictions']:
    print(data['predictions'][0].get('match', '')[:30])
" 2>/dev/null)

  echo "  提示: 自动解析尚未完全实现, 请用交互模式输入赛果"
  echo "  使用: bash verify_and_evolve.sh (不带参数)"
  exit 0

elif [ "$MODE" = "--results" ]; then
  RESULTS_JSON="${2:-}"
  if [ ! -f "$RESULTS_JSON" ]; then
    echo "❌ 赛果文件不存在: $RESULTS_JSON"
    exit 1
  fi
  echo "  从文件加载: $RESULTS_JSON"

else
  # 交互模式
  echo "  交互模式: 逐场输入赛果"
  echo "  输入格式: 主胜/平局/客胜 (或 3/1/0)"
  echo ""

  RESULTS_ARRAY=()
  MATCH_COUNT=$(python -c "import json; d=json.load(open('$LOCK_FILE')); print(len(d['predictions']))" 2>/dev/null)

  for i in $(seq 1 $MATCH_COUNT); do
    MATCH_INFO=$(python -c "
import json
with open('$LOCK_FILE') as f:
    p = json.load(f)['predictions'][$((i-1))]
print(f'{p[\"league\"]} {p[\"match\"][:45]} | 预测: {p[\"decision\"]}')
" 2>/dev/null)
    echo -n "  [$i/$MATCH_COUNT] $MATCH_INFO → 实际: "
    read -r actual

    case "$actual" in
      主胜|3|胜|h|H) actual="主胜" ;;
      平局|1|平|d|D) actual="平局" ;;
      客胜|0|负|a|A) actual="客胜" ;;
      *) actual="未输入" ;;
    esac

    RESULTS_ARRAY+=("$actual")
  done

  # 写入临时JSON
  RESULTS_JSON="$SCRIPT_DIR/.tmp_results.json"
  python -c "
import json
results = $(python -c "import json; print(json.dumps(['${RESULTS_ARRAY[@]}']))" 2>/dev/null)
with open('$RESULTS_JSON', 'w') as f:
    json.dump({'results': results}, f, ensure_ascii=False)
" 2>/dev/null
fi

# ---- 比对预测 vs 实际 ----
echo ""
echo "【步骤3】比对结果..."

COMPARISON=$(python -c "
import json, sys

with open('$LOCK_FILE') as f:
    lock = json.load(f)

# 加载赛果
results = []
if '$RESULTS_JSON' and __import__('os').path.exists('$RESULTS_JSON'):
    with open('$RESULTS_JSON') as f:
        results = json.load(f).get('results', [])

predictions = lock['predictions']
total = len(predictions)
correct = 0
wrong = 0
skip = 0
details = []

for i, pred in enumerate(predictions):
    if i >= len(results):
        details.append({'idx': i, 'status': 'no_result', 'pred': pred['decision']})
        continue

    actual = results[i]
    decision = pred['decision']
    ok = False

    # 判断逻辑
    if actual == '未输入':
        details.append({'idx': i, 'status': 'no_input', 'pred': decision, 'actual': actual})
        continue

    if '跳过' in decision:
        skip += 1
        details.append({'idx': i, 'status': 'skip', 'pred': decision, 'actual': actual})
        continue

    # 单选判断
    if '单选主胜' in decision and actual == '主胜':
        ok = True
    elif '单选平局' in decision and actual == '平局':
        ok = True
    elif '单选客胜' in decision and actual == '客胜':
        ok = True
    elif '双选主不败' in decision and actual in ['主胜', '平局']:
        ok = True
    elif '双选客不败' in decision and actual in ['客胜', '平局']:
        ok = True

    if ok:
        correct += 1
        details.append({'idx': i, 'status': 'correct', 'pred': decision, 'actual': actual})
    else:
        wrong += 1
        details.append({'idx': i, 'status': 'wrong', 'pred': decision, 'actual': actual})

rated = correct + wrong
accuracy = 100 * correct / rated if rated > 0 else 0

# 输出比对表
header = f'{\"#\":<4} {\"预测\":<24} {\"实际\":<8} {\"判定\"}'
print(header)
print('-' * 50)
for d in details:
    idx = d['idx']
    pred_short = d['pred'][:22]
    actual = d.get('actual', '?')
    status = d['status']
    icon = {'correct': '✓', 'wrong': '✗', 'skip': '—', 'no_result': '?', 'no_input': '?'}[status]
    print(f'{idx+1:<4} {pred_short:<24} {actual:<8} {icon}')

print()
print(f'  总计: {total}场 | 正确: {correct} | 错误: {wrong} | 跳过: {skip}')
if rated > 0:
    print(f'  单选准确率: {correct}/{rated} = {accuracy:.1f}%')

# 写入进化日志
import datetime
log_entry = {
    'timestamp': datetime.datetime.now().isoformat(),
    'total': total,
    'correct': correct,
    'wrong': wrong,
    'skip': skip,
    'accuracy': round(accuracy, 1),
    'errors': [d for d in details if d['status'] == 'wrong'],
    'pipeline_version': lock.get('pipeline_version', '?'),
}
print()
print(f'  ACCURACY:{accuracy:.1f}%')
print(f'  ERRORS:{len([d for d in details if d[\"status\"] == \"wrong\"])}')
" 2>/dev/null)

# ---- 触发思维博弈 ----
echo ""
echo "【步骤4】触发思维博弈..."

ERROR_COUNT=$(echo "$COMPARISON" | grep "ERRORS:" | cut -d':' -f2 | tr -d ' ')
ACCURACY=$(echo "$COMPARISON" | grep "ACCURACY:" | cut -d':' -f2 | tr -d ' %')

if [ -f "$SCRIPT_DIR/.claude/scripts/thought-game.sh" ]; then
  echo "  运行 thought-game.sh 逐场复盘..."
  # 对每场错误触发深度复盘
  if [ "${ERROR_COUNT:-0}" -gt 0 ]; then
    echo "  发现 $ERROR_COUNT 场错误, 启动深度复盘..."
    bash "$SCRIPT_DIR/.claude/scripts/thought-game.sh" || true
  else
    echo "  全部正确! 仍然触发复盘(规则0B: 对了≠推理对了)"
    bash "$SCRIPT_DIR/.claude/scripts/thought-game.sh" || true
  fi
else
  echo "  ⚠️ thought-game.sh 不存在, 跳过思维博弈"
fi

# ---- 触发碰撞引擎 ----
echo ""
echo "【步骤5】触发自进化碰撞引擎..."

if [ -f "$SCRIPT_DIR/.claude/scripts/collision-engine.sh" ]; then
  echo "  运行 collision-engine.sh 检测框架偏差..."
  bash "$SCRIPT_DIR/.claude/scripts/collision-engine.sh" || true
else
  echo "  ⚠️ collision-engine.sh 不存在, 跳过碰撞"
fi

# ---- 更新准确率日志 ----
echo ""
echo "【步骤6】更新进化日志..."

python -c "
import json, os
from datetime import datetime

log_file = '$EVOLUTION_LOG'
os.makedirs(os.path.dirname(log_file), exist_ok=True)

# 加载现有日志
if os.path.exists(log_file):
    with open(log_file) as f:
        try:
            history = json.load(f)
        except:
            history = {'records': []}
else:
    history = {'records': []}

# 追加新记录
history['records'].append({
    'date': datetime.now().strftime('%Y-%m-%d'),
    'time': datetime.now().strftime('%H:%M'),
    'accuracy': $ACCURACY,
    'correct': $(echo "$COMPARISON" | grep '正确:' | grep -oP '\d+' | head -1),
    'total_rated': $(( $(echo "$COMPARISON" | grep '正确:' | grep -oP '\d+' | head -1) + ${ERROR_COUNT:-0} )),
    'errors': ${ERROR_COUNT:-0},
    'version': 'v4.0',
})

# 计算滚动准确率
records = history['records']
if len(records) >= 5:
    last5 = [r['accuracy'] for r in records[-5:]]
    avg5 = sum(last5) / len(last5)
    print(f'  近5批滚动准确率: {avg5:.1f}%')
    print(f'  趋势: {\"📈上升\" if len(last5) >= 2 and last5[-1] > last5[0] else \"📉下降\" if last5[-1] < last5[0] else \"➡️平稳\"}')

with open(log_file, 'w') as f:
    json.dump(history, f, ensure_ascii=False, indent=2)
print(f'  日志已更新: $EVOLUTION_LOG')
" 2>/dev/null

# ---- 清理 ----
rm -f "$SCRIPT_DIR/.tmp_results.json" 2>/dev/null

echo ""
echo "=========================================="
echo "  验证闭环完成"
echo "  准确率: ${ACCURACY:-?}%"
echo "  错误数: ${ERROR_COUNT:-?}"
echo "  进化日志: $EVOLUTION_LOG"
echo "=========================================="
