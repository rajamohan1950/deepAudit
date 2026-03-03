"""Compliance framework definitions with control structures and DeepAudit category mappings.

Each framework contains realistic controls based on the actual published standards.
The audit_signals field maps each control to the DeepAudit category IDs (1-40)
whose analyzers would detect issues relevant to that control.

DeepAudit Category Reference:
 1  Authentication          11 OS/Kernel            21 Deployment/CI-CD     31 API Design
 2  Authorization           12 Graceful Shutdown    22 Supply Chain         32 UX/Accessibility
 3  Input Validation        13 SPOF                 23 AI/ML Risks          33 Cost/FinOps
 4  Data Protection         14 Fault Tolerance      24 AI/ML Operations     34 Multi-tenancy
 5  Cryptography            15 Concurrency          25 Metrics/Monitoring   35 Compliance
 6  Memory                  16 Data Integrity       26 Logging              36 Disaster Recovery
 7  CPU/Compute             17 Distributed Systems  27 Distributed Tracing  37 i18n
 8  Network I/O             18 Queue Processing     28 Alerting/Incident    38 State Management
 9  Database                19 Infra Security       29 Testing/QA           39 Backward Compat
10  Caching                 20 Capacity Planning    30 Code Quality         40 Organizational
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Control:
    control_id: str
    title: str
    description: str
    category: str
    audit_signals: list[int] = field(default_factory=list)


@dataclass(frozen=True)
class ComplianceFramework:
    framework_id: str
    name: str
    jurisdiction: str
    version: str
    controls: list[Control] = field(default_factory=list)

    def get_control(self, control_id: str) -> Control | None:
        for c in self.controls:
            if c.control_id == control_id:
                return c
        return None

    def controls_by_category(self) -> dict[str, list[Control]]:
        grouped: dict[str, list[Control]] = {}
        for c in self.controls:
            grouped.setdefault(c.category, []).append(c)
        return grouped

    @property
    def all_audit_signal_ids(self) -> set[int]:
        ids: set[int] = set()
        for c in self.controls:
            ids.update(c.audit_signals)
        return ids


# ---------------------------------------------------------------------------
# SOC 2 — Trust Services Criteria (2017 with 2022 revisions)
# ---------------------------------------------------------------------------

_SOC2_CONTROLS: list[Control] = [
    # CC1 — Control Environment
    Control("CC1.1", "COSO Principle 1: Integrity and Ethical Values",
            "The entity demonstrates a commitment to integrity and ethical values.",
            "Common Criteria — Control Environment", [35, 40]),
    Control("CC1.2", "COSO Principle 2: Board Independence",
            "The board of directors demonstrates independence from management and exercises oversight.",
            "Common Criteria — Control Environment", [35, 40]),
    Control("CC1.3", "COSO Principle 3: Management Oversight Structures",
            "Management establishes structures, reporting lines, and appropriate authorities.",
            "Common Criteria — Control Environment", [35, 40]),
    Control("CC1.4", "COSO Principle 4: Commitment to Competence",
            "The entity demonstrates commitment to attract, develop, and retain competent individuals.",
            "Common Criteria — Control Environment", [40]),
    Control("CC1.5", "COSO Principle 5: Accountability",
            "The entity holds individuals accountable for their internal control responsibilities.",
            "Common Criteria — Control Environment", [35, 40]),

    # CC2 — Communication and Information
    Control("CC2.1", "COSO Principle 13: Quality Information",
            "The entity obtains or generates relevant, quality information to support internal control.",
            "Common Criteria — Communication", [25, 26, 35]),
    Control("CC2.2", "COSO Principle 14: Internal Communication",
            "The entity internally communicates information necessary to support internal control.",
            "Common Criteria — Communication", [26, 28, 35, 40]),
    Control("CC2.3", "COSO Principle 15: External Communication",
            "The entity communicates with external parties regarding matters affecting internal control.",
            "Common Criteria — Communication", [28, 35, 40]),

    # CC3 — Risk Assessment
    Control("CC3.1", "COSO Principle 6: Risk Assessment Objectives",
            "The entity specifies objectives with sufficient clarity to enable risk identification.",
            "Common Criteria — Risk Assessment", [35, 40]),
    Control("CC3.2", "COSO Principle 7: Risk Identification and Analysis",
            "The entity identifies risks to the achievement of its objectives and analyzes them.",
            "Common Criteria — Risk Assessment", [19, 22, 35, 40]),
    Control("CC3.3", "COSO Principle 8: Fraud Risk Assessment",
            "The entity considers the potential for fraud in assessing risks.",
            "Common Criteria — Risk Assessment", [1, 2, 3, 35]),
    Control("CC3.4", "COSO Principle 9: Change Identification",
            "The entity identifies and assesses changes that could significantly impact internal control.",
            "Common Criteria — Risk Assessment", [21, 35, 39, 40]),

    # CC4 — Monitoring Activities
    Control("CC4.1", "COSO Principle 16: Ongoing and Separate Evaluations",
            "The entity selects, develops, and performs ongoing and/or separate evaluations.",
            "Common Criteria — Monitoring", [25, 26, 27, 28, 29, 35]),
    Control("CC4.2", "COSO Principle 17: Deficiency Communication",
            "The entity evaluates and communicates internal control deficiencies in a timely manner.",
            "Common Criteria — Monitoring", [28, 35, 40]),

    # CC5 — Control Activities
    Control("CC5.1", "COSO Principle 10: Risk-Mitigating Control Activities",
            "The entity selects and develops control activities that contribute to risk mitigation.",
            "Common Criteria — Control Activities", [1, 2, 3, 4, 5, 19, 35]),
    Control("CC5.2", "COSO Principle 11: Technology General Controls",
            "The entity selects and develops general control activities over technology.",
            "Common Criteria — Control Activities", [9, 11, 19, 21, 35]),
    Control("CC5.3", "COSO Principle 12: Control Activity Policies",
            "The entity deploys control activities through policies and procedures.",
            "Common Criteria — Control Activities", [35, 40]),

    # CC6 — Logical and Physical Access Controls
    Control("CC6.1", "Logical Access Security",
            "Logical access security software, infrastructure, and architectures have been implemented.",
            "Common Criteria — Access Controls", [1, 2, 5, 19]),
    Control("CC6.2", "User Registration and Authorization",
            "New internal and external users are registered and authorized prior to access.",
            "Common Criteria — Access Controls", [1, 2, 35]),
    Control("CC6.3", "Role-based Access and Least Privilege",
            "Access to data and software is restricted to authorized users via role-based access.",
            "Common Criteria — Access Controls", [1, 2, 34]),
    Control("CC6.4", "Physical Access Restrictions",
            "Physical access to facilities and protected information is restricted.",
            "Common Criteria — Access Controls", [19, 35]),
    Control("CC6.5", "Logical Access Disposition",
            "Logical access credentials and permissions are removed upon termination.",
            "Common Criteria — Access Controls", [1, 2, 35, 40]),
    Control("CC6.6", "Boundary Protection",
            "System boundaries are protected against unauthorized and malicious traffic.",
            "Common Criteria — Access Controls", [8, 19]),
    Control("CC6.7", "Data Transmission Encryption",
            "Data transmitted between entities is protected.",
            "Common Criteria — Access Controls", [5, 8]),
    Control("CC6.8", "Malicious Software Prevention",
            "Controls exist to prevent or detect and act upon introduction of malicious software.",
            "Common Criteria — Access Controls", [3, 11, 19, 22]),

    # CC7 — System Operations
    Control("CC7.1", "Vulnerability Management",
            "Infrastructure and software are monitored for vulnerabilities.",
            "Common Criteria — System Operations", [19, 22, 25, 29]),
    Control("CC7.2", "Anomaly and Event Monitoring",
            "Anomalous activity and security events are monitored and evaluated.",
            "Common Criteria — System Operations", [25, 26, 27, 28]),
    Control("CC7.3", "Security Event Evaluation",
            "Detected security events are evaluated to determine whether they constitute incidents.",
            "Common Criteria — System Operations", [26, 28]),
    Control("CC7.4", "Incident Response",
            "The entity responds to identified security incidents by executing a defined process.",
            "Common Criteria — System Operations", [28, 36, 40]),
    Control("CC7.5", "Incident Recovery",
            "The entity identifies, develops, and implements activities to recover from incidents.",
            "Common Criteria — System Operations", [14, 28, 36]),

    # CC8 — Change Management
    Control("CC8.1", "Change Management Process",
            "Changes to infrastructure, data, software, and procedures are authorized and managed.",
            "Common Criteria — Change Management", [21, 29, 35, 39]),

    # CC9 — Risk Mitigation
    Control("CC9.1", "Risk Identification and Acceptance",
            "The entity identifies, selects, and develops risk mitigation activities for risks.",
            "Common Criteria — Risk Mitigation", [19, 22, 35, 40]),
    Control("CC9.2", "Vendor and Business Partner Risk",
            "The entity assesses and manages risks associated with vendors and business partners.",
            "Common Criteria — Risk Mitigation", [22, 35, 40]),

    # A1 — Availability
    Control("A1.1", "Availability Commitment and Requirements",
            "The entity maintains capacity to meet availability commitments and requirements.",
            "Availability", [13, 14, 17, 20]),
    Control("A1.2", "Environmental Protections and Redundancy",
            "Environmental protections, software, data backup, and recovery provide redundancy.",
            "Availability", [9, 13, 14, 36]),
    Control("A1.3", "Recovery Testing",
            "The entity tests recovery plan procedures supporting system recovery.",
            "Availability", [29, 36]),

    # PI1 — Processing Integrity
    Control("PI1.1", "Processing Integrity Definitions",
            "The entity obtains or generates information about processing integrity commitments.",
            "Processing Integrity", [16, 35]),
    Control("PI1.2", "System Input Controls",
            "System inputs are complete, accurate, and processed in a timely manner.",
            "Processing Integrity", [3, 16]),
    Control("PI1.3", "System Processing Controls",
            "System processing is complete, accurate, timely, and authorized.",
            "Processing Integrity", [15, 16, 18]),
    Control("PI1.4", "System Output Controls",
            "System output is complete, accurate, stored, and distributed timely.",
            "Processing Integrity", [16, 31]),
    Control("PI1.5", "Data Retention and Disposal",
            "Data stored by the entity is complete, accurate, and protected during retention.",
            "Processing Integrity", [4, 9, 16, 35]),

    # C1 — Confidentiality
    Control("C1.1", "Confidential Information Identification",
            "Confidential information is identified and protected during collection and creation.",
            "Confidentiality", [4, 5, 26, 35]),
    Control("C1.2", "Confidential Information Disposal",
            "Confidential information is disposed of in accordance with policy.",
            "Confidentiality", [4, 9, 35]),

    # P1-P8 — Privacy
    Control("P1.1", "Privacy Notice",
            "The entity provides notice about its privacy practices.",
            "Privacy", [35]),
    Control("P2.1", "Privacy Choice and Consent",
            "The entity provides opt-in/opt-out choices for data collection and use.",
            "Privacy", [4, 35]),
    Control("P3.1", "Personal Information Collection",
            "Personal information is collected consistent with the entity's objectives.",
            "Privacy", [4, 35]),
    Control("P3.2", "Explicit Consent for Sensitive Data",
            "Explicit consent is obtained for collection of sensitive personal information.",
            "Privacy", [4, 35]),
    Control("P4.1", "Personal Information Use and Retention",
            "Personal information is used, retained, and disposed of consistent with policies.",
            "Privacy", [4, 9, 35]),
    Control("P5.1", "Subject Access Rights",
            "The entity grants identified and authenticated data subjects the ability to access data.",
            "Privacy", [1, 4, 35]),
    Control("P5.2", "Correction Requests",
            "The entity corrects personal information upon request from data subjects.",
            "Privacy", [4, 16, 35]),
    Control("P6.1", "Disclosure to Third Parties",
            "Personal information is disclosed to third parties only for identified purposes.",
            "Privacy", [4, 22, 35]),
    Control("P6.2", "Third-Party Privacy Compliance",
            "Personal information disclosed to third parties is protected per agreements.",
            "Privacy", [4, 22, 35]),
    Control("P7.1", "Data Quality",
            "The entity collects and maintains accurate, up-to-date, complete personal information.",
            "Privacy", [4, 16, 35]),
    Control("P8.1", "Privacy Complaints and Disputes",
            "The entity has a process for receiving and resolving complaints and disputes.",
            "Privacy", [28, 35, 40]),
]

SOC2 = ComplianceFramework(
    framework_id="soc2",
    name="SOC 2 Type II",
    jurisdiction="United States (AICPA)",
    version="2017 Trust Services Criteria (2022 revision)",
    controls=_SOC2_CONTROLS,
)


# ---------------------------------------------------------------------------
# GDPR — General Data Protection Regulation
# ---------------------------------------------------------------------------

_GDPR_CONTROLS: list[Control] = [
    Control("GDPR-5.1a", "Lawfulness, Fairness, and Transparency",
            "Personal data shall be processed lawfully, fairly and in a transparent manner.",
            "Principles", [4, 35]),
    Control("GDPR-5.1b", "Purpose Limitation",
            "Personal data collected for specified, explicit and legitimate purposes only.",
            "Principles", [4, 35]),
    Control("GDPR-5.1c", "Data Minimisation",
            "Personal data shall be adequate, relevant and limited to what is necessary.",
            "Principles", [4, 9, 35]),
    Control("GDPR-5.1d", "Accuracy",
            "Personal data shall be accurate and kept up to date.",
            "Principles", [4, 16, 35]),
    Control("GDPR-5.1e", "Storage Limitation",
            "Personal data kept in identifying form no longer than necessary.",
            "Principles", [4, 9, 35]),
    Control("GDPR-5.1f", "Integrity and Confidentiality",
            "Appropriate security of personal data including protection against unauthorized processing.",
            "Principles", [4, 5, 19, 35]),
    Control("GDPR-6", "Lawful Basis for Processing",
            "Processing lawful only if at least one legal basis applies (consent, contract, etc.).",
            "Lawfulness", [4, 35]),
    Control("GDPR-7", "Conditions for Consent",
            "Controller shall be able to demonstrate that consent was given, freely, specifically.",
            "Consent", [4, 35]),
    Control("GDPR-9", "Special Categories of Data",
            "Processing of special category data (health, biometric, etc.) prohibited unless exception applies.",
            "Special Data", [4, 23, 35]),
    Control("GDPR-12", "Transparent Communication",
            "Controller provides information in concise, transparent, intelligible and easily accessible form.",
            "Data Subject Rights", [35, 32]),
    Control("GDPR-13", "Information at Collection",
            "Where personal data are collected from data subject, controller provides identity and purpose.",
            "Data Subject Rights", [4, 35]),
    Control("GDPR-15", "Right of Access",
            "Data subject has right to obtain confirmation and access to their personal data.",
            "Data Subject Rights", [1, 4, 35]),
    Control("GDPR-16", "Right to Rectification",
            "Data subject has right to obtain rectification of inaccurate personal data.",
            "Data Subject Rights", [4, 16, 35]),
    Control("GDPR-17", "Right to Erasure (Right to be Forgotten)",
            "Data subject has right to obtain erasure of personal data without undue delay.",
            "Data Subject Rights", [4, 9, 35]),
    Control("GDPR-18", "Right to Restriction of Processing",
            "Data subject has right to restrict processing under certain conditions.",
            "Data Subject Rights", [4, 35]),
    Control("GDPR-20", "Right to Data Portability",
            "Data subject has right to receive data in structured, machine-readable format.",
            "Data Subject Rights", [4, 31, 35]),
    Control("GDPR-22", "Automated Decision-Making and Profiling",
            "Right not to be subject to solely automated decision-making, including profiling.",
            "Data Subject Rights", [23, 24, 35]),
    Control("GDPR-25", "Data Protection by Design and Default",
            "Controller implements appropriate technical measures for data protection by design.",
            "Controller Obligations", [4, 5, 9, 30, 35]),
    Control("GDPR-28", "Processor Obligations",
            "Processing by a processor governed by contract with sufficient guarantees.",
            "Controller Obligations", [22, 35]),
    Control("GDPR-30", "Records of Processing Activities",
            "Controller maintains record of processing activities under its responsibility.",
            "Controller Obligations", [26, 35]),
    Control("GDPR-32", "Security of Processing",
            "Controller implements appropriate technical and organizational measures for security.",
            "Security", [1, 2, 4, 5, 8, 19, 35]),
    Control("GDPR-33", "Breach Notification to Authority",
            "Controller notifies supervisory authority within 72 hours of becoming aware of breach.",
            "Breach Notification", [26, 28, 35]),
    Control("GDPR-34", "Breach Notification to Data Subject",
            "Controller communicates personal data breach to data subject without undue delay.",
            "Breach Notification", [28, 35]),
    Control("GDPR-35", "Data Protection Impact Assessment",
            "Controller carries out DPIA where processing likely to result in high risk.",
            "DPIA", [23, 35, 40]),
    Control("GDPR-37", "Designation of DPO",
            "Controller and processor designate a data protection officer where required.",
            "DPO", [35, 40]),
    Control("GDPR-44", "General Principle for Transfers",
            "Transfer of personal data to third countries subject to adequate safeguards.",
            "Cross-border Transfers", [4, 8, 35]),
    Control("GDPR-46", "Appropriate Safeguards for Transfers",
            "Transfers may take place with appropriate safeguards (SCCs, BCRs, etc.).",
            "Cross-border Transfers", [4, 5, 8, 35]),
    Control("GDPR-47", "Binding Corporate Rules",
            "Binding corporate rules approved by supervisory authority for intra-group transfers.",
            "Cross-border Transfers", [35, 40]),
    Control("GDPR-49", "Derogations for Specific Situations",
            "Transfers permissible based on explicit consent, contract necessity, or public interest.",
            "Cross-border Transfers", [4, 35]),
]

GDPR = ComplianceFramework(
    framework_id="gdpr",
    name="General Data Protection Regulation",
    jurisdiction="European Union",
    version="Regulation (EU) 2016/679",
    controls=_GDPR_CONTROLS,
)


# ---------------------------------------------------------------------------
# HIPAA — Security Rule (§164.308–312)
# ---------------------------------------------------------------------------

_HIPAA_CONTROLS: list[Control] = [
    # Administrative Safeguards — §164.308
    Control("HIPAA-308a1", "Security Management Process",
            "Implement policies and procedures to prevent, detect, contain and correct security violations.",
            "Administrative Safeguards", [19, 26, 28, 35, 40]),
    Control("HIPAA-308a2", "Assigned Security Responsibility",
            "Identify the security official responsible for development and implementation of policies.",
            "Administrative Safeguards", [35, 40]),
    Control("HIPAA-308a3i", "Authorization/Supervision — Workforce Security",
            "Implement procedures for authorization and/or supervision of workforce members.",
            "Administrative Safeguards", [1, 2, 35, 40]),
    Control("HIPAA-308a3ii", "Workforce Clearance Procedure",
            "Implement procedures to determine that access is appropriate for workforce members.",
            "Administrative Safeguards", [1, 2, 35]),
    Control("HIPAA-308a3iii", "Termination Procedures",
            "Implement procedures for terminating access to ePHI when employment ends.",
            "Administrative Safeguards", [1, 2, 35]),
    Control("HIPAA-308a4", "Information Access Management",
            "Implement policies for authorizing access to ePHI consistent with applicable requirements.",
            "Administrative Safeguards", [1, 2, 34, 35]),
    Control("HIPAA-308a5i", "Security Awareness — Reminders",
            "Periodic security reminders to workforce members.",
            "Administrative Safeguards", [35, 40]),
    Control("HIPAA-308a5ii", "Protection from Malicious Software",
            "Procedures for guarding against, detecting, and reporting malicious software.",
            "Administrative Safeguards", [11, 19, 22]),
    Control("HIPAA-308a5iii", "Login Monitoring",
            "Procedures for monitoring log-in attempts and reporting discrepancies.",
            "Administrative Safeguards", [1, 26, 28]),
    Control("HIPAA-308a5iv", "Password Management",
            "Procedures for creating, changing, and safeguarding passwords.",
            "Administrative Safeguards", [1, 5]),
    Control("HIPAA-308a6", "Security Incident Procedures",
            "Implement policies and procedures to address security incidents.",
            "Administrative Safeguards", [26, 28, 36]),
    Control("HIPAA-308a7i", "Contingency Plan — Data Backup",
            "Establish and implement procedures to create and maintain retrievable copies of ePHI.",
            "Administrative Safeguards", [9, 36]),
    Control("HIPAA-308a7ii", "Disaster Recovery Plan",
            "Establish procedures to restore any loss of data.",
            "Administrative Safeguards", [14, 36]),
    Control("HIPAA-308a7iii", "Emergency Mode Operation Plan",
            "Establish procedures to enable continuation of critical processes during emergency.",
            "Administrative Safeguards", [12, 14, 36]),
    Control("HIPAA-308a8", "Evaluation",
            "Perform periodic technical and non-technical evaluation of security policies.",
            "Administrative Safeguards", [29, 35]),
    Control("HIPAA-308b1", "Business Associate Contracts",
            "Written contract or arrangement with business associates regarding ePHI.",
            "Administrative Safeguards", [22, 35]),

    # Physical Safeguards — §164.310
    Control("HIPAA-310a1", "Facility Access Controls",
            "Implement policies to limit physical access to electronic information systems.",
            "Physical Safeguards", [19, 35]),
    Control("HIPAA-310b", "Workstation Use",
            "Specify proper functions, manner of use, and physical attributes of workstations.",
            "Physical Safeguards", [11, 35]),
    Control("HIPAA-310c", "Workstation Security",
            "Implement physical safeguards for workstations that access ePHI.",
            "Physical Safeguards", [11, 19, 35]),
    Control("HIPAA-310d1", "Device and Media Controls — Disposal",
            "Implement policies for final disposition of ePHI and hardware/media on which it is stored.",
            "Physical Safeguards", [4, 9, 35]),

    # Technical Safeguards — §164.312
    Control("HIPAA-312a1", "Access Control — Unique User Identification",
            "Assign a unique name and/or number for identifying and tracking user identity.",
            "Technical Safeguards", [1, 2]),
    Control("HIPAA-312a2i", "Emergency Access Procedure",
            "Establish procedures for obtaining necessary ePHI during an emergency.",
            "Technical Safeguards", [1, 2, 36]),
    Control("HIPAA-312a2ii", "Automatic Logoff",
            "Implement electronic procedures that terminate an electronic session after inactivity.",
            "Technical Safeguards", [1, 38]),
    Control("HIPAA-312a2iv", "Encryption and Decryption",
            "Implement mechanism to encrypt and decrypt electronic protected health information.",
            "Technical Safeguards", [4, 5]),
    Control("HIPAA-312b", "Audit Controls",
            "Implement mechanisms to record and examine activity in systems containing ePHI.",
            "Technical Safeguards", [26, 27, 35]),
    Control("HIPAA-312c1", "Integrity Controls",
            "Implement policies to protect ePHI from improper alteration or destruction.",
            "Technical Safeguards", [4, 5, 16]),
    Control("HIPAA-312d", "Person or Entity Authentication",
            "Implement procedures to verify identity of a person or entity seeking access to ePHI.",
            "Technical Safeguards", [1, 5]),
    Control("HIPAA-312e1", "Transmission Security — Integrity Controls",
            "Implement security measures to ensure electronically transmitted ePHI is not improperly modified.",
            "Technical Safeguards", [5, 8, 16]),
    Control("HIPAA-312e2", "Transmission Security — Encryption",
            "Implement mechanism to encrypt ePHI whenever deemed appropriate in transit.",
            "Technical Safeguards", [5, 8]),
]

HIPAA = ComplianceFramework(
    framework_id="hipaa",
    name="HIPAA Security Rule",
    jurisdiction="United States (HHS)",
    version="45 CFR Part 164 Subpart C",
    controls=_HIPAA_CONTROLS,
)


# ---------------------------------------------------------------------------
# DPDP Act — Digital Personal Data Protection Act 2023 (India)
# ---------------------------------------------------------------------------

_DPDP_CONTROLS: list[Control] = [
    Control("DPDP-4", "Grounds for Processing Personal Data",
            "Personal data shall be processed only for a lawful purpose with consent of the data principal.",
            "Consent & Lawfulness", [4, 35]),
    Control("DPDP-5", "Notice for Consent",
            "Data fiduciary gives notice with description of data, purpose, and rights before consent.",
            "Consent & Lawfulness", [4, 35]),
    Control("DPDP-6", "Consent Requirements",
            "Consent must be free, specific, informed, unconditional, and unambiguous.",
            "Consent & Lawfulness", [4, 35]),
    Control("DPDP-7", "Deemed Consent",
            "Consent deemed for specified legitimate uses (employment, emergencies, etc.).",
            "Consent & Lawfulness", [4, 35]),
    Control("DPDP-8a", "Data Fiduciary Obligations — Accuracy and Completeness",
            "Data fiduciary ensures accuracy, completeness and consistency of personal data.",
            "Data Fiduciary Obligations", [4, 16, 35]),
    Control("DPDP-8b", "Data Fiduciary Obligations — Security Safeguards",
            "Data fiduciary implements reasonable security safeguards to prevent data breach.",
            "Data Fiduciary Obligations", [1, 4, 5, 19, 35]),
    Control("DPDP-8c", "Breach Notification",
            "Data fiduciary notifies Data Protection Board and each affected data principal of breach.",
            "Data Fiduciary Obligations", [26, 28, 35]),
    Control("DPDP-8d", "Data Erasure on Purpose Fulfilment",
            "Data fiduciary erases personal data when purpose is fulfilled unless retention required by law.",
            "Data Fiduciary Obligations", [4, 9, 35]),
    Control("DPDP-9", "Significant Data Fiduciary Obligations",
            "Significant data fiduciaries must appoint DPO, conduct DPIA, and perform periodic audits.",
            "Significant Data Fiduciary", [29, 35, 40]),
    Control("DPDP-11", "Right of Access and Correction",
            "Data principal has right to obtain summary of data and identities of processors.",
            "Data Principal Rights", [1, 4, 35]),
    Control("DPDP-12", "Right of Erasure",
            "Data principal may request erasure of personal data and withdrawal of consent.",
            "Data Principal Rights", [4, 9, 35]),
    Control("DPDP-13", "Right of Grievance Redressal",
            "Data principal may lodge complaint with data fiduciary and Data Protection Board.",
            "Data Principal Rights", [28, 35]),
    Control("DPDP-14", "Children's Data Processing",
            "Verifiable consent of parent/guardian before processing children's data; no tracking/profiling.",
            "Children's Data", [4, 23, 35]),
    Control("DPDP-16", "Cross-border Transfer Restrictions",
            "Central Government may restrict transfer of personal data to specified countries.",
            "Cross-border Transfer", [4, 8, 35]),
    Control("DPDP-17", "Exemptions for State and Security",
            "Central Government may exempt processing in the interest of sovereignty, security, public order.",
            "Exemptions", [35]),
]

DPDP = ComplianceFramework(
    framework_id="dpdp",
    name="Digital Personal Data Protection Act",
    jurisdiction="India",
    version="DPDP Act, 2023",
    controls=_DPDP_CONTROLS,
)


# ---------------------------------------------------------------------------
# ISO 27001:2022 — Annex A Controls (all 93)
# ---------------------------------------------------------------------------

_ISO27001_CONTROLS: list[Control] = [
    # Organizational Controls (A.5.1 – A.5.37)
    Control("A.5.1", "Policies for Information Security",
            "Information security policy and topic-specific policies shall be defined and approved.",
            "Organizational", [35, 40]),
    Control("A.5.2", "Information Security Roles and Responsibilities",
            "Information security roles and responsibilities shall be defined and allocated.",
            "Organizational", [35, 40]),
    Control("A.5.3", "Segregation of Duties",
            "Conflicting duties and conflicting areas of responsibility shall be segregated.",
            "Organizational", [2, 35, 40]),
    Control("A.5.4", "Management Responsibilities",
            "Management shall require all personnel to apply information security per established policies.",
            "Organizational", [35, 40]),
    Control("A.5.5", "Contact with Authorities",
            "The organization shall establish and maintain contact with relevant authorities.",
            "Organizational", [28, 35]),
    Control("A.5.6", "Contact with Special Interest Groups",
            "The organization shall establish contact with special interest groups or forums.",
            "Organizational", [35, 40]),
    Control("A.5.7", "Threat Intelligence",
            "Information relating to information security threats shall be collected and analysed.",
            "Organizational", [19, 22, 25, 28]),
    Control("A.5.8", "Information Security in Project Management",
            "Information security shall be integrated into project management.",
            "Organizational", [21, 30, 35]),
    Control("A.5.9", "Inventory of Information and Other Associated Assets",
            "An inventory of information and other associated assets shall be identified and maintained.",
            "Organizational", [4, 9, 35]),
    Control("A.5.10", "Acceptable Use of Information and Other Associated Assets",
            "Rules for acceptable use of information and assets shall be identified and documented.",
            "Organizational", [4, 35, 40]),
    Control("A.5.11", "Return of Assets",
            "Personnel shall return all organizational assets in their possession upon change or termination.",
            "Organizational", [35, 40]),
    Control("A.5.12", "Classification of Information",
            "Information shall be classified according to information security needs.",
            "Organizational", [4, 35]),
    Control("A.5.13", "Labelling of Information",
            "An appropriate set of procedures for labelling shall be developed and implemented.",
            "Organizational", [4, 35]),
    Control("A.5.14", "Information Transfer",
            "Information transfer rules, procedures, or agreements shall be in place for all transfer.",
            "Organizational", [4, 5, 8, 35]),
    Control("A.5.15", "Access Control",
            "Rules to control physical and logical access to information shall be established.",
            "Organizational", [1, 2, 19]),
    Control("A.5.16", "Identity Management",
            "The full life cycle of identities shall be managed.",
            "Organizational", [1, 35]),
    Control("A.5.17", "Authentication Information",
            "Allocation and management of authentication information shall be controlled.",
            "Organizational", [1, 5]),
    Control("A.5.18", "Access Rights",
            "Access rights to information and other associated assets shall be provisioned and reviewed.",
            "Organizational", [1, 2, 34]),
    Control("A.5.19", "Information Security in Supplier Relationships",
            "Processes and procedures for managing information security risks from suppliers.",
            "Organizational", [22, 35]),
    Control("A.5.20", "Addressing Information Security Within Supplier Agreements",
            "Relevant information security requirements shall be established with each supplier.",
            "Organizational", [22, 35]),
    Control("A.5.21", "Managing Information Security in the ICT Supply Chain",
            "Processes and procedures for managing information security risks in the ICT supply chain.",
            "Organizational", [22, 35]),
    Control("A.5.22", "Monitoring, Review and Change Management of Supplier Services",
            "The organization shall regularly monitor, review and manage changes to supplier services.",
            "Organizational", [22, 25, 35]),
    Control("A.5.23", "Information Security for Use of Cloud Services",
            "Processes for acquisition, use, management and exit from cloud services.",
            "Organizational", [19, 33, 35]),
    Control("A.5.24", "Information Security Incident Management Planning and Preparation",
            "The organization shall plan and prepare for managing information security incidents.",
            "Organizational", [28, 36, 40]),
    Control("A.5.25", "Assessment and Decision on Information Security Events",
            "The organization shall assess information security events and decide classification.",
            "Organizational", [26, 28]),
    Control("A.5.26", "Response to Information Security Incidents",
            "Information security incidents shall be responded to in accordance with documented procedures.",
            "Organizational", [28, 36]),
    Control("A.5.27", "Learning from Information Security Incidents",
            "Knowledge gained from information security incidents shall be used to strengthen controls.",
            "Organizational", [28, 35, 40]),
    Control("A.5.28", "Collection of Evidence",
            "Procedures for the identification, collection, acquisition and preservation of evidence.",
            "Organizational", [26, 35]),
    Control("A.5.29", "Information Security During Disruption",
            "The organization shall plan how to maintain information security during disruption.",
            "Organizational", [12, 14, 36]),
    Control("A.5.30", "ICT Readiness for Business Continuity",
            "ICT readiness shall be planned, implemented, maintained and tested for business continuity.",
            "Organizational", [13, 14, 20, 36]),
    Control("A.5.31", "Legal, Statutory, Regulatory and Contractual Requirements",
            "Legal, statutory, regulatory and contractual requirements shall be identified and documented.",
            "Organizational", [35]),
    Control("A.5.32", "Intellectual Property Rights",
            "The organization shall implement appropriate procedures to protect intellectual property rights.",
            "Organizational", [22, 35]),
    Control("A.5.33", "Protection of Records",
            "Records shall be protected from loss, destruction, falsification and unauthorized access.",
            "Organizational", [4, 9, 16, 26]),
    Control("A.5.34", "Privacy and Protection of PII",
            "The organization shall identify and meet PII protection requirements.",
            "Organizational", [4, 35]),
    Control("A.5.35", "Independent Review of Information Security",
            "The organization's approach to information security shall be independently reviewed.",
            "Organizational", [29, 35]),
    Control("A.5.36", "Compliance with Policies, Rules and Standards for Information Security",
            "Compliance with the information security policy shall be regularly reviewed.",
            "Organizational", [29, 35]),
    Control("A.5.37", "Documented Operating Procedures",
            "Operating procedures for information processing facilities shall be documented.",
            "Organizational", [35, 40]),

    # People Controls (A.6.1 – A.6.8)
    Control("A.6.1", "Screening",
            "Background verification checks on all candidates shall be carried out.",
            "People", [35, 40]),
    Control("A.6.2", "Terms and Conditions of Employment",
            "Employment contractual agreements shall state the responsibilities for information security.",
            "People", [35, 40]),
    Control("A.6.3", "Information Security Awareness, Education and Training",
            "Personnel shall receive appropriate information security awareness education and training.",
            "People", [35, 40]),
    Control("A.6.4", "Disciplinary Process",
            "A disciplinary process shall be formalized and communicated for information security violations.",
            "People", [35, 40]),
    Control("A.6.5", "Responsibilities After Termination or Change of Employment",
            "Information security responsibilities that remain valid after termination shall be defined.",
            "People", [1, 2, 35]),
    Control("A.6.6", "Confidentiality or Non-disclosure Agreements",
            "Confidentiality or non-disclosure agreements reflecting information security needs.",
            "People", [35, 40]),
    Control("A.6.7", "Remote Working",
            "Security measures shall be implemented when personnel are working remotely.",
            "People", [1, 5, 8, 19]),
    Control("A.6.8", "Information Security Event Reporting",
            "The organization shall provide a mechanism for personnel to report information security events.",
            "People", [26, 28, 40]),

    # Physical Controls (A.7.1 – A.7.14)
    Control("A.7.1", "Physical Security Perimeters",
            "Security perimeters shall be defined and used to protect areas containing information.",
            "Physical", [19, 35]),
    Control("A.7.2", "Physical Entry",
            "Secure areas shall be protected by appropriate entry controls and access points.",
            "Physical", [19, 35]),
    Control("A.7.3", "Securing Offices, Rooms and Facilities",
            "Physical security for offices, rooms and facilities shall be designed and implemented.",
            "Physical", [19, 35]),
    Control("A.7.4", "Physical Security Monitoring",
            "Premises shall be continuously monitored for unauthorized physical access.",
            "Physical", [19, 25, 35]),
    Control("A.7.5", "Protecting Against Physical and Environmental Threats",
            "Protection against physical and environmental threats shall be designed and implemented.",
            "Physical", [19, 36]),
    Control("A.7.6", "Working in Secure Areas",
            "Security measures for working in secure areas shall be designed and implemented.",
            "Physical", [19, 35]),
    Control("A.7.7", "Clear Desk and Clear Screen",
            "Clear desk rules for papers and clear screen rules for information processing facilities.",
            "Physical", [4, 35]),
    Control("A.7.8", "Equipment Siting and Protection",
            "Equipment shall be sited securely and protected.",
            "Physical", [11, 19]),
    Control("A.7.9", "Security of Assets Off-premises",
            "Off-premises assets shall be protected.",
            "Physical", [4, 5, 19]),
    Control("A.7.10", "Storage Media",
            "Storage media shall be managed through their life cycle.",
            "Physical", [4, 9, 35]),
    Control("A.7.11", "Supporting Utilities",
            "Information processing facilities shall be protected from power failures.",
            "Physical", [13, 14, 20]),
    Control("A.7.12", "Cabling Security",
            "Cables carrying power, data or supporting information services shall be protected.",
            "Physical", [8, 19]),
    Control("A.7.13", "Equipment Maintenance",
            "Equipment shall be maintained correctly to ensure availability and integrity.",
            "Physical", [20, 35]),
    Control("A.7.14", "Secure Disposal or Re-use of Equipment",
            "Items of equipment containing storage media shall be verified to ensure data is removed.",
            "Physical", [4, 9, 35]),

    # Technological Controls (A.8.1 – A.8.34)
    Control("A.8.1", "User Endpoint Devices",
            "Information stored on, processed by or accessible via user endpoint devices shall be protected.",
            "Technological", [1, 4, 5, 11]),
    Control("A.8.2", "Privileged Access Rights",
            "The allocation and use of privileged access rights shall be restricted and managed.",
            "Technological", [1, 2]),
    Control("A.8.3", "Information Access Restriction",
            "Access to information and other associated assets shall be restricted.",
            "Technological", [1, 2, 34]),
    Control("A.8.4", "Access to Source Code",
            "Read and write access to source code, development tools and software libraries shall be managed.",
            "Technological", [2, 21, 30]),
    Control("A.8.5", "Secure Authentication",
            "Secure authentication technologies and procedures shall be established and implemented.",
            "Technological", [1, 5]),
    Control("A.8.6", "Capacity Management",
            "The use of resources shall be monitored and adjusted in line with current and expected needs.",
            "Technological", [7, 20, 25]),
    Control("A.8.7", "Protection Against Malware",
            "Protection against malware shall be implemented and supported by user awareness.",
            "Technological", [3, 11, 19, 22]),
    Control("A.8.8", "Management of Technical Vulnerabilities",
            "Information about technical vulnerabilities shall be obtained and appropriate measures taken.",
            "Technological", [19, 22, 25, 29]),
    Control("A.8.9", "Configuration Management",
            "Configurations including security configurations shall be established and managed.",
            "Technological", [11, 19, 21]),
    Control("A.8.10", "Information Deletion",
            "Information stored in information systems and devices shall be deleted when no longer required.",
            "Technological", [4, 9]),
    Control("A.8.11", "Data Masking",
            "Data masking shall be used in accordance with policies on access control and business requirements.",
            "Technological", [4, 34]),
    Control("A.8.12", "Data Leakage Prevention",
            "Data leakage prevention measures shall be applied to systems and networks containing sensitive data.",
            "Technological", [4, 8, 19, 26]),
    Control("A.8.13", "Information Backup",
            "Backup copies of information, software and systems shall be maintained and regularly tested.",
            "Technological", [9, 36]),
    Control("A.8.14", "Redundancy of Information Processing Facilities",
            "Information processing facilities shall be implemented with redundancy to meet availability.",
            "Technological", [13, 14, 17, 20]),
    Control("A.8.15", "Logging",
            "Logs that record activities, exceptions, faults and other relevant events shall be produced.",
            "Technological", [26, 27]),
    Control("A.8.16", "Monitoring Activities",
            "Networks, systems and applications shall be monitored for anomalous behaviour.",
            "Technological", [25, 26, 28]),
    Control("A.8.17", "Clock Synchronisation",
            "The clocks of information processing systems shall be synchronised to approved time sources.",
            "Technological", [17, 26]),
    Control("A.8.18", "Use of Privileged Utility Programs",
            "The use of utility programs capable of overriding system and application controls shall be restricted.",
            "Technological", [2, 11]),
    Control("A.8.19", "Installation of Software on Operational Systems",
            "Procedures and measures shall be implemented to securely manage software installation.",
            "Technological", [11, 19, 21, 22]),
    Control("A.8.20", "Networks Security",
            "Networks and network devices shall be secured, managed and controlled.",
            "Technological", [8, 19]),
    Control("A.8.21", "Security of Network Services",
            "Security mechanisms, service levels and service requirements of network services shall be managed.",
            "Technological", [8, 19]),
    Control("A.8.22", "Segregation of Networks",
            "Groups of information services, users and information systems shall be segregated.",
            "Technological", [8, 19, 34]),
    Control("A.8.23", "Web Filtering",
            "Access to external websites shall be managed to reduce exposure to malicious content.",
            "Technological", [3, 8, 19]),
    Control("A.8.24", "Use of Cryptography",
            "Rules for the effective use of cryptography including key management shall be defined.",
            "Technological", [5]),
    Control("A.8.25", "Secure Development Life Cycle",
            "Rules for the secure development of software and systems shall be established and applied.",
            "Technological", [3, 21, 29, 30]),
    Control("A.8.26", "Application Security Requirements",
            "Information security requirements shall be identified and specified for application development.",
            "Technological", [1, 2, 3, 4, 5, 30]),
    Control("A.8.27", "Secure System Architecture and Engineering Principles",
            "Principles for engineering secure systems shall be established and applied.",
            "Technological", [13, 14, 17, 19, 30]),
    Control("A.8.28", "Secure Coding",
            "Secure coding principles shall be applied to software development.",
            "Technological", [3, 6, 15, 30]),
    Control("A.8.29", "Security Testing in Development and Acceptance",
            "Security testing processes shall be defined and implemented in the development life cycle.",
            "Technological", [19, 29]),
    Control("A.8.30", "Outsourced Development",
            "The organization shall direct, monitor and review activities related to outsourced development.",
            "Technological", [22, 30]),
    Control("A.8.31", "Separation of Development, Test and Production Environments",
            "Development, testing and production environments shall be separated and secured.",
            "Technological", [19, 21]),
    Control("A.8.32", "Change Management",
            "Changes to information processing facilities and information systems shall be subject to change management.",
            "Technological", [21, 39]),
    Control("A.8.33", "Test Information",
            "Test information shall be appropriately selected, protected and managed.",
            "Technological", [4, 29]),
    Control("A.8.34", "Protection of Information Systems During Audit Testing",
            "Audit tests and other assurance activities involving operational systems shall be planned.",
            "Technological", [29, 35]),
]

ISO27001 = ComplianceFramework(
    framework_id="iso27001",
    name="ISO/IEC 27001:2022",
    jurisdiction="International (ISO)",
    version="2022 (Annex A)",
    controls=_ISO27001_CONTROLS,
)


# ---------------------------------------------------------------------------
# CCPA / CPRA — California Consumer Privacy Act / California Privacy Rights Act
# ---------------------------------------------------------------------------

_CCPA_CONTROLS: list[Control] = [
    Control("CCPA-1798.100", "Right to Know — Collection",
            "Consumers have the right to know what personal information is collected and how it is used.",
            "Consumer Rights", [4, 26, 35]),
    Control("CCPA-1798.105", "Right to Delete",
            "Consumers have the right to request deletion of their personal information.",
            "Consumer Rights", [4, 9, 35]),
    Control("CCPA-1798.106", "Right to Correct",
            "Consumers have the right to request correction of inaccurate personal information.",
            "Consumer Rights", [4, 16, 35]),
    Control("CCPA-1798.110", "Right to Know — Disclosure",
            "Consumers have the right to request disclosure of specific personal information collected.",
            "Consumer Rights", [4, 26, 35]),
    Control("CCPA-1798.115", "Right to Know — Sale and Sharing",
            "Consumers have right to know about sale or sharing of personal information.",
            "Consumer Rights", [4, 35]),
    Control("CCPA-1798.120", "Right to Opt-Out of Sale/Sharing",
            "Consumers have the right to opt-out of sale or sharing of their personal information.",
            "Consumer Rights", [4, 35]),
    Control("CCPA-1798.121", "Right to Limit Sensitive Personal Information",
            "Consumers have right to limit use and disclosure of sensitive personal information.",
            "Consumer Rights", [4, 35]),
    Control("CCPA-1798.125", "Non-discrimination",
            "Business shall not discriminate against consumer for exercising privacy rights.",
            "Consumer Rights", [35]),
    Control("CCPA-1798.130", "Notice and Process Requirements",
            "Businesses shall make available clear methods for submitting privacy requests.",
            "Privacy Notice", [31, 35]),
    Control("CCPA-1798.135", "Do Not Sell or Share Link",
            "Homepage shall include a clear link titled 'Do Not Sell or Share My Personal Information'.",
            "Privacy Notice", [32, 35]),
    Control("CCPA-1798.140-PI", "Personal Information Inventory",
            "Business shall maintain an inventory of categories of personal information collected.",
            "Data Inventory", [4, 9, 26, 35]),
    Control("CCPA-1798.140-SP", "Service Provider Obligations",
            "Service providers limited to processing personal information per written contract.",
            "Service Providers", [22, 35]),
    Control("CCPA-1798.145", "Exemptions and Exceptions",
            "Certain exemptions apply (e.g., employee data, B2B contacts, public information).",
            "Exemptions", [35]),
    Control("CCPA-1798.185", "Regulations — Security",
            "Businesses must implement reasonable security procedures and practices.",
            "Security Requirements", [1, 4, 5, 19, 35]),
    Control("CCPA-1798.199.40", "Cybersecurity Audits",
            "Businesses whose processing presents significant risk shall perform annual cybersecurity audits.",
            "Security Requirements", [19, 29, 35]),
]

CCPA = ComplianceFramework(
    framework_id="ccpa",
    name="CCPA / CPRA",
    jurisdiction="California, United States",
    version="California Privacy Rights Act (as amended 2023)",
    controls=_CCPA_CONTROLS,
)


# ---------------------------------------------------------------------------
# Framework registry
# ---------------------------------------------------------------------------

FRAMEWORK_REGISTRY: dict[str, ComplianceFramework] = {
    f.framework_id: f
    for f in [SOC2, GDPR, HIPAA, DPDP, ISO27001, CCPA]
}


def get_framework(framework_id: str) -> ComplianceFramework:
    fw = FRAMEWORK_REGISTRY.get(framework_id.lower())
    if not fw:
        valid = ", ".join(sorted(FRAMEWORK_REGISTRY.keys()))
        raise ValueError(f"Unknown framework '{framework_id}'. Valid: {valid}")
    return fw


def list_frameworks() -> list[dict[str, str]]:
    return [
        {
            "framework_id": f.framework_id,
            "name": f.name,
            "jurisdiction": f.jurisdiction,
            "version": f.version,
            "total_controls": str(len(f.controls)),
        }
        for f in FRAMEWORK_REGISTRY.values()
    ]
