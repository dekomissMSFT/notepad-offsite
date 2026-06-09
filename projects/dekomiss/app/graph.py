"""Edge recomputation, clustering, tags, and user-edge overrides."""
from __future__ import annotations

import re
import struct
from collections import Counter

import numpy as np

from .config import settings
from .db import EMBED_DIM, get_conn, tx
from .embeddings import embed

_WORD_RE = re.compile(r"[A-Za-z][A-Za-z0-9_'-]{2,}")
_TAG_RE = re.compile(r"#([A-Za-z][A-Za-z0-9_-]*)")
_STOPWORDS = {
    "the", "and", "for", "with", "that", "this", "from", "have", "has", "had",
    "are", "was", "were", "but", "not", "you", "your", "his", "her", "its",
    "their", "they", "them", "our", "ours", "who", "what", "when", "where",
    "why", "how", "all", "any", "some", "into", "out", "than", "then", "also",
    "about", "over", "under", "between", "while", "just", "such", "very",
    "more", "most", "much", "many", "one", "two", "can", "will", "would",
    "could", "should", "did", "doing", "does", "been", "being", "because",
}


# -------- low level --------------------------------------------------------

def _encode_vec(vec: np.ndarray) -> bytes:
    return struct.pack(f"{len(vec)}f", *vec.tolist())


def _decode_vec(blob: bytes) -> np.ndarray:
    return np.frombuffer(blob, dtype=np.float32)


def _tokenize(text: str) -> list[str]:
    return [w.lower() for w in _WORD_RE.findall(text) if w.lower() not in _STOPWORDS]


def _shared_terms(a_text: str, b_text: str, k: int = 5) -> list[str]:
    a_terms = Counter(_tokenize(a_text))
    b_terms = Counter(_tokenize(b_text))
    return [t for t, _ in (a_terms & b_terms).most_common(k)]


def extract_tags(text: str) -> set[str]:
    return {m.lower() for m in _TAG_RE.findall(text)}


def store_embedding(note_id: int, vec: np.ndarray) -> None:
    conn = get_conn()
    conn.execute(
        "INSERT OR REPLACE INTO note_vec(note_id, embedding) VALUES (?, ?)",
        (note_id, _encode_vec(vec)),
    )
    conn.commit()


# -------- edge composition -------------------------------------------------

def _compose_edge(
    cosine: float | None,
    shared_terms: list[str],
    shared_tags: list[str],
    tags_union_size: int,
    pinned: bool,
) -> tuple[str, str, float]:
    methods: list[str] = []
    parts: list[str] = []
    score_candidates: list[float] = []

    above = cosine is not None and cosine >= settings.sim_threshold
    if above:
        methods.append("cosine+shared-terms" if shared_terms else "cosine")
        score_candidates.append(cosine)
        if shared_terms:
            parts.append(
                f"Cosine {cosine:.3f}; shared terms: {', '.join(shared_terms)}."
            )
        else:
            parts.append(f"Cosine {cosine:.3f}.")
    elif cosine is not None:
        parts.append(f"Cosine {cosine:.3f} (below {settings.sim_threshold} threshold).")

    if shared_tags:
        methods.append("tag-overlap")
        jaccard = len(shared_tags) / max(1, tags_union_size)
        score_candidates.append(min(1.0, jaccard))
        parts.append(
            "Shared tags: " + ", ".join("#" + t for t in shared_tags) + "."
        )

    if pinned:
        methods.append("pinned")
        score_candidates.append(1.0)
        parts.append("Pinned by user.")

    method = "+".join(methods) if methods else "manual"
    score = max(score_candidates) if score_candidates else 0.0
    reason = " ".join(parts) if parts else "Manual edge."
    return method, reason, score


# -------- core ops ---------------------------------------------------------

def recompute_edges_for(note_id: int) -> int:
    """Recompute every edge touching `note_id`, honoring overrides and tags."""
    conn = get_conn()
    row = conn.execute(
        "SELECT title, body FROM notes WHERE id = ?", (note_id,)
    ).fetchone()
    if row is None:
        return 0
    me_text = f"{row['title']}\n\n{row['body']}".strip()
    me_tags = extract_tags(me_text)

    me_vec_row = conn.execute(
        "SELECT embedding FROM note_vec WHERE note_id = ?", (note_id,)
    ).fetchone()
    me_vec = _decode_vec(me_vec_row["embedding"]) if me_vec_row else None

    override_rows = conn.execute(
        "SELECT source_id, target_id, kind FROM edge_overrides "
        "WHERE source_id = ? OR target_id = ?",
        (note_id, note_id),
    ).fetchall()
    overrides = {(r["source_id"], r["target_id"]): r["kind"] for r in override_rows}

    others = conn.execute(
        "SELECT n.id, n.title, n.body, v.embedding "
        "FROM notes n LEFT JOIN note_vec v ON v.note_id = n.id "
        "WHERE n.id != ?",
        (note_id,),
    ).fetchall()

    written = 0
    with tx() as c:
        c.execute(
            "DELETE FROM edges WHERE source_id = ? OR target_id = ?",
            (note_id, note_id),
        )
        for other in others:
            other_id = other["id"]
            a, b = sorted((note_id, other_id))
            override = overrides.get((a, b))
            if override == "suppressed":
                continue

            other_vec = (
                _decode_vec(other["embedding"]) if other["embedding"] else None
            )
            cosine: float | None = None
            if (
                me_vec is not None
                and other_vec is not None
                and me_vec.shape == other_vec.shape
            ):
                cosine = float(np.dot(me_vec, other_vec))

            other_text = f"{other['title']}\n\n{other['body']}".strip()
            other_tags = extract_tags(other_text)
            shared_tags = sorted(me_tags & other_tags)
            tags_union = len(me_tags | other_tags)

            pinned = override == "pinned"
            above_thr = cosine is not None and cosine >= settings.sim_threshold
            include = pinned or above_thr or bool(shared_tags)
            if not include:
                continue

            shared = _shared_terms(me_text, other_text)
            method, reason, score = _compose_edge(
                cosine, shared, shared_tags, tags_union, pinned
            )
            c.execute(
                "INSERT OR REPLACE INTO edges"
                "(source_id, target_id, score, method, reason) "
                "VALUES (?, ?, ?, ?, ?)",
                (a, b, score, method, reason),
            )
            written += 1
    recompute_clusters()
    return written


