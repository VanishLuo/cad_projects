from __future__ import annotations

from license_management.gui.presenters.action_state_presenter import ActionStatePresenter


def test_build_disabled_state_turns_off_all_buttons() -> None:
    presenter = ActionStatePresenter()
    result = presenter.build(enabled=False, workspace="staging", action_keys={"add", "check"})

    assert result.controls_enabled is False
    assert result.button_enabled == {"add": False, "check": False}


def test_build_enabled_state_uses_workspace_policy() -> None:
    presenter = ActionStatePresenter()
    result = presenter.build(enabled=True, workspace="committed", action_keys={"add", "import"})

    assert result.controls_enabled is True
    assert result.button_enabled["add"] is False
    assert result.button_enabled["import"] is False

