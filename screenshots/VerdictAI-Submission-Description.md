# VerdictAI

### Multi-Agent Autonomous Dispute Resolution for Ride-Hailing

**Tencent Cloud x AI Singapore Hackathon 2026 — Digital Native Track (Ryde)**

---

## Overview & Purpose

Every day, ride-hailing platforms process thousands of disputes — contested fares, no-show cancellations, route disagreements. These disputes are currently resolved by human customer service agents who manually review evidence, interpret policies, and issue rulings. The result: resolutions take 24 to 72 hours, rulings vary from agent to agent, and the operational cost of scaling CS teams grows faster than rider and driver growth.

**VerdictAI replaces this manual bottleneck with an autonomous multi-agent system.** Inspired by adversarial legal proceedings, VerdictAI assigns a dedicated AI advocate to each party — one for the rider, one for the driver — and a neutral AI judge weighs both cases against evidence and policy to render a verdict in minutes, not days. Every verdict includes a transparent reasoning chain, a confidence score, and a human escalation path for ambiguous cases.

The purpose is not to eliminate human judgment. It is to **reserve human judgment for the cases that truly need it** — the ambiguous, the edge, the emotionally charged — while letting AI handle the clear-cut majority with speed, consistency, and full transparency.

---

## Who Benefits

### Ryde (Platform)

- **Cuts resolution time from 72 hours to under 5 minutes** for clear-cut disputes
- **Reduces CS workload by 60–80%** on handled dispute types, freeing agents for complex cases
- **Ensures policy consistency** — the same rules applied the same way every time, eliminating inter-agent variance
- **Builds trust** through transparent, explainable verdicts that users can understand

### Riders

- **Fast resolution** — no more waiting days for a fare dispute ruling
- **Fair representation** — a dedicated AI advocate argues their side, not just a neutral arbiter
- **Clear explanations** — every verdict explains *why* using plain language, specific evidence, and cited policy
- **Appeal rights preserved** — 48-hour window to request human review on any AI verdict

### Drivers

- **Equal voice** — drivers get their own advocate, ensuring their perspective is heard
- **Faster exoneration** — wrongly accused drivers are cleared in minutes, not days
- **Evidence-based rulings** — verdicts cite GPS data, trip logs, and chat history, not subjective judgment
- **Same appeal rights** — drivers can escalate to human review at any time

---

## How the Multi-Agent System Works

VerdictAI is built on **CrewAI**, a multi-agent orchestration framework that enables role-based agents with distinct goals, tools, and backstories to collaborate on structured tasks.

### The Agents

**Agent 1 — Rider Advocate**

- **Role:** Acts as the rider's dedicated representative
- **Goal:** Build the strongest possible case for the rider using evidence and policy
- **Tools:** GPS trail retrieval, fare receipt parser, in-trip chat history, policy vector database
- **Process:** Interviews the rider via structured chat, pulls rider-side evidence, cross-references claims against system data, and produces a structured Case Brief

**Agent 2 — Driver Advocate**

- **Role:** Acts as the driver's dedicated representative
- **Goal:** Build the strongest possible case for the driver using evidence and policy
- **Tools:** Route data retrieval, trip log parser, earnings breakdown, navigation data, policy vector database
- **Process:** Interviews the driver via structured chat, pulls driver-side evidence, cross-references claims against system data, and produces a structured Case Brief

**Agent 3 — Judge Agent**

- **Role:** Neutral adjudicator
- **Goal:** Render a fair, policy-grounded verdict with full reasoning
- **Tools:** Policy vector database, evidence cross-referencing, confidence scoring
- **Process:** Reviews both Case Briefs simultaneously, identifies agreements and contradictions, cross-checks evidence claims against raw system data, retrieves relevant policies, and renders a structured verdict

### The Flow (Step by Step)

```
                    ┌─────────────────┐
                    │  Dispute Filed   │
                    │  (rider/driver)  │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │     CrewAI       │
                    │   Orchestrator   │
                    │  (classifies &   │
                    │   routes case)   │
                    └────────┬────────┘
                             │
              ┌──────────────┴──────────────┐
              │                             │
    ┌─────────▼─────────┐         ┌─────────▼─────────┐
    │  Rider Advocate   │         │  Driver Advocate   │
    │                   │         │                   │
    │  • Interviews     │         │  • Interviews     │
    │    rider          │         │    driver          │
    │  • Pulls rider    │         │  • Pulls driver   │
    │    evidence       │         │    evidence        │
    │  • Builds case   │         │  • Builds case    │
    │    brief          │         │    brief           │
    └─────────┬─────────┘         └─────────┬─────────┘
              │                             │
              └──────────────┬──────────────┘
                             │
                    ┌────────▼────────┐
                    │   Judge Agent   │
                    │                 │
                    │ • Reviews both  │
                    │   briefs        │
                    │ • Cross-checks  │
                    │   evidence      │
                    │ • Retrieves     │
                    │   policies      │
                    │ • Scores        │
                    │   confidence    │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │ Confidence Gate  │
                    └────────┬────────┘
                    ┌────────┴────────┐
                    │                 │
              ≥ 70%               < 70%
                    │                 │
           ┌────────▼──────┐  ┌──────▼─────────┐
           │   Verdict     │  │    Human CS    │
           │  Delivered    │  │  Escalation    │
           │  (auto)       │  │  (+ appeals)   │
           └───────────────┘  └────────────────┘
```

