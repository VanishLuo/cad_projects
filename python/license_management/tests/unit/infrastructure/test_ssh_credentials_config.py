from __future__ import annotations

from pathlib import Path

from license_management.infrastructure.config.ssh_credentials_config import load_ssh_credentials


def test_load_ssh_credentials_from_file(tmp_path: Path, monkeypatch) -> None:
    cfg = tmp_path / "config" / "ssh_credentials.json"
    cfg.parent.mkdir(parents=True, exist_ok=True)
    cfg.write_text('{"username":"alice","password":"secret"}', encoding="utf-8")

    monkeypatch.delenv("LM_SSH_USERNAME", raising=False)
    monkeypatch.delenv("LM_SSH_PASSWORD", raising=False)
    monkeypatch.delenv("LM_SSH_CREDENTIALS_FILE", raising=False)

    creds = load_ssh_credentials(tmp_path)
    assert creds.username == "alice"
    assert creds.password == "secret"


def test_load_ssh_credentials_only_password_env_overrides_file(tmp_path: Path, monkeypatch) -> None:
    cfg = tmp_path / "config" / "ssh_credentials.json"
    cfg.parent.mkdir(parents=True, exist_ok=True)
    cfg.write_text('{"username":"file_user","password":"file_pwd"}', encoding="utf-8")

    monkeypatch.setenv("LM_SSH_USERNAME", "env_user")
    monkeypatch.setenv("LM_SSH_PASSWORD", "env_pwd")

    creds = load_ssh_credentials(tmp_path)
    assert creds.username == "file_user"
    assert creds.password == "env_pwd"
