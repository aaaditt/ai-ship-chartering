"""
Route API Routes

Security additions:
  • POST payload validated + sanitized via validators.validate_route_optimize()
  • Internal port list not exposed in error messages (prevents enumeration)

Endpoints:
  GET  /api/routes          - List all predefined shipping routes
  POST /api/routes/optimize - Find optimal route between two ports
"""

import json
import os
import logging
from flask import Blueprint, request, jsonify
from config import Config
from utils.route_utils import (
    haversine, find_matching_route, get_port_coords,
    estimate_voyage, PORT_COORDINATES,
)
from validators import validate_route_optimize

logger = logging.getLogger("chartering.routes")

routes_bp = Blueprint("routes", __name__)


def load_routes():
    path = os.path.join(Config.DATA_DIR, "routes.json")
    with open(path, "r") as f:
        return json.load(f)


def load_vessels():
    path = os.path.join(Config.DATA_DIR, "vessels.json")
    with open(path, "r") as f:
        return json.load(f)


@routes_bp.route("/api/routes", methods=["GET"])
def get_routes():
    """Return all predefined shipping routes."""
    routes = load_routes()
    return jsonify({
        "success": True,
        "count": len(routes),
        "routes": routes,
    })


@routes_bp.route("/api/routes/optimize", methods=["POST"])
def optimize_route():
    """
    Find optimal route between two ports with cost estimates.

    Request body (JSON):
    {
        "originPort":      "Jamnagar",
        "destinationPort": "Rotterdam",
        "cargoVolume":     90000,
        "vesselType":      "LR2"       (optional)
    }

    Note: we deliberately don't return the full PORT_COORDINATES list
    in error messages — that would help attackers enumerate valid inputs.
    """
    raw = request.get_json(silent=True)
    if not raw:
        return jsonify({"success": False, "error": "JSON request body is required."}), 400

    # ── Validate and sanitise ─────────────────────────────────────────────────
    data, err = validate_route_optimize(raw)
    if err:
        return jsonify({"success": False, "error": err}), 400

    origin = data["originPort"]
    destination = data["destinationPort"]
    cargo_volume = data["cargoVolume"]
    vessel_type = data.get("vesselType")

    routes = load_routes()
    route = find_matching_route(origin, destination, routes)

    origin_coords = get_port_coords(origin)
    dest_coords = get_port_coords(destination)

    if not origin_coords or not dest_coords:
        # Don't reveal the full port list; just say the port wasn't found.
        return jsonify({
            "success": False,
            "error": "One or more ports not recognised. Check the port name spelling.",
        }), 400

    direct_distance = haversine(
        origin_coords[0], origin_coords[1],
        dest_coords[0], dest_coords[1],
    )

    response = {
        "success": True,
        "origin":      {"name": origin,      "lat": origin_coords[0], "lon": origin_coords[1]},
        "destination": {"name": destination, "lat": dest_coords[0],   "lon": dest_coords[1]},
        "directDistanceNM": round(direct_distance),
    }

    if route:
        response["predefinedRoute"] = True
        response["routeName"] = route.get("name", f"{origin} → {destination}")
        response["routeDistanceNM"] = route.get("distanceNM", round(direct_distance * 1.3))
        response["typicalDurationDays"] = route.get("typicalDurationDays")
        response["waypoints"] = route.get("waypoints", [])
        response["recommendedVesselTypes"] = route.get("recommendedVesselTypes", [])
        response["riskFactors"] = route.get("riskFactors", [])
        response["cargoTypes"] = route.get("cargoTypes", [])
        response["canalTransit"] = route.get("canalTransit")
    else:
        sea_distance = round(direct_distance * 1.3)
        response["predefinedRoute"] = False
        response["routeName"] = f"{origin} → {destination}"
        response["routeDistanceNM"] = sea_distance
        response["typicalDurationDays"] = round(sea_distance / (14 * 24), 1)
        response["waypoints"] = [
            {"name": origin,      "lat": origin_coords[0], "lon": origin_coords[1]},
            {"name": destination, "lat": dest_coords[0],   "lon": dest_coords[1]},
        ]
        response["recommendedVesselTypes"] = []
        response["riskFactors"] = []
        response["canalTransit"] = None

    # Cost estimates for recommended vessel types
    vessels = load_vessels()
    cost_estimates = []
    target_types = response.get("recommendedVesselTypes", [])
    if vessel_type:
        target_types = [vessel_type] + [t for t in target_types if t != vessel_type]

    for vtype in target_types[:3]:
        matching = [v for v in vessels if v["type"] == vtype and v["status"] == "Available"]
        if matching:
            sample = matching[0]
            estimate = estimate_voyage(
                response["routeDistanceNM"],
                sample["speed"],
                sample["fuelConsumption"],
                sample["dailyRate"],
            )
            if cargo_volume > 0:
                estimate["costPerMT"] = round(estimate["totalCost"] / cargo_volume, 2)
            cost_estimates.append({"vesselType": vtype, "estimate": estimate})

    response["costEstimates"] = cost_estimates
    response["availablePorts"] = list(PORT_COORDINATES.keys())

    return jsonify(response)
