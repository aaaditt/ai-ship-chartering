"""
Intelligent Vessel Matching Algorithm

Scores vessels based on multiple factors:
- Distance to loading port (40% weight)
- Capacity match for cargo volume (25% weight)
- Vessel age / modernity (15% weight)
- Vetting / inspection status (10% weight)
- Availability status (10% weight)

Higher scores indicate better matches. Maximum score is 100.
"""

import math
from utils.route_utils import haversine, get_port_coords, estimate_voyage

# Scoring weights (must sum to 1.0)
WEIGHT_DISTANCE = 0.40
WEIGHT_CAPACITY = 0.25
WEIGHT_AGE = 0.15
WEIGHT_VETTING = 0.10
WEIGHT_AVAILABILITY = 0.10

# Vessel type capacity ranges (DWT)
VESSEL_TYPE_RANGES = {
    "VLCC": (200000, 320000),
    "Suezmax": (120000, 200000),
    "Aframax": (80000, 120000),
    "LR2": (80000, 120000),
    "LR1": (55000, 80000),
    "MR": (25000, 55000),
}

# Cargo-to-vessel-type compatibility
CARGO_VESSEL_COMPATIBILITY = {
    "Crude Oil": ["VLCC", "Suezmax", "Aframax"],
    "Gasoline": ["LR2", "LR1", "MR"],
    "Diesel": ["LR2", "LR1", "MR"],
    "Naphtha": ["LR2", "LR1", "MR"],
    "Jet Fuel": ["LR2", "LR1", "MR"],
    "Fuel Oil": ["Aframax", "Suezmax", "VLCC"],
    "Condensate": ["Suezmax", "Aframax", "LR2"],
    "LPG": ["LR1", "MR"],
    "Petrochemicals": ["MR", "LR1"],
    "Clean Products": ["LR2", "LR1", "MR"],
    "Bonny Light": ["Suezmax", "VLCC"],
    "North Sea Blend": ["Suezmax", "VLCC"],
}

CURRENT_YEAR = 2026


def score_distance(vessel: dict, origin_port: str) -> float:
    """
    Score vessel based on proximity to loading port.
    Closer vessels score higher. Max score = 100.
    Distance > 5000 NM scores 0.
    """
    origin_coords = get_port_coords(origin_port)
    if not origin_coords:
        return 50.0  # Default score if port not found

    distance = haversine(
        vessel['currentLat'], vessel['currentLon'],
        origin_coords[0], origin_coords[1]
    )

    # Score: 100 at 0 NM, 0 at 5000+ NM (linear decay)
    max_distance = 5000
    if distance >= max_distance:
        return 0.0
    return max(0, 100 * (1 - distance / max_distance))


def score_capacity(vessel: dict, cargo_volume_mt: float) -> float:
    """
    Score vessel based on capacity match.
    Ideal: cargo fills 75-95% of capacity.
    Penalty for too small (can't carry) or too large (inefficient).
    """
    dwt = vessel['dwt']

    if cargo_volume_mt > dwt:
        return 0.0  # Vessel too small

    utilization = cargo_volume_mt / dwt

    if 0.75 <= utilization <= 0.95:
        return 100.0  # Ideal range
    elif 0.60 <= utilization < 0.75:
        return 80.0
    elif 0.50 <= utilization < 0.60:
        return 60.0
    elif 0.30 <= utilization < 0.50:
        return 40.0
    elif utilization > 0.95:
        return 85.0  # Slightly over-utilized, but acceptable
    else:
        return 20.0  # Very underutilized


def score_age(vessel: dict) -> float:
    """
    Score vessel based on age.
    Newer vessels score higher due to better efficiency and compliance.
    """
    age = CURRENT_YEAR - vessel['built']

    if age <= 3:
        return 100.0
    elif age <= 5:
        return 90.0
    elif age <= 8:
        return 75.0
    elif age <= 10:
        return 60.0
    elif age <= 15:
        return 40.0
    else:
        return 20.0


