"""Cross-framework control overlap analysis.

Identifies controls across different compliance frameworks that share the same
underlying requirements — enabling "fix once, comply with many" remediation
strategies.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from app.engine.compliance.frameworks import (
    FRAMEWORK_REGISTRY,
    ComplianceFramework,
    Control,
)

logger = logging.getLogger(__name__)


@dataclass
class OverlapEntry:
    """A group of controls from different frameworks that share the same requirement."""
    topic: str
    description: str
    controls: list[ControlRef] = field(default_factory=list)
    audit_signal_ids: set[int] = field(default_factory=set)

    @property
    def framework_count(self) -> int:
        return len({c.framework_id for c in self.controls})

    @property
    def framework_ids(self) -> list[str]:
        return sorted({c.framework_id for c in self.controls})


@dataclass(frozen=True)
class ControlRef:
    """Reference to a specific control within a framework."""
    framework_id: str
    framework_name: str
    control_id: str
    control_title: str


@dataclass
class CrossFrameworkReport:
    """Complete cross-framework overlap analysis."""
    overlaps: list[OverlapEntry]
    total_unique_requirements: int
    frameworks_analyzed: list[str]

    @property
    def high_value_overlaps(self) -> list[OverlapEntry]:
        """Overlaps spanning 3+ frameworks — highest ROI for remediation."""
        return [o for o in self.overlaps if o.framework_count >= 3]

    def savings_summary(self) -> dict[str, int]:
        """Count of controls satisfied per framework through shared remediation."""
        savings: dict[str, int] = {}
        for overlap in self.high_value_overlaps:
            for ctrl in overlap.controls:
                savings[ctrl.framework_id] = savings.get(ctrl.framework_id, 0) + 1
        return savings

    def for_framework(self, framework_id: str) -> list[OverlapEntry]:
        return [
            o for o in self.overlaps
            if any(c.framework_id == framework_id for c in o.controls)
        ]


# ---------------------------------------------------------------------------
# Curated overlap mappings based on actual regulatory cross-walks
# ---------------------------------------------------------------------------

_OVERLAP_DEFINITIONS: list[dict] = [
    {
        "topic": "Encryption at Rest",
        "description": "Data stored in databases, file systems, and backups must be encrypted using strong algorithms.",
        "controls": {
            "soc2": ["CC6.1", "C1.1"],
            "gdpr": ["GDPR-32"],
            "hipaa": ["HIPAA-312a2iv"],
            "dpdp": ["DPDP-8b"],
            "iso27001": ["A.8.24"],
            "ccpa": ["CCPA-1798.185"],
        },
        "audit_signals": {4, 5, 9},
    },
    {
        "topic": "Encryption in Transit",
        "description": "All data transmitted over networks must use TLS 1.2+ or equivalent encryption.",
        "controls": {
            "soc2": ["CC6.7"],
            "gdpr": ["GDPR-32", "GDPR-5.1f"],
            "hipaa": ["HIPAA-312e1", "HIPAA-312e2"],
            "dpdp": ["DPDP-8b"],
            "iso27001": ["A.5.14", "A.8.24"],
            "ccpa": ["CCPA-1798.185"],
        },
        "audit_signals": {5, 8},
    },
    {
        "topic": "Access Control and Least Privilege",
        "description": "Logical access restricted to authorized users with minimum necessary permissions.",
        "controls": {
            "soc2": ["CC6.1", "CC6.3"],
            "gdpr": ["GDPR-32", "GDPR-25"],
            "hipaa": ["HIPAA-308a4", "HIPAA-312a1"],
            "dpdp": ["DPDP-8b"],
            "iso27001": ["A.5.15", "A.8.2", "A.8.3"],
            "ccpa": ["CCPA-1798.185"],
        },
        "audit_signals": {1, 2},
    },
    {
        "topic": "Multi-factor Authentication",
        "description": "MFA required for privileged access and sensitive data access.",
        "controls": {
            "soc2": ["CC6.1"],
            "gdpr": ["GDPR-32"],
            "hipaa": ["HIPAA-312d"],
            "iso27001": ["A.8.5", "A.5.17"],
        },
        "audit_signals": {1, 5},
    },
    {
        "topic": "Audit Logging and Monitoring",
        "description": "Systems produce tamper-resistant audit logs of security-relevant events; logs are monitored.",
        "controls": {
            "soc2": ["CC7.2", "CC7.3", "CC4.1"],
            "gdpr": ["GDPR-30"],
            "hipaa": ["HIPAA-312b", "HIPAA-308a5iii"],
            "iso27001": ["A.8.15", "A.8.16", "A.5.25"],
            "ccpa": ["CCPA-1798.199.40"],
        },
        "audit_signals": {25, 26, 27, 28},
    },
    {
        "topic": "Incident Response and Breach Notification",
        "description": "Documented incident response plan with breach notification procedures and timelines.",
        "controls": {
            "soc2": ["CC7.4", "CC7.5"],
            "gdpr": ["GDPR-33", "GDPR-34"],
            "hipaa": ["HIPAA-308a6"],
            "dpdp": ["DPDP-8c"],
            "iso27001": ["A.5.24", "A.5.26", "A.5.27"],
        },
        "audit_signals": {28, 36},
    },
    {
        "topic": "Data Retention and Disposal",
        "description": "Data retained only as long as necessary; secure disposal when no longer needed.",
        "controls": {
            "soc2": ["PI1.5", "C1.2", "P4.1"],
            "gdpr": ["GDPR-5.1e", "GDPR-17"],
            "hipaa": ["HIPAA-310d1"],
            "dpdp": ["DPDP-8d"],
            "iso27001": ["A.8.10", "A.7.14"],
            "ccpa": ["CCPA-1798.105"],
        },
        "audit_signals": {4, 9, 35},
    },
    {
        "topic": "Data Subject / Consumer Access Rights",
        "description": "Individuals can access, correct, and obtain copies of their personal data.",
        "controls": {
            "soc2": ["P5.1", "P5.2"],
            "gdpr": ["GDPR-15", "GDPR-16", "GDPR-20"],
            "dpdp": ["DPDP-11", "DPDP-12"],
            "ccpa": ["CCPA-1798.100", "CCPA-1798.106", "CCPA-1798.110"],
        },
        "audit_signals": {1, 4, 16, 31, 35},
    },
    {
        "topic": "Right to Erasure / Deletion",
        "description": "Individuals can request deletion of their personal data under defined conditions.",
        "controls": {
            "soc2": ["P4.1"],
            "gdpr": ["GDPR-17"],
            "dpdp": ["DPDP-12"],
            "ccpa": ["CCPA-1798.105"],
        },
        "audit_signals": {4, 9, 35},
    },
    {
        "topic": "Consent Management",
        "description": "Obtaining, recording, and managing user consent for data processing.",
        "controls": {
            "soc2": ["P2.1", "P3.2"],
            "gdpr": ["GDPR-7"],
            "dpdp": ["DPDP-5", "DPDP-6"],
            "ccpa": ["CCPA-1798.120"],
        },
        "audit_signals": {4, 35},
    },
    {
        "topic": "Vulnerability Management",
        "description": "Regular scanning, patching, and remediation of technical vulnerabilities.",
        "controls": {
            "soc2": ["CC7.1"],
            "gdpr": ["GDPR-32"],
            "hipaa": ["HIPAA-308a1"],
            "iso27001": ["A.8.8", "A.8.7"],
            "ccpa": ["CCPA-1798.185"],
        },
        "audit_signals": {11, 19, 22, 25, 29},
    },
    {
        "topic": "Vendor / Third-Party Risk Management",
        "description": "Assessing and managing security risks from suppliers and service providers.",
        "controls": {
            "soc2": ["CC9.2", "P6.1", "P6.2"],
            "gdpr": ["GDPR-28"],
            "hipaa": ["HIPAA-308b1"],
            "dpdp": ["DPDP-16"],
            "iso27001": ["A.5.19", "A.5.20", "A.5.21", "A.5.22"],
            "ccpa": ["CCPA-1798.140-SP"],
        },
        "audit_signals": {22, 35},
    },
    {
        "topic": "Backup and Disaster Recovery",
        "description": "Regular backups, tested recovery procedures, and business continuity planning.",
        "controls": {
            "soc2": ["A1.2", "A1.3"],
            "hipaa": ["HIPAA-308a7i", "HIPAA-308a7ii"],
            "iso27001": ["A.8.13", "A.8.14", "A.5.30"],
        },
        "audit_signals": {9, 13, 14, 36},
    },
    {
        "topic": "Change Management",
        "description": "Authorized, documented, and tested changes to production systems.",
        "controls": {
            "soc2": ["CC8.1"],
            "iso27001": ["A.8.32", "A.8.9"],
            "hipaa": ["HIPAA-308a8"],
        },
        "audit_signals": {21, 29, 39},
    },
    {
        "topic": "Data Minimisation and Purpose Limitation",
        "description": "Collect only data necessary for stated purposes; do not repurpose without consent.",
        "controls": {
            "soc2": ["P3.1"],
            "gdpr": ["GDPR-5.1b", "GDPR-5.1c"],
            "dpdp": ["DPDP-4"],
            "ccpa": ["CCPA-1798.100"],
        },
        "audit_signals": {4, 9, 35},
    },
    {
        "topic": "Data Protection Impact Assessment",
        "description": "Risk assessment conducted before high-risk data processing activities.",
        "controls": {
            "gdpr": ["GDPR-35"],
            "dpdp": ["DPDP-9"],
            "iso27001": ["A.5.35"],
        },
        "audit_signals": {23, 29, 35, 40},
    },
    {
        "topic": "Cross-border Data Transfers",
        "description": "Adequate safeguards when transferring personal data internationally.",
        "controls": {
            "gdpr": ["GDPR-44", "GDPR-46"],
            "dpdp": ["DPDP-16"],
        },
        "audit_signals": {4, 8, 35},
    },
    {
        "topic": "Secure Development Lifecycle",
        "description": "Security integrated into software development process with secure coding practices.",
        "controls": {
            "soc2": ["CC5.2", "CC8.1"],
            "iso27001": ["A.8.25", "A.8.26", "A.8.28"],
        },
        "audit_signals": {3, 21, 29, 30},
    },
    {
        "topic": "Input Validation and Injection Prevention",
        "description": "All user input validated/sanitized to prevent injection, XSS, and related attacks.",
        "controls": {
            "soc2": ["CC6.8", "PI1.2"],
            "iso27001": ["A.8.26", "A.8.28"],
        },
        "audit_signals": {3, 30},
    },
    {
        "topic": "Network Segmentation and Boundary Protection",
        "description": "Network boundaries defined and protected; internal segmentation isolates sensitive systems.",
        "controls": {
            "soc2": ["CC6.6"],
            "hipaa": ["HIPAA-310a1"],
            "iso27001": ["A.8.20", "A.8.21", "A.8.22"],
        },
        "audit_signals": {8, 19, 34},
    },
    {
        "topic": "Security Testing and Evaluation",
        "description": "Regular security testing including penetration testing and code reviews.",
        "controls": {
            "soc2": ["CC7.1"],
            "hipaa": ["HIPAA-308a8"],
            "iso27001": ["A.8.29", "A.8.34"],
            "ccpa": ["CCPA-1798.199.40"],
        },
        "audit_signals": {19, 29},
    },
    {
        "topic": "Data Integrity Controls",
        "description": "Mechanisms to ensure data is not improperly altered and maintains accuracy.",
        "controls": {
            "soc2": ["PI1.3", "PI1.4"],
            "gdpr": ["GDPR-5.1d"],
            "hipaa": ["HIPAA-312c1"],
            "dpdp": ["DPDP-8a"],
            "iso27001": ["A.5.33"],
        },
        "audit_signals": {4, 5, 16},
    },
    {
        "topic": "Automated Decision-Making and AI Risks",
        "description": "Safeguards around automated decision-making, profiling, and AI/ML systems.",
        "controls": {
            "gdpr": ["GDPR-22"],
            "dpdp": ["DPDP-14"],
        },
        "audit_signals": {23, 24},
    },
    {
        "topic": "User Credential and Session Management",
        "description": "Secure handling of credentials, session tokens, and automatic logoff for inactive sessions.",
        "controls": {
            "soc2": ["CC6.1", "CC6.5"],
            "hipaa": ["HIPAA-308a5iv", "HIPAA-312a2ii"],
            "iso27001": ["A.5.17", "A.8.5"],
        },
        "audit_signals": {1, 5, 38},
    },
    {
        "topic": "Availability and Redundancy",
        "description": "System architecture ensures high availability via redundancy and failover.",
        "controls": {
            "soc2": ["A1.1", "A1.2"],
            "iso27001": ["A.8.14", "A.7.11"],
            "hipaa": ["HIPAA-308a7iii"],
        },
        "audit_signals": {13, 14, 17, 20},
    },
    {
        "topic": "Capacity Management",
        "description": "Resource usage monitored and planned to meet current and future demand.",
        "controls": {
            "soc2": ["A1.1"],
            "iso27001": ["A.8.6"],
        },
        "audit_signals": {7, 20, 25},
    },
    {
        "topic": "Privacy Notice and Transparency",
        "description": "Clear, accessible privacy notices describing data practices and individual rights.",
        "controls": {
            "soc2": ["P1.1"],
            "gdpr": ["GDPR-12", "GDPR-13"],
            "dpdp": ["DPDP-5"],
            "ccpa": ["CCPA-1798.130", "CCPA-1798.135"],
        },
        "audit_signals": {32, 35},
    },
    {
        "topic": "Segregation of Duties",
        "description": "No single individual can authorize, execute, and record a transaction end-to-end.",
        "controls": {
            "soc2": ["CC5.1"],
            "iso27001": ["A.5.3"],
        },
        "audit_signals": {2, 35, 40},
    },
    {
        "topic": "Security Awareness Training",
        "description": "Personnel receive regular security awareness training and reminders.",
        "controls": {
            "soc2": ["CC1.4"],
            "hipaa": ["HIPAA-308a5i"],
            "iso27001": ["A.6.3"],
        },
        "audit_signals": {35, 40},
    },
    {
        "topic": "Malware Prevention",
        "description": "Controls to prevent, detect, and respond to malicious software.",
        "controls": {
            "soc2": ["CC6.8"],
            "hipaa": ["HIPAA-308a5ii"],
            "iso27001": ["A.8.7"],
        },
        "audit_signals": {3, 11, 19, 22},
    },
    {
        "topic": "Separation of Environments",
        "description": "Development, testing, and production environments are logically or physically separated.",
        "controls": {
            "soc2": ["CC5.2"],
            "iso27001": ["A.8.31"],
        },
        "audit_signals": {19, 21},
    },
]


class CrossFrameworkMapper:
    """Identifies and reports overlapping controls across compliance frameworks."""

    def __init__(
        self,
        framework_ids: list[str] | None = None,
    ):
        if framework_ids:
            self._frameworks = {
                fid: FRAMEWORK_REGISTRY[fid]
                for fid in framework_ids
                if fid in FRAMEWORK_REGISTRY
            }
        else:
            self._frameworks = dict(FRAMEWORK_REGISTRY)

    def analyze(self) -> CrossFrameworkReport:
        overlaps = self._build_overlaps()
        overlaps.sort(key=lambda o: -o.framework_count)

        return CrossFrameworkReport(
            overlaps=overlaps,
            total_unique_requirements=len(overlaps),
            frameworks_analyzed=sorted(self._frameworks.keys()),
        )

    def find_overlaps_for_control(self, framework_id: str, control_id: str) -> list[OverlapEntry]:
        report = self.analyze()
        return [
            o for o in report.overlaps
            if any(
                c.framework_id == framework_id and c.control_id == control_id
                for c in o.controls
            )
        ]

    def remediation_priority(self) -> list[dict]:
        """Rank overlap topics by cross-framework impact for remediation prioritization."""
        report = self.analyze()
        items = []
        for overlap in report.overlaps:
            items.append({
                "topic": overlap.topic,
                "frameworks_covered": overlap.framework_count,
                "total_controls_satisfied": len(overlap.controls),
                "framework_ids": overlap.framework_ids,
                "audit_signal_ids": sorted(overlap.audit_signal_ids),
            })
        items.sort(key=lambda x: (-x["frameworks_covered"], -x["total_controls_satisfied"]))
        return items

    def _build_overlaps(self) -> list[OverlapEntry]:
        overlaps: list[OverlapEntry] = []
        active_fids = set(self._frameworks.keys())

        for defn in _OVERLAP_DEFINITIONS:
            controls: list[ControlRef] = []
            for fid, control_ids in defn["controls"].items():
                if fid not in active_fids:
                    continue
                fw = self._frameworks[fid]
                for cid in control_ids:
                    ctrl = fw.get_control(cid)
                    if ctrl:
                        controls.append(ControlRef(
                            framework_id=fid,
                            framework_name=fw.name,
                            control_id=cid,
                            control_title=ctrl.title,
                        ))

            if len({c.framework_id for c in controls}) < 2:
                continue

            overlaps.append(OverlapEntry(
                topic=defn["topic"],
                description=defn["description"],
                controls=controls,
                audit_signal_ids=set(defn.get("audit_signals", set())),
            ))

        return overlaps

    def overlap_matrix(self) -> dict[str, dict[str, int]]:
        """Build a framework × framework matrix counting shared overlap topics."""
        report = self.analyze()
        fids = sorted(self._frameworks.keys())
        matrix: dict[str, dict[str, int]] = {
            f1: {f2: 0 for f2 in fids} for f1 in fids
        }

        for overlap in report.overlaps:
            present = overlap.framework_ids
            for i, f1 in enumerate(present):
                for f2 in present[i + 1:]:
                    matrix[f1][f2] += 1
                    matrix[f2][f1] += 1

        return matrix
