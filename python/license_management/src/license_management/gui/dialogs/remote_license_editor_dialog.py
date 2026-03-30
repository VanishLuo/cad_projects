from __future__ import annotations

from typing import Any

from license_management.gui.qt_compat import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QTextEdit,
    Qt,
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
        server_hostname: str = "",
        server_mac: str = "",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("RemoteLicenseEditorDialog")
        self.setWindowTitle("Edit License File")
        self.resize(980, 700)

        resolved_hostname = server_hostname.strip() or "(unknown)"
        resolved_mac = server_mac.strip() or "(unknown)"
        display_mac = resolved_mac.replace(":", "") if resolved_mac != "(unknown)" else resolved_mac
        header = QLabel((f"Host: {host}\n" f"Path: {remote_path}"))
        header.setWordWrap(True)

        hostname_label = QLabel(f"Server Hostname: {resolved_hostname}")
        hostname_label.setTextInteractionFlags(
            _qt_enum_member(Qt, "TextInteractionFlag", "TextSelectableByMouse")
            | _qt_enum_member(Qt, "TextInteractionFlag", "TextSelectableByKeyboard")
        )

        # Keep the label colon while normalizing MAC value by removing ':' characters.
        mac_label = QLabel(f"Server MAC: {display_mac}")
        mac_label.setTextInteractionFlags(
            _qt_enum_member(Qt, "TextInteractionFlag", "TextSelectableByMouse")
            | _qt_enum_member(Qt, "TextInteractionFlag", "TextSelectableByKeyboard")
        )

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
        layout.addWidget(hostname_label)
        layout.addWidget(mac_label)
        layout.addWidget(editor, 1)
        layout.addWidget(buttons)
        self.setLayout(layout)

    def text_content(self) -> str:
        return self._editor.toPlainText()


def _qt_enum_member(owner: object, enum_name: str, member_name: str) -> Any:
    enum_owner = getattr(owner, enum_name, owner)
    return getattr(enum_owner, member_name)
