Flo Martech Apps - Overview
===========================

This repo contains:

- streamlit-app/
  - The original Streamlit application with full UI and example wiring.
  - Includes `app.py`, `util.py`, `style.css`, `images/`, and supporting files.

- streamlit-app-template/
  - A client-ready template preserving the same UI/UX, with data access routed through a provider interface.
  - Defaults to a placeholder provider for preview; auto-detects Databricks env vars to use a Databricks data source once implemented.
  - See `streamlit-app-template/README.md` for Databricks Apps setup, env vars (HOST, TOKEN, WAREHOUSE_ID), and deployment checklist.

- notebooks/
  - Put your dataset-generation notebooks here (e.g., to publish Unity Catalog tables for campaigns, compliance, handoff, analysis).
  - A short guide is in `notebooks/README.md`.

Notes
- No sample/synthetic data is committed. The template shows clear empty states until you connect Unity Catalog data.
- Optional zip bundles of the template may appear in the root for sharing (e.g., `streamlit-app-template-v2.zip`).


