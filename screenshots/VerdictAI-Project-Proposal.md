# VerdictAI — Multi-Agent Autonomous Dispute Resolution System

**Tencent Cloud x AI Singapore Hackathon 2026 — Digital Native Track (Ryde)**

---

## Project Name & Tagline

**VerdictAI** — *"Fair AI justice for every Ryde dispute"*

---

## Problem We Solve

Ride-hailing platforms like Ryde process thousands of disputes daily — fare disputes, no-show cancellations, safety incidents, lost items. Today these are resolved by human customer service agents, creating three critical problems:

1. **Slow resolution (24–72 hours):** Riders and drivers wait days for a ruling. Frustration mounts, trust erodes, churn increases.
2. **Inconsistent rulings:** Different CS agents interpret policies differently. The same dispute can yield opposite verdicts depending on who handles it.
3. **High operational cost:** Large CS teams are expensive to scale. As rider/driver counts grow, dispute volume scales faster than CS headcount.

**The gap:** No ride-hailing platform uses AI to autonomously resolve disputes with adversarial representation for both parties and transparent, policy-grounded verdicts.

---

## Solution Overview

VerdictAI deploys a **multi-agent adversarial system** where each party gets a dedicated AI advocate that builds their case, and a neutral AI judge renders a verdict with full reasoning. Think of it as a **mini digital courtroom** — resolving disputes in minutes, not days.

---

## Core Architecture — 3 Agents + 1 Orchestrator

### Agent 1: Rider Advocate Agent

**Role:** Represents the rider's interest — the rider's "AI attorney."

**Responsibilities:**

- Conducts a structured interview with the rider via in-app chat
- Collects and validates rider-side evidence: GPS trail, fare receipt, chat history with driver, trip recording timestamps
- Cross-references rider claims against system data (e.g., actual GPS route vs. expected route)
- Builds a structured Case Brief: claim summary, evidence list, policy citations, recommended outcome from rider's perspective

### Agent 2: Driver Advocate Agent

**Role:** Represents the driver's interest — the driver's "AI attorney."

**Responsibilities:**

- Conducts a structured interview with the driver via in-app chat
- Collects and validates driver-side evidence: assigned route, trip logs, earnings breakdown, navigation app data, dashcam metadata
- Cross-references driver claims against system data
- Builds a structured Case Brief: claim summary, evidence list, policy citations, recommended outcome from driver's perspective

### Agent 3: Judge Agent (Adjudicator)

**Role:** Neutral arbiter. Weighs both case briefs against evidence and policy.

**Responsibilities:**

- Reviews both advocates' case briefs simultaneously
- Identifies areas of agreement and contradiction between the two briefs
- Cross-checks evidence claims against raw system data (GPS, timestamps, fares)
- Retrieves relevant policies from the policy vector database (Ryde policies + Singapore regulations)
- Renders a structured verdict: liable party, recommended action, confidence score (0–100%), and full reasoning chain
- Auto-escalates to human CS when confidence falls below threshold (e.g., < 70%)

### Supporting: Case Orchestrator (Coordinator)

**Role:** Lightweight router — not a full LLM agent. Classifies dispute type, creates the case, triggers both advocates in parallel, then triggers the judge when both briefs are ready. Implemented as a simple LangGraph state machine.

---

## How It Works — Step by Step

### Step 1: Dispute Triggered

A rider or driver taps "File a Dispute" in the Ryde app after a completed trip. They select a dispute category and provide a free-text description.

### Step 2: Case Orchestrator Classifies & Routes

The orchestrator:

- Classifies the dispute type (fare/route, cancellation/no-show, etc.)
- Creates a case ID and pulls the trip record from the database
- Launches Rider Advocate and Driver Advocate agents **in parallel**

### Step 3: Advocates Collect Evidence (Parallel Execution)

Both advocates run simultaneously:

**Rider Advocate Agent:**

- Sends a structured chat prompt to the rider: "Tell me what happened. Did the driver take a different route than expected?"
- Pulls rider-side data: GPS trail, fare breakdown, timestamps, in-trip chat
- Cross-references rider's claim against data (e.g., GPS shows actual route vs. expected route)
- Builds a **Case Brief** with: claim summary, evidence list, policy citations, recommended outcome from rider's perspective

**Driver Advocate Agent:**

- Sends a structured chat prompt to the driver: "What happened during this trip? Did the rider change the destination?"
- Pulls driver-side data: assigned route, trip logs, earnings, navigation app data
- Cross-references driver's claim against data
- Builds a **Case Brief** with: claim summary, evidence list, policy citations, recommended outcome from driver's perspective

