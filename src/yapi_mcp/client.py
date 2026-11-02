"""Thin YApi HTTP client (project open-token or login JWT session)."""

from __future__ import annotations

import base64
import json
from typing import Any

import httpx

from .config import YapiSettings, load_settings
from .url_parser import YapiUrlParts, parse_yapi_url


class YapiError(RuntimeError):
    def __init__(self, message: str, *, errcode: int | None = None, payload: Any = None):
        super().__init__(message)
        self.errcode = errcode
        self.payload = payload


def _b64url_json(segment: str) -> dict[str, Any] | None:
    try:
        padded = segment + "=" * (-len(segment) % 4)
        raw = base64.urlsafe_b64decode(padded.encode("ascii"))
        data = json.loads(raw.decode("utf-8"))
        return data if isinstance(data, dict) else None
    except Exception:
        return None


def detect_auth_mode(token: str) -> tuple[str, int | None]:
    """Return ('session'|'open', uid_or_none).

    Login JWTs contain uid/iat/exp and must be sent as cookies
    `_yapi_token` + `_yapi_uid`. Project open tokens are passed as ?token=.
    """
    parts = token.split(".")
    if len(parts) == 3:
        payload = _b64url_json(parts[1]) or {}
        uid = payload.get("uid")
        if uid is not None:
            try:
                return "session", int(uid)
            except (TypeError, ValueError):
                return "session", None
    return "open", None


class YapiClient:
    def __init__(self, settings: YapiSettings) -> None:
        if not settings.base_url:
            raise YapiError(
                "缺少 YApi 地址：请传入 url / base_url，或配置 YAPI_BASE_URL / yapi_configure"
            )
        if not settings.token and not settings.cookie:
            raise YapiError(
                "缺少凭证：配置 YAPI_TOKEN（登录 JWT 或项目 open token），"
                "或通过 yapi_configure / 工具参数 token 传入"
            )

        self.base_url = settings.base_url.rstrip("/")
        self.token = settings.token or ""
        self.auth_mode, detected_uid = (
            detect_auth_mode(self.token) if self.token else ("open", None)
        )
        self.uid = settings.uid if settings.uid is not None else detected_uid

        headers = {"Accept": "application/json"}
        cookies: dict[str, str] = {}

        if settings.cookie:
            headers["Cookie"] = settings.cookie
        elif self.auth_mode == "session" and self.token:
            cookies["_yapi_token"] = self.token
            if self.uid is not None:
                cookies["_yapi_uid"] = str(self.uid)

        self._http = httpx.Client(
            base_url=self.base_url,
            timeout=settings.timeout,
            headers=headers,
            cookies=cookies or None,
        )

    def close(self) -> None:
        self._http.close()

    def __enter__(self) -> YapiClient:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def _get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        query: dict[str, Any] = {}
        if self.auth_mode == "open" and self.token:
            query["token"] = self.token
        if params:
            query.update({k: v for k, v in params.items() if v is not None})
        response = self._http.get(path, params=query or None)
        response.raise_for_status()
        body = response.json()
        if isinstance(body, dict) and body.get("errcode") not in (None, 0):
            raise YapiError(
                str(body.get("errmsg") or f"YApi error {body.get('errcode')}"),
                errcode=body.get("errcode"),
                payload=body,
            )
        return body.get("data") if isinstance(body, dict) and "data" in body else body

    def get_project(self, project_id: int | None = None) -> Any:
        params: dict[str, Any] = {}
        if project_id is not None:
            params["id"] = project_id
        return self._get("/api/project/get", params)

    def list_menu(self, project_id: int) -> Any:
        return self._get("/api/interface/list_menu", {"project_id": project_id})

    def list_interfaces(
        self,
        project_id: int,
        *,
        page: int = 1,
        limit: int = 1000,
    ) -> Any:
        return self._get(
            "/api/interface/list",
            {"project_id": project_id, "page": page, "limit": limit},
        )

    def list_cat(self, catid: int, *, page: int = 1, limit: int = 1000) -> Any:
        return self._get(
            "/api/interface/list_cat",
            {"catid": catid, "page": page, "limit": limit},
        )

    def get_interface(self, interface_id: int) -> Any:
        return self._get("/api/interface/get", {"id": interface_id})

    def get_cat_menu(self, project_id: int) -> Any:
        return self._get("/api/interface/getCatMenu", {"project_id": project_id})


def resolve_connection(
    *,
    url: str | None = None,
    base_url: str | None = None,
    token: str | None = None,
    uid: int | None = None,
) -> tuple[YapiSettings, YapiUrlParts | None]:
    parts: YapiUrlParts | None = None
    url_base: str | None = None
    if url:
        parts = parse_yapi_url(url)
        url_base = parts.base_url

    settings = load_settings(
        base_url=url_base or base_url,
        token=token,
        uid=uid,
    )
    if not settings.base_url and url_base:
        settings.base_url = url_base
    return settings, parts


class ClientSession:
    """Context manager yielding (client, parsed_url_parts)."""

    def __init__(
        self,
        *,
        url: str | None = None,
        base_url: str | None = None,
        token: str | None = None,
        uid: int | None = None,
    ) -> None:
        settings, parts = resolve_connection(
            url=url, base_url=base_url, token=token, uid=uid
        )
        self.client = YapiClient(settings)
        self.parts = parts

    def __enter__(self) -> tuple[YapiClient, YapiUrlParts | None]:
        return self.client, self.parts

    def __exit__(self, *args: object) -> None:
        self.client.close()


def open_client(
    *,
    url: str | None = None,
    base_url: str | None = None,
    token: str | None = None,
    uid: int | None = None,
) -> ClientSession:
    return ClientSession(url=url, base_url=base_url, token=token, uid=uid)
