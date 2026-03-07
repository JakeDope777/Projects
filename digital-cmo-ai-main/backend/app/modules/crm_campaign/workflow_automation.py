"""
Workflow Automation Engine

Provides a rich library of pre-built marketing automation sequences and an
engine to execute them. Supports event-triggered workflows, conditional
branching, time-based delays, and multi-channel actions.

Pre-built sequences:
- Welcome / Onboarding series
- Re-engagement / Win-back
- Lead nurture (standard, accelerated)
- Upsell / Cross-sell
- Event-triggered (cart abandonment, pricing page, trial expiry)
- Post-purchase follow-up
- Referral programme
- Feedback / NPS collection
"""

import uuid
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional
from enum import Enum

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Enums & constants
# ---------------------------------------------------------------------------

class WorkflowStatus(str, Enum):
    PENDING = "pending"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ERROR = "error"


class ActionType(str, Enum):
    SEND_EMAIL = "send_email"
    SEND_SMS = "send_sms"
    SEND_PUSH = "send_push_notification"
    ADD_TAG = "add_tag"
    REMOVE_TAG = "remove_tag"
    UPDATE_FIELD = "update_field"
    UPDATE_STATUS = "update_status"
    UPDATE_SCORE = "update_score"
    CHECK_ENGAGEMENT = "check_engagement"
    CHECK_ACTIVITY = "check_activity"
    CHECK_CONDITION = "check_condition"
    WAIT = "wait"
    BRANCH = "branch"
    NOTIFY_SALES = "notify_sales"
    NOTIFY_TEAM = "notify_team"
    ADD_TO_SEGMENT = "add_to_segment"
    REMOVE_FROM_SEGMENT = "remove_from_segment"
    TRIGGER_WEBHOOK = "trigger_webhook"
    ENROL_WORKFLOW = "enrol_workflow"


class TriggerType(str, Enum):
    MANUAL = "manual"
    LEAD_CREATED = "lead_created"
    LEAD_UPDATED = "lead_updated"
    SCORE_THRESHOLD = "score_threshold"
    TAG_ADDED = "tag_added"
    FORM_SUBMITTED = "form_submitted"
    PAGE_VISITED = "page_visited"
    EMAIL_OPENED = "email_opened"
    EMAIL_CLICKED = "email_clicked"
    CART_ABANDONED = "cart_abandoned"
    TRIAL_STARTED = "trial_started"
    TRIAL_EXPIRING = "trial_expiring"
    PURCHASE_MADE = "purchase_made"
    INACTIVITY = "inactivity"
    DATE_BASED = "date_based"
    CUSTOM_EVENT = "custom_event"


# ---------------------------------------------------------------------------
# Workflow templates
# ---------------------------------------------------------------------------

