#!/usr/bin/env bash
# ============================================================
# auto_pipeline.sh — 赛前一键管道
# 用法: bash auto_pipeline.sh <数据目录> [联赛]
# 示例: bash auto_pipeline.sh "D:/足彩/2026.5.27" 挪超
#       bash auto_pipeline.sh "D:/足彩/2026.5.27"          # 自动检测联赛
# ============================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# ---- 参数 ----
DATA_DIR="${1:-}"
LEAGUE="${2:-}"

if [ -z "$DATA_DIR" ]; then
  echo "用法: bash auto_pipeline.sh <数据目录> [联赛]"
  echo "示例: bash auto_pipeline.sh 'D:/足彩/2026.5.27' 挪超"
  exit 1
fi

if [ ! -d "$DATA_DIR" ]; then
  echo "❌ 数据目录不存在: $DATA_DIR"
  exit 1
fi

# ---- 截止时间检测 ----
DOW=$(date +%u)  # 1=Mon, 7=Sun
HOUR=$(date +%H)
MINUTE=$(date +%M)
NOW_MINUTES=$((10#$HOUR * 60 + 10#$MINUTE))

if [ "$DOW" -ge 6 ]; then
  # 周末: 22:30截止
  DEADLINE="22:30"
  DEADLINE_MINUTES=$((22 * 60 + 30))
else
  # 周中: 21:30截止
  DEADLINE="21:30"
  DEADLINE_MINUTES=$((21 * 60 + 30))
fi

REMAINING=$((DEADLINE_MINUTES - NOW_MINUTES))

echo "=========================================="
echo "  赛前分析管道 — 园中园足彩框架 v4.0"
echo "=========================================="
echo "  数据目录: $DATA_DIR"
echo "  截止时间: $DEADLINE"
echo "  剩余时间: $((REMAINING / 60))时$((REMAINING % 60))分"
echo "=========================================="

# 截止时间已过?
if [ "$REMAINING" -le 0 ]; then
  echo ""
  echo "🔴 截止时间已过! 当前时间: $(date +%H:%M)"
  echo "   截止时间: $DEADLINE"
  echo "   拒绝执行——规则0D: 错过截止=一切归零"
  exit 2
fi

# T-30min 快速模式
if [ "$REMAINING" -le 30 ]; then
  echo ""
  echo "⚠️  距截止不足30分钟——切换快速模式"
  echo "   跳过碰撞验证, 直接输出预测"
  FAST_MODE=true
else
  FAST_MODE=false
fi

# T-15min 警告
if [ "$REMAINING" -le 15 ]; then
  echo ""
  echo "🔴🔴 距截止不足15分钟! 立即锁定预测!"
fi

# ---- 联赛自动检测 ----
detect_league() {
  local fname="$1"
  if echo "$fname" | grep -q "挪超"; then echo "挪超"
  elif echo "$fname" | grep -q "瑞超"; then echo "瑞超"
  elif echo "$fname" | grep -q "德甲"; then echo "德甲"
  elif echo "$fname" | grep -q "英超"; then echo "英超"
  elif echo "$fname" | grep -q "意甲"; then echo "意甲"
  elif echo "$fname" | grep -q "西甲"; then echo "西甲"
  elif echo "$fname" | grep -q "日职"; then echo "日职"
  elif echo "$fname" | grep -q "英甲"; then echo "英甲"
  else echo "其他"
  fi
}

# ---- 扫描比赛文件夹 ----
echo ""
echo "【步骤1】扫描比赛文件夹..."

MATCH_DIRS=()
while IFS= read -r d; do
  MATCH_DIRS+=("$d")
done < <(find "$DATA_DIR" -maxdepth 1 -type d | tail -n +2 | sort)

if [ ${#MATCH_DIRS[@]} -eq 0 ]; then
  echo "❌ 未找到比赛文件夹"
  exit 3
fi

echo "  找到 ${#MATCH_DIRS[@]} 场比赛"

# ---- 逐场分析 ----
echo ""
echo "【步骤2】逐场分析 (framework_v4 原生单选引擎)..."

PREDICTIONS=()
SINGLES=0
DOUBLES=0
SKIPS=0

for dir in "${MATCH_DIRS[@]}"; do
  fname=$(basename "$dir")

  # 跳过非比赛文件夹
  if echo "$fname" | grep -qv "VS\|vs"; then
    if echo "$fname" | grep -qv "挪超\|瑞超\|德甲\|英超\|意甲\|西甲\|日职\|英甲"; then
      continue
    fi
  fi

  if [ -z "$LEAGUE" ]; then
    LG=$(detect_league "$fname")
  else
    LG="$LEAGUE"
  fi

  echo -n "  分析: $(echo "$fname" | cut -c1-40)..."

  # 调用框架
  RESULT=$(python -c "
import sys; sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, '$SCRIPT_DIR')
from framework_v4 import analyze_match
r = analyze_match('$dir', '$LG')
print(f'{r[\"decision\"]}|{r[\"pick_type\"]}|{r[\"badge\"]}')
" 2>/dev/null) || {
    echo " ❌ 解析失败"
    continue
  }

  DECISION=$(echo "$RESULT" | cut -d'|' -f1)
  PICK_TYPE=$(echo "$RESULT" | cut -d'|' -f2)
  BADGE=$(echo "$RESULT" | cut -d'|' -f3)

  case "$PICK_TYPE" in
    单选) SINGLES=$((SINGLES + 1)) ;;
    双选) DOUBLES=$((DOUBLES + 1)) ;;
    *) SKIPS=$((SKIPS + 1)) ;;
  esac

  echo " $DECISION [$BADGE]"

  PREDICTIONS+=("{\"match\": \"$(echo "$fname" | cut -c1-50)\", \"league\": \"$LG\", \"decision\": \"$DECISION\", \"pick_type\": \"$PICK_TYPE\", \"badge\": \"$BADGE\"}")
