#!/bin/bash
# 检查 skill 是否已安装 — 安装前必须运行
# 用法: bash .claude/scripts/check-skills.sh skill1 skill2 skill3 ...

SKILLS_DIR=".claude/skills"
AGENTS_DIR=".agents/skills"
HAVE=(); MISS=()

for skill in "$@"; do
  name=$(basename "$skill")
  if [ -f "$SKILLS_DIR/$name/SKILL.md" ] || [ -f "$AGENTS_DIR/$name/SKILL.md" ]; then
    HAVE+=("$name")
  else
    MISS+=("$name")
  fi
done

if [ ${#HAVE[@]} -gt 0 ]; then
  echo "已安装(${#HAVE[@]}): ${HAVE[*]}"
fi
if [ ${#MISS[@]} -gt 0 ]; then
  echo "需安装(${#MISS[@]}): ${MISS[*]}"
  exit 1
else
  echo "全部已安装，无需额外操作"
  exit 0
fi
