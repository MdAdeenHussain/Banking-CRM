"""Dashboard route controllers for role-based screens."""

# =====================================
# SECTION: Imports
# =====================================
from flask import Blueprint, render_template
from flask_login import current_user, login_required

from app.decorators import role_required
from app.fraud_ai.alert_service import FraudAlertService
from app.services.dashboard_kpi_service import DashboardKPIService


# =====================================
# SECTION: Blueprint Definition
# =====================================
dashboard_bp = Blueprint("dashboard", __name__)


# =====================================
# SECTION: Dashboard Routes
# =====================================
@dashboard_bp.get("/dashboard/owner")
@role_required("owner", "platform")
def owner_dashboard():
    kpis = DashboardKPIService(tenant_id=current_user.tenant_id).get_owner_kpis()
    from app.ai_hub.assistant_service import AssistantService
    from app.ai_hub.report_generator import ReportGenerator
    from app.rag_engine.case_similarity_service import CaseSimilarityService
    from app.rag_engine.prompt_context_builder import PromptContextBuilder

    branch_report = ReportGenerator().generate_owner_report(
        {
            "branch_name": "Network Overview",
            "conversion_change": f"{kpis.get('conversions', 0)}%",
            "lead_volume": kpis.get("total_leads", 0),
            "sanction_count": kpis.get("applications", 0),
            "fraud_alerts": kpis.get("fraud_alerts", 0),
            "focus_area": "improve disbursal conversion and document turnaround",
        },
        tenant_id=current_user.tenant_id,
    )
    rejection_insight = AssistantService().explain_rejection(
        {
            "lender": "Preferred lender panel",
            "foir": 53,
            "credit_score": 662,
            "decision_reason": "FOIR exceeds current lender threshold and bureau score is borderline.",
            "next_step": "reduce obligations or consider a secured product before reapplying",
        },
        tenant_id=current_user.tenant_id,
    )
    similarity_service = CaseSimilarityService()
    similar_cases = similarity_service.find_similar_loan_cases(
        "home loan rejected due to FOIR and bureau score",
        tenant_id=current_user.tenant_id,
        top_k=3,
    )
    fraud_memory = similarity_service.find_similar_fraud_cases(
        "salary mismatch metadata anomaly duplicate PAN",
        tenant_id=current_user.tenant_id,
        top_k=3,
    )
    lender_memory = PromptContextBuilder().build_context(
        "best lender rule for fast approval and easy documentation",
        tenant_id=current_user.tenant_id,
        top_k=3,
        namespaces=["lender_rules", "historical_applications"],
    )
    return render_template(
        "dashboard/owner_dashboard.html",
        kpis=kpis,
        ai_branch_report=branch_report,
        ai_rejection_insight=rejection_insight,
        similar_cases=similar_cases,
        fraud_memory=fraud_memory,
        lender_memory=lender_memory,
    )


@dashboard_bp.get("/dashboard/branch")
@role_required("branch", "owner", "platform")
def branch_dashboard():
    kpis = DashboardKPIService(tenant_id=current_user.tenant_id).get_branch_kpis(branch_name=current_user.name)
    from app.ai_hub.report_generator import ReportGenerator
    from app.rag_engine.case_similarity_service import CaseSimilarityService
    from app.rag_engine.prompt_context_builder import PromptContextBuilder

    ai_branch_report = ReportGenerator().generate_branch_report(
        {
            "branch_name": current_user.name,
            "conversion_change": f"{kpis.get('conversions', 0)}%",
            "lead_volume": kpis.get("total_leads", 0),
            "sanction_count": kpis.get("applications", 0),
            "fraud_alerts": kpis.get("fraud_alerts", 0),
            "focus_area": "reduce stale leads and accelerate lender submissions",
        },
        tenant_id=current_user.tenant_id,
    )
    case_service = CaseSimilarityService()
    similar_cases = case_service.find_similar_loan_cases(
        "docs pending personal loan with medium credit score",
        tenant_id=current_user.tenant_id,
        top_k=3,
    )
    lender_memory = PromptContextBuilder().build_context(
        "lender memory for fast branch disbursal and easier documentation",
        tenant_id=current_user.tenant_id,
        top_k=3,
        namespaces=["lender_rules", "historical_applications"],
    )
    return render_template(
        "dashboard/branch_dashboard.html",
        kpis=kpis,
        ai_branch_report=ai_branch_report,
        similar_cases=similar_cases,
        lender_memory=lender_memory,
    )


@dashboard_bp.get("/dashboard/agent")
@role_required("agent", "branch", "owner", "platform")
def agent_dashboard():
    kpis = DashboardKPIService(tenant_id=current_user.tenant_id).get_agent_kpis(agent_name=current_user.name)
    from app.ai_hub.next_action_service import NextActionService
    from app.rag_engine.case_similarity_service import CaseSimilarityService

    ai_next_action = NextActionService().recommend(
        {
            "lead_stage": "DOCS_PENDING",
            "docs_uploaded": False,
            "stale_days": 4,
            "credit_score": 648,
            "pending_item": "salary slip and bank statement",
            "customer_name": current_user.name,
        },
        tenant_id=current_user.tenant_id,
    )
    similar_cases = CaseSimilarityService().find_similar_loan_cases(
        "docs pending case with callback delay and borderline credit score",
        tenant_id=current_user.tenant_id,
        top_k=3,
    )
    return render_template(
        "dashboard/agent_dashboard.html",
        kpis=kpis,
        ai_next_action=ai_next_action,
        similar_cases=similar_cases,
    )


@dashboard_bp.get("/dashboard/calls")
@login_required
def calls_dashboard():
    from app.ai_hub.call_summary_service import CallSummaryService
    from app.ai_hub.message_draft_service import MessageDraftService
    from app.rag_engine.prompt_context_builder import PromptContextBuilder

    transcript = (
        "Customer needs a home loan of INR 500000 and wants fast processing. "
        "They are concerned about EMI and asked for a callback tomorrow."
    )
    ai_call_summary = CallSummaryService().summarize_call(
        transcript,
        tenant_id=current_user.tenant_id,
    )
    ai_whatsapp_draft = MessageDraftService().draft_whatsapp(
        {
            "customer_name": "Rahul",
            "loan_type": "home loan",
            "pending_docs": "salary slip and bank statement",
            "next_follow_up": "tomorrow",
        },
        tenant_id=current_user.tenant_id,
    )
    interaction_memory = PromptContextBuilder().build_context(
        transcript,
        tenant_id=current_user.tenant_id,
        top_k=3,
        namespaces=["call_transcripts", "historical_applications", "rejections"],
    )
    return render_template(
        "dashboard/calls_dashboard.html",
        ai_call_summary=ai_call_summary,
        ai_whatsapp_draft=ai_whatsapp_draft,
        interaction_memory=interaction_memory,
    )


@dashboard_bp.get("/dashboard/platform")
@role_required("platform", "owner")
def platform_dashboard():
    kpis = DashboardKPIService(tenant_id=current_user.tenant_id).get_owner_kpis()
    alert_service = FraudAlertService(current_user.tenant_id)
    alerts = alert_service.serialize_alerts(alert_service.list_alerts(limit=5))
    return render_template(
        "dashboard/platform_dashboard.html",
        kpis=kpis,
        fraud_alerts_feed=alerts,
    )
