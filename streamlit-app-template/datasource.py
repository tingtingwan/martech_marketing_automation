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
        raise NotImplementedError(
            "Implement SELECT to fetch campaigns (brief_id, names, metadata) from Unity Catalog."
        )

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


