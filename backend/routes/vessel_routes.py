"""
Vessel API Routes

Endpoints:
  GET  /api/vessels        - List all vessels in the fleet
  POST /api/vessels/match  - Match vessels to cargo requirements
"""

import json
import os
from flask import Blueprint, request, jsonify
from config import Config
from utils.matching import match_vessels

vessels_bp = Blueprint('vessels', __name__)

# Load vessel data
def load_vessels():
    path = os.path.join(Config.DATA_DIR, 'vessels.json')
    with open(path, 'r') as f:
        return json.load(f)


@vessels_bp.route('/api/vessels', methods=['GET'])
def get_vessels():
    """
    Return all vessels with optional filtering.

    Query params:
      - type: Filter by vessel type (e.g., VLCC, Suezmax)
      - status: Filter by status (Available, On Voyage, Under Maintenance)
      - vetted: Filter by vetting status (true/false)
    """
    vessels = load_vessels()

    # Apply filters
    vessel_type = request.args.get('type')
    status = request.args.get('status')
    vetted = request.args.get('vetted')

    if vessel_type:
        vessels = [v for v in vessels if v['type'].lower() == vessel_type.lower()]
    if status:
        vessels = [v for v in vessels if v['status'].lower() == status.lower()]
    if vetted is not None:
        vetted_bool = vetted.lower() == 'true'
        vessels = [v for v in vessels if v['vetted'] == vetted_bool]

    return jsonify({
        "success": True,
        "count": len(vessels),
        "vessels": vessels
    })


@vessels_bp.route('/api/vessels/match', methods=['POST'])
def match_vessels_endpoint():
    """
    Match vessels to cargo requirements using intelligent scoring algorithm.

    Request body (JSON):
    {
        "cargoType": "Gasoline",
        "cargoVolume": 90000,
        "originPort": "Jamnagar",
        "destinationPort": "Rotterdam",
        "topN": 5
    }
    """
    data = request.get_json()

    if not data:
        return jsonify({"success": False, "error": "Request body is required"}), 400

    # Validate required fields
    required = ['cargoType', 'cargoVolume', 'originPort', 'destinationPort']
    missing = [f for f in required if f not in data]
    if missing:
        return jsonify({
            "success": False,
            "error": f"Missing required fields: {', '.join(missing)}"
        }), 400

    cargo_type = data['cargoType']
    cargo_volume = float(data['cargoVolume'])
    origin_port = data['originPort']
    destination_port = data['destinationPort']
    top_n = int(data.get('topN', 5))

    if cargo_volume <= 0:
        return jsonify({"success": False, "error": "Cargo volume must be positive"}), 400

    vessels = load_vessels()

    results = match_vessels(
        vessels, cargo_type, cargo_volume,
        origin_port, destination_port, top_n
    )

    return jsonify({
        "success": True,
        "query": {
            "cargoType": cargo_type,
            "cargoVolume": cargo_volume,
            "originPort": origin_port,
            "destinationPort": destination_port
        },
        "matchCount": len(results),
        "matches": results
    })
