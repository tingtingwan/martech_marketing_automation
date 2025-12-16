import streamlit as st  # type: ignore
from datetime import datetime
import json
from typing import Optional, Dict, Any
import time
import os  
from PIL import Image  # type: ignore
import html
import pandas as pd  # type: ignore
import base64
from io import BytesIO
import importlib
import util
from util import (
    normalize_brief as _normalize_brief,
    get_handoff_output,
    get_compliance_from_uc_timeout,
    get_generated_image_b64_from_uc,
    generate_approval_checklist_from_compliance,
)



APP_BASE_DIR = os.path.dirname(__file__)
DEBUG_UC = (os.environ.get("UC_DEBUG", "false") or "").lower() in ("1", "true", "yes", "on")
PRODUCTION_CAMPAIGNS = {
    "brief_001": {
        "brief_id": "brief_001",
        "brief_title": "Women's Health Awareness",
        "campaign_name": "Women's Health Awareness - Q1 Acquisition",
        "type": "Acquisition",
        "seed_image_path": os.path.join(APP_BASE_DIR, "images", "seed_images", "flo_cycle_tracking.jpg"),
        "generated_image_path": os.path.join(APP_BASE_DIR, "images", "generated", "brief_001_Women's_Health_Awareness_-_Q1_Acquisition.png"),
        "expert_prompt": """A warm, inviting lifestyle image showing three diverse women (Black, Asian, and Caucasian, ages 20-35) in a bright, airy space with natural lighting. They\'re casually dressed in comfortable athleisure wear, smiling and engaging with smartphones displaying the app interface. The composition is balanced with women positioned on the right two-thirds, leaving space for text on the left. The color palette features soft gradients of coral (#F15A6B) and pink (#FF9A9E) accents that complement natural tones. Text overlay reads "Your personalized women\'s health companion" in a clean, modern sans-serif font. The mood is empowering, supportive and professional. Style reference: modern lifestyle photography with soft shadows, slight depth of field, and high-end magazine editorial quality. 1200x628px format with room for Meta/Instagram safe zones.""" },
    "brief_002": {
        "brief_id": "brief_002",
        "brief_title": "Menopause Support",
        "campaign_name": "Menopause Support - Retention Campaign",
        "type": "Retention",
        "seed_image_path": os.path.join(APP_BASE_DIR, "images", "seed_images", "flo_menopause.jpg"),
        "generated_image_path": os.path.join(APP_BASE_DIR, "images", "generated", "brief_002_Menopause_Support_-_Retention_Campaign.png"),
        "expert_prompt": """A warm, empowering image of three diverse women in their 40s-50s smiling confidently together in a bright, airy space with soft natural lighting. They appear supportive, relaxed and vibrant, dressed in casual-elegant clothing with subtle coral and pink accents. The background features gentle gradient transitions from soft coral (#F15A6B) to light pink (#FF9A9E). Text overlay reads "Navigate menopause with confidence" in modern, clean typography positioned elegantly in the composition. The overall aesthetic combines professional healthcare quality with approachable warmth, avoiding clinical sterility. Photographic style with subtle depth of field, 1200x628px ratio optimized for social media, high-resolution with balanced negative space for text placement.""",
    },
    "brief_003": {
        "brief_id": "brief_003",
        "brief_title": "Pregnancy Planning",
        "campaign_name": "Pregnancy Planning - Educational Series",
        "type": "Engagement",
        "seed_image_path": os.path.join(APP_BASE_DIR, "images", "seed_images", "flo_pregnancy.jpg"),
        "generated_image_path": os.path.join(APP_BASE_DIR, "images", "generated", "brief_003_Pregnancy_Planning_-_Educational_Series.png"),
        "expert_prompt": """A warm, inviting digital illustration showing a diverse group of women (25-40, different ethnicities) gathered around a stylized pregnancy planning calendar/app interface. The women are smiling and engaged, pointing at data visualizations and pregnancy timeline markers. The interface should feature clean, minimalist design with coral (#F15A6B) and pink (#FF9A9E) color accents. Background has a soft gradient from white to pale pink. Include subtle pregnancy-related icons (baby footprints, hearts) floating in background. Text overlay in modern sans-serif font: "Plan your pregnancy with data-driven insights" positioned prominently but elegantly. The overall composition should balance professional medical authority with warmth and optimism. Lighting is bright and airy with soft shadows. Style reference: modern digital illustration similar to medical textbook illustrations but with a friendly, approachable aesthetic. 1200x628px, Instagram/Meta format, high resolution.""",
    },
}

BRIEFS_DATA = [
    {
        "brief_id": "brief_001",
        "brief_title": "Women's Health Awareness - Q1 Acquisition",
        "target_segment": "18-35 Women, Health Conscious",
        "lifecycle_stage": "cycle_tracking",
        "campaign_type": "acquisition",
        "key_message": "Your personalized women's health companion",
        "brand_guidelines": "Modern, empowering, non-judgmental tone. Focus on education and control.",
        "medical_constraints": ["No unsupported medical claims", "Cite research for any health benefits"],
        "legal_requirements": ["HIPAA compliant", "FDA disclosure required", "Privacy policy link visible"],
        "created_at": datetime.now(),
        "created_by": "marketing_team"
    },
    {
        "brief_id": "brief_002",
        "brief_title": "Menopause Support - Retention Campaign",
        "target_segment": "45-55 Women",
        "lifecycle_stage": "menopause",
        "campaign_type": "retention",
        "key_message": "Navigate menopause with confidence and expert support",
        "brand_guidelines": "Supportive, expert-driven, warm and inclusive. Normalize the experience.",
        "medical_constraints": ["No hormone therapy promotion", "Avoid medical diagnosis claims"],
        "legal_requirements": ["Medical disclaimer visible", "Privacy policy link", "Safe data handling"],
        "created_at": datetime.now(),
        "created_by": "marketing_team"
    },
    {
        "brief_id": "brief_003",
        "brief_title": "Pregnancy Planning - Educational Series",
        "target_segment": "25-40 Women Planning Pregnancy",
        "lifecycle_stage": "pregnancy",
        "campaign_type": "acquisition",
        "key_message": "Plan your pregnancy with data-driven insights",
        "brand_guidelines": "Informative, supportive, science-backed. Celebrate milestones.",
        "medical_constraints": ["No fertility treatment claims", "Educational focus only"],
        "legal_requirements": ["Pregnancy-related disclaimers", "Professional consultation recommended"],
        "created_at": datetime.now(),
        "created_by": "marketing_team"
    }
]

# Enrich PRODUCTION_CAMPAIGNS with lifecycle/key message/segment/constraints from BRIEFS_DATA
try:
    _BRIEFS_BY_ID = {b.get("brief_id"): b for b in BRIEFS_DATA if b.get("brief_id")}
    for _k, _c in PRODUCTION_CAMPAIGNS.items():
        _bid = _c.get("brief_id")
        _b = _BRIEFS_BY_ID.get(_bid) if _bid else None
        if _b:
            if "lifecycle_stage" not in _c:
                _c["lifecycle_stage"] = _b.get("lifecycle_stage")
            if "key_message" not in _c:
                _c["key_message"] = _b.get("key_message")
            if "target_segment" not in _c:
                _c["target_segment"] = _b.get("target_segment")
            if "medical_constraints" not in _c:
                _c["medical_constraints"] = _b.get("medical_constraints")
            if "legal_requirements" not in _c:
                _c["legal_requirements"] = _b.get("legal_requirements")
