"""
agents/core/browser_client.py
==============================
Async HTTP client for the agent-browser MCP (Model Context Protocol) server.

The agent-browser server exposes a JSON-RPC 2.0 interface over HTTP at the
URL configured in AGENT_BROWSER_MCP_URL (default: http://agent-browser:8765).

All methods are async and use httpx for non-blocking HTTP calls.

Protocol:
  POST /rpc
  Content-Type: application/json
  Body: { "jsonrpc": "2.0", "id": <int>, "method": "<name>", "params": {...} }

Usage:
    from agents.core.browser_client import BrowserClient

    async with BrowserClient() as browser:
        await browser.open_url("https://www.linkedin.com/jobs")
        await browser.load_state("linkedin")
        snapshot = await browser.snapshot()
        await browser.click("button[data-action='easy-apply']")
        screenshot_path = await browser.screenshot("/app/outputs/confirm.png")
        await browser.save_state("linkedin")
"""

from __future__ import annotations

import itertools
import os
from typing import Any, Optional

import httpx
from loguru import logger


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

AGENT_BROWSER_MCP_URL: str = os.environ.get(
    "AGENT_BROWSER_MCP_URL", "http://agent-browser:8765"
).rstrip("/")

# Default HTTP timeout in seconds (browser operations can be slow)
_HTTP_TIMEOUT: float = float(os.environ.get("BROWSER_CLIENT_TIMEOUT", "60"))

# JSON-RPC ID generator (monotonically increasing per process)
_id_counter = itertools.count(start=1)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _next_id() -> int:
    """Return the next unique JSON-RPC request ID."""
    return next(_id_counter)


def _rpc_payload(method: str, params: dict[str, Any]) -> dict[str, Any]:
    """Build a JSON-RPC 2.0 request body."""
    return {
        "jsonrpc": "2.0",
        "id": _next_id(),
        "method": method,
        "params": params,
    }


# ---------------------------------------------------------------------------
# BrowserClient
# ---------------------------------------------------------------------------

