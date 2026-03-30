from __future__ import annotations

import sqlite3
from pathlib import Path


class SqliteLicenseTextSnapshotRepository:
    """Manage persisted initial/current license text snapshots."""

    def __init__(self, db_path: Path, *, table_name: str, id_column: str) -> None:
        self._db_path = db_path
        self._table_name = table_name
        self._id_column = id_column

    def ensure_schema(self, conn: sqlite3.Connection) -> None:
        conn.execute(f"""
            CREATE TABLE IF NOT EXISTS {self._table_name} (
                {self._id_column} TEXT PRIMARY KEY,
                initial_text TEXT NOT NULL DEFAULT '',
                current_text TEXT NOT NULL DEFAULT ''
            )
            """)

    def upsert(
        self,
        record_id: str,
        *,
        initial_text: str | None = None,
        current_text: str | None = None,
    ) -> None:
        if record_id.strip() == "":
            return

        with sqlite3.connect(self._db_path) as conn:
            row = conn.execute(
                f"""
                SELECT initial_text, current_text
                FROM {self._table_name}
                WHERE {self._id_column} = ?
                """,
                (record_id,),
            ).fetchone()

            if row is None:
                initial_value = initial_text if initial_text is not None else ""
                current_value = current_text if current_text is not None else initial_value
                conn.execute(
                    f"""
                    INSERT INTO {self._table_name}
                    ({self._id_column}, initial_text, current_text)
                    VALUES (?, ?, ?)
                    """,
                    (record_id, initial_value, current_value),
                )
                conn.commit()
                return

            existing_initial = str(row[0]) if row[0] is not None else ""
            existing_current = str(row[1]) if row[1] is not None else ""
            new_initial = existing_initial if existing_initial != "" else (initial_text or "")
            new_current = existing_current if current_text is None else current_text
            conn.execute(
                f"""
                UPDATE {self._table_name}
                SET initial_text = ?, current_text = ?
                WHERE {self._id_column} = ?
                """,
                (new_initial, new_current, record_id),
            )
            conn.commit()

    def get(self, record_id: str) -> tuple[str, str] | None:
        with sqlite3.connect(self._db_path) as conn:
            row = conn.execute(
                f"""
                SELECT initial_text, current_text
                FROM {self._table_name}
                WHERE {self._id_column} = ?
                """,
                (record_id,),
            ).fetchone()
        if row is None:
            return None
        return (
            str(row[0]) if row[0] is not None else "",
            str(row[1]) if row[1] is not None else "",
        )

    def delete(self, record_id: str, *, conn: sqlite3.Connection | None = None) -> None:
        if conn is None:
            with sqlite3.connect(self._db_path) as own_conn:
                own_conn.execute(
                    f"DELETE FROM {self._table_name} WHERE {self._id_column} = ?",
                    (record_id,),
                )
                own_conn.commit()
            return

        conn.execute(
            f"DELETE FROM {self._table_name} WHERE {self._id_column} = ?",
            (record_id,),
        )

    def sync_rows_with_committed(self, conn: sqlite3.Connection, *, committed_table: str) -> None:
        conn.execute(f"""
            DELETE FROM {self._table_name}
            WHERE {self._id_column} NOT IN (
                SELECT {self._id_column} FROM {committed_table}
            )
            """)
