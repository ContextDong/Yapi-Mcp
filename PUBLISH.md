# Publish checklist

Local open-source prep is done (secrets removed, dynamic config, `server.json`). Finish distribution with your GitHub / PyPI accounts:

## 1. GitHub

```powershell
gh auth login --hostname github.com --git-protocol https --web
cd "D:\python code\yapi"
gh repo create ContextDong/Yapi-Mcp --public --source=. --remote=origin --push
```

If the empty repo already exists:

```powershell
git remote add origin https://github.com/ContextDong/Yapi-Mcp.git
git push -u origin main
```

## 2. PyPI (required for Official MCP Registry `pypi` package)

```powershell
python -m pip install build twine
python -m build
python -m twine upload dist/*
```

README already contains: `<!-- mcp-name: io.github.ContextDong/yapi-mcp -->`

## 3. Official MCP Registry

```powershell
# Windows amd64
Invoke-WebRequest -Uri "https://github.com/modelcontextprotocol/registry/releases/latest/download/mcp-publisher_windows_amd64.tar.gz" -OutFile mcp-publisher.tar.gz
tar xf mcp-publisher.tar.gz mcp-publisher.exe
.\mcp-publisher.exe login github
.\mcp-publisher.exe publish
```

Verify:

```text
https://registry.modelcontextprotocol.io/v0.1/servers?search=io.github.ContextDong/yapi-mcp
```

## Consumer install (after PyPI)

See `mcp.example.json` / README (`uvx --from yapi-mcp yapi-mcp` + `YAPI_BASE_URL` / `YAPI_TOKEN`).
