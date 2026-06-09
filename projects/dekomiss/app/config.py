import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    db_path: str = os.environ.get("NOTE_GRAPH_DB", "notes.db")
    model_name: str = os.environ.get("NOTE_GRAPH_MODEL", "all-MiniLM-L6-v2")
    sim_threshold: float = float(os.environ.get("NOTE_GRAPH_SIM_THRESHOLD", "0.35"))
    host: str = os.environ.get("NOTE_GRAPH_HOST", "127.0.0.1")
    port: int = int(os.environ.get("NOTE_GRAPH_PORT", "8000"))


settings = Settings()
