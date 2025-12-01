import os
import json
import time
import pandas as pd
import streamlit as st
from databricks import sql

# Config from environment (set in Lakehouse App)
DB_HOST = os.getenv("DATABRICKS_HOST")
DB_HTTP_PATH = os.getenv("DATABRICKS_HTTP_PATH")
DB_TOKEN = os.getenv("DATABRICKS_TOKEN")

st.set_page_config(page_title="Flo Health Marketing Automation", layout="wide")

# --- DB Helpers ---
def run_sql(query: str, params=None, fetch_df=True):
    with sql.connect(server_hostname=DB_HOST, http_path=DB_HTTP_PATH, access_token=DB_TOKEN) as conn:
        with conn.cursor() as cur:
            if params:
                cur.execute(query, params)
            else:
                cur.execute(query)
            if fetch_df and cur.description:
                cols = [d[0] for d in cur.description]
                rows = cur.fetchall()
                return pd.DataFrame(rows, columns=cols)
            return None

def ensure_tables():
    # Minimal table for publish handoff events
    run_sql("""
        CREATE TABLE IF NOT EXISTS flo_martech.publish_events (
            event_id STRING,
            creative_id STRING,
            brief_id STRING,
            ad_network STRING,
            status STRING,
            notes STRING,
            event_ts TIMESTAMP
        )
        USING DELTA
    """, fetch_df=False)

ensure_tables()

# --- UI ---
st.title("Flo Health – Marketing Automation Workflow")
st.caption("Step-by-step demo with human approvals (Agentbricks-ready skeleton)")

st.sidebar.header("Workflow Navigation")
step = st.sidebar.radio("Go to step", ["1) Briefing", "2) Production", "3) Compliance", "4) Handoff", "5) Performance"])

# Cache small reads for snappy UX
@st.cache_data(ttl=30)
def load_briefs():
    return run_sql("""
        SELECT brief_id, brief_title, target_segment, campaign_type, key_message, brand_guidelines
        FROM flo_martech.creative_briefs
        ORDER BY brief_id
    """)

@st.cache_data(ttl=30)
def load_creatives(brief_id):
    return run_sql(f"""
        SELECT creative_id, brief_id, creative_type, creative_title, creative_content, generation_timestamp, model_used
        FROM flo_martech.generated_creatives
        WHERE brief_id = '{brief_id}'
        ORDER BY creative_id
    """)

@st.cache_data(ttl=30)
def load_evals(creative_id):
    return run_sql(f"""
        SELECT judge_type, score, passed, feedback, flags, evaluation_timestamp
        FROM flo_martech.evaluations
        WHERE creative_id = '{creative_id}'
        ORDER BY judge_type
    """)

@st.cache_data(ttl=30)
def load_approvals(brief_id):
    return run_sql(f"""
        SELECT creative_id, brief_id, creative_title, status, overall_score, approval_timestamp
        FROM flo_martech.approved_creatives
        WHERE brief_id = '{brief_id}'
        ORDER BY approval_timestamp DESC
    """)

@st.cache_data(ttl=30)
def load_perf(brief_id):
    return run_sql(f"""
        SELECT ad_network, SUM(impressions) AS impressions, SUM(clicks) AS clicks, 
               SUM(conversions) AS conversions, SUM(spend) AS spend,
               AVG(ctr) AS ctr, AVG(conversion_rate) AS conversion_rate, AVG(roas) AS roas
        FROM flo_martech.campaign_performance
        WHERE brief_id = '{brief_id}'
        GROUP BY ad_network
        ORDER BY roas DESC
    """)

# Shared brief selector
briefs_df = load_briefs()
brief_choice = st.selectbox(
    "Select campaign brief",
    briefs_df["brief_id"].tolist(),
    format_func=lambda bid: f"{bid} – {briefs_df.set_index('brief_id').loc[bid]['brief_title']}"
)

selected_brief = briefs_df.set_index("brief_id").loc[brief_choice]
st.info(f"Target segment: {selected_brief['target_segment']} | Type: {selected_brief['campaign_type']}")

if step.startswith("1"):
    st.header("1) Briefing")
    st.subheader("Key message")
    st.write(selected_brief["key_message"])
    with st.expander("Brand guidelines"):
        st.write(selected_brief["brand_guidelines"])
    st.success("Human-in-the-loop: Confirm the brief is correct before moving to Production.")
    if st.button("Approve Brief to proceed"):
        st.toast("Brief approved. Move to Production.")
        time.sleep(0.5)

elif step.startswith("2"):
    st.header("2) Production")
    st.caption("Using pre-generated creatives for the demo (Agentbricks generation can be wired later).")
    creatives_df = load_creatives(brief_choice)
    for _, row in creatives_df.iterrows():
        with st.container(border=True):
            st.subheader(f"{row['creative_title']} ({row['creative_id']})")
            content = json.loads(row["creative_content"]) if isinstance(row["creative_content"], str) else row["creative_content"]
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Headline", content.get("headline", "—"))
            col2.metric("Tone", content.get("tone", "—"))
            col3.metric("CTA", content.get("cta", "—"))
            col4.metric("Model", row["model_used"])
            st.caption(f"Generated at {row['generation_timestamp']}")
    st.info("Proceed to Compliance to review medical/legal/appeal judges and approve creatives.")