class BrowserClient:
    """
    Async client for the agent-browser MCP server.

    Can be used as an async context manager (recommended) or instantiated
    directly. Call `await client.close()` to release the HTTP connection pool
    when not using the context manager.

    Example (context manager):
        async with BrowserClient() as browser:
            await browser.open_url("https://linkedin.com")
            text = await browser.get_text("h1.job-title")

    Example (manual):
        browser = BrowserClient()
        await browser.open_url("https://linkedin.com")
        await browser.close()
    """

    def __init__(
        self,
        base_url: str = AGENT_BROWSER_MCP_URL,
        timeout: float = _HTTP_TIMEOUT,
    ) -> None:
        self._base_url = base_url
        self._timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def _get_client(self) -> httpx.AsyncClient:
        """Return (lazily create) the shared httpx async client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self._base_url,
                timeout=self._timeout,
                headers={"Content-Type": "application/json"},
            )
        return self._client

    async def close(self) -> None:
        """Close the underlying httpx client and release connections."""
        if self._client:
            await self._client.aclose()
            self._client = None
            logger.debug("BrowserClient connection closed.")

    async def __aenter__(self) -> "BrowserClient":
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()

    # ------------------------------------------------------------------
    # Core JSON-RPC dispatcher
    # ------------------------------------------------------------------

    async def _call(self, method: str, **params: Any) -> Any:
        """
        Send a JSON-RPC 2.0 request and return the `result` field.

        Raises:
            httpx.HTTPStatusError  on 4xx/5xx HTTP responses.
            RuntimeError           on JSON-RPC error responses.
        """
        client = await self._get_client()
        payload = _rpc_payload(method, params)

        logger.debug("BrowserClient → {} params={}", method, params)
        response = await client.post("/rpc", json=payload)
        response.raise_for_status()

        body = response.json()

        if "error" in body:
            error = body["error"]
            raise RuntimeError(
                f"MCP error [{error.get('code')}]: {error.get('message')} — {error.get('data', '')}"
            )

        result = body.get("result")
        logger.debug("BrowserClient ← {} result={}", method, str(result)[:120])
        return result

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------

    async def open_url(self, url: str, session: Optional[str] = None) -> dict[str, Any]:
        """
        Navigate to a URL in the managed browser.

        Args:
            url:     Full URL to navigate to.
            session: Optional named session to load before navigating
                     (restores cookies / localStorage for that portal).

        Returns:
            dict with keys: { "url": str, "title": str, "status": int }
        """
        params: dict[str, Any] = {"url": url}
        if session:
            params["session"] = session
        return await self._call("browser.navigate", **params)

    # ------------------------------------------------------------------
    # DOM inspection
    # ------------------------------------------------------------------

    async def snapshot(self) -> dict[str, Any]:
        """
        Return the current page's accessibility tree snapshot.

        The snapshot is a JSON representation of the ARIA tree, useful for
        the LLM to understand page structure without raw HTML.

        Returns:
            dict: accessibility tree node hierarchy.
        """
        return await self._call("browser.snapshot")

    async def get_text(self, selector: str) -> str:
        """
        Return the visible text content of the first element matching selector.

        Args:
            selector: CSS selector or ARIA role string.

        Returns:
            Trimmed text string, or "" if element not found.
        """
        result = await self._call("browser.getInnerText", selector=selector)
        return result.get("text", "") if isinstance(result, dict) else str(result)

    # ------------------------------------------------------------------
    # Interaction
    # ------------------------------------------------------------------

    async def click(self, selector: str) -> dict[str, Any]:
        """
        Click the first element matching selector.

        Args:
            selector: CSS selector or ARIA label.

        Returns:
            dict: { "clicked": bool, "selector": str }
        """
        return await self._call("browser.click", selector=selector)

    async def fill(self, selector: str, text: str) -> dict[str, Any]:
        """
        Clear and type text into an input element.

        Args:
            selector: CSS selector for the input/textarea.
            text:     Value to type.

        Returns:
            dict: { "filled": bool, "selector": str }
        """
        return await self._call("browser.fill", selector=selector, text=text)

    # ------------------------------------------------------------------
    # Screenshot
    # ------------------------------------------------------------------

    async def screenshot(self, path: Optional[str] = None) -> str:
        """
        Capture a screenshot of the current viewport.

        Args:
            path: Optional absolute path inside the container where the PNG
                  should be saved. If omitted, the server returns base64 data.

        Returns:
            Absolute path to the saved PNG, or base64-encoded PNG data string.
        """
        params: dict[str, Any] = {}
        if path:
            params["path"] = path
        result = await self._call("browser.screenshot", **params)
        if isinstance(result, dict):
            return result.get("path", result.get("data", ""))
        return str(result)

    # ------------------------------------------------------------------
    # Session management (Playwright storageState)
    # ------------------------------------------------------------------

    async def load_state(self, name: str) -> bool:
        """
        Load a saved browser state (cookies, localStorage, sessionStorage).

        State files are stored on the browser_sessions Docker volume.

        Args:
            name: Named session identifier (e.g. "linkedin", "computrabajo").

        Returns:
            True if state was loaded successfully, False if not found.
        """
        try:
            result = await self._call("browser.loadState", name=name)
            return bool(result.get("loaded", False)) if isinstance(result, dict) else bool(result)
        except RuntimeError as exc:
            logger.warning("load_state('{}') failed: {}", name, exc)
            return False

    async def save_state(self, name: str) -> bool:
        """
        Persist current browser state to a named slot on the sessions volume.

        Args:
            name: Named session identifier to save under.

        Returns:
            True if saved successfully.
        """
        result = await self._call("browser.saveState", name=name)
        return bool(result.get("saved", False)) if isinstance(result, dict) else bool(result)

    # ------------------------------------------------------------------
    # Batch execution
    # ------------------------------------------------------------------

    async def batch(self, commands: list[dict[str, Any]]) -> list[Any]:
        """
        Execute a list of MCP commands in sequence, returning a list of results.

        Each command is a dict with keys:
            { "method": str, "params": dict }

        This avoids multiple round-trips for simple multi-step operations.

        Args:
            commands: List of command dicts.

        Returns:
            List of results in the same order as commands.

        Example:
            results = await browser.batch([
                {"method": "browser.navigate", "params": {"url": "https://..."}},
                {"method": "browser.click", "params": {"selector": "#login"}},
                {"method": "browser.snapshot", "params": {}},
            ])
        """
        return await self._call("browser.batch", commands=commands)


# ---------------------------------------------------------------------------
# Module-level convenience singleton
# ---------------------------------------------------------------------------

# Agents can import this singleton directly for simpler usage.
# It is lazily connected on first use.
_default_client: Optional[BrowserClient] = None


def get_browser_client() -> BrowserClient:
    """
    Return the module-level BrowserClient singleton.

    Prefer using BrowserClient as an async context manager in production code
    to ensure proper connection cleanup.
    """
    global _default_client
    if _default_client is None:
        _default_client = BrowserClient()
    return _default_client
