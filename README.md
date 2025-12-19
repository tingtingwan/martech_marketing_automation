Flo Martech Apps - Overview
===========================

> Important: This repository is provided for demo purposes only and is not intended for production use. Security hardening, error handling, resiliency, and observability are intentionally minimal to keep the template simple. Review and adapt all code, dependencies, and infrastructure to your organization’s production standards before deploying to end users.

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

