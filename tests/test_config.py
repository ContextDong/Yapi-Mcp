import json
from pathlib import Path

from yapi_mcp.config import load_settings, reset_runtime_settings, update_runtime_settings


def test_runtime_overrides_env(monkeypatch, tmp_path: Path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("YAPI_BASE_URL", "https://env.example.com")
    monkeypatch.setenv("YAPI_TOKEN", "env-token")
    reset_runtime_settings()
    update_runtime_settings(base_url="https://runtime.example.com", token="runtime-token")
    settings = load_settings()
    assert settings.base_url == "https://runtime.example.com"
    assert settings.token == "runtime-token"
    reset_runtime_settings()


def test_config_file(monkeypatch, tmp_path: Path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("YAPI_BASE_URL", raising=False)
    monkeypatch.delenv("YAPI_TOKEN", raising=False)
    monkeypatch.delenv("YAPI_UID", raising=False)
    reset_runtime_settings()
    cfg = {
        "base_url": "https://file.example.com",
        "token": "file-token",
        "uid": 7,
    }
    (tmp_path / ".yapi-mcp.json").write_text(json.dumps(cfg), encoding="utf-8")
    settings = load_settings()
    assert settings.base_url == "https://file.example.com"
    assert settings.token == "file-token"
    assert settings.uid == 7
    reset_runtime_settings()
