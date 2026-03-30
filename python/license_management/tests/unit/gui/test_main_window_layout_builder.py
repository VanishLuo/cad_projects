# mypy: ignore-errors
# pyright: reportUnknownParameterType=false, reportMissingParameterType=false, reportUnknownVariableType=false, reportUnknownMemberType=false, reportUnknownArgumentType=false, reportArgumentType=false
from __future__ import annotations

import license_management.gui.composition.main_window_layout_builder as mod


class _Signal:
    def __init__(self) -> None:
        self._callback = None

    def connect(self, callback):
        self._callback = callback

    def emit(self) -> None:
        if self._callback is not None:
            self._callback()


class _Widget:
    def __init__(self, *args, **kwargs) -> None:
        _ = (args, kwargs)
        self.object_name = ""
        self.layout = None

    def setObjectName(self, name: str) -> None:
        self.object_name = name

    def setLayout(self, layout) -> None:
        self.layout = layout


class _Window(_Widget):
    def __init__(self) -> None:
        super().__init__()
        self.central_widget = None

    def setCentralWidget(self, widget) -> None:
        self.central_widget = widget


class _Layout:
    def __init__(self) -> None:
        self.items = []

    def addWidget(self, widget, *args) -> None:
        self.items.append(("widget", widget, args))

    def addLayout(self, layout) -> None:
        self.items.append(("layout", layout))

    def addStretch(self, value: int) -> None:
        self.items.append(("stretch", value))

    def setContentsMargins(self, *args) -> None:
        self.items.append(("margins", args))


class _Button(_Widget):
    def __init__(self, text: str) -> None:
        super().__init__()
        self.text = text
        self.clicked = _Signal()

    def click(self) -> None:
        self.clicked.emit()


class _Splitter(_Widget):
    def __init__(self, _orientation) -> None:
        super().__init__()

    def setChildrenCollapsible(self, _value: bool) -> None:
        return

    def addWidget(self, _widget) -> None:
        return

    def setStretchFactor(self, _index: int, _factor: int) -> None:
        return


class _Qt:
    class Orientation:
        Vertical = 1


def test_build_layout_returns_action_buttons_and_binds_callbacks(monkeypatch) -> None:
    monkeypatch.setattr(mod, "QWidget", _Widget)
    monkeypatch.setattr(mod, "QGroupBox", _Widget)
    monkeypatch.setattr(mod, "QLabel", _Widget)
    monkeypatch.setattr(mod, "QPushButton", _Button)
    monkeypatch.setattr(mod, "QGridLayout", _Layout)
    monkeypatch.setattr(mod, "QHBoxLayout", _Layout)
    monkeypatch.setattr(mod, "QVBoxLayout", _Layout)
    monkeypatch.setattr(mod, "QSplitter", _Splitter)
    monkeypatch.setattr(mod, "Qt", _Qt)

    window = _Window()
    called: dict[str, int] = {}

    def mark(name: str) -> None:
        called[name] = called.get(name, 0) + 1

    result = mod.MainWindowLayoutBuilder().build(
        window=window,
        keyword=_Widget(),
        vendor=_Widget(),
        server=_Widget(),
        status=_Widget(),
        table=_Widget(),
        hint=_Widget(),
        log=_Widget(),
        workspace_badge=_Widget(),
        on_search=lambda: mark("search"),
        on_reset=lambda: mark("reset"),
        on_add=lambda: mark("add"),
        on_import=lambda: mark("import"),
        on_check=lambda: mark("check"),
        on_switch_workspace=lambda: mark("switch_workspace"),
        on_delete=lambda: mark("delete"),
        on_export=lambda: mark("export"),
        on_compare=lambda: mark("compare"),
        on_edit=lambda: mark("edit"),
        on_start=lambda: mark("start"),
        on_stop=lambda: mark("stop"),
    )

    assert window.central_widget is not None
    assert len(result.action_buttons) == 10
    assert "compare" in result.action_button_map

    result.btn_add.click()
    result.btn_export.click()
    result.btn_stop.click()

    assert called["add"] == 1
    assert called["export"] == 1
    assert called["stop"] == 1
