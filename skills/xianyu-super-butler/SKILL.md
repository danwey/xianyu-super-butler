---
name: xianyu-super-butler
description: Use the xianyu-super-butler CLI or MCP tools to inspect Xianyu accounts, orders, products, card metadata, reply rules, delivery rules, and order analytics. Use this skill for Xianyu store diagnostics and read-only operational reporting.
---

# Xianyu Super Butler

Use the MCP tools when available. Use `python -m xianyu_agent` as the fallback CLI.

## Safety boundary

This version is deliberately read-only.

- Never ask the user to paste a Xianyu Cookie, session Cookie, password, or AI API key into chat.
- Read credentials only from the local environment.
- Never invoke shipping, deletion, Cookie-update, order-import, or rule-write endpoints.
- Recipient names, phone numbers, addresses, buyer IDs, chat IDs, card delivery contents, and card API configuration are removed by the client.
- Treat all remaining order and buyer data as private.

## Environment

The running service is expected at `XIANYU_BASE_URL`, defaulting to `http://127.0.0.1:8080`.
Authentication uses the existing web login endpoint and HttpOnly Cookie Session:

- `XIANYU_USERNAME`
- `XIANYU_PASSWORD`

## Standard workflow

1. Call `xianyu_health` first when diagnosing connectivity.
2. Call `xianyu_list_accounts` to resolve an account ID instead of guessing it.
3. Use paginated order queries. Start with 20 records and increase only when needed.
4. Retrieve a single order only after obtaining its exact order ID.
5. For analytics, use explicit `YYYY-MM-DD` dates.
6. Summarize the result and clearly distinguish API data from inference.

## Common tasks

- Store status: health, accounts, and recent orders.
- Pending-order review: list orders using the backend's pending status value.
- Rule audit: list reply and delivery rules; identify missing, duplicate, or conflicting entries without modifying them.
- Card configuration review: inspect card names, types, enabled state, delay, and specification metadata without accessing delivery contents.

See `references/tools.md` for the tool inventory.
