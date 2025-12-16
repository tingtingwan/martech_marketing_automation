import os
import sys
import html
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

import streamlit as st  # type: ignore
import pandas as pd  # type: ignore
from PIL import Image  # type: ignore
from io import BytesIO
import base64

from utils import (
    normalize_brief as _normalize_brief,
    get_handoff_output,
    get_compliance_from_uc_timeout,
    get_generated_image_b64_from_uc,
    generate_approval_checklist_from_compliance,
    get_analysis_output,
)
from config import get_data_source
from datasource import PlaceholderDataSource


APP_BASE_DIR = os.path.dirname(__file__)
_provider = get_data_source()

if APP_BASE_DIR and APP_BASE_DIR not in sys.path:
    # Ensure local module imports (utils, config, datasource) work when run as a script
    sys.path.insert(0, APP_BASE_DIR)

def _load_icon():
    try:
        _flo_logo_path = os.path.join(APP_BASE_DIR, "images", "brand_logo.png")
        return Image.open(_flo_logo_path)
    except Exception:
        return "🎯"


st.set_page_config(
    page_title="Flo Campaign Workflow",
    page_icon=_load_icon(),
    layout="wide",
    initial_sidebar_state="expanded",
)


def load_css():
    candidates = ["style.css", "style_css.css", "styles.css"]
    for name in candidates:
        css_file = os.path.join(APP_BASE_DIR, name)
        try:
            with open(css_file, "r") as f:
                st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
                return
        except FileNotFoundError:
            continue
    st.warning("CSS file not found (tried style.css, style_css.css, styles.css). Using default styles.")


load_css()

# ===================== Session State =====================
if "campaign_id" not in st.session_state:
    st.session_state.campaign_id = None
if "workflow_state" not in st.session_state:
    st.session_state.workflow_state = {
        "step": 0,
        "agent": "idle",
        "briefing_approved": False,
        "production_approved": False,
        "compliance_approved": False,
        "handoff_approved": False,
        "analysis_complete": False,
        "messages": [],
    }
if "approval_feedback" not in st.session_state:
    st.session_state.approval_feedback = {}
if "compliance_result" not in st.session_state:
    st.session_state.compliance_result = None

DEFAULT_BRIEF = {
    "type": "Awareness",
    "audience": "Women 18-35, health-conscious, digital-native",
    "budget": 250000,
    "timeline": "6 weeks",
    "brief": "Increase awareness, drive feature adoption, and build community. KPIs: CTR > 1.2%, Conversion > 4.5%, ROAS > 3.5x.",
}
if "campaign_brief" not in st.session_state:
    st.session_state.campaign_brief = DEFAULT_BRIEF.copy()


# ===================== Helpers =====================
def normalize_brief(brief: dict) -> dict:
    return _normalize_brief(brief, DEFAULT_BRIEF)



def render_header():
    col1, col2, col3 = st.columns([1, 3, 1])
    with col1:
        try:
            st.image(os.path.join(APP_BASE_DIR, "images", "brand_logo.png"), width=120)
        except Exception:
            st.markdown("### 🎯 Flo")
    with col2:
        st.title("Campaign Workflow Automation")
        st.caption("Single AI-powered System with Human Approval Loops built on Databricks")
    with col3:
        if st.session_state.campaign_id:
            st.metric("Campaign ID", st.session_state.campaign_id)


