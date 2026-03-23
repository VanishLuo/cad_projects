from __future__ import annotations

import sqlite3
from pathlib import Path


class SchemaMigrator:
    """Applies idempotent SQLite schema migrations with version tracking."""

    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path

    def initialize(self) -> None:
        with sqlite3.connect(self._db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    migration_id TEXT PRIMARY KEY,
                    applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """)
            conn.commit()

    def applied_migrations(self) -> set[str]:
        self.initialize()
        with sqlite3.connect(self._db_path) as conn:
            rows = conn.execute(
                "SELECT migration_id FROM schema_migrations ORDER BY migration_id"
            ).fetchall()
        return {row[0] for row in rows}

    def apply_migration(self, migration_id: str, sql: str) -> bool:
        """Applies one migration once. Returns True if applied, False if already applied."""
        self.initialize()
        with sqlite3.connect(self._db_path) as conn:
            exists = conn.execute(
                "SELECT 1 FROM schema_migrations WHERE migration_id = ?",
                (migration_id,),
            ).fetchone()
            if exists is not None:
                return False

            conn.executescript(sql)
            conn.execute(
                "INSERT INTO schema_migrations (migration_id) VALUES (?)",
                (migration_id,),
            )
            conn.commit()
        return True

    def apply_baseline_v1(self) -> bool:
        """Creates baseline tables required by the repository layer."""
        sql = """
        CREATE TABLE IF NOT EXISTS license_records (
            record_id TEXT PRIMARY KEY,
            server_name TEXT NOT NULL,
            provider TEXT NOT NULL,
            feature_name TEXT NOT NULL,
            process_name TEXT NOT NULL,
            expires_on TEXT NOT NULL,
            vendor TEXT NOT NULL DEFAULT '',
            start_executable_path TEXT NOT NULL DEFAULT '',
            license_file_path TEXT NOT NULL DEFAULT '',
            start_option_override TEXT NOT NULL DEFAULT ''
        );
        CREATE INDEX IF NOT EXISTS idx_license_records_provider
            ON license_records(provider);
        CREATE INDEX IF NOT EXISTS idx_license_records_expires_on
            ON license_records(expires_on);
        """
        return self.apply_migration("0001_baseline", sql)

    def apply_record_fields_v2(self) -> bool:
        """Adds newer record fields for command-path based workflows."""
        self.initialize()
        with sqlite3.connect(self._db_path) as conn:
            rows = conn.execute("PRAGMA table_info(license_records)").fetchall()
            existing_columns = {str(row[1]) for row in rows}

            alter_statements: list[str] = []
            if "vendor" not in existing_columns:
                alter_statements.append(
                    "ALTER TABLE license_records ADD COLUMN vendor TEXT NOT NULL DEFAULT ''"
                )
            if "start_executable_path" not in existing_columns:
                alter_statements.append(
                    "ALTER TABLE license_records ADD COLUMN start_executable_path TEXT NOT NULL DEFAULT ''"
                )
            if "license_file_path" not in existing_columns:
                alter_statements.append(
                    "ALTER TABLE license_records ADD COLUMN license_file_path TEXT NOT NULL DEFAULT ''"
                )
            if "start_option_override" not in existing_columns:
                alter_statements.append(
                    "ALTER TABLE license_records ADD COLUMN start_option_override TEXT NOT NULL DEFAULT ''"
                )

            if not alter_statements:
                return False

            for sql in alter_statements:
                conn.execute(sql)

            conn.execute(
                "INSERT OR IGNORE INTO schema_migrations (migration_id) VALUES (?)",
                ("0002_record_fields",),
            )
            conn.commit()
        return True
