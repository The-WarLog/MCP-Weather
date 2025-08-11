# whatsapp_adapter.py
import os
import json
import asyncio
import threading
import logging
from typing import Dict, Any
import httpx
from fastapi import FastAPI, Request, HTTPException
from starlette.responses import PlainTextResponse

# import the get_weather tool function directly from your MCP module
# Make sure puch.py does NOT call mcp.run() on import (it shouldn't).
from puch import get_weather  # <- your MCP module (ensure function importable)

from mcp.server.fastmcp import FastMCP

# --- config / env ---
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")          # Page Access Token
WHATSAPP_PHONE_ID = os.getenv("WHATSAPP_PHONE_ID")    # Phone number id (e.g. 1081234567890)
VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN", "puch_verify_token")
PORT = int(os.getenv("PORT", "8080"))
GRAPH_API_VERSION = os.getenv("GRAPH_API_VERSION", "v17.0")
GRAPH_URL = f"https://graph.facebook.com/{GRAPH_API_VERSION}/{WHATSAPP_PHONE_ID}/messages"

if not WHATSAPP_TOKEN or not WHATSAPP_PHONE_ID:
    raise RuntimeError("WHATSAPP_TOKEN and WHATSAPP_PHONE_ID must be configured")

# logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("puch.whatsapp")

app = FastAPI()

# simple health
@app.get("/healthz")
async def health():
    return {"ok": True}

# webhook verification (GET from Meta when registering webhook)
@app.get("/webhook")
async def webhook_verify(request: Request):
    params = dict(request.query_params)
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")
    if mode == "subscribe" and token == VERIFY_TOKEN:
        logger.info("Webhook verified successfully")
        return PlainTextResponse(challenge)
    logger.warning("Webhook verification failed")
    raise HTTPException(status_code=403, detail="Verification token mismatch")

# incoming messages (POST)
@app.post("/webhook")
async def webhook_inbound(payload: Dict[str, Any]):
    # Meta sends a complex envelope - follow their structure.
    # For each entry -> changes -> value -> messages
    try:
        entries = payload.get("entry", [])
        for entry in entries:
            for change in entry.get("changes", []):
                value = change.get("value", {})
                messages = value.get("messages", [])
                for msg in messages:
                    from_number = msg.get("from")  # sender phone
                    text = msg.get("text", {}).get("body", "").strip()
                    if not text:
                        # ignore non-text for now
                        continue

                    # rudimentary command parsing: "weather Mumbai" OR "Mumbai"
                    # keep it flexible for users
                    cmd = text
                    if text.lower().startswith("weather "):
                        cmd = text[len("weather "):].strip()

                    # call your get_weather tool (it's async)
                    # If get_weather lives in puch.py and is decorated as @mcp.tool(),
                    # it is still a normal function we can call directly.
                    result = await get_weather(cmd)  # expects dict {ok: True/False, ...}

                    # format reply
                    if result.get("ok"):
                        unit_sym = "°C" if result.get("units", "metric") == "metric" else "°F"
                        body = (
                            f"Weather for {result.get('city')}, {result.get('country')}\n"
                            f"Temp: {result.get('temp')}{unit_sym} (feels like {result.get('feels_like')}{unit_sym})\n"
                            f"Conditions: {result.get('conditions')}\n"
                            f"Humidity: {result.get('humidity')}%\n"
                        )
                    else:
                        body = f"Error: {result.get('detail', 'Could not fetch weather.')}"

                    # send reply through WhatsApp Cloud API
                    await send_whatsapp_text(to=from_number, text=body)
        return {"status": "processed"}
    except Exception as e:
        logger.exception("Error processing webhook")
        raise HTTPException(status_code=500, detail=str(e))

# helper to send message via Graph API
async def send_whatsapp_text(to: str, text: str):
    headers = {"Authorization": f"Bearer {WHATSAPP_TOKEN}", "Content-Type": "application/json"}
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"preview_url": False, "body": text}
    }
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(GRAPH_URL, headers=headers, json=payload)
        if resp.status_code not in (200, 201):
            logger.error("Failed to send message: %s %s", resp.status_code, resp.text)
        else:
            logger.info("Sent message to %s", to)
        return resp

# --- run MCP server in background thread so this single container can serve both endpoints ---
mcp = FastMCP("Puch.AI Weather Server")

def start_mcp_in_thread():
    def _run():
        try:
            mcp.run()  # blocking call to start MCP
        except Exception:
            logger.exception("MCP server crashed")
    t = threading.Thread(target=_run, daemon=True)
    t.start()

# start app (uvicorn) entrypoint
if __name__ == "__main__":
    import uvicorn
    logger.info("Starting combined WhatsApp adapter + MCP server")
    start_mcp_in_thread()
    uvicorn.run("whatsapp_adapter:app", host="0.0.0.0", port=PORT, log_level="info")
