import os
from datasource import DataSource, PlaceholderDataSource, DatabricksDataSource


def get_data_source() -> DataSource:
    """
    Select a data source without requiring a DATA_PROVIDER toggle.
    - If Databricks environment variables are present, return DatabricksDataSource.
    - Otherwise, return PlaceholderDataSource (empty, safe defaults).
    """
    host = os.environ.get("DATABRICKS_HOST", "") or ""
    token = os.environ.get("DATABRICKS_TOKEN", "") or ""
    # Prefer DATABRICKS_WAREHOUSE_ID; fall back to SQL_WAREHOUSE_ID for compatibility
    warehouse_id = os.environ.get("DATABRICKS_WAREHOUSE_ID", "") or os.environ.get("SQL_WAREHOUSE_ID", "") or ""
    if host and token:
        return DatabricksDataSource(
            host=host,
            token=token,
            warehouse_id=warehouse_id,
            http_path=os.environ.get("DATABRICKS_HTTP_PATH", "") or "",
            catalog=os.environ.get("DATABRICKS_CATALOG", "") or "",
            schema=os.environ.get("DATABRICKS_SCHEMA", "") or "",
        )
    return PlaceholderDataSource()


def get_creative_briefs_table() -> str:
    """
    Returns the fully-qualified table name for creative briefs.
    Override with env var CREATIVE_BRIEFS_TABLE, defaults to main.flo_martech.creative_briefs.
    """
    return os.environ.get("CREATIVE_BRIEFS_TABLE", "main.flo_martech.creative_briefs")

def get_generated_creatives_table() -> str:
    """
    Returns the fully-qualified table name for generated creatives.
    Override with env var GENERATED_CREATIVES_TABLE, defaults to main.flo_martech.generated_creatives.
    """
    return os.environ.get("GENERATED_CREATIVES_TABLE", "main.flo_martech.generated_creatives")