WORKFLOW_TEMPLATES = {
    # ── Original templates (enhanced) ──────────────────────────────────
    "welcome_series": {
        "name": "Welcome Email Series",
        "description": "Onboard new subscribers with a warm welcome sequence",
        "trigger": TriggerType.LEAD_CREATED,
        "category": "onboarding",
        "steps": [
            {"action": ActionType.SEND_EMAIL, "template": "welcome", "delay_hours": 0,
             "subject": "Welcome to {{company_name}}!"},
            {"action": ActionType.ADD_TAG, "tag": "onboarding_started", "delay_hours": 0},
            {"action": ActionType.SEND_EMAIL, "template": "onboarding_tips", "delay_hours": 72,
             "subject": "Getting started – 3 tips for success"},
            {"action": ActionType.SEND_EMAIL, "template": "feature_highlight", "delay_hours": 168,
             "subject": "Did you know? Top features you should try"},
            {"action": ActionType.CHECK_ENGAGEMENT, "condition": "opened_any", "delay_hours": 240},
            {"action": ActionType.BRANCH, "condition": "engaged",
             "true_step": 6, "false_step": 7, "delay_hours": 0},
            {"action": ActionType.ADD_TAG, "tag": "engaged_new_user", "delay_hours": 0},
            {"action": ActionType.ENROL_WORKFLOW, "workflow_id": "re_engagement", "delay_hours": 0},
        ],
    },
    "re_engagement": {
        "name": "Re-engagement Campaign",
        "description": "Win back inactive subscribers before they churn",
        "trigger": TriggerType.INACTIVITY,
        "trigger_config": {"inactive_days": 30},
        "category": "retention",
        "steps": [
            {"action": ActionType.CHECK_ACTIVITY, "condition": "inactive_30_days", "delay_hours": 0},
            {"action": ActionType.SEND_EMAIL, "template": "we_miss_you", "delay_hours": 0,
             "subject": "We miss you, {{first_name}}!"},
            {"action": ActionType.SEND_EMAIL, "template": "special_offer", "delay_hours": 120,
             "subject": "A special offer just for you"},
            {"action": ActionType.CHECK_ENGAGEMENT, "condition": "opened_any", "delay_hours": 168},
            {"action": ActionType.BRANCH, "condition": "engaged",
             "true_step": 6, "false_step": 7, "delay_hours": 0},
            {"action": ActionType.REMOVE_TAG, "tag": "at_risk", "delay_hours": 0},
            {"action": ActionType.UPDATE_STATUS, "new_status": "churned", "delay_hours": 336},
        ],
    },
    "lead_nurture": {
        "name": "Lead Nurture Sequence",
        "description": "Educate and warm leads toward sales readiness",
        "trigger": TriggerType.FORM_SUBMITTED,
        "category": "nurture",
        "steps": [
            {"action": ActionType.SEND_EMAIL, "template": "intro_resources", "delay_hours": 0,
             "subject": "Resources to help you get started"},
            {"action": ActionType.SEND_EMAIL, "template": "case_study", "delay_hours": 96,
             "subject": "How {{customer_name}} achieved 3x ROI"},
            {"action": ActionType.SEND_EMAIL, "template": "demo_invite", "delay_hours": 192,
             "subject": "See it in action – book a demo"},
            {"action": ActionType.CHECK_ENGAGEMENT, "condition": "clicked_demo", "delay_hours": 240},
            {"action": ActionType.BRANCH, "condition": "demo_booked",
             "true_step": 6, "false_step": 7, "delay_hours": 0},
            {"action": ActionType.NOTIFY_SALES, "delay_hours": 0,
             "message": "Lead {{lead_id}} booked a demo"},
            {"action": ActionType.SEND_EMAIL, "template": "roi_calculator", "delay_hours": 48,
             "subject": "Calculate your potential ROI"},
        ],
    },

    # ── New templates ──────────────────────────────────────────────────
    "onboarding_product": {
        "name": "Product Onboarding",
        "description": "Guide new users through product setup and first value",
        "trigger": TriggerType.TRIAL_STARTED,
        "category": "onboarding",
        "steps": [
            {"action": ActionType.SEND_EMAIL, "template": "trial_welcome", "delay_hours": 0,
             "subject": "Your trial has started – let's get you set up"},
            {"action": ActionType.ADD_TAG, "tag": "trial_active", "delay_hours": 0},
            {"action": ActionType.SEND_EMAIL, "template": "setup_guide", "delay_hours": 24,
             "subject": "Step-by-step: Complete your setup in 5 minutes"},
            {"action": ActionType.CHECK_CONDITION, "condition": "setup_completed", "delay_hours": 72},
            {"action": ActionType.BRANCH, "condition": "setup_done",
             "true_step": 6, "false_step": 5, "delay_hours": 0},
            {"action": ActionType.SEND_EMAIL, "template": "setup_reminder", "delay_hours": 0,
             "subject": "Need help? Let us walk you through setup"},
            {"action": ActionType.SEND_EMAIL, "template": "first_win", "delay_hours": 120,
             "subject": "Congrats on your first milestone!"},
            {"action": ActionType.SEND_EMAIL, "template": "advanced_features", "delay_hours": 240,
             "subject": "Level up: Advanced features to explore"},
            {"action": ActionType.NOTIFY_TEAM, "delay_hours": 312,
             "message": "User {{lead_id}} completing onboarding – check engagement"},
        ],
    },
    "upsell_sequence": {
        "name": "Upsell / Cross-sell Sequence",
        "description": "Promote upgrades and complementary products to existing customers",
        "trigger": TriggerType.PURCHASE_MADE,
        "category": "revenue",
        "steps": [
            {"action": ActionType.SEND_EMAIL, "template": "thank_you_purchase", "delay_hours": 1,
             "subject": "Thank you for your purchase!"},
            {"action": ActionType.ADD_TAG, "tag": "customer", "delay_hours": 0},
            {"action": ActionType.WAIT, "delay_hours": 168},
            {"action": ActionType.SEND_EMAIL, "template": "product_tips", "delay_hours": 0,
             "subject": "Get more from your {{product_name}}"},
            {"action": ActionType.SEND_EMAIL, "template": "complementary_products", "delay_hours": 336,
             "subject": "Customers also loved these"},
            {"action": ActionType.CHECK_ENGAGEMENT, "condition": "clicked_upsell", "delay_hours": 48},
            {"action": ActionType.BRANCH, "condition": "interested",
             "true_step": 8, "false_step": 9, "delay_hours": 0},
            {"action": ActionType.SEND_EMAIL, "template": "upgrade_offer", "delay_hours": 0,
             "subject": "Exclusive upgrade offer – save 20%"},
            {"action": ActionType.ADD_TAG, "tag": "upsell_attempted", "delay_hours": 0},
        ],
    },
    "win_back": {
        "name": "Win-back Campaign",
        "description": "Re-activate churned customers with compelling offers",
        "trigger": TriggerType.INACTIVITY,
        "trigger_config": {"inactive_days": 90},
        "category": "retention",
        "steps": [
            {"action": ActionType.SEND_EMAIL, "template": "long_time_no_see", "delay_hours": 0,
             "subject": "It's been a while, {{first_name}}"},
            {"action": ActionType.SEND_EMAIL, "template": "whats_new", "delay_hours": 120,
             "subject": "Look what's new since you've been away"},
            {"action": ActionType.SEND_EMAIL, "template": "win_back_offer", "delay_hours": 240,
             "subject": "Come back and save 30% – just for you"},
            {"action": ActionType.CHECK_ENGAGEMENT, "condition": "opened_any", "delay_hours": 72},
            {"action": ActionType.BRANCH, "condition": "re_engaged",
             "true_step": 6, "false_step": 7, "delay_hours": 0},
            {"action": ActionType.REMOVE_TAG, "tag": "churned", "delay_hours": 0},
            {"action": ActionType.ADD_TAG, "tag": "permanently_churned", "delay_hours": 0},
        ],
    },
    "cart_abandonment": {
        "name": "Cart Abandonment Recovery",
        "description": "Recover revenue from abandoned shopping carts",
        "trigger": TriggerType.CART_ABANDONED,
        "category": "revenue",
        "steps": [
            {"action": ActionType.SEND_EMAIL, "template": "cart_reminder", "delay_hours": 1,
             "subject": "You left something behind!"},
            {"action": ActionType.CHECK_CONDITION, "condition": "cart_recovered", "delay_hours": 24},
            {"action": ActionType.BRANCH, "condition": "purchased",
             "true_step": 7, "false_step": 4, "delay_hours": 0},
            {"action": ActionType.SEND_EMAIL, "template": "cart_urgency", "delay_hours": 0,
             "subject": "Your cart is waiting – items selling fast"},
            {"action": ActionType.SEND_EMAIL, "template": "cart_discount", "delay_hours": 48,
             "subject": "10% off to complete your order"},
            {"action": ActionType.SEND_PUSH, "template": "cart_push", "delay_hours": 24,
             "message": "Don't forget your cart!"},
            {"action": ActionType.ADD_TAG, "tag": "cart_abandoned_final", "delay_hours": 0},
        ],
    },
    "trial_expiry": {
        "name": "Trial Expiry Conversion",
        "description": "Convert trial users before and after expiry",
        "trigger": TriggerType.TRIAL_EXPIRING,
        "trigger_config": {"days_before": 7},
        "category": "conversion",
        "steps": [
            {"action": ActionType.SEND_EMAIL, "template": "trial_expiring_soon", "delay_hours": 0,
             "subject": "Your trial ends in 7 days – here's what you'll miss"},
            {"action": ActionType.SEND_EMAIL, "template": "trial_3_days", "delay_hours": 96,
             "subject": "3 days left – upgrade now and keep your data"},
            {"action": ActionType.SEND_EMAIL, "template": "trial_last_day", "delay_hours": 144,
             "subject": "Last day! Don't lose access"},
            {"action": ActionType.CHECK_CONDITION, "condition": "converted", "delay_hours": 24},
            {"action": ActionType.BRANCH, "condition": "converted",
             "true_step": 6, "false_step": 7, "delay_hours": 0},
            {"action": ActionType.ADD_TAG, "tag": "converted_from_trial", "delay_hours": 0},
            {"action": ActionType.SEND_EMAIL, "template": "trial_expired", "delay_hours": 0,
             "subject": "Your trial has ended – but it's not too late"},
            {"action": ActionType.SEND_EMAIL, "template": "trial_extended_offer", "delay_hours": 72,
             "subject": "We've extended your trial by 3 days"},
        ],
    },
    "post_purchase": {
        "name": "Post-Purchase Follow-up",
        "description": "Delight customers after purchase and drive reviews/referrals",
        "trigger": TriggerType.PURCHASE_MADE,
        "category": "retention",
        "steps": [
            {"action": ActionType.SEND_EMAIL, "template": "order_confirmation", "delay_hours": 0,
             "subject": "Order confirmed – here's what's next"},
            {"action": ActionType.SEND_EMAIL, "template": "shipping_update", "delay_hours": 48,
             "subject": "Your order is on its way!"},
            {"action": ActionType.SEND_EMAIL, "template": "delivery_followup", "delay_hours": 168,
             "subject": "How's everything? We'd love your feedback"},
            {"action": ActionType.SEND_EMAIL, "template": "review_request", "delay_hours": 336,
             "subject": "Leave a review and get 10% off your next order"},
            {"action": ActionType.ADD_TAG, "tag": "review_requested", "delay_hours": 0},
        ],
    },
    "referral_programme": {
        "name": "Referral Programme",
        "description": "Encourage satisfied customers to refer others",
        "trigger": TriggerType.CUSTOM_EVENT,
        "trigger_config": {"event": "nps_promoter"},
        "category": "growth",
        "steps": [
            {"action": ActionType.SEND_EMAIL, "template": "referral_invite", "delay_hours": 0,
             "subject": "Love us? Share the love and earn rewards!"},
            {"action": ActionType.ADD_TAG, "tag": "referral_invited", "delay_hours": 0},
            {"action": ActionType.CHECK_CONDITION, "condition": "referral_made", "delay_hours": 168},
            {"action": ActionType.BRANCH, "condition": "referred",
             "true_step": 5, "false_step": 6, "delay_hours": 0},
            {"action": ActionType.SEND_EMAIL, "template": "referral_thank_you", "delay_hours": 0,
             "subject": "Thanks for referring a friend!"},
            {"action": ActionType.SEND_EMAIL, "template": "referral_reminder", "delay_hours": 0,
             "subject": "Your referral link is waiting – share and earn"},
        ],
    },
    "nps_feedback": {
        "name": "NPS / Feedback Collection",
        "description": "Collect Net Promoter Score and act on feedback",
        "trigger": TriggerType.DATE_BASED,
        "trigger_config": {"frequency_days": 90},
        "category": "feedback",
        "steps": [
            {"action": ActionType.SEND_EMAIL, "template": "nps_survey", "delay_hours": 0,
             "subject": "Quick question: How likely are you to recommend us?"},
            {"action": ActionType.CHECK_CONDITION, "condition": "survey_completed", "delay_hours": 72},
            {"action": ActionType.BRANCH, "condition": "responded",
             "true_step": 4, "false_step": 3, "delay_hours": 0},
            {"action": ActionType.SEND_EMAIL, "template": "nps_reminder", "delay_hours": 0,
             "subject": "We'd really value your feedback (takes 30 seconds)"},
            {"action": ActionType.CHECK_CONDITION, "condition": "nps_score_check", "delay_hours": 0},
            {"action": ActionType.BRANCH, "condition": "promoter",
             "true_step": 7, "false_step": 6, "delay_hours": 0},
            {"action": ActionType.NOTIFY_TEAM, "delay_hours": 0,
             "message": "Detractor alert: {{lead_id}} scored low NPS"},
            {"action": ActionType.ENROL_WORKFLOW, "workflow_id": "referral_programme", "delay_hours": 0},
        ],
    },
    "event_followup": {
        "name": "Event / Webinar Follow-up",
        "description": "Follow up with event attendees and no-shows",
        "trigger": TriggerType.CUSTOM_EVENT,
        "trigger_config": {"event": "webinar_registered"},
        "category": "engagement",
        "steps": [
            {"action": ActionType.SEND_EMAIL, "template": "event_reminder", "delay_hours": -24,
             "subject": "Reminder: {{event_name}} starts tomorrow!"},
            {"action": ActionType.CHECK_CONDITION, "condition": "attended", "delay_hours": 2},
            {"action": ActionType.BRANCH, "condition": "attended",
             "true_step": 4, "false_step": 5, "delay_hours": 0},
            {"action": ActionType.SEND_EMAIL, "template": "event_attended_followup", "delay_hours": 0,
             "subject": "Thanks for attending! Here's the recording"},
            {"action": ActionType.SEND_EMAIL, "template": "event_missed", "delay_hours": 0,
             "subject": "Sorry we missed you – here's the recording"},
            {"action": ActionType.SEND_EMAIL, "template": "event_resources", "delay_hours": 72,
             "subject": "Additional resources from {{event_name}}"},
            {"action": ActionType.UPDATE_SCORE, "score_delta": 10, "delay_hours": 0},
        ],
    },
}


