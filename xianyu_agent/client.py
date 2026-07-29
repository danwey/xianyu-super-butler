"""HTTP client shared by the CLI and MCP server.

The client deliberately talks to the running FastAPI service instead of
importing CookieManager/XianyuLive. This prevents duplicate WebSocket workers,
multiple event loops, and concurrent writes to the same SQLite database.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Mapping

import httpx


_PRIVATE_ORDER_FIELDS = {
    "buyer_id",
    "chat_id",
    "receiver_name",
    "receiver_phone",
    "receiver_address",
    "receiver_city",
    "send_user_id",
    "user_url",
}

_CARD_METADATA_FIELDS = {
    "id",
    "name",
    "type",
    "description",
    "enabled",
    "delay_seconds",
    "is_multi_spec",
    "spec_name",
    "spec_value",
    "created_at",
    "updated_at",
}


class XianyuClientError(RuntimeError):
    """Raised when the xianyu-super-butler API cannot satisfy a request."""

    def __init__(self, message: str, *, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


@dataclass(frozen=True, slots=True)
class XianyuSettings:
    """Connection settings loaded from explicit values or environment variables."""

    base_url: str = "http://127.0.0.1:8080"
    username: str | None = None
    password: str | None = None
    timeout: float = 30.0
    verify_tls: bool = True

    @classmethod
    def from_env(cls) -> "XianyuSettings":
        verify_value = os.getenv("XIANYU_VERIFY_TLS", "true").strip().lower()
        return cls(
            base_url=os.getenv("XIANYU_BASE_URL", "http://127.0.0.1:8080").rstrip("/"),
            username=os.getenv("XIANYU_USERNAME") or None,
            password=os.getenv("XIANYU_PASSWORD") or None,
            timeout=float(os.getenv("XIANYU_TIMEOUT", "30")),
            verify_tls=verify_value not in {"0", "false", "no", "off"},
        )


class XianyuClient:
    """Async client for the existing xianyu-super-butler FastAPI service."""

    def __init__(
        self,
        settings: XianyuSettings | None = None,
        *,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.settings = settings or XianyuSettings.from_env()
        self._client = httpx.AsyncClient(
            base_url=self.settings.base_url,
            timeout=self.settings.timeout,
            verify=self.settings.verify_tls,
            follow_redirects=False,
            transport=transport,
            headers={"Accept": "application/json", "User-Agent": "xianyu-agent/0.1.0"},
        )
        self._authenticated = False

    async def __aenter__(self) -> "XianyuClient":
        return self

    async def __aexit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        await self._client.aclose()

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
        json: Any = None,
        require_auth: bool = True,
    ) -> Any:
        if require_auth:
            await self.ensure_authenticated()

        try:
            response = await self._client.request(method, path, params=params, json=json)
        except httpx.HTTPError as exc:
            raise XianyuClientError(f"无法连接闲鱼超级管家服务: {exc}") from exc

        content_type = response.headers.get("content-type", "")
        payload: Any
        if "application/json" in content_type:
            try:
                payload = response.json()
            except ValueError:
                payload = None
        else:
            payload = response.text

        if response.status_code >= 400:
            detail = None
            if isinstance(payload, dict):
                detail = payload.get("detail") or payload.get("message") or payload.get("msg")
            elif isinstance(payload, str):
                detail = payload.strip()
            raise XianyuClientError(
                str(detail or f"请求失败: HTTP {response.status_code}"),
                status_code=response.status_code,
            )

        return payload

    async def login(self) -> dict[str, Any]:
        if not self.settings.username or not self.settings.password:
            raise XianyuClientError(
                "缺少登录凭据，请设置 XIANYU_USERNAME 和 XIANYU_PASSWORD。"
            )

        payload = await self._request(
            "POST",
            "/login",
            json={"username": self.settings.username, "password": self.settings.password},
            require_auth=False,
        )
        if not isinstance(payload, dict) or not payload.get("success"):
            message = payload.get("message") if isinstance(payload, dict) else None
            raise XianyuClientError(str(message or "登录失败"))

        self._authenticated = True
        return payload

    async def ensure_authenticated(self) -> None:
        if self._authenticated:
            return

        verify = await self.verify_session(require_auth=False)
        if verify.get("authenticated"):
            self._authenticated = True
            return
        await self.login()

    async def health(self) -> dict[str, Any]:
        payload = await self._request("GET", "/health", require_auth=False)
        return _require_dict(payload, "健康检查")

    async def verify_session(self, *, require_auth: bool = False) -> dict[str, Any]:
        payload = await self._request("GET", "/verify", require_auth=require_auth)
        return _require_dict(payload, "会话验证")

    async def list_accounts(self) -> list[dict[str, Any]]:
        payload = await self._request("GET", "/cookies/details")
        return _extract_list(payload, keys=("accounts", "cookies", "data"), operation="账号列表")

    async def list_orders(
        self,
        *,
        account_id: str | None = None,
        status: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict[str, Any]:
        if page < 1:
            raise XianyuClientError("page 必须大于等于 1")
        if not 1 <= page_size <= 100:
            raise XianyuClientError("page_size 必须在 1 到 100 之间")

        params: dict[str, Any] = {"page": page, "page_size": page_size}
        if account_id:
            params["cookie_id"] = account_id
        if status and status != "all":
            params["status"] = status

        payload = await self._request("GET", "/api/orders", params=params)
        if isinstance(payload, list):
            orders = [_strip_fields(item, _PRIVATE_ORDER_FIELDS) for item in payload]
            return {"orders": orders, "total": len(orders), "page": page, "page_size": page_size}
        result = _require_dict(payload, "订单列表")
        orders = result.get("orders") or result.get("data") or []
        if not isinstance(orders, list):
            raise XianyuClientError("订单列表返回格式无效")
        safe_orders = [_strip_fields(item, _PRIVATE_ORDER_FIELDS) for item in orders]
        return {
            **result,
            "orders": safe_orders,
            "total": result.get("total", len(safe_orders)),
            "page": result.get("page", page),
            "page_size": result.get("page_size", page_size),
        }

    async def get_order(self, order_id: str) -> dict[str, Any]:
        if not order_id.strip():
            raise XianyuClientError("order_id 不能为空")
        payload = await self._request("GET", f"/api/orders/{order_id}")
        result = _require_dict(payload, "订单详情")
        order = _require_dict(result.get("order") or result.get("data") or result, "订单详情")
        return _strip_fields(order, _PRIVATE_ORDER_FIELDS)

    async def list_items(self) -> list[dict[str, Any]]:
        payload = await self._request("GET", "/items")
        return _extract_list(payload, keys=("items", "data"), operation="商品列表")

    async def list_cards(self) -> list[dict[str, Any]]:
        payload = await self._request("GET", "/cards")
        cards = _extract_list(payload, keys=("cards", "data"), operation="卡券列表")
        return [
            {key: value for key, value in card.items() if key in _CARD_METADATA_FIELDS}
            for card in cards
        ]

    async def list_delivery_rules(self) -> list[dict[str, Any]]:
        payload = await self._request("GET", "/delivery-rules")
        return _extract_list(payload, keys=("rules", "data"), operation="发货规则")

    async def list_reply_rules(self, account_id: str) -> list[dict[str, Any]]:
        if not account_id.strip():
            raise XianyuClientError("account_id 不能为空")
        payload = await self._request("GET", f"/keywords-with-item-id/{account_id}")
        return _extract_list(payload, keys=("keywords", "data"), operation="回复规则")

    async def order_analytics(self, *, start_date: str, end_date: str) -> dict[str, Any]:
        if not start_date or not end_date:
            raise XianyuClientError("start_date 和 end_date 不能为空")
        payload = await self._request(
            "GET",
            "/analytics/orders",
            params={"start_date": start_date, "end_date": end_date},
        )
        return _require_dict(payload, "订单分析")


def _require_dict(payload: Any, operation: str) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise XianyuClientError(f"{operation}返回格式无效")
    return payload


def _strip_fields(payload: dict[str, Any], fields: set[str]) -> dict[str, Any]:
    return {key: value for key, value in payload.items() if key.lower() not in fields}


def _extract_list(payload: Any, *, keys: tuple[str, ...], operation: str) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        values = payload
    elif isinstance(payload, dict):
        values = None
        for key in keys:
            candidate = payload.get(key)
            if isinstance(candidate, list):
                values = candidate
                break
        if values is None:
            raise XianyuClientError(f"{operation}返回格式无效")
    else:
        raise XianyuClientError(f"{operation}返回格式无效")

    if not all(isinstance(item, dict) for item in values):
        raise XianyuClientError(f"{operation}包含无效项目")
    return values
