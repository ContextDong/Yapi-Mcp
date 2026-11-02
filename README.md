# Yapi-Mcp

MCP server that fetches [YApi](https://github.com/YMFE/yapi) project API docs (JSON request / JSON response) so coding agents can integrate client projects from a pasted YApi URL.

<!-- mcp-name: io.github.ContextDong/yapi-mcp -->

## Features

- Parse YApi page URLs → `base_url` / `project_id` / `interface_id`
- List / search interfaces, export catalogs
- Fetch normalized request & response JSON (JSON Schema / examples)
- Auth: **login JWT** (Cookie `_yapi_token` + `_yapi_uid`) or **project open token**
- **Dynamic credentials**: env, `.env`, `.yapi-mcp.json`, runtime `yapi_configure`, or per-tool args

## Quick install (consumers)

### Cursor / Claude Desktop MCP

```json
{
  "mcpServers": {
    "yapi": {
      "command": "uvx",
      "args": ["--from", "contextdong-yapi-mcp", "yapi-mcp"],
      "env": {
        "YAPI_BASE_URL": "https://yapi.example.com",
        "YAPI_TOKEN": "YOUR_LOGIN_JWT_OR_PROJECT_OPEN_TOKEN"
      }
    }
  }
}
```

From Git (before / without PyPI):

```json
{
  "mcpServers": {
    "yapi": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/ContextDong/Yapi-Mcp",
        "yapi-mcp"
      ],
      "env": {
        "YAPI_BASE_URL": "https://yapi.example.com",
        "YAPI_TOKEN": "YOUR_TOKEN"
      }
    }
  }
}
```

Or pip:

```bash
pip install contextdong-yapi-mcp
# or: pip install git+https://github.com/ContextDong/Yapi-Mcp
```

## Configure credentials (no secrets in repo)

Priority (high → low):

1. Tool arguments (`token`, `base_url`)
2. Runtime `yapi_configure` (in-memory for the MCP process)
3. Environment / `.env` (`YAPI_BASE_URL`, `YAPI_TOKEN`, `YAPI_UID`, `YAPI_COOKIE`)
4. Config file `.yapi-mcp.json` or path in `YAPI_MCP_CONFIG`

Copy examples:

```bash
cp .env.example .env
cp .yapi-mcp.example.json .yapi-mcp.json
```

| Variable | Description |
|----------|-------------|
| `YAPI_BASE_URL` | YApi host, e.g. `https://yapi.example.com` |
| `YAPI_TOKEN` | Login JWT **or** project open token |
| `YAPI_UID` | Optional; login JWT usually auto-parses `uid` |
| `YAPI_COOKIE` | Optional raw `Cookie` header override |
| `YAPI_MCP_CONFIG` | Optional path to JSON config file |

**Never commit** `.env`, `.yapi-mcp.json`, or real tokens.

## Tools

| Tool | Purpose |
|------|---------|
| `yapi_configure` / `yapi_get_config` | Dynamic non-durable / inspect settings |
| `yapi_parse_url` | Extract host + ids from a page URL |
| `yapi_get_project` | Project metadata |
| `yapi_list_interfaces` | Searchable interface index |
| `yapi_get_interface` | Full JSON req/res for codegen |
| `yapi_export_catalog` | Catalog (+ optional details) |

## Agent usage

Paste a project URL in chat:

```text
Integrate APIs from https://yapi.example.com/project/123/interface/api/
```

The agent should configure credentials (if needed), list interfaces, pull details, then implement the client against your codebase conventions.

Project skill (optional): `.cursor/skills/yapi-api-client/SKILL.md`

## Local development

```bash
python -m pip install -e ".[dev]"
python -m pytest
python -m yapi_mcp.server
```

## MCP Registry

Official registry name: `io.github.ContextDong/yapi-mcp`  
Package: PyPI `contextdong-yapi-mcp` (stdio via `uvx` / `yapi-mcp`)  
Note: the shorter name `yapi-mcp` is already taken on PyPI by another project.

## License

MIT
