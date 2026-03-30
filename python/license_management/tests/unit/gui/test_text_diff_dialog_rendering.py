from __future__ import annotations

from typing import Any
from typing import cast

from license_management.gui.dialogs.text_diff_dialog import TextDiffDialog
from license_management.gui.dialogs.text_diff_dialog import _qt_enum_member


def test_text_diff_colored_html_marks_changes_for_each_side() -> None:
    class _Proxy:
        def _render_lines(
            self,
            lines: list[str],
            start_no: int,
            *,
            bg: str,
            prefix: str = "",
        ) -> str:
            return TextDiffDialog._render_lines(
                cast(Any, self),
                lines,
                start_no,
                bg=bg,
                prefix=prefix,
            )

    proxy = _Proxy()
    left_html = TextDiffDialog._build_colored_html(
        cast(Any, proxy),
        left_text="a\nb\nc",
        right_text="a\nx\nc\nd",
        side="left",
    )
    right_html = TextDiffDialog._build_colored_html(
        cast(Any, proxy),
        left_text="a\nb\nc",
        right_text="a\nx\nc\nd",
        side="right",
    )

    assert "#ffe082" in left_html
    assert "~ " in left_html
    assert "#c8e6c9" in right_html
    assert "+ " in right_html


def test_render_lines_escapes_html_and_prefixes_line_numbers() -> None:
    class _Proxy:
        pass

    html_text = TextDiffDialog._render_lines(
        cast(Any, _Proxy()),
        ["<danger>", "safe"],
        10,
        bg="#abc",
        prefix="+ ",
    )

    assert "&lt;danger&gt;" in html_text
    assert "#abc" in html_text
    assert "  10" in html_text
    assert "+ " in html_text


def test_qt_enum_member_works_for_plain_owner_and_nested_enum() -> None:
    class _NestedOwner:
        class Orientation:
            Horizontal = 7

    class _PlainOwner:
        Horizontal = 9

    assert _qt_enum_member(_NestedOwner, "Orientation", "Horizontal") == 7
    assert _qt_enum_member(_PlainOwner, "Orientation", "Horizontal") == 9
