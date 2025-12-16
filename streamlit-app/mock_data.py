"""
Enhanced mock data for Flo compliance workflow demo.
Provides realistic compliance scores, analysis metrics, and handoff plans.
"""

from datetime import datetime, timedelta
import json
from typing import Optional, Dict, Any

ENHANCED_ANALYSIS_DATA = {
    "output": {
        "performance_metrics": [
            {
                "metric": "Click-Through Rate",
                "value": 1.47,
                "benchmark": 1.20,
                "status": "+22.5%"
            },
            {
                "metric": "Conversion Rate",
                "value": 5.23,
                "benchmark": 4.50,
                "status": "+16.2%"
            },
            {
                "metric": "Cost Per Acquisition",
                "value": 12.45,
                "benchmark": 14.80,
                "status": "-15.9%"
            },
            {
                "metric": "Return on Ad Spend",
                "value": 3.85,
                "benchmark": 3.50,
                "status": "+10%"
            },
            {
                "metric": "User Retention (30-day)",
                "value": 68.4,
                "benchmark": 62.0,
                "status": "+6.4pp"
            },
            {
                "metric": "Engagement Rate",
                "value": 4.32,
                "benchmark": 3.80,
                "status": "+13.7%"
            }
        ],
        
        "key_findings": [
            "Brief 001 exceeded CTR benchmark by 22.5%, indicating strong creative and messaging alignment",
            "Brief 003 achieved highest conversion rate (5.23%) - educational positioning drives intent",
            "Overall ROAS of 3.85x surpasses 3.5x campaign KPI target",
            "Compliance-approved campaigns with zero CRITICAL issues showed 18% higher engagement",
            "Diverse representation in Brief 002 resonated strongly with retention audience",
            "Medical/legal compliance scores inversely correlated with brand safety incidents (r=-0.94)"
        ],
        
        "next_iteration_brief": (
            "Based on Q1 performance: (1) Expand pregnancy planning content - highest "
            "conversion rate. (2) Deepen diversity in visuals - correlates with engagement. "
            "(3) Replicate medical rigor from Brief 003 across all campaigns. "
            "(4) Scale Brief 001 to 40-55 age group. Recommended Q2 allocation: "
            "35% Pregnancy, 30% Wellness, 20% Menopause, 15% Experimental."
        ),
        
        "budget_analysis": {
            "total_spent": 248750,
            "budget_allocated": 250000,
            "efficiency": "99.5%",
            "roi_multiple": 3.85,
            "total_revenue": 958088,
            "cac_reduction": "15.9%"
        }
    }
}



def get_analysis_output(params: Dict = None) -> Dict[str, Any]:
    """Get analysis output with performance metrics."""
    return ENHANCED_ANALYSIS_DATA.copy()
