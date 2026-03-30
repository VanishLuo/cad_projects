from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
from collections.abc import Sequence


class WorkspaceRepositoryProtocol(Protocol):
    @property
    def current_workspace(self) -> str: ...

    def switch_workspace(self, workspace: str) -> None: ...

    def enter_staging_workspace(self) -> None: ...

    def list_all(self) -> Sequence[object]: ...


class WorkspaceFeatureCatalogProtocol(Protocol):
    def switch_workspace(self, workspace: str) -> None: ...

    def enter_staging_workspace(self) -> None: ...


@dataclass(slots=True, frozen=True)
class WorkspaceToggleResult:
    target_workspace: str
    row_count: int


class WorkspaceController:
    """Manage workspace switching behavior shared by GUI actions."""

    def __init__(
        self,
        *,
        repository: WorkspaceRepositoryProtocol,
        feature_catalog: WorkspaceFeatureCatalogProtocol,
    ) -> None:
        self._repository = repository
        self._feature_catalog = feature_catalog

    def toggle_workspace(self) -> WorkspaceToggleResult:
        current_workspace = self._repository.current_workspace
        target_workspace = "committed" if current_workspace == "staging" else "staging"
        self.switch_workspace(target_workspace)
        return WorkspaceToggleResult(
            target_workspace=target_workspace,
            row_count=len(self._repository.list_all()),
        )

    def switch_workspace(self, workspace: str) -> None:
        self._repository.switch_workspace(workspace)
        self._feature_catalog.switch_workspace(workspace)

    def enter_staging_workspace(self) -> bool:
        previous = self._repository.current_workspace
        self._repository.enter_staging_workspace()
        self._feature_catalog.enter_staging_workspace()
        return previous != self._repository.current_workspace
