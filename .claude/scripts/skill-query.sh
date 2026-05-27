#!/bin/bash
# ============================================
# Skill 查询优化器 —— 索引优先，避免全扫
# 用法: bash skill-query.sh <场景>
# ============================================

QUERY="$1"
INDEX=".claude/evolution/skill-index.json"

if [ ! -f "$INDEX" ]; then
  echo "❌ 索引文件不存在: $INDEX"
  exit 1
fi

# === 第1步: 场景精确匹配 ===
echo "🔍 查询: '$QUERY'"
echo ""

SCENE_MATCH=$(python3 -c "
import json, sys
with open('$INDEX') as f:
    idx = json.load(f)
scenes = idx['indexes']['by_scenario']
q = '$QUERY'.lower().strip()

# 精确匹配
if q in scenes:
    print('EXACT:' + ','.join(scenes[q]))
    sys.exit(0)

# 模糊匹配
for key, skills in scenes.items():
    if q in key or key in q:
        print('FUZZY:' + key + ':' + ','.join(skills))
        sys.exit(0)

print('NOT_FOUND')
" 2>&1)

if echo "$SCENE_MATCH" | grep -q "EXACT:"; then
  SKILLS=$(echo "$SCENE_MATCH" | sed 's/EXACT://')
  echo "  ✅ 场景精确匹配"
  echo "  Skills: $(echo "$SKILLS" | tr ',' '\n' | sed 's/^/    - /')"
  echo ""
  count=$(echo "$SKILLS" | tr ',' '\n' | wc -l)
  echo "  📊 命中 $count 个 skill (从 3400 中索引匹配)"

elif echo "$SCENE_MATCH" | grep -q "FUZZY:"; then
  KEY=$(echo "$SCENE_MATCH" | cut -d: -f2)
  SKILLS=$(echo "$SCENE_MATCH" | cut -d: -f3-)
  echo "  ⚠️  场景模糊匹配: '$KEY'"
  echo "  Skills: $(echo "$SKILLS" | tr ',' '\n' | sed 's/^/    - /')"

else
  echo "  ❌ 场景未命中索引"
  echo ""
  echo "  --- 第2步: 触发词匹配 ---"
  TRIGGER_MATCH=$(python3 -c "
import json
with open('$INDEX') as f:
    idx = json.load(f)
triggers = idx['indexes']['by_trigger_word']
q = '$QUERY'.lower().strip()

for word, skills in triggers.items():
    if word in q or q in word:
        print(f'TRIGGER:{word}:' + ','.join(skills))
        sys.exit(0)
print('NOT_FOUND')
" 2>&1)

  if echo "$TRIGGER_MATCH" | grep -q "TRIGGER:"; then
    WORD=$(echo "$TRIGGER_MATCH" | cut -d: -f2)
    SKILLS=$(echo "$TRIGGER_MATCH" | cut -d: -f3-)
    echo "  ✅ 触发词匹配: '$WORD'"
    echo "  Skills: $(echo "$SKILLS" | tr ',' '\n' | sed 's/^/    - /')"
  else
    echo "  ❌ 全索引未命中，建议全目录 grep"
  fi
fi

echo ""
echo "--- 推荐链 ---"
CHAIN_MATCH=$(python3 -c "
import json
with open('$INDEX') as f:
    idx = json.load(f)
chains = idx['indexes']['by_chain']
q = '$QUERY'.lower().strip()
if q in chains:
    print('CHAIN:' + q + ':' + ','.join(chains[q]))
" 2>&1)
if echo "$CHAIN_MATCH" | grep -q "CHAIN:"; then
  echo "  执行: bash .claude/scripts/chain-runner.sh $QUERY"
else
  echo "  无对应链，使用独立 skill 或自定义组合"
fi