def score_vetting(vessel: dict) -> float:
    """
    Score vessel based on vetting/inspection status.
    Approved = 100, Not approved = 20 (still usable but risky).
    """
    return 100.0 if vessel.get('vetted', False) else 20.0


def score_availability(vessel: dict) -> float:
    """
    Score vessel based on availability status.
    Available = 100, On Voyage = 40 (may become available), Under Maintenance = 10.
    """
    status = vessel.get('status', 'Unknown')
    if status == 'Available':
        return 100.0
    elif status == 'On Voyage':
        return 40.0
    elif status == 'Under Maintenance':
        return 10.0
    return 20.0


def check_cargo_compatibility(vessel_type: str, cargo_type: str) -> bool:
    """Check if vessel type is compatible with cargo type."""
    compatible_types = CARGO_VESSEL_COMPATIBILITY.get(cargo_type, [])
    if not compatible_types:
        return True  # If cargo type unknown, allow all
    return vessel_type in compatible_types


def match_vessels(vessels: list, cargo_type: str, cargo_volume: float,
                  origin_port: str, destination_port: str, top_n: int = 5) -> list:
    """
    Match and rank vessels for a chartering request.

    Args:
        vessels: List of vessel dictionaries
        cargo_type: Type of cargo (e.g., "Crude Oil", "Gasoline")
        cargo_volume: Volume in metric tons
        origin_port: Loading port name
        destination_port: Discharge port name
        top_n: Number of top results to return

    Returns:
        List of top-N vessel matches with scores and details
    """
    scored_vessels = []

    origin_coords = get_port_coords(origin_port)

    for vessel in vessels:
        # Check cargo compatibility
        compatible = check_cargo_compatibility(vessel['type'], cargo_type)

        # Calculate individual scores
        dist_score = score_distance(vessel, origin_port)
        cap_score = score_capacity(vessel, cargo_volume)
        age_score = score_age(vessel)
        vet_score = score_vetting(vessel)
        avail_score = score_availability(vessel)

        # Weighted total score
        total_score = (
            WEIGHT_DISTANCE * dist_score +
            WEIGHT_CAPACITY * cap_score +
            WEIGHT_AGE * age_score +
            WEIGHT_VETTING * vet_score +
            WEIGHT_AVAILABILITY * avail_score
        )

        # Apply compatibility penalty
        if not compatible:
            total_score *= 0.3  # Heavy penalty for incompatible vessels

        # Calculate distance to origin port
        distance_to_origin = 0
        if origin_coords:
            distance_to_origin = round(haversine(
                vessel['currentLat'], vessel['currentLon'],
                origin_coords[0], origin_coords[1]
            ))

        # Calculate ETA to origin (in days)
        eta_days = round(distance_to_origin / (vessel['speed'] * 24), 1) if vessel['speed'] > 0 else None

        # Calculate voyage estimate for the main route
        dest_coords = get_port_coords(destination_port)
        voyage_estimate = None
        if origin_coords and dest_coords:
            route_distance = haversine(origin_coords[0], origin_coords[1],
                                       dest_coords[0], dest_coords[1])
            # Apply sea-route factor (actual routes are ~1.3x Haversine)
            route_distance *= 1.3
            voyage_estimate = estimate_voyage(
                route_distance, vessel['speed'],
                vessel['fuelConsumption'], vessel['dailyRate']
            )
            if voyage_estimate and cargo_volume > 0:
                voyage_estimate['costPerMT'] = round(
                    voyage_estimate['totalCost'] / cargo_volume, 2
                )

        scored_vessels.append({
            "vessel": vessel,
            "totalScore": round(total_score, 1),
            "scores": {
                "distance": round(dist_score, 1),
                "capacity": round(cap_score, 1),
                "age": round(age_score, 1),
                "vetting": round(vet_score, 1),
                "availability": round(avail_score, 1)
            },
            "compatible": compatible,
            "distanceToOrigin": distance_to_origin,
            "etaDays": eta_days,
            "voyageEstimate": voyage_estimate
        })

    # Sort by total score (descending)
    scored_vessels.sort(key=lambda x: x['totalScore'], reverse=True)

    return scored_vessels[:top_n]
