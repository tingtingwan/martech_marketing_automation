from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable
import json
import time


@runtime_checkable
class DataSource(Protocol):
    def list_campaigns(self) -> List[Dict[str, Any]]:
        """
        Returns a list of campaign dictionaries.
        Expected fields if present:
          - brief_id: str
          - brief_title: str
          - campaign_name: str
          - type: str
          - lifecycle_stage: Optional[str]
          - medical_constraints: Optional[List[str]]
          - legal_requirements: Optional[List[str]]
          - seed_image_path: Optional[str]
          - generated_image_path: Optional[str]
          - expert_prompt: Optional[str]
        May return empty list when no data is available.
        """
        ...

    def get_compliance(self, brief_id: str) -> Optional[Dict[str, Any]]:
        """Return a compliance record for a brief or None when not available."""
        ...

    def get_generated_image_b64(self, brief_id: str) -> Optional[str]:
        """Return a base64 encoded image string or None if not available."""
        ...

    def get_handoff_output(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Return the handoff output structure. Should always return a dict."""
        ...

    def get_analysis_output(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Return the analysis output structure. Should always return a dict."""
        ...


class PlaceholderDataSource:
    """
    Production-friendly placeholder provider.
    Returns empty but valid results without any mock/sample data.
    """

    def list_campaigns(self) -> List[Dict[str, Any]]:
        """
        Replace placeholder output by querying Unity Catalog directly:
        SELECT * FROM main.flo_martech.creative_briefs
        and map rows to the UI's expected campaign structure.
        """
        try:
            # Lazy import to avoid circulars and to leverage shared connector
            from utils import get_databricks_connection  # type: ignore
            from config import get_creative_briefs_table  # type: ignore
        except Exception:
            return []

        rows: List[Dict[str, Any]] = []
        conn = None
        cursor = None
        try:
            conn = get_databricks_connection()
            if not conn:
                return []
            cursor = conn.cursor()
            # Keep query conservative: fetch recent briefs; adjust as needed
            table_name = get_creative_briefs_table()
            sql_text = (
                """
                SELECT
                    brief_id,
                    brief_title,
                    target_segment,
                    lifecycle_stage,
                    campaign_type,
                    key_message,
                    brand_guidelines,
                    medical_constraints,
                    legal_requirements,
                    created_at,
                    created_by
                FROM {table}
                ORDER BY created_at DESC
                LIMIT 100
                """.format(table=table_name)
            )
            cursor.execute(sql_text)
            desc = [c[0] for c in (cursor.description or [])]
            while True:
                rec = cursor.fetchone()
                if not rec:
                    break
                as_dict = {desc[i]: rec[i] for i in range(len(desc))}
                rows.append(as_dict)
            # Fallback: if fetchone loop yielded no rows, try fetchall once
            if not rows:
                try:
                    cursor.execute(sql_text)
                    all_rows = cursor.fetchall() or []
                    desc = [c[0] for c in (cursor.description or [])]
                    for rec in all_rows:
                        try:
                            as_dict = {desc[i]: rec[i] for i in range(len(desc))}
                            rows.append(as_dict)
                        except Exception:
                            continue
                except Exception:
                    pass
        except Exception:
            return []
        finally:
            try:
                if cursor:
                    cursor.close()
            except Exception:
                pass
            try:
                if conn:
                    conn.close()
            except Exception:
                pass

        def _as_list(val: Any) -> List[str]:
            if val is None:
                return []
            if isinstance(val, list):
                return [str(x) for x in val]
            if isinstance(val, (bytes, bytearray)):
                try:
                    s = val.decode("utf-8")
                except Exception:
                    s = str(val)
            else:
                s = str(val)
            s_strip = s.strip()
            # JSON array/object
            if s_strip.startswith("[") or s_strip.startswith("{"):
                try:
                    parsed = json.loads(s_strip)
                    if isinstance(parsed, list):
                        return [str(x) for x in parsed]
                    # If object, return values
                    if isinstance(parsed, dict):
                        return [str(v) for v in parsed.values()]
                except Exception:
                    pass
            # Comma-separated
            if "," in s:
                return [part.strip() for part in s.split(",") if part.strip()]
            # Single token
            return [s_strip] if s_strip else []

        campaigns: List[Dict[str, Any]] = []
        for r in rows:
            # Flexible mapping to accommodate different column naming conventions
            brief_id = (
                r.get("brief_id")
                or r.get("id")
                or r.get("brief_key")
                or r.get("campaign_id")
            )
            if brief_id is None:
                # Skip records without a stable identifier
                continue
            brief_title = (
                r.get("brief_title")
                or r.get("title")
                or r.get("name")
                or r.get("campaign_name")
                or str(brief_id)
            )
            campaign_name = (
                r.get("campaign_name")
                or r.get("campaign_title")
                or r.get("name")
                or brief_title
            )
            campaign_type = r.get("type") or r.get("campaign_type") or "Awareness"
            lifecycle_stage = r.get("lifecycle_stage") or r.get("lifecycle") or None

            medical_constraints = _as_list(
                r.get("medical_constraints") or r.get("medical_guidelines")
            )
            legal_requirements = _as_list(
                r.get("legal_requirements") or r.get("legal_guidelines")
            )

            campaigns.append(
                {
                    "brief_id": str(brief_id),
                    "brief_title": str(brief_title),
                    "campaign_name": str(campaign_name),
                    "type": str(campaign_type),
                    "lifecycle_stage": lifecycle_stage,
                    "medical_constraints": medical_constraints,
                    "legal_requirements": legal_requirements,
                    # Optional fields if present in table
                    "seed_image_path": r.get("seed_image_path"),
                    "generated_image_path": r.get("generated_image_path"),
                    "expert_prompt": r.get("expert_prompt"),
                }
            )

        return campaigns

    def get_compliance(self, brief_id: str) -> Optional[Dict[str, Any]]:
        return None

    def get_generated_image_b64(self, brief_id: str) -> Optional[str]:
        return None

    def get_handoff_output(self, params: Dict[str, Any]) -> Dict[str, Any]:
        # Keep the expected output contract but empty
        return {"output": {}}

    def get_analysis_output(self, params: Dict[str, Any]) -> Dict[str, Any]:
        # Keep the expected output contract but empty
        return {"output": {}}


@dataclass
class DatabricksDataSource:
    """
    Skeleton to connect to Databricks. All query methods intentionally
    raise NotImplementedError. Implement with your preferred client
    (databricks-sql-connector, DBSQL via JDBC/ODBC, or REST APIs).
    """

    host: str
    token: str
    warehouse_id: str = ""  # SQL Warehouse ID (a.k.a. DBSQL Warehouse)
    http_path: str = ""
    catalog: str = ""
    schema: str = ""

    # Example: lazy connection handle (not initialized here)
    _conn: Any = None

    def _ensure_conn(self) -> None:
        """
        Establish and cache a connection. Not implemented by default.
        """
        raise NotImplementedError(
            "Implement Databricks connection setup in DatabricksDataSource._ensure_conn"
        )

    def list_campaigns(self) -> List[Dict[str, Any]]:
        """
        Reuse the placeholder implementation which already queries
        main.flo_martech.creative_briefs via shared utils connection and
        maps rows to the UI's expected structure.
        """
        try:
            provider = PlaceholderDataSource()
            return provider.list_campaigns()
        except Exception:
            return []

    def get_compliance(self, brief_id: str) -> Optional[Dict[str, Any]]:
        raise NotImplementedError(
            "Implement a query to fetch compliance by brief_id from Unity Catalog."
        )

    def get_generated_image_b64(self, brief_id: str) -> Optional[str]:
        raise NotImplementedError(
            "Implement a query or object store fetch to retrieve generated image b64 for brief_id."
        )

    def get_handoff_output(self, params: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError(
            "Implement a query to fetch handoff output by brief_id or related keys."
        )

    def get_analysis_output(self, params: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError(
            "Implement a query to fetch analysis outputs / metrics for the campaign."
        )
 
