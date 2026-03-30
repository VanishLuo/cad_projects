from __future__ import annotations

from datetime import date
from typing import cast

from license_management.gui.feature_search import FeatureSearchResult
from license_management.gui.state.models import UiLicenseRow
from license_management.gui.presenters.search_filter_presenter import SearchFilterPresenter
from license_management.gui.state.view_model import SearchFilters


class _Search:
    def __init__(self) -> None:
        self.search_called = False
        self.reset_called = False

    def search(
        self,
        *,
        today: date,
        keyword: str = "",
        vendor: str = "",
        server_name: str = "",
        status: str = "",
    ) -> FeatureSearchResult:
        _ = (today, keyword, vendor, server_name, status)
        self.search_called = True
        return FeatureSearchResult(
            rows=cast(tuple[UiLicenseRow, ...], ()),
            empty_hint="none",
            active_filters=SearchFilters(),
        )

    def reset(self, *, today: date) -> FeatureSearchResult:
        _ = today
        self.reset_called = True
        return FeatureSearchResult(
            rows=cast(tuple[UiLicenseRow, ...], ()),
            empty_hint="none",
            active_filters=SearchFilters(),
        )


def test_apply_search_returns_log_fields_and_rows() -> None:
    presenter = SearchFilterPresenter(_Search())
    result = presenter.apply_search(
        trigger="manual",
        today=date(2026, 3, 30),
        keyword="k",
        vendor="v",
        server_name="s",
        status="active",
    )

    assert result.empty_hint == "none"
    assert result.log_fields["trigger"] == "manual"
    assert result.log_fields["status"] == "active"


def test_reset_filters_returns_feedback_and_before_payload() -> None:
    presenter = SearchFilterPresenter(_Search())
    result = presenter.reset_filters(
        today=date(2026, 3, 30),
        before={"keyword": "k", "vendor": "v", "server": "s", "status": "active"},
    )

    assert result.feedback == "Filters reset."
    assert "before" in result.log_fields

