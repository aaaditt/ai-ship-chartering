"""
validators.py — Input validation and sanitization helpers.

All POST endpoints pass their JSON payloads through these helpers before
any business logic runs. This gives us a single, auditable place for:

  • Required-field checks  → 400 with a descriptive error list
  • Type / range checks    → 400 with a human-readable message
  • HTML/script stripping  → protects Gemini prompts from prompt-injection
  • Max-length limits      → cap strings before they hit the AI model
"""

import re
import html
from typing import Any


# ─── Max-length constants ──────────────────────────────────────────────────────
# Adjust these if you add new large-text fields down the line.
MAX_NEGOTIATE_MSG  = 2_000   # Characters — negotiation free-text message
MAX_PORT_NAME      = 100     # Port names are short; reject suspiciously long ones
MAX_CARGO_TYPE     = 100     # e.g. "Gasoline", "Crude Oil"
MAX_VESSEL_TYPE    = 50      # e.g. "VLCC", "Suezmax"
MAX_GENERIC_STRING = 500     # Fallback for any string field not listed above


# ─── Sanitisation ─────────────────────────────────────────────────────────────

# Matches any HTML/XML tag: <script>, </div>, <!-- comments -->, etc.
_HTML_TAG_RE = re.compile(r"<[^>]+>", re.IGNORECASE)

# Matches javascript: URI scheme (usable in attribute values even without tags)
_JS_URI_RE = re.compile(r"javascript\s*:", re.IGNORECASE)

# Match common SQL injection starters for a basic sanity check on port names etc.
# We don't rely on this for real SQL protection (we have no SQL), but it's extra noise filtering.
_SQL_RE = re.compile(
    r"(--|;|'|\"|\bOR\b|\bAND\b|\bDROP\b|\bSELECT\b|\bINSERT\b|\bUNION\b)",
    re.IGNORECASE,
)


def sanitize_string(value: str, max_length: int = MAX_GENERIC_STRING) -> str:
    """
    Clean a user-supplied string before it enters business logic / AI prompts.

    Steps:
      1. Strip leading/trailing whitespace.
      2. HTML-escape special characters (&, <, >, ", ') — this neutralises
         any tags that slip past the regex.
      3. Remove residual HTML/XML tags.
      4. Remove 'javascript:' URI schemes.
      5. Truncate to max_length (defence-in-depth against the length check
         above in case someone calls this directly).
    """
    if not isinstance(value, str):
        return str(value)[:max_length]

    value = value.strip()
    value = html.escape(value, quote=True)   # &lt; &gt; &#x27;  etc.
    value = _HTML_TAG_RE.sub("", value)      # remove any tag-shaped leftovers
    value = _JS_URI_RE.sub("", value)        # remove javascript: URIs
    return value[:max_length]


# ─── Validate /api/negotiate ──────────────────────────────────────────────────

def validate_negotiate(data: dict) -> tuple[dict | None, str | None]:
    """
    Validate and sanitize the payload for POST /api/negotiate.

    Returns:
      (cleaned_data, None)       on success
      (None, error_message)      on failure — caller returns a 400
    """
    # ── Required fields ────────────────────────────────────────────────────────
    message = data.get("message")
    if not message or not str(message).strip():
        return None, "Field 'message' is required and must not be empty."

    message_str = str(message).strip()
    if len(message_str) > MAX_NEGOTIATE_MSG:
        return None, (
            f"Field 'message' exceeds the maximum allowed length "
            f"of {MAX_NEGOTIATE_MSG} characters."
        )

    # ── Context validation (optional block, but fields inside are typed) ───────
    context = data.get("context", {})
    if not isinstance(context, dict):
        return None, "Field 'context' must be a JSON object."

    vessel = context.get("vessel", {})
    if not isinstance(vessel, dict):
        return None, "Field 'context.vessel' must be a JSON object."

    route = context.get("route", {})
    if not isinstance(route, dict):
        return None, "Field 'context.route' must be a JSON object."

    # ── History validation (optional array of {role, content} objects) ─────────
    history = data.get("history", [])
    if not isinstance(history, list):
        return None, "Field 'history' must be an array."

    # ── Sanitise ───────────────────────────────────────────────────────────────
    # The message goes directly into the Gemini prompt, so we must strip any
    # HTML / script content that could manipulate the model's instructions.
    sanitized_message = sanitize_string(message_str, MAX_NEGOTIATE_MSG)

    # Sanitise free-text fields inside vessel / route that could reach the prompt
    if "name" in vessel:
        vessel["name"] = sanitize_string(str(vessel["name"]), 200)
    if "type" in vessel:
        vessel["type"] = sanitize_string(str(vessel["type"]), MAX_VESSEL_TYPE)
    if "currentPort" in vessel:
        vessel["currentPort"] = sanitize_string(str(vessel["currentPort"]), MAX_PORT_NAME)

    if "origin" in route:
        route["origin"] = sanitize_string(str(route["origin"]), MAX_PORT_NAME)
    if "destination" in route:
        route["destination"] = sanitize_string(str(route["destination"]), MAX_PORT_NAME)

    # Rebuild cleaned payload
    cleaned = {
        "message": sanitized_message,
        "context": {"vessel": vessel, "route": route},
        "history": history,
    }
    return cleaned, None


