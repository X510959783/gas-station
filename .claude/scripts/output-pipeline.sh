#!/bin/bash
# ============================================
# 输出 CI/CD 流水线 —— 每条输出自动过门控
# 用法: bash output-pipeline.sh <文件路径> <类型>
# ============================================

FILE="$1"
TYPE="${2:-auto}"
PASS=0; FAIL=0

echo "========================================"
echo "  输出 CI/CD 流水线: $FILE"
echo "========================================"

# === Stage 1: Lint (语法检查) ===
stage_lint() {
  echo ""; echo "--- Stage 1: Lint ---"

  # Python 文件检查
  if echo "$FILE" | grep -qE "\.py$"; then
    # 检查是否有 bare except
    BARE_EXCEPT=$(grep -c "except:" "$FILE" 2>/dev/null || echo 0)
    BARE_EXCEPT_PASS=$(grep -c "except Exception:" "$FILE" 2>/dev/null || echo 0)
    if [ "$BARE_EXCEPT" -gt "$BARE_EXCEPT_PASS" ]; then
      echo "  ❌ bare except 检测: $BARE_EXCEPT 处 (含 $BARE_EXCEPT_PASS 处 Exception)"
      FAIL=$((FAIL+1))
    else
      echo "  ✅ 异常处理规范"
      PASS=$((PASS+1))
    fi

    # 检查是否有类型标注（函数定义处）
    NO_TYPE=$(grep -cP "^def \w+\([^)]*\):\s*$" "$FILE" 2>/dev/null || echo 0)
    if [ "$NO_TYPE" -gt 0 ]; then
      echo "  ⚠️  无类型标注函数: $NO_TYPE 个"
    else
      echo "  ✅ 类型标注完整"
      PASS=$((PASS+1))
    fi

    # 检查是否有 print 调试残留
    DEBUG_PRINTS=$(grep -c "print(" "$FILE" 2>/dev/null || echo 0)
    if [ "$DEBUG_PRINTS" -gt 5 ]; then
      echo "  ⚠️  print 语句: $DEBUG_PRINTS 处 (考虑用 logger)"
    fi
  fi

  # Bash 文件检查
  if echo "$FILE" | grep -qE "\.sh$"; then
    if head -1 "$FILE" | grep -q "#!/bin/bash"; then
      echo "  ✅ Shebang 正确"
      PASS=$((PASS+1))
    else
      echo "  ❌ 缺少 Shebang"
      FAIL=$((FAIL+1))
    fi

    if grep -q "set -e" "$FILE" 2>/dev/null; then
      echo "  ✅ set -e 已设置"
      PASS=$((PASS+1))
    fi
  fi
}

# === Stage 2: Type Check (类型检查) ===
stage_typecheck() {
  echo ""; echo "--- Stage 2: Type Check ---"
  if echo "$FILE" | grep -qE "\.py$"; then
    if command -v mypy &>/dev/null; then
      mypy "$FILE" --ignore-missing-imports 2>&1 | tail -3
      if [ ${PIPESTATUS[0]} -eq 0 ]; then
        echo "  ✅ mypy 通过"
        PASS=$((PASS+1))
      else
        echo "  ❌ mypy 失败"
        FAIL=$((FAIL+1))
      fi
    else
      echo "  ⏭️  mypy 未安装，跳过"
    fi
  fi
}

# === Stage 3: Self Check (项目特定) ===
stage_selfcheck() {
  echo ""; echo "--- Stage 3: Self Check ---"
  if [ -f "self_check.py" ]; then
    RESULT=$(python3 self_check.py 2>&1 | tail -1)
    if echo "$RESULT" | grep -q "通过"; then
      echo "  ✅ $RESULT"
      PASS=$((PASS+1))
    else
      echo "  ❌ $RESULT"
      FAIL=$((FAIL+1))
    fi
  else
    echo "  ⏭️  无 self_check.py"
  fi
}

# === Stage 4: Verification Gate ===
stage_verify() {
  echo ""; echo "--- Stage 4: Verification Gate ---"
  echo "  📋 验证清单:"
  echo "     - 修改了什么: $(git diff --stat HEAD 2>/dev/null | tail -1 || echo 'N/A')"
  echo "     - 为什么这样改: 请确认改动有明确理由"
  echo "     - 证明改对了: 请提供测试/检查输出"
  PASS=$((PASS+1))
}

# === Stage 5: Output (最终输出) ===
stage_output() {
  echo ""; echo "--- Stage 5: Ready to Output ---"
  if [ "$FAIL" -eq 0 ]; then
    echo "  ✅ 所有门控通过，可以输出"
  else
    echo "  ❌ $FAIL 项失败，阻塞输出。请修复后重试。"
    exit 1
  fi
}

# === 执行流水线 ===
case "$TYPE" in
  python)
    stage_lint
    stage_typecheck
    stage_selfcheck
    stage_verify
    stage_output
    ;;
  bash)
    stage_lint
    stage_verify
    stage_output
    ;;
  full)
    stage_lint
    stage_typecheck
    stage_selfcheck
    stage_verify
    stage_output
    ;;
  *)
    stage_lint
    stage_verify
    stage_output
    ;;
esac

echo ""
echo "========================================"
echo "  流水线结果: $PASS 通过 / $FAIL 失败"
echo "========================================"
