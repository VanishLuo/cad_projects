from __future__ import annotations

import unicodedata


def normalize_local_path_text(path_text: str) -> str:
    """Normalize imported path text for local file existence checks.

    Excel and copy-paste operations may introduce invisible Unicode formatting
    characters (for example U+202A) that break Path.is_file().
    """

    text = path_text.strip().strip('"').strip("'")
    cleaned_chars: list[str] = []
    for char in text:
        # Drop Unicode formatting marks (category Cf), keep printable chars.
        if unicodedata.category(char) == "Cf":
            continue
        cleaned_chars.append(char)
    return "".join(cleaned_chars).strip()