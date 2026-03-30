from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class WorkspaceBadgeViewState:
    text: str
    style_sheet: str


class WorkspaceBadgePresenter:
    def present(self, workspace: str) -> WorkspaceBadgeViewState:
        if workspace == "staging":
            return WorkspaceBadgeViewState(
                text="STAGING (not committed)",
                style_sheet=(
                    "QLabel { background:#f57c00; color:#ffffff; font-weight:700; "
                    "padding:4px 10px; border-radius:10px; }"
                ),
            )

        return WorkspaceBadgeViewState(
            text="COMMITTED (production)",
            style_sheet=(
                "QLabel { background:#2e7d32; color:#ffffff; font-weight:700; "
                "padding:4px 10px; border-radius:10px; }"
            ),
        )
