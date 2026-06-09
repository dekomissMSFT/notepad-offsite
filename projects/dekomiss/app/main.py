"""FastAPI app: notes CRUD, graph fetch, edges, import/export, static UI."""
from __future__ import annotations

import io
import re
import zipfile
from pathlib import Path
from typing import List

from fastapi import FastAPI, HTTPException, Query, UploadFile, File
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from . import graph
from .config import settings
from .db import get_conn

app = FastAPI(title="Note Graph")

STATIC_DIR = Path(__file__).parent / "static"


class NoteIn(BaseModel):
    title: str = ""
    body: str = ""


class NoteOut(BaseModel):
    id: int
    title: str
    body: str
    created_at: str
    updated_at: str


@app.on_event("startup")
def _startup() -> None:
    get_conn()


# ---- notes ---------------------------------------------------------------

@app.get("/api/notes", response_model=list[NoteOut])
def list_notes() -> list[NoteOut]:
    rows = get_conn().execute(
        "SELECT id, title, body, created_at, updated_at FROM notes ORDER BY id"
    ).fetchall()
    return [NoteOut(**dict(r)) for r in rows]


@app.post("/api/notes", response_model=NoteOut)
def create_note(payload: NoteIn) -> NoteOut:
    conn = get_conn()
    cur = conn.execute(
        "INSERT INTO notes(title, body) VALUES (?, ?)",
        (payload.title, payload.body),
    )
    conn.commit()
    # No embed/edges on create — only on edit.
    return _get_note(int(cur.lastrowid))


@app.get("/api/notes/{note_id}", response_model=NoteOut)
def get_note(note_id: int) -> NoteOut:
    return _get_note(note_id)


@app.put("/api/notes/{note_id}", response_model=NoteOut)
def update_note(note_id: int, payload: NoteIn) -> NoteOut:
    conn = get_conn()
    cur = conn.execute(
        "UPDATE notes SET title = ?, body = ?, updated_at = datetime('now') "
        "WHERE id = ?",
        (payload.title, payload.body, note_id),
    )
    if cur.rowcount == 0:
        raise HTTPException(404, "note not found")
    conn.commit()
    graph.on_note_edit(note_id, payload.title, payload.body)
    return _get_note(note_id)


@app.delete("/api/notes/{note_id}")
def delete_note(note_id: int) -> dict:
    conn = get_conn()
    cur = conn.execute("DELETE FROM notes WHERE id = ?", (note_id,))
    if cur.rowcount == 0:
        raise HTTPException(404, "note not found")
    conn.commit()
    graph.on_note_delete(note_id)
    return {"ok": True}


# ---- graph ---------------------------------------------------------------

@app.get("/api/graph")
def get_graph(
    min_score: float = Query(0.0, ge=0.0, le=1.0),
) -> dict:
    conn = get_conn()
    notes = conn.execute(
        "SELECT n.id, n.title, COALESCE(nc.cluster_id, -1) AS cluster_id "
        "FROM notes n LEFT JOIN note_cluster nc ON nc.note_id = n.id"
    ).fetchall()
    edges = conn.execute(
        "SELECT source_id, target_id, score, method FROM edges"
    ).fetchall()
    clusters = conn.execute(
        "SELECT c.id, c.label, COUNT(nc.note_id) AS size "
        "FROM clusters c LEFT JOIN note_cluster nc ON nc.cluster_id = c.id "
        "GROUP BY c.id ORDER BY size DESC, c.id"
    ).fetchall()

    def keep(e) -> bool:
        # Always keep user-asserted edges regardless of slider.
        if "pinned" in e["method"] or "manual" in e["method"] or "tag-overlap" in e["method"]:
            return True
        return e["score"] >= min_score

    return {
        "nodes": [
            {
                "data": {
                    "id": str(n["id"]),
                    "label": n["title"] or f"Note {n['id']}",
                    "cluster": int(n["cluster_id"]),
                }
            }
            for n in notes
        ],
        "edges": [
            {
                "data": {
                    "id": f"{e['source_id']}-{e['target_id']}",
                    "source": str(e["source_id"]),
                    "target": str(e["target_id"]),
                    "score": float(e["score"]),
                    "method": e["method"],
                }
            }
            for e in edges if keep(e)
        ],
        "clusters": [
            {"id": int(c["id"]), "label": c["label"], "size": int(c["size"])}
            for c in clusters
        ],
    }


