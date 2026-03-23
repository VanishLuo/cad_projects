from __future__ import annotations

from PyQt5.QtCore import QDate, Qt  # type: ignore[import-not-found]
from PyQt5.QtGui import QColor  # type: ignore[import-not-found]
from PyQt5.QtWidgets import (  # type: ignore[import-not-found]
    QApplication,
    QComboBox,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

QT_BINDING = "PyQt5"


def app_exec(app: QApplication) -> int:
    return int(app.exec_())


def dialog_exec(dialog: QDialog) -> int:
    return int(dialog.exec_())


def dialog_is_accepted(result: int) -> bool:
    return result == int(getattr(QDialog, "Accepted"))


__all__ = [
    "QApplication",
    "QComboBox",
    "QColor",
    "QDate",
    "QDateEdit",
    "QDialog",
    "QDialogButtonBox",
    "QFileDialog",
    "QFormLayout",
    "QGridLayout",
    "QGroupBox",
    "QHBoxLayout",
    "QHeaderView",
    "QLabel",
    "QLineEdit",
    "QMainWindow",
    "QMessageBox",
    "QPushButton",
    "QTextEdit",
    "QTableWidget",
    "QTableWidgetItem",
    "Qt",
    "QVBoxLayout",
    "QWidget",
    "QT_BINDING",
    "app_exec",
    "dialog_exec",
    "dialog_is_accepted",
]
