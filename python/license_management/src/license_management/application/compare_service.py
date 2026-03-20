from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from license_management.domain.models.license_record import LicenseRecord


@dataclass(slots=True, frozen=True)
class TargetSnapshot:
    target_name: str
    records: tuple[LicenseRecord, ...]


@dataclass(slots=True, frozen=True)
class CompareIssue:
    provider: str
    server_name: str
    feature_name: str
    process_name: str
    issue_type: str
    left_expires_on: date | None
    right_expires_on: date | None


@dataclass(slots=True, frozen=True)
class CompareReport:
    left_target_name: str
    right_target_name: str
    left_count: int
    right_count: int
    issues: tuple[CompareIssue, ...]

    @property
    def has_differences(self) -> bool:
        return len(self.issues) > 0


class CrossTargetCompareService:
    """Compares two target snapshots and returns deterministic diff report."""

    def compare(self, left: TargetSnapshot, right: TargetSnapshot) -> CompareReport:
        left_index = self._index_records(left.records)
        right_index = self._index_records(right.records)

        issues: list[CompareIssue] = []

        for key in sorted(set(left_index) | set(right_index)):
            left_record = left_index.get(key)
            right_record = right_index.get(key)
            provider, server_name, feature_name, process_name = key

            if left_record is None and right_record is not None:
                issues.append(
                    CompareIssue(
                        provider=provider,
                        server_name=server_name,
                        feature_name=feature_name,
                        process_name=process_name,
                        issue_type="missing_in_left",
                        left_expires_on=None,
                        right_expires_on=right_record.expires_on,
                    )
                )
                continue

            if right_record is None and left_record is not None:
                issues.append(
                    CompareIssue(
                        provider=provider,
                        server_name=server_name,
                        feature_name=feature_name,
                        process_name=process_name,
                        issue_type="missing_in_right",
                        left_expires_on=left_record.expires_on,
                        right_expires_on=None,
                    )
                )
                continue

            if left_record is not None and right_record is not None:
                if left_record.expires_on != right_record.expires_on:
                    issues.append(
                        CompareIssue(
                            provider=provider,
                            server_name=server_name,
                            feature_name=feature_name,
                            process_name=process_name,
                            issue_type="expiration_mismatch",
                            left_expires_on=left_record.expires_on,
                            right_expires_on=right_record.expires_on,
                        )
                    )

        return CompareReport(
            left_target_name=left.target_name,
            right_target_name=right.target_name,
            left_count=len(left.records),
            right_count=len(right.records),
            issues=tuple(issues),
        )

    def _index_records(
        self,
        records: tuple[LicenseRecord, ...],
    ) -> dict[tuple[str, str, str, str], LicenseRecord]:
        # For deterministic output, duplicates under same compare key are normalized
        # by latest expiration date first, then stable record_id ordering.
        ordered = sorted(
            records,
            key=lambda item: (
                item.provider,
                item.server_name,
                item.feature_name,
                item.process_name,
                -item.expires_on.toordinal(),
                item.record_id,
            ),
        )

        index: dict[tuple[str, str, str, str], LicenseRecord] = {}
        for record in ordered:
            key = (
                record.provider,
                record.server_name,
                record.feature_name,
                record.process_name,
            )
            if key not in index:
                index[key] = record
        return index
