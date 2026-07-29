# Tool inventory

- `xianyu_health`: service, database, and CookieManager status.
- `xianyu_list_accounts`: accessible account metadata with sensitive fields removed.
- `xianyu_list_orders`: paginated orders with optional account and status filters; recipient and buyer identifiers are removed.
- `xianyu_get_order`: one order by exact ID with private recipient and buyer fields removed.
- `xianyu_list_items`: synchronized product records.
- `xianyu_list_cards`: card metadata with delivery contents and API configuration removed.
- `xianyu_list_delivery_rules`: read-only delivery rules.
- `xianyu_list_reply_rules`: read-only keyword rules for one account.
- `xianyu_order_analytics`: analytics for an explicit date range.

No v1 tool performs shipping, deletion, import, credential changes, or configuration writes.