# ─── Validate /api/vessels/match ─────────────────────────────────────────────

def validate_vessel_match(data: dict) -> tuple[dict | None, str | None]:
    """
    Validate and sanitize the payload for POST /api/vessels/match.
    """
    required = ["cargoType", "cargoVolume", "originPort", "destinationPort"]
    missing = [f for f in required if f not in data or data[f] is None]
    if missing:
        return None, f"Missing required fields: {', '.join(missing)}."

    # ── Type checks ────────────────────────────────────────────────────────────
    try:
        cargo_volume = float(data["cargoVolume"])
    except (ValueError, TypeError):
        return None, "Field 'cargoVolume' must be a number."

    if cargo_volume <= 0:
        return None, "Field 'cargoVolume' must be a positive number."

    if cargo_volume > 500_000:
        # Largest ULCC is ~550,000 DWT; flag unrealistic values
        return None, "Field 'cargoVolume' exceeds realistic maximum (500,000 MT)."

    top_n = data.get("topN", 5)
    try:
        top_n = int(top_n)
        if top_n < 1 or top_n > 20:
            raise ValueError
    except (ValueError, TypeError):
        return None, "Field 'topN' must be an integer between 1 and 20."

    # ── Length checks ──────────────────────────────────────────────────────────
    cargo_type = str(data["cargoType"]).strip()
    if len(cargo_type) > MAX_CARGO_TYPE:
        return None, f"Field 'cargoType' exceeds {MAX_CARGO_TYPE} characters."

    origin_port = str(data["originPort"]).strip()
    if len(origin_port) > MAX_PORT_NAME:
        return None, f"Field 'originPort' exceeds {MAX_PORT_NAME} characters."

    dest_port = str(data["destinationPort"]).strip()
    if len(dest_port) > MAX_PORT_NAME:
        return None, f"Field 'destinationPort' exceeds {MAX_PORT_NAME} characters."

    # ── Sanitise ───────────────────────────────────────────────────────────────
    cleaned = {
        "cargoType":        sanitize_string(cargo_type, MAX_CARGO_TYPE),
        "cargoVolume":      cargo_volume,
        "originPort":       sanitize_string(origin_port, MAX_PORT_NAME),
        "destinationPort":  sanitize_string(dest_port, MAX_PORT_NAME),
        "topN":             top_n,
    }
    return cleaned, None


# ─── Validate /api/routes/optimize ───────────────────────────────────────────

def validate_route_optimize(data: dict) -> tuple[dict | None, str | None]:
    """
    Validate and sanitize the payload for POST /api/routes/optimize.
    """
    origin = str(data.get("originPort", "")).strip()
    destination = str(data.get("destinationPort", "")).strip()

    if not origin:
        return None, "Field 'originPort' is required."
    if not destination:
        return None, "Field 'destinationPort' is required."
    if len(origin) > MAX_PORT_NAME:
        return None, f"Field 'originPort' exceeds {MAX_PORT_NAME} characters."
    if len(destination) > MAX_PORT_NAME:
        return None, f"Field 'destinationPort' exceeds {MAX_PORT_NAME} characters."

    cargo_volume = data.get("cargoVolume", 0)
    try:
        cargo_volume = float(cargo_volume)
        if cargo_volume < 0:
            raise ValueError
    except (ValueError, TypeError):
        return None, "Field 'cargoVolume' must be a non-negative number."

    vessel_type = data.get("vesselType")
    if vessel_type is not None:
        vessel_type = sanitize_string(str(vessel_type), MAX_VESSEL_TYPE)

    cleaned = {
        "originPort":       sanitize_string(origin, MAX_PORT_NAME),
        "destinationPort":  sanitize_string(destination, MAX_PORT_NAME),
        "cargoVolume":      cargo_volume,
        "vesselType":       vessel_type,
    }
    return cleaned, None
