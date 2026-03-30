from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path

from license_management.application.license_file_parser import ParsedLicenseFeature
from license_management.domain.models.license_record import LicenseRecord
from license_management.shared.path_normalization import normalize_local_path_text


class SqliteLicenseFeatureRepository:
    """Stores parsed feature snapshots in a dedicated SQLite database."""

    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._committed_table = "license_feature_snapshots"
        self._staging_table = f"{self._committed_table}_staging"
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
            conn.execute(f"""
                INSERT INTO {self._staging_table} (
                    server_name,
                    provider,
                    vendor,
                    license_file_path,
                    feature_name,
                    expires_on,
                    quantity,
                    updated_at
                )
                SELECT
                    server_name,
                    provider,
                    vendor,
                    license_file_path,
                    feature_name,
                    expires_on,
                    quantity,
                    updated_at
                FROM {self._committed_table}
                """)
            conn.commit()
        self._current_workspace = "staging"

    def publish_staging_to_committed(self) -> int:
        with sqlite3.connect(self._db_path) as conn:
            conn.execute("BEGIN IMMEDIATE")
            conn.execute(f"DELETE FROM {self._committed_table}")
            conn.execute(f"""
                INSERT INTO {self._committed_table} (
                    server_name,
                    provider,
                    vendor,
                    license_file_path,
                    feature_name,
                    expires_on,
                    quantity,
                    updated_at
                )
                SELECT
                    server_name,
                    provider,
                    vendor,
                    license_file_path,
                    feature_name,
                    expires_on,
                    quantity,
                    updated_at
                FROM {self._staging_table}
                """)
            row = conn.execute(f"SELECT COUNT(*) FROM {self._committed_table}").fetchone()
            conn.execute(f"DELETE FROM {self._staging_table}")
            conn.commit()
        self._current_workspace = "committed"
        return int(row[0]) if row is not None else 0

    def _active_table(self) -> str:
        return (
            self._staging_table if self._current_workspace == "staging" else self._committed_table
        )

    def _detect_initial_workspace(self) -> str:
        if self._count_rows(self._staging_table) > 0:
            return "staging"
        return "committed"

    def _count_rows(self, table_name: str) -> int:
        with sqlite3.connect(self._db_path) as conn:
            row = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()
        return int(row[0]) if row is not None else 0

    def _ensure_schema(self) -> None:
        with sqlite3.connect(self._db_path) as conn:
            for table_name in (self._committed_table, self._staging_table):
                existing_cols = {
                    str(row[1])
                    for row in conn.execute(f"PRAGMA table_info({table_name})").fetchall()
                }
                # Migrate legacy schema that used composite primary key (dedup behavior).
                if existing_cols and "feature_id" not in existing_cols:
                    conn.execute(f"DROP TABLE {table_name}")

                conn.execute(f"""
                    CREATE TABLE IF NOT EXISTS {table_name} (
                        feature_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        record_id TEXT NOT NULL DEFAULT '',
                        server_name TEXT NOT NULL,
                        provider TEXT NOT NULL,
                        vendor TEXT NOT NULL,
                        license_file_path TEXT NOT NULL,
                        feature_name TEXT NOT NULL,
                        expires_on TEXT NOT NULL,
                        quantity INTEGER NOT NULL,
                        updated_at TEXT NOT NULL
                    )
                    """)

                existing_cols = {
                    str(row[1])
                    for row in conn.execute(f"PRAGMA table_info({table_name})").fetchall()
                }
                if "record_id" not in existing_cols:
                    conn.execute(
                        f"ALTER TABLE {table_name} ADD COLUMN record_id TEXT NOT NULL DEFAULT ''"
                    )
            conn.commit()

    def replace_for_record(
        self, record: LicenseRecord, features: list[ParsedLicenseFeature]
    ) -> None:
        self.delete_for_record(record)
        if not features:
            return

        now = datetime.now().isoformat(timespec="seconds")
        normalized_path = normalize_local_path_text(record.license_file_path)
        table_name = self._active_table()
        with sqlite3.connect(self._db_path) as conn:
            conn.executemany(
                f"""
                INSERT INTO {table_name} (
                    record_id,
                    server_name,
                    provider,
                    vendor,
                    license_file_path,
                    feature_name,
                    expires_on,
                    quantity,
                    updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        record.record_id,
                        record.server_name,
                        record.provider,
                        record.vendor,
                        normalized_path,
                        item.feature_name.strip() or "(empty)",
                        item.expires_on.isoformat(),
                        max(1, int(item.quantity)),
                        now,
                    )
                    for item in features
                ],
            )
            conn.commit()

    def delete_for_record(self, record: LicenseRecord) -> None:
        normalized_path = normalize_local_path_text(record.license_file_path)
        table_name = self._active_table()
        with sqlite3.connect(self._db_path) as conn:
            conn.execute(
                f"""
                DELETE FROM {table_name}
                WHERE record_id = ?
                   OR (
                       record_id = ''
                   AND server_name = ?
                   AND provider = ?
                   AND vendor = ?
                   AND license_file_path = ?
                   )
                """,
                (
                    record.record_id,
                    record.server_name,
                    record.provider,
                    record.vendor,
                    normalized_path,
                ),
            )
            conn.commit()

    def list_for_record(self, record: LicenseRecord) -> list[tuple[str, str, int]]:
        normalized_path = normalize_local_path_text(record.license_file_path)
        table_name = self._active_table()
        with sqlite3.connect(self._db_path) as conn:
            rows = conn.execute(
                f"""
                SELECT feature_name, expires_on, quantity
                FROM {table_name}
                WHERE record_id = ?
                   OR (
                       record_id = ''
                   AND server_name = ?
                   AND provider = ?
                   AND vendor = ?
                   AND license_file_path = ?
                   )
                ORDER BY expires_on, feature_name
                """,
                (
                    record.record_id,
                    record.server_name,
                    record.provider,
                    record.vendor,
                    normalized_path,
                ),
            ).fetchall()

        return [
            (str(feature), str(expires_on), int(quantity)) for feature, expires_on, quantity in rows
        ]