**Step 1 — Dispute filed.** A rider or driver taps "File a Dispute" in the Ryde app after a completed trip, selects a category, and describes what happened in free text.

**Step 2 — CrewAI Orchestrator routes the case.** The orchestrator classifies the dispute type, creates a case ID, pulls the trip record from the database, and launches both advocate agents in parallel.

**Step 3 — Advocates work simultaneously.** Each advocate interviews its respective party through a structured chat, retrieves evidence from the system, cross-references claims against hard data, and produces a structured Case Brief containing: claim summary, evidence list, policy citations, and a recommended outcome from that party's perspective.

**Step 4 — Judge reviews both briefs.** The Judge Agent receives both Case Briefs, identifies where the two sides agree and where they contradict, cross-checks evidence claims against raw system data (GPS coordinates, timestamps, fare calculations), retrieves relevant policies from the vector database, and calculates a confidence score (0–100%).

**Step 5 — Confidence gate.** If confidence is 70% or above, the verdict is auto-delivered to both parties with a full reasoning chain and a 48-hour appeal window. If below 70%, the case is escalated to human CS — the AI augments human judgment rather than replacing it.

**Step 6 — Verdict delivered.** Both parties receive the ruling, the recommended action (refund, warning, account flag), a plain-language explanation citing specific evidence and policy clauses, the confidence level, and appeal instructions.

---

## The 2 Dispute Scenarios (MVP)

### Scenario 1: Fare / Route Dispute

**The conflict:** A rider claims the driver took a longer route to inflate the fare. The driver claims they followed the GPS-assigned route or that the rider requested the deviation.

**How VerdictAI resolves it:**

- The Rider Advocate pulls the expected fare estimate, the rider's GPS trail, and in-trip chat history to check for any route change request
- The Driver Advocate pulls the navigation app's assigned route, the trip log, and the driver's earnings breakdown
- The Judge cross-references: Does the actual GPS route match the assigned route? Was there a route change request in the chat? How much longer was the actual distance?
- Verdict is rendered against Ryde Fare Policy (detour thresholds), LTA point-to-point transport regulations, and the Consumer Protection (Fair Trading) Act

**Example verdict:** GPS data shows the route was 3.2km longer than estimated. In-trip chat shows no route change request from the rider. Driver is liable — partial refund of S$4.50 issued automatically. Confidence: 82%.

### Scenario 2: Cancellation / No-Show Dispute

**The conflict:** A rider claims the driver never showed up at the pickup point. The driver claims the rider wasn't at the agreed location.

**How VerdictAI resolves it:**

- The Rider Advocate pulls the rider's arrival timestamp, waiting duration, and location coordinates at the time of cancellation
- The Driver Advocate pulls the driver's arrival timestamp, GPS position at the pickup point, waiting time log, and any call or chat attempts made
- The Judge cross-references: Were both parties' GPS coordinates within proximity of the pickup point? Who arrived first? How long did each wait? Did the driver attempt to contact the rider?
- Verdict is rendered against Ryde's cancellation policy (wait time thresholds, who initiated cancellation), LTA rules, and fair cancellation fee guidelines

**Example verdict:** Driver's GPS shows arrival at the pickup point at 10:42 AM. Rider's GPS shows arrival at 10:48 AM — 6 minutes after the driver. Driver made 2 call attempts at 10:44 and 10:46. Cancellation was initiated by the rider. Rider is liable for the cancellation fee. Confidence: 89%.

---


## Business Impact

### Speed
| Metric | Before (Human CS) | After (VerdictAI) | Improvement |
|--------|-------------------|-------------------|-------------|
| Resolution time | 24–72 hours | 3–5 minutes | **99% faster** |
| Evidence gathering | Manual, per-agent | Automated, parallel | Simultaneous |

### Cost
| Metric | Before | After | Impact |
|--------|--------|-------|--------|
| CS agent hours per dispute | 45–90 min | 0 min (auto) / 15 min (escalated) | **60–80% reduction** on handled types |
| Disputes requiring human review | 100% | ~20–30% (low confidence + appeals) | Humans handle only what matters |

### Fairness
| Metric | Before | After | Impact |
|--------|--------|-------|--------|
| Ruling consistency | Varies by agent | Same rules every time | **Eliminated inter-agent variance** |
| Transparency | "Decision made" email | Full reasoning chain with evidence + policy citations | Users see exactly *why* |
| Appeal process | Email request, days to review | In-app, 48-hour window, routes to human CS | Faster, more accessible |

