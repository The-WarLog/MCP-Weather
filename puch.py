#!/usr/bin/env python3
"""
Puch.AI — Production-Grade Weather MCP Server

Goals achieved in this production refactor:
- Robust configuration via environment with clear validation.
- Structured (JSON-ish) logging with rotation for observability.
- Async HTTP client reused across calls with sensible connection limits.
- Retry + exponential backoff for transient failures (incl. 429 rate limit support).
- Input validation and explicit error handling with consistent return shapes.
- CLI and MCP server modes with graceful shutdown signal handling.
- Safe API-key handling and minimal logging of secrets.

Run examples:
  # set API key (PowerShell)
  $env:OPENWEATHER_API_KEY = "your_api_key_here"

  # Run as CLI test (fast verification)
  python puch.py --city "Mumbai"

  # Run as MCP server
  python puch.py --server

"""

from __future__ import annotations

import os
import sys
import re
import json
import time
import signal
import asyncio
import logging
from logging.handlers import RotatingFileHandler
from typing import Optional, Dict, Any

import httpx
from mcp.server.fastmcp import FastMCP

# ------------------------------
# Configuration & Validation
# ------------------------------
API_KEY = os.getenv("OPENWEATHER_API_KEY")
BASE_URL = os.getenv("OPENWEATHER_BASE_URL", "https://api.openweathermap.org/data/2.5/weather")
DEFAULT_UNITS = os.getenv("OPENWEATHER_UNITS", "metric")

# Minimal input limits
CITY_MAX_LEN = 80
CITY_RE = re.compile(r"^[A-Za-z0-9 \-.,']+$")

# ------------------------------
# Observability (Logging)
# ------------------------------
LOG_FILE = os.getenv("PUCH_LOG_FILE", "puch_weather.log")
LOG_LEVEL = os.getenv("PUCH_LOG_LEVEL", "INFO").upper()

logger = logging.getLogger("puch.weather")
logger.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))

# Console handler (human-readable)
console_handler = logging.StreamHandler()
console_fmt = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
console_handler.setFormatter(console_fmt)
logger.addHandler(console_handler)

# Rotating file handler (structured JSON-ish lines)
file_handler = RotatingFileHandler(LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=5)

class JsonLineFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": int(time.time()),
            "logger": record.name,
            "level": record.levelname,
            "msg": record.getMessage(),
        }
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        return json.dumps(payload)

file_handler.setFormatter(JsonLineFormatter())
logger.addHandler(file_handler)

# ------------------------------
# HTTP Client (async, reused)
# ------------------------------
# Use a module-level client to reuse connections and limits.
HTTP_CLIENT: Optional[httpx.AsyncClient] = None
HTTP_CLIENT_LOCK = asyncio.Lock()

DEFAULT_TIMEOUT = httpx.Timeout(10.0, connect=5.0)
DEFAULT_LIMITS = httpx.Limits(max_connections=50, max_keepalive_connections=20)

async def get_http_client() -> httpx.AsyncClient:
    global HTTP_CLIENT
    async with HTTP_CLIENT_LOCK:
        if HTTP_CLIENT is None:
            HTTP_CLIENT = httpx.AsyncClient(timeout=DEFAULT_TIMEOUT, limits=DEFAULT_LIMITS)
        return HTTP_CLIENT

# ------------------------------
# MCP Server
# ------------------------------
mcp = FastMCP("Puch.AI Weather Server")

# Retry/backoff parameters
MAX_RETRIES = 3
BACKOFF_BASE = 0.8  # seconds

async def _fetch_with_retries(params: Dict[str, Any]) -> httpx.Response:
    client = await get_http_client()
    last_exc: Optional[Exception] = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = await client.get(BASE_URL, params=params)

            # If rate-limited, attempt backoff and retry
            if resp.status_code == 429:
                wait = BACKOFF_BASE * (2 ** (attempt - 1))
                logger.warning(f"Rate limited (429). Backing off {wait}s and retrying (attempt {attempt}).")
                await asyncio.sleep(wait)
                continue

            return resp

        except (httpx.ReadTimeout, httpx.ConnectTimeout, httpx.NetworkError) as exc:
            last_exc = exc
            wait = BACKOFF_BASE * (2 ** (attempt - 1))
            logger.warning(f"Transient HTTP error on attempt {attempt}: {exc!r}. Backing off {wait}s.")
            await asyncio.sleep(wait)
            continue

    # all retries exhausted
    raise last_exc or RuntimeError("Unknown error during HTTP fetch")


def _mask_key(key: Optional[str]) -> str:
    if not key:
        return "<missing>"
    return "*" * max(0, len(key) - 4) + key[-4:]


def _validate_city(city: str) -> Optional[str]:
    if not isinstance(city, str):
        return "City must be a string."
    s = city.strip()
    if not s:
        return "City cannot be empty."
    if len(s) > CITY_MAX_LEN:
        return f"City too long (max {CITY_MAX_LEN} chars)."
    if not CITY_RE.match(s):
        return "City contains invalid characters."
    return None


