# SBI Vishwas
### One trusted AI companion across a customer's entire SBI relationship — from the first branch visit to the first formal loan.

*("Vishwas" = trust, deliberately named after the first of RBI FREE-AI's seven Sutras: "Trust is the Foundation.")*

---

## 1. The One-Line Pitch

A single agentic AI system that follows a customer through two connected moments where SBI currently loses them: **at the front door**, where inconsistent branch practices, forced product bundling, and unresponsive support drive people away during acquisition — and **later, in silence**, when accounts go dormant and are never given a real path to formal credit. One architecture, one trusted identity, two coordinated phases, spanning all three pillars of the problem statement.

---

## 2. The Problem, Stated With Evidence (Not Assumptions)

### Phase A evidence — the acquisition experience is actively repelling people, right now, in public
Real, current discussion across r/personalfinanceindia, r/IndiaTech, r/IndianWorkplace, r/AskIndia, r/LegalAdviceIndia surfaces a consistent pattern:
- **Time-consuming, inconsistent branch processes.** Customers describe multi-hour waits for something as simple as opening an account, and arbitrary demands (e.g., insisting a specific person's physical presence is "mandatory" when it isn't) that force repeat visits for a single task.
- **Mandatory product bundling that contradicts official policy.** Multiple accounts describe being told insurance purchase is "mandatory" to open a plain zero-balance savings account — which directly contradicts RBI's own rules for Basic Savings Bank Deposit accounts.
- **Unreliable digital channels and confusing security friction** — technical errors that persist for days, and security requirements so aggressive they block legitimate, already-secure setups.
- **No communication after digital processes complete** — one account describes an account opening confirmed only by a single vague SMS, with no account details, no welcome email, no card-dispatch timeline.
- **Customer support that loops without resolving** — one person describes being transferred six times, each time promised a handoff to "the relevant agent," with nothing resolved.
- **A broken internal escalation path.** The clearest, most damning data point: a complaint sat unresolved at branch level for six months, and was fixed within one day only after being escalated to the RBI Banking Ombudsman. That is direct evidence SBI's *own* internal grievance process does not work as an internal process — customers only get resolution by going external.
- **This isn't purely a "bad staff" problem.** Bank employees themselves describe unrealistic cross-sell quotas ("I'm a banker, not a street vendor") and workdays running to 9–9:30pm. Aggressive selling is a systems and incentive problem, not an individual one — and any fix that ignores this will meet internal resistance.

### Phase B evidence — the accounts that do get opened often go silent, and are never given a path to credit
- SBI's own Jan Dhan dormancy rate rose from **19% (Sept 2024) to 25% (Sept 2025)** — worsening, not stable.
- Nationally, **142.8 million of 545.5 million PSB Jan Dhan accounts are inactive**, holding roughly **₹3.06 lakh crore** in the overall PMJDY pool.
- The government ran a **manual door-to-door reactivation campaign in July–Sept 2025** — proving both the need and the budget exist, and that manual outreach doesn't scale.
- Independent policy critique (The India Forum, 2026) notes PMJDY accounts have mostly served as an insurance cross-sell channel, not a genuine gateway to credit.
- **Only ~3% of India's Jan Dhan accounts sit with private-sector banks** — this is structurally a public-sector-bank problem.

**The connecting insight:** these are not two separate problems. They are the same relationship, at two different points of neglect. A customer who survives a bad onboarding experience is exactly the kind of customer who later goes quiet and is never reactivated properly. Fixing only one half leaves the other half of the leak untouched.

---

## 3. Target Segments

- **Phase A:** Any new or existing customer at the point of branch/call-center/digital contact — walk-in account openers, existing customers seeking basic service changes, anyone navigating a support issue.
- **Phase B:** Dormant/low-activity PMJDY account holders already in SBI's book — rural, first-generation, vernacular-first, often reachable only via Bank Mitra or IVR.

---

## 4. Pillars Addressed (all three, one coherent brand)

- **Pillar 1 — Acquisition:** Phase A directly fixes the leaking front door — the exact moment SBI is losing prospective and existing customers to a bad first experience.
- **Pillar 2 — Adoption:** Both phases drive adoption — Phase A by making digital/branch account opening actually work as advertised; Phase B by moving reactivated customers onto formal credit products (KCC, Mudra) they never had access to.
- **Pillar 3 — Engagement:** The same trusted identity carries through — the agent that got you a fair, transparent onboarding is the same one that reaches back out, respectfully, if your account goes quiet later.

---

## 5. Full Agent Architecture

### PHASE A — Onboarding Advocate

**Agent 1 — Journey Tracker Agent**
Maintains a single, persistent case file per customer from first contact (branch, call center, app, WhatsApp) through resolution. No customer is ever forced to re-explain themselves after being "transferred six times" — the exact failure mode found in the evidence. Any channel a customer touches sees the same case history.
*Tools:* unified case-management layer across branch/call-center/digital systems (sandboxed for the prototype).
*Autonomy:* decides which existing case a new contact belongs to and routes accordingly, without asking the customer to repeat themselves.

**Agent 2 — Policy Compliance Companion Agent** *(the sharpest, most differentiated mechanic in the pitch)*
In real time, checks any document demand or product-bundling requirement mentioned during a branch or call interaction against actual official policy — e.g., confirming that a zero-balance BSBD account genuinely requires no insurance purchase. Framed constructively for both sides: it gives the **customer** an instant, accurate answer they can act on immediately, and it gives the **branch employee** the same accurate policy reference on demand, removing the burden of memorizing every scheme's fine print and reducing honest mistakes. Deviations are logged to a branch-level pattern dashboard for management — this is about surfacing systemic issues (e.g., a quota-driven push at a specific branch) to leadership, not flagging individual staff for blame.
*Tools:* a maintained knowledge base of current RBI/SBI product policies; conversation-monitoring interface (sandboxed).
*Autonomy:* decides when a stated requirement conflicts with policy and surfaces the correct information immediately, in-conversation.

**Agent 3 — Proactive Communication Agent**
The moment any process completes — account opening, a service request, a complaint resolution — automatically sends a complete, specific status update: account number, card dispatch ETA, next steps, and how to get help. Directly closes the "just one vague message, nothing else" gap found in the evidence.
*Tools:* CBS event triggers, SMS/email/WhatsApp dispatch.
*Autonomy:* decides what information is relevant to send and when, without waiting for a customer to ask.

**Agent 4 — Escalation & Advocate Agent**
Tracks every open issue against a defined SLA. If a service issue isn't resolved internally within that window, it escalates automatically up SBI's own grievance hierarchy — before the customer is forced to go external to the RBI Ombudsman, which the evidence shows is currently the *only* path that reliably works. This directly fixes the six-months-vs-one-day gap.
*Tools:* internal escalation/ticketing system integration (sandboxed), SLA tracking.
*Autonomy:* decides when internal escalation is warranted and to whom, without waiting for the customer to complain further.

### PHASE B — Reactivation & Credit-Readiness *(carried forward from the validated Sopan architecture)*

**Agent 5 — Diagnosis Agent**
Classifies each dormant account's likely cause of silence — no DBT-linkage, lost access, duplicate/migrated account, seasonal income gaps, or genuinely no ongoing need — from historical CBS signals, and suppresses outreach to genuinely no-need accounts rather than wasting effort pursuing them.

**Agent 6 — Readiness Agent**
Computes a **Day-1 financial-readiness score from each account's existing historical data** (DBT receipt regularity, past overdraft/KCC conduct, prior RuPay usage) — the technical unlock that makes this demoable immediately rather than requiring months of new data. Refines the score continuously as real post-reactivation behavior accrues. Never approves anything — only classifies readiness with an explainability note.

**Agent 7 — Channel & Journey Agent**
Chooses the outreach channel per account — YONO/WhatsApp for the digitally reachable, IVR in the customer's registered language for voice-only reach, or a **pre-qualified, pre-scripted Bank Mitra visit** for the hardest cases. Pre-scripting raises a BC's success rate per visit — a genuine productivity and earnings improvement for Bank Mitras, directly answering the fair-pay/workload tension BCs have publicly raised, not just loading more unpaid work onto them.

**Agent 8 — Graduation Agent**
Once the readiness score crosses a defined threshold, prepares (never approves) a small-ticket credit application — a KCC top-up, a Mudra loan, or a formal personal loan — for human sign-off.

### Shared across both phases — Human Override & Audit Guardian
A sidecar to every agent above. Any credit-adjacent or policy-deviation-flagging output routes to a human before any action is finalized. Every diagnosis, score, policy check, escalation, and override is logged immutably, creating a full audit trail across both phases.

---

## 6. Why This Is Genuinely Agentic, Not a Chatbot or a Compliance Checklist

Both phases reason and act autonomously across multiple steps without a human prompting each one: Phase A tracks a case across channels, checks a live conversation against policy, decides what communication to send and when, and decides when internal escalation is warranted — all without the customer having to ask. Phase B diagnoses a cause, computes a score from existing data, chooses a channel, runs the outreach conversation, and decides when someone has earned a credit conversation. A chatbot answers questions when asked. This system watches, decides, and acts across an entire relationship lifecycle, touching a human only at the specific points regulators and good judgment actually require one.

---

## 7. The Moat — Why This Is Genuinely Hard to Copy

- **Phase A's moat is organizational, not technical:** building a Policy Compliance Companion that checks live branch conversations against policy requires deep, credible internal access and institutional trust that only an actual SBI-sanctioned initiative could get — no external fintech could plausibly get permission to "watch" bank staff interactions. This is a moat of *mandate*, not just data.
- **Phase B's moat is structural:** requires a Jan Dhan book and Bank Mitra network at genuinely national PSU scale, and years of historical CBS/DBT data on a population private banks and fintechs have never held (~3% of Jan Dhan accounts sit with private banks).
- **Together:** no private-sector competitor can plausibly pitch either half of this, let alone both.

---

## 8. Scale & Vernacular Design

- Phase A's Policy Compliance Companion works in any branch conversation, in the customer's language, and scales the moment it's rolled out to a branch — no per-customer onboarding required.
- Phase B remains channel-agnostic by design — BC-assisted default, IVR/USSD for feature phones, WhatsApp/YONO for the digitally comfortable — chosen automatically per account.
- Both phases are vernacular-first: every customer-facing interaction runs in the language on record or the local branch language, not just Hindi/English.
- Pilot-to-national path: Phase A can start in a cluster of branches with known service-quality variance; Phase B starts as a 10-branch dormancy pilot. Neither requires re-architecture to scale — only rollout.

---

## 9. Regulatory Design

**FREE-AI Sutras embodied (verified against RBI's actual framework, 13 Aug 2025):**
- **Trust is the Foundation** — the entire brand identity of "Vishwas" is built around this; both phases exist specifically to make AI-mediated banking *more* trustworthy than the current human-only process, not less.
- **People First** — every policy flag, escalation, and credit-readiness output is advisory; a human always makes the final call, and customers/staff can always override.
- **Innovation over Restraint** — proactively surfacing policy violations and readiness signals is a genuinely bold use of AI in a regulated environment, consistent with the framework's stated preference for responsible innovation over excessive caution.
- **Fairness and Equity** — Phase A protects customers regardless of branch, literacy, or negotiating confidence from being pushed into unwanted products; Phase B is built specifically for a population conventional credit scoring excludes.
- **Accountability** — accountability for every flagged deviation or credit decision sits with the human/branch/rules engine that acts on it, not the AI.
- **Understandable by Design** — every policy check and readiness score carries a plain-language explanation.
- **Safety, Resilience, and Sustainability** — Phase A never overrides a staff member's action directly, only informs; Phase B is read-mostly and never autonomously moves funds.

**DPDP Act 2023 mechanics:**
- Phase A's conversation-monitoring for policy compliance is scoped narrowly to policy-relevant statements (product terms, requirements mentioned), not full conversation retention — data minimisation by design.
- Phase B's staged consent (service-communication basis for reactivation, then separate explicit opt-in for readiness scoring) carries forward unchanged from the validated Sopan design.
- Neither phase functions as an external credit bureau or reporting mechanism — both are internal SBI tools serving internal SBI decisions.

---

## 10. Business Case

**Metrics moved:**
- Phase A: account-opening completion time and drop-off rate, first-contact-resolution rate, internal-vs-external (Ombudsman) escalation ratio, new-to-bank conversion rate — all metrics directly tied to the acquisition-cost problem the evidence exposes.
- Phase B: Jan Dhan dormancy rate (reversing the current 19%→25% trend), CASA float, priority-sector-lending pipeline, Bank Mitra per-visit success rate.

**Why this is bigger than either phase alone:** Phase A reduces the number of customers lost at the door in the first place — directly lowering the cost of acquiring the customers Phase B would otherwise have to win back later. A jury sees a single, coherent economic story: fewer people leaking out of the top of the funnel, and a real path back in for the ones who already went quiet.

**Employee-side framing, addressed directly (not ignored):** the Policy Compliance Companion is explicitly designed to reduce staff burden — giving frontline employees an instant, accurate policy reference removes the pressure of memorizing every scheme's fine print and protects good employees from being blamed for honest mistakes, while surfacing systemic quota-driven patterns to leadership rather than individual staff. This is a genuine answer to the internal resistance a "watching staff" framing would otherwise create.

**Post-hackathon commercialisation path:**
- *Phase 1:* Pilot Phase A in a small cluster of branches with known service-quality complaints; pilot Phase B in 10 dormancy-heavy branches.
- *Phase 2:* Expand both to ~200 branches per phase, integrating with SBI's internal case-management and BC systems.
- *Phase 3:* Pan-India rollout of both modules under one Vishwas brand, priced as a SaaS-style or outcome-based contract.

---

## 11. 30-Day Prototype Scope — Honest About What Gets Built

Given the timeline, **the live demo should center on Phase A** — the Policy Compliance Companion and Journey Tracker are more viscerally demonstrable in a 30-day sandbox (a jury can watch a live conversation get checked against policy in real time), while Phase B's Readiness Agent is described and partially demoed on historical data as the validated next module, not built to the same depth. Say this scoping decision to the jury directly — it shows judgment about what a 30-day build can and can't credibly deliver.

**Real, working in the demo:**
- Journey Tracker Agent maintaining a single case across at least two simulated channels.
- Policy Compliance Companion checking a live, scripted branch conversation against a real policy knowledge base (e.g., correctly flagging an attempted mandatory insurance bundling on a zero-balance account).
- Proactive Communication Agent firing a complete status message immediately after a simulated account-opening event.
- Escalation Agent auto-escalating a simulated unresolved case past its SLA window.
- Phase B's Diagnosis and Readiness Agents computing a live Day-1 score from a realistic synthetic historical dataset — shown as validated proof of the second module, not the primary live demo.

**Clearly labelled as simulated:**
- Live integration with SBI's actual branch/call-center systems and CBS.
- The live human escalation-handling workflow on the SBI side.
- Full BC-app integration for Phase B.

---

## 12. Honest Rubric Self-Score

| Dimension | Score | Why |
|---|---|---|
| Innovation | 89 | An AI that checks a bank's own staff against policy in real time, live, in front of the customer, is a genuinely sharp, rarely-pitched mechanic — sharper than dormancy-scoring alone. |
| Technical Feasibility | 82 | Phase A's live conversation-monitoring is honestly the harder engineering problem in 30 days; scoping the demo around it (rather than both phases equally) keeps this credible. |
| Business Potential | 90 | Directly reduces acquisition-cost leakage at the top of the funnel while Phase B recovers value lower down — one coherent economic story. |
| Scalability | 92 | Both phases are vernacular-first and channel-agnostic; Phase A scales branch-by-branch with no per-customer onboarding needed. |
| User Experience | 90 | Solves the two most viscerally-felt complaints in the evidence directly: forced bundling and communication silence. |
| Regulatory Readiness | 86 | Full FREE-AI Sutra mapping for both phases, narrowly-scoped data use for Phase A, staged consent carried over from the validated Phase B design. |
| **Average** | **~88.2** | **Floor: 82 — every dimension clears the 75 minimum with real margin.** |

---

## 13. The Toughest Jury Questions, Answered in Advance

**"Won't branch staff resist or sabotage an AI that's watching them?"**
It isn't framed or built as surveillance of individuals — it gives staff the same accurate, instant policy answer it gives customers, reducing the burden of memorizing every scheme's terms and protecting honest employees from being blamed for mistakes. Patterns are surfaced to branch/regional leadership for systemic quota or training issues, not used to flag individual staff. This is designed to reduce frontline pressure, not add to it.

**"How do you verify the policy checks are accurate, so you're not creating false accusations against staff or wrong information for customers?"**
The compliance knowledge base is maintained against official RBI/SBI policy documents with version control and a human-reviewed update process; any flagged deviation is presented as informational to the customer and staff member in real time, never as an automatic penalty or public accusation — a human always resolves any actual dispute.

**"Isn't it risky and potentially embarrassing for SBI if the AI publicly corrects a staff member in front of a customer?"**
The correction is framed collaboratively — "let's check the current policy on this together" — not as a public callout, and the staff member benefits from the same accurate answer. This is materially better for SBI's reputation than the status quo the evidence shows: customers escalating to the RBI Ombudsman and posting about six-month unresolved complaints publicly on Reddit.

**"Why hasn't SBI already fixed this internally, without AI?"**
Because the evidence shows the internal escalation path itself is the broken part — a complaint that sat for six months got fixed in one day only once it left SBI's internal process entirely. Vishwas's Escalation & Advocate Agent is specifically an automation of internal accountability, not a new customer-facing gimmick layered on top of a working process.

**"Isn't this two ideas bundled into one submission?"**
They're one relationship viewed at two points of failure: the same trust identity that gets you onboarded fairly is the one that reaches back out if your account goes quiet. The 30-day prototype is honestly scoped to build Phase A deepest, with Phase B demonstrated as the validated next module — not two unrelated builds competing for the same 30 days.

---

## 14. Closing Argument for the Submission

Every complaint in this evidence — the six-hour account opening, the forced insurance, the silence after digital account creation, the six-times-transferred call, the six-month wait fixed in a day only by going outside the bank entirely — describes the same underlying failure: nobody at SBI is watching the relationship as a whole, in real time, with the customer's interest actually held as the priority. Vishwas is that missing layer. It doesn't replace branch staff or Bank Mitras — it gives both the customer and the employee the same accurate, real-time ground truth, and it makes sure a relationship that starts well doesn't quietly die later for lack of anyone noticing. That is what "Trust is the Foundation" means when it stops being a Sutra on a page and becomes a system running in every branch.
