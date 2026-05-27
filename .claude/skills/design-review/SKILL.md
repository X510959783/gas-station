---
name: design-review
description: |
  Dispatch an independent challenger agent to adversarially review a spec or implementation
  plan against the actual codebase. Catches hallucinated APIs, wrong field names, nonexistent
  files, and incorrect assumptions. Two modes: (1) spec review — verifies DB model fields,
  API paths, config attributes, file paths referenced in a design spec, (2) plan review —
  verifies imports, function signatures, constructor args, file paths in an implementation plan.
  Use after brainstorming produces a spec, or after writing-plans produces a plan, before execution.
  Triggers: "review the spec", "review the plan", "challenge this", "check for hallucinations",
  "design review", "spec review", "plan review", "/design-review".
---

# Design Review (Challenger Agent)

## Overview

Specs and plans written by AI often contain hallucinations: references to APIs that don't exist, wrong column names, incorrect file paths, assumed config attributes that were never defined. These errors waste hours during implementation.

This skill dispatches an **independent challenger agent** that reads the spec or plan, identifies every concrete claim, and verifies each one against the actual codebase. The challenger has zero context from the authoring session — it trusts only `grep`, `read`, and the code.

**Announce at start:** "I'm using the design-review skill to dispatch a challenger agent for adversarial review."

## When to Use

- After `superpowers:brainstorming` produces a spec → `design-review spec <path>`
- After `superpowers:writing-plans` produces a plan → `design-review plan <path>`
- When a spec/plan references models, APIs, or config from an unfamiliar codebase
- When the document was written in a session that hit context limits (higher hallucination risk)
- User says "review the spec", "review the plan", "challenge this", "check for hallucinations"

## Modes

### Mode 1: Spec Review — `design-review spec <path>`

Triggered after a spec is written. Verifies:

| Claim Type | Verification Method |
|-----------|-------------------|
| DB model fields mentioned in spec | `grep "column_name" models.py` or `backend/db/models.py` |
| API endpoints mentioned in spec | `grep "router.*path" backend/api/` |
| Config attributes mentioned in spec | `grep "get_setting.*key" backend/` |
| File paths mentioned in spec | `ls` / `test -f` to verify existence |
| Function names mentioned in spec | `grep "def func_name" backend/` |

### Mode 2: Plan Review — `design-review plan <path> [--spec <spec_path>]`

Triggered after a plan is written. Two verification dimensions:

**Dimension 1: Technical Reference Verification** (same as original plan-review)

| Claim Type | Verification Method |
|-----------|-------------------|
| Import statements | Does the module/function exist? `grep "def Y\|class Y" X.py` |
| Model field access | Does the column exist? Read model file |
| Function calls | Does the function exist with that signature? |
| File paths | Does the file exist? Is the name correct? |
| Config attributes | Does config have this attribute? |
| Constructor arguments | Does the model/class accept these kwargs? |

**Dimension 2: Spec Coverage Verification** (requires `--spec` parameter)

When a spec path is provided, the challenger also verifies plan ↔ spec alignment:

| Check | Method |
|-------|--------|
| Spec requirement → Plan task mapping | Every spec requirement (F1, F2, ...) must have at least one plan task covering it |
| Missing requirements | List any spec sections with NO corresponding plan task → BLOCKER |
| Partial coverage | Spec requirement mentioned in plan but implementation steps incomplete → WARNING |
| Extra scope | Plan tasks that don't trace to any spec requirement → WARNING (scope creep) |

Usage: `design-review plan <plan_path> --spec <spec_path>` or `design-review plan <plan_path>` (spec-only review if spec auto-detected from same date prefix)

### Graph Enhancement (optional, if graph available)

If `.code-review-graph/graph.db` exists:
- Plan files → `/explore impact` to check for missed affected modules
- Spec functions → query graph nodes to verify existence

## Process

```
1. Identify the document path and type (spec or plan)
2. If plan review → auto-detect related spec (same date prefix in docs/superpowers/specs/) or use --spec
3. Dispatch challenger agent (general-purpose, in foreground)
4. Receive findings: BLOCKERs + WARNINGs + Coverage matrix (if spec provided)
5. If BLOCKERs exist → fix inline, re-verify
6. If only WARNINGs → present to user, fix if agreed
7. Report final status
```

## Step 1: Identify Inputs

Determine the document type and path:

**Spec locations:**
- `docs/superpowers/specs/*.md`
- User-specified path

**Plan locations:**
- `docs/superpowers/plans/*.md`
- `.harness/plans/*.md`
- User-specified path

## Step 2: Dispatch Challenger Agent

Use the Agent tool:

```
Agent:
  description: "Adversarial design review"
  subagent_type: general-purpose
  prompt: <see challenger-prompt.md — fill [DOC_PATH], [DOC_TYPE], [SPEC_PATH]>
```

**Critical rules:**
- MUST be `general-purpose` (needs Read, Grep, Glob tools)
- Do NOT use `superpowers:code-reviewer` — this is codebase verification, not code review
- Run in **foreground** (need results before proceeding)

## Step 3-6: Same as plan-review

See the Process section above. Handle BLOCKERs (must fix) and WARNINGs (should fix) exactly as described in the original plan-review skill.

## Severity Levels

### BLOCKER (must fix before execution)
- Nonexistent attribute / field / column
- Wrong import path / module name
- Hallucinated API / function
- Wrong function signature
- Nonexistent file path

### WARNING (should fix, won't crash)
- Stale patterns (codebase has better approach)
- Missing error handling that siblings have
- Field name cosmetic mismatch
- Missing data fetch

## Anti-Patterns

| Wrong | Right |
|-------|-------|
| Review the document yourself in the same session | Dispatch a fresh agent with zero context |
| Use `superpowers:code-reviewer` agent type | Use `general-purpose` — codebase verification |
| Only check text for readability | Verify every import, field, API against actual code |
| Trust model fields because they "sound right" | `grep` for the actual column definition |
| Skip spec review because "it's just a design" | Specs with wrong field names become plans with wrong field names |

## Key Principle

**The challenger trusts nothing from the authoring session.** Every concrete reference is verified by reading the actual source.
