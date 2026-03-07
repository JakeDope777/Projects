"""
Compliance Management Engine

Comprehensive regulatory compliance for marketing communications covering
GDPR (EU), CAN-SPAM (US), CASL (Canada), and general data protection.

Features:
- GDPR data subject rights: access, export, rectification, erasure, portability
- Consent management with granular opt-in/opt-out tracking
- CAN-SPAM compliance checking for email content
- CASL compliance with express/implied consent tracking
- Content scanning for prohibited patterns
- Audit logging for all compliance-related actions
- Data retention policy enforcement
- Breach notification tracking
"""

import re
import uuid
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional
from enum import Enum
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class ConsentType(str, Enum):
    EXPRESS = "express"          # Explicit opt-in (GDPR, CASL)
    IMPLIED = "implied"          # Implied consent (CASL transitional)
    LEGITIMATE_INTEREST = "legitimate_interest"  # GDPR Art. 6(1)(f)
    CONTRACTUAL = "contractual"  # GDPR Art. 6(1)(b)
    WITHDRAWN = "withdrawn"      # Consent withdrawn


class ConsentChannel(str, Enum):
    EMAIL = "email"
    SMS = "sms"
    PHONE = "phone"
    PUSH = "push_notification"
    SOCIAL = "social_media"
    DIRECT_MAIL = "direct_mail"
    ALL = "all"


class DataSubjectRight(str, Enum):
    ACCESS = "access"            # Art. 15 – Right of access
    RECTIFICATION = "rectification"  # Art. 16 – Right to rectification
    ERASURE = "erasure"          # Art. 17 – Right to erasure
    RESTRICTION = "restriction"  # Art. 18 – Right to restriction
    PORTABILITY = "portability"  # Art. 20 – Right to data portability
    OBJECTION = "objection"      # Art. 21 – Right to object
    EXPORT = "export"            # Data export request


class ComplianceRegulation(str, Enum):
    GDPR = "gdpr"
    CAN_SPAM = "can_spam"
    CASL = "casl"
    CCPA = "ccpa"
    GENERAL = "general"


# ---------------------------------------------------------------------------
# Compliance rules
# ---------------------------------------------------------------------------

