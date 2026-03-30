from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class WorkspaceActionPolicy:
    action_enabled: dict[str, bool]
    action_tooltips: dict[str, str]
    table_editable: bool


def build_workspace_action_policy(workspace: str) -> WorkspaceActionPolicy:
    action_keys = {
        "add",
        "import",
        "check",
        "reset_data",
        "delete",
        "export",
        "compare",
        "edit",
        "start",
        "stop",
    }

    enabled = {key: True for key in action_keys}
    tooltips = {key: "" for key in action_keys}
    tooltips["reset_data"] = "Switch between staging and committed workspaces"

    if workspace == "staging":
        allowed = {"add", "import", "check", "reset_data"}
        for key in action_keys:
            enabled[key] = key in allowed
        tooltips["export"] = "Run Check and publish to committed before export/compare"
        tooltips["compare"] = "Run Check and publish to committed before export/compare"
        tooltips["edit"] = "Run Check and publish to committed before remote edit/start/stop"
        tooltips["start"] = "Run Check and publish to committed before remote edit/start/stop"
        tooltips["stop"] = "Run Check and publish to committed before remote edit/start/stop"
        tooltips["delete"] = "Staging only allows Add/Import/Check; delete in committed"
        return WorkspaceActionPolicy(
            action_enabled=enabled,
            action_tooltips=tooltips,
            table_editable=True,
        )

    enabled["add"] = False
    enabled["import"] = False
    tooltips["add"] = "Committed workspace does not allow Add/Import; switch to staging"
    tooltips["import"] = "Committed workspace does not allow Add/Import; switch to staging"
    return WorkspaceActionPolicy(
        action_enabled=enabled,
        action_tooltips=tooltips,
        table_editable=False,
    )
