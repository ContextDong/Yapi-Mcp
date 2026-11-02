"""Normalize YApi interface payloads into agent-friendly JSON API docs."""

from __future__ import annotations

import json
from typing import Any


def _parse_jsonish(value: Any) -> Any:
    if value is None or value == "":
        return None
    if isinstance(value, (dict, list)):
        return value
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return value
    return value


def _fields(items: Any) -> list[dict[str, Any]]:
    if not isinstance(items, list):
        return []
    out: list[dict[str, Any]] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        out.append(
            {
                "name": item.get("name"),
                "type": item.get("type"),
                "required": str(item.get("required", "0")) in ("1", "true", "True"),
                "example": item.get("example"),
                "desc": item.get("desc") or item.get("description") or "",
            }
        )
    return out


def flatten_menu(menu: Any) -> list[dict[str, Any]]:
    """Flatten list_menu categories into a searchable interface index."""
    rows: list[dict[str, Any]] = []
    if not isinstance(menu, list):
        return rows
    for cat in menu:
        if not isinstance(cat, dict):
            continue
        cat_name = cat.get("name") or cat.get("desc") or ""
        cat_id = cat.get("_id")
        for api in cat.get("list") or []:
            if not isinstance(api, dict):
                continue
            rows.append(
                {
                    "id": api.get("_id"),
                    "title": api.get("title"),
                    "path": api.get("path"),
                    "method": (api.get("method") or "").upper(),
                    "status": api.get("status"),
                    "catid": api.get("catid") or cat_id,
                    "cat_name": cat_name,
                    "project_id": api.get("project_id"),
                }
            )
    return rows


def search_index(
    rows: list[dict[str, Any]],
    *,
    keyword: str | None = None,
    path: str | None = None,
    method: str | None = None,
) -> list[dict[str, Any]]:
    result = rows
    if method:
        m = method.upper()
        result = [r for r in result if (r.get("method") or "").upper() == m]
    if path:
        p = path.lower()
        result = [r for r in result if p in str(r.get("path") or "").lower()]
    if keyword:
        k = keyword.lower()
        result = [
            r
            for r in result
            if k in str(r.get("title") or "").lower()
            or k in str(r.get("path") or "").lower()
            or k in str(r.get("cat_name") or "").lower()
        ]
    return result


def normalize_interface(raw: Any) -> dict[str, Any]:
    """Convert /api/interface/get payload into a stable client-doc shape."""
    if not isinstance(raw, dict):
        return {"raw": raw}

    req_body = _parse_jsonish(raw.get("req_body_other") or raw.get("req_body"))
    res_body = _parse_jsonish(raw.get("res_body"))

    return {
        "id": raw.get("_id"),
        "project_id": raw.get("project_id"),
        "catid": raw.get("catid"),
        "title": raw.get("title"),
        "path": raw.get("path"),
        "method": (raw.get("method") or "").upper(),
        "status": raw.get("status"),
        "desc": raw.get("desc") or "",
        "markdown": raw.get("markdown") or "",
        "request": {
            "content_type_hint": raw.get("req_body_type"),
            "params": _fields(raw.get("req_params")),
            "query": _fields(raw.get("req_query")),
            "headers": _fields(raw.get("req_headers")),
            "form": _fields(raw.get("req_body_form")),
            "body_is_json_schema": bool(raw.get("req_body_is_json_schema")),
            "body": req_body,
        },
        "response": {
            "content_type_hint": raw.get("res_body_type") or "json",
            "body_is_json_schema": bool(raw.get("res_body_is_json_schema")),
            "body": res_body,
        },
    }


def build_project_catalog(
    *,
    project: Any,
    menu_rows: list[dict[str, Any]],
    base_url: str,
) -> dict[str, Any]:
    basepath = ""
    if isinstance(project, dict):
        basepath = project.get("basepath") or ""
    return {
        "base_url": base_url,
        "project": {
            "id": project.get("_id") if isinstance(project, dict) else None,
            "name": project.get("name") if isinstance(project, dict) else None,
            "desc": project.get("desc") if isinstance(project, dict) else None,
            "basepath": basepath,
        },
        "interface_count": len(menu_rows),
        "interfaces": menu_rows,
        "notes": [
            "请求与响应均为 JSON（以各接口 request/response 为准）",
            "调用 yapi_get_interface 获取单个接口完整请求/响应定义后再写客户端代码",
            "完整 URL = 业务网关 host + project.basepath + interface.path（以项目实际环境为准）",
        ],
    }
