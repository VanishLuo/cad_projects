from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import date

from license_management.domain.models.license_record import LicenseRecord


@dataclass(slots=True, frozen=True)
class TableEditDecision:
    action: str
    updated_record: LicenseRecord | None = None
    user_feedback: str = ""
    log_message: str = ""
    log_level: str = "info"


class TableEditController:
    """Evaluate and transform table edit operations without UI dependencies."""

    def apply(
        self,
        *,
        record: LicenseRecord,
        column_name: str,
        value: str,
    ) -> TableEditDecision:
        current_value = str(getattr(record, column_name, ""))
        if value == current_value:
            return TableEditDecision(action="unchanged")

        if column_name in {"server_name", "provider", "prot"} and value == "":
            return TableEditDecision(
                action="invalid",
                user_feedback="Table edit reverted due to invalid value.",
                log_message=(
                    f"table_edit_blocked: field={column_name} cannot be empty "
                    f"for record_id={record.record_id}"
                ),
                log_level="error",
            )

        if column_name == "expires_on":
            try:
                parsed_date = date.fromisoformat(value)
            except ValueError:
                return TableEditDecision(
                    action="invalid",
                    user_feedback="Table edit reverted due to invalid date format.",
                    log_message=(
                        "table_edit_blocked: field=expires_on must be ISO date "
                        f"(YYYY-MM-DD) for record_id={record.record_id}"
                    ),
                    log_level="error",
                )
            return TableEditDecision(
                action="updated",
                updated_record=replace(record, expires_on=parsed_date),
            )

        if column_name == "server_name":
            updated = replace(record, server_name=value)
        elif column_name == "provider":
            updated = replace(record, provider=value)
        elif column_name == "prot":
            updated = replace(record, prot=value)
        elif column_name == "feature_name":
            updated = replace(record, feature_name=value)
        elif column_name == "process_name":
            updated = replace(record, process_name=value)
        elif column_name == "vendor":
            updated = replace(record, vendor=value)
        elif column_name == "start_executable_path":
            updated = replace(record, start_executable_path=value)
        elif column_name == "license_file_path":
            updated = replace(record, license_file_path=value)
        elif column_name == "start_option_override":
            updated = replace(record, start_option_override=value)
        else:
            return TableEditDecision(action="unchanged")

        return TableEditDecision(action="updated", updated_record=updated)
