---
name: explore
description: |
  Graph-driven project understanding using code-review-graph (CRG). Query architecture,
  modules, callers/callees, impact radius, hotspots, execution flows, and search nodes.
  Use when: (1) brainstorming and need to understand project structure, (2) writing plans
  and need impact analysis, (3) user says "understand this project", "how does this module
  work", "impact analysis", "/explore", (4) reviewing code changes and need blast radius.
  Requires .code-review-graph/graph.db — run /graph build first if missing.
---

# Explore — Graph-Driven Project Understanding

## Overview

Query the project's code knowledge graph to understand architecture, trace call chains, and analyze impact. Powered by CRG's graph.db (SQLite) + CRG Python API.

**Announce at start:** "I'm using the explore skill to query the project's code knowledge graph."

## Prerequisites

- CRG must be installed: `python -c "import code_review_graph.tools"`
- Graph must exist: `.code-review-graph/graph.db`
- If missing → tell user: "Please run `/graph build` first"
- If graph older than 24h → suggest: "Graph may be stale, consider `/graph update`"

## Commands

### `/explore architecture` — Project Architecture Overview

Shows module decomposition, coupling relationships, and entry points.

```python
from pathlib import Path
from code_review_graph.tools import list_communities_func, get_architecture_overview_func

# Get communities (modules) — CRG takes repo_root, not db_path
repo = Path(".")
result = list_communities_func(repo_root=repo)
communities = result.get("communities", [])

# Get architecture overview
overview = get_architecture_overview_func(repo_root=repo)
```

Present as: module list with node counts, inter-module coupling, key entry points.

### `/explore module <name>` — Module Details

Shows nodes, edges, and responsibilities of a specific module.

```python
from pathlib import Path
from code_review_graph.tools import list_communities_func

# CRG has no single-community query API — filter from full list
result = list_communities_func(repo_root=Path("."))
communities = result.get("communities", [])
target = [c for c in communities if name.lower() in str(c).lower()]
```

### `/explore callers <func>` — Who Calls This Function?

Direct SQLite query (no CRG wrapper available for this):

```python
import sqlite3
conn = sqlite3.connect(".code-review-graph/graph.db")
conn.row_factory = sqlite3.Row
rows = conn.execute(
    "SELECT * FROM edges WHERE target_qualified LIKE ? AND kind='CALLS'",
    (f"%{func}%",)
).fetchall()
conn.close()
```

### `/explore callees <func>` — What Does This Function Call?

```python
import sqlite3
conn = sqlite3.connect(".code-review-graph/graph.db")
conn.row_factory = sqlite3.Row
rows = conn.execute(
    "SELECT * FROM edges WHERE source_qualified LIKE ? AND kind='CALLS'",
    (f"%{func}%",)
).fetchall()
conn.close()
```

### `/explore impact <file>` — Impact Analysis

Shows which flows and functions are affected by changes to a file.

```python
from pathlib import Path
from code_review_graph.tools import get_impact_radius, get_affected_flows_func

# CRG takes changed_files (list) and repo_root, not file_path + db_path
repo = Path(".")
impact = get_impact_radius(changed_files=["<file>"], repo_root=repo)
result = get_affected_flows_func(changed_files=["<file>"], repo_root=repo)
flows = result.get("flows", result.get("affected_flows", []))
```

### `/explore hotspots` — Hub Nodes, Bridge Nodes, Knowledge Gaps

**IMPORTANT:** `get_hub_nodes_func` / `get_bridge_nodes_func` from `code_review_graph.tools` are buggy. Use `code_review_graph.analysis` instead:

```python
from code_review_graph.tools._common import _get_store
from code_review_graph.analysis import find_hub_nodes, find_bridge_nodes

# CRG analysis functions take a store object, not db_path
# Must use _get_store() first to get the store
store, _ = _get_store(str(Path(".").resolve()))
hubs = find_hub_nodes(store, top_n=20)
bridges = find_bridge_nodes(store, top_n=20)
```

For knowledge gaps (`get_knowledge_gaps` has sqlite3.Row type issue), use direct SQLite:

```python
import sqlite3
conn = sqlite3.connect(".code-review-graph/graph.db")
# Nodes with high connectivity but no docstring/comments
rows = conn.execute("""
    SELECT n.qualified_name, n.kind, COUNT(e.id) as edge_count
    FROM nodes n
    JOIN edges e ON n.qualified_name = e.source_qualified OR n.qualified_name = e.target_qualified
    WHERE n.docstring IS NULL OR n.docstring = ''
    GROUP BY n.qualified_name
    HAVING edge_count > 5
    ORDER BY edge_count DESC
    LIMIT 20
""").fetchall()
conn.close()
```

### `/explore flows` — Execution Flow List

```python
from pathlib import Path
from code_review_graph.tools import list_flows

# Note: NO _func suffix — it's list_flows, not list_flows_func
result = list_flows(repo_root=Path("."))
flows = result.get("flows", [])
```

### `/explore search <keyword>` — Search Nodes by Keyword

Try CRG's search first, fallback to direct SQLite:

```python
import sqlite3
conn = sqlite3.connect(".code-review-graph/graph.db")
# Try FTS5 first
try:
    rows = conn.execute(
        "SELECT * FROM nodes_fts WHERE nodes_fts MATCH ?", (keyword,)
    ).fetchall()
except:
    # Fallback: LIKE query
    rows = conn.execute(
        "SELECT * FROM nodes WHERE name LIKE ?", (f"%{keyword}%",)
    ).fetchall()
conn.close()
```

## CRG API Notes (from challenger review)

These bugs are confirmed in `backend/services/graph_builder.py` workarounds:

| API | Issue | Workaround |
|-----|-------|------------|
| `get_hub_nodes_func` (tools) | Bug | Use `find_hub_nodes` from `code_review_graph.analysis` + `_get_store()` |
| `get_bridge_nodes_func` (tools) | Bug | Use `find_bridge_nodes` from `code_review_graph.analysis` + `_get_store()` |
| `get_knowledge_gaps` (tools) | sqlite3.Row type issue | Direct SQLite query |
| callers/callees | No CRG wrapper | Direct SQLite on edges table |

## Development Workflow Integration

| Phase | How to Use |
|-------|-----------|
| brainstorming | `/explore architecture` before designing — understand existing structure |
| writing-plans | `/explore impact <file>` to predict blast radius, inform Files list |
| coding | `/explore callers <func>` to understand upstream/downstream |
| code-review | `/explore impact <file>` to verify blast radius coverage |

## Graceful Degradation

- CRG not installed or graph missing → "Please run `/graph build` first"
- Graph stale (>24h since last update) → "Graph may be outdated, suggest `/graph update`"
