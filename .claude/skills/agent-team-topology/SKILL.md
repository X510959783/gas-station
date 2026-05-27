# Topology Chooser

This skill helps you select the right agent team topology for your task. When invoked with `/topology`, walk the user through a diagnostic questionnaire and recommend one of the 8 topology patterns.

## Instructions

When the user invokes this skill, follow these steps exactly:

### Step 1: Ask the Diagnostic Questions

Present all 4 questions at once using AskUserQuestion:

1. **What's your goal?**
   a) Discover / research — explore and understand the codebase
   b) Review code — check quality, security, or performance
   c) Debug — find root cause of an ambiguous issue
   d) Build a feature — implement a new feature spanning multiple areas
   e) Process a backlog — handle many small independent tasks
   f) Coordinate — manage a complex project with multiple workstreams

2. **Can the work be split into independent streams?**
   a) Yes — tasks are fully independent, no shared files
   b) Mostly — some dependencies but largely parallel
   c) No — tasks are sequential or tightly coupled

3. **What's the risk level?**
   a) Low — mistakes are easy to revert
   b) Medium — mistakes require some effort to fix
   c) High — mistakes could cause outages, data loss, or security issues

4. **Do you need quality gates?**
   a) Yes — work must pass tests/lint/review before being accepted
   b) No — trust agents to self-validate

### Step 2: Apply the Decision Tree

Map the user's answers to one of the 8 topologies:

| Goal | Independence | Risk | Topology |
|------|-------------|------|----------|
| Discover/research | Yes/Mostly | Any | **Parallel Explorers** |
| Review code | Yes/Mostly | Any | **Review Board** |
| Debug | Yes/Mostly | Any | **Competing Hypotheses** |
| Build feature | Yes/Mostly | Low/Medium | **Feature Pod** |
| Build feature | Any | High | **Risky Refactor** |
| Build feature | No | Low/Medium | **Risky Refactor** (sequential safety) |
| Process backlog | Yes | Any | **Task Queue** |
| Coordinate | Yes/Mostly | Any | **Orchestrator-Only** |
| Any | No | Any | Consider single agent instead of a team |

**Quality gates modifier:** If gates=yes, recommend adding **Quality-Gated Delivery** as a composable overlay on top of the primary topology.

**Edge cases:**
- Discover + No independence → single Explorer agent (no team needed)
- Review + No independence → sequential review (single agent with multiple passes)
- Process + No independence → Risky Refactor (sequential pipeline)

### Step 3: Present the Recommendation

Format your output like this:

```
## Recommendation: [Topology Name]

**Why this fits:** [2-3 sentences explaining why this topology matches their answers]

### Team Shape
[Description of team composition — lead + which agents]

### Spawn Prompt
Copy-paste this to get started:

[A ready-to-use prompt tailored to the topology, using the spawn prompts from the pattern cards]

### Pattern Card
Read the full pattern: [topologies/<name>/index.md]

### Alternatives
If this doesn't feel right:
- **[Alternative topology]** — better if [condition]
- **[Alternative topology]** — better if [condition]
```

For the spawn prompt, use the prompt template from the corresponding topology pattern card in `topologies/<name>/index.md`.

If quality gates were requested, add a section:

```
### Quality Gates
Layer Quality-Gated Delivery on top. Install hooks:
- `.claude/hooks/quality-gate.sh` — blocks task completion if tests/lint fail
- `.claude/hooks/idle-summary.sh` — requires structured summary before idle

See: [topologies/quality-gated/index.md]
```

### Step 4: Offer to Refine

After presenting the recommendation, ask: "Does this fit your situation, or would you like to adjust any of your answers?"

## The 8 Topologies (Reference)

| Topology | Best For | Pattern Card |
|----------|----------|-------------|
| Parallel Explorers | Discovery, research, codebase mapping | `topologies/parallel-explorers/` |
| Review Board | Code review with distinct lenses | `topologies/review-board/` |
| Competing Hypotheses | Ambiguous bugs, architectural decisions | `topologies/competing-hypotheses/` |
| Feature Pod | Cross-layer feature delivery | `topologies/feature-pod/` |
| Risky Refactor | High-risk changes needing plan approval | `topologies/risky-refactor/` |
| Orchestrator-Only | Pure coordination, lead never codes | `topologies/orchestrator-only/` |
| Quality-Gated | Enforcing completion standards (composable) | `topologies/quality-gated/` |
| Task Queue | Many small independent tasks | `topologies/task-queue/` |

## Notes

- If the user's answers are ambiguous, present the two best-fit topologies and explain the tradeoff.
- If the user skips questions, make reasonable assumptions and note them.
- Always include at least one alternative recommendation.
- The spawn prompt should be practical and complete — the user should be able to copy-paste it directly.
