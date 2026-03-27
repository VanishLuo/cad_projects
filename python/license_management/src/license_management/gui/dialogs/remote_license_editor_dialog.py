from __future__ import annotations

from license_management.gui.qt_compat import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


class RemoteLicenseEditorDialog(QDialog):
    """Subwindow for editing remote license file text content."""

    def __init__(
        self,
        *,
        host: str,
        remote_path: str,
        content: str,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("RemoteLicenseEditorDialog")
        self.setWindowTitle("Edit License File")
        self.resize(980, 700)

        header = QLabel(f"Host: {host}\nPath: {remote_path}")
        header.setWordWrap(True)

        editor = QTextEdit()
        editor.setAcceptRichText(False)
        editor.setLineWrapMode(QTextEdit.NoWrap)
        editor.setPlainText(content)
        self._editor = editor

        save_button = QDialogButtonBox.Save
        cancel_button = QDialogButtonBox.Cancel
        buttons = QDialogButtonBox(save_button | cancel_button)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout()
        layout.addWidget(header)
        layout.addWidget(editor, 1)
        layout.addWidget(buttons)
        self.setLayout(layout)

    def text_content(self) -> str:
        return self._editor.toPlainText()
