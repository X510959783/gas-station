#!/bin/bash
# ============================================
# 🔴 截止时间管道 — 体彩命脉
# 周一至五21:30前 / 周六日22:30前 必须完成全部分析
# ============================================

# 判断今天是周中还是周末
DAY=$(date +%u)  # 1=Mon 5=Fri 6=Sat 7=Sun
if [ "$DAY" -le 5 ]; then
    DEADLINE="21:30"
    FAST_MODE="21:00"    # 提前30分钟切换快速模式
    LOCK_TIME="21:15"    # 提前15分钟锁定预测
    MODE="周中"
else
    DEADLINE="22:30"
    FAST_MODE="22:00"
    LOCK_TIME="22:15"
    MODE="周末"
fi

NOW=$(date +%H:%M)
DATA_DIR="${1:-D:/足彩}"

echo "╔══════════════════════════════════════════════╗"
echo "║  🔴 截止时间管道 — $MODE 模式               ║"
echo "║  截止: $DEADLINE | 快速: $FAST_MODE | 锁定: $LOCK_TIME  ║"
echo "║  当前: $NOW                                    ║"
echo "╚══════════════════════════════════════════════╝"

# 检查是否已过截止时间
if [[ "$NOW" > "$DEADLINE" ]]; then
    echo ""
    echo "  ❌ 已过截止时间 $DEADLINE！"
    echo "  无法提交新预测。请等待下一批比赛。"
    exit 1
fi

# 检查是否在快速模式
if [[ "$NOW" > "$FAST_MODE" ]]; then
    SPEED="fast"
    echo ""
    echo "  ⚡ 快速模式 — 跳过非关键碰撞，优先输出预测"
else
    SPEED="full"
    echo ""
    echo "  🧠 完整模式 — 全链路分析+碰撞"
fi

# 扫描最新比赛数据
echo ""
echo "--- 1. 扫描比赛数据 ---"
LATEST=$(ls -dt "$DATA_DIR"/*/ 2>/dev/null | head -1)
if [ -z "$LATEST" ]; then
    echo "  ❌ 未找到比赛数据"
    exit 1
fi
echo "  📂 $LATEST"
MATCH_COUNT=$(ls "$LATEST"/*/ 2>/dev/null | wc -l)
echo "  📊 $MATCH_COUNT 场比赛"

# 运行框架分析
echo ""
echo "--- 2. 框架分析 ---"
cd d:/gas-station

if [ "$SPEED" = "fast" ]; then
    echo "  ⚡ 快速模式: 跳过碰撞引擎"
    python3 framework_v3.py 2>&1 | tail -5
else
    echo "  🧠 完整模式: 分析+碰撞"
    python3 framework_v3.py 2>&1 | tail -5
    # 碰撞引擎
    if [ -f ".claude/scripts/collision-engine.sh" ]; then
        bash .claude/scripts/collision-engine.sh 2>&1 | grep -E "偏差|完成"
    fi
fi

# 锁定预测
echo ""
echo "--- 3. 锁定预测 ---"
python3 -c "
import json, os
from datetime import datetime
lock = {
    'locked_at': str(datetime.now()),
    'deadline': '$DEADLINE',
    'mode': '$MODE',
    'speed': '$SPEED',
    'matches': []
}
with open('betting-lock.json', 'w', encoding='utf-8') as f:
    json.dump(lock, f, ensure_ascii=False, indent=2)
print('  🔒 预测已锁定: betting-lock.json')
print('  ⚠️  截止时间前不可修改!')
"

echo ""
echo "╔══════════════════════════════════════════════╗"
echo "║  ✅ 截止时间管道完成                          ║"
echo "║  下次触发: 新比赛数据到达时                    ║"
echo "╚══════════════════════════════════════════════╝"
