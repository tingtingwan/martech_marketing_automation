import os
import time
import json
import threading
from typing import Optional, Dict, Any, List

import streamlit as st  # type: ignore
from databricks.sdk.core import Config  # type: ignore


DEBUG_UC = (os.environ.get("UC_DEBUG", "false") or "").lower() in ("1", "true", "yes", "on")


def normalize_brief(brief: dict, defaults: dict) -> dict:
    return {
        "type": brief.get("type") or defaults.get("type"),
        "audience": brief.get("audience") or defaults.get("audience"),
        "budget": brief.get("budget") if brief.get("budget") not in (None, "", 0) else defaults.get("budget"),
        "timeline": brief.get("timeline") or defaults.get("timeline"),
        "brief": brief.get("brief") or defaults.get("brief"),
    }


def get_handoff_output(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Returns realistic handoff data for demo purposes.
    Includes go-live plan, channels, budget allocation, and monitoring metrics.
    """
    
    campaign_brief_id = params.get("brief_id", "brief_001")
    
    # Campaign-specific handoff data
    handoff_config = {
        "brief_001": {
            "readiness_status": "GO_LIVE",
            "go_live_timestamp": "2025-01-15T08:00:00Z",
            "channels": ["Instagram", "Facebook", "TikTok", "Google Ads"],
            "budget_allocation": {
                "instagram": "35%",
                "facebook": "30%",
                "tiktok": "20%",
                "google_ads": "15%"
            },
            "monitoring_metrics": [
                "CTR (Target: >1.2%)",
                "Conversion Rate (Target: >4.5%)",
                "ROAS (Target: >3.5x)",
                "Cost per Install (Target: <$2.50)",
                "User Retention Day 7 (Target: >40%)"
            ],
            "assignees": {
                "instagram": "Sarah Chen (Media)",
                "facebook": "Alex Novak (Paid Social)",
                "tiktok": "Priya Patel (Creator Partnerships)",
                "google_ads": "Mark Li (Search)"
            },
            "campaign_assets_ready": True,
            "tracking_configured": True,
            "stakeholders_notified": True
        },
        "brief_002": {
            "readiness_status": "GO_LIVE",
            "go_live_timestamp": "2025-01-22T10:00:00Z",
            "channels": ["Email", "Instagram", "Facebook", "Tiktok"],
            "budget_allocation": {
                "email": "25%",
                "instagram": "40%",
                "facebook": "20%",
                "tiktok": "15%"
            },
            "monitoring_metrics": [
                "Email Open Rate (Target: >28%)",
                "Click-through Rate (Target: >3.5%)",
                "Conversion Rate (Target: >6.2%)",
                "ROAS (Target: >4.0x)",
                "Customer Lifetime Value (Target: >$185)"
            ],
            "assignees": {
                "email": "Emma Davis (CRM)",
                "instagram": "Alex Novak (Paid Social)",
                "facebook": "Jamie Wright (Paid Social)",
                "Tiktok": "Linda Gómez (Creative Ops)"
            },
            "campaign_assets_ready": True,
            "tracking_configured": True,
            "stakeholders_notified": True
        },
        "brief_003": {
            "readiness_status": "PENDING",
            "go_live_timestamp": "2025-02-05T09:00:00Z",
            "channels": ["Instagram", "Facebook", "YouTube", "Search Ads"],
            "budget_allocation": {
                "instagram": "30%",
                "facebook": "25%",
                "youtube": "25%",
                "search_ads": "20%"
            },
            "monitoring_metrics": [
                "View-through Rate (Target: >2.1%)",
                "Engagement Rate (Target: >5.8%)",
                "Conversion Rate (Target: >5.0%)",
                "ROAS (Target: >3.2x)",
                "Video Completion Rate (Target: >65%)"
            ],
            "assignees": {
                "instagram": "Mina Rao (Paid Social)",
                "facebook": "Jamie Wright (Paid Social)",
                "youtube": "Chris Park (Video)",
                "search_ads": "Mark Li (Search)"
            },
            "campaign_assets_ready": False,
            "tracking_configured": True,
            "stakeholders_notified": False
        }
    }
    
    # Get config for this campaign, or use brief_001 as fallback
    config = handoff_config.get(campaign_brief_id, handoff_config["brief_001"])
    
    return {
        "output": {
            "readiness_status": config["readiness_status"],
            "go_live_timestamp": config["go_live_timestamp"],
            "channels": config["channels"],
            "budget_allocation": config["budget_allocation"],
            "monitoring_metrics": config["monitoring_metrics"],
            "assignees": config.get("assignees", {}),
            "campaign_assets_ready": config["campaign_assets_ready"],
            "tracking_configured": config["tracking_configured"],
            "stakeholders_notified": config["stakeholders_notified"],
        }
    }


def get_analysis_output(params: dict) -> dict:
    """
    Returns realistic campaign performance analysis.
    Data varies by campaign lifecycle stage and type.
    """
    brief_id = params.get("brief_id") or ""
    
    # Campaign-specific performance scenarios
    analysis_scenarios = {
        "brief_001": {  # Women's Health Awareness - Acquisition
            "performance_metrics": [
                {
                    "metric": "Click-Through Rate",
                    "value": 1.42,
                    "benchmark": 1.2,
                    "status": "↑ +18%",
                    "context": "Above industry average for health apps"
                },
                {
                    "metric": "Cost Per Install",
                    "value": 2.15,
                    "benchmark": 2.5,
                    "status": "↓ -14%",
                    "context": "Better than benchmark, efficient spend"
                },
                {
                    "metric": "7-Day Retention",
                    "value": 48.3,
                    "benchmark": 45.0,
                    "status": "↑ +7.3%",
                    "context": "Strong early engagement signals"
                },
                {
                    "metric": "Install Volume",
                    "value": 12450,
                    "benchmark": 10000,
                    "status": "↑ +24.5%",
                    "context": "Exceeded initial targets"
                },
                {
                    "metric": "Cost Per Mille (CPM)",
                    "value": 8.75,
                    "benchmark": 9.2,
                    "status": "↓ -5%",
                    "context": "Efficient media buying"
                }
            ],
            "key_findings": [
                "Instagram and TikTok driving 68% of installs (highest ROI channels)",
                "Video creative (20s) outperforms carousel ads by 34%",
                "Women 25-30 segment shows 42% higher LTV than 18-24",
                "Peak engagement occurs Tuesday-Thursday, 7-9 PM",
                "User flow optimization increased conversion by 12%"
            ],
            "next_iteration_brief": {
                "focus": "Scale winning creative + expand to lookalike audiences",
                "recommended_budget_shift": "Increase TikTok from 30% → 40%, reduce Tiktok 10% → 5%",
                "creative_strategy": "Test 15s vertical format, double down on educational content",
                "targeting_expansion": "Expand to +35 segment, test interest overlap with wellness apps",
                "timeline": "Week 3-4 of campaign"
            }
        },
        "brief_002": {  # Menopause Support - Retention
            "performance_metrics": [
                {
                    "metric": "Email Open Rate",
                    "value": 28.5,
                    "benchmark": 25.0,
                    "status": "↑ +14%",
                    "context": "Strong subject line performance"
                },
                {
                    "metric": "In-App Engagement",
                    "value": 3.2,
                    "benchmark": 2.5,
                    "status": "↑ +28%",
                    "context": "Users spending more time with features"
                },
                {
                    "metric": "Re-activation Rate",
                    "value": 18.7,
                    "benchmark": 12.0,
                    "status": "↑ +56%",
                    "context": "Win-back campaign highly effective"
                },
                {
                    "metric": "Customer Lifetime Value (CLTV)",
                    "value": 245.80,
                    "benchmark": 180.0,
                    "status": "↑ +36.5%",
                    "context": "Retention strategy improving LTV significantly"
                },
                {
                    "metric": "Churn Rate",
                    "value": 4.2,
                    "benchmark": 6.5,
                    "status": "↓ -35%",
                    "context": "Lower than expected churn"
                }
            ],
            "key_findings": [
                "Educational content (expert Q&A) drives 2.8x higher engagement than promotional",
                "Email cadence of 2x/week optimal; 3x/week shows 15% increase in unsubscribes",
                "In-app feature adoption: 67% users access community, 54% use symptom tracker",
                "Retention cohort from menopause content shows 23% higher LTV",
                "Personalized recommendations increase session length by 34%"
            ],
            "next_iteration_brief": {
                "focus": "Deepen engagement through community features + expert partnerships",
                "recommended_budget_shift": "Reallocate 10% from Facebook to in-app experience improvements",
                "creative_strategy": "Feature community stories, expert testimonials, symptom management tools",
                "targeting_expansion": "Expand to perimenopause audience (40-45), partner with OB-GYN practices",
                "timeline": "Weeks 5-8 of campaign"
            }
        },
        "brief_003": {  # Pregnancy Planning - Engagement
            "performance_metrics": [
                {
                    "metric": "Video Completion Rate",
                    "value": 67.8,
                    "benchmark": 60.0,
                    "status": "↑ +13%",
                    "context": "Strong video content performance"
                },
                {
                    "metric": "Email Signup Rate",
                    "value": 8.4,
                    "benchmark": 6.5,
                    "status": "↑ +29%",
                    "context": "Educational series converting well"
                },
                {
                    "metric": "Content Engagement Rate",
                    "value": 4.6,
                    "benchmark": 3.2,
                    "status": "↑ +44%",
                    "context": "Educational focus resonates"
                },
                {
                    "metric": "Series Completion Rate",
                    "value": 72.5,
                    "benchmark": 55.0,
                    "status": "↑ +32%",
                    "context": "High interest in educational journey"
                },
                {
                    "metric": "Social Share Rate",
                    "value": 12.3,
                    "benchmark": 8.0,
                    "status": "↑ +54%",
                    "context": "Highly shareable content"
                }
            ],
            "key_findings": [
                "YouTube channel driving 89% of views and 92% of email signups",
                "3-part educational series on pregnancy timeline most popular (145K views)",
                "Audience age: 28-35 shows 3.2x higher engagement than 25-28",
                "Instagram carousel posts (timeline infographics) get 4.8x more saves",
                "Content about 'what to expect' generates 2.1x more comments than symptom posts"
            ],
            "next_iteration_brief": {
                "focus": "Expand educational video series + build community around journey",
                "recommended_budget_shift": "Increase YouTube from 35% → 45%, reduce TikTok 15% → 8%",
                "creative_strategy": "Launch 'Your Pregnancy Timeline' video series (8 episodes), add expert interviews",
                "targeting_expansion": "Add couples demographic, women planning pregnancy (no current pregnancy)",
                "timeline": "Weeks 6-10 of campaign"
            }
        }
    }
    
    # Get scenario for the brief
    scenario = analysis_scenarios.get(brief_id, analysis_scenarios.get("brief_001"))
    
    return {
        "output": {
            "performance_metrics": scenario.get("performance_metrics", []),
            "key_findings": scenario.get("key_findings", []),
            "next_iteration_brief": scenario.get("next_iteration_brief", {})
        }
    }

def get_databricks_connection():
    try:
        from databricks import sql  # type: ignore
    except Exception as e:
        st.error(f"❌ databricks-sql-connector not available: {e}")
        return None
    try:
        cfg = Config()
        warehouse_id = os.environ.get("DATABRICKS_WAREHOUSE_ID") or os.environ.get("SQL_WAREHOUSE_ID")
        if not warehouse_id:
            st.error("❌ DATABRICKS_WAREHOUSE_ID (or SQL_WAREHOUSE_ID) not set")
            return None
        if DEBUG_UC:
            st.write({
                "uc_debug": True,
                "warehouse_var_used": "DATABRICKS_WAREHOUSE_ID" if os.environ.get("DATABRICKS_WAREHOUSE_ID") else "SQL_WAREHOUSE_ID",
                "warehouse_id_set": bool(warehouse_id),
                "server_hostname_set": bool(cfg.host),
                "http_path_preview": f"/sql/1.0/warehouses/{warehouse_id[:6]}...{warehouse_id[-4:]}"
            })
        connection = sql.connect(
            server_hostname=cfg.host,
            http_path=f"/sql/1.0/warehouses/{warehouse_id}",
            credentials_provider=lambda: cfg.authenticate
        )
        return connection
    except Exception as e:
        st.error(f"❌ Connection failed: {e}")
        return None


@st.cache_data(ttl=300, show_spinner=False)
def get_compliance_from_uc(brief_id: str) -> Dict[str, Any]:
    try:
        logs: List[str] = []
        t0 = time.time()
        conn = get_databricks_connection()
        if not conn:
            return {}
        try:
            cursor = conn.cursor()
            if DEBUG_UC:
                logs.append("cursor_opened")
                try:
                    cursor.execute("SELECT 1")
                    _ = cursor.fetchone()
                    logs.append("select_1_ok")
                except Exception as e:
                    logs.append(f"select_1_failed:{e}")
            cursor.execute(
                """
                SELECT 
                    brief_id, campaign_name, medical_legal_score, privacy_score,
                    brand_score, accessibility_score, content_score, overall_score,
                    approval_status, final_recommendation, reviewed_at, reviewed_by,
                    confidence_score, issues_json, issue_count, critical_count, high_count
                FROM flo_martech.compliance_decisions
                WHERE brief_id = ?
                ORDER BY reviewed_at DESC
                LIMIT 1
                """,
                (brief_id,)
            )
            result = cursor.fetchone()
            if DEBUG_UC:
                logs.append(f"fetchone_done:{'hit' if bool(result) else 'miss'}")
        finally:
            try:
                cursor.close()
            except Exception:
                pass
            try:
                conn.close()
            except Exception:
                pass
        if not result:
            if DEBUG_UC:
                st.write({"uc_fetch_ms": int((time.time()-t0)*1000), "debug": logs, "brief_id": brief_id})
            return {}
        (
            r_brief_id, r_campaign_name, r_med, r_priv, r_brand, r_acc, r_content,
            r_overall, r_status, r_reco, r_reviewed_at, r_reviewed_by,
            r_conf, r_issues_json, r_issue_count, r_critical_count, r_high_count
        ) = result
        out = {
            "status": "success",
            "brief_id": r_brief_id,
            "campaign_name": r_campaign_name,
            "medical_legal_score": float(r_med or 0),
            "privacy_score": float(r_priv or 0),
            "brand_score": float(r_brand or 0),
            "accessibility_score": float(r_acc or 0),
            "content_score": float(r_content or 0),
            "overall_score": float(r_overall or 0),
            "approval_status": r_status or "PENDING",
            "final_recommendation": r_reco,
            "reviewed_at": r_reviewed_at,
            "reviewed_by": r_reviewed_by,
            "confidence_score": float(r_conf or 0.0),
            "issues_json": r_issues_json,
            "issue_count": int(r_issue_count or 0),
            "critical_count": int(r_critical_count or 0),
            "high_count": int(r_high_count or 0)
        }
        if DEBUG_UC:
            out["_uc_fetch_ms"] = int((time.time()-t0)*1000)
            out["_debug"] = logs
            st.write({"uc_fetch_ms": out["_uc_fetch_ms"], "debug": logs})
        return out
    except Exception as e:
        st.error(f"❌ Error reading UC compliance: {e}")
        return {}


def _run_with_timeout(fn, args=(), kwargs=None, timeout: int = 8):
    kwargs = kwargs or {}
    result_holder: Dict[str, Any] = {}
    error_holder: Dict[str, Any] = {}

    def _target():
        try:
            result_holder["value"] = fn(*args, **kwargs)
        except Exception as e:
            error_holder["error"] = e

    t = threading.Thread(target=_target, daemon=True)
    t.start()
    t.join(timeout)
    if t.is_alive():
        return {"_timeout": True}
    if "error" in error_holder:
        raise error_holder["error"]
    return result_holder.get("value")


def get_compliance_from_uc_timeout(brief_id: str, timeout: int = 8) -> Dict[str, Any]:
    res = _run_with_timeout(get_compliance_from_uc, args=(brief_id,), timeout=timeout)
    if isinstance(res, dict) and res.get("_timeout"):
        if DEBUG_UC:
            st.write({"uc_timeout_s": timeout, "brief_id": brief_id})
        return {"status": "error", "message": f"UC fetch timed out after {timeout}s"}
    return res or {}


@st.cache_data(ttl=300, show_spinner=False)
def get_compliance_history_from_uc(brief_id: str, limit: int = 5):
    try:
        conn = get_databricks_connection()
        if not conn:
            return []
        try:
            cursor = conn.cursor()
            cursor.execute(
                f"""
                SELECT *
                FROM flo_martech.compliance_decisions
                WHERE brief_id = ?
                ORDER BY reviewed_at DESC
                LIMIT {int(limit)}
                """,
                (brief_id,)
            )
            rows = cursor.fetchall()
            colnames = [d[0] for d in cursor.description] if cursor.description else []
        finally:
            try:
                cursor.close()
            except Exception:
                pass
            try:
                conn.close()
            except Exception:
                pass
        results = []
        for r in rows or []:
            try:
                results.append({colnames[i]: r[i] for i in range(len(colnames))})
            except Exception:
                pass
        return results
    except Exception as e:
        st.warning(f"UC history query failed: {e}")
        return []


def get_assignee_for_category(category: str) -> str:
    mapping = {
        "Medical/Legal": "legal_team",
        "Medical/Legal Compliance": "legal_team",
        "Privacy": "privacy_team",
        "Privacy & Data Protection": "privacy_team",
        "Brand": "brand_team",
        "Brand Guidelines": "brand_team",
        "Accessibility": "qa_team",
        "Content": "content_team",
        "Content Quality": "content_team",
    }
    return mapping.get(str(category), "compliance_team")


def generate_approval_checklist_from_compliance(compliance: Dict[str, Any]) -> Dict[str, Any]:
    try:
        issues_all = []
        raw_issues = compliance.get("issues_json")
        if isinstance(raw_issues, str) and raw_issues.strip():
            issues_all = json.loads(raw_issues)
        elif isinstance(raw_issues, list):
            issues_all = raw_issues
    except Exception:
        issues_all = []
    critical_high = [
        i for i in (issues_all or [])
        if str(i.get("severity", "")).upper() in ("CRITICAL", "HIGH")
    ]
    items = []
    for issue in critical_high:
        cat = issue.get("category")
        items.append({
            "category": cat,
            "issue": issue.get("issue"),
            "severity": str(issue.get("severity", "")).upper(),
            "recommendation": issue.get("recommendation"),
            "assignee": get_assignee_for_category(cat),
            "status": "pending_approval",
            "due_date": time.strftime("%Y-%m-%dT%H:%M:%S")
        })
    return {
        "brief_id": compliance.get("brief_id"),
        "campaign_name": compliance.get("campaign_name"),
        "total_items": len(items),
        "items": items
    }


@st.cache_data(ttl=300, show_spinner=False)
def get_generated_image_b64_from_uc(brief_id: str) -> Optional[str]:
    try:
        conn = get_databricks_connection()
        if not conn:
            return None
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT generated_image_b64
                FROM flo_martech.generated_creatives
                WHERE brief_id = ?
                ORDER BY generation_timestamp DESC
                LIMIT 1
                """,
                (brief_id,)
            )
            row = cursor.fetchone()
        finally:
            try:
                cursor.close()
            except Exception:
                pass
            try:
                conn.close()
            except Exception:
                pass
        if row and row[0]:
            return row[0]
        return None
    except Exception as e:
        if DEBUG_UC:
            st.write({"generated_image_fetch_error": str(e)})
        return None