# ---- edges ---------------------------------------------------------------

@app.get("/api/edges/{a}/{b}")
def explain_edge(a: int, b: int) -> dict:
    lo, hi = sorted((a, b))
    row = get_conn().execute(
        "SELECT source_id, target_id, score, method, reason, created_at "
        "FROM edges WHERE source_id = ? AND target_id = ?",
        (lo, hi),
    ).fetchone()
    ovr = get_conn().execute(
        "SELECT kind FROM edge_overrides WHERE source_id = ? AND target_id = ?",
        (lo, hi),
    ).fetchone()
    if row is None and ovr is None:
        raise HTTPException(404, "edge not found")
    result = dict(row) if row else {
        "source_id": lo, "target_id": hi, "score": 0.0,
        "method": "suppressed", "reason": "Edge suppressed by user.",
        "created_at": "",
    }
    result["override"] = ovr["kind"] if ovr else None
    return result


@app.post("/api/edges/{a}/{b}/pin")
def pin_edge(a: int, b: int) -> dict:
    graph.set_edge_override(a, b, "pinned")
    return {"ok": True, "override": "pinned"}


@app.post("/api/edges/{a}/{b}/suppress")
def suppress_edge(a: int, b: int) -> dict:
    graph.set_edge_override(a, b, "suppressed")
    return {"ok": True, "override": "suppressed"}


@app.delete("/api/edges/{a}/{b}/override")
def clear_edge_override(a: int, b: int) -> dict:
    graph.set_edge_override(a, b, None)
    return {"ok": True, "override": None}


# ---- import / export ----------------------------------------------------

_SLUG_RE = re.compile(r"[^a-z0-9-]+")


def _slugify(s: str) -> str:
    s = s.lower().strip().replace(" ", "-")
    s = _SLUG_RE.sub("", s)
    return s[:60] or "note"


@app.post("/api/import")
async def import_markdown(files: List[UploadFile] = File(...)) -> dict:
    created = 0
    conn = get_conn()
    for up in files:
        raw = (await up.read()).decode("utf-8", errors="replace")
        title = ""
        body = raw
        # Use first H1 as title, else strip .md filename.
        m = re.search(r"^#\s+(.+)$", raw, re.MULTILINE)
        if m:
            title = m.group(1).strip()
            body = raw[: m.start()] + raw[m.end():]
            body = body.lstrip("\n")
        else:
            title = Path(up.filename or "note").stem
        cur = conn.execute(
            "INSERT INTO notes(title, body) VALUES (?, ?)", (title, body)
        )
        conn.commit()
        graph.on_note_edit(int(cur.lastrowid), title, body)
        created += 1
    return {"ok": True, "created": created}


@app.get("/api/export")
def export_markdown() -> StreamingResponse:
    conn = get_conn()
    rows = conn.execute("SELECT id, title, body FROM notes ORDER BY id").fetchall()
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for r in rows:
            name = f"{r['id']:04d}-{_slugify(r['title'] or 'note')}.md"
            title = r["title"] or ""
            content = (f"# {title}\n\n" if title else "") + (r["body"] or "")
            zf.writestr(name, content)
    buf.seek(0)
    return StreamingResponse(
        buf,
        media_type="application/zip",
        headers={"Content-Disposition": 'attachment; filename="notes.zip"'},
    )


# ---- helpers + static ----------------------------------------------------

def _get_note(note_id: int) -> NoteOut:
    row = get_conn().execute(
        "SELECT id, title, body, created_at, updated_at FROM notes WHERE id = ?",
        (note_id,),
    ).fetchone()
    if row is None:
        raise HTTPException(404, "note not found")
    return NoteOut(**dict(row))


app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/")
def index() -> FileResponse:
    return FileResponse(str(STATIC_DIR / "index.html"))


def main() -> None:
    import uvicorn

    uvicorn.run("app.main:app", host=settings.host, port=settings.port, reload=False)


if __name__ == "__main__":
    main()
