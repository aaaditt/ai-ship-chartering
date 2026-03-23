"""
security.py — Production-grade security middleware for the Flask backend.

Covers:
  1. Rate limiting  (flask-limiter, Redis-backed in prod / in-memory in dev)
  2. Security headers  (manual, no extra dep needed)
  3. Request logging  (IP · endpoint · status code — no payload data)
  4. Error hardening  (strip stack traces, remove Server/X-Powered-By headers)
  5. CORS lockdown    (handled via flask-cors config in app.py; OPTIONS throttle here)
"""

import logging
import os
import time
from flask import request, g
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# ─── Logging setup ────────────────────────────────────────────────────────────
# We log to stdout (captured by Render/Gunicorn) and never log request bodies
# or headers that could contain secrets.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger("chartering.security")


# ─── Rate-limiter factory ──────────────────────────────────────────────────────
def create_limiter(app):
    """
    Build and return a flask-limiter instance.

    Storage strategy:
      • If REDIS_URL is set we use Redis — rate limits survive app restarts
        and are shared across all Gunicorn workers.
      • Otherwise we fall back to in-memory storage (fine for local dev,
        workers don't share counters but that's acceptable).

    Key function: get_remote_address() uses the real client IP.
    On Render this works automatically; if you're behind a custom proxy that
    sets X-Forwarded-For, also add ProxyFix middleware (see app.py comment).
    """
    redis_url = os.environ.get("REDIS_URL")

    if redis_url:
        # Redis backend — shared across Gunicorn workers
        storage_uri = redis_url
        logger.info("Rate limiter: using Redis storage at %s", redis_url.split("@")[-1])
    else:
        # In-memory — development only; not shared across workers
        storage_uri = "memory://"
        logger.info("Rate limiter: using in-memory storage (dev mode)")

    limiter = Limiter(
        key_func=get_remote_address,
        # Global default: 100 requests per minute per IP.
        # Applied to every route unless overridden with @limiter.limit(...)
        default_limits=["100 per minute"],
        storage_uri=storage_uri,
        # Return a clean JSON 429 instead of the default HTML page.
        # The on_breach handler in app.py formats the actual response.
        headers_enabled=True,      # Adds X-RateLimit-* headers so the client knows its quota
        swallow_errors=True,       # If Redis is momentarily down, don't crash the request
    )

    return limiter


# ─── Security headers ──────────────────────────────────────────────────────────
# We add headers manually (no flask-talisman dep) so we have full control.
# Called from app.after_request in app.py.

def apply_security_headers(response):
    """
    Attach security headers to every outgoing response.

    Why each header exists:
      X-Content-Type-Options   — Prevents browsers from MIME-sniffing a response away
                                 from the declared Content-Type (stops script injection
                                 via polyglot uploads).
      X-Frame-Options          — Blocks our API from being embedded in <iframe>, preventing
                                 clickjacking attacks.
      X-XSS-Protection         — Legacy IE/Chrome XSS auditor; harmless on modern browsers
                                 but still good practice.
      Referrer-Policy          — Limits how much referrer info is sent so we don't leak
                                 internal paths/query strings to third parties.
      Content-Security-Policy  — Only allows content from our own origin. For a pure
                                 JSON API this is belt-and-suspenders safety.
      Permissions-Policy       — Explicitly disables browser features we never use.
      Cache-Control            — Prevents caching of API responses that may contain
                                 session-specific data.
    """
    h = response.headers

    h["X-Content-Type-Options"] = "nosniff"
    h["X-Frame-Options"] = "DENY"
    h["X-XSS-Protection"] = "1; mode=block"
    h["Referrer-Policy"] = "strict-origin-when-cross-origin"
    h["Content-Security-Policy"] = "default-src 'self'"
    h["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    h["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"

    # Force HTTPS in production via HSTS.
    # We only add this when we know we're running behind HTTPS (Render/Vercel
    # always terminate TLS) so local dev over plain HTTP isn't broken.
    is_production = os.environ.get("FLASK_ENV") == "production" or os.environ.get("RENDER")
    if is_production:
        # 1-year max-age, include subdomains
        h["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

    # ── Strip headers that reveal our tech stack ───────────────────────────────
    # Werkzeug sets "Server: Werkzeug/x.y.z Python/x.y.z" by default;
    # an attacker can fingerprint the exact version and look for known CVEs.
    h.pop("Server", None)
    h.pop("X-Powered-By", None)   # Not set by Flask by default, but just in case

    return response


# ─── Request logging ───────────────────────────────────────────────────────────
# We log: timestamp (via log format), client IP, HTTP method, path, status code.
# We deliberately DO NOT log: request body, query params, Authorization headers.
# This is the minimum needed for incident investigation without risking data leaks.

def log_request_start():
    """Store the start time so we can compute latency in log_request_end."""
    g.start_time = time.monotonic()


def log_request_end(response):
    """Log a single structured line per request — safe for production."""
    duration_ms = round((time.monotonic() - g.get("start_time", time.monotonic())) * 1000)
    ip = get_remote_address()

    # Omit query strings from the logged path to avoid leaking filter values.
    path = request.path

    logger.info(
        "%s %s %s | %d | %dms",
        ip,
        request.method,
        path,
        response.status_code,
        duration_ms,
    )
    return response
