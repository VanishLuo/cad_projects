from __future__ import annotations

from license_management.application.record_check_service import RecordCheckIssue
from license_management.gui.qt_compat import (
    QDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


class CheckResultDialog(QDialog):
    """Expandable grouped check-result dialog for high-volume issue review."""

    def __init__(
        self,
        *,
        scanned: int,
        grouped: dict[str, list[RecordCheckIssue]],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("CheckResultDialog")
        self.setWindowTitle("Check Result")
        self.resize(900, 620)

        total = sum(len(items) for items in grouped.values())
        summary = QLabel(
            (
                f"Scanned: {scanned} | Total issues: {total}\n"
                f"License: {len(grouped.get('license', []))} | "
                f"SSH: {len(grouped.get('ssh', []))} | "
                f"Start Command: {len(grouped.get('start', []))} | "
                f"Other: {len(grouped.get('other', []))}"
            )
        )
        summary.setWordWrap(True)

        root = QVBoxLayout()
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(8)
        root.addWidget(summary)

        root.addWidget(self._build_section("License", grouped.get("license", [])))
        root.addWidget(self._build_section("SSH", grouped.get("ssh", [])))
        root.addWidget(self._build_section("Start Command", grouped.get("start", [])))
        root.addWidget(self._build_section("Other", grouped.get("other", [])))

        close_btn = QPushButton("Close")
        close_btn.setObjectName("DialogCloseButton")
        close_btn.clicked.connect(self.accept)

        footer = QHBoxLayout()
        footer.addStretch(1)
        footer.addWidget(close_btn)
        root.addLayout(footer)
        self.setLayout(root)

    def _build_section(self, title: str, items: list[RecordCheckIssue]) -> QGroupBox:
        box = QGroupBox(f"{title} ({len(items)})")
        layout = QVBoxLayout()

        toggle = QPushButton("Show details")
        detail = QTextEdit()
        detail.setReadOnly(True)
        detail.setVisible(False)

        if items:
            lines = [
                f"{index}. record_id={item.record_id} | reason={item.reason}"
                for index, item in enumerate(items, start=1)
            ]
            detail.setText("\n".join(lines))
        else:
            detail.setText("No issues.")

        def _toggle() -> None:
            visible = not detail.isVisible()
            detail.setVisible(visible)
            toggle.setText("Hide details" if visible else "Show details")

        toggle.clicked.connect(_toggle)

        layout.addWidget(toggle)
        layout.addWidget(detail)
        box.setLayout(layout)
        return box
