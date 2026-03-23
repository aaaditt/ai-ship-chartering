"""
Vessel API Routes

Security additions:
  • All POST payloads run through validators.validate_vessel_match()
  • String inputs are sanitized before being passed to business logic
  • Type errors on numeric fields return descriptive 400s

Endpoints:
  GET  /api/vessels        - List all vessels in the fleet
  POST /api/vessels/match  - Match vessels to cargo requirements
"""

import json
import os
import logging
from flask import Blueprint, request, jsonify
from config import Config
from utils.matching import match_vessels
from validators import validate_vessel_match

logger = logging.getLogger("chartering.vessels")

vessels_bp = Blueprint("vessels", __name__)

ALLOWED_VESSEL_TYPES = {"VLCC", "Suezmax", "Aframax", "LR2", "LR1", "MR", "Panamax"}
ALLOWED_STATUSES = {"Available", "On Voyage", "Under Maintenance"}


def load_vessels():
    path = os.path.join(Config.DATA_DIR, "vessels.json")
    with open(path, "r") as f:
        return json.load(f)


@vessels_bp.route("/api/vessels", methods=["GET"])
def get_vessels():
    """
    Return all vessels with optional filtering.

    Query params:
      - type:   Filter by vessel type (VLCC, Suezmax, …)
      - status: Filter by status (Available, On Voyage, …)
      - vetted: Filter by vetting status (true / false)

    We whitelist the type and status values so we don't leak the full
    schema when an unexpected value is passed.
    """
    vessels = load_vessels()

    vessel_type = request.args.get("type", "").strip()
    status = request.args.get("status", "").strip()
    vetted = request.args.get("vetted", "").strip()

    # Whitelist check: reject unknown enum values rather than returning nothing silently
    if vessel_type and vessel_type not in ALLOWED_VESSEL_TYPES:
        return jsonify({
            "success": False,
            "error": f"Unknown vessel type. Allowed: {', '.join(sorted(ALLOWED_VESSEL_TYPES))}",
        }), 400

    if status and status not in ALLOWED_STATUSES:
        return jsonify({
            "success": False,
            "error": f"Unknown status. Allowed: {', '.join(sorted(ALLOWED_STATUSES))}",
        }), 400

    if vessel_type:
        vessels = [v for v in vessels if v["type"].lower() == vessel_type.lower()]
    if status:
        vessels = [v for v in vessels if v["status"].lower() == status.lower()]
    if vetted:
        vetted_bool = vetted.lower() == "true"
        vessels = [v for v in vessels if v["vetted"] == vetted_bool]

    return jsonify({
        "success": True,
        "count": len(vessels),
        "vessels": vessels,
    })


@vessels_bp.route("/api/vessels/match", methods=["POST"])
def match_vessels_endpoint():
    """
    Match vessels to cargo requirements using intelligent scoring algorithm.

    Request body (JSON):
    {
        "cargoType":        "Gasoline",
        "cargoVolume":      90000,
        "originPort":       "Jamnagar",
        "destinationPort":  "Rotterdam",
        "topN":             5           (optional, 1-20)
    }
    """
    raw = request.get_json(silent=True)
    if not raw:
        return jsonify({"success": False, "error": "JSON request body is required."}), 400

    # ── Validate and sanitise ─────────────────────────────────────────────────
    data, err = validate_vessel_match(raw)
    if err:
        return jsonify({"success": False, "error": err}), 400

    vessels = load_vessels()
    results = match_vessels(
        vessels,
        data["cargoType"],
        data["cargoVolume"],
        data["originPort"],
        data["destinationPort"],
        data["topN"],
    )

    return jsonify({
        "success": True,
        "query": {
            "cargoType":       data["cargoType"],
            "cargoVolume":     data["cargoVolume"],
            "originPort":      data["originPort"],
            "destinationPort": data["destinationPort"],
        },
        "matchCount": len(results),
        "matches": results,
    })
