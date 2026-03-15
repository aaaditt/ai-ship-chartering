"""
Haversine distance calculation and route optimization utilities.

Used to calculate great-circle distance between ports and estimate
voyage durations, fuel costs, and optimal routes.
"""

import math
import json
import os


def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great-circle distance between two points on Earth
    using the Haversine formula.

    Args:
        lat1, lon1: Latitude and longitude of point 1 (degrees)
        lat2, lon2: Latitude and longitude of point 2 (degrees)

    Returns:
        Distance in nautical miles
    """
    R_NM = 3440.065  # Earth's radius in nautical miles

    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    c = 2 * math.asin(math.sqrt(a))

    return R_NM * c


def estimate_voyage(distance_nm: float, speed_knots: float, fuel_consumption: float, daily_rate: float):
    """
    Estimate voyage duration and costs.

    Args:
        distance_nm: Distance in nautical miles
        speed_knots: Vessel speed in knots
        fuel_consumption: Daily fuel consumption in metric tons
        daily_rate: Daily charter rate in USD

    Returns:
        Dictionary with duration (days), fuel cost, charter cost, total cost
    """
    if speed_knots <= 0:
        return {"error": "Speed must be positive"}

    hours = distance_nm / speed_knots
    days = hours / 24

    # Bunker fuel price per metric ton (current market estimate)
    bunker_price = 620  # USD per MT
    fuel_cost = days * fuel_consumption * bunker_price
    charter_cost = days * daily_rate
    port_charges = 50000  # Estimated port charges for origin + destination
    insurance = charter_cost * 0.015  # 1.5% of charter cost

    total_cost = fuel_cost + charter_cost + port_charges + insurance

    return {
        "durationDays": round(days, 1),
        "durationHours": round(hours, 1),
        "fuelCost": round(fuel_cost),
        "charterCost": round(charter_cost),
        "portCharges": port_charges,
        "insurance": round(insurance),
        "totalCost": round(total_cost),
        "costPerMT": None  # Filled in later when cargo volume is known
    }


def find_matching_route(origin: str, destination: str, routes_data: list) -> dict:
    """
    Find a predefined route matching the origin and destination.
    Falls back to direct Haversine calculation if no route found.

    Args:
        origin: Origin port name
        destination: Destination port name
        routes_data: List of predefined routes

    Returns:
        Route dictionary or generated route
    """
    origin_lower = origin.lower().strip()
    dest_lower = destination.lower().strip()

    for route in routes_data:
        if (route['origin'].lower() == origin_lower and
                route['destination'].lower() == dest_lower):
            return route

    # Reverse route check
    for route in routes_data:
        if (route['origin'].lower() == dest_lower and
                route['destination'].lower() == origin_lower):
            reverse = route.copy()
            reverse['origin'], reverse['destination'] = route['destination'], route['origin']
            reverse['originLat'], reverse['destLat'] = route['destLat'], route['originLat']
            reverse['originLon'], reverse['destLon'] = route['destLon'], route['originLon']
            reverse['waypoints'] = list(reversed(route['waypoints']))
            reverse['name'] = f"{reverse['origin']} → {reverse['destination']}"
            return reverse

    return None


# Port coordinates lookup for Haversine calculation when no predefined route exists
PORT_COORDINATES = {
    "jamnagar": (22.457, 70.067),
    "rotterdam": (51.922, 4.479),
    "ras tanura": (26.635, 50.155),
    "fujairah": (25.112, 56.336),
    "singapore": (1.264, 103.820),
    "bonny terminal": (4.427, 7.152),
    "houston": (29.748, -95.273),
    "mumbai": (18.948, 72.844),
    "piraeus": (37.943, 23.647),
    "novorossiysk": (44.723, 37.768),
    "qingdao": (36.067, 120.322),
    "durban": (-29.871, 31.015),
    "ain sukhna": (29.616, 32.334),
    "port klang": (2.998, 101.392),
    "mongstad": (60.810, 5.028),
    "mangalore": (12.866, 74.831),
    "jebel ali": (25.005, 55.064),
    "yanbu": (24.089, 38.063),
    "sikka": (22.420, 69.840),
    "vadinar": (22.383, 69.717),
}


def get_port_coords(port_name: str):
    """Look up coordinates for a port name."""
    return PORT_COORDINATES.get(port_name.lower().strip())
