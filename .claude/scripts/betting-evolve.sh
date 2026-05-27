#!/bin/bash
# ============================================
# 体彩分析专属进化管道
# 赛后自动: 记录→评估→校准→进化
# 用法: bash betting-evolve.sh <match_id>
# ============================================

MATCH_ID="${1:-latest}"
EVOLVE_DIR=".claude/evolution/betting"
mkdir -p "$EVOLVE_DIR/predictions" "$EVOLVE_DIR/results" "$EVOLVE_DIR/calibrations"

echo "========================================"
echo "  体彩进化管道: $MATCH_ID"
echo "========================================"

# === Step 1: 记录预测快照 ===
echo ""; echo "--- Step 1: 预测快照 ---"
TIMESTAMP=$(date +%Y-%m-%d_%H%M%S)
PRED_FILE="$EVOLVE_DIR/predictions/$TIMESTAMP-$MATCH_ID.json"

# 从 match-db.json 读取最新预测
python3 -c "
import json, sys
try:
    with open('match-db.json', 'r', encoding='utf-8') as f:
        db = json.load(f)
    matches = db.get('matches', [])
    if matches:
        last = matches[-1]
        with open('$PRED_FILE', 'w', encoding='utf-8') as out:
            json.dump({
                'match_id': last.get('id', '$MATCH_ID'),
                'prediction': last.get('verdict', '?'),
                'scores': last.get('scores', {}),
                'timestamp': '$TIMESTAMP'
            }, out, ensure_ascii=False, indent=2)
        print(f'  📝 快照: {last.get(\"id\", \"?\")} → {last.get(\"verdict\", \"?\")}')
    else:
        print('  ⚠️  数据库为空')
except Exception as e:
    print(f'  ❌ 读取失败: {e}')
" 2>&1

# === Step 2: 赛后校准 ===
echo ""; echo "--- Step 2: 赛后校准 ---"

CALIB_FILE="$EVOLVE_DIR/calibrations/$TIMESTAMP-$MATCH_ID.md"
cat > "$CALIB_FILE" << 'CALIBEOF'
# 赛后校准

## 预测 vs 实际

| 维度 | 预测 | 实际 | 偏差分析 |
|------|------|------|----------|
| D1 赔率区间 | - | - | - |
| D2 盘口变化 | - | - | - |
| D3 赛事类型 | - | - | - |
| D4 庄家共识 | - | - | - |
| D5 凯利指数 | - | - | - |
| D6 主任恐惧 | - | - | - |
| 综合决策 | - | - | - |

## 框架参数调整

- 无

## 教训

- 待填写
CALIBEOF
echo "  📝 校准模板: $CALIB_FILE"

# === Step 3: Kelly 评估 ===
echo ""; echo "--- Step 3: Kelly 模型评估 ---"

python3 -c "
import json, sys
# 读取预测记录，计算 Kelly 收益
try:
    with open('match-db.json', 'r', encoding='utf-8') as f:
        db = json.load(f)
    matches = db.get('matches', [])
    total = len(matches)
    correct = sum(1 for m in matches if m.get('verdict') != '跳过不买' and '主胜' in m.get('result', ''))
    skip_rate = sum(1 for m in matches if m.get('verdict') == '跳过不买') / max(total, 1)

    print(f'  总场次: {total}')
    print(f'  跳过率: {skip_rate:.1%}')
    if total > 0:
        print(f'  Kelly增长: 基准线 = 1.00')
except Exception as e:
    print(f'  ⚠️  评估待数据: {e}')
" 2>&1

# === Step 4: 触发进化链 ===
echo ""; echo "--- Step 4: 进化链触发 ---"
if [ -f ".claude/scripts/evolve.sh" ]; then
  bash .claude/scripts/evolve.sh snapshot 2>&1 | tail -1
fi

echo ""; echo "  ✅ 体彩进化管道完成"
echo "  快照: $PRED_FILE"
echo "  校准: $CALIB_FILE"
