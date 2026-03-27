from __future__ import annotations

import sqlite3
from datetime import date
from pathlib import Path

from license_management.domain.models.license_record import LicenseRecord
from license_management.infrastructure.config.table_header_config import load_table_header_config


class SqliteLicenseRepository:
    """SQLite-backed repository for persistent license records."""

    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._cfg = load_table_header_config()
        self._committed_table = self._cfg.sqlite_table_name
        self._staging_table = f"{self._committed_table}_staging"
        self._cols = self._cfg.sqlite_columns
        self._id_col = self._cols["record_id"]
        self._ensure_schema()
        self._current_workspace = self._detect_initial_workspace()

    @property
    def current_workspace(self) -> str:
        return self._current_workspace

    def switch_workspace(self, workspace: str) -> None:
        if workspace not in {"staging", "committed"}:
            raise ValueError(f"Unsupported workspace: {workspace}")
        self._current_workspace = workspace

    def enter_staging_workspace(self) -> None:
        if self._current_workspace == "staging":
            return

        with sqlite3.connect(self._db_path) as conn:
            conn.execute("BEGIN IMMEDIATE")
            conn.execute(f"DELETE FROM {self._staging_table}")
            conn.execute(
                f"""
                INSERT INTO {self._staging_table} ({', '.join(self._cols.values())})
                SELECT {', '.join(self._cols.values())} FROM {self._committed_table}
                """
            )
            conn.commit()
        self._current_workspace = "staging"

    def publish_staging_to_committed(self) -> int:
        with sqlite3.connect(self._db_path) as conn:
            conn.execute("BEGIN IMMEDIATE")
            conn.execute(f"DELETE FROM {self._committed_table}")
            conn.execute(
                f"""
                INSERT INTO {self._committed_table} ({', '.join(self._cols.values())})
                SELECT {', '.join(self._cols.values())} FROM {self._staging_table}
                """
            )
            row = conn.execute(f"SELECT COUNT(*) FROM {self._committed_table}").fetchone()
            conn.execute(f"DELETE FROM {self._staging_table}")
            conn.commit()
        self._current_workspace = "committed"
        return int(row[0]) if row is not None else 0

    def _active_table(self) -> str:
        return self._staging_table if self._current_workspace == "staging" else self._committed_table

    def _detect_initial_workspace(self) -> str:
        staging_count = self._count_rows(self._staging_table)
        if staging_count > 0:
            return "staging"
        return "committed"

    def _count_rows(self, table_name: str) -> int:
        with sqlite3.connect(self._db_path) as conn:
            row = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()
        return int(row[0]) if row is not None else 0

    def _ensure_schema(self) -> None:
        create_cols = [f"{self._id_col} TEXT PRIMARY KEY"]
        for field, column in self._cols.items():
            if field == "record_id":
                continue
            create_cols.append(f"{column} TEXT NOT NULL DEFAULT ''")

        committed_sql = f"CREATE TABLE IF NOT EXISTS {self._committed_table} ({', '.join(create_cols)})"
        staging_sql = f"CREATE TABLE IF NOT EXISTS {self._staging_table} ({', '.join(create_cols)})"
        with sqlite3.connect(self._db_path) as conn:
            conn.execute(committed_sql)
            conn.execute(staging_sql)
            for table_name in (self._committed_table, self._staging_table):
                existing_cols = {
                    str(row[1]) for row in conn.execute(f"PRAGMA table_info({table_name})").fetchall()
                }
                for field, column in self._cols.items():
                    if column in existing_cols:
                        continue
                    conn.execute(
                        f"ALTER TABLE {table_name} ADD COLUMN {column} TEXT NOT NULL DEFAULT ''"
                    )
            conn.commit()

    def upsert(self, record: LicenseRecord) -> None:
        columns = list(self._cols.values())
        values = [self._record_field_value(field, record) for field in self._cols.keys()]
        update_cols = [column for column in columns if column != self._id_col]
        update_sql = ", ".join(f"{col} = excluded.{col}" for col in update_cols)
        table_name = self._active_table()
        with sqlite3.connect(self._db_path) as conn:
            conn.execute(
                f"""
                INSERT INTO {table_name} (
                    {', '.join(columns)}
                ) VALUES ({', '.join(['?'] * len(columns))})
                ON CONFLICT({self._id_col}) DO UPDATE SET
                    {update_sql}
                """,
                tuple(values),
            )
            conn.commit()

    def get(self, record_id: str) -> LicenseRecord | None:
        select_cols = list(self._cols.values())
        table_name = self._active_table()
        with sqlite3.connect(self._db_path) as conn:
            row = conn.execute(
                f"""
                SELECT
                    {', '.join(select_cols)}
                FROM {table_name}
                WHERE {self._id_col} = ?
                """,
                (record_id,),
            ).fetchone()

        if row is None:
            return None
        return self._to_record(row, tuple(self._cols.keys()))

    def list_all(self) -> list[LicenseRecord]:
        select_cols = list(self._cols.values())
        table_name = self._active_table()
        with sqlite3.connect(self._db_path) as conn:
            rows = conn.execute(f"""
                SELECT
                    {', '.join(select_cols)}
                FROM {table_name}
                ORDER BY {self._id_col}
                """).fetchall()

        fields = tuple(self._cols.keys())
        return [self._to_record(row, fields) for row in rows]

    def delete(self, record_id: str) -> bool:
        table_name = self._active_table()
        with sqlite3.connect(self._db_path) as conn:
            cursor = conn.execute(
                f"DELETE FROM {table_name} WHERE {self._id_col} = ?",
                (record_id,),
            )
            conn.commit()
            return cursor.rowcount > 0

    def _to_record(self, row: tuple[object, ...], fields: tuple[str, ...]) -> LicenseRecord:
        values_by_field = {field: str(value) for field, value in zip(fields, row)}
        return LicenseRecord(
            record_id=values_by_field.get("record_id", ""),
            server_name=values_by_field.get("server_name", ""),
            provider=values_by_field.get("provider", ""),
            prot=values_by_field.get("prot", ""),
            feature_name=values_by_field.get("feature_name", ""),
            process_name=values_by_field.get("process_name", ""),
            expires_on=self._parse_date(values_by_field.get("expires_on", "")),
            vendor=values_by_field.get("vendor", ""),
            start_executable_path=values_by_field.get("start_executable_path", ""),
            license_file_path=values_by_field.get("license_file_path", ""),
            start_option_override=values_by_field.get("start_option_override", ""),
        )

    def _record_field_value(self, field: str, record: LicenseRecord) -> str:
        if field == "record_id":
            return record.record_id
        if field == "server_name":
            return record.server_name
        if field == "provider":
            return record.provider
        if field == "prot":
            return record.prot
        if field == "feature_name":
            return record.feature_name
        if field == "process_name":
            return record.process_name
        if field == "expires_on":
            return record.expires_on.isoformat()
        if field == "vendor":
            return record.vendor
        if field == "start_executable_path":
            return record.start_executable_path
        if field == "license_file_path":
            return record.license_file_path
        if field == "start_option_override":
            return record.start_option_override
        return ""

    def _parse_date(self, value: str) -> date:
        try:
            return date.fromisoformat(value)
        except ValueError:
            return date.today()
