"""
BDHT — Bounty Digital Hiring Tracker Rules Engine
Meridian HR Intelligence — Pure Technology

Audit logic, compliance thresholds, and privacy guardrails for
tracking candidates across the hiring pipeline.

BDHT monitors the hiring process for:
- Compliance violations (EEOC, salary transparency, data retention)
- Process integrity (stage skipping, approval gaps, timeline breaches)
- Privacy guardrails (social media checks, background check boundaries)
- Quality metrics (time-to-hire, cost-per-hire, source effectiveness)
"""

from dataclasses import dataclass
from typing import Optional
from datetime import datetime, timedelta
import json
import os


@dataclass
class AuditFinding:
    """A single audit finding from the rules engine."""
    rule_id: str
    severity: str  # "critical", "warning", "info"
    category: str  # "compliance", "process", "privacy", "quality"
    title: str
    description: str
    remediation: str
    auto_block: bool  # If True, blocks the pipeline action


@dataclass
class AuditResult:
    """Complete audit result for a hiring action."""
    action: str  # What was being audited
    candidate_id: str
    job_id: str
    timestamp: str
    passed: bool
    findings: list
    blocked: bool  # True if any auto_block finding triggered
    block_reason: str

    def to_dict(self):
        return {
            "action": self.action,
            "candidate_id": self.candidate_id,
            "job_id": self.job_id,
            "timestamp": self.timestamp,
            "passed": self.passed,
            "blocked": self.blocked,
            "block_reason": self.block_reason,
            "findings_count": {
                "critical": len([f for f in self.findings if f.severity == "critical"]),
                "warning": len([f for f in self.findings if f.severity == "warning"]),
                "info": len([f for f in self.findings if f.severity == "info"]),
            },
            "findings": [
                {
                    "rule_id": f.rule_id,
                    "severity": f.severity,
                    "category": f.category,
                    "title": f.title,
                    "description": f.description,
                    "remediation": f.remediation,
                }
                for f in self.findings
            ],
        }