### The Bigger Picture
VerdictAI transforms dispute resolution from a **cost center** into a **trust engine**. Faster, fairer, more transparent resolutions mean happier riders and drivers — which means better retention, higher platform ratings, and lower churn. The system is also extensible: new dispute types (lost items, safety incidents, payment failures) can be added by defining new evidence sources and policy sets — the agent architecture stays the same.

---

## Tools & Technologies

### Multi-Agent Orchestration
| Tool | Role |
|------|------|
| **CrewAI** | Core multi-agent framework. Defines the Rider Advocate, Driver Advocate, and Judge as role-based agents with distinct goals, tools, and backstories. The orchestrator uses CrewAI's process management to run both advocates in parallel, collect their case briefs, then pass both to the Judge agent for adjudication. |

### User Interface
| Tool | Role |
|------|------|
| **Streamlit** | Web application framework for the demo interface. Renders the dispute filing form, live agent status updates, evidence display panels, and the final verdict with reasoning chain. Chosen for rapid prototyping — a full chat-based dispute UI can be built in under 2 hours. |

### Development
| Tool | Role |
|------|------|
| **WorkBuddy / CodeBuddy** | AI development assistant used throughout the build. Architecture planning, agent prompt engineering, code scaffolding, debugging, and iterative refinement of the CrewAI agent definitions and Streamlit UI components. Accelerates the 1-day build timeline significantly. |

### Supporting Infrastructure
| Tool | Role |
|------|------|
| **Tencent Cloud Hunyuan** | LLM powering all three agents — aligned with hackathon sponsor ecosystem |
| **Tencent Cloud VectorDB** | Stores Ryde policies and Singapore regulations as embeddings for semantic retrieval during adjudication |
| **Tencent Cloud COS** | Object storage for evidence files (screenshots, dashcam metadata, receipts) |
| **Python + FastAPI** | Backend API layer connecting the CrewAI agents to the Streamlit frontend |

### Why This Stack
- **CrewAI** was chosen over LangGraph and AutoGen because its role-based agent model maps naturally to the advocate-judge pattern — each agent has a clear role, goal, and set of tools, and the framework handles parallel execution and result aggregation natively
- **Streamlit** was chosen over React/Next.js because it lets a single developer build a complete, interactive demo UI in under 2 hours — critical for a 1-day hackathon
- **WorkBuddy / CodeBuddy** accelerates every stage — from architecture design to prompt engineering to UI scaffolding — compressing what would be a 2–3 day build into 1 day

---

## Sample Verdict Output

```json
{
  "case_id": "RYDE-DSPT-20261015-0042",
  "dispute_type": "fare_route_dispute",
  "verdict": {
    "liable_party": "driver",
    "recommended_action": "partial_refund",
    "refund_amount_sgd": 4.50,
    "confidence_score": 82,
    "escalate_to_human": false
  },
  "reasoning_chain": [
    "Rider claims driver took a longer route via Bukit Timah Road instead of the direct PIE route.",
    "GPS data confirms actual route was 3.2km longer than the estimated route.",
    "Driver claims rider requested the route change, but in-trip chat shows no such request.",
    "Ryde Fare Policy Section 4.2: drivers must follow the assigned route unless the rider explicitly requests a change.",
    "LTA Point-to-Point Transport Rules require fare transparency — deviations without rider consent are classified as overcharging.",
    "Conclusion: Driver is liable for the fare difference. Partial refund of S$4.50 recommended."
  ],
  "appeal_available": true,
  "appeal_window_hours": 48,
  "agents_involved": ["rider_advocate", "driver_advocate", "judge"]
}
```

---

## What Makes VerdictAI Different

| Feature | Traditional CS | Single-LLM Chatbot | VerdictAI |
|---------|----------------|--------------------|----|
| Both parties represented | Partially | No — one-sided | **Yes — dedicated advocates per party** |
| Policy grounded | Yes (manual lookup) | No — LLM hallucinates rules | **Yes — vector DB retrieval with citations** |
| Transparent reasoning | "Decision: refund issued" | Black box | **Full reasoning chain with evidence + policy** |
| Human escalation | All cases | None | **Confidence-gated — only ambiguous cases** |
| Resolution speed | 24–72 hours | Minutes | **3–5 minutes** |
| Ruling consistency | Varies by agent | Varies by prompt | **Same rules every time** |

---

## Conclusion

VerdictAI brings the principles of adversarial justice to ride-hailing disputes. By giving both riders and drivers dedicated AI advocates, grounding every verdict in real policy via vector database retrieval, and gating human escalation on confidence scores, VerdictAI delivers a system that is faster, fairer, and more transparent than today's manual process — while preserving human judgment for the cases that truly need it.

Built with CrewAI for multi-agent orchestration, Streamlit for rapid UI prototyping, and developed using WorkBuddy / CodeBuddy for accelerated coding, the entire system is achievable within a single hackathon day and immediately demonstrable on two of the most common real-world dispute scenarios.
