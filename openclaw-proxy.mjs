#!/usr/bin/env node
/**
 * openclaw-proxy.mjs
 * Thin HTTP proxy in front of the OpenClaw Gateway's OpenAI-compatible endpoint.
 *
 * POST /send   { "message": "...", "sessionKey": "..." (optional) }
 *   → { "reply": "...", "sessionKey": "..." }
 *
 * GET  /health → { "ok": true }
 *
 * Required env:
 *   OPENCLAW_GATEWAY_TOKEN   Gateway bearer token
 *
 * Optional env:
 *   OPENCLAW_GATEWAY_URL     Base URL of gateway (default: http://localhost:18789)
 *   PROXY_PORT               Port this proxy listens on (default: 18790)
 */

import http from 'node:http';

const PORT = parseInt(process.env.PROXY_PORT ?? '18790', 10);
const GATEWAY_URL = (process.env.OPENCLAW_GATEWAY_URL ?? 'http://localhost:18789').replace(/\/$/, '');
const GATEWAY_TOKEN = process.env.OPENCLAW_GATEWAY_TOKEN;

if (!GATEWAY_TOKEN) {
  console.error('ERROR: OPENCLAW_GATEWAY_TOKEN env variable is required.');
  process.exit(1);
}

const HEADERS = {
  'Authorization': `Bearer ${GATEWAY_TOKEN}`,
  'Content-Type': 'application/json',
};

async function sendMessage(message, sessionKey) {
  const messages = [];
  if (sessionKey) {
    // Pass session key via header so the gateway routes to the right session
  }

  const body = JSON.stringify({
    model: 'openclaw',
    messages: [{ role: 'user', content: message }],
    stream: false,
  });

  const extraHeaders = sessionKey
    ? { ...HEADERS, 'x-openclaw-session-key': sessionKey }
    : HEADERS;

  const res = await fetch(`${GATEWAY_URL}/v1/chat/completions`, {
    method: 'POST',
    headers: extraHeaders,
    body,
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Gateway returned ${res.status}: ${text}`);
  }

  const data = await res.json();
  const reply = data.choices?.[0]?.message?.content ?? '';
  const newSessionKey = res.headers.get('x-openclaw-session-key') ?? sessionKey ?? '';

  return { reply, sessionKey: newSessionKey };
}

const server = http.createServer(async (req, res) => {
  res.setHeader('Content-Type', 'application/json');

  if (req.method === 'GET' && req.url === '/health') {
    res.end(JSON.stringify({ ok: true }));
    return;
  }

  if (req.method === 'POST' && req.url === '/send') {
    let body = '';
    req.on('data', d => body += d);
    await new Promise(r => req.on('end', r));

    let payload;
    try { payload = JSON.parse(body); } catch {
      res.statusCode = 400;
      res.end(JSON.stringify({ error: 'invalid JSON' }));
      return;
    }

    const { message, sessionKey } = payload;
    if (!message || typeof message !== 'string') {
      res.statusCode = 400;
      res.end(JSON.stringify({ error: 'message is required' }));
      return;
    }

    try {
      const result = await sendMessage(message, sessionKey ?? null);
      res.end(JSON.stringify(result));
    } catch (err) {
      console.error('send error:', err.message);
      res.statusCode = 500;
      res.end(JSON.stringify({ error: err.message }));
    }
    return;
  }

  res.statusCode = 404;
  res.end(JSON.stringify({ error: 'not found' }));
});

server.listen(PORT, '127.0.0.1', () => {
  console.log(`OpenClaw proxy listening on http://127.0.0.1:${PORT}`);
});
