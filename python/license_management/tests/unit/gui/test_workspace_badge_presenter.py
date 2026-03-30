from __future__ import annotations

from license_management.gui.presenters.workspace_badge_presenter import WorkspaceBadgePresenter


def test_present_staging_workspace() -> None:
    presenter = WorkspaceBadgePresenter()

    result = presenter.present("staging")

    assert result.text == "STAGING (not committed)"
    assert "#f57c00" in result.style_sheet


def test_present_committed_workspace() -> None:
    presenter = WorkspaceBadgePresenter()

    result = presenter.present("committed")

    assert result.text == "COMMITTED (production)"
    assert "#2e7d32" in result.style_sheet

