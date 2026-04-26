#!/usr/bin/env node
/**
 * openclaw-proxy.mjs
 * Tiny HTTP proxy that exposes a simple REST API on top of the OpenClaw Gateway.
 *
 * POST /send   { "message": "...", "sessionKey": "..." (optional) }
 *   → { "reply": "...", "sessionKey": "..." }
 *
 * GET  /health → { "ok": true }
 *
 * Usage:  node openclaw-proxy.mjs [--port 18790]
 */

import http from 'node:http';
import { randomUUID } from 'node:crypto';
import { r as callGateway } from '/home/sage/.npm-global/lib/node_modules/openclaw/dist/call-BA3do6C0.js';

const PORT = parseInt(process.env.PROXY_PORT ?? '18790', 10);
const GATEWAY_URL = process.env.OPENCLAW_GATEWAY_URL ?? 'ws://localhost:18789';
const GATEWAY_TOKEN = process.env.OPENCLAW_GATEWAY_TOKEN ?? '27a132ac47f034dc0842ba08eb25f0ce62cdb70a86dcb865';
const POLL_INTERVAL_MS = 1500;
const POLL_MAX_MS = 60000;

async function rpc(method, params) {
  return callGateway({
    url: GATEWAY_URL,
    token: GATEWAY_TOKEN,
    method,
    params,
    expectFinal: false,
    timeoutMs: 15000,
  });
}

async function send(message, sessionKey) {
  // Create session if needed
  if (!sessionKey) {
    const created = await rpc('sessions.create', {});
    sessionKey = created.key;
  }

  const idempotencyKey = randomUUID();
  const sent = await rpc('sessions.send', { key: sessionKey, message, idempotencyKey });
  const runId = sent.runId;

  // Poll for assistant reply
  const deadline = Date.now() + POLL_MAX_MS;
  const seenIds = new Set();

  while (Date.now() < deadline) {
    await new Promise(r => setTimeout(r, POLL_INTERVAL_MS));
    const hist = await rpc('chat.history', { sessionKey, limit: 10 });
    for (const msg of hist.messages ?? []) {
      if (msg.role !== 'assistant') continue;
      const id = msg.__openclaw?.id ?? msg.id ?? '';
      if (seenIds.has(id)) continue;
      seenIds.add(id);
      const text = (msg.content ?? []).filter(c => c.type === 'text').map(c => c.text).join(' ').trim();
      if (text) return { reply: text, sessionKey, runId };
    }
  }

  return { reply: '', sessionKey, runId, timedOut: true };
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
      const result = await send(message, sessionKey ?? null);
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

server.listen(PORT, '0.0.0.0', () => {
  console.log(`OpenClaw proxy listening on http://0.0.0.0:${PORT}`);
});
