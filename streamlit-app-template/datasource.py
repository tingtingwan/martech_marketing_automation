from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable


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
        # Minimal metadata to allow clients to navigate the UI without real data.
        # These entries do NOT include images or UC-backed fields.
        return [
            {
                "brief_id": "brief_001",
                "brief_title": "Women's Health Awareness - Q1 Acquisition",
                "campaign_name": "Women's Health Awareness - Q1 Acquisition",
                "type": "Acquisition",
                "lifecycle_stage": "cycle_tracking",
                "medical_constraints": [
                    "No unsupported medical claims",
                    "Cite research for any health benefits",
                ],
                "legal_requirements": [
                    "HIPAA compliant",
                    "FDA disclosure required",
                    "Privacy policy link visible",
                ],
            },
            {
                "brief_id": "brief_002",
                "brief_title": "Menopause Support - Retention Campaign",
                "campaign_name": "Menopause Support - Retention Campaign",
                "type": "Retention",
                "lifecycle_stage": "menopause",
                "medical_constraints": [
                    "No hormone therapy promotion",
                    "Avoid medical diagnosis claims",
                ],
                "legal_requirements": [
                    "Medical disclaimer visible",
                    "Privacy policy link",
                    "Safe data handling",
                ],
            },
        ]

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
    Skeleton to connect to Databricks. Query methods are provided as no-op
    stubs that return empty-but-valid structures so the app flow does not break.
    Implement with your preferred client (databricks-sdk SQL Statements API,
    databricks-sql-connector, or JDBC/ODBC) using the Warehouse ID.
    """

    host: str
    token: str
    warehouse_id: str = ""  # SQL Warehouse ID (a.k.a. DBSQL Warehouse)
    http_path: str = ""
    catalog: str = ""
    schema: str = ""

    # Example: lazy connection handle (not initialized by default)
    _conn: Any = None

    def _ensure_conn(self) -> None:
        """
        Establish and cache a connection to a SQL Warehouse using the
        databricks-sql-connector when available. Non-breaking: silently
        returns if connector is unavailable or env is incomplete.
        """
        if self._conn is not None:
            return
        # Prefer building http_path from warehouse_id if not provided
        http_path = self.http_path or (f"/sql/1.0/warehouses/{self.warehouse_id}" if self.warehouse_id else "")
        if not (self.host and self.token and http_path):
            return
        try:
            from databricks import sql  # type: ignore
        except Exception:
            return
        try:
            self._conn = sql.connect(
                server_hostname=self.host,
                http_path=http_path,
                access_token=self.token,
            )
        except Exception:
            # Keep non-breaking behavior; leave _conn as None
            self._conn = None

    def _execute_sql(self, query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Execute SQL against the configured Warehouse. Returns list of dict rows.
        This is a non-breaking stub; update with real execution code.
        """
        # Ensure connection (no-op until implemented or available)
        self._ensure_conn()
        if self._conn is None:
            # For now, return empty results and let the UI show empty state messages.
            return []
        # Best-effort minimal execution; ignore params in this stub
        try:
            cur = self._conn.cursor()
            try:
                cur.execute(query)
                cols = [c[0] for c in cur.description] if getattr(cur, "description", None) else []
                rows = cur.fetchall() or []
                out: List[Dict[str, Any]] = []
                if cols:
                    for r in rows:
                        # databricks-sql-connector returns tuples
                        out.append({cols[i]: r[i] for i in range(len(cols))})
                return out
            finally:
                try:
                    cur.close()
                except Exception:
                    pass
        except Exception:
            return []

    def list_campaigns(self) -> List[Dict[str, Any]]:
        # Example (replace with your UC SQL):
        # rows = self._execute_sql(
        #     "SELECT brief_id, brief_title, campaign_name, type, lifecycle_stage, "
        #     "medical_constraints, legal_requirements "
        #     "FROM catalog.schema.campaigns ORDER BY brief_id"
        # )
        # return rows
        return []

    def get_compliance(self, brief_id: str) -> Optional[Dict[str, Any]]:
        # Example (replace with your UC SQL):
        # rows = self._execute_sql(
        #     "SELECT * FROM catalog.schema.compliance WHERE brief_id = :brief_id LIMIT 1",
        #     {"brief_id": brief_id},
        # )
        # return rows[0] if rows else None
        return {}

    def get_generated_image_b64(self, brief_id: str) -> Optional[str]:
        # Example: fetch from a UC table or object store and return base64 string
        return None

    def get_handoff_output(self, params: Dict[str, Any]) -> Dict[str, Any]:
        # Example query placeholder:
        # rows = self._execute_sql("""
        #   SELECT * FROM catalog.schema.handoff WHERE brief_id = :brief_id LIMIT 1
        # """, {"brief_id": params.get("brief_id")})
        # if rows:
        #     return {"output": rows[0]}
        return {"output": {}}

    def get_analysis_output(self, params: Dict[str, Any]) -> Dict[str, Any]:
        # Example query placeholder:
        # rows = self._execute_sql("""
        #   SELECT * FROM catalog.schema.analysis WHERE brief_id = :brief_id ORDER BY ts DESC LIMIT 100
        # """, {"brief_id": params.get("brief_id")})
        return {"output": {}}


