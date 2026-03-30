from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Protocol

from license_management.gui.feature_search import FeatureSearchResult
from license_management.gui.state.models import UiLicenseRow


class SearchControllerProtocol(Protocol):
    def search(
        self,
        *,
        today: date,
        keyword: str = "",
        vendor: str = "",
        server_name: str = "",
        status: str = "",
    ) -> FeatureSearchResult: ...

    def reset(self, *, today: date) -> FeatureSearchResult: ...


@dataclass(slots=True, frozen=True)
class SearchPresentation:
    rows: tuple[UiLicenseRow, ...]
    empty_hint: str
    log_fields: dict[str, object]


@dataclass(slots=True, frozen=True)
class ResetPresentation:
    rows: tuple[UiLicenseRow, ...]
    empty_hint: str
    feedback: str
    log_fields: dict[str, object]


class SearchFilterPresenter:
    """Coordinate search/reset and produce UI/log payloads for the view."""

    def __init__(self, search_controller: SearchControllerProtocol) -> None:
        self._search = search_controller

    def apply_search(
        self,
        *,
        trigger: str,
        today: date,
        keyword: str,
        vendor: str,
        server_name: str,
        status: str,
    ) -> SearchPresentation:
        result = self._search.search(
            today=today,
            keyword=keyword,
            vendor=vendor,
            server_name=server_name,
            status=status,
        )
        return SearchPresentation(
            rows=result.rows,
            empty_hint=result.empty_hint,
            log_fields={
                "trigger": trigger,
                "keyword": keyword,
                "vendor": vendor,
                "server_name": server_name,
                "status": status,
                "result_count": len(result.rows),
            },
        )

    def reset_filters(self, *, today: date, before: dict[str, str]) -> ResetPresentation:
        result = self._search.reset(today=today)
        return ResetPresentation(
            rows=result.rows,
            empty_hint=result.empty_hint,
            feedback="Filters reset.",
            log_fields={
                "before": before,
                "result_count": len(result.rows),
            },
        )