COMPLIANCE_RULES = {
    "email": {
        "required_fields": ["unsubscribe_link", "sender_address", "company_name"],
        "can_spam_required": [
            "unsubscribe_link", "sender_address", "company_name",
            "physical_address",
        ],
        "casl_required": [
            "unsubscribe_link", "sender_identity", "contact_information",
        ],
        "gdpr_required": [
            "unsubscribe_link", "privacy_policy_link", "sender_identity",
            "purpose_of_processing",
        ],
        "prohibited_patterns": [
            r"(?i)guaranteed\s+results",
            r"(?i)act\s+now\s+or\s+lose",
            r"(?i)no\s+risk",
            r"(?i)100%\s+free",
            r"(?i)click\s+below\s+to\s+confirm",
            r"(?i)congratulations.*you('ve)?\s+(been\s+)?selected",
            r"(?i)dear\s+(friend|winner|customer)\b",
        ],
        "max_frequency_per_day": 3,
        "requires_consent": True,
        "unsubscribe_deadline_days": 10,  # CAN-SPAM: 10 business days
    },
    "sms": {
        "required_fields": ["opt_out_instructions", "sender_id"],
        "prohibited_patterns": [],
        "max_frequency_per_day": 1,
        "requires_consent": True,
        "consent_type_required": "express",
    },
    "social": {
        "required_fields": [],
        "prohibited_patterns": [
            r"(?i)guaranteed\s+results",
        ],
        "max_frequency_per_day": 10,
        "requires_consent": False,
    },
    "push_notification": {
        "required_fields": ["opt_out_instructions"],
        "prohibited_patterns": [],
        "max_frequency_per_day": 5,
        "requires_consent": True,
    },
}


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class ConsentRecord:
    """Tracks consent status for a specific lead and channel."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    lead_id: str = ""
    channel: ConsentChannel = ConsentChannel.EMAIL
    consent_type: ConsentType = ConsentType.EXPRESS
    granted: bool = False
    granted_at: Optional[str] = None
    withdrawn_at: Optional[str] = None
    expires_at: Optional[str] = None
    source: str = ""               # How consent was obtained
    ip_address: Optional[str] = None
    proof_reference: Optional[str] = None  # Reference to consent proof
    regulation: ComplianceRegulation = ComplianceRegulation.GENERAL

    def is_valid(self) -> bool:
        """Check if consent is currently valid."""
        if not self.granted:
            return False
        if self.withdrawn_at:
            return False
        if self.expires_at:
            try:
                expires = datetime.fromisoformat(self.expires_at)
                if datetime.now(timezone.utc) > expires:
                    return False
            except (ValueError, TypeError):
                pass
        return True

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "lead_id": self.lead_id,
            "channel": self.channel.value,
            "consent_type": self.consent_type.value,
            "granted": self.granted,
            "granted_at": self.granted_at,
            "withdrawn_at": self.withdrawn_at,
            "expires_at": self.expires_at,
            "source": self.source,
            "is_valid": self.is_valid(),
            "regulation": self.regulation.value,
        }


@dataclass
class AuditLogEntry:
    """Immutable audit log entry for compliance actions."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    action: str = ""
    lead_id: Optional[str] = None
    performed_by: str = "system"
    details: dict = field(default_factory=dict)
    regulation: str = ""

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "timestamp": self.timestamp,
            "action": self.action,
            "lead_id": self.lead_id,
            "performed_by": self.performed_by,
            "details": self.details,
            "regulation": self.regulation,
        }


