"""
services/openclaw_api.py — OpenClaw agent API client.

Sends a text message to the configured OpenClaw session and returns
the agent's reply as a plain string.
"""

from __future__ import annotations

import logging

import httpx

from config import OpenClawConfig

logger = logging.getLogger(__name__)

_SEND_TIMEOUT_SECONDS = 60


class OpenClawService:
    """
    Thin HTTP client for the OpenClaw message API.

    Usage:
        svc = OpenClawService(openclaw_cfg)
        reply = svc.send(text)
    """

    def __init__(self, cfg: OpenClawConfig) -> None:
        self._cfg = cfg
        self._client = httpx.Client(
            base_url=cfg.base_url,
            headers={
                "Authorization": f"Bearer {cfg.api_token}",
                "Content-Type": "application/json",
            },
            timeout=_SEND_TIMEOUT_SECONDS,
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
        """
        payload = {
            "session": self._cfg.session,
            "message": text,
        }
        logger.info("Sending to OpenClaw: %s", text)

        response = self._client.post("/api/message", json=payload)
        response.raise_for_status()

        data = response.json()
        reply = data.get("reply") or data.get("message") or data.get("text") or ""
        logger.info("OpenClaw reply: %s", reply[:120])
        return reply

    def close(self) -> None:
        self._client.close()
        logger.debug("OpenClaw HTTP client closed.")