done

# ---- 生成预测锁定文件 ----
LOCK_FILE="$SCRIPT_DIR/betting-lock.json"

echo ""
echo "【步骤3】锁定预测..."

# 提取编号函数
extract_num() {
  local fname="$1"
  if echo "$fname" | grep -oP '^\w+(\d+)' | head -1; then
    echo "$fname" | grep -oP '^\w+(\d+)' | head -1
  elif echo "$fname" | grep -oP '周[一二三四五六日](\d+)' | head -1; then
    echo "$fname" | grep -oP '周[一二三四五六日](\d+)' | head -1
  else
    echo "$fname" | head -c 10
  fi
}

cat > "$LOCK_FILE" << LOCKEOF
{
  "locked_at": "$(date '+%Y-%m-%d %H:%M:%S')",
  "deadline": "$(date '+%Y-%m-%d') $DEADLINE",
  "pipeline_version": "v4.0",
  "mode": "$([ "$FAST_MODE" = true ] && echo 'fast' || echo 'normal')",
  "total_matches": ${#PREDICTIONS[@]},
  "singles": $SINGLES,
  "doubles": $DOUBLES,
  "skips": $SKIPS,
  "predictions": [
LOCKEOF

for i in "${!PREDICTIONS[@]}"; do
  if [ $i -lt $((${#PREDICTIONS[@]} - 1)) ]; then
    echo "    ${PREDICTIONS[$i]}," >> "$LOCK_FILE"
  else
    echo "    ${PREDICTIONS[$i]}" >> "$LOCK_FILE"
  fi
done

cat >> "$LOCK_FILE" << LOCKEOF
  ],
  "status": "locked"
}
LOCKEOF

echo "  预测已锁定: $LOCK_FILE"
echo "  单选: $SINGLES | 双选: $DOUBLES | 跳过: $SKIPS"

# ---- 2串1组合建议 ----
echo ""
echo "【步骤4】2串1组合建议 (单选×单选=2元)..."

python -c "
import json, sys
sys.stdout.reconfigure(encoding='utf-8')
with open('$LOCK_FILE', encoding='utf-8') as f:
    data = json.load(f)

singles = [(i, p) for i, p in enumerate(data['predictions']) if p.get('pick_type') == '单选']
n = len(singles)

print(f'  {n}场单选, 可组 {n*(n-1)//2} 种2串1, 每种成本2元')
print()

if n >= 2:
    # Stable > Correct > Risk 排序
    badge_order = {'Stable': 0, 'Correct': 1, 'Risk': 2}
    singles.sort(key=lambda x: badge_order.get(x[1].get('badge', 'Risk'), 99))

    # 推荐: Stable+Stable, Stable+Correct, Correct+Correct (最多10组)
    print('  推荐组合:')
    count = 0
    for i in range(min(6, n)):
        for j in range(i+1, min(6, n)):
            if count >= 10: break
            s1 = singles[i][1]
            s2 = singles[j][1]
            b1 = s1.get('badge', '?')
            b2 = s2.get('badge', '?')
            # 成本估算
            cost = 2
            print(f'  [{b1}+{b2}] {cost}元 | {s1[\"decision\"]} × {s2[\"decision\"]} | {s1[\"match\"][:25]} + {s2[\"match\"][:25]}')
            count += 1
        if count >= 10: break

    print()
    print(f'  总计 {count} 组推荐, 全部投注需 {count*2} 元')
else:
    print('  单选不足2场, 无法组2串1')
" 2>/dev/null

# ---- 完成 ----
echo ""
echo "=========================================="
echo "  管道完成 $(date '+%H:%M:%S')"
echo "  预测文件: $LOCK_FILE"
echo "  ⚠️ 截止时间前请勿修改此文件"
echo "  赛后执行: bash verify_and_evolve.sh"
echo "=========================================="
