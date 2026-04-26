"""
services/openclaw_api.py — OpenClaw agent API client.

Connects to the OpenClaw Gateway via WebSocket (JSON-RPC) and sends
a text message, waiting for the agent's final reply.
"""

from __future__ import annotations

import json
import logging
import uuid

import websocket

from config import OpenClawConfig

logger = logging.getLogger(__name__)

_RECV_TIMEOUT_SECONDS = 60


class OpenClawService:
    """
    WebSocket JSON-RPC client for the OpenClaw Gateway.

    Protocol:
        1. Connect to ws://<host>:<port>
        2. Send auth token as first message
        3. Send JSON-RPC request with method "chat.send"
        4. Read responses until a message with role "assistant" and
           finished=True (or equivalent) arrives

    Usage:
        svc = OpenClawService(openclaw_cfg)
        reply = svc.send("What's the weather?")
        svc.close()
    """

    def __init__(self, cfg: OpenClawConfig) -> None:
        self._cfg = cfg
        self._ws: websocket.WebSocket | None = None

    def _connect(self) -> websocket.WebSocket:
        url = self._cfg.base_url
        # Support both http(s):// and ws(s):// base URLs
        if url.startswith("http://"):
            url = "ws://" + url[7:]
        elif url.startswith("https://"):
            url = "wss://" + url[8:]

        logger.debug("Connecting to OpenClaw Gateway: %s", url)
        ws = websocket.create_connection(url, timeout=_RECV_TIMEOUT_SECONDS)

        # Step 1: authenticate
        ws.send(json.dumps({"token": self._cfg.api_token}))
        auth_response = ws.recv()
        logger.debug("Auth response: %s", auth_response)

        return ws

    def send(self, text: str) -> str:
        """
        Send a message to the agent and return the reply text.

        Args:
            text: The user's transcribed utterance.

        Returns:
            Agent reply as a plain string.

        Raises:
            RuntimeError: On protocol errors or empty replies.
        """
        ws = self._connect()
        try:
            request_id = str(uuid.uuid4())
            payload = {
                "id": request_id,
                "method": "chat.send",
                "params": {
                    "message": text,
                    "agentId": self._cfg.session,
                },
            }
            logger.info("Sending to OpenClaw: %s", text)
            ws.send(json.dumps(payload))

            # Read responses until we get the final assistant message
            reply = ""
            while True:
                raw = ws.recv()
                if not raw:
                    break

                try:
                    msg = json.loads(raw)
                except json.JSONDecodeError:
                    logger.warning("Non-JSON response: %s", raw[:200])
                    continue

                logger.debug("Gateway msg: %s", str(msg)[:300])

                # Handle JSON-RPC error
                if "error" in msg:
                    raise RuntimeError(f"OpenClaw error: {msg['error']}")

                # Extract reply text from various response shapes
                result = msg.get("result") or msg.get("params") or msg
                content = (
                    result.get("reply")
                    or result.get("message")
                    or result.get("text")
                    or result.get("content")
                    or ""
                )

                if content:
                    reply = content

                # Check if this is the final message
                finished = (
                    result.get("finished")
                    or result.get("done")
                    or result.get("final")
                    or msg.get("id") == request_id
                )
                if finished:
                    break

            logger.info("OpenClaw reply: %s", reply[:120])
            return reply

        finally:
            ws.close()

    def close(self) -> None:
        if self._ws:
            self._ws.close()
            self._ws = None
        logger.debug("OpenClaw WebSocket client closed.")
