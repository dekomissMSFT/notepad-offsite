"""Smoke test: seed notes, exercise tags + edge overrides + clustering."""
from __future__ import annotations

import os
import sys
import tempfile

_tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
_tmp.close()
os.environ["NOTE_GRAPH_DB"] = _tmp.name
os.environ.setdefault("NOTE_GRAPH_SIM_THRESHOLD", "0.25")

from app.db import get_conn  # noqa: E402
from app.graph import on_note_edit, set_edge_override  # noqa: E402

SAMPLES = [
    ("Sourdough starter", "Mixed flour and water, let it ferment. #baking"),
    ("Bread baking notes", "Sourdough loaf rose well; oven spring was great. #baking"),
    ("Pizza dough", "High-hydration dough using bread flour and a poolish. #baking"),
    ("Linear algebra recap", "Eigenvectors, SVD, and orthogonal projections. #math"),
    ("Calculus refresher", "Reviewed limits, derivatives, and the chain rule. #math"),
    ("Kayaking trip plan", "Pack drybag, life vest, and snacks for the river."),
]


def count(sql: str) -> int:
    return get_conn().execute(sql).fetchone()["c"]


def main() -> int:
    conn = get_conn()
    ids: list[int] = []
    for title, body in SAMPLES:
        cur = conn.execute(
            "INSERT INTO notes(title, body) VALUES (?, ?)", (title, body)
        )
        conn.commit()
        nid = int(cur.lastrowid)
        on_note_edit(nid, title, body)
        ids.append(nid)

    n_notes = count("SELECT COUNT(*) AS c FROM notes")
    n_edges = count("SELECT COUNT(*) AS c FROM edges")
    n_clusters = count("SELECT COUNT(DISTINCT cluster_id) AS c FROM note_cluster")
    tag_edges = count(
        "SELECT COUNT(*) AS c FROM edges WHERE method LIKE '%tag-overlap%'"
    )
    print(f"notes={n_notes} edges={n_edges} clusters={n_clusters} tag_edges={tag_edges}")

    assert n_notes == len(SAMPLES), f"expected {len(SAMPLES)} notes"
    assert n_edges > 0, "expected similarity edges"
    assert n_clusters > 1, "expected multiple clusters"
    assert tag_edges >= 3, "expected tag-overlap edges among #baking trio"

    # Pin an edge between two unrelated notes (kayaking ↔ algebra).
    kayak = ids[5]
    algebra = ids[3]
    set_edge_override(kayak, algebra, "pinned")
    pinned = get_conn().execute(
        "SELECT method FROM edges WHERE source_id = ? AND target_id = ?",
        tuple(sorted((kayak, algebra))),
    ).fetchone()
    assert pinned is not None and "pinned" in pinned["method"], "pin failed"

    # Suppress an auto edge (sourdough ↔ bread baking) and ensure it disappears.
    sd, bb = ids[0], ids[1]
    set_edge_override(sd, bb, "suppressed")
    still = get_conn().execute(
        "SELECT 1 FROM edges WHERE source_id = ? AND target_id = ?",
        tuple(sorted((sd, bb))),
    ).fetchone()
    assert still is None, "suppress failed: edge still present"

    # Clear override → edge should come back on next recompute.
    set_edge_override(sd, bb, None)
    back = get_conn().execute(
        "SELECT 1 FROM edges WHERE source_id = ? AND target_id = ?",
        tuple(sorted((sd, bb))),
    ).fetchone()
    assert back is not None, "clear-override failed: edge missing"

    print("OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