def render_workflow_progress():
    steps = [("📋", "Briefing"), ("🎨", "Production"), ("✅", "Compliance"), ("🚀", "Handoff"), ("📊", "Analysis")]
    current = st.session_state.workflow_state["step"]

    st.markdown('<div class="workflow-stepper-container">', unsafe_allow_html=True)
    parts = []
    for idx, (icon, _) in enumerate(steps):
        cls = "workflow-step"
        if idx < current:
            cls += " complete"
        elif idx == current:
            cls += " active"
        parts.append(f"<div class='{cls}'>{icon}</div>")
        if idx < len(steps) - 1:
            conn_cls = "workflow-connector"
            if idx < current:
                conn_cls += " complete"
            parts.append(f"<div class='{conn_cls}'><div class='progress'></div></div>")
    st.markdown(f'<div class="workflow-stepper">{"".join(parts)}</div>', unsafe_allow_html=True)
    lbls = []
    for idx, (_, name) in enumerate(steps):
        lcls = "workflow-label"
        if idx < current:
            lcls += " complete"
        elif idx == current:
            lcls += " active"
        lbls.append(f"<div class='{lcls}'>{name}</div>")
    st.markdown(f'<div class="workflow-labels">{"".join(lbls)}</div>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)


def render_approval_section(agent_name: str, step_num: int):
    st.markdown(f"### 👤 {agent_name} Approval")
    col1, col2 = st.columns([2, 1])
    with col1:
        feedback = st.text_area(
            "Approval Feedback (optional)",
            placeholder="Leave comments for the creative team...",
            height=80,
            key=f"feedback_{agent_name}",
        )
    with col2:
        st.write("")
        st.write("")
        approve_clicked = st.button("✅ Approve", key=f"approve_{agent_name}", use_container_width=True)
        reject_clicked = st.button("❌ Request Changes", key=f"reject_{agent_name}", use_container_width=True)
    approval_key = f"{agent_name.lower()}_approved"
    if approve_clicked:
        st.session_state.workflow_state[approval_key] = True
        st.session_state.approval_feedback[agent_name] = feedback
        st.success(f"✅ {agent_name} step approved!")
        st.session_state.workflow_state["step"] = step_num
        return True
    if reject_clicked:
        st.error(f"Changes requested for {agent_name} step. Please revise and resubmit.")
        return False
    if st.session_state.workflow_state.get(approval_key, False):
        st.info(f"{agent_name} already approved.")
    return False


def main():
    render_header()
    render_workflow_progress()
    st.divider()

    if "workflow_started" not in st.session_state:
        st.session_state["workflow_started"] = False

    # Fetch available campaigns from provider
    try:
        campaigns: List[Dict[str, Any]] = _provider.list_campaigns() or []
    except Exception:
        campaigns = []

    # ---------- Intro Section: choose campaign or show empty state ----------
    if not st.session_state.get("workflow_started", False):
        if isinstance(_provider, PlaceholderDataSource):
            st.info("Preview mode: no UC data or images. Configure Databricks access to enable live data.")

        def _format_campaign_top(item: Dict[str, Any]) -> str:
            key = str(item.get("brief_id") or "unknown")
            name = str(item.get("campaign_name") or item.get("brief_title") or key)
            return f"{key} — {name}"

        sel_idx = 0
        sel_item = st.selectbox(
            "Choose a campaign",
            options=list(range(len(campaigns))),
            index=sel_idx,
            format_func=lambda i: _format_campaign_top(campaigns[i]),
            key="selected_campaign_index",
        )
        chosen = campaigns[sel_item]
        st.session_state["campaign_meta"] = {
            "brief_id": chosen.get("brief_id"),
            "brief_title": chosen.get("brief_title"),
            "campaign_name": chosen.get("campaign_name"),
        }
        st.session_state.campaign_brief = normalize_brief(
            {
                "type": chosen.get("type", DEFAULT_BRIEF["type"]),
                "audience": DEFAULT_BRIEF["audience"],
                "budget": DEFAULT_BRIEF["budget"],
                "timeline": DEFAULT_BRIEF["timeline"],
                "brief": DEFAULT_BRIEF["brief"],
            }
        )

        # Summary card (same structure)
        meta = st.session_state.get("campaign_meta", {}) or {}
        lifecycle = chosen.get("lifecycle_stage") or "-"
        med_cons = ", ".join(chosen.get("medical_constraints") or []) if isinstance(chosen.get("medical_constraints"), list) else str(chosen.get("medical_constraints") or "-")
        legal_reqs = ", ".join(chosen.get("legal_requirements") or []) if isinstance(chosen.get("legal_requirements"), list) else str(chosen.get("legal_requirements") or "-")
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("##### Campaign Summary")
        st.markdown(
            "<div class='brief-grid' style='margin-top:8px;'>"
            f"<div class='brief-item'><div class='brief-item-label'>Title</div><div class='brief-item-value'>{html.escape(meta.get('brief_title','-') or '-')}</div></div>"
            f"<div class='brief-item'><div class='brief-item-label'>Campaign</div><div class='brief-item-value'>{html.escape(meta.get('campaign_name','-') or '-')}</div></div>"
            f"<div class='brief-item'><div class='brief-item-label'>Type</div><div class='brief-item-value'>{html.escape(st.session_state.campaign_brief.get('type','-') or '-')}</div></div>"
            f"<div class='brief-item'><div class='brief-item-label'>Lifecycle</div><div class='brief-item-value'>{html.escape(str(lifecycle))}</div></div>"
            f"<div class='brief-item'><div class='brief-item-label'>Medical Constraints</div><div class='brief-item-value'>{html.escape(med_cons)}</div></div>"
            f"<div class='brief-item'><div class='brief-item-label'>Legal Requirements</div><div class='brief-item-value'>{html.escape(legal_reqs)}</div></div>"
            "</div>",
            unsafe_allow_html=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)
        st.divider()
        if st.button("🚀 Start Campaign Creation", use_container_width=True):
            st.session_state.campaign_id = chosen.get("brief_id")
            st.session_state["prod_generated"] = False
            st.session_state.workflow_state = {
                "step": 0,
                "agent": "idle",
                "briefing_approved": False,
                "production_approved": False,
                "compliance_approved": False,
                "handoff_approved": False,
                "analysis_complete": False,
                "messages": [],
            }
            st.session_state.approval_feedback = {}
            st.session_state["workflow_started"] = True
            st.rerun()
        return

    # ---------- Workflow Tabs ----------
    step = st.session_state.workflow_state.get("step", 0)
    pct = int((max(0, min(step, 5)) / 5) * 100)
    st.markdown("#### Overall Progress")
    st.progress(pct)
    st.markdown("#### Approvals")
    chips = []
    chips.append(
        ("<span style='background:#e8f5e9;color:#2e7d32;padding:4px 10px;border-radius:999px;border:1px solid #c8e6c9'>Compliance Approved</span>")
        if st.session_state.workflow_state.get("compliance_approved")
        else "<span style='background:#fff3e0;color:#e65100;padding:4px 10px;border-radius:999px;border:1px solid #ffe0b2'>Compliance Pending</span>"
    )
    chips.append(
        ("<span style='background:#e8f5e9;color:#2e7d32;padding:4px 10px;border-radius:999px;border:1px solid #c8e6c9'>Handoff Approved</span>")
        if st.session_state.workflow_state.get("handoff_approved")
        else "<span style='background:#fff3e0;color:#e65100;padding:4px 10px;border-radius:999px;border:1px solid #ffe0b2'>Handoff Pending</span>"
    )
    st.markdown(" ".join(chips), unsafe_allow_html=True)
    brief = st.session_state.campaign_brief
    meta = st.session_state.get("campaign_meta", {})

    tabs = st.tabs(["📝 Briefing", "🎨 Production", "✅ Compliance", "🚀 Handoff", "📊 Analysis"])

    # ----- BRIEFING -----
    with tabs[0]:
        st.subheader("📝 Briefing")
        if not st.session_state.get("campaign_meta", {}).get("brief_id"):
            st.info("No campaign selected.")
        else:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown("##### Campaign Summary")
            st.markdown(
                "<div class='brief-grid' style='margin-top:8px;'>"
                f"<div class='brief-item'><div class='brief-item-label'>Title</div><div class='brief-item-value'>{html.escape(meta.get('brief_title','-') or '-')}</div></div>"
                f"<div class='brief-item'><div class='brief-item-label'>Campaign</div><div class='brief-item-value'>{html.escape(meta.get('campaign_name','-') or '-')}</div></div>"
                f"<div class='brief-item'><div class='brief-item-label'>Type</div><div class='brief-item-value'>{html.escape(brief.get('type','-') or '-')}</div></div>"
                f"<div class='brief-item'><div class='brief-item-label'>Lifecycle</div><div class='brief-item-value'>{html.escape(str(meta.get('lifecycle_stage','-')))}</div></div>"
                f"<div class='brief-item'><div class='brief-item-label'>Medical Constraints</div><div class='brief-item-value'>{html.escape('-')}</div></div>"
                f"<div class='brief-item'><div class='brief-item-label'>Legal Requirements</div><div class='brief-item-value'>{html.escape('-')}</div></div>"
                "</div>",
                unsafe_allow_html=True,
            )
            st.markdown("</div>", unsafe_allow_html=True)
            st.info("Next: open the “🎨 Production” tab to generate variations.")

    # ----- PRODUCTION -----
    with tabs[1]:
        st.subheader("🎨 Production Agent - Text-to-Image")
        col_seed, col_gen = st.columns([3, 2])
        with col_seed:
            st.markdown("#### Agent Steps")
            if not st.session_state.get("prod_prompt_generated", False):
                if st.button("🧠 Generate Expert Prompt", key="btn_gen_prompt", use_container_width=True):
                    st.session_state["prod_prompt_generated"] = True
                    st.session_state["prod_prompt_text"] = ""
            else:
                st.success("Expert prompt generated")
                _ep = st.session_state.get("prod_prompt_text") or ""
                st.markdown(
                    "<div class='expert-prompt' "
                    "style='font-size:16px; line-height:1.55; padding:12px 14px; "
                    "border:1px solid #eee; border-radius:10px; background:#fafafa; white-space:pre-wrap;'>"
                    f"{html.escape(_ep)}</div>",
                    unsafe_allow_html=True,
                )
            st.divider()
            if st.session_state.get("prod_prompt_generated", False) and not st.session_state.get("prod_seed_found", False):
                if st.button("🔎 Find Seed Image", key="btn_find_seed", use_container_width=True):
                    st.session_state["prod_seed_found"] = True
            elif st.session_state.get("prod_seed_found", False):
                st.success("Seed image ready")
                st.markdown("<div class='section-label'>Seed Image</div>", unsafe_allow_html=True)
                st.markdown("<div class='img-card'>", unsafe_allow_html=True)
                st.info("No seed image available in template. Integrate your own source via Databricks provider.")
                st.markdown("</div>", unsafe_allow_html=True)

        with col_gen:
            st.caption("**Generated Variation**")
            if not st.session_state.get("prod_generated", False):
                if not (st.session_state.get("prod_prompt_generated") and st.session_state.get("prod_seed_found")):
                    st.info("Complete steps on the left to enable generation.")
                    st.markdown('<div class="shimmer"></div>', unsafe_allow_html=True)
                else:
                    btn_label = "✨ Generate Creative" if not st.session_state.get("prod_generating") else "⏳ Generating..."
                    btn_disabled = st.session_state.get("prod_generating", False)
                    if st.button(btn_label, key="run_production_generate", use_container_width=True, disabled=btn_disabled):
                        st.session_state["prod_generating"] = True
                        st.session_state["prod_generate_started_at"] = time.time()
                    if st.session_state.get("prod_generating"):
                        stages = [
                            ("Analyzing", "Analyzing prompt and context..."),
                            ("Applying Guidelines", "Applying brand and compliance guidelines..."),
                            ("Generating", "Generating creative with model..."),
                            ("Optimizing", "Optimizing colors, layout, and composition..."),
                            ("Finalizing", "Finalizing output and preparing preview..."),
                        ]
                        st.markdown("<div class='stages'>" + "".join([f"<span class='stage'>{html.escape(n)}</span>" for n, _ in stages]) + "</div>", unsafe_allow_html=True)
                        stage_container = st.empty()
                        shimmer_container = st.empty()
                        for idx, (name, msg) in enumerate(stages):
                            chips = []
                            for j, (n2, _) in enumerate(stages):
                                cls = "stage"
                                if j < idx:
                                    cls += " done"
                                elif j == idx:
                                    cls += " active"
                                chips.append(f"<span class='{cls}'>{html.escape(n2)}</span>")
                            stage_container.markdown("<div class='stages'>" + "".join(chips) + "</div>", unsafe_allow_html=True)
                            shimmer_container.markdown("<div class='shimmer'></div>", unsafe_allow_html=True)
                            st.markdown(f"<div style='font-size:14px;color:#555;margin:6px 0'>{html.escape(msg)}</div>", unsafe_allow_html=True)
                            time.sleep(0.5)
                        shimmer_container.empty()
                        st.session_state["prod_generating"] = False
                        st.session_state["prod_generated"] = True
                        st.session_state["prod_generate_elapsed"] = 0.0
                        st.markdown("<span class='success-badge'>✅ Generated</span>", unsafe_allow_html=True)
                        st.session_state.workflow_state["step"] = 3
                        st.rerun()
            else:
                st.markdown("<div class='section-label'>Generated Creative</div>", unsafe_allow_html=True)
                st.markdown('<div class="img-card">', unsafe_allow_html=True)
                st.info("No generated image in the template. Provide your own via Databricks provider.")
                st.markdown('</div>', unsafe_allow_html=True)
        if st.session_state.get("prod_generated", False):
            st.info("Proceed to Compliance for approval.")

    # ----- COMPLIANCE -----
    with tabs[2]:
        st.subheader("✅ Compliance Review")
        brief_id = st.session_state.get("campaign_meta", {}).get("brief_id")
        if not brief_id:
            st.warning("⚠️ No campaign selected")
        else:
            st.markdown("###### Review campaigns for 5 areas:")
            st.markdown(
                "- Medical/Legal (35%): Accurate health claims, FDA compliance, HIPAA\n"
                "- Privacy (20%): GDPR compliance, data handling, consent\n"
                "- Brand (20%): Color usage (#F15A6B, #FF9A9E), tone, targeting\n"
                "- Accessibility (15%): WCAG AA contrast, text readability\n"
                "- Content (10%): Inclusive representation, accuracy"
            )
            with st.spinner("🔎 Fetching compliance decision..."):
                compliance = get_compliance_from_uc_timeout(brief_id, timeout=8)
            if not compliance:
                st.warning(f"❌ No compliance record for {brief_id}")
            else:
                col_img, col_det = st.columns([1, 1])
                with col_img:
                    st.markdown("##### Generated Creative")
                    img_b64 = get_generated_image_b64_from_uc(brief_id)
                    if img_b64:
                        try:
                            img = Image.open(BytesIO(base64.b64decode(img_b64)))
                            st.image(img, use_column_width=True)
                        except Exception as e:
                            st.warning(f"Could not display image: {e}")
                    else:
                        st.info("No generated image found for this brief.")
                with col_det:
                    st.markdown("##### Compliance Overview")
                    st.info("Compliance scoring visualization will render when data is available from the provider.")
                checklist = generate_approval_checklist_from_compliance(compliance)
                st.markdown("###### Approval Checklist")
                if checklist.get("total_items", 0) > 0:
                    df_chk = pd.DataFrame([{"Assignee": it.get("assignee"), "Due Date": it.get("due_date")} for it in checklist.get("items", [])])
                    st.table(df_chk)

            approved = render_approval_section("Compliance", 4)
            if approved:
                st.session_state.workflow_state["compliance_approved"] = True
                st.session_state.workflow_state["step"] = 4
                st.rerun()

    # ----- HANDOFF -----
    with tabs[3]:
        st.subheader("🚀 Handoff & Go-Live")
        if not st.session_state.workflow_state.get("compliance_approved", False):
            st.warning("⚠️ Please get Compliance approval first before handoff.")
        else:
            brief_id = st.session_state.get("campaign_meta", {}).get("brief_id") or ""
            handoff_output = get_handoff_output({"brief_id": brief_id})
            data = handoff_output.get("output", {})
            status = str(data.get("readiness_status", "PENDING")).upper()
            ts = data.get("go_live_timestamp", "-")
            channels = data.get("channels", []) or []
            budget = data.get("budget_allocation", {}) or {}
            monitors = data.get("monitoring_metrics", []) or []
            assignees = data.get("assignees", {}) or {}
            color = "#2e7d32" if status == "GO_LIVE" else ("#f9a825" if status == "PENDING" else "#d32f2f")
            status_text = "✅ Ready to Launch" if status == "GO_LIVE" else ("⏳ Pending Launch" if status == "PENDING" else "🚫 Blocked")
            st.markdown(
                "<div style='display:inline-block;padding:6px 12px;border-radius:999px;"
                f"background:{color};color:#fff;font-weight:700;font-size:14px;'>"
                f"{status_text}</div>",
                unsafe_allow_html=True,
            )
            st.markdown(f"**Target Launch:** {ts}", unsafe_allow_html=True)
            st.divider()
            col_channels, col_budget, col_team = st.columns([1.2, 1, 1.3])
            with col_channels:
                st.markdown("#### 📱 Channels")
                if channels:
                    chip_html = " ".join(
                        f"<span style='display:inline-block;padding:5px 12px;border-radius:20px;background:#e3f2fd;color:#1565c0;margin:3px 6px 3px 0;border:1px solid #90caf9;font-weight:600;font-size:13px'>{html.escape(c)}</span>"
                        for c in channels
                    )
                    st.markdown(chip_html, unsafe_allow_html=True)
                else:
                    st.write("—")
                st.markdown("#### 📊 Monitoring Metrics", unsafe_allow_html=True)
                if monitors:
                    metrics_html = "<ul style='margin:8px 0;padding-left:20px;'>"
                    for m in monitors:
                        metrics_html += f"<li style='margin:6px 0;color:#424242;font-size:13px'>{html.escape(str(m))}</li>"
                    metrics_html += "</ul>"
                    st.markdown(metrics_html, unsafe_allow_html=True)
                else:
                    st.write("—")
            with col_budget:
                st.markdown("#### 💰 Budget Split")
                if budget:
                    budget_data = [{"Channel": k.title(), "Allocation": v} for k, v in budget.items()]
                    df_budget = pd.DataFrame(budget_data)
                    st.dataframe(
                        df_budget,
                        use_container_width=True,
                        hide_index=True,
                        column_config={"Channel": st.column_config.TextColumn(width="medium"), "Allocation": st.column_config.TextColumn(width="small")},
                    )
                    st.markdown("**Allocation Breakdown**")
                    for ch, pct in budget.items():
                        pct_num = float(pct.rstrip("%")) if isinstance(pct, str) else 0
                        st.progress(pct_num / 100, text=f"{ch.title()}: {pct}")
                else:
                    st.write("—")
            with col_team:
                st.markdown("#### 👥 Channel Owners")
                if assignees:
                    for channel, owner in assignees.items():
                        owner_name = str(owner).split("(")[0].strip() if "(" in str(owner) else str(owner)
                        owner_role = str(owner).split("(")[1].rstrip(")") if "(" in str(owner) else ""
                        owner_html = (
                            f"<div style='padding:8px 10px;margin:6px 0;border-radius:8px;"
                            f"background:#f5f5f5;border-left:4px solid #f15a6b;'>"
                            f"<div style='font-weight:600;color:#1a1a1a;font-size:13px'>{html.escape(channel)}</div>"
                            f"<div style='font-size:12px;color:#666;margin-top:3px'>{html.escape(owner_name)}</div>"
                            f"<div style='font-size:11px;color:#999;margin-top:2px'>{html.escape(owner_role)}</div>"
                            f"</div>"
                        )
                        st.markdown(owner_html, unsafe_allow_html=True)
                else:
                    st.write("—")
                st.divider()
            st.markdown("#### ✓ Pre-Launch Checklist")
            checklist_items = [
                ("Campaign assets approved & uploaded", False),
                ("Tracking parameters configured", False),
                ("Compliance notes shared with owners", False),
                ("Team assignments confirmed", False),
                ("Budget limits set in ad platforms", False),
            ]
            checklist_html = "<div style='background:#f9f9f9;padding:12px;border-radius:8px;border:1px solid #eee;'>"
            for item, completed in checklist_items:
                check_icon = "✅" if completed else "⏳"
                check_color = "#2e7d32" if completed else "#ffa500"
                checklist_html += (
                    f"<div style='padding:6px 0;display:flex;align-items:center;color:#333;font-size:13px;'>"
                    f"<span style='color:{check_color};margin-right:10px;font-weight:bold;'>{check_icon}</span>"
                    f"{html.escape(item)}"
                    f"</div>"
                )
            checklist_html += "</div>"
            st.markdown(checklist_html, unsafe_allow_html=True)
            st.divider()
            approved = render_approval_section("Handoff", 5)
            if approved:
                st.session_state.workflow_state["handoff_approved"] = True
                st.session_state.workflow_state["step"] = 5
                st.rerun()

    # ----- ANALYSIS -----
    with tabs[4]:
        st.subheader("📊 Campaign Performance Analysis")
        brief_id = st.session_state.get("campaign_meta", {}).get("brief_id") or ""
        analysis_output = get_analysis_output({"brief_id": brief_id})
        out = analysis_output.get("output", {})
        metrics = out.get("performance_metrics", []) or []
        findings = out.get("key_findings", []) or []
        next_brief = out.get("next_iteration_brief", {}) or {}
        if not metrics:
            st.info("📈 Performance analysis will be available after campaign launch.")
        else:
            st.markdown("#### 📈 Key Performance Indicators")
            try:
                m1 = metrics[0]
                m2 = metrics[1]
                m3 = metrics[2]
                col1, col2, col3 = st.columns(3)
                for i, m in enumerate([m1, m2, m3], start=1):
                    status_color = "#2e7d32" if "↑" in m.get("status", "") else "#d32f2f"
                    with (col1 if i == 1 else col2 if i == 2 else col3):
                        st.markdown(
                            f"<div style='padding:16px;border-radius:12px;background:#fafafa;border:1px solid #eee;'>"
                            f"<div style='font-size:12px;color:#666;font-weight:600;margin-bottom:8px'>{html.escape(m.get('metric', '-'))}</div>"
                            f"<div style='font-size:32px;font-weight:700;color:#1a1a1a'>{m.get('value', 0):.2f}</div>"
                            f"<div style='font-size:13px;color:{status_color};font-weight:600;margin-top:8px'>{html.escape(m.get('status', ''))}</div>"
                            f"<div style='font-size:11px;color:#999;margin-top:6px;line-height:1.4'>{html.escape(m.get('context', ''))}</div>"
                            f"</div>",
                            unsafe_allow_html=True,
                        )
            except Exception:
                st.info("Metrics present but not in expected format.")
            st.divider()
            st.markdown("#### 🔍 Key Findings & Insights")
            if findings:
                findings_html = (
                    "<div style='background:#f0f7ff;padding:16px;border-radius:12px;border-left:4px solid #1565c0;'>"
                    "<ul style='margin:0;padding-left:20px;'>"
                )
                for finding in findings:
                    findings_html += f"<li style='margin:8px 0;color:#1a1a1a;font-size:13px;line-height:1.6'>{html.escape(str(finding))}</li>"
                findings_html += "</ul></div>"
                st.markdown(findings_html, unsafe_allow_html=True)
            else:
                st.write("—")
            st.divider()
            st.markdown("#### 🚀 Next Iteration Recommendations")
            if isinstance(next_brief, dict) and next_brief:
                st.write(next_brief)
            else:
                st.write("—")
            st.divider()
            st.markdown("##### Performance Insight Dashboard")
            st.caption("Overview of media spend and revenue across all active marketing campaigns")
            dashboard_url = os.environ.get("DATABRICKS_DASHBOARD_URL", "")
            if dashboard_url:
                st.components.v1.html(
                    f"""
                    <iframe
                        src="{dashboard_url}"
                        width="100%"
                        height="1500"
                        frameborder="0">
                    </iframe>
                    """,
                    height=1500,
                    scrolling=True,
                )
            else:
                st.info("Set environment variable DATABRICKS_DASHBOARD_URL to embed your Databricks dashboard here.")


if __name__ == "__main__":
    main()
