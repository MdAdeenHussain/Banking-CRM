"""Automation engine package exports.

Phase 10 centralizes workflow orchestration, communications, scheduling,
campaign attribution, and notification rules in this package.
"""

# ==========================================
# SECTION: Workflow Rules
# ==========================================
from app.automation_engine.campaign_attribution_service import CampaignAttributionService
from app.automation_engine.communication_service import CommunicationService
from app.automation_engine.meta_tracking_service import MetaTrackingService
from app.automation_engine.notification_rules import NotificationRulesEngine
from app.automation_engine.scheduler_service import SchedulerService
from app.automation_engine.workflow_engine import WorkflowEngine


# ==========================================
# SECTION: Communication
# ==========================================
# Communication helpers are exported for reuse across services and tasks.


# ==========================================
# SECTION: Scheduling
# ==========================================
# SchedulerService handles callback and follow-up timing metadata.


# ==========================================
# SECTION: Tracking
# ==========================================
__all__ = [
    "WorkflowEngine",
    "CommunicationService",
    "SchedulerService",
    "MetaTrackingService",
    "CampaignAttributionService",
    "NotificationRulesEngine",
]
