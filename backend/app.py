"""
AI-Powered Ship Chartering System - Backend API

A Flask-based REST API that provides intelligent vessel matching,
route optimization, AI-powered negotiation, and analytics for
the oil shipping / tanker chartering industry.

Research basis: AI integration reduces chartering time from 4-6 hours
to 30 minutes, cuts staffing by 70%, and improves success rates to 97%.

Author: Aadit
"""

import os
import json
from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
from config import Config

# Import route blueprints
from routes.vessel_routes import vessels_bp
from routes.route_routes import routes_bp
from routes.negotiate_routes import negotiate_bp
from routes.analytics_routes import analytics_bp


def create_app():
    """Application factory."""
    app = Flask(__name__)
    app.config.from_object(Config)

    # Enable CORS for frontend communication
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # Register blueprints
    app.register_blueprint(vessels_bp)
    app.register_blueprint(routes_bp)
    app.register_blueprint(negotiate_bp)
    app.register_blueprint(analytics_bp)

    # Health check endpoint
    @app.route('/api/health', methods=['GET'])
    def health():
        return jsonify({
            "status": "healthy",
            "service": "AI Ship Chartering API",
            "version": "1.0.0",
            "geminiConfigured": bool(Config.GEMINI_API_KEY)
        })

    # API documentation endpoint
    @app.route('/api', methods=['GET'])
    def api_docs():
        return jsonify({
            "service": "AI-Powered Ship Chartering System API",
            "version": "1.0.0",
            "endpoints": {
                "GET /api/health": "Health check",
                "GET /api/vessels": "List all vessels (filterable by type, status, vetted)",
                "POST /api/vessels/match": "Match vessels to cargo requirements",
                "GET /api/routes": "List predefined shipping routes",
                "POST /api/routes/optimize": "Find optimal route between ports",
                "POST /api/negotiate": "AI-powered charter negotiation",
                "GET /api/analytics": "Performance metrics and comparisons"
            }
        })

    # Error handlers
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"success": False, "error": "Endpoint not found"}), 404

    @app.errorhandler(500)
    def server_error(e):
        return jsonify({"success": False, "error": "Internal server error"}), 500

    return app


if __name__ == '__main__':
    app = create_app()
    port = Config.PORT
    print(f"""
    ╔══════════════════════════════════════════════════╗
    ║   AI Ship Chartering System - Backend API        ║
    ║   Running on http://localhost:{port}               ║
    ║   Gemini API: {'Configured ✓' if Config.GEMINI_API_KEY else 'Not configured ✗'}          ║
    ╚══════════════════════════════════════════════════╝
    """)
    app.run(host='0.0.0.0', port=port, debug=Config.DEBUG)