class BDHTRulesEngine:
    """
    Rules engine for the Bounty Digital Hiring Tracker.

    Rule Categories:
    1. COMPLIANCE — Legal requirements (EEOC, salary laws, data retention)
    2. PROCESS — Pipeline integrity (stage gates, approvals, timelines)
    3. PRIVACY — Candidate data handling (social media, background checks)
    4. QUALITY — Hiring effectiveness metrics and alerts
    """

    def __init__(self, config_path: Optional[str] = None):
        config_file = config_path or os.path.join(os.path.dirname(__file__), "config.json")
        if os.path.exists(config_file):
            with open(config_file) as f:
                self.config = json.load(f)
        else:
            self.config = self._default_config()

    def audit_stage_transition(
        self,
        candidate_id: str,
        job_id: str,
        from_stage: str,
        to_stage: str,
        metadata: dict,
    ) -> AuditResult:
        """
        Audit a candidate moving from one pipeline stage to another.

        metadata should include:
            - interviewer_count: int
            - has_scorecard: bool
            - days_in_current_stage: int
            - rejection_reason: str (if rejecting)
            - salary_disclosed: bool
            - location_state: str (for jurisdiction-specific rules)
            - approver: str (who approved the transition)
        """
        findings = []
        timestamp = datetime.utcnow().isoformat()

        # Run all applicable rules
        findings.extend(self._check_compliance_rules(from_stage, to_stage, metadata))
        findings.extend(self._check_process_rules(from_stage, to_stage, metadata))
        findings.extend(self._check_privacy_rules(from_stage, to_stage, metadata))
        findings.extend(self._check_quality_rules(from_stage, to_stage, metadata))

        # Determine if blocked
        blockers = [f for f in findings if f.auto_block]
        blocked = len(blockers) > 0
        block_reason = blockers[0].description if blockers else ""
        passed = not any(f.severity == "critical" for f in findings)

        return AuditResult(
            action=f"stage_transition:{from_stage}->{to_stage}",
            candidate_id=candidate_id,
            job_id=job_id,
            timestamp=timestamp,
            passed=passed,
            findings=findings,
            blocked=blocked,
            block_reason=block_reason,
        )

    def audit_candidate_data_access(
        self,
        candidate_id: str,
        accessor: str,
        data_type: str,
        purpose: str,
    ) -> AuditResult:
        """Audit who is accessing candidate data and why."""
        findings = []
        timestamp = datetime.utcnow().isoformat()

        sensitive_types = {"social_media", "background_check", "credit_report", "medical", "salary_history"}

        if data_type in sensitive_types:
            findings.append(AuditFinding(
                rule_id="PRIV-001",
                severity="info",
                category="privacy",
                title="Sensitive data access logged",
                description=f"{accessor} accessed {data_type} for candidate {candidate_id}. Purpose: {purpose}",
                remediation="Ensure access is within policy and purpose is documented",
                auto_block=False,
            ))

        if data_type == "salary_history":
            # Many jurisdictions prohibit asking for salary history
            findings.append(AuditFinding(
                rule_id="COMP-005",
                severity="critical",
                category="compliance",
                title="Salary history access — check jurisdiction",
                description="Accessing salary history is prohibited in many jurisdictions (NYC, CA, CO, etc.)",
                remediation="Verify state/local law permits salary history inquiry. Use comp expectations instead.",
                auto_block=True,
            ))

        if data_type == "social_media":
            findings.append(AuditFinding(
                rule_id="PRIV-003",
                severity="warning",
                category="privacy",
                title="Social media review — guardrails apply",
                description="Social media reviews must follow documented policy: no protected class info, no friend requests, document only job-relevant findings.",
                remediation="Follow BDHT Social Media Review Policy. Document reviewer name, date, findings summary only.",
                auto_block=False,
            ))

        passed = not any(f.severity == "critical" for f in findings)
        blocked = any(f.auto_block for f in findings)

        return AuditResult(
            action=f"data_access:{data_type}",
            candidate_id=candidate_id,
            job_id="N/A",
            timestamp=timestamp,
            passed=passed,
            findings=findings,
            blocked=blocked,
            block_reason=findings[0].description if blocked else "",
        )

    def _check_compliance_rules(self, from_stage: str, to_stage: str, meta: dict) -> list:
        """EEOC, salary transparency, and legal compliance rules."""
        findings = []
        state = meta.get("location_state", "").upper()
        salary_states = self.config.get("salary_transparency_states", [])

        # Rule COMP-001: Salary transparency
        if to_stage == "offer" and state in salary_states and not meta.get("salary_disclosed"):
            findings.append(AuditFinding(
                rule_id="COMP-001",
                severity="critical",
                category="compliance",
                title="Salary range not disclosed — required by law",
                description=f"State {state} requires salary range disclosure. Cannot extend offer without it.",
                remediation=f"Disclose salary range per {state} salary transparency law before extending offer.",
                auto_block=True,
            ))

        # Rule COMP-002: EEOC — rejection reason required
        if to_stage == "rejected" and not meta.get("rejection_reason"):
            findings.append(AuditFinding(
                rule_id="COMP-002",
                severity="critical",
                category="compliance",
                title="No rejection reason documented",
                description="EEOC best practice requires documented, job-related rejection reasons.",
                remediation="Document specific, job-related reason for rejection before finalizing.",
                auto_block=True,
            ))

        # Rule COMP-003: Consistent process (adverse impact prevention)
        if to_stage == "interview" and meta.get("interviewer_count", 0) < 2:
            findings.append(AuditFinding(
                rule_id="COMP-003",
                severity="warning",
                category="compliance",
                title="Single interviewer — bias risk",
                description="Best practice requires 2+ interviewers to reduce individual bias.",
                remediation="Add at least one additional interviewer to the panel.",
                auto_block=False,
            ))

        return findings

    def _check_process_rules(self, from_stage: str, to_stage: str, meta: dict) -> list:
        """Pipeline integrity rules."""
        findings = []
        stage_order = self.config.get("stage_order", [
            "applied", "screening", "interview", "assessment", "reference_check", "offer", "hired"
        ])

        # Rule PROC-001: No stage skipping
        if from_stage in stage_order and to_stage in stage_order:
            from_idx = stage_order.index(from_stage)
            to_idx = stage_order.index(to_stage)
            if to_idx > from_idx + 1 and to_stage != "rejected":
                skipped = stage_order[from_idx + 1:to_idx]
                findings.append(AuditFinding(
                    rule_id="PROC-001",
                    severity="warning",
                    category="process",
                    title="Stage(s) skipped in pipeline",
                    description=f"Skipped: {', '.join(skipped)}. From {from_stage} directly to {to_stage}.",
                    remediation="Document justification for skipping stages or process them in order.",
                    auto_block=False,
                ))

        # Rule PROC-002: Scorecard required before advancing past interview
        if from_stage == "interview" and to_stage in ("assessment", "reference_check", "offer") and not meta.get("has_scorecard"):
            findings.append(AuditFinding(
                rule_id="PROC-002",
                severity="critical",
                category="process",
                title="No interview scorecard submitted",
                description="Cannot advance candidate past interview without completed scorecard.",
                remediation="Complete and submit interview scorecard with structured ratings.",
                auto_block=True,
            ))

        # Rule PROC-003: Approval required for offer
        if to_stage == "offer" and not meta.get("approver"):
            findings.append(AuditFinding(
                rule_id="PROC-003",
                severity="critical",
                category="process",
                title="Offer extended without approval",
                description="All offers require hiring manager + HR approval.",
                remediation="Obtain documented approval from hiring manager and HR before extending offer.",
                auto_block=True,
            ))

        # Rule PROC-004: Stale candidate alert
        days = meta.get("days_in_current_stage", 0)
        max_days = self.config.get("max_days_per_stage", {}).get(from_stage, 14)
        if days > max_days:
            findings.append(AuditFinding(
                rule_id="PROC-004",
                severity="warning",
                category="process",
                title="Candidate stale in pipeline",
                description=f"Candidate has been in '{from_stage}' for {days} days (max: {max_days}).",
                remediation="Either advance, reject, or document reason for delay.",
                auto_block=False,
            ))

        return findings

    def _check_privacy_rules(self, from_stage: str, to_stage: str, meta: dict) -> list:
        """Candidate data privacy and handling rules."""
        findings = []

        # Rule PRIV-002: Background check consent
        if to_stage == "reference_check" and not meta.get("background_consent"):
            findings.append(AuditFinding(
                rule_id="PRIV-002",
                severity="critical",
                category="privacy",
                title="Background check without consent",
                description="FCRA requires written candidate consent before initiating background checks.",
                remediation="Obtain signed FCRA authorization form before proceeding.",
                auto_block=True,
            ))

        # Rule PRIV-004: Data retention on rejection
        if to_stage == "rejected":
            retention_days = self.config.get("rejected_data_retention_days", 730)  # 2 years default
            findings.append(AuditFinding(
                rule_id="PRIV-004",
                severity="info",
                category="privacy",
                title="Data retention timer started",
                description=f"Candidate data will be retained for {retention_days} days per policy, then purged.",
                remediation=f"Automatic purge scheduled. Override only if candidate consents to talent pool.",
                auto_block=False,
            ))

        return findings

    def _check_quality_rules(self, from_stage: str, to_stage: str, meta: dict) -> list:
        """Hiring quality and effectiveness metrics."""
        findings = []

        # Rule QUAL-001: Time to hire alert
        total_days = meta.get("total_days_in_pipeline", 0)
        target = self.config.get("target_time_to_hire_days", 45)
        if total_days > target and to_stage not in ("rejected", "hired"):
            findings.append(AuditFinding(
                rule_id="QUAL-001",
                severity="warning",
                category="quality",
                title="Time-to-hire exceeding target",
                description=f"Candidate has been in pipeline for {total_days} days (target: {target}).",
                remediation="Review for bottlenecks. Consider expediting or closing if not progressing.",
                auto_block=False,
            ))

        return findings

    def _default_config(self) -> dict:
        return {
            "salary_transparency_states": ["NY", "CA", "CO", "WA", "CT", "MD", "NV", "RI", "HI"],
            "stage_order": ["applied", "screening", "interview", "assessment", "reference_check", "offer", "hired"],
            "max_days_per_stage": {
                "applied": 5,
                "screening": 7,
                "interview": 14,
                "assessment": 10,
                "reference_check": 10,
                "offer": 7,
            },
            "target_time_to_hire_days": 45,
            "rejected_data_retention_days": 730,
        }
