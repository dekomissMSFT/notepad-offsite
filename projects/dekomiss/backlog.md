# Backlog

The coder agent works this file top-down. Each `- [ ]` item is a work item.
Add new items at the **bottom**. The agent picks the **topmost unchecked**
item, implements it end-to-end (code + smoke test still passes + browser
still works), marks it `- [x]`, and moves to the next one. The agent stops
when there are no unchecked items left, or when a single item is too
ambiguous to act on without you.

## Format

```
- [ ] Short title — optional one-line clarification.
      Extra detail can go on indented continuation lines.
```

Use plain English. You don't need to spec the implementation — the agent
will design it within the locked stack (FastAPI + SQLite/sqlite-vec +
sentence-transformers + Cytoscape.js).

## Items

<!-- Add new items below this line. Top = highest priority. -->

- [] add tags to the notes and weight the tags more heavily for edge generation
- [] user should be able to add tags themselves and tags can automatically be generated based on the note contents

## Done

<!-- Items move here when finished, newest on top, with a one-line note. -->

- [x] Import/export markdown — `POST /api/import` accepts multipart `.md`
      uploads (first H1 becomes title, rest is body; falls back to filename
      stem). `GET /api/export` streams a zip of `NNNN-slug.md` files. UI:
      Import / Export buttons in the header.
- [x] Tags — `#tag` words extracted from title+body produce `tag-overlap`
      edges (Jaccard-scored) alongside cosine. Combined edges report all
      contributing methods in their reason. Cluster labels also weight tags.
- [x] Cluster-aware layout — Cytoscape now uses `fcose` with one compound
      parent node per cluster, so clusters are visibly grouped (with the
      cluster label rendered on the parent box) in addition to color-coded.
- [x] Configurable similarity threshold — header slider 0.00–1.00 calls
      `/api/graph?min_score=`. Backend filters auto edges below the cutoff
      but always keeps user-asserted edges (pinned / tag-overlap / manual).
- [x] Search box — header `<input type="search">` dims non-matching graph
      nodes (and their edges) and the matching ones get a highlight border;
      also filters the notes list sidebar in sync.
- [x] Notes list sidebar — collapsible left sidebar lists every note with
      title + snippet; click opens in the edit panel; toggle via header
      hamburger button; active note is highlighted.
- [x] Manually add an edge — right-click a node → "Add link from here…",
      then left-click any other node to create a pinned edge between them.
      `Esc` or background-click cancels link mode.
- [x] Modifiable edges (pin / suppress / clear) — new `edge_overrides`
      table; endpoints `POST /api/edges/{a}/{b}/pin`,
      `POST /api/edges/{a}/{b}/suppress`,
      `DELETE /api/edges/{a}/{b}/override`. Edge explain panel and edge
      right-click menu expose all three. Pinned edges always exist;
      suppressed edges never auto-appear; pinned edges render dashed
      yellow, tag-overlap green.
- [x] Right-click context menu on nodes — `cxttap` shows a menu with
      Edit / Add link from here / Delete; delete also tears down overrides
      that referenced the note.
- [x] Hover preview — node hover shows a fixed-position tooltip with the
      title and first 150 chars of body; cached per-note and invalidated on
      save/delete.
- [x] Cluster labels — each cluster has an auto-generated label from its
      top shared terms; surfaced as a legend in the side panel and as the
      label on the compound parent box.
