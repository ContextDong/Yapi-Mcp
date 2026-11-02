"""YApi MCP server entrypoint for Cursor / other MCP hosts."""

from __future__ import annotations

import json
from typing import Any

from mcp.server import MCPServer

from .client import YapiError, open_client
from .config import (
    clear_runtime_secrets,
    get_runtime_settings,
    load_settings,
    update_runtime_settings,
)
from .normalize import (
    build_project_catalog,
    flatten_menu,
    normalize_interface,
    search_index,
)
from .url_parser import parse_yapi_url

mcp = MCPServer(
    "yapi",
    instructions=(
        "Fetch YApi project API docs (JSON request/response) from a project URL "
        "so the agent can implement client integrations. Configure credentials via "
        "env (YAPI_BASE_URL / YAPI_TOKEN), config file (.yapi-mcp.json), "
        "yapi_configure, or per-tool token/base_url. Prefer: configure → parse URL → "
        "list/search interfaces → get interface detail → generate client code."
    ),
)


def _dumps(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2)


@mcp.tool()
def yapi_configure(
    base_url: str | None = None,
    token: str | None = None,
    uid: int | None = None,
    cookie: str | None = None,
    timeout: float | None = None,
    clear_secrets: bool = False,
) -> str:
    """Set runtime connection settings for this MCP session (overrides env/file).

    Prefer env vars or `.yapi-mcp.json` for durable config. Use this when the user
    pastes host/token in chat. Never echo the raw token back.
    """
    if clear_secrets:
        clear_runtime_secrets()
    kwargs: dict[str, Any] = {}
    if base_url is not None:
        kwargs["base_url"] = base_url
    if token is not None:
        kwargs["token"] = token
    if uid is not None:
        kwargs["uid"] = uid
    if cookie is not None:
        kwargs["cookie"] = cookie
    if timeout is not None:
        kwargs["timeout"] = timeout
    if kwargs:
        update_runtime_settings(**kwargs)
    effective = load_settings()
    return _dumps(
        {
            "runtime": get_runtime_settings().public_dict(),
            "effective": effective.public_dict(),
            "hint": "Secrets are stored in-memory for this MCP process only.",
        }
    )


@mcp.tool()
def yapi_get_config() -> str:
    """Show non-secret connection settings currently in effect."""
    return _dumps(
        {
            "runtime": get_runtime_settings().public_dict(),
            "effective": load_settings().public_dict(),
            "sources": [
                "tool args",
                "yapi_configure runtime",
                "env / .env (YAPI_BASE_URL, YAPI_TOKEN, YAPI_UID, YAPI_COOKIE)",
                "config file (.yapi-mcp.json or YAPI_MCP_CONFIG)",
            ],
        }
    )


@mcp.tool()
def yapi_parse_url(url: str) -> str:
    """Parse a YApi page URL into base_url, project_id, and optional interface_id.

    Example: https://yapi.example.com/project/123/interface/api/
    """
    parts = parse_yapi_url(url)
    return _dumps(
        {
            "base_url": parts.base_url,
            "project_id": parts.project_id,
            "interface_id": parts.interface_id,
            "raw_path": parts.raw_path,
        }
    )


@mcp.tool()
def yapi_get_project(
    url: str | None = None,
    project_id: int | None = None,
    base_url: str | None = None,
    token: str | None = None,
) -> str:
    """Get YApi project metadata (name, basepath, desc)."""
    try:
        with open_client(url=url, base_url=base_url, token=token) as (client, parts):
            pid = project_id or (parts.project_id if parts else None)
            data = client.get_project(pid)
            return _dumps({"base_url": client.base_url, "project": data})
    except YapiError as exc:
        return _dumps({"error": str(exc), "errcode": exc.errcode})


@mcp.tool()
def yapi_list_interfaces(
    url: str | None = None,
    project_id: int | None = None,
    base_url: str | None = None,
    token: str | None = None,
    keyword: str | None = None,
    path: str | None = None,
    method: str | None = None,
) -> str:
    """List interfaces under a YApi project (from list_menu), with optional filters.

    Pass a browser URL like https://yapi.example.com/project/123/interface/api/
    or set project_id + base_url. Credentials via env / config / token arg.
    """
    try:
        with open_client(url=url, base_url=base_url, token=token) as (client, parts):
            pid = project_id or (parts.project_id if parts else None)
            if pid is None:
                raise YapiError("缺少 project_id：请在 url 中包含 /project/{id} 或显式传入")
            menu = client.list_menu(pid)
            rows = flatten_menu(menu)
            matched = search_index(rows, keyword=keyword, path=path, method=method)
            return _dumps(
                {
                    "base_url": client.base_url,
                    "project_id": pid,
                    "total": len(rows),
                    "matched": len(matched),
                    "interfaces": matched,
                }
            )
    except YapiError as exc:
        return _dumps({"error": str(exc), "errcode": exc.errcode})


@mcp.tool()
def yapi_get_interface(
    interface_id: int | None = None,
    url: str | None = None,
    base_url: str | None = None,
    token: str | None = None,
) -> str:
    """Get one interface's full JSON request/response definition for client codegen.

    Prefer interface_id from yapi_list_interfaces, or a detail URL:
    https://yapi.example.com/project/123/interface/api/456
    """
    try:
        with open_client(url=url, base_url=base_url, token=token) as (client, parts):
            iid = interface_id or (parts.interface_id if parts else None)
            if iid is None:
                raise YapiError("缺少 interface_id")
            raw = client.get_interface(iid)
            return _dumps(
                {
                    "base_url": client.base_url,
                    "interface": normalize_interface(raw),
                }
            )
    except YapiError as exc:
        return _dumps({"error": str(exc), "errcode": exc.errcode})


@mcp.tool()
def yapi_export_catalog(
    url: str | None = None,
    project_id: int | None = None,
    base_url: str | None = None,
    token: str | None = None,
    include_details: bool = False,
    limit: int = 50,
) -> str:
    """Export a project API catalog for agent understanding / client scaffolding.

    By default returns an index (method/path/title). Set include_details=true to
    also pull normalized request/response bodies (capped by limit).
    """
    try:
        with open_client(url=url, base_url=base_url, token=token) as (client, parts):
            pid = project_id or (parts.project_id if parts else None)
            if pid is None:
                raise YapiError("缺少 project_id")
            project = client.get_project(pid)
            rows = flatten_menu(client.list_menu(pid))
            catalog = build_project_catalog(
                project=project, menu_rows=rows, base_url=client.base_url
            )
            if include_details:
                details = []
                for row in rows[: max(0, limit)]:
                    iid = row.get("id")
                    if iid is None:
                        continue
                    raw = client.get_interface(int(iid))
                    details.append(normalize_interface(raw))
                catalog["details"] = details
                catalog["details_count"] = len(details)
            return _dumps(catalog)
    except YapiError as exc:
        return _dumps({"error": str(exc), "errcode": exc.errcode})


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
