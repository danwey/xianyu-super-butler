"""Command-line interface for Agent and shell usage."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from dataclasses import replace
from typing import Any, Awaitable, Callable

from .client import XianyuClient, XianyuClientError, XianyuSettings


async def _run(args: argparse.Namespace) -> Any:
    settings = XianyuSettings.from_env()
    if args.base_url:
        settings = replace(settings, base_url=args.base_url.rstrip("/"))
    if args.username:
        settings = replace(settings, username=args.username)
    if args.timeout is not None:
        settings = replace(settings, timeout=args.timeout)
    if args.insecure:
        settings = replace(settings, verify_tls=False)

    async with XianyuClient(settings) as client:
        handler: Callable[[], Awaitable[Any]]
        command = args.command

        if command == "health":
            handler = client.health
        elif command == "verify":
            handler = lambda: client.verify_session(require_auth=True)
        elif command == "accounts":
            handler = client.list_accounts
        elif command == "orders-list":
            handler = lambda: client.list_orders(
                account_id=args.account_id,
                status=args.status,
                page=args.page,
                page_size=args.page_size,
            )
        elif command == "orders-show":
            handler = lambda: client.get_order(args.order_id)
        elif command == "items":
            handler = client.list_items
        elif command == "cards":
            handler = client.list_cards
        elif command == "delivery-rules":
            handler = client.list_delivery_rules
        elif command == "reply-rules":
            handler = lambda: client.list_reply_rules(args.account_id)
        elif command == "analytics-orders":
            handler = lambda: client.order_analytics(
                start_date=args.start_date,
                end_date=args.end_date,
            )
        else:  # pragma: no cover - argparse prevents this branch
            raise XianyuClientError(f"未知命令: {command}")

        return await handler()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="xianyu-agent",
        description="闲鱼超级管家只读 Agent CLI",
    )
    parser.add_argument("--base-url", help="服务地址，默认读取 XIANYU_BASE_URL")
    parser.add_argument("--username", help="登录用户名，默认读取 XIANYU_USERNAME")
    parser.add_argument("--timeout", type=float, help="请求超时秒数")
    parser.add_argument("--insecure", action="store_true", help="关闭 TLS 证书校验")
    parser.add_argument("--compact", action="store_true", help="输出紧凑 JSON")

    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("health", help="检查服务状态")
    sub.add_parser("verify", help="验证登录会话")
    sub.add_parser("accounts", help="列出闲鱼账号")

    orders = sub.add_parser("orders-list", help="查询订单")
    orders.add_argument("--account-id")
    orders.add_argument("--status")
    orders.add_argument("--page", type=int, default=1)
    orders.add_argument("--page-size", type=int, default=20)

    order = sub.add_parser("orders-show", help="查看订单详情")
    order.add_argument("order_id")

    sub.add_parser("items", help="列出商品")
    sub.add_parser("cards", help="列出卡券")
    sub.add_parser("delivery-rules", help="列出发货规则")

    reply_rules = sub.add_parser("reply-rules", help="列出账号回复规则")
    reply_rules.add_argument("account_id")

    analytics = sub.add_parser("analytics-orders", help="查询订单分析")
    analytics.add_argument("--start-date", required=True, help="YYYY-MM-DD")
    analytics.add_argument("--end-date", required=True, help="YYYY-MM-DD")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        result = asyncio.run(_run(args))
    except (XianyuClientError, ValueError) as exc:
        error = {
            "success": False,
            "error": str(exc),
            "status_code": getattr(exc, "status_code", None),
        }
        print(json.dumps(error, ensure_ascii=False), file=sys.stderr)
        return 1

    print(
        json.dumps(
            {"success": True, "data": result},
            ensure_ascii=False,
            indent=None if args.compact else 2,
            default=str,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
