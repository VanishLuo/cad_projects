from __future__ import annotations

from license_management.shared.path_normalization import normalize_local_path_text


def test_normalize_local_path_text_removes_invisible_format_chars() -> None:
    raw = "\u202aC:\\Users\\luozhenyu\\Desktop\\a.txt"
    normalized = normalize_local_path_text(raw)
    assert normalized == "C:\\Users\\luozhenyu\\Desktop\\a.txt"
