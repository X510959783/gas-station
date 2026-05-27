#!/usr/bin/env bash
# ============================================================
# cron_daily.sh — 定时触发采集+分析+锁定管道
#
# 使用方式:
#   手动: bash cron_daily.sh
#   定时: 添加到 crontab / 任务计划程序
#     Windows: schtasks /create /tn "GasStation" /tr "bash d:\gas-station\cron_daily.sh" /sc daily /st 20:00
#     Linux:   (crontab -e) 0 20 * * 1-5 /path/to/cron_daily.sh
#
# 调度逻辑:
#   周一到周五: 20:00 自动触发
#   周六周日:   21:00 自动触发
#   T-30min 自动切换快速模式
#   T-15min 强制锁定
# ============================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

LOG_FILE="$SCRIPT_DIR/.pipeline.log"
TODAY=$(date +%Y-%m-%d)
NOW=$(date '+%H:%M:%S')

log() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

# ---- 检查是否在休赛期 ----
# 简单逻辑: 如果 fetch_500.py 返回空结果, 则跳过
# 实际使用中由 cron 调度决定

log "===== 管道启动 ====="

# ---- 步骤1: 数据采集 ----
log "步骤1: 采集赔率数据..."

DATA_DIR="D:/足彩/$TODAY"

# 检查是否已经采集过
if [ -d "$DATA_DIR" ] && [ "$(ls -A "$DATA_DIR" 2>/dev/null)" ]; then
  log "  数据目录已存在, 跳过采集: $DATA_DIR"
else
  python "$SCRIPT_DIR/fetch_500.py" --date "$TODAY" 2>&1 | tee -a "$LOG_FILE"
  if [ $? -ne 0 ]; then
    log "❌ 采集失败, 检查网络连接"
    exit 1
  fi
  log "  采集完成: $DATA_DIR"
fi

# 统计比赛数
MATCH_COUNT=$(find "$DATA_DIR" -maxdepth 1 -type d | tail -n +2 | wc -l)
log "  比赛数量: $MATCH_COUNT"

if [ "$MATCH_COUNT" -eq 0 ]; then
  log "  今日无比赛, 管道结束"
  exit 0
fi

# ---- 步骤2: L3搜索情报 (生成搜索提示) ----
log "步骤2: 生成搜索情报提示..."

INTEL_DIR="$SCRIPT_DIR/.intel/$TODAY"
mkdir -p "$INTEL_DIR"

python "$SCRIPT_DIR/search_intel.py" --batch "$DATA_DIR" > "$INTEL_DIR/search_queries.txt" 2>&1
log "  搜索查询已生成: $INTEL_DIR/search_queries.txt"

# 检查是否有缓存的搜索数据
CACHE_COUNT=$(python -c "
import os, json
cache_dir = os.path.join('$SCRIPT_DIR', '.search_cache')
if os.path.exists(cache_dir):
    print(len(os.listdir(cache_dir)))
else:
    print(0)
" 2>/dev/null)
log "  缓存搜索数据: ${CACHE_COUNT:-0} 条"

# ---- 步骤3: 运行分析管道 ----
log "步骤3: 运行分析管道..."

bash "$SCRIPT_DIR/auto_pipeline.sh" "$DATA_DIR" 2>&1 | tee -a "$LOG_FILE"

PIPELINE_EXIT=$?
if [ $PIPELINE_EXIT -ne 0 ]; then
  log "⚠️ 管道退出码: $PIPELINE_EXIT"
fi

# ---- 步骤4: 摘要 ----
log "步骤4: 生成摘要..."

LOCK_FILE="$SCRIPT_DIR/betting-lock.json"
if [ -f "$LOCK_FILE" ]; then
  python -c "
import json
with open('$LOCK_FILE') as f:
    data = json.load(f)
print(f'  锁定时间: {data[\"locked_at\"]}')
print(f'  总场次: {data[\"total_matches\"]}')
print(f'  单选: {data[\"singles\"]} | 双选: {data[\"doubles\"]} | 跳过: {data[\"skips\"]}')
print()
print('  预测汇总:')
for i, p in enumerate(data['predictions']):
    print(f'  [{i+1}] {p[\"league\"]} {p[\"match\"][:35]}')
    print(f'      → {p[\"decision\"]} ({p[\"badge\"]})')
" 2>&1 | tee -a "$LOG_FILE"
fi

log "===== 管道完成 ====="
log ""
