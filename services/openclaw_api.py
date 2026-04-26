"""
services/openclaw_api.py — OpenClaw agent API client.

Sends messages to the openclaw-proxy.mjs HTTP server (port 18790 by default),
which handles the Gateway WebSocket JSON-RPC protocol internally.

POST /send   { "message": "...", "sessionKey": "..." (optional) }
  → { "reply": "...", "sessionKey": "..." }
"""

from __future__ import annotations

import logging

import httpx

from config import OpenClawConfig

logger = logging.getLogger(__name__)

_TIMEOUT_SECONDS = 90   # allow time for agent to think + poll


class OpenClawService:
    """
    HTTP client for the openclaw-proxy.mjs sidecar.

    The proxy runs on the same machine as the OpenClaw Gateway and handles
    all WebSocket/JSON-RPC details. The Python voice client just POSTs to it.

    Usage:
        svc = OpenClawService(cfg)
        reply = svc.send("What's the weather?")
        svc.close()
    """

    def __init__(self, cfg: OpenClawConfig) -> None:
        self._cfg = cfg
        self._session_key: str | None = None
        self._client = httpx.Client(
            base_url=cfg.base_url,
            headers={
                "Authorization": f"Bearer {cfg.api_token}",
                "Content-Type": "application/json",
            },
            timeout=_TIMEOUT_SECONDS,
        )

    def send(self, text: str) -> str:
        """
        Send a message to the agent and return the reply text.

        Args:
            text: The user's transcribed utterance.

        Returns:
            Agent reply as a plain string.

        Raises:
            httpx.HTTPStatusError: On non-2xx responses.
            RuntimeError: If the proxy returns an empty reply.
        """
        payload: dict = {"message": text}
        if self._session_key:
            payload["sessionKey"] = self._session_key

        logger.info("Sending to OpenClaw: %s", text)
        response = self._client.post("/send", json=payload)
        response.raise_for_status()

        data = response.json()

        # Cache the session key so subsequent turns have context
        if data.get("sessionKey"):
            self._session_key = data["sessionKey"]

        reply = data.get("reply", "")
        if reply:
            logger.info("OpenClaw reply: %s", reply[:120])
        else:
            logger.warning("Empty reply from OpenClaw (timedOut=%s)", data.get("timedOut"))
        return reply

    def close(self) -> None:
        self._client.close()
        logger.debug("OpenClaw HTTP client closed.")
