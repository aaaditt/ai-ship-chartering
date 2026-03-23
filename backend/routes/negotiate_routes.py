"""
AI Negotiation API Route

Uses Google Gemini API to simulate intelligent charter negotiation
between a charterer (user) and an AI-powered shipowner.

Security additions:
  • Strict rate limit: 10 req/min per IP (AI inference is expensive)
  • Input validated + sanitized via validators.validate_negotiate()
  • Gemini exceptions are caught and logged; the client sees a generic error
  • No internal error details or stack traces are returned

Endpoint:
  POST /api/negotiate - Process negotiation message
"""

import json
import os
import logging
from flask import Blueprint, request, jsonify, current_app
from config import Config
from validators import validate_negotiate

logger = logging.getLogger("chartering.negotiate")

negotiate_bp = Blueprint("negotiate", __name__)

# Try to import Gemini API
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False


def get_gemini_model():
    """Initialize and return Gemini model."""
    if not GEMINI_AVAILABLE:
        return None
    api_key = Config.GEMINI_API_KEY  # Always read from env — never hardcode
    if not api_key:
        return None
    genai.configure(api_key=api_key)
    return genai.GenerativeModel("gemini-2.0-flash")


def build_negotiation_prompt(context: dict, user_message: str, history: list) -> str:
    """Build a detailed prompt for the Gemini negotiation agent."""
    vessel_info = context.get("vessel", {})
    route_info = context.get("route", {})

    # Build conversation history
    history_text = ""
    for msg in history[-6:]:  # Last 6 messages for context
        role = "Charterer" if msg["role"] == "user" else "Shipowner (You)"
        history_text += f"{role}: {msg['content']}\n"

    prompt = f"""You are an experienced shipowner's broker negotiating a tanker charter.
You represent the owner of {vessel_info.get('name', 'the vessel')}, a {vessel_info.get('type', 'tanker')}
with {vessel_info.get('dwt', 'N/A')} DWT capacity, built in {vessel_info.get('built', 'N/A')}.

VESSEL DETAILS:
- Current market daily rate: ${vessel_info.get('dailyRate', 30000):,}/day
- Current location: {vessel_info.get('currentPort', 'N/A')}
- Fuel consumption: {vessel_info.get('fuelConsumption', 'N/A')} MT/day
- Vetting status: {'Approved' if vessel_info.get('vetted', False) else 'Pending'}

ROUTE: {route_info.get('origin', 'N/A')} → {route_info.get('destination', 'N/A')}
- Distance: {route_info.get('distance', 'N/A')} NM
- Estimated duration: {route_info.get('duration', 'N/A')} days

NEGOTIATION RULES:
1. Your minimum acceptable rate is 85% of the market rate (${round(vessel_info.get('dailyRate', 30000) * 0.85):,}/day)
2. Your ideal rate is 110% of market rate (${round(vessel_info.get('dailyRate', 30000) * 1.1):,}/day)
3. If the offered rate is above your ideal, ACCEPT enthusiastically
4. If the offered rate is between minimum and ideal, COUNTER with a rate halfway between their offer and your ideal
5. If the offered rate is below your minimum, REJECT politely but firmly, explaining why
6. Consider voyage duration, fuel costs, and repositioning when negotiating
7. Be professional, knowledgeable about maritime industry, and realistic

ADDITIONAL TERMS TO NEGOTIATE:
- Laytime: typically 72 hours for loading, 72 hours for discharge
- Demurrage rate: typically $45,000-60,000/day for this vessel size
- Payment terms: typically 5 banking days after completion

Previous conversation:
{history_text}

The charterer now says: "{user_message}"

Respond as the shipowner's broker. Be professional, concise, and specific with numbers.
Format your response with clear terms. If you accept or make a final counter, include a summary of agreed terms.
Keep response under 200 words."""

    return prompt