### Step 4: Judge Agent Reviews Both Briefs

The Judge Agent:

- Receives both Case Briefs simultaneously
- Identifies areas of agreement and contradiction
- Cross-checks evidence claims (e.g., does GPS data support rider's claim about route deviation?)
- Retrieves relevant policies from the policy vector database
- Evaluates each side's arguments against evidence and policy
- Calculates a **confidence score** (0–100%)

### Step 5: Verdict Rendered

The Judge Agent outputs a structured verdict:

- **Liable party:** Rider / Driver / Neither (system error)
- **Recommended action:** Full refund, partial refund, warning, account flag, escalation to human
- **Confidence score:** If below threshold (e.g., < 70%), automatically escalate to human CS
- **Reasoning chain:** Step-by-step explanation citing specific evidence and policy rules
- **Appeal option:** Either party can request a human review within 48 hours

### Step 6: Verdict Delivered

Both parties receive the verdict in-app with:

- The ruling and recommended action
- A plain-language explanation of the reasoning
- The confidence level (with escalation note if applicable)
- Option to appeal for human review

---

## MVP Dispute Types (2 for Hackathon)

### Dispute Type 1: Fare / Route Dispute

**Scenario:** Rider claims the driver took a longer route to inflate the fare. Driver claims they followed GPS or the rider requested a route change.

**Evidence sources:**

| Party  | Evidence                                                         |
| ------ | ---------------------------------------------------------------- |
| Rider  | Expected fare estimate, GPS trail, in-trip chat                  |
| Driver | Navigation app route, trip log, assigned route                   |
| System | Actual distance traveled vs. estimated distance, time comparison |

**Key policies checked:**

- Ryde fare policy (detour thresholds, acceptable deviation)
- LTA regulations on point-to-point transport
- Consumer Protection (Fair Trading) Act — unfair practices

### Dispute Type 2: Cancellation / No-Show Dispute

**Scenario:** Rider claims driver didn't show up at pickup. Driver claims rider wasn't at the pickup location.

**Evidence sources:**

| Party  | Evidence                                                                     |
| ------ | ---------------------------------------------------------------------------- |
| Rider  | Arrival timestamp, waiting time, location at cancellation                    |
| Driver | Arrival timestamp, GPS at pickup point, waiting time log, call/chat attempts |
| System | GPS proximity at cancellation, time window analysis, cancellation fee logic  |

**Key policies checked:**

- Ryde cancellation policy (who initiated, wait time thresholds)
- LTA point-to-point transport rules
- Fair cancellation fee guidelines

---

## Tech Stack

### AI / Agent Layer

| Component           | Technology                 | Why                                                                         |
| ------------------- | -------------------------- | --------------------------------------------------------------------------- |
| LLM                 | **Tencent Cloud Hunyuan**  | Powerful LLM, aligned with hackathon sponsor ecosystem                      |
| Agent orchestration | **LangGraph** (Python)     | First-class multi-agent stateful workflows, native parallel agent execution |
| Policy retrieval    | **Tencent Cloud VectorDB** | Store Ryde policies + SG regulations as embeddings for semantic retrieval   |
| Evidence storage    | **Tencent Cloud COS**      | Object storage for screenshots, dashcam metadata, receipts                  |

### Backend

| Component     | Technology                                | Why                                                         |
| ------------- | ----------------------------------------- | ----------------------------------------------------------- |
| API server    | **FastAPI** (Python)                      | Async, fast, pairs naturally with LangGraph                 |
| Database      | **PostgreSQL** (or Tencent Cloud TDSQL-C) | ACID for case records, trip data, verdicts                  |
| Session/state | **Redis**                                 | Agent conversation state, caching, pub/sub for live updates |

### Frontend

| Component   | Technology                  | Why                                                  |
| ----------- | --------------------------- | ---------------------------------------------------- |
| Web demo UI | **React + Next.js**         | Rapid UI for demo chat interface and verdict display |
| Real-time   | **WebSocket** (via FastAPI) | Live agent status updates to user                    |

### Deployment

| Component | Technology                                    | Why                                    |
| --------- | --------------------------------------------- | -------------------------------------- |
| Compute   | **Tencent Cloud CVM** or **SCF (Serverless)** | Containerized or serverless deployment |
| Domain    | Tencent Cloud domain + SSL                    | Production-ready demo URL              |

### Data Flow

```
Ryde App
  → FastAPI API
    → LangGraph Orchestrator
      ├→ Rider Advocate (LLM + VectorDB + COS)  ┐
      └→ Driver Advocate (LLM + VectorDB + COS) ┤
                                               ↓
                                         Judge Agent
                                               ↓
                                     Verdict → PostgreSQL
                                               ↓
                                     WebSocket → React UI
```

---

## What Makes It Innovative

### 1. Adversarial Multi-Agent Design

Unlike single-LLM "ask the AI" systems, VerdictAI gives **both parties dedicated AI advocates**. This mirrors real legal systems where each side has representation, ensuring the verdict considers both perspectives — not just whoever filed first.

### 2. Transparent Reasoning Chains

Every verdict comes with a **human-readable reasoning chain** that cites specific evidence and policy clauses. Users can see exactly *why* the AI decided what it did — building trust through transparency.

### 3. Confidence-Gated Human Escalation

The Judge Agent calculates a **confidence score**. Low-confidence cases auto-escalate to human CS, meaning humans only handle genuinely ambiguous cases. This is AI-augmented CS, not AI-replaced CS.

### 4. Policy-Grounded, Not LLM-Hallucinated

Verdicts are checked against a **vector database of real Ryde policies and Singapore regulations**. The LLM cannot invent rules — it retrieves and cites actual policy documents. Every claim in a verdict traces back to a specific policy clause.


### 5. Speed + Consistency

Resolves disputes in **minutes** (vs. 24–72h today) with **consistent policy application** (same rules every time, no inter-agent variance). Reduces CS cost while improving user satisfaction.

---

## 1-Day Build Plan (Hackathon Schedule)

| Time     | Task                                                                                                      |
| -------- | --------------------------------------------------------------------------------------------------------- |
| Hour 1   | Set up FastAPI scaffold, LangGraph agent graph, VectorDB with 5–6 sample Ryde policies                    |
| Hour 2–3 | Build Rider Advocate Agent: interview prompt template + evidence collection logic + case brief generation |
| Hour 3–4 | Build Driver Advocate Agent (mirror of Rider Advocate with driver-specific data sources)                  |
| Hour 4–5 | Build Judge Agent: brief review + policy retrieval + verdict generation + confidence scoring              |
| Hour 5–6 | Wire all agents into LangGraph graph, test end-to-end with mock dispute data                              |
| Hour 6–7 | Build React chat UI: dispute filing form, live agent status, verdict display                              |
| Hour 7–8 | Deploy to Tencent Cloud, prepare 2 demo scenarios (fare dispute + cancellation dispute), polish UI        |
| Hour 8   | Final demo run + buffer for debugging                                                                     |

---

## Alignment with Handbook Requirements

- Uses Tencent Cloud services (Hunyuan, VectorDB, COS, CVM/SCF)
- AI Singapore track: multi-agent system applied to Singapore transport regulations
- Digital Native: transforms a manual CS process into an autonomous AI system
- Ryde-relevant: solves a real ride-hailing pain point with real impact
- Buildable in 1 day: focused MVP with 2 dispute types, mock data for evidence sources

---

## Sample Verdict Output (Demo)

```json
{
  "case_id": "RYDE-DSPT-20261015-0042",
  "dispute_type": "fare_route_dispute",
  "verdict": {
    "liable_party": "driver",
    "recommended_action": "partial_refund",
    "refund_amount": 4.50,
    "confidence_score": 82,
    "escalate_to_human": false
  },
  "reasoning_chain": [
    "Rider claims driver took a longer route via Bukit Timah Road instead of the direct PIE route.",
    "GPS data confirms actual route was 3.2km longer than the estimated route.",
    "Driver claims rider requested the route change, but in-trip chat shows no such request.",
    "Ryde Fare Policy Section 4.2 states: drivers must follow the assigned route unless the rider explicitly requests a change.",
    "LTA Point-to-Point Transport Rules require fare transparency — deviations without rider consent are classified as overcharging.",
    "Conclusion: Driver is liable for the fare difference. Partial refund of $4.50 recommended."
  ],
  "appeal_available": true,
  "appeal_window_hours": 48
}
```

---

## Key Design Decisions

| Decision                                         | Rationale                                                                                                                |
| ------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------ |
| LangGraph over AutoGen/CrewAI                    | LangGraph has native parallel agent execution and state management — essential for running both advocates simultaneously |
| VectorDB for policies instead of prompt-stuffing | Policies are long and contextual; semantic retrieval gets the right clause without bloating context windows              |
| Confidence-gated escalation                      | Builds trust with users (humans handle hard cases) and with Ryde (AI doesn't replace CS, it augments it)                 |
| Mock evidence data for MVP                       | Real Ryde API integration isn't possible at a hackathon; mock trip data lets us demonstrate the full pipeline            |
| 2 dispute types only                             | Keeps the build achievable in 1 day while covering the two most common real-world scenarios                              |
