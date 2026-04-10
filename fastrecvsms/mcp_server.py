"""MCP (Model Context Protocol) server for FastRecvSMS.

Exposes SMS verification tools to AI coding assistants:
Claude Code, Codex, Gemini, Cursor, etc.

Usage:
  fastrecvsms-mcp            # stdio mode (default for Claude Code / Cursor)

Config for Claude Code (~/.claude/settings.json):
  {
    "mcpServers": {
      "fastrecvsms": {
        "command": "fastrecvsms-mcp"
      }
    }
  }
"""

import json
from typing import Any

from mcp.server import Server
from mcp.server.stdio import run_stdio
from mcp.types import TextContent, Tool

from fastrecvsms.config import Config
from fastrecvsms.providers import get_provider

server = Server("fastrecvsms")

# Track active orders across tool calls
_active_orders: dict[int, dict] = {}


def _get_provider(provider_name: str | None = None):
    cfg = Config()
    name = provider_name or cfg.default_provider
    api_key = cfg.get_api_key(name)
    if not api_key:
        raise ValueError(f"No API key for {name}. Run: fastrecvsms config set-key {name} YOUR_KEY")
    return get_provider(name, api_key)


@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="get_balance",
            description="Check account balance for an SMS provider (5sim or sms-activate).",
            inputSchema={
                "type": "object",
                "properties": {
                    "provider": {"type": "string", "enum": ["5sim", "sms-activate"], "description": "SMS provider"},
                },
            },
        ),
        Tool(
            name="list_services",
            description="List available services (WhatsApp, Telegram, etc.) with prices and available numbers for a country.",
            inputSchema={
                "type": "object",
                "properties": {
                    "country": {"type": "string", "description": "Country name or code (e.g., russia, usa, india)", "default": "any"},
                    "provider": {"type": "string", "enum": ["5sim", "sms-activate"]},
                },
            },
        ),
        Tool(
            name="buy_number",
            description="Buy a temporary phone number for receiving SMS verification codes.",
            inputSchema={
                "type": "object",
                "properties": {
                    "service": {"type": "string", "description": "Service name (e.g., whatsapp, telegram, google, twitter)"},
                    "country": {"type": "string", "description": "Country (e.g., russia, usa)", "default": "any"},
                    "provider": {"type": "string", "enum": ["5sim", "sms-activate"]},
                },
                "required": ["service"],
            },
        ),
        Tool(
            name="check_sms",
            description="Check if an SMS verification code has been received for an active order.",
            inputSchema={
                "type": "object",
                "properties": {
                    "order_id": {"type": "integer", "description": "Order ID from buy_number"},
                    "provider": {"type": "string", "enum": ["5sim", "sms-activate"]},
                },
                "required": ["order_id"],
            },
        ),
        Tool(
            name="wait_for_sms",
            description="Wait for an SMS code to arrive, polling every few seconds until received or timeout.",
            inputSchema={
                "type": "object",
                "properties": {
                    "order_id": {"type": "integer", "description": "Order ID from buy_number"},
                    "timeout": {"type": "integer", "description": "Max wait time in seconds", "default": 120},
                    "provider": {"type": "string", "enum": ["5sim", "sms-activate"]},
                },
                "required": ["order_id"],
            },
        ),
        Tool(
            name="cancel_order",
            description="Cancel an active order and release the phone number.",
            inputSchema={
                "type": "object",
                "properties": {
                    "order_id": {"type": "integer", "description": "Order ID to cancel"},
                    "provider": {"type": "string", "enum": ["5sim", "sms-activate"]},
                },
                "required": ["order_id"],
            },
        ),
        Tool(
            name="finish_order",
            description="Mark an order as finished after successfully receiving the SMS code.",
            inputSchema={
                "type": "object",
                "properties": {
                    "order_id": {"type": "integer", "description": "Order ID to finish"},
                    "provider": {"type": "string", "enum": ["5sim", "sms-activate"]},
                },
                "required": ["order_id"],
            },
        ),
        Tool(
            name="list_active_orders",
            description="List all active (pending) orders in this session.",
            inputSchema={"type": "object", "properties": {}},
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    try:
        result = _dispatch(name, arguments)
        return [TextContent(type="text", text=json.dumps(result, indent=2))]
    except Exception as e:
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]


def _dispatch(name: str, args: dict) -> Any:
    provider_name = args.get("provider")

    if name == "get_balance":
        p = _get_provider(provider_name)
        bal = p.get_balance()
        return {"amount": bal.amount, "currency": bal.currency, "provider": bal.provider}

    elif name == "list_services":
        p = _get_provider(provider_name)
        services = p.get_services(country=args.get("country", "any"))
        return [{"name": s.name, "quantity": s.quantity, "price": s.price, "country": s.country} for s in services[:50]]

    elif name == "buy_number":
        p = _get_provider(provider_name)
        order = p.buy_number(args["service"], country=args.get("country", "any"))
        _active_orders[order.id] = {
            "id": order.id, "phone": order.phone, "service": order.service,
            "country": order.country, "price": order.price, "provider": order.provider,
        }
        return {
            "order_id": order.id, "phone": order.phone, "country": order.country,
            "service": order.service, "price": order.price, "status": order.status.value,
            "provider": order.provider,
        }

    elif name == "check_sms":
        p = _get_provider(provider_name)
        order = p.check_order(args["order_id"])
        return {
            "order_id": order.id, "phone": order.phone, "status": order.status.value,
            "sms_code": order.sms_code, "sms_text": order.sms_text,
        }

    elif name == "wait_for_sms":
        import time
        p = _get_provider(provider_name)
        timeout = args.get("timeout", 120)
        start = time.time()
        while time.time() - start < timeout:
            order = p.check_order(args["order_id"])
            if order.sms_code:
                return {
                    "order_id": order.id, "phone": order.phone, "status": order.status.value,
                    "sms_code": order.sms_code, "sms_text": order.sms_text,
                    "waited": f"{time.time() - start:.0f}s",
                }
            if order.status.value in ("CANCELED", "TIMEOUT", "BANNED"):
                return {"order_id": order.id, "status": order.status.value, "sms_code": None, "error": "Order ended without SMS"}
            time.sleep(5)
        return {"order_id": args["order_id"], "status": "TIMEOUT", "sms_code": None, "error": f"No SMS received within {timeout}s"}

    elif name == "cancel_order":
        p = _get_provider(provider_name)
        success = p.cancel_order(args["order_id"])
        _active_orders.pop(args["order_id"], None)
        return {"success": success, "order_id": args["order_id"]}

    elif name == "finish_order":
        p = _get_provider(provider_name)
        success = p.finish_order(args["order_id"])
        _active_orders.pop(args["order_id"], None)
        return {"success": success, "order_id": args["order_id"]}

    elif name == "list_active_orders":
        return list(_active_orders.values())

    return {"error": f"Unknown tool: {name}"}


def main():
    """Entry point for fastrecvsms-mcp command."""
    import asyncio
    asyncio.run(run_stdio(server))


if __name__ == "__main__":
    main()
