"""Reusable prompt templates for LLM-powered assistant features."""

# ==========================================
# SECTION: Imports
# ==========================================
from __future__ import annotations


# ==========================================
# SECTION: Provider Routing
# ==========================================
# Prompt templates are provider-agnostic. Routing decisions are made in
# app.ai_hub.router after a prompt has been rendered.


# ==========================================
# SECTION: Prompt Templates
# ==========================================
CALL_SUMMARY_PROMPT = """
Summarize this banking sales call transcript.
Extract:
- customer requirement
- loan amount
- urgency
- objections
- next action
- sentiment
- callback date

Transcript:
{transcript}

Relevant historical memory:
{memory_context}
"""

NEXT_ACTION_PROMPT = """
You are advising a banking CRM agent on the next best action.
Use these facts:
- lead stage: {lead_stage}
- docs uploaded: {docs_uploaded}
- stale days: {stale_days}
- credit score: {credit_score}
- pending item: {pending_item}
- recommended rule action: {recommended_action}

Return short human-readable advice for the agent.

Relevant historical memory:
{memory_context}
"""

WHATSAPP_DRAFT_PROMPT = """
Draft a professional WhatsApp follow-up for a banking customer.
Use:
- customer name: {customer_name}
- loan type: {loan_type}
- pending docs: {pending_docs}
- next follow-up: {next_follow_up}
- tone: professional and helpful

Relevant previous interaction memory:
{memory_context}
"""

EMAIL_DRAFT_PROMPT = """
Draft a professional banking follow-up email.
Use:
- customer name: {customer_name}
- loan type: {loan_type}
- pending docs: {pending_docs}
- next follow-up: {next_follow_up}
- include a short subject line

Relevant previous interaction memory:
{memory_context}
"""

SMS_DRAFT_PROMPT = """
Draft a short SMS reminder for a banking customer.
Use:
- customer name: {customer_name}
- loan type: {loan_type}
- pending docs: {pending_docs}
- next follow-up: {next_follow_up}
Keep it concise and professional.

Relevant previous interaction memory:
{memory_context}
"""

REJECTION_EXPLANATION_PROMPT = """
Explain a banking loan rejection in borrower-friendly language.
Use:
- lender: {lender}
- FOIR: {foir}
- credit score: {credit_score}
- decision reason: {decision_reason}
- suggested next step: {next_step}

Avoid blame. Be clear and respectful.

Relevant historical memory:
{memory_context}
"""

BRANCH_REPORT_PROMPT = """
Write a short branch performance narrative report.
Use:
- branch name: {branch_name}
- conversion change: {conversion_change}
- lead volume: {lead_volume}
- sanction count: {sanction_count}
- fraud alerts: {fraud_alerts}
- focus area: {focus_area}

Keep the report concise and managerial.

Relevant business memory:
{memory_context}
"""


class PromptManager:
    """Centralized prompt formatter for all Phase 7 assistant tasks."""

    PROMPTS = {
        "call_summary": CALL_SUMMARY_PROMPT,
        "next_action": NEXT_ACTION_PROMPT,
        "whatsapp_draft": WHATSAPP_DRAFT_PROMPT,
        "email_draft": EMAIL_DRAFT_PROMPT,
        "sms_draft": SMS_DRAFT_PROMPT,
        "rejection_explanation": REJECTION_EXPLANATION_PROMPT,
        "branch_report": BRANCH_REPORT_PROMPT,
    }

    @classmethod
    def render(cls, prompt_key: str, **kwargs) -> str:
        """Render a prompt template with runtime values."""
        template = cls.PROMPTS.get(prompt_key)
        if template is None:
            raise ValueError(f"Unknown prompt key: {prompt_key}")
        return template.format(**kwargs)


# ==========================================
# SECTION: Assistant Logic
# ==========================================
# PromptManager is used by service classes to produce provider-ready
# prompts without duplicating instruction text.
