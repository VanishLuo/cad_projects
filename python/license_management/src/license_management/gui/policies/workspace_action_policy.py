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
        "switch_workspace",
        "delete",
        "export",
        "compare",
        "edit",
        "start",
        "stop",
    }

    enabled = {key: True for key in action_keys}
    tooltips = {key: "" for key in action_keys}
    tooltips["switch_workspace"] = "Switch between staging and committed workspaces"

    if workspace == "staging":
        allowed = {"add", "import", "check", "switch_workspace", "delete"}
        for key in action_keys:
            enabled[key] = key in allowed
        tooltips["export"] = "Run Check and publish to committed before export/compare"
        tooltips["compare"] = "Compare is only available in committed workspace"
        tooltips["edit"] = "Run Check and publish to committed before remote edit/start/stop"
        tooltips["start"] = "Run Check and publish to committed before remote edit/start/stop"
        tooltips["stop"] = "Run Check and publish to committed before remote edit/start/stop"
        tooltips["delete"] = "Delete selected staging rows"
        return WorkspaceActionPolicy(
            action_enabled=enabled,
            action_tooltips=tooltips,
            table_editable=True,
        )

    enabled["add"] = False
    enabled["import"] = False
    tooltips["add"] = "Committed workspace does not allow Add/Import; switch to staging"
    tooltips["import"] = "Committed workspace does not allow Add/Import; switch to staging"
    tooltips["compare"] = (
        "Select one row for initial-vs-current text compare, or two rows for current-text compare"
    )
    tooltips["delete"] = "Delete selected committed rows"
    return WorkspaceActionPolicy(
        action_enabled=enabled,
        action_tooltips=tooltips,
        table_editable=False,
    )
