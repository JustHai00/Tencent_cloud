# ⚖️ VerdictAI
## Multi-Agent Autonomous Dispute Resolution System
**Tencent Cloud x AI Singapore Hackathon 2026 — Digital Native Track (Ryde)**
> Fair AI justice for every Ryde dispute

---

## 📌 Overview
VerdictAI transforms Ryde's manual dispute resolution (24–72 hours) into an autonomous multi-agent system that resolves cases in **3–5 minutes**. Two dedicated advocates represent the rider and driver, then a neutral Judge Agent renders a policy-grounded verdict with confidence scoring. Low-confidence cases auto-escalate to human support.

## 🧠 How It Works
Dispute → Rider Advocate ─┐
                           ↓
                         Judge → Verdict + Confidence
                           ↑
Dispute → Driver Advocate ─┘


### 3 Core Agents
| Agent | Role |
|---|---|
| **Rider Advocate** | Builds the rider's case from evidence |
| **Driver Advocate** | Builds the driver's defence |
| **Judge Agent** | Reviews both, applies Ryde policy, delivers verdict |

### MVP Dispute Types
1. **Route / Fare Deviation** — Refund if >20% above estimated distance with no rider consent
2. **No-Show Cancellation** — Waive fee if rider arrived within 5-minute grace period

## 🚀 How to Run
```bash
pip install streamlit
streamlit run app.py

Then open: http://localhost:8501