except Exception:
    pass


# ============================================================
# PAGE CONFIG & STYLING
# ============================================================


try:
    _flo_logo_path = os.path.join(APP_BASE_DIR, "images", "brand_logo.png")
    _flo_page_icon = Image.open(_flo_logo_path)
except Exception:
    _flo_page_icon = "🎯"


st.set_page_config(
    page_title="Flo Campaign Workflow",
    page_icon=_flo_page_icon,
    layout="wide",
    initial_sidebar_state="expanded"
)


# Load external CSS
def load_css():
    # Try common filenames in order of preference
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


# ============================================================
# SESSION STATE
# ============================================================


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
        "messages": []
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
    "brief": "Increase awareness, drive feature adoption, and build community. KPIs: CTR > 1.2%, Conversion > 4.5%, ROAS > 3.5x."
}


if "campaign_brief" not in st.session_state:
    st.session_state.campaign_brief = DEFAULT_BRIEF.copy()


# ============================================================
# HELPER FUNCTIONS
# ============================================================


def normalize_brief(brief: dict) -> dict:
    return _normalize_brief(brief, DEFAULT_BRIEF)


# ============================================================
# UI COMPONENTS
# ============================================================


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

    st.markdown('</div>', unsafe_allow_html=True)


def render_campaign_brief_input():
    st.subheader("📝 Campaign Brief Input")
    current = st.session_state.campaign_brief

    col1, col2 = st.columns(2)
    with col1:
        allowed_types = ["Awareness", "Acquisition", "Retention", "Engagement"]
        current_type = current.get("type", DEFAULT_BRIEF["type"])
        selected_index = allowed_types.index(current_type) if current_type in allowed_types else 0
        campaign_type = st.selectbox("Campaign Type", allowed_types, index=selected_index, key="campaign_type")
    with col2:
        # Build audience options from BRIEFS_DATA target segments
        segment_options = sorted({b.get("target_segment") for b in BRIEFS_DATA if b.get("target_segment")})
        current_aud = current.get("audience", DEFAULT_BRIEF["audience"])
        seg_index = segment_options.index(current_aud) if current_aud in segment_options else 0
        selected_segment = st.selectbox("Target Audience", segment_options, index=seg_index, key="target_audience_segment")

    col1, col2 = st.columns(2)
    with col1:
        budget = st.number_input("Budget ($)", value=int(current.get("budget", DEFAULT_BRIEF["budget"])), step=10000, key="budget")
    with col2:
        timeline = st.text_input(
            "Timeline",
            value=current.get("timeline", DEFAULT_BRIEF["timeline"]) if isinstance(current.get("timeline"), str) else DEFAULT_BRIEF["timeline"],
            placeholder="e.g., 6 weeks",
            key="timeline"
        )

    brief_value = current.get("brief", DEFAULT_BRIEF["brief"])
    if not isinstance(brief_value, str):
        try:
            brief_value = json.dumps(brief_value, ensure_ascii=False)
        except Exception:
            brief_value = str(brief_value)

    campaign_brief_text = st.text_area(
        "Campaign Objectives",
        value=brief_value,
        placeholder="Describe campaign goals, key messages, and success criteria...",
        height=100,
        key="campaign_brief_text"
    )

    normalized = normalize_brief({
        "type": campaign_type,
        "audience": selected_segment,
        "budget": budget,
        "timeline": timeline,
        "brief": campaign_brief_text
    })
    st.session_state.campaign_brief = normalized

    # Inline Brief Summary (concise)
    meta = st.session_state.get("campaign_meta", {})
    bid = meta.get("brief_id")
    bd = {}
    try:
        bd = next((b for b in BRIEFS_DATA if b.get("brief_id") == bid), {})
    except Exception:
        bd = {}
    title_val = bd.get("brief_title") or meta.get("brief_title") or "-"
    segment_val = bd.get("target_segment") or normalized.get("audience") or "-"
    type_val = bd.get("campaign_type") or normalized.get("type") or "-"
    key_msg_val = bd.get("key_message") or "-"
    lifecycle_val = bd.get("lifecycle_stage") or "-"
    med_cons_val = ", ".join(bd.get("medical_constraints") or []) if isinstance(bd.get("medical_constraints"), list) else str(bd.get("medical_constraints") or "-")
    legal_reqs_val = ", ".join(bd.get("legal_requirements") or []) if isinstance(bd.get("legal_requirements"), list) else str(bd.get("legal_requirements") or "-")
    st.markdown(
        "<div class='card' style='margin-top:8px;'>"
        "<div class='card-header'><h5 class='card-title' style='margin:0;'>Brief Summary</h5></div>"
        "<div class='brief-grid' style='margin-top:8px;'>"
        f"<div class='brief-item'><div class='brief-item-label'>Title</div><div class='brief-item-value'>{html.escape(str(title_val))}</div></div>"
        f"<div class='brief-item'><div class='brief-item-label'>Target Segment</div><div class='brief-item-value'>{html.escape(str(segment_val))}</div></div>"
        f"<div class='brief-item'><div class='brief-item-label'>Campaign Type</div><div class='brief-item-value'>{html.escape(str(type_val))}</div></div>"
        f"<div class='brief-item'><div class='brief-item-label'>Lifecycle</div><div class='brief-item-value'>{html.escape(str(lifecycle_val))}</div></div>"
        f"<div class='brief-item'><div class='brief-item-label'>Medical Constraints</div><div class='brief-item-value'>{html.escape(med_cons_val)}</div></div>"
        f"<div class='brief-item'><div class='brief-item-label'>Legal Requirements</div><div class='brief-item-value'>{html.escape(legal_reqs_val)}</div></div>"
        "</div>"
        "</div>",
        unsafe_allow_html=True
    )
    return normalized


