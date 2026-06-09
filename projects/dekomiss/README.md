# Note Graph

A local, semantic note-taking app. Your notes are nodes in a graph; the app
automatically infers relationships, clusters related notes, and explains
*why* any two notes are connected.

- **Backend:** FastAPI + SQLite (with [`sqlite-vec`](https://github.com/asg017/sqlite-vec)) + [`sentence-transformers`](https://www.sbert.net/).
- **Clustering:** Louvain over the cosine-similarity graph.
- **Frontend:** Cytoscape.js, force-directed.

## Install

```bash
python -m venv .venv
. .venv/Scripts/activate   # Windows
# . .venv/bin/activate     # macOS/Linux
pip install -e .
```

First run downloads the embedding model (~90 MB, `all-MiniLM-L6-v2`).

## Run

```bash
python -m app.main
# → http://127.0.0.1:8000
```

Click **+ New note** to add a note. The graph updates incrementally as you
save: edges are recomputed only for the touched note, then clusters are
re-detected over the whole graph.

- **Click a node** → view and edit the note in the side panel.
- **Click an edge** → see the similarity score, the method that produced it,
  and a human-readable reason (shared terms + cosine score).

## Smoke test

```bash
python scripts/smoke.py
# notes=6 edges=N clusters=M
# OK
```

Seeds six sample notes spanning three topics (baking, math, outdoors) and
asserts the graph has at least one edge and more than one cluster.

## Configuration

Environment variables (see `.env.example`):

| Var | Default | Meaning |
|-----|---------|---------|
| `NOTE_GRAPH_DB` | `notes.db` | SQLite file path |
| `NOTE_GRAPH_MODEL` | `all-MiniLM-L6-v2` | sentence-transformers model name |
| `NOTE_GRAPH_SIM_THRESHOLD` | `0.35` | cosine-similarity cutoff for edges |
| `NOTE_GRAPH_HOST` | `127.0.0.1` | bind host |
| `NOTE_GRAPH_PORT` | `8000` | bind port |

> If you change the model, also update `EMBED_DIM` in `app/db.py` to match.

## Data model

```
notes(id, title, body, created_at, updated_at)
note_vec(note_id, embedding)        -- sqlite-vec virtual table
edges(source_id, target_id, score, method, reason, created_at)
clusters(id, label)
note_cluster(note_id, cluster_id)
```

Edges are undirected and stored with `source_id < target_id`.
