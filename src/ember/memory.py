"""Explicitly requested, locally stored Ember memories."""

from __future__ import annotations

import os
from pathlib import Path
import sqlite3
import threading


class LocalMemoryStore:
    def __init__(self, path: Path | None = None) -> None:
        data_home = Path(
            os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share")
        )
        self.path = path or data_home / "ember" / "memory.sqlite3"
        self._lock = threading.RLock()

    def _connect(self) -> sqlite3.Connection:
        self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        try:
            self.path.parent.chmod(0o700)
        except OSError:
            pass
        connection = sqlite3.connect(self.path)
        connection.execute(
            "CREATE TABLE IF NOT EXISTS memories ("
            "id INTEGER PRIMARY KEY, fact TEXT NOT NULL UNIQUE, "
            "created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)"
        )
        try:
            self.path.chmod(0o600)
        except OSError:
            pass
        return connection

    def add(self, fact: str) -> bool:
        cleaned = fact.strip()
        if not cleaned or len(cleaned) > 1000:
            raise ValueError("الذكرى يجب أن تكون بين حرف واحد و1000 حرف.")
        with self._lock:
            connection = self._connect()
            try:
                cursor = connection.execute(
                    "INSERT OR IGNORE INTO memories(fact) VALUES (?)", (cleaned,)
                )
                connection.commit()
                return cursor.rowcount > 0
            finally:
                connection.close()

    def list_all(self) -> list[tuple[int, str]]:
        if not self.path.is_file():
            return []
        with self._lock:
            connection = self._connect()
            try:
                rows = connection.execute(
                    "SELECT id, fact FROM memories ORDER BY id DESC"
                ).fetchall()
            finally:
                connection.close()
        return [(int(row[0]), str(row[1])) for row in rows]

    def search(self, query: str = "") -> list[str]:
        facts = [fact for _memory_id, fact in self.list_all()]
        terms = [term.casefold() for term in query.split() if term]
        if not terms:
            return facts
        matching = [
            fact for fact in facts
            if all(term in fact.casefold() for term in terms)
        ]
        return matching

    def remove(self, memory_id: int) -> bool:
        with self._lock:
            connection = self._connect()
            try:
                cursor = connection.execute(
                    "DELETE FROM memories WHERE id = ?", (memory_id,)
                )
                connection.commit()
                return cursor.rowcount > 0
            finally:
                connection.close()

    def remove_fact(self, fact: str) -> bool:
        with self._lock:
            connection = self._connect()
            try:
                cursor = connection.execute(
                    "DELETE FROM memories WHERE fact = ?", (fact.strip(),)
                )
                connection.commit()
                return cursor.rowcount > 0
            finally:
                connection.close()
