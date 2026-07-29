# Agent adapter: CLI + MCP + Skill

This repository includes a read-only Agent layer for the existing FastAPI service. It calls the running service over HTTP instead of importing `CookieManager` or `XianyuLive`, so the project keeps a single WebSocket and event-loop owner.

## Install

```bash
pip install -r requirements.txt
pip install -r agent-requirements.txt
```

Set credentials only through local environment variables:

```bash
export XIANYU_BASE_URL=http://127.0.0.1:8080
export XIANYU_USERNAME=admin
export XIANYU_PASSWORD='replace-with-your-password'
```

Do not commit credentials or pass the password as a command-line argument.

## CLI

```bash
python -m xianyu_agent health
python -m xianyu_agent accounts
python -m xianyu_agent orders-list --status pending --page-size 20
python -m xianyu_agent orders-show ORDER_ID
python -m xianyu_agent cards
python -m xianyu_agent reply-rules ACCOUNT_ID
python -m xianyu_agent analytics-orders --start-date 2026-07-01 --end-date 2026-07-30
```

Every command prints a JSON envelope:

```json
{"success": true, "data": {}}
```

## MCP over stdio

```bash
python -m xianyu_agent.mcp_server
```

Generic MCP client configuration:

```json
{
  "command": "python",
  "args": ["-m", "xianyu_agent.mcp_server"],
  "env": {
    "XIANYU_BASE_URL": "http://127.0.0.1:8080",
    "XIANYU_USERNAME": "admin",
    "XIANYU_PASSWORD": "replace-with-your-password"
  }
}
```

For a local Streamable HTTP MCP server:

```bash
XIANYU_MCP_TRANSPORT=streamable-http python -m xianyu_agent.mcp_server
```

## Tests

```bash
python -m unittest discover -s tests -p 'test_*.py'
```

## Security

The first release exposes read-only tools only. Order recipient and buyer identifiers are removed before results reach the CLI or MCP client. Card delivery contents and API configuration are also removed.

Shipping, deletion, order import, Cookie changes, AI keys, and rule writes are intentionally unavailable. Add those later only with scoped Agent tokens, audit logs, idempotency keys, preview operations, and one-time confirmation tokens.
