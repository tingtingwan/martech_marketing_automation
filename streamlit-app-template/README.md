## Databricks Streamlit App Template

Build a Streamlit app on Databricks for a marketing workflow (brief → creative → compliance → launch → analysis). This template keeps the exact UI and styling from the reference app, but leaves all data connections for you to wire up to your own sources.

### What this gives your team
- A ready-to-run UI for your campaign workflow
  - Briefing, Production, Compliance, Handoff, and Analysis tabs
  - Consistent layout, components, and styles
- Clear “empty” states instead of demo data
  - The app runs end-to-end even before you connect data
  - Users see helpful messages where data will appear
- A simple switch to plug in your own data later

### When to use this template
- You want to pilot a marketing workflow UI quickly, then connect to real data.
- You need a clean starting point with no sample or synthetic datasets.
- You plan to deploy on Databricks (Repos + Apps) and wire to Unity Catalog tables, Delta files, or Warehouses.

### Typical use cases
- Creative production with human approvals and compliance checks
- Handoff to channel owners with launch readiness and status tracking
- Post-launch analysis: KPIs, findings, next-iteration recommendations

### How the data side works (in plain terms)
- The app reads from a “data provider.” You can choose:
  - Placeholder (default): shows empty-state messages; no data needed.
  - Databricks (skeleton): you fill in how to read your tables/files.
- You can switch providers with one environment variable.

#### Choose your provider
- Start empty (recommended to validate the UI):
  ```bash
  export DATA_PROVIDER=placeholder
  ```
- Switch to Databricks when ready to connect data:
  ```bash
  export DATA_PROVIDER=databricks
  export DATABRICKS_HOST=https://<your-workspace-url>
  export DATABRICKS_TOKEN=<your-token>
  export DATABRICKS_HTTP_PATH=<optional-sql-warehouse-http-path>
  export DATABRICKS_CATALOG=<your-catalog>
  export DATABRICKS_SCHEMA=<your-schema>
  ```
  Then complete the methods inside `streamlit-app-template/datasource.py` (DatabricksDataSource) to fetch:
  - Campaign list (for selection)
  - Compliance details (and generated creative, if stored)
  - Handoff data (status, owners, budgets, timelines)
  - Analysis outputs (KPIs, findings, next steps)

### Run locally
```bash
pip install -r streamlit-app-template/requirements.txt
export DATA_PROVIDER=placeholder
streamlit run streamlit-app-template/app.py
```

### Deploy on Databricks (Apps)
1. Put this folder in a Git repo.
2. In Databricks, open Repos and connect to your repo.
3. Navigate to `streamlit-app-template/app.py` and open it as a Streamlit App.
4. In the App settings, add environment variables:
   - Start with: `DATA_PROVIDER=placeholder`
   - Later, add the Databricks variables above and change to `DATA_PROVIDER=databricks`
5. Attach to a cluster or SQL Warehouse that can read your Unity Catalog data.

### Databricks Apps best practices (specific)
- Ports and binding:
  - Databricks Apps provides the port via `DATABRICKS_APP_PORT`. Streamlit typically binds correctly without extra flags. If needed, you can add `--server.port ${DATABRICKS_APP_PORT} --server.address 0.0.0.0` in `app.yaml`.
- Keep startup fast:
  - Avoid heavy installs or blocking init; pin Python deps in `requirements.txt`.
- Log to stdout/stderr:
  - Streamlit logs go to stdout; avoid writing local log files.
- Use governed data access:
  - Query via SQL Warehouses/Unity Catalog; do not embed credentials in code.
- Configure with environment variables:
  - Use App settings for `DATA_PROVIDER`, Unity Catalog settings, and dashboard URL.
- Principle of least privilege:
  - Prefer `CAN USE` over `CAN MANAGE`; use service principals for uniform access.
- Secrets management:
  - Store tokens/secrets in App environment variables or secret scopes; never in code.
- Networking:
  - Allow only required outbound domains (package repos, APIs) per workspace policy.

### Deployment checklist (Databricks Apps)
- [ ] Code is in a Git repo and connected via Databricks Repos
- [ ] App created in Workspace Apps pointing to `streamlit-app-template/app.py`
- [ ] Environment variables set:
  - [ ] `DATA_PROVIDER=placeholder` (or `databricks` after you implement queries)
  - [ ] `DATABRICKS_HOST`, `DATABRICKS_TOKEN` (if using service principal), `DATABRICKS_HTTP_PATH` (optional)
  - [ ] `DATABRICKS_CATALOG`, `DATABRICKS_SCHEMA` (Unity Catalog context)
  - [ ] `DATABRICKS_DASHBOARD_URL` (embed URL; keep secrets out)
- [ ] Compute selected with access to Unity Catalog objects (SQL Warehouse or cluster)
- [ ] App permissions follow least-privilege (grant `CAN USE` to intended users/groups)
- [ ] Secrets stored in App environment variables or secret scopes (not in code)
- [ ] Logs visible in App run output (no local file logging)
- [ ] Outbound access restricted to needed domains only
- [ ] Smoke test: App loads, basic navigation works, no import errors

References
- Databricks App Templates (examples): [databricks/app-templates](https://github.com/databricks/app-templates)
- Databricks Apps best practices: [docs.databricks.com – Apps best practices](https://docs.databricks.com/en/dev-tools/databricks-apps/best-practices.html)

### What to implement (when connecting to data)
- In `datasource.py` (DatabricksDataSource):
  - `list_campaigns`: rows with `brief_id`, `brief_title`, `campaign_name`, `type`, optional lifecycle/legal/medical notes
  - `get_compliance`: scores, status, issues, and (optional) a generated image
  - `get_handoff_output`: channels, budget splits, team owners, target launch
  - `get_analysis_output`: KPIs, findings, next-iteration suggestions
- Keep secrets out of code. Use App environment variables, Secret Scopes, or `st.secrets`.

### Why no sample data?
Pilot apps often stall when “demo numbers” don’t match reality. This template shows the exact UI your users will get, while making it obvious where data will plug in—so you can align on the screens first, then connect to the right sources.
