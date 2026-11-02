"""Dynamic connection settings for YApi MCP (env / file / runtime)."""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, fields
from pathlib import Path
from typing import Any


CONFIG_ENV = "YAPI_MCP_CONFIG"
CONFIG_FILENAMES = (".yapi-mcp.json", "yapi-mcp.config.json")


@dataclass
class YapiSettings:
    """Connection settings. All fields optional until a request needs them."""

    base_url: str | None = None
    token: str | None = None
    uid: int | None = None
    cookie: str | None = None
    timeout: float = 30.0

    def merged(self, override: YapiSettings | None = None) -> YapiSettings:
        if override is None:
            return YapiSettings(**asdict(self))
        data = asdict(self)
        for key, value in asdict(override).items():
            if value is None:
                continue
            if key == "timeout" and value == 30.0 and self.timeout != 30.0:
                continue
            data[key] = value
        return YapiSettings(**data)

    def public_dict(self) -> dict[str, Any]:
        """Safe view for tools/logs (never includes token/cookie)."""
        return {
            "base_url": self.base_url,
            "uid": self.uid,
            "timeout": self.timeout,
            "has_token": bool(self.token),
            "has_cookie": bool(self.cookie),
        }


_runtime = YapiSettings()


def get_runtime_settings() -> YapiSettings:
    return YapiSettings(**asdict(_runtime))


def update_runtime_settings(**kwargs: Any) -> YapiSettings:
    global _runtime
    data = asdict(_runtime)
    for key, value in kwargs.items():
        if key not in data:
            continue
        if value is None and key != "timeout":
            continue
        if key == "uid" and value is not None:
            data[key] = int(value)
        elif key == "timeout" and value is not None:
            data[key] = float(value)
        elif key in ("base_url", "token", "cookie"):
            text = str(value).strip()
            data[key] = text or None
        else:
            data[key] = value
    _runtime = YapiSettings(**data)
    return get_runtime_settings()


def clear_runtime_secrets() -> YapiSettings:
    global _runtime
    _runtime = YapiSettings(
        base_url=_runtime.base_url,
        token=None,
        uid=None,
        cookie=None,
        timeout=_runtime.timeout,
    )
    return get_runtime_settings()


def reset_runtime_settings() -> YapiSettings:
    """Clear all runtime overrides (mainly for tests)."""
    global _runtime
    _runtime = YapiSettings()
    return get_runtime_settings()


def _load_dotenv(path: Path) -> dict[str, str]:
    if not path.is_file():
        return {}
    out: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        text = line.strip()
        if not text or text.startswith("#") or "=" not in text:
            continue
        key, _, value = text.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            out[key] = value
    return out


def _from_mapping(data: dict[str, Any]) -> YapiSettings:
    known = {f.name for f in fields(YapiSettings)}
    kwargs: dict[str, Any] = {}
    aliases = {
        "YAPI_BASE_URL": "base_url",
        "baseUrl": "base_url",
        "YAPI_TOKEN": "token",
        "YAPI_UID": "uid",
        "YAPI_COOKIE": "cookie",
        "YAPI_TIMEOUT": "timeout",
    }
    normalized: dict[str, Any] = {}
    for key, value in data.items():
        target = aliases.get(key, key)
        if target in known:
            normalized[target] = value
    for key, value in normalized.items():
        if value is None or value == "":
            continue
        if key == "uid":
            kwargs[key] = int(value)
        elif key == "timeout":
            kwargs[key] = float(value)
        else:
            kwargs[key] = str(value).strip()
    return YapiSettings(**kwargs)


def _find_config_file() -> Path | None:
    explicit = os.environ.get(CONFIG_ENV)
    if explicit:
        path = Path(explicit).expanduser()
        return path if path.is_file() else None
    cwd = Path.cwd()
    for name in CONFIG_FILENAMES:
        candidate = cwd / name
        if candidate.is_file():
            return candidate
    return None


def load_file_settings() -> YapiSettings:
    path = _find_config_file()
    if path is None:
        return YapiSettings()
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"config file must be a JSON object: {path}")
    return _from_mapping(raw)


def load_env_settings() -> YapiSettings:
    dotenv = _load_dotenv(Path.cwd() / ".env")
    merged = {
        "base_url": os.environ.get("YAPI_BASE_URL") or dotenv.get("YAPI_BASE_URL"),
        "token": os.environ.get("YAPI_TOKEN") or dotenv.get("YAPI_TOKEN"),
        "uid": os.environ.get("YAPI_UID") or dotenv.get("YAPI_UID"),
        "cookie": os.environ.get("YAPI_COOKIE") or dotenv.get("YAPI_COOKIE"),
        "timeout": os.environ.get("YAPI_TIMEOUT") or dotenv.get("YAPI_TIMEOUT") or 30.0,
    }
    return _from_mapping(merged)


def load_settings(
    *,
    base_url: str | None = None,
    token: str | None = None,
    uid: int | None = None,
    cookie: str | None = None,
) -> YapiSettings:
    """Resolve settings with precedence:

    call args > runtime overrides > env/.env > config file
    """
    file_cfg = load_file_settings()
    env_cfg = load_env_settings()
    runtime_cfg = get_runtime_settings()
    call_cfg = YapiSettings(
        base_url=base_url,
        token=token,
        uid=uid,
        cookie=cookie,
    )
    return file_cfg.merged(env_cfg).merged(runtime_cfg).merged(call_cfg)