def recompute_clusters() -> None:
    """Run Louvain on the similarity graph; persist note → cluster mapping
    and an auto-generated label per cluster."""
    import networkx as nx

    try:
        import community as community_louvain  # python-louvain
    except ImportError:  # pragma: no cover
        community_louvain = None

    conn = get_conn()
    notes = [r["id"] for r in conn.execute("SELECT id FROM notes").fetchall()]
    edges = conn.execute(
        "SELECT source_id, target_id, score FROM edges"
    ).fetchall()

    g = nx.Graph()
    g.add_nodes_from(notes)
    for e in edges:
        g.add_edge(e["source_id"], e["target_id"], weight=e["score"])

    if community_louvain is not None and g.number_of_edges() > 0:
        partition = community_louvain.best_partition(g, weight="weight")
    else:
        partition = {
            n: i
            for i, comp in enumerate(nx.connected_components(g))
            for n in comp
        }

    members: dict[int, list[int]] = {}
    for note_id, cid in partition.items():
        members.setdefault(cid, []).append(note_id)

    labels = {cid: _label_for_cluster(conn, ids) for cid, ids in members.items()}

    with tx() as c:
        c.execute("DELETE FROM note_cluster")
        c.execute("DELETE FROM clusters")
        for cid in sorted(members):
            c.execute(
                "INSERT INTO clusters(id, label) VALUES (?, ?)",
                (cid, labels[cid]),
            )
        for note_id, cid in partition.items():
            c.execute(
                "INSERT INTO note_cluster(note_id, cluster_id) VALUES (?, ?)",
                (note_id, cid),
            )


def _label_for_cluster(conn, note_ids: list[int], k: int = 3) -> str:
    if not note_ids:
        return "(empty)"
    rows = conn.execute(
        f"SELECT title, body FROM notes WHERE id IN "
        f"({','.join('?' * len(note_ids))})",
        note_ids,
    ).fetchall()
    if len(rows) == 1:
        title = (rows[0]["title"] or "").strip()
        return title or "(untitled)"
    doc_freq: Counter[str] = Counter()
    for r in rows:
        text = f"{r['title']}\n{r['body']}"
        terms = set(_tokenize(text))
        tags = {"#" + t for t in extract_tags(text)}
        doc_freq.update(terms | tags)
    top = [t for t, count in doc_freq.most_common(k) if count >= 2]
    if not top:
        for r in rows:
            t = (r["title"] or "").strip()
            if t:
                return t
        return "(cluster)"
    return ", ".join(top)


# -------- lifecycle hooks --------------------------------------------------

def on_note_edit(note_id: int, title: str, body: str) -> None:
    """Re-embed and recompute edges for the note. Called on PUT."""
    text = f"{title}\n\n{body}".strip()
    if not text:
        on_note_clear_links(note_id)
        return
    vec = embed(text)
    if vec.shape[0] != EMBED_DIM:
        raise RuntimeError(
            f"Embedding dim {vec.shape[0]} != configured {EMBED_DIM}. "
            "Update EMBED_DIM in app/db.py to match the model."
        )
    store_embedding(note_id, vec)
    recompute_edges_for(note_id)


def on_note_clear_links(note_id: int) -> None:
    with tx() as c:
        c.execute("DELETE FROM note_vec WHERE note_id = ?", (note_id,))
        c.execute(
            "DELETE FROM edges WHERE source_id = ? OR target_id = ?",
            (note_id, note_id),
        )
    recompute_clusters()


def on_note_delete(note_id: int) -> None:
    with tx() as c:
        c.execute("DELETE FROM note_vec WHERE note_id = ?", (note_id,))
        c.execute(
            "DELETE FROM edges WHERE source_id = ? OR target_id = ?",
            (note_id, note_id),
        )
        c.execute(
            "DELETE FROM edge_overrides WHERE source_id = ? OR target_id = ?",
            (note_id, note_id),
        )
    recompute_clusters()


# -------- override ops -----------------------------------------------------

def set_edge_override(a: int, b: int, kind: str | None) -> None:
    """kind in {'pinned','suppressed', None}. None removes the override."""
    if a == b:
        raise ValueError("self-loops not allowed")
    lo, hi = sorted((a, b))
    conn = get_conn()
    if kind is None:
        conn.execute(
            "DELETE FROM edge_overrides WHERE source_id = ? AND target_id = ?",
            (lo, hi),
        )
    else:
        if kind not in ("pinned", "suppressed"):
            raise ValueError(f"bad kind {kind!r}")
        conn.execute(
            "INSERT OR REPLACE INTO edge_overrides"
            "(source_id, target_id, kind) VALUES (?, ?, ?)",
            (lo, hi, kind),
        )
    conn.commit()
    # Re-derive edges for both endpoints so the change takes effect now.
    recompute_edges_for(lo)
    recompute_edges_for(hi)
