from __future__ import annotations

import sqlite3
from pathlib import Path
from threading import Lock


class Database:
    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path)
        self.__lock = Lock()

        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "CREATE TABLE IF NOT EXISTS downloads (track_id TEXT PRIMARY KEY, filename TEXT)",
            )

    def get(self, track_id: int) -> str | None:
        with self.__lock, sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT filename FROM downloads WHERE track_id = ?",
                (track_id,),
            ).fetchone()
            return row[0] if row else None

    def set(self, track_id: int, filename: str):
        with self.__lock, sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO downloads (track_id, filename) VALUES (?, ?)",
                (track_id, filename),
            )
