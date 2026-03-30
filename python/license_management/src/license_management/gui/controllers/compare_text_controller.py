from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Protocol

from license_management.domain.models.license_record import LicenseRecord


class CompareTextRepositoryProtocol(Protocol):
    def get_license_text_snapshot(self, record_id: str) -> tuple[str, str] | None: ...

    def upsert_license_text_snapshot(
        self,
        record_id: str,
        *,
        initial_text: str | None = None,
        current_text: str | None = None,
    ) -> None: ...


@dataclass(slots=True, frozen=True)
class CompareTextPayload:
    left_title: str
    right_title: str
    left_text: str
    right_text: str


class CompareTextController:
    """Build compare payload for one/two selected records with a single code path."""

    def __init__(
        self,
        *,
        repository: CompareTextRepositoryProtocol,
        load_remote_text: Callable[[LicenseRecord], str | None],
    ) -> None:
        self._repository = repository
        self._load_remote_text = load_remote_text

    def build_payload(
        self,
        *,
        workspace: str,
        selected_records: list[LicenseRecord],
    ) -> tuple[CompareTextPayload | None, str | None]:
        if len(selected_records) == 1:
            return self._build_single_payload(selected_records[0])
        if len(selected_records) == 2:
            return self._build_double_payload(
                workspace=workspace, selected_records=selected_records
            )
        return None, "Please select one or two rows first."

    def _build_single_payload(
        self,
        record: LicenseRecord,
    ) -> tuple[CompareTextPayload | None, str | None]:
        snapshot = self._repository.get_license_text_snapshot(record.record_id)
        initial_text = ""
        current_text = ""
        if snapshot is not None:
            initial_text, current_text = snapshot

        if current_text.strip() == "":
            remote_loaded = self._load_remote_text(record)
            if remote_loaded is None:
                return None, "Unable to load current license text for compare."
            current_text = remote_loaded

        if initial_text.strip() == "":
            initial_text = current_text
            self._repository.upsert_license_text_snapshot(
                record.record_id,
                initial_text=initial_text,
                current_text=current_text,
            )

        if current_text.strip() != "":
            self._repository.upsert_license_text_snapshot(
                record.record_id,
                current_text=current_text,
            )

        if initial_text.strip() == "" and current_text.strip() == "":
            return None, None

        return (
            CompareTextPayload(
                left_title=f"Initial | record_id={record.record_id}",
                right_title=f"Current | record_id={record.record_id}",
                left_text=initial_text,
                right_text=current_text,
            ),
            None,
        )

    def _build_double_payload(
        self,
        *,
        workspace: str,
        selected_records: list[LicenseRecord],
    ) -> tuple[CompareTextPayload | None, str | None]:
        left_record = selected_records[0]
        right_record = selected_records[1]

        left_text = self._resolve_current_text_for_record(left_record)
        if left_text is None:
            return (
                None,
                f"Unable to load current license text for record_id={left_record.record_id}.",
            )

        right_text = self._resolve_current_text_for_record(right_record)
        if right_text is None:
            return (
                None,
                f"Unable to load current license text for record_id={right_record.record_id}.",
            )

        return (
            CompareTextPayload(
                left_title=f"{workspace.title()} | record_id={left_record.record_id}",
                right_title=f"{workspace.title()} | record_id={right_record.record_id}",
                left_text=left_text,
                right_text=right_text,
            ),
            None,
        )

    def _resolve_current_text_for_record(self, record: LicenseRecord) -> str | None:
        remote_loaded = self._load_remote_text(record)
        if remote_loaded is not None and remote_loaded.strip() != "":
            self._repository.upsert_license_text_snapshot(
                record.record_id,
                current_text=remote_loaded,
            )
            return remote_loaded

        snapshot = self._repository.get_license_text_snapshot(record.record_id)
        if snapshot is None:
            return None
        _initial_text, current_text = snapshot
        if current_text.strip() == "":
            return None
        return current_text
