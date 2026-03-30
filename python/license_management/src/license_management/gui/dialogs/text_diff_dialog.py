from __future__ import annotations

import difflib
import html
from typing import Any

from license_management.gui.qt_compat import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSplitter,
    QTextEdit,
    Qt,
    QVBoxLayout,
    QWidget,
)


class TextDiffDialog(QDialog):
    """Display side-by-side text compare with color highlights."""

    def __init__(
        self,
        *,
        title: str,
        summary: str,
        left_title: str,
        right_title: str,
        left_text: str,
        right_text: str,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("TextDiffDialog")
        self.setWindowTitle(title)
        self.resize(980, 680)

        summary_label = QLabel(summary)
        summary_label.setWordWrap(True)

        left_header = QLabel(left_title)
        right_header = QLabel(right_title)

        left_viewer = QTextEdit()
        left_viewer.setReadOnly(True)
        left_viewer.setLineWrapMode(QTextEdit.NoWrap)
        left_viewer.setHtml(
            self._build_colored_html(left_text=left_text, right_text=right_text, side="left")
        )

        right_viewer = QTextEdit()
        right_viewer.setReadOnly(True)
        right_viewer.setLineWrapMode(QTextEdit.NoWrap)
        right_viewer.setHtml(
            self._build_colored_html(left_text=left_text, right_text=right_text, side="right")
        )

        left_panel = QWidget()
        left_layout = QVBoxLayout()
        left_layout.addWidget(left_header)
        left_layout.addWidget(left_viewer)
        left_panel.setLayout(left_layout)

        right_panel = QWidget()
        right_layout = QVBoxLayout()
        right_layout.addWidget(right_header)
        right_layout.addWidget(right_viewer)
        right_panel.setLayout(right_layout)

        splitter = QSplitter(_qt_enum_member(Qt, "Orientation", "Horizontal"))
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([1, 1])

        legend = QLabel(
            "Legend: <span style='background:#ffe082;'>changed</span>  <span style='background:#ffcdd2;'>removed</span>  <span style='background:#c8e6c9;'>added</span>"
        )
        legend.setWordWrap(True)

        close_btn = QPushButton("Close")
        close_btn.setObjectName("DialogCloseButton")
        close_btn.clicked.connect(self.accept)

        layout = QVBoxLayout()
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        layout.addWidget(summary_label)
        layout.addWidget(legend)
        layout.addWidget(splitter, 1)

        footer = QHBoxLayout()
        footer.addStretch(1)
        footer.addWidget(close_btn)
        layout.addLayout(footer)
        self.setLayout(layout)

    def _build_colored_html(self, *, left_text: str, right_text: str, side: str) -> str:
        left_lines = left_text.splitlines()
        right_lines = right_text.splitlines()
        matcher = difflib.SequenceMatcher(a=left_lines, b=right_lines)

        chunks: list[str] = []
        if side == "left":
            line_no = 1
        else:
            line_no = 1

        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if side == "left":
                if tag == "equal":
                    chunks.append(self._render_lines(left_lines[i1:i2], line_no, bg=""))
                    line_no += i2 - i1
                elif tag == "replace":
                    chunks.append(
                        self._render_lines(left_lines[i1:i2], line_no, bg="#ffe082", prefix="~ ")
                    )
                    line_no += i2 - i1
                elif tag == "delete":
                    chunks.append(
                        self._render_lines(left_lines[i1:i2], line_no, bg="#ffcdd2", prefix="- ")
                    )
                    line_no += i2 - i1
                elif tag == "insert":
                    continue
            else:
                if tag == "equal":
                    chunks.append(self._render_lines(right_lines[j1:j2], line_no, bg=""))
                    line_no += j2 - j1
                elif tag == "replace":
                    chunks.append(
                        self._render_lines(right_lines[j1:j2], line_no, bg="#ffe082", prefix="~ ")
                    )
                    line_no += j2 - j1
                elif tag == "delete":
                    continue
                elif tag == "insert":
                    chunks.append(
                        self._render_lines(right_lines[j1:j2], line_no, bg="#c8e6c9", prefix="+ ")
                    )
                    line_no += j2 - j1

        body = "".join(chunks)
        return (
            "<html><body style='font-family:\"SF Mono\", Menlo, Monaco, Consolas, 'Courier New', monospace; font-size:10px;'>"
            f"{body}"
            "</body></html>"
        )

    def _render_lines(self, lines: list[str], start_no: int, *, bg: str, prefix: str = "") -> str:
        if not lines:
            return ""
        parts: list[str] = []
        style = "padding:1px 4px; white-space:pre;"
        if bg != "":
            style += f" background:{bg};"

        line_no = start_no
        for line in lines:
            escaped = html.escape(line)
            parts.append(
                f"<div style='{style}'><span style='color:#666666;'>{line_no:>4}</span> {html.escape(prefix)}{escaped}</div>"
            )
            line_no += 1
        return "".join(parts)


def _qt_enum_member(owner: object, enum_name: str, member_name: str) -> Any:
    enum_owner = getattr(owner, enum_name, owner)
    return getattr(enum_owner, member_name)
