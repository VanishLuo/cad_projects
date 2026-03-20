from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from license_management.gui.models import UiLicenseRow
from license_management.gui.view_model import MainListViewModel, SearchFilters


@dataclass(slots=True, frozen=True)
class FeatureSearchResult:
    rows: tuple[UiLicenseRow, ...]
    empty_hint: str
    active_filters: SearchFilters


class FeatureSearchController:
    """M06 T6.4 feature-level search with combined filter orchestration."""

    def __init__(self, view_model: MainListViewModel) -> None:
        self._view_model = view_model

    def search(
        self,
        *,
        today: date,
        feature_name: str = "",
        feature_code: str = "",
        keyword: str = "",
        provider: str = "",
        server_name: str = "",
        status: str = "",
        expires_before: date | None = None,
        text_query: str = "",
    ) -> FeatureSearchResult:
        filters = SearchFilters(
            text_query=text_query,
            feature_name=feature_name,
            feature_code=feature_code,
            keyword=keyword,
            provider=provider,
            server_name=server_name,
            status=status,
            expires_before=expires_before,
        )
        rows = self._view_model.search_and_filter(filters=filters, today=today)
        return FeatureSearchResult(
            rows=rows,
            empty_hint=self._view_model.empty_state_hint(),
            active_filters=filters,
        )

    def reset(self, *, today: date) -> FeatureSearchResult:
        rows = self._view_model.reset_filters(today=today)
        return FeatureSearchResult(
            rows=rows,
            empty_hint=self._view_model.empty_state_hint(),
            active_filters=self._view_model.filters,
        )