@dataclass
class DataSubjectRequest:
    """A GDPR data subject request."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    lead_id: str = ""
    right: DataSubjectRight = DataSubjectRight.ACCESS
    status: str = "pending"  # pending, processing, completed, rejected
    requested_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    completed_at: Optional[str] = None
    response_data: Optional[dict] = None
    notes: str = ""

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "lead_id": self.lead_id,
            "right": self.right.value,
            "status": self.status,
            "requested_at": self.requested_at,
            "completed_at": self.completed_at,
            "notes": self.notes,
        }


# ---------------------------------------------------------------------------
# Compliance engine
# ---------------------------------------------------------------------------

class ComplianceEngine:
    """
    Manages consent, data subject rights, content compliance checking,
    and audit logging for GDPR, CAN-SPAM, and CASL.
    """

    def __init__(self):
        self._consent_records: dict[str, list[ConsentRecord]] = {}  # lead_id -> records
        self._audit_log: list[AuditLogEntry] = []
        self._dsr_requests: dict[str, DataSubjectRequest] = {}
        self._suppression_list: set[str] = set()  # lead_ids that must not be contacted
        self._data_retention_days: int = 730  # 2 years default
        self._breach_log: list[dict] = []

    # ---- Consent management ------------------------------------------------

    def record_consent(
        self,
        lead_id: str,
        channel: str,
        consent_type: str = "express",
        source: str = "web_form",
        ip_address: Optional[str] = None,
        regulation: str = "general",
        expires_in_days: Optional[int] = None,
    ) -> dict:
        """Record consent for a lead on a specific channel."""
        now = datetime.now(timezone.utc)
        expires_at = None
        if expires_in_days:
            expires_at = (now + timedelta(days=expires_in_days)).isoformat()

        record = ConsentRecord(
            lead_id=lead_id,
            channel=ConsentChannel(channel),
            consent_type=ConsentType(consent_type),
            granted=True,
            granted_at=now.isoformat(),
            expires_at=expires_at,
            source=source,
            ip_address=ip_address,
            regulation=ComplianceRegulation(regulation),
        )

        self._consent_records.setdefault(lead_id, []).append(record)
        self._log_action("consent_granted", lead_id, {
            "channel": channel,
            "consent_type": consent_type,
            "source": source,
        }, regulation)

        return {
            "status": "success",
            "details": record.to_dict(),
            "logs": [f"Consent recorded for lead {lead_id} on {channel}"],
        }

    def withdraw_consent(self, lead_id: str, channel: str) -> dict:
        """Withdraw consent for a lead on a specific channel."""
        records = self._consent_records.get(lead_id, [])
        withdrawn = False

        for record in records:
            if record.channel.value == channel and record.granted and not record.withdrawn_at:
                record.withdrawn_at = datetime.now(timezone.utc).isoformat()
                record.granted = False
                withdrawn = True

        if withdrawn:
            self._log_action("consent_withdrawn", lead_id, {"channel": channel})
            return {
                "status": "success",
                "details": {"lead_id": lead_id, "channel": channel},
                "logs": [f"Consent withdrawn for lead {lead_id} on {channel}"],
            }
        return {
            "status": "not_found",
            "details": {"message": "No active consent found"},
            "logs": [],
        }

    def check_consent(self, lead_id: str, channel: str) -> dict:
        """Check if a lead has valid consent for a channel."""
        records = self._consent_records.get(lead_id, [])

        for record in records:
            if record.channel.value == channel and record.is_valid():
                return {
                    "has_consent": True,
                    "consent_type": record.consent_type.value,
                    "granted_at": record.granted_at,
                    "expires_at": record.expires_at,
                }

        # Check for ALL channel consent
        for record in records:
            if record.channel == ConsentChannel.ALL and record.is_valid():
                return {
                    "has_consent": True,
                    "consent_type": record.consent_type.value,
                    "granted_at": record.granted_at,
                    "expires_at": record.expires_at,
                }

        return {"has_consent": False}

    def get_consent_status(self, lead_id: str) -> dict:
        """Get full consent status for a lead across all channels."""
        records = self._consent_records.get(lead_id, [])
        status = {}
        for record in records:
            channel = record.channel.value
            status[channel] = {
                "consent_type": record.consent_type.value,
                "granted": record.granted,
                "is_valid": record.is_valid(),
                "granted_at": record.granted_at,
                "withdrawn_at": record.withdrawn_at,
            }
        return {
            "lead_id": lead_id,
            "channels": status,
            "is_suppressed": lead_id in self._suppression_list,
        }

    # ---- Content compliance checking ---------------------------------------

    def check_content_compliance(
        self,
        message: str,
        channel: str,
        regulations: Optional[list[str]] = None,
    ) -> dict:
        """
        Check whether message content complies with regulations.

        Args:
            message: The message content to check.
            channel: The delivery channel.
            regulations: List of regulations to check against.
                         Defaults to all applicable regulations.
        """
        regulations = regulations or ["can_spam", "gdpr", "casl"]
        issues = []
        warnings = []
        channel_rules = COMPLIANCE_RULES.get(channel, COMPLIANCE_RULES.get("email", {}))

        # Check required fields per regulation
        for reg in regulations:
            required_key = f"{reg}_required"
            required_fields = channel_rules.get(required_key, channel_rules.get("required_fields", []))
            for field_name in required_fields:
                normalised = field_name.lower().replace("_", " ")
                if normalised not in message.lower():
                    issues.append({
                        "regulation": reg,
                        "severity": "error",
                        "field": field_name,
                        "message": f"Missing required element: {field_name}",
                    })

        # Check prohibited patterns
        for pattern in channel_rules.get("prohibited_patterns", []):
            if re.search(pattern, message):
                issues.append({
                    "regulation": "general",
                    "severity": "error",
                    "message": f"Prohibited content pattern detected: {pattern}",
                })

        # CAN-SPAM specific checks
        if "can_spam" in regulations and channel == "email":
            # Must have physical address
            if "physical address" not in message.lower() and "physical_address" not in message.lower():
                # Check for address-like patterns
                address_pattern = r'\d+\s+\w+\s+(st|street|ave|avenue|blvd|rd|road|dr|drive)'
                if not re.search(address_pattern, message, re.IGNORECASE):
                    issues.append({
                        "regulation": "can_spam",
                        "severity": "error",
                        "message": "CAN-SPAM requires a valid physical postal address",
                    })

            # Subject line must not be deceptive
            if message.startswith("RE:") or message.startswith("FW:"):
                warnings.append({
                    "regulation": "can_spam",
                    "severity": "warning",
                    "message": "Subject line may be misleading (RE:/FW: prefix without prior conversation)",
                })

        # CASL specific checks
        if "casl" in regulations:
            if "unsubscribe" not in message.lower():
                issues.append({
                    "regulation": "casl",
                    "severity": "error",
                    "message": "CASL requires a functioning unsubscribe mechanism",
                })

        # GDPR specific checks
        if "gdpr" in regulations:
            if "privacy" not in message.lower() and "privacy_policy" not in message.lower():
                warnings.append({
                    "regulation": "gdpr",
                    "severity": "warning",
                    "message": "Consider including a link to your privacy policy (GDPR best practice)",
                })

        # Consent requirement check
        if channel_rules.get("requires_consent", False):
            warnings.append({
                "regulation": "general",
                "severity": "info",
                "message": "Ensure recipient has given valid consent before sending",
            })

        is_compliant = len([i for i in issues if i["severity"] == "error"]) == 0

        return {
            "status": "compliant" if is_compliant else "non_compliant",
            "details": {
                "channel": channel,
                "regulations_checked": regulations,
                "issues": issues,
                "warnings": warnings,
                "is_compliant": is_compliant,
                "issue_count": len(issues),
                "warning_count": len(warnings),
            },
            "logs": [f"Compliance check for {channel}: {'PASS' if is_compliant else 'FAIL'} "
                     f"({len(issues)} issues, {len(warnings)} warnings)"],
        }

    # ---- GDPR data subject rights ------------------------------------------

    def handle_data_subject_request(
        self,
        lead_id: str,
        right: str,
        lead_data: Optional[dict] = None,
        leads_store: Optional[dict] = None,
    ) -> dict:
        """
        Handle a GDPR data subject request.

        Args:
            lead_id: The data subject's lead ID.
            right: The right being exercised (access, erasure, export, etc.).
            lead_data: The lead's current data (for access/export).
            leads_store: Reference to the leads store (for erasure).
        """
        right_enum = DataSubjectRight(right)
        dsr = DataSubjectRequest(
            lead_id=lead_id,
            right=right_enum,
            status="processing",
        )
        self._dsr_requests[dsr.id] = dsr

        result = {"request_id": dsr.id, "right": right}

        if right_enum == DataSubjectRight.ACCESS:
            result["data"] = self._handle_access_request(lead_id, lead_data)
            dsr.status = "completed"

        elif right_enum == DataSubjectRight.EXPORT:
            result["data"] = self._handle_export_request(lead_id, lead_data)
            dsr.status = "completed"

        elif right_enum == DataSubjectRight.ERASURE:
            result["data"] = self._handle_erasure_request(lead_id, leads_store)
            dsr.status = "completed"

        elif right_enum == DataSubjectRight.RECTIFICATION:
            result["data"] = {"message": "Rectification request logged. Please provide corrected data."}
            dsr.status = "pending"

        elif right_enum == DataSubjectRight.RESTRICTION:
            self._suppression_list.add(lead_id)
            result["data"] = {"message": f"Processing of lead {lead_id} data has been restricted"}
            dsr.status = "completed"

        elif right_enum == DataSubjectRight.OBJECTION:
            self._suppression_list.add(lead_id)
            result["data"] = {"message": f"Objection recorded. Lead {lead_id} added to suppression list"}
            dsr.status = "completed"

        elif right_enum == DataSubjectRight.PORTABILITY:
            result["data"] = self._handle_portability_request(lead_id, lead_data)
            dsr.status = "completed"

        dsr.completed_at = datetime.now(timezone.utc).isoformat()
        self._log_action(f"dsr_{right}", lead_id, result, "gdpr")

        return {
            "status": "success",
            "details": result,
            "logs": [f"Data subject request ({right}) processed for lead {lead_id}"],
        }

    def _handle_access_request(self, lead_id: str, lead_data: Optional[dict]) -> dict:
        """Handle right of access (Art. 15)."""
        consent_records = [
            r.to_dict() for r in self._consent_records.get(lead_id, [])
        ]
        return {
            "lead_data": lead_data or {},
            "consent_records": consent_records,
            "processing_purposes": ["marketing_communications", "lead_scoring", "analytics"],
            "data_categories": ["contact_info", "engagement_data", "behavioral_data", "demographic_data"],
            "retention_period_days": self._data_retention_days,
            "data_recipients": ["internal_marketing_team"],
        }

    def _handle_export_request(self, lead_id: str, lead_data: Optional[dict]) -> dict:
        """Handle data export request."""
        consent_records = [
            r.to_dict() for r in self._consent_records.get(lead_id, [])
        ]
        export_data = {
            "lead_profile": lead_data or {},
            "consent_history": consent_records,
            "audit_trail": [
                entry.to_dict() for entry in self._audit_log
                if entry.lead_id == lead_id
            ],
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "format": "json",
        }
        return export_data

    def _handle_erasure_request(self, lead_id: str, leads_store: Optional[dict]) -> dict:
        """Handle right to erasure (Art. 17)."""
        erased_data = []

        # Remove from leads store
        if leads_store and lead_id in leads_store:
            del leads_store[lead_id]
            erased_data.append("lead_profile")

        # Remove consent records
        if lead_id in self._consent_records:
            del self._consent_records[lead_id]
            erased_data.append("consent_records")

        # Add to suppression list (must keep to prevent re-contact)
        self._suppression_list.add(lead_id)

        return {
            "erased_data": erased_data,
            "suppression_list_added": True,
            "message": f"Lead {lead_id} data erased. ID retained on suppression list to prevent re-contact.",
        }

    def _handle_portability_request(self, lead_id: str, lead_data: Optional[dict]) -> dict:
        """Handle right to data portability (Art. 20)."""
        portable_data = {
            "format": "json",
            "schema_version": "1.0",
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "data": {
                "profile": lead_data or {},
                "consent": [
                    r.to_dict() for r in self._consent_records.get(lead_id, [])
                ],
            },
        }
        return portable_data

    # ---- Suppression list --------------------------------------------------

    def add_to_suppression(self, lead_id: str, reason: str = "") -> dict:
        """Add a lead to the suppression list."""
        self._suppression_list.add(lead_id)
        self._log_action("suppression_added", lead_id, {"reason": reason})
        return {"status": "success", "lead_id": lead_id}

    def remove_from_suppression(self, lead_id: str) -> dict:
        """Remove a lead from the suppression list."""
        self._suppression_list.discard(lead_id)
        self._log_action("suppression_removed", lead_id, {})
        return {"status": "success", "lead_id": lead_id}

    def is_suppressed(self, lead_id: str) -> bool:
        """Check if a lead is on the suppression list."""
        return lead_id in self._suppression_list

    def get_suppression_list(self) -> list[str]:
        """Get all suppressed lead IDs."""
        return list(self._suppression_list)

    # ---- Data retention ----------------------------------------------------

    def set_retention_policy(self, days: int) -> dict:
        """Set the data retention period in days."""
        self._data_retention_days = days
        self._log_action("retention_policy_updated", None, {"days": days})
        return {"status": "success", "retention_days": days}

    def check_retention_compliance(self, leads: dict) -> dict:
        """Check which leads exceed the retention period."""
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(days=self._data_retention_days)
        expired = []

        for lead_id, lead in leads.items():
            created = lead.get("created_at")
            if created:
                try:
                    created_dt = datetime.fromisoformat(created)
                    if created_dt < cutoff:
                        expired.append({
                            "lead_id": lead_id,
                            "created_at": created,
                            "days_old": (now - created_dt).days,
                        })
                except (ValueError, TypeError):
                    pass

        return {
            "retention_period_days": self._data_retention_days,
            "expired_leads_count": len(expired),
            "expired_leads": expired,
        }

    # ---- Breach management -------------------------------------------------

    def record_breach(self, description: str, affected_leads: list[str],
                      severity: str = "high") -> dict:
        """Record a data breach for notification purposes."""
        breach = {
            "id": str(uuid.uuid4()),
            "description": description,
            "affected_lead_count": len(affected_leads),
            "severity": severity,
            "detected_at": datetime.now(timezone.utc).isoformat(),
            "notification_deadline": (
                datetime.now(timezone.utc) + timedelta(hours=72)
            ).isoformat(),  # GDPR: 72 hours
            "status": "detected",
        }
        self._breach_log.append(breach)
        self._log_action("breach_detected", None, breach, "gdpr")
        return breach

    def get_breach_log(self) -> list[dict]:
        """Return all recorded breaches."""
        return self._breach_log

    # ---- Audit logging -----------------------------------------------------

    def _log_action(self, action: str, lead_id: Optional[str],
                    details: dict, regulation: str = "") -> None:
        """Add an entry to the audit log."""
        entry = AuditLogEntry(
            action=action,
            lead_id=lead_id,
            details=details,
            regulation=regulation,
        )
        self._audit_log.append(entry)

    def get_audit_log(self, lead_id: Optional[str] = None,
                      action: Optional[str] = None,
                      limit: int = 100) -> list[dict]:
        """Retrieve audit log entries with optional filtering."""
        entries = self._audit_log
        if lead_id:
            entries = [e for e in entries if e.lead_id == lead_id]
        if action:
            entries = [e for e in entries if e.action == action]
        return [e.to_dict() for e in entries[-limit:]]

    def get_dsr_requests(self, lead_id: Optional[str] = None,
                         status: Optional[str] = None) -> list[dict]:
        """Get data subject requests with optional filtering."""
        requests = list(self._dsr_requests.values())
        if lead_id:
            requests = [r for r in requests if r.lead_id == lead_id]
        if status:
            requests = [r for r in requests if r.status == status]
        return [r.to_dict() for r in requests]

    # ---- Pre-send compliance gate ------------------------------------------

    def pre_send_check(self, lead_id: str, channel: str, message: str) -> dict:
        """
        Comprehensive pre-send compliance gate.
        Checks consent, suppression, and content compliance before sending.
        """
        blocks = []
        warnings = []

        # 1. Suppression check
        if self.is_suppressed(lead_id):
            blocks.append("Lead is on the suppression list – cannot send")

        # 2. Consent check
        consent = self.check_consent(lead_id, channel)
        if not consent.get("has_consent", False):
            channel_rules = COMPLIANCE_RULES.get(channel, {})
            if channel_rules.get("requires_consent", True):
                blocks.append(f"No valid consent for {channel} channel")

        # 3. Content compliance
        content_check = self.check_content_compliance(message, channel)
        if not content_check["details"]["is_compliant"]:
            for issue in content_check["details"]["issues"]:
                if issue["severity"] == "error":
                    blocks.append(issue["message"])

        can_send = len(blocks) == 0

        return {
            "can_send": can_send,
            "blocks": blocks,
            "warnings": warnings,
            "consent_status": consent,
        }
