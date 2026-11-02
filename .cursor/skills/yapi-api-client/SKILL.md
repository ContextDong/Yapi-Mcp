---
name: yapi-api-client
description: >-
  Fetch YApi project API docs (JSON request/response) from a pasted project URL
  and implement client integrations. Use when the user pastes a yapi URL such as
  https://yapi.example.com/project/123/interface/api/, mentions YApi, or asks to
 对接 / generate API client code from YApi documentation.
---

# YApi → Client Integration

## Goal

User pastes a YApi project URL in chat. Agent fetches the project's API docs
(JSON in / JSON out) and implements or updates the client-side integration.

## Prerequisites

1. MCP server `yapi` / `yapi-mcp` is configured.
2. Credentials via **dynamic config** (do not hardcode secrets in repo):
   - env `YAPI_TOKEN` (+ optional `YAPI_BASE_URL`), or
   - `.yapi-mcp.json`, or
   - `yapi_configure` / per-tool `token` when the user pastes credentials in chat.
3. Auth may be login JWT (cookies) or project open token.

If tools return 登录 / missing token errors, ask the user for a fresh token and call `yapi_configure`.

## Workflow

```
YApi client task:
- [ ] 1. Ensure credentials (yapi_get_config / yapi_configure)
- [ ] 2. Parse URL
- [ ] 3. List / search interfaces
- [ ] 4. Pull details for needed APIs
- [ ] 5. Map to client code
- [ ] 6. Implement + verify types against JSON schemas
```

### 1. Parse URL

Call `yapi_parse_url` with the pasted URL → `base_url`, `project_id`, optional `interface_id`.

### 2. Discover APIs

- `yapi_get_project` + `yapi_list_interfaces`
- Filter with `keyword` / `path` / `method`
- Bulk index: `yapi_export_catalog` (`include_details=false` first)

Do **not** dump every interface detail unless needed.

### 3. Load definitions

`yapi_get_interface` → normalized `request` / `response` JSON.

### 4. Client implementation rules

1. Reuse the project's existing HTTP client, auth, base URL, and error envelope.
2. Path = `project.basepath` + `interface.path` when set; confirm against env config.
3. Prefer typed models from JSON Schema / examples when the stack supports it.
4. Handle common wrappers (`error_code` / `errcode` / `data`) like existing code.
5. Prefer small modules per feature area.

## Anti-patterns

- Scraping SPA HTML instead of MCP tools
- Committing tokens / private hosts into the client repo
- Guessing fields when `yapi_get_interface` is available
- Fetching all interface details by default
