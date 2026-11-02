"""Parse YApi web URLs into base_url / project_id / interface_id."""

from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import urlparse


_PROJECT_RE = re.compile(
    r"/project/(?P<project_id>\d+)(?:/interface(?:/api(?:/(?P<interface_id>\d+))?)?)?",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class YapiUrlParts:
    base_url: str
    project_id: int | None = None
    interface_id: int | None = None
    raw_path: str = ""


def parse_yapi_url(url: str) -> YapiUrlParts:
    """Extract host root and IDs from a YApi page or OpenAPI-style URL.

    Supported examples:
    - http://yapi.example.com/project/529/interface/api/
    - http://yapi.example.com/project/529/interface/api/12345
    - http://yapi.example.com/project/529
    - http://yapi.example.com  (base only)
    """
    text = (url or "").strip()
    if not text:
        raise ValueError("url is empty")

    if "://" not in text:
        text = "http://" + text

    parsed = urlparse(text)
    if not parsed.scheme or not parsed.netloc:
        raise ValueError(f"invalid url: {url!r}")

    base_url = f"{parsed.scheme}://{parsed.netloc}".rstrip("/")
    match = _PROJECT_RE.search(parsed.path or "")
    if not match:
        return YapiUrlParts(base_url=base_url, raw_path=parsed.path or "")

    project_id = int(match.group("project_id"))
    interface_raw = match.group("interface_id")
    interface_id = int(interface_raw) if interface_raw else None
    return YapiUrlParts(
        base_url=base_url,
        project_id=project_id,
        interface_id=interface_id,
        raw_path=parsed.path or "",
    )
