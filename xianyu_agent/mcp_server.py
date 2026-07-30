"""Read-only MCP server for xianyu-super-butler."""

from __future__ import annotations

import os
from typing import Any

from mcp.server.fastmcp import FastMCP

from .client import XianyuClient


mcp = FastMCP(
    "Xianyu Super Butler",
    instructions=(
        "Read-only tools for accounts, orders, products, cards, rules and analytics. "
        "Never request or reveal account cookies, passwords or AI API keys."
    ),
    json_response=True,
)


async def _call(method: str, *args: Any, **kwargs: Any) -> Any:
    async with XianyuClient() as client:
        return await getattr(client, method)(*args, **kwargs)


@mcp.tool()
async def xianyu_health() -> dict[str, Any]:
    """Check the xianyu-super-butler service, database and CookieManager status."""
    return await _call("health")


@mcp.tool()
async def xianyu_list_accounts() -> list[dict[str, Any]]:
    """List accessible Xianyu accounts without returning Cookie values."""
    accounts = await _call("list_accounts")
    sensitive = {"value", "cookie", "login_password", "password", "api_key"}
    return [{key: value for key, value in item.items() if key not in sensitive} for item in accounts]


@mcp.tool()
async def xianyu_list_orders(
    account_id: str | None = None,
    status: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> dict[str, Any]:
    """List orders, optionally filtered by Xianyu account and order status."""
    return await _call(
        "list_orders",
        account_id=account_id,
        status=status,
        page=page,
        page_size=page_size,
    )


@mcp.tool()
async def xianyu_get_order(order_id: str) -> dict[str, Any]:
    """Get one order by its order ID."""
    return await _call("get_order", order_id)


@mcp.tool()
async def xianyu_list_items() -> list[dict[str, Any]]:
    """List locally synchronized Xianyu products."""
    return await _call("list_items")


@mcp.tool()
async def xianyu_list_cards() -> list[dict[str, Any]]:
    """List card metadata with delivery contents and API configuration removed."""
    return await _call("list_cards")


@mcp.tool()
async def xianyu_list_delivery_rules() -> list[dict[str, Any]]:
    """List automatic delivery rules. This tool does not change any rule."""
    return await _call("list_delivery_rules")


@mcp.tool()
async def xianyu_list_reply_rules(account_id: str) -> list[dict[str, Any]]:
    """List keyword reply rules for one Xianyu account."""
    return await _call("list_reply_rules", account_id)


@mcp.tool()
async def xianyu_order_analytics(start_date: str, end_date: str) -> dict[str, Any]:
    """Get order analytics for an inclusive YYYY-MM-DD date range."""
    return await _call("order_analytics", start_date=start_date, end_date=end_date)


def main() -> None:
    transport = os.getenv("XIANYU_MCP_TRANSPORT", "stdio").strip().lower()
    if transport == "stdio":
        mcp.run()
    elif transport in {"streamable-http", "sse"}:
        host = os.getenv("XIANYU_MCP_HOST", "127.0.0.1").strip() or "127.0.0.1"
        try:
            port = int(os.getenv("XIANYU_MCP_PORT", "8000"))
        except ValueError as exc:
            raise SystemExit("XIANYU_MCP_PORT 必须是整数") from exc
        mcp.run(transport=transport, host=host, port=port)
    else:
        raise SystemExit(f"不支持的 XIANYU_MCP_TRANSPORT: {transport}")


if __name__ == "__main__":
    main()