def render_approval_section(agent_name: str, step_num: int):
    st.markdown(f"### 👤 {agent_name} Approval")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        feedback = st.text_area(
            "Approval Feedback (optional)",
            placeholder="Leave comments for the creative team...",
            height=80,
            key=f"feedback_{agent_name}"
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


# ============================================================
# MAIN APP
# ============================================================


def main():
    render_header()
    render_workflow_progress()
    st.divider()

    if "workflow_started" not in st.session_state:
        st.session_state["workflow_started"] = False

    if not st.session_state.get("workflow_started", False):

        def _format_campaign_top(opt_key: str) -> str:
            c = PRODUCTION_CAMPAIGNS.get(opt_key, {})
            name = c.get("campaign_name", opt_key)
            return f"{opt_key} — {name}"

        campaign_keys_top = list(PRODUCTION_CAMPAIGNS.keys())
        sel_key_top = st.selectbox(
            "Choose a campaign",
            options=campaign_keys_top,
            index=0,
            format_func=_format_campaign_top,
            key="selected_campaign_key"
        )
        sel_campaign = PRODUCTION_CAMPAIGNS[sel_key_top]
        st.session_state["campaign_meta"] = {
            "brief_id": sel_campaign.get("brief_id"),
            "brief_title": sel_campaign.get("brief_title"),
            "campaign_name": sel_campaign.get("campaign_name"),
        }
        st.session_state.campaign_brief = normalize_brief({
            "type": sel_campaign.get("type", DEFAULT_BRIEF["type"]),
            "audience": DEFAULT_BRIEF["audience"],
            "budget": DEFAULT_BRIEF["budget"],
            "timeline": DEFAULT_BRIEF["timeline"],
            "brief": DEFAULT_BRIEF["brief"]
        })
        # Show Campaign Summary (same style as Dashboard) include lifecycle, medical/legal
        meta = st.session_state.get("campaign_meta", {}) or {}
        brief_card = st.session_state.campaign_brief if isinstance(st.session_state.get("campaign_brief"), dict) else {}
        lifecycle = sel_campaign.get("lifecycle_stage") or "-"
        med_cons = ", ".join(sel_campaign.get("medical_constraints") or []) if isinstance(sel_campaign.get("medical_constraints"), list) else str(sel_campaign.get("medical_constraints") or "-")
        legal_reqs = ", ".join(sel_campaign.get("legal_requirements") or []) if isinstance(sel_campaign.get("legal_requirements"), list) else str(sel_campaign.get("legal_requirements") or "-")
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("##### Campaign Summary")
        st.markdown(
            "<div class='brief-grid' style='margin-top:8px;'>"
            f"<div class='brief-item'><div class='brief-item-label'>Title</div><div class='brief-item-value'>{html.escape(meta.get('brief_title','-') or '-')}</div></div>"
            f"<div class='brief-item'><div class='brief-item-label'>Campaign</div><div class='brief-item-value'>{html.escape(meta.get('campaign_name','-') or '-')}</div></div>"
            f"<div class='brief-item'><div class='brief-item-label'>Type</div><div class='brief-item-value'>{html.escape(brief_card.get('type','-') or '-')}</div></div>"
            f"<div class='brief-item'><div class='brief-item-label'>Lifecycle</div><div class='brief-item-value'>{html.escape(str(lifecycle))}</div></div>"
            f"<div class='brief-item'><div class='brief-item-label'>Medical Constraints</div><div class='brief-item-value'>{html.escape(med_cons)}</div></div>"
            f"<div class='brief-item'><div class='brief-item-label'>Legal Requirements</div><div class='brief-item-value'>{html.escape(legal_reqs)}</div></div>"
            "</div>",
            unsafe_allow_html=True
        )
        st.markdown('</div>', unsafe_allow_html=True)
        st.divider()
        if st.button("🚀 Start Campaign Creation", use_container_width=True):
            # Align campaign_id and initialize workflow only after explicit start
            st.session_state.campaign_id = sel_campaign.get("brief_id")
            st.session_state["prod_generated"] = False
            st.session_state.workflow_state = {
                    "step": 0,
                    "agent": "idle",
                    "briefing_approved": False,
                    "production_approved": False,
                    "compliance_approved": False,
                    "handoff_approved": False,
                    "analysis_complete": False,
                    "messages": []
            }
            st.session_state.approval_feedback = {}
            st.session_state["workflow_started"] = True
            st.rerun()
    
    else:
        # Overview strip: progress + approvals
        step = st.session_state.workflow_state.get("step", 0)
        pct = int((max(0, min(step, 5)) / 5) * 100)
        st.markdown("#### Overall Progress")
        st.progress(pct)
        st.markdown("#### Approvals")
        chips = []
        chips.append(("<span style='background:#e8f5e9;color:#2e7d32;padding:4px 10px;border-radius:999px;border:1px solid #c8e6c9'>Compliance Approved</span>")
                     if st.session_state.workflow_state.get("compliance_approved") else
                     "<span style='background:#fff3e0;color:#e65100;padding:4px 10px;border-radius:999px;border:1px solid #ffe0b2'>Compliance Pending</span>")
        chips.append(("<span style='background:#e8f5e9;color:#2e7d32;padding:4px 10px;border-radius:999px;border:1px solid #c8e6c9'>Handoff Approved</span>")
                     if st.session_state.workflow_state.get("handoff_approved") else
                     "<span style='background:#fff3e0;color:#e65100;padding:4px 10px;border-radius:999px;border:1px solid #ffe0b2'>Handoff Pending</span>")
        st.markdown(" ".join(chips), unsafe_allow_html=True)
        brief = st.session_state.campaign_brief
        meta = st.session_state.get("campaign_meta", {})
        # Show Campaign Summary above tabs (mirrors Dashboard card with extras)
        selected_key_top = st.session_state.get("prod_selected_campaign_prev") or (list(PRODUCTION_CAMPAIGNS.keys())[0] if PRODUCTION_CAMPAIGNS else None)
        selected_campaign_top = PRODUCTION_CAMPAIGNS.get(selected_key_top, {}) if selected_key_top else {}
        lifecycle_top = selected_campaign_top.get("lifecycle_stage") or "-"
        med_top = ", ".join(selected_campaign_top.get("medical_constraints") or []) if isinstance(selected_campaign_top.get("medical_constraints"), list) else str(selected_campaign_top.get("medical_constraints") or "-")
        legal_top = ", ".join(selected_campaign_top.get("legal_requirements") or []) if isinstance(selected_campaign_top.get("legal_requirements"), list) else str(selected_campaign_top.get("legal_requirements") or "-")
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("##### Campaign Summary")
        st.markdown(
            "<div class='brief-grid' style='margin-top:8px;'>"
            f"<div class='brief-item'><div class='brief-item-label'>Title</div><div class='brief-item-value'>{html.escape(meta.get('brief_title','-') or '-')}</div></div>"
            f"<div class='brief-item'><div class='brief-item-label'>Campaign</div><div class='brief-item-value'>{html.escape(meta.get('campaign_name','-') or '-')}</div></div>"
            f"<div class='brief-item'><div class='brief-item-label'>Type</div><div class='brief-item-value'>{html.escape(brief.get('type','-') or '-')}</div></div>"
            f"<div class='brief-item'><div class='brief-item-label'>Lifecycle</div><div class='brief-item-value'>{html.escape(str(lifecycle_top))}</div></div>"
            f"<div class='brief-item'><div class='brief-item-label'>Medical Constraints</div><div class='brief-item-value'>{html.escape(med_top)}</div></div>"
            f"<div class='brief-item'><div class='brief-item-label'>Legal Requirements</div><div class='brief-item-value'>{html.escape(legal_top)}</div></div>"
            "</div>",
            unsafe_allow_html=True
        )
        st.markdown('</div>', unsafe_allow_html=True)
        
        tabs = st.tabs([
            "📝 Briefing",
            "🎨 Production",
            "✅ Compliance",
            "🚀 Handoff",
            "📊 Analysis"
        ])

        # BRIEFING TAB
        with tabs[0]:
            st.subheader("📝 Briefing")
            # Campaign picker moved here
            def _format_campaign_top(opt_key: str) -> str:
                c = PRODUCTION_CAMPAIGNS.get(opt_key, {})
                name = c.get("campaign_name", opt_key)
                return f"{opt_key} — {name}"

            campaign_keys_top = list(PRODUCTION_CAMPAIGNS.keys())
            sel_key_top = st.selectbox(
                "Select campaign",
                options=campaign_keys_top,
                index=0,
                format_func=_format_campaign_top,
                key="brief_selected_campaign"
            )
            sel_campaign = PRODUCTION_CAMPAIGNS[sel_key_top]
            # Persist into session/meta when changed
            prev_top = st.session_state.get("prod_selected_campaign_prev")
            if prev_top is None or prev_top != sel_key_top:
                st.session_state["prod_generated"] = False
                st.session_state["prod_prompt_generated"] = False
                st.session_state["prod_seed_found"] = False
                if "prod_prompt_text" in st.session_state:
                    st.session_state.pop("prod_prompt_text", None)
                st.session_state["generated_image_path"] = sel_campaign.get("generated_image_path")
                st.session_state["prod_selected_campaign_prev"] = sel_key_top
                st.session_state["campaign_meta"] = {
                    "brief_id": sel_campaign.get("brief_id"),
                    "brief_title": sel_campaign.get("brief_title"),
                    "campaign_name": sel_campaign.get("campaign_name"),
                }
                # Align campaign id and type
                st.session_state.campaign_id = sel_campaign.get("brief_id")
                if "campaign_brief" in st.session_state and isinstance(st.session_state.campaign_brief, dict):
                    st.session_state.campaign_brief["type"] = sel_campaign.get("type", st.session_state.campaign_brief.get("type"))
                # Reset workflow to beginning on campaign switch
                st.session_state.workflow_state = {
                    "step": 0,
                    "agent": "idle",
                    "briefing_approved": False,
                    "production_approved": False,
                    "compliance_approved": False,
                    "handoff_approved": False,
                    "analysis_complete": False,
                    "messages": []
                }
                st.session_state.approval_feedback = {}
                st.rerun()
            # Show only the brief summary for selected campaign (no editable form)
            # Remove janky navigation button; guide the user instead
            # Brief summary card (match Dashboard “Campaign Summary”)
            meta = st.session_state.get("campaign_meta", {}) or {}
            brief_card = st.session_state.campaign_brief if isinstance(st.session_state.get("campaign_brief"), dict) else {}
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown("##### Campaign Summary")
            _sel_key = st.session_state.get('brief_selected_campaign') or ''
            _sel_obj = (PRODUCTION_CAMPAIGNS.get(_sel_key) or {}) if _sel_key else {}
            _life_txt = str((_sel_obj.get('lifecycle_stage') if isinstance(_sel_obj, dict) else None) or "-")
            _med_txt = ", ".join((_sel_obj.get('medical_constraints') or [])) if isinstance(_sel_obj.get('medical_constraints', []), list) else str((_sel_obj.get('medical_constraints')) or "-")
            _legal_txt = ", ".join((_sel_obj.get('legal_requirements') or [])) if isinstance(_sel_obj.get('legal_requirements', []), list) else str((_sel_obj.get('legal_requirements')) or "-")
            st.markdown(
                "<div class='brief-grid' style='margin-top:8px;'>"
                f"<div class='brief-item'><div class='brief-item-label'>Title</div><div class='brief-item-value'>{html.escape(meta.get('brief_title','-') or '-')}</div></div>"
                f"<div class='brief-item'><div class='brief-item-label'>Campaign</div><div class='brief-item-value'>{html.escape(meta.get('campaign_name','-') or '-')}</div></div>"
                f"<div class='brief-item'><div class='brief-item-label'>Type</div><div class='brief-item-value'>{html.escape(brief_card.get('type','-') or '-')}</div></div>"
                f"<div class='brief-item'><div class='brief-item-label'>Lifecycle</div><div class='brief-item-value'>{html.escape(_life_txt)}</div></div>"
                f"<div class='brief-item'><div class='brief-item-label'>Medical Constraints</div><div class='brief-item-value'>{html.escape(_med_txt)}</div></div>"
                f"<div class='brief-item'><div class='brief-item-label'>Legal Requirements</div><div class='brief-item-value'>{html.escape(_legal_txt)}</div></div>"
                "</div>",
                unsafe_allow_html=True
            )
            st.markdown('</div>', unsafe_allow_html=True)
            # Move guidance to the bottom
            st.info("Next: open the “🎨 Production” tab to generate variations.")

        # PRODUCTION TAB
        with tabs[1]:
            st.subheader("🎨 Production Agent - Text-to-Image")
            # Use campaign selected in Briefing
            selected_key = st.session_state.get("prod_selected_campaign_prev") or list(PRODUCTION_CAMPAIGNS.keys())[0]
            selected_campaign = PRODUCTION_CAMPAIGNS[selected_key]

            seed_image_path = selected_campaign.get("seed_image_path")
            generated_image_path = selected_campaign.get("generated_image_path")

            # Initialize staged flags
            if "prod_prompt_generated" not in st.session_state:
                st.session_state["prod_prompt_generated"] = False
            if "prod_seed_found" not in st.session_state:
                st.session_state["prod_seed_found"] = False
            if "prod_generating" not in st.session_state:
                st.session_state["prod_generating"] = False
            if "prod_generate_elapsed" not in st.session_state:
                st.session_state["prod_generate_elapsed"] = None
            # Simple hover style for image cards (scoped)
            st.markdown(
                """
                <style>
                .img-card{border:1px solid #eee;border-radius:12px;box-shadow:0 1px 8px rgba(0,0,0,0.06);padding:8px;transition:transform .12s ease, box-shadow .12s ease;background:#fff;}
                .img-card:hover{transform:scale(1.02);box-shadow:0 3px 14px rgba(0,0,0,0.10);}
                .img-caption{font-size:12px;color:#666;margin-top:6px}
                .img-meta{font-size:12px;color:#444;margin-top:8px}
                .img-sub{font-size:11px;color:#888}
                .section-label{font-weight:700;margin:6px 0 8px 0}
                /* shimmer skeleton */
                .shimmer{position:relative;overflow:hidden;border-radius:12px;background:linear-gradient(90deg,#f2f2f2 25%,#e6e6e6 37%,#f2f2f2 63%);background-size:400% 100%;animation:sh 1.2s ease infinite;width:100%;height:320px;border:1px solid #eee;}
                @keyframes sh{0%{background-position:100% 50%}100%{background-position:0 50%}}
                /* stage indicators */
                .stages{display:flex;gap:8px;flex-wrap:wrap;margin:8px 0 6px 0}
                .stage{font-size:12px;padding:6px 10px;border-radius:999px;border:1px solid #e5e7eb;background:#fafafa;color:#666}
                .stage.active{background:#e8f0fe;color:#1a73e8;border-color:#c6dafc;font-weight:700}
                .stage.done{background:#e8f5e9;color:#2e7d32;border-color:#c8e6c9}
                .success-badge{display:inline-block;padding:6px 10px;border-radius:999px;background:#e8f5e9;color:#2e7d32;border:1px solid #c8e6c9;font-weight:700}
                </style>
                """,
                unsafe_allow_html=True
            )

            # Give more space to the left for prompt; right for output
            col_seed, col_gen = st.columns([3, 2])
            with col_seed:
                st.markdown("#### Agent Steps")
                # Step 1: Generate Expert Prompt
                if not st.session_state.get("prod_prompt_generated", False):
                    if st.button("🧠 Generate Expert Prompt", key="btn_gen_prompt", use_container_width=True):
                        st.session_state["prod_prompt_generated"] = True
                        st.session_state["prod_prompt_text"] = selected_campaign.get("expert_prompt", "") or ""
                else:
                    st.success("Expert prompt generated")
                    _ep = st.session_state.get("prod_prompt_text") or selected_campaign.get("expert_prompt", "") or ""
                    st.markdown("##### Expert Prompt")
                    st.markdown(
                        "<div class='expert-prompt' "
                        "style='font-size:16px; line-height:1.55; padding:12px 14px; "
                        "border:1px solid #eee; border-radius:10px; background:#fafafa; white-space:pre-wrap;'>"
                        f"{html.escape(_ep)}</div>",
                        unsafe_allow_html=True
                    )
                st.divider()
                # Step 2: Find Seed Image
                if st.session_state.get("prod_prompt_generated", False) and not st.session_state.get("prod_seed_found", False):
                    if st.button("🔎 Find Seed Image", key="btn_find_seed", use_container_width=True):
                        st.session_state["prod_seed_found"] = True
                elif st.session_state.get("prod_seed_found", False):
                    st.success("Seed image ready")
                    st.markdown("<div class='section-label'>Seed Image</div>", unsafe_allow_html=True)
                    st.markdown("<div class='img-card'>", unsafe_allow_html=True)
                    st.image(seed_image_path, use_column_width=True)
                    # Seed metadata
                    try:
                        from PIL import Image as PILImage  # type: ignore
                        _im = PILImage.open(seed_image_path)
                        _w, _h = _im.size
                        seed_dims = f"{_w}×{_h}"
                    except Exception:
                        seed_dims = "-"
                    st.markdown(
                        f"<div class='img-meta'>Dimensions: <span class='img-sub'>{seed_dims}</span></div>",
                        unsafe_allow_html=True
                    )
                    st.markdown("</div>", unsafe_allow_html=True)

            with col_gen:
                st.caption("**Generated Variation**")
                if not st.session_state.get("prod_generated", False):
                    # Require steps 1 and 2 before allowing generation
                    if not (st.session_state.get("prod_prompt_generated") and st.session_state.get("prod_seed_found")):
                        st.info("Complete steps on the left to enable generation.")
                        st.markdown('<div class="shimmer"></div>', unsafe_allow_html=True)
                    else:
                        # Button states
                        btn_label = "✨ Generate Creative" if not st.session_state["prod_generating"] else "⏳ Generating..."
                        btn_disabled = st.session_state["prod_generating"]
                        if st.button(btn_label, key="run_production_generate", use_container_width=True, disabled=btn_disabled):
                            st.session_state["prod_generating"] = True
                            st.session_state["prod_generate_started_at"] = time.time()
                        # Run staged flow if generating
                        if st.session_state.get("prod_generating"):
                            stages = [
                                ("Analyzing", "Analyzing prompt and context..."),
                                ("Applying Guidelines", "Applying brand and compliance guidelines..."),
                                ("Generating", "Generating creative with model..."),
                                ("Optimizing", "Optimizing colors, layout, and composition..."),
                                ("Finalizing", "Finalizing output and preparing preview..."),
                            ]
                            # Stage UI containers
                            st.markdown("<div class='stages'>" + "".join(
                                [f"<span class='stage'>{html.escape(n)}</span>" for n, _ in stages]
                            ) + "</div>", unsafe_allow_html=True)
                            stage_container = st.empty()
                            shimmer_container = st.empty()
                            # Iterate stages with smooth feedback
                            for idx, (name, msg) in enumerate(stages):
                                # Update stages with active/done states
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
                                time.sleep(0.8)
                            # Complete
                            shimmer_container.empty()
                            st.session_state["prod_generating"] = False
                            st.session_state["prod_generated"] = True
                            # Persist the exact generated image path for downstream (Compliance/Handoff)
                            st.session_state["generated_image_path"] = generated_image_path
                            # Capture metadata
                            ended = time.time()
                            started = st.session_state.get("prod_generate_started_at") or ended
                            st.session_state["prod_generate_elapsed"] = max(0.0, ended - started)
                            st.session_state["prod_generated_ts"] = datetime.now().strftime("%Y-%m-%d %H:%M")
                            st.session_state["prod_generated_model"] = "flux-kontext-apps/multi-image-kontext-max"
                            try:
                                from PIL import Image as PILImage  # type: ignore
                                _gen_im = PILImage.open(generated_image_path)
                                _gw, _gh = _gen_im.size
                                st.session_state["prod_generated_dims"] = f"{_gw}×{_gh}"
                            except Exception:
                                st.session_state["prod_generated_dims"] = "-"
                            st.session_state["prod_quality_score"] = 0.92
                            # Success badge and elapsed
                            elapsed = st.session_state.get("prod_generate_elapsed") or 0.0
                            st.markdown(f"<span class='success-badge'>✅ Generated in {elapsed:.1f}s</span>", unsafe_allow_html=True)
                            # advance directly to compliance and rerun
                            st.session_state.workflow_state["step"] = 3
                            st.rerun()
                else:
                    # Prefer the persisted path to ensure consistency across tabs
                    _gen_path = st.session_state.get("generated_image_path") or generated_image_path
                    if isinstance(_gen_path, str) and os.path.exists(_gen_path):
                        st.markdown("<div class='section-label'>Generated Creative</div>", unsafe_allow_html=True)
                        st.markdown('<div class="img-card">', unsafe_allow_html=True)
                        st.image(_gen_path, use_column_width=True)
                        # Metadata under generated image
                        ts = st.session_state.get("prod_generated_ts") or "-"
                        model = st.session_state.get("prod_generated_model") or "Demo Model"
                        dims = st.session_state.get("prod_generated_dims") or "-"
                        q = st.session_state.get("prod_quality_score")
                        qtxt = f"{q:.2f}" if isinstance(q, float) else "-"
                        st.markdown(
                            f"<div class='img-meta'>"
                            f"Model: <span class='img-sub'>{html.escape(str(model))}</span><br>"
                            f"Timestamp: <span class='img-sub'>{html.escape(str(ts))}</span><br>"
                            f"Dimensions: <span class='img-sub'>{html.escape(str(dims))}</span><br>"
                            f"Quality score: <span class='img-sub'>{html.escape(qtxt)}</span>"
                            f"</div>",
                            unsafe_allow_html=True
                        )
                        st.markdown('</div>', unsafe_allow_html=True)
                    else:
                        st.warning("Generated image not found. Please generate variations again.")

            if st.session_state.get("prod_generated", False):
                st.info("Proceed to Compliance for approval.")

        # COMPLIANCE TAB - READ DIRECTLY FROM UC
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
                with st.spinner("🔎 Fetching compliance decision from UC..."):
                    compliance = get_compliance_from_uc_timeout(brief_id, timeout=8)
                if not compliance:
                    st.warning(f"❌ No compliance record for {brief_id}")
                else:
                    st.success("✅ Compliance loaded")
                    # Two-column layout: left image, right details/scores
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
                        # Styled dashboard for scores
                        st.markdown(
                            """
                            <style>
                            .comp-wrap{display:flex;flex-direction:column;gap:10px}
                            .status-row{display:flex;align-items:center;gap:12px}
                            .status-badge{display:inline-block;padding:8px 14px;border-radius:999px;font-weight:700;color:#fff}
                            .status-approved{background:#2e7d32}
                            .status-flagged{background:#d32f2f}
                            .status-pending{background:#f9a825; animation:pulse 1.6s infinite}
                            @keyframes pulse {0%{box-shadow:0 0 0 0 rgba(249,168,37,0.5)}70%{box-shadow:0 0 0 14px rgba(249,168,37,0)}100%{box-shadow:0 0 0 0 rgba(249,168,37,0)}}
                            .grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px;align-items:center}
                            .circle{width:110px;height:110px;border-radius:50%;display:flex;align-items:center;justify-content:center;position:relative;background:#eee}
                            .circle-inner{position:absolute;inset:0;border-radius:50%;background:conic-gradient(var(--c) var(--p), #eee 0)}
                            .circle-hole{position:absolute;width:84px;height:84px;border-radius:50%;background:#fff}
                            .circle-text{position:relative;font-weight:800;color:#1a1a1a;font-size:18px}
                            .tile{display:flex;flex-direction:column;align-items:center;gap:6px;padding:8px;border:1px solid #eee;border-radius:12px;background:#fff}
                            .tile-label{font-size:12px;color:#555;font-weight:700}
                            .tile-sub{font-size:11px;color:#888}
                            .overall{grid-column:2;display:flex;flex-direction:column;align-items:center}
                            .overall .circle{width:140px;height:140px}
                            .overall .circle-hole{width:106px;height:106px}
                            .overall .circle-text{font-size:24px}
                            </style>
                            """,
                            unsafe_allow_html=True
                        )
                        # Extract scores
                        ml = float(compliance.get('medical_legal_score', 0) or 0)
                        pr = float(compliance.get('privacy_score', 0) or 0)
                        br = float(compliance.get('brand_score', 0) or 0)
                        ac = float(compliance.get('accessibility_score', 0) or 0)
                        co = float(compliance.get('content_score', 0) or 0)
                        ov = float(compliance.get('overall_score', 0) or 0)
                        def color_for(v: float) -> str:
                            return "#d32f2f" if v < 70 else ("#f9a825" if v <= 85 else "#2e7d32")
                        status_raw = str(compliance.get('approval_status', 'PENDING') or 'PENDING').upper()
                        status_cls = "status-approved" if status_raw == "APPROVED" else ("status-flagged" if status_raw in ("FLAGGED","REJECTED","DENIED") else "status-pending")
                        status_label = "APPROVED" if status_raw == "APPROVED" else ("FLAGGED" if status_raw in ("FLAGGED","REJECTED","DENIED") else "PENDING")
                        # Build tiles
                        def circle_tile(label: str, score: float, weight: str) -> str:
                            c = color_for(score)
                            p = max(0, min(int(score), 100))
                            return (
                                "<div class='tile'>"
                                f"<div class='tile-label'>{html.escape(label)}</div>"
                                f"<div class='circle' style='--p:{p}%;--c:{c}'>"
                                "<div class='circle-inner'></div>"
                                "<div class='circle-hole'></div>"
                                f"<div class='circle-text'>{p}</div>"
                                "</div>"
                                f"<div class='tile-sub'>Weight: {weight}</div>"
                                "</div>"
                            )
                        grid_html = (
                            "<div class='comp-wrap'>"
                            f"<div class='status-row'><span class='status-badge {status_cls}'>{html.escape(status_label)}</span>"
                            f"<span style='font-size:12px;color:#666'>Overall compliance status</span></div>"
                            "<div class='grid'>"
                            f"{circle_tile('Medical/Legal', ml, '35%')}"
                            "<div class='overall'>"
                            f"<div class='circle' style='--p:{int(ov)}%;--c:{color_for(ov)}'>"
                            "<div class='circle-inner'></div>"
                            "<div class='circle-hole'></div>"
                            f"<div class='circle-text'>{int(ov)}</div>"
                            "</div>"
                            "<div class='tile-sub'>Overall Score</div>"
                            "</div>"
                            f"{circle_tile('Privacy', pr, '20%')}"
                            f"{circle_tile('Brand', br, '20%')}"
                            f"{circle_tile('Accessibility', ac, '15%')}"
                            f"{circle_tile('Content', co, '10%')}"
                            "</div>"
                            "</div>"
                        )
                        st.markdown(grid_html, unsafe_allow_html=True)

                        if compliance.get('final_recommendation'):
                            st.markdown("###### Recommendation")
                            rec_text = str(compliance.get('final_recommendation') or "").strip()
                            if rec_text:
                                # Styled recommendation card
                                rec_trim = rec_text if len(rec_text) <= 500 else (rec_text[:500] + " ...")
                                st.markdown(
                                    "<div style='padding:12px;border:1px solid #ffdede;border-radius:12px;"
                                    "background:#fff7f7;box-shadow:0 1px 6px rgba(241,90,107,0.12);'>"
                                    f"{html.escape(rec_trim)}"
                                    "</div>",
                                    unsafe_allow_html=True
                                )
                                if len(rec_text) > 500:
                                    with st.expander("Read full recommendation"):
                                        st.write(rec_text)

                        # Issues list (detailed)
                        st.markdown("###### Top Issues")
                        try:
                            issues_all = []
                            raw_issues = compliance.get("issues_json")
                            if isinstance(raw_issues, str) and raw_issues.strip():
                                issues_all = json.loads(raw_issues)
                            elif isinstance(raw_issues, list):
                                issues_all = raw_issues
                        except Exception:
                            issues_all = []
                        # Rank issues by severity
                        sev_rank = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}

                        def _rank(it):
                            return sev_rank.get(str(it.get("severity", "")).upper(), 99)

                        issues_sorted = sorted(issues_all, key=_rank)
                        top_issues = issues_sorted[:3]
                        more_count = max(0, len(issues_sorted) - 3)
                        if top_issues:
                            for issue in top_issues:
                                sev = str(issue.get('severity', '')).upper()
                                cat = str(issue.get('category', '-'))
                                desc = str(issue.get('issue', '-'))
                                reci = str(issue.get('recommendation', ''))
                                # severity pill color
                                color = "#d32f2f" if sev == "CRITICAL" else (
                                    "#e65100" if sev == "HIGH" else ("#f9a825" if sev == "MEDIUM" else "#2e7d32"))
                                pill = f"<span style='display:inline-block;padding:2px 8px;border-radius:999px;background:{color};color:#fff;font-size:12px;font-weight:700;'>{sev}</span>"
                                rec_block = ""
                                if reci:
                                    rec_block = (
                                        "<div style='margin-top:6px;color:#555'><b>Recommendation:</b> "
                                        f"{html.escape(reci)}</div>"
                                    )
                                st.markdown(
                                    "<div style='padding:10px;border:1px solid #eee;border-radius:10px;margin-bottom:8px;'>" +
                                    f"{pill} <span style='font-weight:600;margin-left:6px'>{html.escape(cat)}</span>" +
                                    f"<div style='margin-top:4px;color:#333'>{html.escape(desc)}</div>" +
                                    rec_block +
                                    "</div>",
                                    unsafe_allow_html=True
                                )
                            if more_count > 0:
                                st.caption(f"... and {more_count} more issues in UC")
                        if not top_issues:
                            st.write("No issues found.")

                        # Approval checklist for CRITICAL/HIGH issues
                        checklist = generate_approval_checklist_from_compliance(compliance)
                        st.markdown("###### Approval Checklist")
                        if checklist.get("total_items", 0) > 0:
                            df_chk = pd.DataFrame([
                                {
                                    "Assignee": it.get("assignee"),
                                    "Due Date": it.get("due_date"),
                                } for it in checklist.get("items", [])
                            ])
                            st.table(df_chk)
                        # else (removed)
                        #     st.write("No approvals required.")
                    # Approval workflow - standardized
                    approved = render_approval_section("Compliance", 4)
                    if approved:
                        st.session_state.workflow_state["compliance_approved"] = True
                        st.session_state.workflow_state["step"] = 4
                        st.rerun()
        
        # HANDOFF TAB
        with tabs[3]:
            st.subheader("🚀 Handoff & Go-Live")
            if not st.session_state.workflow_state.get("compliance_approved", False):
                st.warning("⚠️ Please get Compliance approval first before handoff.")
            else:
                # Get brief_id for contextualized handoff data
                brief_id = st.session_state.get("campaign_meta", {}).get("brief_id") or ""
                handoff_output = get_handoff_output({"brief_id": brief_id})
                data = handoff_output.get("output", {})
                
                status = str(data.get("readiness_status", "PENDING")).upper()
                ts = data.get("go_live_timestamp", "-")
                channels = data.get("channels", []) or []
                budget = data.get("budget_allocation", {}) or {}
                monitors = data.get("monitoring_metrics", []) or []
                assignees = data.get("assignees", {}) or {}

                # ========== STATUS + TIMELINE ==========
                # Status pill
                color = "#2e7d32" if status == "GO_LIVE" else ("#f9a825" if status == "PENDING" else "#d32f2f")
                status_text = "✅ Ready to Launch" if status == "GO_LIVE" else ("⏳ Pending Launch" if status == "PENDING" else "🚫 Blocked")
                st.markdown(
                    "<div style='display:inline-block;padding:6px 12px;border-radius:999px;"
                    f"background:{color};color:#fff;font-weight:700;font-size:14px;'>"
                    f"{status_text}</div>",
                    unsafe_allow_html=True
                )
                st.markdown(f"**Target Launch:** {ts}", unsafe_allow_html=True)
                st.divider()
                
                # ========== THREE-COLUMN LAYOUT ==========
                col_channels, col_budget, col_team = st.columns([1.2, 1, 1.3])
                
                # ===== LEFT: CHANNELS & MONITORING =====
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

                # ===== CENTER: BUDGET ALLOCATION =====
                with col_budget:
                    st.markdown("#### 💰 Budget Split")
                    if budget:
                        budget_data = [{"Channel": k.title(), "Allocation": v} for k, v in budget.items()]
                        df_budget = pd.DataFrame(budget_data)
                        st.dataframe(
                            df_budget,
                            use_container_width=True,
                            hide_index=True,
                            column_config={
                                "Channel": st.column_config.TextColumn(width="medium"),
                                "Allocation": st.column_config.TextColumn(width="small")
                            }
                        )
                        # Visual progress bars for budget
                        st.markdown("**Allocation Breakdown**")
                        for ch, pct in budget.items():
                            pct_num = float(pct.rstrip('%')) if isinstance(pct, str) else 0
                            st.progress(pct_num / 100, text=f"{ch.title()}: {pct}")
                    else:
                        st.write("—")

                # ===== RIGHT: TEAM ASSIGNMENTS =====
                with col_team:
                    st.markdown("#### 👥 Channel Owners")
                    if assignees:
                        for channel, owner in assignees.items():
                            # Extract role from owner (e.g., "Sarah Chen (Media)" → role="Media")
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

                # ========== PRE-LAUNCH CHECKLIST ==========
                st.markdown("#### ✓ Pre-Launch Checklist")
                checklist_items = [
                    ("Campaign assets approved & uploaded", True),
                    ("Tracking parameters configured", True),
                    ("Compliance notes shared with owners", True),
                    ("Team assignments confirmed", True),
                    ("Budget limits set in ad platforms", status == "GO_LIVE"),
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

                # ========== APPROVAL SECTION ==========
                approved = render_approval_section("Handoff", 5)
                if approved:
                    st.session_state.workflow_state["handoff_approved"] = True
                    st.session_state.workflow_state["step"] = 5
                    st.rerun()
        # ANALYSIS TAB
        with tabs[4]:
            st.subheader("📊 Campaign Performance Analysis")
            
            # Get brief_id for contextualized analysis data
            brief_id = st.session_state.get("campaign_meta", {}).get("brief_id") or ""
            try:
                importlib.reload(util)
            except Exception:
                pass
            analysis_output = util.get_analysis_output({"brief_id": brief_id})
            out = analysis_output.get("output", {})
            
            metrics = out.get("performance_metrics", []) or []
            findings = out.get("key_findings", []) or []
            next_brief = out.get("next_iteration_brief", {}) or {}

            if not metrics:
                st.info("📈 Performance analysis will be available after campaign launch.")
            else:
                # ========== HEADLINE METRICS ==========
                st.markdown("#### 📈 Key Performance Indicators")
                
                # Show top 3 metrics as big numbers
                if metrics:
                    try:
                        m1 = metrics[0]
                        m2 = metrics[1]
                        m3 = metrics[2]
                        
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            status_color = "#2e7d32" if "↑" in m1.get("status", "") else "#d32f2f"
                            st.markdown(
                                f"<div style='padding:16px;border-radius:12px;background:#fafafa;border:1px solid #eee;'>"
                                f"<div style='font-size:12px;color:#666;font-weight:600;margin-bottom:8px'>{html.escape(m1.get('metric', '-'))}</div>"
                                f"<div style='font-size:32px;font-weight:700;color:#1a1a1a'>{m1.get('value', 0):.2f}</div>"
                                f"<div style='font-size:13px;color:{status_color};font-weight:600;margin-top:8px'>{html.escape(m1.get('status', ''))}</div>"
                                f"<div style='font-size:11px;color:#999;margin-top:6px;line-height:1.4'>{html.escape(m1.get('context', ''))}</div>"
                                f"</div>",
                                unsafe_allow_html=True
                            )
                        
                        with col2:
                            status_color = "#2e7d32" if "↑" in m2.get("status", "") else "#d32f2f"
                            st.markdown(
                                f"<div style='padding:16px;border-radius:12px;background:#fafafa;border:1px solid #eee;'>"
                                f"<div style='font-size:12px;color:#666;font-weight:600;margin-bottom:8px'>{html.escape(m2.get('metric', '-'))}</div>"
                                f"<div style='font-size:32px;font-weight:700;color:#1a1a1a'>{m2.get('value', 0):.2f}</div>"
                                f"<div style='font-size:13px;color:{status_color};font-weight:600;margin-top:8px'>{html.escape(m2.get('status', ''))}</div>"
                                f"<div style='font-size:11px;color:#999;margin-top:6px;line-height:1.4'>{html.escape(m2.get('context', ''))}</div>"
                                f"</div>",
                                unsafe_allow_html=True
                            )
                        
                        with col3:
                            status_color = "#2e7d32" if "↑" in m3.get("status", "") else "#d32f2f"
                            st.markdown(
                                f"<div style='padding:16px;border-radius:12px;background:#fafafa;border:1px solid #eee;'>"
                                f"<div style='font-size:12px;color:#666;font-weight:600;margin-bottom:8px'>{html.escape(m3.get('metric', '-'))}</div>"
                                f"<div style='font-size:32px;font-weight:700;color:#1a1a1a'>{m3.get('value', 0):.2f}</div>"
                                f"<div style='font-size:13px;color:{status_color};font-weight:600;margin-top:8px'>{html.escape(m3.get('status', ''))}</div>"
                                f"<div style='font-size:11px;color:#999;margin-top:6px;line-height:1.4'>{html.escape(m3.get('context', ''))}</div>"
                                f"</div>",
                                unsafe_allow_html=True
                            )
                    except Exception as e:
                        st.warning(f"Could not display metrics: {e}")
            
                # Removed Performance vs Benchmark table per request
                st.divider()
            
                # ========== KEY FINDINGS ==========
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

                # ========== NEXT ITERATION RECOMMENDATIONS ==========
                st.markdown("#### 🚀 Next Iteration Recommendations")
                if isinstance(next_brief, dict) and next_brief:
                    col_left, col_right = st.columns([1.2, 1])
                    with col_left:
                        rec_html = "<div style='background:#f5f5f5;padding:14px;border-radius:10px;border:1px solid #e0e0e0;'>"
                        if next_brief.get("focus"):
                            rec_html += (
                                f"<div style='margin-bottom:12px;'>"
                                f"<div style='font-weight:600;color:#1a1a1a;font-size:12px;margin-bottom:4px'>📍 FOCUS</div>"
                                f"<div style='color:#333;font-size:13px;line-height:1.5'>{html.escape(str(next_brief.get('focus', '')))}</div>"
                                f"</div>"
                            )
                        if next_brief.get("creative_strategy"):
                            rec_html += (
                                f"<div style='margin-bottom:12px;'>"
                                f"<div style='font-weight:600;color:#1a1a1a;font-size:12px;margin-bottom:4px'>🎨 CREATIVE</div>"
                                f"<div style='color:#333;font-size:13px;line-height:1.5'>{html.escape(str(next_brief.get('creative_strategy', '')))}</div>"
                                f"</div>"
                            )
                        if next_brief.get("targeting_expansion"):
                            rec_html += (
                                f"<div style='margin-bottom:12px;'>"
                                f"<div style='font-weight:600;color:#1a1a1a;font-size:12px;margin-bottom:4px'>🎯 TARGETING</div>"
                                f"<div style='color:#333;font-size:13px;line-height:1.5'>{html.escape(str(next_brief.get('targeting_expansion', '')))}</div>"
                                f"</div>"
                            )
                        rec_html += "</div>"
                        st.markdown(rec_html, unsafe_allow_html=True)
                    with col_right:
                        if next_brief.get("recommended_budget_shift"):
                            budget_html = (
                                "<div style='background:#fff3e0;padding:14px;border-radius:10px;border:1px solid #ffe0b2;border-left:4px solid #f57c00;'>"
                                f"<div style='font-weight:600;color:#e65100;font-size:12px;margin-bottom:8px'>💰 BUDGET REALLOCATION</div>"
                                f"<div style='color:#333;font-size:13px;line-height:1.6;white-space:pre-wrap'>"
                                f"{html.escape(str(next_brief.get('recommended_budget_shift', '')))}"
                                f"</div>"
                                f"</div>"
                            )
                            st.markdown(budget_html, unsafe_allow_html=True)
                        if next_brief.get("timeline"):
                            timeline_html = (
                                "<div style='background:#e8f5e9;padding:14px;border-radius:10px;border:1px solid #c8e6c9;border-left:4px solid #2e7d32;margin-top:12px;'>"
                                f"<div style='font-weight:600;color:#2e7d32;font-size:12px;margin-bottom:6px'>⏱️ TIMELINE</div>"
                                f"<div style='color:#333;font-size:13px;'>{html.escape(str(next_brief.get('timeline', '')))}</div>"
                                f"</div>"
                            )
                            st.markdown(timeline_html, unsafe_allow_html=True)
                else:
                    st.write("—")

                st.divider()

                # ========== EXPORT / EXPORT SUMMARY ==========
                st.markdown("#### 📄 Campaign Summary")
                _next_text = ""
                try:
                    if isinstance(next_brief, dict):
                        _next_text = str(next_brief.get("focus") or next_brief.get("summary") or "")
                    else:
                        _next_text = str(next_brief or "")
                except Exception:
                    _next_text = ""
                summary_text = (
                    f"**Campaign:** {st.session_state.get('campaign_meta', {}).get('campaign_name', 'N/A')}\n\n"
                    f"**Performance Status:** {metrics[0].get('status', 'Pending') if metrics else 'N/A'}\n\n"
                    f"**Top Performer:** {metrics[0].get('metric', 'N/A') if metrics else 'N/A'}\n\n"
                    f"**Key Insight:** {findings[0] if findings else 'Pending analysis'}\n\n"
                    f"**Next Steps:** {(_next_text or 'Pending recommendations')[:100]}..."
                )
                st.info(summary_text)
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
                        scrolling=True
                    )
                else:
                    st.info("Set environment variable DATABRICKS_DASHBOARD_URL to embed your Databricks dashboard here.")


if __name__ == "__main__":
    main()