elif step.startswith("3"):
    st.header("3) Compliance")
    st.caption("Simulated judges from evaluations table. Approve/reject creatives for handoff.")
    creatives_df = load_creatives(brief_choice)
    for _, row in creatives_df.iterrows():
        with st.container(border=True):
            st.subheader(f"Evaluate: {row['creative_title']} ({row['creative_id']})")
            evals = load_evals(row["creative_id"])
            cols = st.columns(3)
            for i, jt in enumerate(["medical", "legal", "appeal"]):
                e = evals[evals["judge_type"] == jt]
                if len(e):
                    score = float(e["score"].iloc[0])
                    passed = bool(e["passed"].iloc[0])
                    cols[i].metric(f"{jt.title()} score", f"{score:.1f}", "PASS" if passed else "FAIL")
                    cols[i].write(e["feedback"].iloc[0])
            st.divider()
            c1, c2 = st.columns(2)
            if c1.button(f"Approve {row['creative_id']}", key=f"approve_{row['creative_id']}"):
                # Upsert into approved_creatives with status=approved (idempotent-ish)
                run_sql(f"""
                    MERGE INTO flo_martech.approved_creatives t
                    USING (SELECT '{row['creative_id']}' AS creative_id, '{row['brief_id']}' AS brief_id, 
                                  '{row['creative_title']}' AS creative_title, map() AS creative_content,
                                  'approved' AS status, current_timestamp() AS approval_timestamp, 0.0 AS overall_score) s
                    ON t.creative_id = s.creative_id
                    WHEN MATCHED THEN UPDATE SET status='approved', approval_timestamp=current_timestamp()
                    WHEN NOT MATCHED THEN INSERT *
                """, fetch_df=False)
                st.success("Approved for handoff.")
                st.cache_data.clear()
            if c2.button(f"Reject {row['creative_id']}", key=f"reject_{row['creative_id']}"):
                run_sql(f"""
                    MERGE INTO flo_martech.approved_creatives t
                    USING (SELECT '{row['creative_id']}' AS creative_id, '{row['brief_id']}' AS brief_id, 
                                  '{row['creative_title']}' AS creative_title, map() AS creative_content,
                                  'rejected' AS status, current_timestamp() AS approval_timestamp, 0.0 AS overall_score) s
                    ON t.creative_id = s.creative_id
                    WHEN MATCHED THEN UPDATE SET status='rejected', approval_timestamp=current_timestamp()
                    WHEN NOT MATCHED THEN INSERT *
                """, fetch_df=False)
                st.warning("Rejected.")
                st.cache_data.clear()

elif step.startswith("4"):
    st.header("4) Handoff")
    st.caption("Publish approved creatives to an ad network (demo log).")
    approvals = load_approvals(brief_choice)
    approved = approvals[approvals["status"] == "approved"]
    if approved.empty:
        st.info("No approved creatives yet. Approve in Compliance step.")
    else:
        creative_id = st.selectbox("Choose approved creative", approved["creative_id"].tolist())
        ad_network = st.selectbox("Ad network", ["Meta", "Google", "TikTok", "Snapchat"])
        notes = st.text_input("Notes (optional)", "")
        if st.button("Publish (log handoff event)"):
            event_id = f"evt_{int(time.time())}"
            run_sql(f"""
                INSERT INTO flo_martech.publish_events
                VALUES ('{event_id}', '{creative_id}', '{brief_choice}', '{ad_network}', 'published', '{notes}', current_timestamp())
            """, fetch_df=False)
            st.success("Publish event logged.")
            st.cache_data.clear()

    st.divider()
    st.subheader("Recent handoff events")
    events = run_sql(f"""
        SELECT event_id, creative_id, brief_id, ad_network, status, notes, event_ts
        FROM flo_martech.publish_events
        WHERE brief_id = '{brief_choice}'
        ORDER BY event_ts DESC
        LIMIT 20
    """)
    st.dataframe(events, use_container_width=True)

elif step.startswith("5"):
    st.header("5) Performance insights")
    st.caption("Summarized performance (CTR/CR/ROAS/Spend) by ad network for the brief.")
    perf = load_perf(brief_choice)
    if perf is not None and len(perf):
        st.dataframe(perf, use_container_width=True)
        st.bar_chart(data=perf.set_index("ad_network")[["roas"]])
        st.bar_chart(data=perf.set_index("ad_network")[["ctr", "conversion_rate"]])
        st.bar_chart(data=perf.set_index("ad_network")[["impressions", "clicks", "conversions"]])
    else:
        st.info("No performance data yet for this brief.")

st.caption("This demo reads/writes Delta in Unity Catalog, ready to swap in Agentbricks tools and real serving endpoints.")