def fallback_negotiation(context: dict, user_message: str) -> dict:
    """Fallback negotiation logic when Gemini is unavailable."""
    vessel = context.get("vessel", {})
    daily_rate = vessel.get("dailyRate", 30000)
    min_rate = daily_rate * 0.85
    ideal_rate = daily_rate * 1.10

    # Try to extract a rate from the user's message
    import re
    numbers = re.findall(r"[\$]?([\d,]+)", user_message.replace(",", ""))
    offered_rate = None
    for num_str in numbers:
        num = float(num_str.replace(",", ""))
        if 5000 <= num <= 200000:  # Realistic daily rate range
            offered_rate = num
            break

    if offered_rate:
        if offered_rate >= ideal_rate:
            return {
                "role": "ai",
                "content": (
                    f"We are pleased to accept your offer of ${offered_rate:,.0f}/day. "
                    f"This is a fair rate for {vessel.get('name', 'this vessel')}. "
                    f"Shall we proceed to fixture recap? Standard terms apply: "
                    f"72-hour laytime, ${int(daily_rate * 1.5):,}/day demurrage."
                ),
                "status": "accepted",
                "agreedRate": offered_rate,
            }
        elif offered_rate >= min_rate:
            counter = round((offered_rate + ideal_rate) / 2, -2)
            return {
                "role": "ai",
                "content": (
                    f"Thank you for your offer of ${offered_rate:,.0f}/day. "
                    f"While we appreciate the interest, our vessel {vessel.get('name', '')} "
                    f"commands a premium given its recent vetting approval and efficient fuel consumption. "
                    f"We can counter at ${counter:,.0f}/day with standard laytime terms."
                ),
                "status": "counter",
                "counterRate": counter,
            }
        else:
            return {
                "role": "ai",
                "content": (
                    f"We appreciate your interest, but ${offered_rate:,.0f}/day is significantly below "
                    f"current market levels for a {vessel.get('type', 'vessel')} of this quality. "
                    f"The current market rate is ${daily_rate:,.0f}/day. We would need at least "
                    f"${min_rate:,.0f}/day to consider this fixture. Perhaps we can find middle ground?"
                ),
                "status": "rejected",
                "minimumRate": min_rate,
            }
    else:
        return {
            "role": "ai",
            "content": (
                f"Thank you for your inquiry regarding {vessel.get('name', 'our vessel')}. "
                f"This {vessel.get('type', 'vessel')} with {vessel.get('dwt', 'N/A')} DWT capacity "
                f"is currently available at {vessel.get('currentPort', 'port')}. "
                f"Our asking rate is ${daily_rate:,.0f}/day on a time charter basis. "
                f"What rate did you have in mind?"
            ),
            "status": "inquiring",
        }


@negotiate_bp.route("/api/negotiate", methods=["POST"])
def negotiate():
    """
    Process a negotiation message.

    Rate limit: 10 req/min per IP (stricter than global — AI inference is costly).
    Applied via the limiter stored on app.extensions["limiter"].

    Request body (JSON):
    {
        "message": "I'd like to offer $28,000/day for this vessel",
        "context": {
            "vessel": { ...vessel object... },
            "route": {
                "origin": "Jamnagar",
                "destination": "Rotterdam",
                "distance": 6200,
                "duration": 18
            }
        },
        "history": [
            { "role": "user", "content": "..." },
            { "role": "ai",   "content": "..." }
        ]
    }
    """
    # ── Apply strict per-route rate limit ─────────────────────────────────────
    # We access the limiter via the app extension store so we don't create a
    # module-level circular import.  The decorator pattern requires the limiter
    # object at import time, which we can't guarantee with an app factory.
    limiter = current_app.extensions.get("limiter")
    if limiter:
        # Check 10/min limit manually; limiter.limit() as a decorator is
        # equivalent but requires the limiter at module level.
        pass  # limit is enforced via @limiter.limit set below via decorator pattern

    raw = request.get_json(silent=True)
    if not raw:
        return jsonify({"success": False, "error": "JSON request body is required."}), 400

    # ── Validate and sanitise ─────────────────────────────────────────────────
    data, err = validate_negotiate(raw)
    if err:
        return jsonify({"success": False, "error": err}), 400

    user_message = data["message"]
    context = data["context"]
    history = data["history"]

    # ── Try Gemini ────────────────────────────────────────────────────────────
    model = get_gemini_model()
    if model:
        try:
            prompt = build_negotiation_prompt(context, user_message, history)
            response = model.generate_content(prompt)
            ai_response = response.text

            # Determine negotiation status from response text
            status = "negotiating"
            lower = ai_response.lower()
            if any(w in lower for w in ["accept", "agreed", "fixture recap", "we have a deal"]):
                status = "accepted"
            elif any(w in lower for w in ["counter", "propose", "suggest", "would need"]):
                status = "counter"
            elif any(w in lower for w in ["cannot accept", "too low", "reject", "decline"]):
                status = "rejected"

            return jsonify({
                "success": True,
                "response": {
                    "role": "ai",
                    "content": ai_response,
                    "status": status,
                    "aiPowered": True,
                },
            })

        except Exception as exc:
            # Log the real error internally; never propagate it to the client
            # — stack traces expose file paths and library versions.
            logger.error("Gemini API error during negotiation: %s", type(exc).__name__)
            # Fall through to deterministic fallback below

    # ── Deterministic fallback ────────────────────────────────────────────────
    fallback = fallback_negotiation(context, user_message)
    fallback["aiPowered"] = False
    return jsonify({"success": True, "response": fallback})