# ---------------------------------------------------------------------------
# Workflow execution engine
# ---------------------------------------------------------------------------

class WorkflowEngine:
    """
    Executes workflow sequences for leads, managing state, branching,
    and multi-step progression.
    """

    def __init__(self):
        self._workflow_states: dict[str, dict] = {}
        self._event_subscriptions: dict[str, list[dict]] = {}
        self._execution_log: list[dict] = []

    def get_available_workflows(self) -> dict:
        """Return all available workflow templates with metadata."""
        result = {}
        for wf_id, template in WORKFLOW_TEMPLATES.items():
            result[wf_id] = {
                "name": template["name"],
                "description": template.get("description", ""),
                "trigger": template.get("trigger", TriggerType.MANUAL),
                "category": template.get("category", "general"),
                "step_count": len(template["steps"]),
            }
        return result

    def get_workflow_categories(self) -> dict[str, list[str]]:
        """Group workflows by category."""
        categories: dict[str, list[str]] = {}
        for wf_id, template in WORKFLOW_TEMPLATES.items():
            cat = template.get("category", "general")
            categories.setdefault(cat, []).append(wf_id)
        return categories

    async def enrol_lead(self, workflow_id: str, lead_id: str,
                         context: Optional[dict] = None) -> dict:
        """Enrol a lead in a workflow and execute the first step."""
        if workflow_id not in WORKFLOW_TEMPLATES:
            return {
                "status": "error",
                "details": {"message": f"Unknown workflow: {workflow_id}"},
                "logs": [f"Workflow '{workflow_id}' not found"],
            }

        state_key = f"{workflow_id}:{lead_id}"

        # Check if already enrolled
        if state_key in self._workflow_states:
            existing = self._workflow_states[state_key]
            if existing["status"] == WorkflowStatus.ACTIVE:
                return {
                    "status": "already_enrolled",
                    "details": {
                        "workflow": workflow_id,
                        "lead_id": lead_id,
                        "current_step": existing["current_step"],
                    },
                    "logs": [f"Lead {lead_id} already active in workflow {workflow_id}"],
                }

        self._workflow_states[state_key] = {
            "workflow_id": workflow_id,
            "lead_id": lead_id,
            "status": WorkflowStatus.ACTIVE,
            "current_step": 0,
            "started_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "history": [],
            "context": context or {},
            "branch_results": {},
        }

        # Execute first step
        return await self.advance_workflow(workflow_id, lead_id)

    async def advance_workflow(self, workflow_id: str, lead_id: str,
                               condition_results: Optional[dict] = None) -> dict:
        """Execute the next step of a workflow for a lead."""
        if workflow_id not in WORKFLOW_TEMPLATES:
            return {
                "status": "error",
                "details": {"message": f"Unknown workflow: {workflow_id}"},
                "logs": [f"Workflow '{workflow_id}' not found"],
            }

        state_key = f"{workflow_id}:{lead_id}"
        template = WORKFLOW_TEMPLATES[workflow_id]

        if state_key not in self._workflow_states:
            return {
                "status": "error",
                "details": {"message": "Lead not enrolled in this workflow"},
                "logs": [f"Lead {lead_id} not found in workflow {workflow_id}"],
            }

        state = self._workflow_states[state_key]

        if state["status"] != WorkflowStatus.ACTIVE:
            return {
                "status": state["status"],
                "details": {"message": f"Workflow is {state['status']}"},
                "logs": state["history"],
            }

        step_index = state["current_step"]
        if step_index >= len(template["steps"]):
            state["status"] = WorkflowStatus.COMPLETED
            return {
                "status": "completed",
                "details": {"message": "Workflow completed"},
                "logs": state["history"],
            }

        step = template["steps"][step_index]
        action = step.get("action", "")

        # Store condition results if provided
        if condition_results:
            state["branch_results"].update(condition_results)

        # Execute step
        log_entry = self._execute_step(step, lead_id, state)

        state["history"].append(log_entry)
        state["updated_at"] = datetime.now(timezone.utc).isoformat()

        # Handle branching
        if action == ActionType.BRANCH:
            condition = step.get("condition", "")
            is_true = state["branch_results"].get(condition, False)
            if is_true and "true_step" in step:
                state["current_step"] = step["true_step"]
            elif not is_true and "false_step" in step:
                state["current_step"] = step["false_step"]
            else:
                state["current_step"] = step_index + 1
        else:
            state["current_step"] = step_index + 1

        # Log execution
        self._execution_log.append({
            "workflow_id": workflow_id,
            "lead_id": lead_id,
            "step_index": step_index,
            "action": action,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

        next_step = state["current_step"]
        is_completed = next_step >= len(template["steps"])
        if is_completed:
            state["status"] = WorkflowStatus.COMPLETED

        return {
            "status": "completed" if is_completed else "success",
            "details": {
                "workflow": workflow_id,
                "lead_id": lead_id,
                "step_executed": step,
                "step_index": step_index,
                "next_step": None if is_completed else next_step,
            },
            "logs": [log_entry],
        }

    def _execute_step(self, step: dict, lead_id: str, state: dict) -> str:
        """Execute a single workflow step and return a log entry."""
        action = step.get("action", "unknown")
        log_parts = [f"Step: {action}"]

        if action == ActionType.SEND_EMAIL:
            template = step.get("template", "default")
            subject = step.get("subject", "")
            log_parts.append(f"template={template}, subject='{subject}'")

        elif action == ActionType.SEND_SMS:
            log_parts.append(f"message='{step.get('message', '')}'")

        elif action == ActionType.SEND_PUSH:
            log_parts.append(f"message='{step.get('message', '')}'")

        elif action in (ActionType.ADD_TAG, ActionType.REMOVE_TAG):
            log_parts.append(f"tag='{step.get('tag', '')}'")

        elif action == ActionType.UPDATE_STATUS:
            log_parts.append(f"new_status='{step.get('new_status', '')}'")

        elif action == ActionType.UPDATE_SCORE:
            log_parts.append(f"score_delta={step.get('score_delta', 0)}")

        elif action in (ActionType.CHECK_ENGAGEMENT, ActionType.CHECK_ACTIVITY,
                        ActionType.CHECK_CONDITION):
            condition = step.get("condition", "")
            log_parts.append(f"condition='{condition}'")

        elif action == ActionType.BRANCH:
            condition = step.get("condition", "")
            result = state.get("branch_results", {}).get(condition, False)
            log_parts.append(f"condition='{condition}', result={result}")

        elif action == ActionType.NOTIFY_SALES or action == ActionType.NOTIFY_TEAM:
            log_parts.append(f"message='{step.get('message', '')}'")

        elif action == ActionType.ENROL_WORKFLOW:
            log_parts.append(f"target_workflow='{step.get('workflow_id', '')}'")

        elif action == ActionType.TRIGGER_WEBHOOK:
            log_parts.append(f"url='{step.get('url', '')}'")

        elif action == ActionType.WAIT:
            log_parts.append(f"delay_hours={step.get('delay_hours', 0)}")

        return " | ".join(log_parts)

    # ---- Event handling ----------------------------------------------------

    def register_event_trigger(self, event_type: str, workflow_id: str,
                               config: Optional[dict] = None) -> None:
        """Register a workflow to be triggered by a specific event."""
        self._event_subscriptions.setdefault(event_type, []).append({
            "workflow_id": workflow_id,
            "config": config or {},
        })

    async def fire_event(self, event_type: str, lead_id: str,
                         event_data: Optional[dict] = None) -> list[dict]:
        """Fire an event and enrol the lead in any matching workflows."""
        results = []
        subscriptions = self._event_subscriptions.get(event_type, [])
        for sub in subscriptions:
            result = await self.enrol_lead(
                sub["workflow_id"], lead_id, context=event_data
            )
            results.append(result)
        return results

    # ---- State management --------------------------------------------------

    def pause_workflow(self, workflow_id: str, lead_id: str) -> dict:
        """Pause a workflow for a lead."""
        state_key = f"{workflow_id}:{lead_id}"
        if state_key in self._workflow_states:
            self._workflow_states[state_key]["status"] = WorkflowStatus.PAUSED
            return {"status": "paused"}
        return {"status": "not_found"}

    def resume_workflow(self, workflow_id: str, lead_id: str) -> dict:
        """Resume a paused workflow."""
        state_key = f"{workflow_id}:{lead_id}"
        if state_key in self._workflow_states:
            state = self._workflow_states[state_key]
            if state["status"] == WorkflowStatus.PAUSED:
                state["status"] = WorkflowStatus.ACTIVE
                return {"status": "resumed"}
            return {"status": state["status"]}
        return {"status": "not_found"}

    def cancel_workflow(self, workflow_id: str, lead_id: str) -> dict:
        """Cancel a workflow for a lead."""
        state_key = f"{workflow_id}:{lead_id}"
        if state_key in self._workflow_states:
            self._workflow_states[state_key]["status"] = WorkflowStatus.CANCELLED
            return {"status": "cancelled"}
        return {"status": "not_found"}

    def get_lead_workflows(self, lead_id: str) -> list[dict]:
        """Get all workflow states for a specific lead."""
        results = []
        for key, state in self._workflow_states.items():
            if state["lead_id"] == lead_id:
                results.append(state)
        return results

    def get_workflow_stats(self, workflow_id: str) -> dict:
        """Get aggregate statistics for a workflow."""
        total = active = completed = paused = cancelled = 0
        for key, state in self._workflow_states.items():
            if state["workflow_id"] == workflow_id:
                total += 1
                status = state["status"]
                if status == WorkflowStatus.ACTIVE:
                    active += 1
                elif status == WorkflowStatus.COMPLETED:
                    completed += 1
                elif status == WorkflowStatus.PAUSED:
                    paused += 1
                elif status == WorkflowStatus.CANCELLED:
                    cancelled += 1
        return {
            "workflow_id": workflow_id,
            "total_enrolled": total,
            "active": active,
            "completed": completed,
            "paused": paused,
            "cancelled": cancelled,
            "completion_rate": completed / max(total, 1),
        }

    def get_execution_log(self, workflow_id: Optional[str] = None,
                          lead_id: Optional[str] = None,
                          limit: int = 100) -> list[dict]:
        """Retrieve execution log entries with optional filtering."""
        entries = self._execution_log
        if workflow_id:
            entries = [e for e in entries if e["workflow_id"] == workflow_id]
        if lead_id:
            entries = [e for e in entries if e["lead_id"] == lead_id]
        return entries[-limit:]
