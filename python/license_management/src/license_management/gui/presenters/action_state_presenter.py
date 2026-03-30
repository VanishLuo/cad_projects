from __future__ import annotations

from dataclasses import dataclass

from license_management.gui.policies.workspace_action_policy import (
    WorkspaceActionPolicy,
    build_workspace_action_policy,
)


@dataclass(slots=True, frozen=True)
class ActionStatePresentation:
    controls_enabled: bool
    button_enabled: dict[str, bool]
    button_tooltips: dict[str, str]
    table_editable: bool


class ActionStatePresenter:
    """Build action-state presentation from workspace policy and global running state."""

    def build(
        self,
        *,
        enabled: bool,
        workspace: str,
        action_keys: set[str],
    ) -> ActionStatePresentation:
        if not enabled:
            return ActionStatePresentation(
                controls_enabled=False,
                button_enabled={key: False for key in action_keys},
                button_tooltips={key: "" for key in action_keys},
                table_editable=False,
            )

        policy: WorkspaceActionPolicy = build_workspace_action_policy(workspace)
        return ActionStatePresentation(
            controls_enabled=True,
            button_enabled={key: policy.action_enabled.get(key, True) for key in action_keys},
            button_tooltips={key: policy.action_tooltips.get(key, "") for key in action_keys},
            table_editable=policy.table_editable,
        )
