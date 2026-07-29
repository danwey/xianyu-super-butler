from __future__ import annotations

import json
import unittest

import httpx

from xianyu_agent.client import XianyuClient, XianyuSettings


class XianyuClientTests(unittest.IsolatedAsyncioTestCase):
    async def test_login_cookie_is_reused_for_orders(self) -> None:
        seen_session = False

        async def handler(request: httpx.Request) -> httpx.Response:
            nonlocal seen_session
            if request.url.path == "/verify":
                return httpx.Response(200, json={"authenticated": False, "initialized": True})
            if request.url.path == "/login":
                body = json.loads(request.content)
                self.assertEqual(body["username"], "admin")
                return httpx.Response(
                    200,
                    headers={"set-cookie": "session=test-session; HttpOnly; Path=/"},
                    json={"success": True, "message": "登录成功"},
                )
            if request.url.path == "/api/orders":
                seen_session = request.headers.get("cookie") == "session=test-session"
                return httpx.Response(200, json={"orders": [{"id": "1"}], "total": 1})
            return httpx.Response(404, json={"detail": "not found"})

        settings = XianyuSettings(username="admin", password="secret")
        async with XianyuClient(settings, transport=httpx.MockTransport(handler)) as client:
            result = await client.list_orders()

        self.assertTrue(seen_session)
        self.assertEqual(result["total"], 1)
        self.assertEqual(result["orders"][0]["id"], "1")

    async def test_health_does_not_require_credentials(self) -> None:
        async def handler(request: httpx.Request) -> httpx.Response:
            self.assertEqual(request.url.path, "/health")
            return httpx.Response(200, json={"status": "healthy"})

        async with XianyuClient(transport=httpx.MockTransport(handler)) as client:
            result = await client.health()
        self.assertEqual(result["status"], "healthy")

    async def test_order_and_card_secrets_are_redacted(self) -> None:
        async def handler(request: httpx.Request) -> httpx.Response:
            if request.url.path == "/verify":
                return httpx.Response(200, json={"authenticated": True})
            if request.url.path == "/api/orders":
                return httpx.Response(200, json={
                    "orders": [{
                        "order_id": "o-1",
                        "receiver_phone": "13800000000",
                        "receiver_address": "private",
                        "amount": "10.00",
                    }]
                })
            if request.url.path == "/cards":
                return httpx.Response(200, json=[{
                    "id": 1,
                    "name": "test",
                    "type": "text",
                    "text_content": "secret-code",
                    "api_config": {"token": "secret"},
                    "enabled": True,
                }])
            return httpx.Response(404, json={"detail": "not found"})

        async with XianyuClient(transport=httpx.MockTransport(handler)) as client:
            orders = await client.list_orders()
            cards = await client.list_cards()

        order = orders["orders"][0]
        self.assertEqual(order["order_id"], "o-1")
        self.assertNotIn("receiver_phone", order)
        self.assertNotIn("receiver_address", order)
        self.assertEqual(cards, [{"id": 1, "name": "test", "type": "text", "enabled": True}])

    async def test_raw_data_order_list_is_not_returned(self) -> None:
        async def handler(request: httpx.Request) -> httpx.Response:
            if request.url.path == "/verify":
                return httpx.Response(200, json={"authenticated": True})
            if request.url.path == "/api/orders":
                return httpx.Response(200, json={
                    "data": [{
                        "order_id": "o-2",
                        "receiver_phone": "13900000000",
                    }],
                    "total": 1,
                })
            return httpx.Response(404, json={"detail": "not found"})

        async with XianyuClient(transport=httpx.MockTransport(handler)) as client:
            result = await client.list_orders()

        self.assertNotIn("data", result)
        self.assertEqual(result["orders"], [{"order_id": "o-2"}])


if __name__ == "__main__":
    unittest.main()
