import os
from typing import Literal

from .datasource import DataSource, PlaceholderDataSource, DatabricksDataSource

ProviderName = Literal["placeholder", "databricks"]


def get_provider_name() -> ProviderName:
    name = (os.environ.get("DATA_PROVIDER", "placeholder") or "").strip().lower()
    return "databricks" if name == "databricks" else "placeholder"


def get_data_source() -> DataSource:
    provider = get_provider_name()
    if provider == "databricks":
        # Skeleton; raises NotImplementedError on query calls
        return DatabricksDataSource(
            host=os.environ.get("DATABRICKS_HOST", ""),
            token=os.environ.get("DATABRICKS_TOKEN", ""),
            http_path=os.environ.get("DATABRICKS_HTTP_PATH", ""),
            catalog=os.environ.get("DATABRICKS_CATALOG", ""),
            schema=os.environ.get("DATABRICKS_SCHEMA", ""),
        )
    return PlaceholderDataSource()


