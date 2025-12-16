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
        Establish and cache a connection to a SQL Warehouse.
        This is a placeholder; replace with actual connection code.
        """
        # Example using databricks-sdk (Statements API):
        # from databricks.sdk import WorkspaceClient
        # self._conn = WorkspaceClient(host=self.host, token=self.token)
        # Or using databricks-sql-connector:
        # from databricks import sql
        # self._conn = sql.connect(server_hostname=..., http_path=self.http_path, access_token=self.token)
        return

    def _execute_sql(self, query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Execute SQL against the configured Warehouse. Returns list of dict rows.
        This is a non-breaking stub; update with real execution code.
        """
        # Ensure connection (no-op until implemented)
        self._ensure_conn()
        # TODO: Implement SQL execution using your preferred client.
        # For now, return empty results and let the UI show empty state messages.
        return []

    def list_campaigns(self) -> List[Dict[str, Any]]:
        # Example query (replace catalog.schema.table with your UC table/view)
        # rows = self._execute_sql(\"\"\"\n# SELECT brief_id, brief_title, campaign_name, type, lifecycle_stage,\n#        medical_constraints, legal_requirements\n# FROM catalog.schema.campaigns\n# ORDER BY brief_id\n# \"\"\")\n# return rows
        return []

    def get_compliance(self, brief_id: str) -> Optional[Dict[str, Any]]:
        # Example query placeholder:
        # rows = self._execute_sql(\"\"\"\n# SELECT * FROM catalog.schema.compliance WHERE brief_id = :brief_id LIMIT 1\n# \"\"\", {\"brief_id\": brief_id})\n# return rows[0] if rows else None
        return {}

    def get_generated_image_b64(self, brief_id: str) -> Optional[str]:
        # Example: fetch from a UC table or object store and return base64 string
        return None

    def get_handoff_output(self, params: Dict[str, Any]) -> Dict[str, Any]:
        # Example query placeholder:
        # rows = self._execute_sql(\"\"\"\n# SELECT * FROM catalog.schema.handoff WHERE brief_id = :brief_id LIMIT 1\n# \"\"\", {\"brief_id\": params.get(\"brief_id\")})\n+        # if rows:\n+        #     return {\"output\": rows[0]}\n+        return {\"output\": {}}

    def get_analysis_output(self, params: Dict[str, Any]) -> Dict[str, Any]:
        # Example query placeholder:
        # rows = self._execute_sql(\"\"\"\n# SELECT * FROM catalog.schema.analysis WHERE brief_id = :brief_id ORDER BY ts DESC LIMIT 100\n# \"\"\", {\"brief_id\": params.get(\"brief_id\")})\n+        return {\"output\": {}}


