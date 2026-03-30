from __future__ import annotations

from license_management.gui.controllers.workspace_controller import WorkspaceController


class _FakeRepository:
    def __init__(self) -> None:
        self.current_workspace = "committed"
        self._rows = {
            "committed": ["r1", "r2"],
            "staging": ["s1"],
        }

    def switch_workspace(self, workspace: str) -> None:
        self.current_workspace = workspace

    def enter_staging_workspace(self) -> None:
        self.current_workspace = "staging"

    def list_all(self) -> list[object]:
        return list(self._rows[self.current_workspace])


class _FakeFeatureCatalog:
    def __init__(self) -> None:
        self.workspace_calls: list[str] = []
        self.enter_calls = 0

    def switch_workspace(self, workspace: str) -> None:
        self.workspace_calls.append(workspace)

    def enter_staging_workspace(self) -> None:
        self.enter_calls += 1


def test_toggle_workspace_switches_and_returns_row_count() -> None:
    repo = _FakeRepository()
    catalog = _FakeFeatureCatalog()
    controller = WorkspaceController(repository=repo, feature_catalog=catalog)

    result = controller.toggle_workspace()

    assert result.target_workspace == "staging"
    assert result.row_count == 1
    assert repo.current_workspace == "staging"
    assert catalog.workspace_calls == ["staging"]


def test_enter_staging_workspace_returns_change_flag() -> None:
    repo = _FakeRepository()
    catalog = _FakeFeatureCatalog()
    controller = WorkspaceController(repository=repo, feature_catalog=catalog)

    changed = controller.enter_staging_workspace()
    changed_again = controller.enter_staging_workspace()

    assert changed is True
    assert changed_again is False
    assert repo.current_workspace == "staging"
    assert catalog.enter_calls == 2

