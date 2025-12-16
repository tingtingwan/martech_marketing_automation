from __future__ import annotations

from typing import Any, Dict, Optional
import time

from .config import get_data_source

_provider = get_data_source()


def normalize_brief(brief: Dict[str, Any], defaults: Dict[str, Any]) -> Dict[str, Any]:
    normalized = dict(defaults or {})
    for k, v in (brief or {}).items():
        normalized[k] = v
    return normalized


def get_compliance_from_uc_timeout(brief_id: str, timeout: float = 8.0) -> Optional[Dict[str, Any]]:
    """
    Delegates to provider.get_compliance. The timeout is advisory; this
    implementation does not enforce a hard timeout and returns None on error.
    """
    try:
        started = time.time()
        result = _provider.get_compliance(brief_id)
        # Optional: respect advisory timeout by dropping late results
        if (time.time() - started) > timeout:
            return None
        return result
    except Exception:
        return None


def get_generated_image_b64_from_uc(brief_id: str) -> Optional[str]:
    try:
        return _provider.get_generated_image_b64(brief_id)
    except Exception:
        return None


def get_handoff_output(params: Dict[str, Any]) -> Dict[str, Any]:
    try:
        return _provider.get_handoff_output(params)
    except Exception:
        return {"output": {}}


def get_analysis_output(params: Dict[str, Any]) -> Dict[str, Any]:
    try:
        return _provider.get_analysis_output(params)
    except Exception:
        return {"output": {}}


def generate_approval_checklist_from_compliance(compliance: Dict[str, Any]) -> Dict[str, Any]:
    """
    Keep contract compatible with the existing UI, but return an empty checklist
    by default to avoid mock/sample data in the template.
    """
    return {"total_items": 0, "items": []}

import os
import time
import json
from typing import Optional, Dict, Any, List

import streamlit as st  # type: ignore


def normalize_brief(brief: dict, defaults: dict) -> dict:
    return {
        "type": brief.get("type") or defaults.get("type"),
        "audience": brief.get("audience") or defaults.get("audience"),
        "budget": brief.get("budget") if brief.get("budget") not in (None, "", 0) else defaults.get("budget"),
        "timeline": brief.get("timeline") or defaults.get("timeline"),
        "brief": brief.get("brief") or defaults.get("brief"),
    }


def get_handoff_output(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Placeholder: returns an empty handoff plan.
    Replace with your implementation to fetch handoff/readiness data.
    """
    return {
        "output": {
            "readiness_status": "PENDING",
            "go_live_timestamp": "-",
            "channels": [],
            "budget_allocation": {},
            "monitoring_metrics": [],
            "assignees": {},
        }
    }


def get_analysis_output(params: dict) -> dict:
    """
    Placeholder: returns empty analysis.
    Replace with your implementation that fetches real performance metrics/findings.
    """
    return {
        "output": {
            "performance_metrics": [],
            "key_findings": [],
            "next_iteration_brief": {}
        }
    }


def get_databricks_connection():
    """
    Placeholder for Databricks connectivity. Implement using databricks-sdk or
    databricks-sql-connector and return a connection/cursor as needed.
    """
    return None


@st.cache_data(ttl=300, show_spinner=False)
def get_compliance_from_uc(brief_id: str) -> Dict[str, Any]:
    """
    Placeholder: returns empty compliance record.
    Replace with a query to your Unity Catalog tables/views.
    """
    return {}


def _run_with_timeout(fn, args=(), kwargs=None, timeout: int = 8):
    import threading
    kwargs = kwargs or {}
    result_holder: Dict[str, Any] = {}
    error_holder: Dict[str, Any] = {}

    def _target():
        try:
            result_holder["value"] = fn(*args, **kwargs)
        except Exception as e:
            error_holder["error"] = e

    t = threading.Thread(target=_target, daemon=True)
    t.start()
    t.join(timeout)
    if t.is_alive():
        return {"_timeout": True}
    if "error" in error_holder:
        raise error_holder["error"]
    return result_holder.get("value")


def get_compliance_from_uc_timeout(brief_id: str, timeout: int = 8) -> Dict[str, Any]:
    res = _run_with_timeout(get_compliance_from_uc, args=(brief_id,), timeout=timeout)
    if isinstance(res, dict) and res.get("_timeout"):
        return {"status": "error", "message": f"UC fetch timed out after {timeout}s"}
    return res or {}


@st.cache_data(ttl=300, show_spinner=False)
def get_generated_image_b64_from_uc(brief_id: str) -> Optional[str]:
    """
    Placeholder: returns None.
    Replace with a query to fetch the latest generated image (base64) for the brief.
    """
    return None


def generate_approval_checklist_from_compliance(compliance: Dict[str, Any]) -> Dict[str, Any]:
    """
    Placeholder: returns empty approval checklist.
    Replace with logic to map issues to approvers and due dates.
    """
    return {
        "brief_id": compliance.get("brief_id"),
        "campaign_name": compliance.get("campaign_name"),
        "total_items": 0,
        "items": []
    }


