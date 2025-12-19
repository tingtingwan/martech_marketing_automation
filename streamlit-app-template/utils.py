from __future__ import annotations

from typing import Any, Dict, Optional
import time

from config import get_data_source

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
from config import get_generated_creatives_table  # type: ignore


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
    Connect to Databricks SQL Warehouse using databricks-sdk for auth context
    and databricks-sql-connector for the connection.
    """
    try:
        from databricks import sql  # type: ignore
        from databricks.sdk.core import Config  # type: ignore
    except Exception:
        # Streamlit-safe: avoid crashing if connector not installed
        import streamlit as st  # type: ignore
        st.error("❌ Databricks connector not available. Please install databricks-sql-connector.")
        return None
    try:
        cfg = Config()
        # Prefer DATABRICKS_WAREHOUSE_ID; fall back to SQL_WAREHOUSE_ID
        warehouse_id = os.environ.get("DATABRICKS_WAREHOUSE_ID") or os.environ.get("SQL_WAREHOUSE_ID")
        if not warehouse_id:
            import streamlit as st  # type: ignore
            st.error("❌ DATABRICKS_WAREHOUSE_ID (or SQL_WAREHOUSE_ID) not set")
            return None
        connection = sql.connect(
            server_hostname=cfg.host,
            http_path=f"/sql/1.0/warehouses/{warehouse_id}",
            credentials_provider=lambda: cfg.authenticate,
        )
        return connection
    except Exception as e:
        import streamlit as st  # type: ignore
        st.error(f"❌ Connection failed: {e}")
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
    try:
        conn = get_databricks_connection()
        if not conn:
            return None
        cursor = None
        try:
            cursor = conn.cursor()
            table_name = get_generated_creatives_table()
            cursor.execute(
                f"""
                SELECT generated_image_b64
                FROM {table_name}
                WHERE brief_id = ?
                ORDER BY generation_timestamp DESC
                LIMIT 1
                """,
                (brief_id,)
            )
            row = cursor.fetchone()
            return row[0] if row and row[0] else None
        finally:
            try:
                if cursor:
                    cursor.close()
            except Exception:
                pass
            try:
                conn.close()
            except Exception:
                pass
    except Exception:
        return None

@st.cache_data(ttl=300, show_spinner=False)
def get_latest_creative_record(brief_id: str) -> Dict[str, Any]:
    rows: List[Dict[str, Any]] = []
    try:
        conn = get_databricks_connection()
        if not conn:
            return {}
        cursor = None
        try:
            cursor = conn.cursor()
            table_name = get_generated_creatives_table()
            cursor.execute(
                f"""
                SELECT
                    brief_id,
                    brief_title,
                    campaign_name,
                    expert_prompt,
                    expert_prompt_preview,
                    key_message,
                    lifecycle_stage,
                    seed_image_path,
                    seed_image_b64,
                    generated_image_path,
                    generated_image_b64,
                    generation_timestamp,
                    target_segment
                FROM {table_name}
                WHERE brief_id = ?
                ORDER BY generation_timestamp DESC
                LIMIT 1
                """,
                (brief_id,)
            )
            cols = [d[0] for d in (cursor.description or [])]
            rec = cursor.fetchone()
            if rec:
                try:
                    return {cols[i]: rec[i] for i in range(len(cols))}
                except Exception:
                    return {}
            return {}
        finally:
            try:
                if cursor:
                    cursor.close()
            except Exception:
                pass
            try:
                conn.close()
            except Exception:
                pass
    except Exception:
        return {}

@st.cache_data(ttl=300, show_spinner=False)
def get_expert_prompt_from_uc(brief_id: str) -> Optional[str]:
    rec = get_latest_creative_record(brief_id)
    if not isinstance(rec, dict) or not rec:
        return None
    prompt = rec.get("expert_prompt") or rec.get("expert_prompt_preview")
    if isinstance(prompt, (bytes, bytearray)):
        try:
            return prompt.decode("utf-8")
        except Exception:
            return str(prompt)
    return str(prompt) if prompt else None


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


