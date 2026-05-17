# SPDX-License-Identifier: MIT
"""Corporate function skills — budget, PM, HR, fundraising, marketing, sales, legal."""

from specsmith.skills import SkillDomain, SkillEntry

SKILLS: list[SkillEntry] = [
    SkillEntry(
        slug="budget-tracking",
        name="Budget Tracking — P&L, cash flow, Excel models, variance analysis",
        description=(
            "Financial management: P&L structure, cash flow forecasting, "
            "budget variance analysis, Excel financial models, and reporting."
        ),
        domain=SkillDomain.CORPORATE,
        tags=[
            "budget",
            "finance",
            "pl",
            "cash-flow",
            "excel",
            "forecast",
            "variance",
            "accounting",
            "reporting",
            "kpi",
        ],
        prerequisites=[],
        body="""\
# Budget Tracking Skill

## P&L structure
```
Revenue
  - Gross Revenue
  - Discounts / Refunds
  = Net Revenue

Cost of Goods Sold (COGS)
  - Direct materials / hosting / cloud costs
  = Gross Profit   (Gross Margin = Gross Profit / Net Revenue)

Operating Expenses (OpEx)
  - R&D (salaries, contractors, tools)
  - Sales & Marketing
  - G&A (finance, HR, legal, rent)
  = EBITDA

D&A (Depreciation & Amortisation)
  = EBIT (Operating Income)

Interest + Tax
  = Net Income
```

## Monthly budget template (Excel)
```
Columns: Category | Budget ($) | Actual ($) | Variance ($) | Variance (%)
Rows: Every expense category + revenue line

Key formula:
=Actual - Budget                   # absolute variance
=(Actual - Budget) / ABS(Budget)   # % variance
=IF(ABS(E2/D2)>0.1, "⚠️ >10%", "✓")  # flag large variances
```

## Cash flow forecast (13-week rolling)
```
Weekly template:
  Opening cash
+ Collections (AR received)
- Payroll
- Vendor payments
- Software/cloud
- Rent/utilities
= Closing cash   → feed into next week's opening

Key metric: minimum cash runway = Min(weekly closing cash)
Alert: if runway < 8 weeks, escalate immediately.
```

## Variance analysis report (monthly)
```
Format: "We spent $X vs budget of $Y (+/- Z%).
Reason: [specific cause — not 'market conditions'].
Offset: [what we'll do differently next month]."

Favourable variances also need explanation — may indicate under-investment.
```

## Budget KPIs to track monthly
- **Burn rate**: monthly cash outflow
- **Runway**: cash / monthly burn
- **CAC**: Customer Acquisition Cost = S&M spend / new customers
- **LTV**: Lifetime Value = ARPU × average retention months × gross margin
- **Payback period**: CAC / (MRR × gross margin)
- **Rule of 40**: ARR growth % + EBITDA margin % ≥ 40 (SaaS benchmark)

## Common pitfalls
- Mixing cash basis and accrual: pick one (accrual for management reporting).
- Ignoring working capital: profitable companies can still run out of cash.
- Single scenario model: always have base / upside / downside cases.
- Revenue recognition: SaaS = recognise monthly, not when annual contract signed.
""",
    ),
    SkillEntry(
        slug="project-management",
        name="Project Management — scope, milestones, RACI, risk, retrospectives",
        description=(
            "Project management fundamentals: scope definition, milestone planning, "
            "RACI matrix, risk register, stakeholder communication, and retrospectives."
        ),
        domain=SkillDomain.CORPORATE,
        tags=[
            "project-management",
            "pm",
            "agile",
            "scrum",
            "kanban",
            "milestones",
            "raci",
            "risk",
            "stakeholder",
            "retrospective",
        ],
        prerequisites=[],
        body="""\
# Project Management Skill

## Project charter (one page)
```markdown
## [Project Name] Charter

**Objective**: [1 sentence — what success looks like]
**In scope**: [list of deliverables]
**Out of scope**: [explicitly list what we're NOT doing]
**Timeline**: [Start date] → [End date]
**Budget**: $[amount]
**Sponsor**: [Name]
**PM**: [Name]
**Key stakeholders**: [Name/Role]
**Success criteria**: [measurable outcomes — not activities]
**Risks**: [top 3 with mitigation]
```

## Milestone planning
```
Phase 1: Discovery (weeks 1-2)
  M1: Requirements signed off [DATE]
Phase 2: Design (weeks 3-5)
  M2: Architecture approved [DATE]
Phase 3: Build (weeks 6-12)
  M3: Beta ready for testing [DATE]
Phase 4: Launch (weeks 13-14)
  M4: Production launch [DATE]
  M5: Post-launch review [DATE + 2 weeks]

Rule: milestones have dates, not "when it's ready".
```

## RACI matrix
```
R = Responsible (does the work)
A = Accountable (one person — signs off)
C = Consulted (gives input before decision)
I = Informed (notified after decision)

Example:
Task            | PM | Dev Lead | Designer | CEO
Architecture    | C  | R/A      | C        | I
Budget approval | R  | I        | I        | A
Launch decision | C  | C        | C        | R/A
```

## Risk register
```markdown
| ID | Risk | Probability | Impact | Score | Mitigation | Owner | Status |
|----|------|-------------|--------|-------|------------|-------|--------|
| R1 | Key engineer leaves | M | H | 6 | Document all systems; cross-train | PM | Open |
| R2 | API partner goes down | L | H | 4 | Build fallback; SLA agreement | CTO | Mitigated |

Score = Probability (1-3) × Impact (1-3)
Review weekly; close resolved risks.
```

## Agile sprint template (2-week)
```
Monday week 1: Sprint planning
  → Goal: [one sentence]
  → Stories committed: [list with points]

Daily standup (15 min):
  1. What did I do yesterday?
  2. What will I do today?
  3. Any blockers?

Friday week 2: Sprint review + retrospective
  Review: demo completed stories to stakeholders
  Retro: What went well? What didn't? Action items?
```

## Status report template (weekly)
```
🟢 On track  🟡 At risk  🔴 Off track

**Status**: 🟢 On track for [DATE] launch

**This week**:
- Completed: [list]
- In progress: [list with % done]

**Next week**: [list]

**Blockers**: [none / specific ask]

**Budget**: $[spent] of $[total] ([%])
```

## Stakeholder communication plan
```
Cadence | Audience | Format | Owner
Daily standup | Dev team | Slack/call | PM
Weekly status | Project team | Email + doc | PM
Bi-weekly exec update | Leadership | 1-page doc | PM + Sponsor
Monthly board update | Board | Deck | CEO
```

## Common pitfalls
- Scope creep: all change requests go through formal change control — never "just add it."
- Missing RACI: two people think they're Accountable → conflict.
- No retrospectives: same problems repeat sprint after sprint.
- Status report optimism: red status early is better than surprise failure later.
""",
    ),
    SkillEntry(
        slug="hr-onboarding",
        name="HR & Onboarding — job descriptions, interviews, onboarding, performance",
        description=(
            "HR fundamentals: writing JDs, structured interviewing, "
            "30/60/90-day onboarding plans, and performance review templates."
        ),
        domain=SkillDomain.CORPORATE,
        tags=[
            "hr",
            "hiring",
            "onboarding",
            "performance",
            "interviews",
            "job-description",
            "culture",
            "feedback",
            "pip",
            "okr",
        ],
        prerequisites=[],
        body="""\
# HR & Onboarding Skill

## Job description template
```markdown
## [Role Title]

**About us**: [2-3 sentences — mission, stage, team size]

**The role**: [What this person will own — not a task list]

**You will**:
- Own [major responsibility] — specific outcome expected
- Build [what] with [who]
- Lead [initiative] to [business goal]

**You bring**:
- [Must-have 1]: evidence of X (e.g., "shipped production systems handling 1M+ users")
- [Must-have 2]
- [Nice-to-have]: not required but valuable

**Compensation**: $[X]-$[Y] base + equity [%] + benefits

**Process**: [interview stages + timeline]
```

## Structured interview scorecard
```
Competency: Problem-solving (weight: 30%)
Question: "Tell me about the hardest technical problem you've solved."
4 - Exceptional: identified root cause others missed; invented novel solution
3 - Strong: methodical approach; clear reasoning; good outcome
2 - Adequate: solved the problem but reactively; learning needed
1 - Weak: unclear thinking; avoided or passed to others

Total score: Weighted average across 5-6 competencies.
Hire threshold: ≥ 3.0 average; no 1s on must-have competencies.
```

## Interview process (for IC engineering roles)
```
1. 30-min recruiter screen — culture fit, salary, timeline
2. 60-min technical phone screen — coding or system design
3. 4-hour virtual onsite:
   a. 60-min coding challenge
   b. 60-min system design
   c. 30-min behavioural (STAR method)
   d. 30-min "meet the team" (informal)
4. Debrief: all interviewers score independently before meeting
5. Offer: within 24-48h of decision
```

## 30-60-90 day onboarding plan
```markdown
### Month 1 (Listen & Learn)
- Week 1: Setup, introductions, read all documentation
- Week 2-3: Shadow team members; attend all standups/meetings
- Week 4: Complete first small task independently
Goal: understand the product, team, and codebase/domain

### Month 2 (Contribute)
- Own first meaningful project with light supervision
- Identify 3 things that could be improved
- Get 360° feedback from team
Goal: deliver independently; integrate into team culture

### Month 3 (Lead)
- Drive a cross-functional initiative
- Mentor a newer team member
- Set H2 OKRs with manager
Goal: operate as a full-speed team member
```

## Performance review template (semi-annual)
```markdown
## [Employee Name] — [Period]

### Achievements (what was delivered vs objectives)
- [Achievement + quantified impact]

### Strengths (what to do more of)
- [Specific behaviour + example]

### Development areas (not "weaknesses")
- [Growth area + specific suggestion]

### Rating: Exceeds / Meets / Developing / Below expectations

### Next period goals
- [Objective] — success metric: [measurable outcome] by [date]
```

## Common pitfalls
- Hiring for "culture fit": define culture as specific behaviours, not demographics.
- No structured scoring: recency bias + halo effect → bad hires.
- Skipping onboarding plan: even senior hires need structured ramp-up.
- Annual reviews only: give feedback weekly; annual review should have no surprises.
""",
    ),
    SkillEntry(
        slug="fundraising-vc",
        name="Fundraising — VC/Angel pitch, deck, due diligence, term sheet",
        description=(
            "Startup fundraising: investor pitch deck structure, VC/Angel targeting, "
            "due diligence preparation, term sheet key terms, and post-close."
        ),
        domain=SkillDomain.CORPORATE,
        tags=[
            "fundraising",
            "vc",
            "venture-capital",
            "angel",
            "pitch",
            "deck",
            "term-sheet",
            "due-diligence",
            "startup",
            "investment",
        ],
        prerequisites=[],
        body="""\
# Fundraising (VC/Angel) Skill

## Investor pitch deck structure (12-15 slides)
```
1. Cover: Company name, tagline, date, founder name
2. Problem: Specific customer pain + data showing scale
3. Solution: What you do + demo screenshot/GIF
4. Market: TAM / SAM / SOM — bottoms-up preferred
5. Business model: How you make money + unit economics
6. Traction: Key metrics (MRR, growth rate, customers, NPS)
7. Go-to-market: How you acquire customers + CAC
8. Competition: 2×2 matrix — honest about where you win
9. Team: Relevant experience + why you'll win
10. Financials: 3-year projection (revenue, burn, headcount)
11. The ask: How much, use of funds, expected runway
12. Appendix: Detailed financials, product roadmap, customer quotes
```

## Target investor research
```
Criteria for targeting investors:
1. Stage match: pre-seed / seed / Series A — check portfolio
2. Sector match: check thesis on website + recent investments
3. Geography: some funds require local or US-incorporated companies
4. Check size: typical check = 5-10% of fund, 2-10% of round
5. Lead vs follow: identify lead investor first (sets terms)

Research tools:
- Crunchbase Pro: portfolio, round history
- Signal.nfx.com: VC intelligence
- LinkedIn: mutual connections for warm intros
- Twitter/X: VCs share thesis + post on interesting problems
```

## Due diligence checklist
```
Corporate:
□ Certificate of incorporation + bylaws
□ Cap table (fully-diluted, including options pool)
□ All existing investor agreements (SAFEs, convertible notes)
□ Board minutes (last 3 years)

Commercial:
□ Signed customer contracts (top 10 by ARR)
□ Revenue breakdown + cohort retention data
□ Pipeline forecast + methodology

Technical:
□ Architecture overview
□ Key technical risks + mitigations
□ Security audit results (if any)
□ IP ownership: all contractors signed IP assignment agreements?

People:
□ Org chart + key person dependencies
□ Employment agreements (non-compete, IP assignment)
□ Option pool size + vesting schedules
□ Compensation benchmarks
```

## Term sheet key terms
```
Pre-money valuation: company value before new investment
Post-money = pre-money + new investment

Liquidation preference: 1× non-participating = investor gets back
their investment first, then participates pro-rata. (Founder-friendly.)
2× or participating = investor gets 2× back AND participates.

Anti-dilution: Broad-based weighted average (fair) vs.
Full ratchet (very investor-friendly — avoid).

Board seats: typical at Series A = 2 investors, 2 founders, 1 independent.
Pro-rata rights: right to invest in future rounds to maintain %.
Information rights: monthly financials + board observer seat.
```

## SAFE (Simple Agreement for Future Equity)
```
Y Combinator Standard SAFE (post-money, 2018+):
- Valuation cap: $5M-$15M for pre-seed
- Discount: 15-20% to next round price
- No interest, no maturity date
- Converts at next priced round

Best practice: use YC standard SAFE templates — investors know them.
Side letter is OK for pro-rata rights; never for preferential treatment.
```

## Post-close
```
1. Wire received → update cap table in Carta/LTSE
2. Update Delaware registered agent if first institutional round
3. Issue stock certificates / update SAFE register
4. Set up data room for ongoing updates
5. Schedule quarterly investor updates (email + deck)
6. Board calendar: set recurring dates for 12 months
```

## Common pitfalls
- Fundraising takes 3-6 months: start 6 months before you need the money.
- Warm intro >> cold email: 10× conversion rate; ask portfolio founders for intros.
- Never take first meeting as "feedback only": always pitch — you can get a no but also a yes.
- Cap table errors: use Carta from day 1; don't track in a spreadsheet.
""",
    ),
    SkillEntry(
        slug="marketing-gtm",
        name="Marketing GTM — positioning, ICP, content, demand gen, analytics",
        description=(
            "Go-to-market marketing: ICP definition, positioning, content strategy, "
            "demand generation, SEO basics, paid acquisition, and analytics."
        ),
        domain=SkillDomain.CORPORATE,
        tags=[
            "marketing",
            "gtm",
            "icp",
            "positioning",
            "content",
            "seo",
            "demand-gen",
            "analytics",
            "brand",
            "funnel",
        ],
        prerequisites=[],
        body="""\
# Marketing Go-To-Market Skill

## Positioning framework
```
FOR [target customer]
WHO [has this problem/need]
[Product name] IS A [product category]
THAT [key benefit — what makes it different]
UNLIKE [alternative]
WE [differentiated capability]

Example:
FOR devops teams at mid-market SaaS companies
WHO struggle to maintain governance at scale
specsmith IS A project governance CLI
THAT enforces compliance programmatically without process overhead
UNLIKE Jira or Monday.com
WE make governance a developer tool, not a management process
```

## ICP (Ideal Customer Profile)
```markdown
## ICP Definition

**Firmographics**:
- Company size: 10-200 employees
- Stage: Series A-C
- Industry: SaaS, developer tools, fintech
- Geography: US, UK, EU

**Role/Contact**:
- Title: CTO, VP Engineering, Lead Developer
- Reports to: CEO or CTO
- Budget authority: Yes (< $50K)/No (needs approval)

**Behavioural signals**:
- Uses GitHub + CI/CD
- Has active compliance requirements (SOC 2, HIPAA)
- Already paying for dev tools (>$5K/mo tools budget)

**Pain signals**:
- Recently hired compliance/security person
- Failed audit or security incident
- Fast-growing team (>50% headcount growth)
```

## Content strategy pillars
```
Pillar 1: [Core problem] — e.g., "Engineering governance at scale"
  → Blog: "How to enforce code review standards across 50 engineers"
  → Video: "Governance vs process: why most teams get it wrong"
  → Tool: "Free governance health checker"

Pillar 2: [Use case] — e.g., "SOC 2 compliance automation"
  → Case study: "How Acme reduced audit prep from 3 months to 3 weeks"
  → Comparison: "specsmith vs Jira for compliance tracking"
  → Guide: "SOC 2 for startups: 90-day checklist"

Distribution: publish → repurpose → amplify
Blog post → LinkedIn thread → Twitter summary → Podcast guest → Newsletter
```

## Demand generation channels (by stage)
```
Pre-product-market-fit (< $1M ARR):
  Focus: founder-led sales + community
  - Founder posts on LinkedIn/Twitter (personal brand)
  - Cold email to ICP (target: 20% open, 5% reply)
  - Community (HN, Reddit, Discord groups)

PMF → Scale ($1M-$10M ARR):
  Add: content + SEO + partnerships
  - SEO: target high-intent keywords ("best [tool] for [use case]")
  - G2/Capterra: get reviews from happy customers
  - Partner integrations: appear in ecosystem marketplaces

Scale ($10M+ ARR):
  Add: paid acquisition + events
  - Google Ads: capture high-intent search
  - LinkedIn Ads: ABM for enterprise ICP
  - Conferences: sponsor + speak at 2-3 key events
```

## Marketing analytics (weekly dashboard)
```
Acquisition:
  - Website visitors (MoM growth %)
  - MQL volume (Marketing Qualified Leads)
  - Channel breakdown: organic/paid/referral/direct

Conversion:
  - MQL → SQL rate (target: 20-30%)
  - Demo → trial rate
  - Trial → paid rate (target: 20-30%)

Revenue:
  - New MRR from marketing-sourced deals
  - CAC (blended + by channel)
  - Pipeline coverage ratio (5:1 = healthy)
```

## SEO quick wins
```bash
# 1. Check indexing: site:yourdomain.com in Google
# 2. Keyword research: Ahrefs / Semrush / Google Search Console
# 3. On-page: title tag, H1, meta description, internal links
# 4. Technical: sitemap.xml, robots.txt, page speed (Core Web Vitals)
# 5. Backlinks: get listed on integrations pages, guest posts, communities

# Google Search Console (free)
# → Performance: see which queries drive clicks
# → Coverage: find pages Google can't index
```

## Common pitfalls
- Marketing before ICP is defined: spray-and-pray wastes budget.
- Vanity metrics: website traffic without conversion = expensive distraction.
- Content without distribution: "publish and pray" doesn't work.
- No attribution model: agree on first-touch, last-touch, or multi-touch before spend.
""",
    ),
    SkillEntry(
        slug="sales-crm",
        name="Sales CRM — pipeline, outreach, discovery, closing, Salesforce/HubSpot",
        description=(
            "Sales process management: CRM setup, outbound cadences, "
            "discovery call frameworks, objection handling, and closing."
        ),
        domain=SkillDomain.CORPORATE,
        tags=[
            "sales",
            "crm",
            "salesforce",
            "hubspot",
            "pipeline",
            "outbound",
            "discovery",
            "objections",
            "closing",
            "b2b",
        ],
        prerequisites=[],
        body="""\
# Sales CRM Skill

## CRM pipeline stages (SaaS B2B)
```
1. Lead (unqualified — from marketing / outbound)
2. Qualified (BANT confirmed: Budget, Authority, Need, Timeline)
3. Discovery (meeting booked/held — understand pain)
4. Demo / Evaluation (product demonstrated; trial started)
5. Proposal (pricing/contract sent)
6. Negotiation (legal/procurement review)
7. Closed Won | Closed Lost

Each stage: define entry criteria + exit criteria + average days
Review pipeline weekly: flag deals stuck > 2× average stage duration
```

## Outbound email cadence (10-day)
```
Day 1: Email 1 — personalised cold outreach
  Subject: "Quick q re: [specific pain based on research]"
  Body: 3-4 sentences — problem you solve + proof + CTA (15-min call?)

Day 3: Email 2 — add value
  Send relevant article, benchmark, or case study

Day 5: LinkedIn connection request (no message yet)

Day 7: Email 3 — different angle
  Challenge their current approach with a question

Day 9: LinkedIn message — short, reference email thread

Day 10: Final email — graceful breakup
  "Happy to close the loop. Here's the deck if helpful [link]."

Metrics: 15-20% open rate, 3-5% reply rate is good for cold outbound.
```

## Discovery call framework (MEDDIC)
```
M — Metrics: What does success look like quantitatively?
  "How do you measure the problem today? What's the cost?"

E — Economic Buyer: Who approves the budget?
  "Who else needs to be involved in this decision?"

D — Decision Criteria: How will you evaluate options?
  "What would a perfect solution look like for your team?"

D — Decision Process: What are the steps to get a contract signed?
  "Walk me through how you've bought software before."

I — Identify Pain: What's the urgency?
  "What happens if you don't solve this by [DATE]?"

C — Champion: Who will advocate internally?
  "Who on your team is most excited about solving this?"
```

## HubSpot CRM essentials
```
Contacts → create deal → associate contact + company
Deals → set pipeline stage → add notes after every interaction
Sequences: automate email cadences (Sales Hub)
Reports: Pipeline by stage → identify conversion bottlenecks
Tasks: log next action with due date on every deal (never let a deal go dark)

Key HubSpot shortcuts:
  Ctrl+K: universal search
  @ mentions: tag teammates in notes
  @contact: link contact in notes
```

## Salesforce essentials
```bash
# Objects: Account → Contact → Opportunity → Activity
# Views: My Open Opportunities, This Quarter Closing

# Key fields to track:
Account: Industry, Size, ACV, Renewal date
Opportunity: Stage, Close date, Amount, Next step, Probability
Activity: Subject, Due date, Result

# SFDC reports:
Pipeline by Stage: shows deals + weighted value
Forecast: rollup by owner + stage
Activity: calls/emails per rep per week

# Salesforce CLI (for admins)
sf org login web --set-default-org
sf data query --query "SELECT Id, Name, Amount FROM Opportunity WHERE StageName='Proposal'"
```

## Objection handling patterns
```
Objection: "It's too expensive."
Response: "I understand. Help me understand — relative to what? [pause]
  If we can show ROI of 3-5× in 6 months, would that change the conversation?"

Objection: "We're happy with our current solution."
Response: "That's great. What made you take the call today?
  Most customers who say that eventually switch because of [common pain]."

Objection: "Not the right time."
Response: "That makes sense. What would have to change for the timing to be right?
  Is it budget, priorities, or something else?"

Rule: acknowledge → ask a question → don't pitch back immediately.
```

## Common pitfalls
- Not updating CRM after every touchpoint: pipeline becomes inaccurate → bad forecasting.
- Quoting before discovery: feature pitch without understanding pain → price objection.
- Single-threaded deals: only knowing one contact → deal dies when champion leaves.
- Discounting too early: creates expectation; anchor on value first.
""",
    ),
    SkillEntry(
        slug="legal-contracts",
        name="Legal — contracts review, NDAs, SaaS agreements, IP, compliance",
        description=(
            "Legal fundamentals for tech teams: NDA review, SaaS MSA/DPA terms, "
            "IP assignment, open-source compliance, and when to escalate to counsel."
        ),
        domain=SkillDomain.CORPORATE,
        tags=[
            "legal",
            "contracts",
            "nda",
            "saas",
            "msa",
            "ip",
            "gdpr",
            "compliance",
            "open-source",
            "corporate",
        ],
        prerequisites=[],
        body="""\
# Legal Contracts Skill

## NDA review checklist (as disclosing party)
```
✅ Mutual vs one-way: mutual preferred (protects both sides)
✅ Definition of confidential: broad enough to cover all discussions
✅ Exclusions: standard carve-outs are fine (public info, independently developed)
✅ Term: 2-3 years for discussions; perpetual for trade secrets
✅ Purpose limitation: "solely for evaluating a potential business relationship"
✅ Governing law: your home state preferred; avoid arbitration clause in NDAs
✅ Return/destroy: include obligation to destroy confidential info on request

🚩 Red flags:
- Missing "as determined by the disclosing party" on what's confidential
- Overly broad injunction clause (seek legal advice)
- Liability cap lower than potential damages
```

## SaaS subscription agreement key terms
```
For customers reviewing vendor MSAs:
✅ Data ownership: "Customer retains all rights to Customer Data"
✅ DPA (Data Processing Agreement): required for GDPR if EU data involved
✅ Uptime SLA: 99.9% = ~8.7h downtime/year; 99.99% = ~52 min/year
✅ Service credits: credit for SLA breaches (typically 10-25% of monthly fee)
✅ Security: SOC 2 Type II report available? Penetration testing?
✅ Termination for cause: 30-day cure period before termination
✅ Data deletion: 30-day post-termination export window + deletion confirmation
✅ Liability cap: typically 12 months of fees paid — negotiate for higher if critical

🚩 Red flags:
- Unilateral price change without notice
- "We may change these terms at any time" without notification
- Broad license to use your data for product improvement
- No data breach notification SLA (should be ≤ 72h for GDPR)
```

## IP assignment (employee/contractor)
```
Every employee and contractor MUST sign:
1. Proprietary Information and Inventions Agreement (PIIA)
   - Assigns all work-product to company
   - Covers inventions created during employment (even outside work hours if related)
   - Exception: pre-existing IP listed in Exhibit A

2. Non-disclosure agreement (included in most employment agreements)

Key: do this BEFORE work starts. Retroactive assignment is messy.
Tools: Clerky, Stripe Atlas, or Wilson Sonsini templates for standard forms.
```

## Open-source license compliance
```
License types and restrictions:
MIT / BSD / Apache 2.0:
  - Permissive: use in commercial product, no copyleft
  - Requirement: include copyright notice in distribution

GPL v2/v3:
  - Copyleft: if you distribute GPL software, you must open your source too
  - Concern: using GPL library in closed-source product = problem
  - Solution: LGPL (Lesser GPL) allows linking without copyleft

AGPL:
  - Network copyleft: even SaaS use requires open-sourcing
  - Never use AGPL dependencies in commercial SaaS without legal review

SSPL (MongoDB, Elasticsearch):
  - Service provision copyleft: providing SSPL software as a service = must open all
  - Not OSI-approved; treat as proprietary for commercial use

Compliance tools:
- FOSSA: automated open-source license compliance scanning
- Snyk: security + license scanning
- licensee: GitHub's open-source license detection
```

## GDPR basics for tech teams
```
Key obligations for SaaS companies with EU users:
1. Lawful basis for processing (consent / legitimate interest / contract)
2. Privacy notice: what data, why, how long, with whom
3. DPA with all sub-processors (AWS, Stripe, etc.)
4. Data subject rights: access, deletion, portability (respond within 30 days)
5. Breach notification: report to DPA within 72 hours if >250 people affected
6. Data residency: EU customers may require EU data storage
7. SCCs (Standard Contractual Clauses) for transfers to non-EU processors

Tools: osano.com (consent management), OneTrust (privacy compliance platform)
```

## When to get a lawyer
```
Always use a lawyer for:
- Incorporating the company
- First investment (SAFE, convertible note, equity round)
- Hiring your first employees in a new country
- Enterprise contracts > $50K that you didn't draft
- IP disputes or cease-and-desist letters
- Any acquisition or M&A discussion

Cost-effective options:
- Clerky / Stripe Atlas: automated startup legal docs (~$500-2K)
- Gust Launch: free incorporation + standard docs
- Priori Legal / Lawtrades: marketplace for startup-focused lawyers
- Big firm: only for Series A+ or complex IP matters
```

## Common pitfalls
- Handshake deals: always get it in writing, even with friends/co-founders.
- No IP assignment from contractors: most expensive startup legal mistake.
- GPL in commercial product: audit your dependencies with FOSSA before scaling.
- Ignoring GDPR: EU fines up to 4% of global revenue — not theoretical.
""",
    ),
]
