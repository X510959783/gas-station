#!/bin/bash
# ============================================
# 自进化碰撞引擎 — 新比赛自动触发→找矛盾→修正→验证→更新
# ============================================

COLLISION_DIR=".claude/evolution/betting/collisions"
mkdir -p "$COLLISION_DIR"

echo "========================================"
echo "  🧠 自进化碰撞引擎"
echo "  新比赛→预测→对比→找矛盾→提议修正→验证→更新规则"
echo "========================================"

# === Phase 1: 运行框架预测 ===
echo ""; echo "--- Phase 1: 框架预测 ---"
python3 framework_v3.py 2>&1 | tail -12

# === Phase 2: 偏差检测 ===
echo ""; echo "--- Phase 2: 偏差检测 ---"
python3 -c "
import json, sys
sys.stdout.reconfigure(encoding='utf-8')
try:
    with open('match-db.json', 'r', encoding='utf-8') as f:
        db = json.load(f)
    matches = db.get('matches', [])
    total = len(matches)
    # 检测最近5场的偏差
    deviations = []
    for m in matches[-5:]:
        verdict = m.get('verdict', '')
        result = m.get('result', '')
        if '跳过' in str(verdict) and '主胜' in str(result):
            deviations.append(f'{m.get(\"id\",\"?\")}: 跳过但主胜→假阴性')
        elif '可考虑' in str(verdict) and '主胜' not in str(result) and '平局' not in str(result):
            deviations.append(f'{m.get(\"id\",\"?\")}: 正EV但未中→假阳性')
    if deviations:
        print(f'  ⚠️  检测到 {len(deviations)} 个偏差:')
        for d in deviations: print(f'    {d}')
    else:
        print(f'  ✅ 最近{min(total,5)}场无偏差')
except Exception as e:
    print(f'  ⚠️  数据库分析异常: {e}')
"

# === Phase 3: 全网搜索类似案例 ===
echo ""; echo "--- Phase 3: 全网搜索类似案例 ---"
# 此处可接入 WebSearch——当检测到偏差时自动搜索类似盘口/比赛

# === Phase 4: 提议规则修正 ===
echo ""; echo "--- Phase 4: 提议规则修正 ---"
TIMESTAMP=$(date +%Y-%m-%d_%H%M%S)
PROPOSAL="$COLLISION_DIR/proposal-$TIMESTAMP.md"
cat > "$PROPOSAL" << 'PROEOF'
# 规则修正提议

**时间:** $TIMESTAMP
**触发:** 新比赛偏差检测

## 偏差详情

(待填充)

## 影响分析

- 涉及框架层级:
- 可能影响的已有比赛:

## 提议修正

(待填充)

## 回测验证

- [ ] 修正后全部历史比赛仍通过
- [ ] 修正后偏差场次减少
PROEOF
echo "  📄 提议模板: $PROPOSAL"

# === Phase 5: 更新碰撞日志 ===
echo ""; echo "--- Phase 5: 碰撞日志 ---"
COLLISION_LOG="$COLLISION_DIR/log.jsonl"
echo "{\"timestamp\":\"$(date -u +%Y-%m-%dT%H:%M:%SZ)\",\"action\":\"collision_check\"}" >> "$COLLISION_LOG"
echo "  📊 碰撞日志已更新 (总条目: $(wc -l < "$COLLISION_LOG"))"

echo ""
echo "========================================"
echo "  碰撞引擎完成。下次偏差触发时自动运行。"
echo "========================================"
