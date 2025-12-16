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
    if host and token:
        return DatabricksDataSource(
            host=host,
            token=token,
            http_path=os.environ.get("DATABRICKS_HTTP_PATH", "") or "",
            catalog=os.environ.get("DATABRICKS_CATALOG", "") or "",
            schema=os.environ.get("DATABRICKS_SCHEMA", "") or "",
        )
    return PlaceholderDataSource()