@mcp.tool()
async def get_weather(city: str, units: str = DEFAULT_UNITS) -> Dict[str, Any]:
    """MCP tool: returns a structured JSON-like dict with weather or an error."""
    logger.info("get_weather called", extra={"city": city, "units": units})

    if not API_KEY:
        logger.critical("Missing OPENWEATHER_API_KEY; aborting request.")
        return {"ok": False, "error": "server_configuration", "detail": "Missing API key"}

    # validate inputs
    v_err = _validate_city(city)
    if v_err:
        logger.warning("Invalid input for get_weather", extra={"city": city, "error": v_err})
        return {"ok": False, "error": "invalid_input", "detail": v_err}

    units = units if units in ("metric", "imperial") else DEFAULT_UNITS

    params = {"q": city.strip(), "appid": API_KEY, "units": units}

    try:
        resp = await _fetch_with_retries(params)

        if resp.status_code == 200:
            data = resp.json()
            main = data.get("main", {})
            weather_arr = data.get("weather", [])
            first = weather_arr[0] if weather_arr else {}

            result = {
                "ok": True,
                "city": data.get("name"),
                "country": data.get("sys", {}).get("country"),
                "temp": main.get("temp"),
                "feels_like": main.get("feels_like"),
                "humidity": main.get("humidity"),
                "wind_speed": data.get("wind", {}).get("speed"),
                "conditions": first.get("description"),
                "units": units,
            }

            logger.info("Weather fetch successful", extra={"city": result["city"], "units": units})
            return result

        if resp.status_code == 401:
            logger.error("Auth error from OpenWeatherMap. Check API key.")
            return {"ok": False, "error": "auth", "detail": "Authentication failed with upstream"}

        if resp.status_code == 404:
            logger.warning("City not found", extra={"q": city})
            return {"ok": False, "error": "not_found", "detail": f"No weather data for {city.strip()}"}

        # Other unexpected status
        logger.error("Upstream error", extra={"status": resp.status_code, "text": resp.text})
        return {"ok": False, "error": "upstream", "detail": f"Status {resp.status_code}"}

    except Exception as exc:
        logger.critical("Unhandled exception in get_weather", exc_info=True)
        return {"ok": False, "error": "internal", "detail": str(exc)}


# ------------------------------
# CLI + Server Entrypoint + Graceful Shutdown
# ------------------------------

async def _cli_print(city: str, units: str) -> None:
    out = await get_weather(city, units)
    if out.get("ok"):
        # formatted human-friendly output for CLI
        unit_symbol = "°C" if out.get("units") == "metric" else "°F"
        print(f"Weather for {out.get('city')}, {out.get('country')}:"
              f"  Temp: {out.get('temp')}{unit_symbol} (feels like {out.get('feels_like')}{unit_symbol})"
              f"  Conditions: {out.get('conditions')}"
              f"  Humidity: {out.get('humidity')}%"
              f"  Wind: {out.get('wind_speed')} m/s")
    else:
        print(json.dumps(out, indent=2))


def _setup_signal_handlers(loop: asyncio.AbstractEventLoop):
    stop = asyncio.Event()

    def _on_signal(signame):
        logger.info(f"Received signal {signame}; initiating graceful shutdown.")
        stop.set()

    for s in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(s, lambda s=s: _on_signal(s.name))

    return stop


def main(argv: Optional[list[str]] = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(prog="puch.py", description="Puch.AI Weather — MCP server and CLI")
    parser.add_argument("--server", action="store_true", help="Run as MCP server")
    parser.add_argument("--city", type=str, help="Run one-off CLI weather lookup")
    parser.add_argument("--units", type=str, choices=("metric", "imperial"), default=DEFAULT_UNITS)
    args = parser.parse_args(argv)

    if not API_KEY:
        logger.critical("FATAL: OPENWEATHER_API_KEY not configured. Set env var OPENWEATHER_API_KEY before starting.")
        logger.critical(f"Example (PowerShell): $env:OPENWEATHER_API_KEY = 'your_key_here'")
        return 2

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    if args.server:
        logger.info("Starting MCP server mode. API key: %s", _mask_key(API_KEY))
        # start the MCP server in the event loop and handle graceful shutdown
        stop_event = _setup_signal_handlers(loop)

        # run mcp in a background task — FastMCP.run is blocking, so we launch it in a thread
        def _run_mcp():
            try:
                mcp.run()
            except Exception:
                logger.exception("MCP server crashed")

        import threading
        t = threading.Thread(target=_run_mcp, daemon=True)
        t.start()

        try:
            loop.run_until_complete(stop_event.wait())
            logger.info("Shutdown event received; cleaning up HTTP client.")
            # close http client
            if HTTP_CLIENT is not None:
                loop.run_until_complete(HTTP_CLIENT.aclose())
        finally:
            logger.info("Server shutdown complete.")
        return 0

    elif args.city:
        logger.info("Running one-off CLI request for city: %s", args.city)
        loop.run_until_complete(_cli_print(args.city, args.units))
        return 0

    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())
