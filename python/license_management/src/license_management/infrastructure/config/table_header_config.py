from __future__ import annotations

import json
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import cast

_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

_RECORD_FIELDS = (
    "record_id",
    "server_name",
    "provider",
    "prot",
    "feature_name",
    "process_name",
    "expires_on",
    "vendor",
    "start_executable_path",
    "license_file_path",
    "start_option_override",
)

_MIN_SQLITE_FIELDS = ("record_id",)

_GUI_FIELDS = (
    "record_id",
    "server_name",
    "prot",
    "provider",
    "vendor",
    "start_executable_path",
    "license_file_path",
    "status",
)


@dataclass(slots=True, frozen=True)
class TableHeaderConfig:
    sqlite_table_name: str
    sqlite_columns: dict[str, str]
    gui_column_order: tuple[str, ...]
    gui_headers: dict[str, str]


@lru_cache(maxsize=1)
def load_table_header_config() -> TableHeaderConfig:
    config_path = Path(__file__).resolve().parents[2] / "config" / "table_headers.json"
    raw = json.loads(config_path.read_text(encoding="utf-8"))
    data = _to_str_object_dict(raw)

    sqlite_raw = _to_str_object_dict(data.get("sqlite"))
    table_name = _sanitize_identifier(str(sqlite_raw.get("table_name", "license_records")))

    columns_raw = _to_str_object_dict(sqlite_raw.get("columns"))
    sqlite_columns: dict[str, str] = {}
    for field, value in columns_raw.items():
        if field not in _RECORD_FIELDS:
            continue
        sqlite_columns[field] = _sanitize_identifier(str(value))

    for required in _MIN_SQLITE_FIELDS:
        if required not in sqlite_columns:
            raise ValueError(f"Missing required sqlite column mapping: {required}")

    gui_raw = _to_str_object_dict(data.get("gui"))
    order_raw = gui_raw.get("column_order")
    gui_order = _normalize_gui_order(order_raw)

    headers_raw = _to_str_object_dict(gui_raw.get("headers"))
    gui_headers: dict[str, str] = {}
    for field in gui_order:
        gui_headers[field] = str(headers_raw.get(field, field)).strip() or field

    return TableHeaderConfig(
        sqlite_table_name=table_name,
        sqlite_columns=sqlite_columns,
        gui_column_order=gui_order,
        gui_headers=gui_headers,
    )


def _normalize_gui_order(value: object) -> tuple[str, ...]:
    if not isinstance(value, list):
        return _GUI_FIELDS

    typed = cast(list[object], value)
    normalized: list[str] = []
    for item in typed:
        text = str(item).strip()
        if text in _GUI_FIELDS and text not in normalized:
            normalized.append(text)

    if not normalized:
        return _GUI_FIELDS

    return tuple(normalized)


def _sanitize_identifier(name: str) -> str:
    cleaned = name.strip()
    if not _IDENTIFIER_RE.fullmatch(cleaned):
        raise ValueError(f"Invalid SQL identifier in table header config: {name}")
    return cleaned


def _to_str_object_dict(value: object) -> dict[str, object]:
    if not isinstance(value, dict):
        return {}
    typed = cast(dict[object, object], value)
    result: dict[str, object] = {}
    for key, item in typed.items():
        if isinstance(key, str):
            result[key] = item
    return result
