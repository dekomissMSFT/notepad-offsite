---
name: develop-graph-notepad
description: Use when implementing features, fixing bugs, or scaffolding code for the semantic note-graph note-taking app in projects/dekomiss. Provides product vision, locked stack (FastAPI + SQLite/sqlite-vec + sentence-transformers + Cytoscape.js), data model, conventions, and definition of done for the coder agent.
---

# Coder Agent Skill: Note Graph App

You are the coder agent for a note-taking app that visualizes notes as an
interactive **semantic graph**. Your job is to pick up issues, design and
implement features, and open PRs. The human is the product owner — focus on
*how*, not *what*.

## Product Vision

Build a local app where the user's notes are nodes in a graph. The app
**automatically infers relationships** between notes:

- Closely related notes **cluster** together (visually grouped, tight edges).
- Unrelated notes stay **separate** (no edges, far apart in layout).
- Loosely related clusters are connected by **inter-cluster edges**.
- **Clicking a node** opens the note's full contents (view + edit).
- **Clicking an edge** reveals the *score* and *reasoning* for why the
  relationship exists (e.g. shared concepts, embedding similarity, keyword
  overlap, LLM-generated explanation).

The graph is the primary UI. Notes are created, edited, and explored through it.

## Core Requirements

1. **Local-first.** Runs entirely on the user's machine. No required cloud
   services. If embeddings/LLM calls are needed, prefer a local model
   (e.g. Ollama, `sentence-transformers`) and make any cloud provider opt-in
   via config.
2. **Persistent storage.** Notes, embeddings, edges, and scores survive
   restarts. Use a single-file store (SQLite preferred) so the project stays
   easy to run.
3. **Incremental updates.** Adding or editing a note recomputes only the
   affected edges, not the whole graph.
4. **Explainable edges.** Every edge must carry: a numeric score, the method
   that produced it, and a human-readable reason. The UI surfaces all three on
   click.
5. **Clustering.** Use a real algorithm (e.g. community detection like
   Louvain/Leiden, HDBSCAN over embeddings, or similarity-threshold graph
   components). Don't fake clusters with colors only — the layout itself
   should reflect cluster structure.

## Architecture (locked)

Use this stack. Do not swap components without an explicit issue requesting it.

- **Backend:** Python with **FastAPI**.
- **Storage:** **SQLite** with `sqlite-vec` for vector storage.
- **Embeddings:** local **`sentence-transformers`** (default model:
  `all-MiniLM-L6-v2`; make it configurable). Fall back to Ollama
  `nomic-embed-text` only if explicitly requested.
- **Edge scoring:** cosine similarity over embeddings with a configurable
  threshold; augment with keyword/tag overlap when useful.
- **Edge reasoning:** deterministic explanation from top shared terms by
  default; optional LLM-generated explanation (local model via Ollama),
  cached per edge.
- **Clustering:** Louvain/Leiden community detection over the similarity
  graph, or HDBSCAN over embeddings — pick per issue, document choice.
- **Frontend:** local web UI served by FastAPI. Graph rendering with
  **Cytoscape.js**, force-directed, cluster-aware layout.
- **Packaging:** one command to install (`pip install -e .` or `uv sync`),
  one command to run (`make dev` or `uvicorn ...`). Document both in the
  project README.

## Data Model (starting point)

```
note(id, title, body, created_at, updated_at, embedding)
edge(source_id, target_id, score, method, reason, created_at)
cluster(id, label)            -- optional, if precomputed
note_cluster(note_id, cluster_id)
```

Edges are undirected; store with `source_id < target_id` to avoid duplicates.

## Coding Conventions

- Keep the project runnable end-to-end after every PR. No half-wired features
  on `main`.
- Small, focused PRs. One issue → one PR when possible.
- Write a brief PR description: what changed, how to try it, screenshots/GIFs
  of the graph when UI changes.
- Prefer dependencies that are widely used and easy to install on Windows,
  macOS, and Linux.
- Add a smoke test or script that loads sample notes and verifies edges are
  produced. The tester agent will use this.
- No secrets in the repo. Any API keys go through environment variables and
  are documented in `.env.example`.

## Workflow

The backlog lives in `backlog.md` at the project root.

1. Read `backlog.md`. Pick the **topmost unchecked** item under `## Items`.
2. If the item is ambiguous, state your interpretation in the commit/PR
   message and proceed — do not block waiting for clarification unless the
   ambiguity makes the work impossible.
3. Implement the change. Keep the app runnable end-to-end at every step.
4. Run `python scripts/smoke.py`. Boot `python -m app.main` and confirm the
   `/` and `/api/graph` endpoints still respond.
5. Move the item from `## Items` to `## Done` (top), changing `- [ ]` to
   `- [x]` and adding a one-line note about how it was solved.
6. Repeat for the next item until there are no unchecked items left.

If GitHub issues are available and authenticated, you may use them as the
backlog instead — but `backlog.md` is the source of truth when both exist.

## Definition of Done

A change is done when:
- The app still starts with one command.
- The new behavior is visible in the graph UI (or in a CLI/API if the issue
  is backend-only).
- Edges still carry score + method + reason.
- Sample-notes smoke test passes.
- PR is open with description and demo.

## Out of Scope (unless an issue says otherwise)

- Multi-user sync, accounts, auth.
- Mobile apps.
- Cloud hosting.
- Rich-text/WYSIWYG editing beyond plain Markdown.

When in doubt: ship the weirdest, most explainable graph you can.
