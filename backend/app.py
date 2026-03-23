"""
AI-Powered Ship Chartering System - Backend API

A Flask-based REST API that provides intelligent vessel matching,
route optimization, AI-powered negotiation, and analytics for
the oil shipping / tanker chartering industry.

Security posture (production):
  • Rate limiting via flask-limiter (Redis or in-memory)
  • Security headers on every response
  • CORS locked to CORS_ORIGINS env var
  • No stack traces or internal paths in error responses
  • Request logging (IP / endpoint / status only — no payloads)
  • Server / X-Powered-By headers stripped

Author: Aadit
"""

import os
from flask import Flask, jsonify, request
from flask_cors import CORS
from config import Config

# Import security helpers (rate limiter, headers, logging)
from security import (
    create_limiter,
    apply_security_headers,
    log_request_start,
    log_request_end,
)

# Import route blueprints
from routes.vessel_routes import vessels_bp
from routes.route_routes import routes_bp
from routes.negotiate_routes import negotiate_bp
from routes.analytics_routes import analytics_bp


def create_app():
    """Application factory — create and configure the Flask app."""
    app = Flask(__name__)
    app.config.from_object(Config)

    # ── Production hardening: never surface Werkzeug debug UI ────────────────
    # We enforce DEBUG=False in production regardless of what an env var says,
    # using the RENDER environment variable as a reliable signal.
    if os.environ.get("RENDER"):
        app.config["DEBUG"] = False
        app.config["TESTING"] = False
        app.config["PROPAGATE_EXCEPTIONS"] = False

    # ── CORS lockdown ─────────────────────────────────────────────────────────
    # Only origins listed in CORS_ORIGINS are allowed.  In local dev the var
    # is unset so we fall back to "*" (the Vite proxy handles cross-origin
    # anyway, so the wildcard is only reachable from local curl/Postman).
    #
    # Production example (set in Render dashboard):
    #   CORS_ORIGINS=https://ai-ship-chartering.vercel.app
    #
    # Multiple origins: comma-separated
    #   CORS_ORIGINS=https://app.example.com,https://staging.example.com
    cors_origins_raw = os.environ.get("CORS_ORIGINS", "*")
    if cors_origins_raw == "*":
        origins_list = "*"
    else:
        origins_list = [o.strip() for o in cors_origins_raw.split(",") if o.strip()]

    CORS(
        app,
        resources={r"/api/*": {"origins": origins_list}},
        methods=["GET", "POST", "OPTIONS"],   # We never use PUT/DELETE/PATCH
        max_age=600,                           # Cache preflight for 10 min — reduces OPTIONS spam
        supports_credentials=False,            # No cookies/auth credentials cross-origin
    )

    # ── Rate limiter ──────────────────────────────────────────────────────────
    # Global limit: 100 req/min per IP (defined in security.py → create_limiter)
    # AI routes override this with a stricter 10 req/min (applied in the blueprints)
    limiter = create_limiter(app)
    limiter.init_app(app)

    # Expose the limiter on the app context so blueprints can import it
    app.extensions["limiter"] = limiter

    # ── Register blueprints ───────────────────────────────────────────────────
    app.register_blueprint(vessels_bp)
    app.register_blueprint(routes_bp)
    app.register_blueprint(negotiate_bp)
    app.register_blueprint(analytics_bp)

    # ── Security headers + request logging (after_request / before_request) ───
    app.before_request(log_request_start)
    app.after_request(apply_security_headers)
    app.after_request(log_request_end)

    # ── Health check ──────────────────────────────────────────────────────────
    @app.route("/api/health", methods=["GET"])
    def health():
        return jsonify({
            "status": "healthy",
            "service": "AI Ship Chartering API",
            "version": "1.0.0",
            # Show whether Gemini is wired up (useful for ops); never expose the key itself
            "geminiConfigured": bool(Config.GEMINI_API_KEY),
        })

    # ── Minimal API index ─────────────────────────────────────────────────────
    # We intentionally keep this terse: listing every route helps attackers
    # enumerate endpoints.  The health check above is enough for monitors.
    @app.route("/api", methods=["GET"])
    def api_index():
        return jsonify({
            "service": "AI Ship Chartering API",
            "version": "1.0.0",
            "status": "operational",
        })

    # ── Custom 429 handler ────────────────────────────────────────────────────
    # flask-limiter raises a 429 when a limit is breached.  We intercept it
    # and return a clean JSON body instead of the default HTML.
    @app.errorhandler(429)
    def rate_limit_exceeded(e):
        # e.description is the limit string e.g. "100 per 1 minute"
        retry_after = getattr(e, "retry_after", 60)
        return jsonify({
            "error": "Too many requests",
            "message": "You have exceeded the request limit. Please slow down.",
            "retry_after": retry_after,
        }), 429

    # ── Error handlers — no internal details exposed ───────────────────────────
    # In production Flask would normally show a Werkzeug HTML traceback.
    # These handlers return clean JSON so the frontend never sees file paths
    # or stack traces that would help an attacker map the codebase.
    @app.errorhandler(400)
    def bad_request(e):
        return jsonify({"success": False, "error": "Bad request"}), 400

    @app.errorhandler(404)
    def not_found(e):
        # Return "not found" without listing what routes exist
        return jsonify({"success": False, "error": "Endpoint not found"}), 404

    @app.errorhandler(405)
    def method_not_allowed(e):
        return jsonify({"success": False, "error": "Method not allowed"}), 405

    @app.errorhandler(500)
    def server_error(e):
        # Log the real error internally; never surface it to the client
        app.logger.error("Unhandled exception: %s", str(e))
        return jsonify({"success": False, "error": "Internal server error"}), 500

    # ── CORS enforcement: reject unknown origins with 403 ─────────────────────
    # Flask-CORS already handles this for /api/* routes.  This before_request
    # hook adds an extra layer for non-CORS requests that spoof the Origin header.
    if origins_list != "*":
        @app.before_request
        def enforce_origin():
            origin = request.headers.get("Origin")
            if origin and origin not in origins_list:
                return jsonify({
                    "success": False,
                    "error": "Origin not allowed",
                }), 403

    return app


if __name__ == "__main__":
    app = create_app()
    port = Config.PORT
    is_debug = Config.DEBUG and not os.environ.get("RENDER")

    print(f"""
    ╔══════════════════════════════════════════════════╗
    ║   AI Ship Chartering System - Backend API        ║
    ║   Running on http://localhost:{port:<19}║
    ║   Debug: {str(is_debug):<41}║
    ║   Gemini: {'Configured ✓' if Config.GEMINI_API_KEY else 'Not configured ✗':<40}║
    ╚══════════════════════════════════════════════════╝
    """)

    # debug=False is enforced if RENDER is set (above in create_app)
    app.run(host="0.0.0.0", port=port, debug=is_debug)
