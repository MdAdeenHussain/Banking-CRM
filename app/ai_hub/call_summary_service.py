"""Call transcript summarization service."""

# ==========================================
# SECTION: Imports
# ==========================================
from __future__ import annotations

import re
from typing import Any

from app.ai_hub.assistant_service import AssistantService


# ==========================================
# SECTION: Provider Routing
# ==========================================
# Call transcripts often contain customer context and are treated as
# sensitive by default, which routes them to local providers first.


# ==========================================
# SECTION: Prompt Templates
# ==========================================
# Prompt rendering is delegated to AssistantService + PromptManager.


# ==========================================
# SECTION: Assistant Logic
# ==========================================
class CallSummaryService:
    """Summarizes call transcripts and extracts structured details."""

    AMOUNT_REGEX = re.compile(r"(?:rs\.?|inr)?\s*([0-9][0-9,]{4,})", re.IGNORECASE)
    DATE_REGEX = re.compile(
        r"(tomorrow|today|monday|tuesday|wednesday|thursday|friday|saturday|sunday|\d{1,2}/\d{1,2}/\d{2,4})",
        re.IGNORECASE,
    )

    def __init__(self) -> None:
        self.assistant = AssistantService()

    def summarize_call(self, transcript: str, *, tenant_id: int | None = None) -> dict[str, Any]:
        """Summarize long transcript with structured field extraction."""
        lower_text = (transcript or "").lower()
        amount = self._extract_amount(transcript)
        urgency = self._extract_urgency(lower_text)
        objections = self._extract_objections(lower_text)
        callback_date = self._extract_callback_date(transcript)
        sentiment = self._extract_sentiment(lower_text)
        next_action = self._extract_next_action(lower_text, objections)
        requirement = self._extract_requirement(transcript)

        narrative = self.assistant.generate_text(
            task_type="call_summary",
            prompt_key="call_summary",
            prompt_values={"transcript": transcript or "No transcript provided."},
            sensitive=True,
            tenant_id=tenant_id,
            memory_query=transcript or "customer discussion about loan follow-up",
            memory_namespaces=["call_transcripts", "historical_applications", "rejections"],
        )

        return {
            "summary": narrative["content"],
            "customer_requirement": requirement,
            "amount": amount,
            "urgency": urgency,
            "objections": objections,
            "next_action": next_action,
            "sentiment": sentiment,
            "callback_date": callback_date,
            "provider": narrative["provider"],
            "model": narrative["model"],
            "memory_context": narrative["memory_context"],
            "retrieved_items": narrative["retrieved_items"],
        }

    def _extract_amount(self, transcript: str) -> int | None:
        match = self.AMOUNT_REGEX.search(transcript or "")
        if not match:
            return None
        return int(match.group(1).replace(",", ""))

    def _extract_urgency(self, lower_text: str) -> str:
        if any(word in lower_text for word in ["urgent", "immediately", "asap", "today"]):
            return "high"
        if any(word in lower_text for word in ["this week", "soon", "priority"]):
            return "medium"
        return "low"

    def _extract_objections(self, lower_text: str) -> list[str]:
        objections = []
        if "emi" in lower_text:
            objections.append("emi concern")
        if "rate" in lower_text or "interest" in lower_text:
            objections.append("interest rate concern")
        if "document" in lower_text or "docs" in lower_text:
            objections.append("document readiness concern")
        return objections

    def _extract_callback_date(self, transcript: str) -> str | None:
        match = self.DATE_REGEX.search(transcript or "")
        return match.group(1) if match else None

    def _extract_sentiment(self, lower_text: str) -> str:
        if any(word in lower_text for word in ["happy", "interested", "good", "proceed"]):
            return "positive"
        if any(word in lower_text for word in ["concern", "issue", "problem", "delay"]):
            return "mixed"
        return "neutral"

    def _extract_next_action(self, lower_text: str, objections: list[str]) -> str:
        if "document readiness concern" in objections:
            return "collect pending documents"
        if "emi concern" in objections:
            return "share lower-emi options"
        if "call back" in lower_text or "callback" in lower_text:
            return "follow-up on requested callback slot"
        return "send lender shortlist and follow up"

    def _extract_requirement(self, transcript: str) -> str:
        lines = [line.strip() for line in (transcript or "").splitlines() if line.strip()]
        if not lines:
            return "customer requirement not clearly stated"
        return lines[0][:180]
