Notebooks for dataset generation
================================

Use this folder to store the notebooks you use to generate or prepare datasets for the app (e.g., campaigns, compliance artifacts, handoff readiness, analysis metrics).

Recommended conventions
- File naming: prefix with an ordered step and a short purpose.
  - 01_ingest_campaigns.ipynb
  - 02_transform_compliance.ipynb
  - 03_publish_handoff_views.ipynb
- Output targets: publish to Unity Catalog (catalog.schema.table or view).
  - Keep raw/staging/serving layers separate.
  - Avoid writing large data extracts into this repo.
- Databricks configuration:
  - Set the following environment variables in your workspace or notebook session:
    - DATABRICKS_HOST, DATABRICKS_TOKEN
    - DATABRICKS_WAREHOUSE_ID (or SQL_WAREHOUSE_ID) and, if needed, DATABRICKS_HTTP_PATH
    - DATABRICKS_CATALOG, DATABRICKS_SCHEMA
  - Use SQL Warehouses (recommended) or a cluster with UC access for writes.

Notes
- This folder is for notebooks only. Do not store generated data files in git.
- The application expects live data in Unity Catalog; align table/view names with your implementation inside `streamlit-app-template/datasource.py`.


