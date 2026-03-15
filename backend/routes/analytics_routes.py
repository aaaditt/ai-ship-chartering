"""
Analytics API Route

Returns performance metrics comparing Traditional vs AI-powered
chartering processes, based on research paper findings.

Endpoint:
  GET /api/analytics - Return performance metrics and comparison data
"""

import json
import os
from flask import Blueprint, request, jsonify
from config import Config

analytics_bp = Blueprint('analytics', __name__)


def load_freight_rates():
    path = os.path.join(Config.DATA_DIR, 'freight_rates.json')
    with open(path, 'r') as f:
        return json.load(f)


@analytics_bp.route('/api/analytics', methods=['GET'])
def get_analytics():
    """
    Return comprehensive analytics data.

    Query params:
      - section: specific section (comparison, savings, rates, all)
    """
    section = request.args.get('section', 'all')
    response = {"success": True}

    if section in ('all', 'comparison'):
        response["comparison"] = {
            "traditional": {
                "label": "Traditional Process",
                "timePerFixture": {"value": "4-6 hours", "minutes": 300},
                "staffRequired": {"value": "25-30", "avg": 28},
                "successRate": {"value": "85%", "decimal": 0.85},
                "costPerFixture": {"value": "$15,000-25,000", "avg": 20000},
                "dataProcessing": {"value": "Manual", "description": "Email, phone, spreadsheets"},
                "vesselEvaluation": {"value": "2-3 hours", "minutes": 150},
                "negotiationCycles": {"value": "5-8 rounds", "avg": 6},
                "errorRate": {"value": "8-12%", "decimal": 0.10},
                "operatingHours": {"value": "Business hours only", "hoursPerDay": 8}
            },
            "aiPowered": {
                "label": "AI-Powered Process",
                "timePerFixture": {"value": "30 minutes", "minutes": 30},
                "staffRequired": {"value": "8-10", "avg": 9},
                "successRate": {"value": "97%", "decimal": 0.97},
                "costPerFixture": {"value": "$3,000-5,000", "avg": 4000},
                "dataProcessing": {"value": "Automated", "description": "Real-time API integration"},
                "vesselEvaluation": {"value": "< 2 minutes", "minutes": 2},
                "negotiationCycles": {"value": "2-3 rounds", "avg": 2.5},
                "errorRate": {"value": "< 1%", "decimal": 0.005},
                "operatingHours": {"value": "24/7", "hoursPerDay": 24}
            },
            "improvements": {
                "timeSaving": "90%",
                "staffReduction": "70%",
                "successRateImprovement": "14%",
                "costReduction": "80%",
                "errorReduction": "95%"
            }
        }

    if section in ('all', 'savings'):
        response["annualSavings"] = {
            "assumptions": {
                "fixturesPerYear": 250,
                "avgDaysPerFixture": 20,
                "avgCharterRate": 35000,
                "avgCargoVolume": 100000
            },
            "traditional": {
                "annualStaffCost": 3500000,
                "annualOperatingCost": 5000000,
                "fixtureProcessingCost": 5000000,
                "totalAnnualCost": 13500000
            },
            "aiPowered": {
                "annualStaffCost": 1050000,
                "annualOperatingCost": 1500000,
                "fixtureProcessingCost": 1000000,
                "aiPlatformCost": 500000,
                "totalAnnualCost": 4050000
            },
            "netSavings": 9450000,
            "roi": "233%",
            "paybackMonths": 5
        }

    if section in ('all', 'rates'):
        rates = load_freight_rates()
        response["freightRates"] = rates

    if section in ('all', 'kpis'):
        response["kpis"] = {
            "totalFixtures": 1247,
            "avgScore": 92.3,
            "activeVessels": 18,
            "avgTimeToFixture": 28,
            "customerSatisfaction": 4.8,
            "onTimeDelivery": 96.5,
            "fleetUtilization": 87.2,
            "revenueYTD": 45600000
        }

    return jsonify(response)
