---
name: graph
description: |
  Manage code knowledge graphs via code-review-graph (CRG). Build, update, and check status
  of project code graphs stored in .code-review-graph/graph.db. Use when: (1) user says
  "build graph", "update graph", "graph status", "/graph", (2) Harness init detects CRG,
  (3) preparing to use /explore commands. Gracefully degrades if CRG is not installed.
---

# Graph — Knowledge Graph Management

## Overview

Manage project code knowledge graphs powered by [code-review-graph](https://github.com/tirth8205/code-review-graph). The graph stores code structure (functions, classes, calls, imports) in `.code-review-graph/graph.db` (SQLite) and enables architecture understanding, impact analysis, and caller/callee tracing.

**Announce at start:** "I'm using the graph skill to manage the project's code knowledge graph."

## Commands

### `/graph build` — Full Build

Build a complete code graph for the current project:

```bash
# Check CRG is available first
python -c "import code_review_graph.tools" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "CRG not installed. Run: pip install code-review-graph"
    exit 1
fi

# Full build
code-review-graph build --repo .
```

After build, report:
- Graph location: `.code-review-graph/graph.db`
- Node count: `SELECT COUNT(*) FROM nodes`
- Edge count: `SELECT COUNT(*) FROM edges`
- Community count: use `list_communities_func` from `code_review_graph.tools`

### `/graph update` — Incremental Update

Update the graph with recent changes (faster than full build):

```bash
code-review-graph update --repo .
```

### `/graph status` — Graph Status

Check if a graph exists and show stats:

```python
import os, sqlite3

db_path = ".code-review-graph/graph.db"
if not os.path.exists(db_path):
    print("No graph found. Run /graph build first.")
else:
    conn = sqlite3.connect(db_path)
    nodes = conn.execute("SELECT COUNT(*) FROM nodes").fetchone()[0]
    edges = conn.execute("SELECT COUNT(*) FROM edges").fetchone()[0]
    mtime = os.path.getmtime(db_path)
    from datetime import datetime
    last_updated = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M")
    print(f"Graph: {db_path}")
    print(f"Nodes: {nodes} | Edges: {edges} | Last updated: {last_updated}")
    conn.close()
```

Also run `list_communities_func` from `code_review_graph.tools` to show community count.

### `/graph view` — Interactive Visualization in Browser

Open an interactive graph visualization in the browser:

```bash
# Generate HTML + start local server (auto-opens http://localhost:8765)
code-review-graph visualize --repo . --serve
```

View modes:

```bash
# Default: auto-detect best layout
code-review-graph visualize --repo . --serve

# Community/module view: nodes grouped by detected communities
code-review-graph visualize --repo . --mode community --serve

# File-level view: nodes are files, edges are cross-file dependencies
code-review-graph visualize --repo . --mode file --serve

# Full view: every function/class as a node
code-review-graph visualize --repo . --mode full --serve
```

Export (no server):

```bash
# Generate HTML file only → open .code-review-graph/visualization.html manually
code-review-graph visualize --repo .

# Export as SVG image
code-review-graph visualize --repo . --format svg

# Export for Obsidian
code-review-graph visualize --repo . --format obsidian

# Export as GraphML (for yEd/Gephi)
code-review-graph visualize --repo . --format graphml
```

### `/graph wiki` — Generate Markdown Wiki

```bash
code-review-graph wiki --repo .
# Generates markdown docs from community structure
```

### `/graph install` — Check/Install CRG

```bash
python -c "import code_review_graph.tools; print('CRG is available')" 2>/dev/null \
  || echo "CRG not installed. Install with: pip install code-review-graph"
```

## Graceful Degradation

- CRG not installed → show install command, never crash
- Detection method: `python -c "import code_review_graph.tools"` (matches `graph_builder.py` pattern)
- Graph file missing → prompt `/graph build`

## Storage

- Graph: `.code-review-graph/graph.db` (CRG default, in workspace)
- Metadata: `.code-review-graph/` directory, managed by CRG automatically
