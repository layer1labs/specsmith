# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""Structured AI regulation definitions — May 2026.

Each Regulation has Articles (or Controls) with:
  - id, title, description
  - effective_date: when this specific provision took effect
  - specsmith_controls: which specsmith features satisfy the control
  - category: transparency | risk_management | human_oversight | logging |
               data_governance | security | discrimination | disclosure
"""

from __future__ import annotations

from dataclasses import dataclass, field


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


@dataclass
class Article:
    """A single article / control / requirement within a regulation."""

    id: str                              # e.g. "Art.9", "GOVERN-1.1", "Sec.6(a)"
    title: str
    description: str
    effective_date: str                  # ISO-8601 or "2026-02-01"
    category: str                        # transparency | risk_management | etc.
    specsmith_controls: list[str] = field(default_factory=list)
    # specsmith features / CLI commands that satisfy this control
    notes: str = ""


@dataclass
class Regulation:
    """A single AI regulation."""

    id: str                              # e.g. "eu-ai-act"
    name: str
    full_name: str
    jurisdiction: str                    # "EU" | "US-Federal" | "US-Colorado" | etc.
    enacted: str                         # date enacted / published
    effective: str                       # primary effective date
    url: str
    description: str
    articles: list[Article] = field(default_factory=list)
    notes: str = ""

    def article(self, article_id: str) -> Article | None:
        return next((a for a in self.articles if a.id == article_id), None)


# ---------------------------------------------------------------------------
# EU AI Act 2024/1689
# ---------------------------------------------------------------------------

_EU_AI_ACT = Regulation(
    id="eu-ai-act",
    name="EU AI Act",
    full_name="Regulation (EU) 2024/1689 of the European Parliament and of the Council",
    jurisdiction="EU",
    enacted="2024-07-12",
    effective="2025-02-02",  # prohibited AI provisions
    url="https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32024R1689",
    description=(
        "The EU AI Act establishes harmonised rules for the development, "
        "placing on the market, putting into service, and use of AI systems "
        "in the Union. Applies tiered requirements based on risk classification."
    ),
    notes=(
        "Art. 5 (prohibited AI): 2025-02-02. "
        "Arts. 51-56 (GPAI): 2025-08-01. "
        "Arts. 6-15 (high-risk): 2026-08-01. "
        "Full application: 2027-08-01."
    ),
    articles=[
        Article(
            id="Art.5",
            title="Prohibited AI Practices",
            description=(
                "Prohibits AI systems that deploy subliminal manipulation, exploit "
                "vulnerabilities, enable social scoring by public authorities, real-time "
                "biometric identification in public spaces (with limited exceptions), "
                "emotion recognition in workplaces/education, and predictive policing."
            ),
            effective_date="2025-02-02",
            category="risk_management",
            specsmith_controls=[
                "specsmith preflight --escalate-threshold",
                "kill_switch",
                "permission_profiles",
            ],
            notes="specsmith governance tooling is not in scope for Art. 5 prohibition.",
        ),
        Article(
            id="Art.9",
            title="Risk Management System",
            description=(
                "High-risk AI providers must implement a risk management system: "
                "identification and analysis of known and foreseeable risks, estimation "
                "and evaluation of risks, adoption of risk management measures, testing. "
                "Must be an iterative process throughout the lifecycle."
            ),
            effective_date="2026-08-01",
            category="risk_management",
            specsmith_controls=[
                "specsmith epistemic-audit",
                "specsmith stress-test",
                "specsmith preflight",
                "specsmith verify",
                "retry_budget",
                "epistemic_confidence",
            ],
        ),
        Article(
            id="Art.12",
            title="Record-keeping and Logging",
            description=(
                "High-risk AI systems must automatically log events throughout their "
                "operation to the extent reasonably possible. Logging capabilities must "
                "enable monitoring for anomalous behavior, traceability, and post-market "
                "monitoring. Logs must be retained for at least 6 months."
            ),
            effective_date="2026-08-01",
            category="logging",
            specsmith_controls=[
                "specsmith trace (SHA-256 chain)",
                ".specsmith/trace.jsonl",
                "ChronoStore WAL (.chronomemory/events.wal)",
                ".specsmith/ledger.jsonl",
                "specsmith trace verify",
            ],
        ),
        Article(
            id="Art.13",
            title="Transparency and Provision of Information to Deployers",
            description=(
                "High-risk AI systems must be transparent and provide deployers with "
                "instructions for use covering: provider identification, system capabilities "
                "and limitations, human oversight measures, expected accuracy, and conditions "
                "for intended use."
            ),
            effective_date="2026-08-01",
            category="transparency",
            specsmith_controls=[
                "ai_disclosure field in preflight output",
                "specsmith preflight (narration mode)",
                "specsmith agent providers",
                "model_assumptions in ESDB records",
            ],
        ),
        Article(
            id="Art.14",
            title="Human Oversight",
            description=(
                "High-risk AI systems must be designed and developed to be effectively "
                "overseen by humans. Must include human-machine interface tools and enable "
                "humans to understand AI outputs, monitor operations, interrupt and override "
                "the system at any time, and understand capabilities and limitations."
            ),
            effective_date="2026-08-01",
            category="human_oversight",
            specsmith_controls=[
                "specsmith preflight gate",
                "kill_switch (specsmith kill-session)",
                "escalation_threshold",
                "permission_profiles (read_only|standard|extended|admin)",
                "bounded_retry (max_attempts)",
            ],
        ),
        Article(
            id="Art.15",
            title="Accuracy, Robustness, and Cybersecurity",
            description=(
                "High-risk AI systems must achieve appropriate levels of accuracy, "
                "robustness, and cybersecurity. Must be resilient against attempts by "
                "unauthorised parties to alter their use, behavior, or performance. "
                "Must include fallback plans and prevent behavioral anomalies."
            ),
            effective_date="2026-08-01",
            category="security",
            specsmith_controls=[
                "specsmith epistemic-audit (confidence gating)",
                "specsmith stress-test (adversarial challenges)",
                "specsmith trace verify (tamper detection)",
                "H16 anti-drift recursion guard",
                "H15 epistemic scope bounding",
            ],
        ),
        Article(
            id="Art.52",
            title="Transparency Obligations for GPAI Models",
            description=(
                "Providers of GPAI models must ensure their models comply with copyright "
                "law and publish a sufficiently detailed summary of training data. "
                "GPAI models with systemic risk must perform adversarial testing and "
                "notify the Commission of serious incidents."
            ),
            effective_date="2025-08-01",
            category="transparency",
            specsmith_controls=[
                "ai_disclosure (provider + model in every response)",
                "specsmith agent providers (model registry)",
                "specsmith audit --full",
            ],
        ),
        Article(
            id="Art.72",
            title="Post-Market Monitoring",
            description=(
                "Providers of high-risk AI must establish post-market monitoring systems. "
                "Must actively collect and review data on performance throughout the "
                "lifetime of the AI system and report serious incidents."
            ),
            effective_date="2026-08-01",
            category="logging",
            specsmith_controls=[
                "specsmith audit (drift detection)",
                "specsmith watch (continuous monitoring)",
                "specsmith ci watch (CI status monitoring)",
                ".specsmith/ledger.jsonl (continuous record)",
            ],
        ),
    ],
)

# ---------------------------------------------------------------------------
# NIST AI RMF 1.0 + AI 600-1 GenAI Profile
# ---------------------------------------------------------------------------

_NIST_RMF = Regulation(
    id="nist-rmf",
    name="NIST AI RMF",
    full_name=(
        "NIST AI Risk Management Framework 1.0 (AI RMF) + "
        "NIST AI 600-1 Generative AI Profile"
    ),
    jurisdiction="US-Federal",
    enacted="2023-01-26",
    effective="2023-01-26",
    url="https://airc.nist.gov/Home",
    description=(
        "The NIST AI RMF provides a voluntary framework for managing AI risks. "
        "Organized around four core functions: GOVERN, MAP, MEASURE, MANAGE. "
        "AI 600-1 (Jul 2024) extends it with GenAI-specific profiles."
    ),
    articles=[
        Article(
            id="GOVERN-1",
            title="Governance Policies and Processes",
            description=(
                "Organizational policies, processes, procedures, and practices across "
                "the AI lifecycle are in place, transparent, and implemented effectively. "
                "AI risk and benefit management is integrated into operations."
            ),
            effective_date="2023-01-26",
            category="risk_management",
            specsmith_controls=[
                "AGENTS.md (governance hub)",
                "docs/governance/RULES.md or .specsmith/governance/rules.yaml",
                "specsmith audit",
                "specsmith validate --strict",
                "specsmith phase",
            ],
        ),
        Article(
            id="GOVERN-2",
            title="AI Risk Accountability",
            description=(
                "Accountability for AI risk, including third-party systems, is clearly "
                "established and documented. Roles and responsibilities for AI risk "
                "identification, assessment, and management are defined."
            ),
            effective_date="2023-01-26",
            category="risk_management",
            specsmith_controls=[
                "docs/governance/ROLES.md or .specsmith/governance/roles.yaml",
                "permission_profiles",
                "specsmith agent permissions",
            ],
        ),
        Article(
            id="MAP-1",
            title="AI Risk Context Identification",
            description=(
                "AI system context, capabilities, and limitations are understood, "
                "documented, and communicated. The intended and unintended uses and "
                "misuses are identified and evaluated."
            ),
            effective_date="2023-01-26",
            category="risk_management",
            specsmith_controls=[
                "specsmith epistemic-audit",
                "specsmith stress-test",
                "specsmith belief-graph",
                "specsmith preflight (intent classification)",
            ],
        ),
        Article(
            id="MAP-2",
            title="Categorization of Impact",
            description=(
                "Scientific findings, historical experience, expert wisdom, and community "
                "feedback inform AI risk identification and prioritization. Potential "
                "harms and benefits are evaluated."
            ),
            effective_date="2023-01-26",
            category="risk_management",
            specsmith_controls=[
                "specsmith trace seal (decision sealing)",
                "ESDB confidence scores",
                "specsmith preflight --escalate-threshold",
            ],
        ),
        Article(
            id="MEASURE-1",
            title="Risk Analysis Methods",
            description=(
                "Methods and metrics for AI risk analysis are identified and applied. "
                "AI system performance is evaluated against defined metrics and "
                "benchmarks. Testing and evaluation documentation is maintained."
            ),
            effective_date="2023-01-26",
            category="risk_management",
            specsmith_controls=[
                "specsmith verify (confidence scoring)",
                "specsmith epistemic-audit (certainty threshold)",
                "specsmith eval",
                "specsmith stress-test",
                "H17 calibration direction",
            ],
        ),
        Article(
            id="MEASURE-2",
            title="Bias and Fairness Testing",
            description=(
                "AI systems are tested for bias and unfair differential impact across "
                "demographic groups before deployment and on an ongoing basis."
            ),
            effective_date="2023-01-26",
            category="discrimination",
            specsmith_controls=[
                "H19 synthetic contamination prevention",
                "specsmith validate --strict (data quality checks)",
            ],
        ),
        Article(
            id="MANAGE-1",
            title="Risk Response and Treatment",
            description=(
                "Identified and prioritized AI risks are managed and mitigated. "
                "Residual risks are documented. AI systems with unacceptable risk "
                "are not deployed."
            ),
            effective_date="2023-01-26",
            category="risk_management",
            specsmith_controls=[
                "specsmith verify (equilibrium gate)",
                "kill_switch",
                "bounded_retry",
                "specsmith audit --fix",
                "permission_profiles",
            ],
        ),
        Article(
            id="MANAGE-2",
            title="Monitoring and Review",
            description=(
                "Risk management plans are implemented and monitored. AI systems are "
                "monitored for performance, bias, and alignment with intended use. "
                "Feedback mechanisms are in place."
            ),
            effective_date="2023-01-26",
            category="logging",
            specsmith_controls=[
                "specsmith watch",
                "specsmith audit",
                "specsmith drift-metrics",
                ".specsmith/ledger.jsonl",
                "ChronoStore WAL",
            ],
        ),
        # GenAI-specific (AI 600-1, Jul 2024)
        Article(
            id="GV-1.1",
            title="GenAI: Organizational AI Governance",
            description=(
                "Policies address the use and risks specific to generative AI, including "
                "hallucination, data leakage, copyright, and adversarial prompting."
            ),
            effective_date="2024-07-26",
            category="transparency",
            specsmith_controls=[
                "H15 epistemic scope bounding",
                "H16 anti-drift recursion guard",
                "H17 calibration direction",
                "H18 RAG retrieval filtering",
                "H19 synthetic contamination prevention",
                "H20 falsifiability required",
            ],
        ),
        Article(
            id="GV-6.1",
            title="GenAI: Third-party AI Risk",
            description=(
                "Policies and procedures for acquiring and using third-party AI "
                "models and datasets include evaluation of provenance, fitness for "
                "purpose, and ongoing monitoring."
            ),
            effective_date="2024-07-26",
            category="risk_management",
            specsmith_controls=[
                "specsmith agent providers (BYOE registry)",
                "H21 no undisclosed model assumptions",
                "specsmith model-intel scores",
            ],
        ),
    ],
)

# ---------------------------------------------------------------------------
# OMB M-24-10
# ---------------------------------------------------------------------------

_OMB_M2410 = Regulation(
    id="omb-m-24-10",
    name="OMB M-24-10",
    full_name=(
        "OMB Memorandum M-24-10: Advancing Governance, Innovation and Risk Management "
        "for Agency Use of Artificial Intelligence"
    ),
    jurisdiction="US-Federal",
    enacted="2024-03-28",
    effective="2024-03-28",
    url="https://www.whitehouse.gov/wp-content/uploads/2024/03/M-24-10-Advancing-Governance-Innovation-Risk-Management.pdf",
    description=(
        "Requires federal agencies to: designate a Chief AI Officer, "
        "conduct annual AI use-case inventories, publish AI impact assessments "
        "for rights-impacting or safety-impacting use cases, and implement "
        "minimum AI governance practices."
    ),
    articles=[
        Article(
            id="Sec.3",
            title="AI Use-Case Inventory",
            description=(
                "Federal agencies must publish and maintain an annual inventory of "
                "AI use cases, including rights-impacting and safety-impacting uses. "
                "Must include risk classification and human oversight measures."
            ),
            effective_date="2024-03-28",
            category="transparency",
            specsmith_controls=[
                "specsmith export (AI System Inventory section)",
                "specsmith compliance report",
            ],
        ),
        Article(
            id="Sec.5(b)",
            title="Minimum AI Governance Practices",
            description=(
                "Agencies must implement minimum AI governance practices: transparency "
                "about AI use, testing before deployment, ongoing monitoring, human "
                "review of AI-generated content in high-stakes decisions."
            ),
            effective_date="2024-12-01",
            category="human_oversight",
            specsmith_controls=[
                "specsmith preflight gate",
                "specsmith verify",
                "specsmith audit",
                "permission_profiles",
            ],
        ),
    ],
)

# ---------------------------------------------------------------------------
# Colorado SB24-205 — AI Act
# ---------------------------------------------------------------------------

_COLORADO_SB24205 = Regulation(
    id="colorado-sb24-205",
    name="Colorado AI Act",
    full_name="Colorado SB24-205: Concerning Artificial Intelligence",
    jurisdiction="US-Colorado",
    enacted="2024-05-17",
    effective="2026-02-01",
    url="https://leg.colorado.gov/bills/sb24-205",
    description=(
        "Colorado's AI Act applies to developers and deployers of 'high-risk' AI systems "
        "used to make 'consequential decisions' affecting Colorado residents. Requires risk "
        "assessments, anti-discrimination measures, and consumer notification. "
        "'Consequential decisions' include employment, education, housing, credit, "
        "healthcare, insurance, and legal matters."
    ),
    notes=(
        "specsmith is a development governance tool. When used to govern AI systems "
        "making consequential decisions affecting Colorado residents, the developer "
        "must comply. specsmith provides the audit trail and human oversight "
        "infrastructure that enables compliance."
    ),
    articles=[
        Article(
            id="Sec.6(1)(a)",
            title="Developer Risk Assessment",
            description=(
                "Developers of high-risk AI systems must use reasonable care to protect "
                "Colorado consumers from known or reasonably foreseeable risks of "
                "algorithmic discrimination. Must document intended uses, known limitations, "
                "and testing results."
            ),
            effective_date="2026-02-01",
            category="risk_management",
            specsmith_controls=[
                "specsmith stress-test",
                "specsmith epistemic-audit",
                "ESDB confidence scoring",
                "specsmith verify",
            ],
        ),
        Article(
            id="Sec.6(1)(b)",
            title="Impact Assessment",
            description=(
                "Developers must conduct and document impact assessments for high-risk "
                "AI systems, including: known risks of algorithmic discrimination, "
                "data used to train the system, known limitations, and safeguards."
            ),
            effective_date="2026-02-01",
            category="discrimination",
            specsmith_controls=[
                "specsmith compliance report",
                "specsmith epistemic-audit",
                "specsmith export",
            ],
        ),
        Article(
            id="Sec.6(2)(a)",
            title="Deployer Disclosure to Consumers",
            description=(
                "Deployers of high-risk AI systems making consequential decisions must "
                "notify Colorado consumers that AI is being used, provide a plain-language "
                "explanation of the decision, and provide a process to correct inaccurate "
                "information used in the decision."
            ),
            effective_date="2026-02-01",
            category="transparency",
            specsmith_controls=[
                "ai_disclosure field in governance outputs",
                "specsmith preflight (narration mode)",
            ],
        ),
        Article(
            id="Sec.6(2)(b)",
            title="Deployer Anti-Discrimination Policy",
            description=(
                "Deployers must implement a policy for managing risk of algorithmic "
                "discrimination, regularly monitor for discrimination, and provide "
                "an appeal mechanism for adverse decisions."
            ),
            effective_date="2026-02-01",
            category="discrimination",
            specsmith_controls=[
                "H19 synthetic contamination prevention",
                "specsmith validate --strict",
                "specsmith audit",
            ],
        ),
    ],
)

# ---------------------------------------------------------------------------
# Texas HB 1709 — AI Transparency Act
# ---------------------------------------------------------------------------

_TEXAS_HB1709 = Regulation(
    id="texas-hb1709",
    name="Texas AI Transparency Act",
    full_name="Texas HB 1709: Relating to the use of artificial intelligence systems",
    jurisdiction="US-Texas",
    enacted="2025-06-15",
    effective="2025-09-01",
    url="https://capitol.texas.gov/BillLookup/History.aspx?LegSess=89R&Bill=HB1709",
    description=(
        "Texas state agencies using high-risk AI systems must publicly disclose use cases, "
        "conduct risk assessments annually, notify Texas residents when AI is used in "
        "significant decisions, and report to the Texas Department of Emergency Management."
    ),
    articles=[
        Article(
            id="Sec.2252.002",
            title="Public Disclosure of AI Use",
            description=(
                "State agencies must publish on their website a list of high-risk AI "
                "systems in use, their purpose, and the types of decisions they support. "
                "Must be updated annually."
            ),
            effective_date="2025-09-01",
            category="transparency",
            specsmith_controls=[
                "specsmith export (AI System Inventory)",
                "specsmith compliance report",
            ],
        ),
        Article(
            id="Sec.2252.003",
            title="Annual Risk Assessment",
            description=(
                "State agencies must conduct annual risk assessments of high-risk AI systems. "
                "Must document: intended uses, known risks, human oversight measures, "
                "and steps taken to minimize harm."
            ),
            effective_date="2025-09-01",
            category="risk_management",
            specsmith_controls=[
                "specsmith audit",
                "specsmith epistemic-audit",
                "specsmith compliance audit",
            ],
        ),
    ],
)

# ---------------------------------------------------------------------------
# Illinois AI Employment Transparency Act
# ---------------------------------------------------------------------------

_ILLINOIS_AIETA = Regulation(
    id="illinois-aieta",
    name="Illinois AI Employment Transparency Act",
    full_name=(
        "Illinois Artificial Intelligence Video Interview Act + "
        "AI Employment Transparency Amendments (2023)"
    ),
    jurisdiction="US-Illinois",
    enacted="2023-01-01",
    effective="2023-01-01",
    url="https://www.ilga.gov/legislation/ilcs/ilcs3.asp?ActID=4015",
    description=(
        "Employers in Illinois using AI in employment decisions must: disclose AI use to "
        "applicants and employees, explain how AI characteristics are used, and collect "
        "and report race/ethnicity data on applicants screened by AI."
    ),
    articles=[
        Article(
            id="Sec.10",
            title="Disclosure of AI Use in Employment",
            description=(
                "Employers must notify applicants before using AI tools. Must explain "
                "what characteristics the AI uses and how the AI is used to screen "
                "applicants. Must collect and report annual demographic data."
            ),
            effective_date="2023-01-01",
            category="transparency",
            specsmith_controls=[
                "ai_disclosure field",
                "specsmith agent permissions (tool disclosure)",
            ],
            notes="Applies when specsmith-governed AI makes or assists employment decisions.",
        ),
    ],
)

# ---------------------------------------------------------------------------
# California ADMT (AB 2930 / CPPA)
# ---------------------------------------------------------------------------

_CALIFORNIA_ADMT = Regulation(
    id="california-admt",
    name="California ADMT Regulations",
    full_name=(
        "California AB 2930 / CPPA Automated Decision-Making Technology Regulations"
    ),
    jurisdiction="US-California",
    enacted="2024-09-01",
    effective="2026-01-01",
    url="https://cppa.ca.gov/regulations/",
    description=(
        "California's ADMT regulations (finalized 2026) require businesses using "
        "automated decision-making technology to: provide pre-use notices, offer opt-out "
        "rights for significant decisions, conduct annual risk assessments for high-risk uses, "
        "and allow consumers to request human review."
    ),
    articles=[
        Article(
            id="Sec.7030(a)",
            title="Pre-Use Notice",
            description=(
                "Businesses must provide clear notice to consumers before using ADMT "
                "for significant decisions (employment, housing, credit, healthcare, etc). "
                "Notice must include: purpose, logic description, and opt-out mechanism."
            ),
            effective_date="2026-01-01",
            category="transparency",
            specsmith_controls=[
                "ai_disclosure field in governance outputs",
                "specsmith preflight (transparent intent classification)",
            ],
        ),
        Article(
            id="Sec.7030(b)",
            title="Risk Assessment for High-Risk ADMT",
            description=(
                "Businesses using high-risk ADMT must conduct documented risk assessments "
                "annually covering: intended purpose, potential harms to consumers, "
                "data used, safeguards implemented, and evaluation of differential impact."
            ),
            effective_date="2026-01-01",
            category="risk_management",
            specsmith_controls=[
                "specsmith compliance audit",
                "specsmith epistemic-audit",
                "specsmith stress-test",
            ],
        ),
    ],
)

# ---------------------------------------------------------------------------
# NYC Local Law 144
# ---------------------------------------------------------------------------

_NYC_LL144 = Regulation(
    id="nyc-ll144",
    name="NYC Local Law 144",
    full_name="New York City Local Law 144 of 2021: Automated Employment Decision Tools",
    jurisdiction="US-NYC",
    enacted="2021-12-11",
    effective="2023-07-05",
    url="https://legistar.council.nyc.gov/LegislationDetail.aspx?ID=4344524",
    description=(
        "NYC employers and employment agencies using Automated Employment Decision Tools "
        "(AEDTs) must: conduct annual independent bias audits, publish summaries of audit "
        "results, notify candidates of AEDT use 10+ business days in advance."
    ),
    articles=[
        Article(
            id="Sec.20-871",
            title="Annual Bias Audit Requirement",
            description=(
                "Employers must commission an independent annual bias audit of any AEDT "
                "used for employment decisions. Must publish a summary including: date "
                "of audit, distribution of job candidates by race/sex/intersectional categories, "
                "score rates for each category."
            ),
            effective_date="2023-07-05",
            category="discrimination",
            specsmith_controls=[
                "H19 synthetic contamination prevention",
                "ESDB confidence + source_type tracking",
                "specsmith validate --strict",
            ],
            notes="Requires independent third-party audit; specsmith provides the audit trail.",
        ),
        Article(
            id="Sec.20-872",
            title="Notice to Candidates",
            description=(
                "Employers must provide notice to candidates and employees at least 10 "
                "business days before using an AEDT. Notice must state AEDT is used and "
                "what job qualifications are being assessed."
            ),
            effective_date="2023-07-05",
            category="transparency",
            specsmith_controls=[
                "ai_disclosure field",
            ],
        ),
    ],
)

# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

REGULATIONS: dict[str, Regulation] = {
    reg.id: reg
    for reg in [
        _EU_AI_ACT,
        _NIST_RMF,
        _OMB_M2410,
        _COLORADO_SB24205,
        _TEXAS_HB1709,
        _ILLINOIS_AIETA,
        _CALIFORNIA_ADMT,
        _NYC_LL144,
    ]
}

# Convenience aliases
EU_AI_ACT = _EU_AI_ACT
NIST_RMF = _NIST_RMF
OMB_M2410 = _OMB_M2410
COLORADO = _COLORADO_SB24205
TEXAS = _TEXAS_HB1709
ILLINOIS = _ILLINOIS_AIETA
CALIFORNIA = _CALIFORNIA_ADMT
NYC = _NYC_LL144
