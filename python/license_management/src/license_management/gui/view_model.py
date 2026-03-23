from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from license_management.domain.expiration_engine import ExpirationStateEngine, ExpirationStatus
from license_management.domain.models.license_record import LicenseRecord
from license_management.gui.models import UiLicenseRow
from license_management.infrastructure.config.table_header_config import load_table_header_config


@dataclass(slots=True, frozen=True)
class SearchFilters:
    keyword: str = ""
    vendor: str = ""
    server_name: str = ""
    status: str = ""


class MainListViewModel:
    """M06 T6.1/T6.4 main list and combined search/filter view model."""

    def __init__(self, *, warning_days: int = 30) -> None:
        self._engine = ExpirationStateEngine(warning_days=warning_days)
        self._source_records: tuple[LicenseRecord, ...] = ()
        self._visible_rows: tuple[UiLicenseRow, ...] = ()
        self._filters = SearchFilters()
        cfg = load_table_header_config()
        self._searchable_fields = tuple(cfg.sqlite_columns.keys())

    @property
    def filters(self) -> SearchFilters:
        return self._filters

    @property
    def rows(self) -> tuple[UiLicenseRow, ...]:
        return self._visible_rows

    def load(self, records: list[LicenseRecord], *, today: date) -> tuple[UiLicenseRow, ...]:
        self._source_records = tuple(records)
        return self.search_and_filter(filters=self._filters, today=today)

    def search_and_filter(
        self,
        *,
        filters: SearchFilters,
        today: date,
    ) -> tuple[UiLicenseRow, ...]:
        self._filters = filters

        rows: list[UiLicenseRow] = []
        for record in self._source_records:
            status = self._engine.evaluate(record, today=today).status
            if not self._matches(record=record, status=status, filters=filters):
                continue

            rows.append(
                UiLicenseRow(
                    record_id=record.record_id,
                    server_name=record.server_name,
                    provider=record.provider,
                    prot=record.prot,
                    vendor=record.vendor,
                    feature_name=record.feature_name,
                    process_name=record.process_name,
                    expires_on=record.expires_on,
                    start_executable_path=record.start_executable_path,
                    license_file_path=record.license_file_path,
                    status=status.value,
                    highlight_level=self._to_highlight(status),
                    matched_terms=self._matched_terms(record=record, filters=filters),
                )
            )

        rows.sort(
            key=lambda row: (
                row.status,
                row.expires_on,
                row.provider.lower(),
                row.server_name.lower(),
                row.feature_name.lower(),
                row.record_id.lower(),
            )
        )
        self._visible_rows = tuple(rows)
        return self._visible_rows

    def reset_filters(self, *, today: date) -> tuple[UiLicenseRow, ...]:
        return self.search_and_filter(filters=SearchFilters(), today=today)

    def empty_state_hint(self) -> str:
        if self._visible_rows:
            return ""
        if self._source_records:
            return "No matching records. Try resetting filters or broadening keywords."
        return "No records available. Import or add a record to get started."

    def _matches(
        self,
        *,
        record: LicenseRecord,
        status: ExpirationStatus,
        filters: SearchFilters,
    ) -> bool:
        if filters.vendor and filters.vendor.lower() not in record.vendor.lower():
            return False

        if filters.server_name and filters.server_name.lower() not in record.server_name.lower():
            return False

        if filters.status and status.value != filters.status:
            return False

        if filters.keyword and not self._contains_any(
            record,
            token=filters.keyword,
            fields=self._searchable_fields,
        ):
            return False

        return True

    def _contains_any(self, record: LicenseRecord, *, token: str, fields: tuple[str, ...]) -> bool:
        value = token.lower()
        for field in fields:
            candidate = getattr(record, field, "")
            if isinstance(candidate, str) and value in candidate.lower():
                return True
        return False

    def _matched_terms(self, *, record: LicenseRecord, filters: SearchFilters) -> tuple[str, ...]:
        terms = (filters.keyword,)
        matched: list[str] = []
        haystack = " ".join(
            [str(getattr(record, field, "")) for field in self._searchable_fields]
        ).lower()

        for term in terms:
            term_value = term.strip().lower()
            if term_value and term_value in haystack and term_value not in matched:
                matched.append(term_value)
        return tuple(matched)

    def _to_highlight(self, status: ExpirationStatus) -> str:
        if status is ExpirationStatus.EXPIRED:
            return "danger"
        if status is ExpirationStatus.EXPIRING_SOON:
            return "warning"
        return "normal"
