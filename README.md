# Yapi-Mcp

从粘贴的 [YApi](https://github.com/YMFE/yapi) 项目地址拉取接口文档（JSON 请求 / JSON 响应），供编码 Agent 自动理解并对接客户端项目的 MCP Server。

[English](README_EN.md)

<!-- mcp-name: io.github.ContextDong/yapi-mcp -->

## 功能

- 解析 YApi 页面 URL → `base_url` / `project_id` / `interface_id`
- 列出 / 搜索接口，导出目录
- 拉取归一化后的请求与响应 JSON（JSON Schema / 示例）
- 鉴权：登录 JWT（Cookie `_yapi_token` + `_yapi_uid`）或项目 open token
- **动态凭证**：环境变量、`.env`、`.yapi-mcp.json`、运行时 `yapi_configure`、或工具参数

## 快速接入

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

从 Git 安装（不经 PyPI）：

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

或使用 pip：

```bash
pip install contextdong-yapi-mcp
# 或: pip install git+https://github.com/ContextDong/Yapi-Mcp
```

## 配置凭证（仓库内不存放密钥）

优先级从高到低：

1. 工具参数（`token`、`base_url`）
2. 运行时 `yapi_configure`（仅当前 MCP 进程内存）
3. 环境变量 / `.env`（`YAPI_BASE_URL`、`YAPI_TOKEN`、`YAPI_UID`、`YAPI_COOKIE`）
4. 配置文件 `.yapi-mcp.json`，或 `YAPI_MCP_CONFIG` 指向的路径

示例：

```bash
cp .env.example .env
cp .yapi-mcp.example.json .yapi-mcp.json
```

| 变量 | 说明 |
|------|------|
| `YAPI_BASE_URL` | YApi 主机，如 `https://yapi.example.com` |
| `YAPI_TOKEN` | 登录 JWT **或** 项目 open token |
| `YAPI_UID` | 可选；登录 JWT 一般会自动解析 `uid` |
| `YAPI_COOKIE` | 可选；原始 Cookie 头覆盖 |
| `YAPI_MCP_CONFIG` | 可选；JSON 配置文件路径 |

**切勿提交** `.env`、`.yapi-mcp.json` 或真实 token。

## 工具列表

| 工具 | 用途 |
|------|------|
| `yapi_configure` / `yapi_get_config` | 动态配置 / 查看非敏感配置 |
| `yapi_parse_url` | 从页面 URL 解析主机与 id |
| `yapi_get_project` | 项目元信息 |
| `yapi_list_interfaces` | 可搜索的接口索引 |
| `yapi_get_interface` | 单个接口完整 JSON 定义（便于写客户端） |
| `yapi_export_catalog` | 导出目录（可选详情） |

## Agent 用法

在对话中粘贴项目地址：

```text
根据 https://yapi.example.com/project/123/interface/api/ 对接登录相关接口
```

Agent 应先配置凭证（如需要），再列表 / 拉详情，最后按目标工程现有风格实现客户端。

可选 Skill：`.cursor/skills/yapi-api-client/SKILL.md`

## 本地开发

```bash
python -m pip install -e ".[dev]"
python -m pytest
python -m yapi_mcp.server
```

## MCP Registry

- 官方名：`io.github.ContextDong/yapi-mcp`
- PyPI 包：`contextdong-yapi-mcp`（`uvx` / 命令 `yapi-mcp`）
- 说明：短名 `yapi-mcp` 在 PyPI 上已被其他项目占用

## License

MIT
