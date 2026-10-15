# ⚖️ VerdictAI
## Multi-Agent Autonomous Dispute Resolution System
**Tencent Cloud x AI Singapore Hackathon 2026 — Digital Native Track (Ryde)**
> Fair AI justice for every Ryde dispute

---

## 📌 Overview
VerdictAI demonstrates ride-dispute review with three AI roles: a rider advocate, a driver advocate, and a neutral judge. It runs a local Ollama model, so live deliberation does not require a paid cloud API or API key. Verdicts below **70% confidence** are flagged for human support.

## 🧠 How It Works
```
Dispute → Rider Advocate ─┐
                           ↓
                         Judge → Verdict + Confidence
                           ↑
Dispute → Driver Advocate ─┘
```

### 3 Core Agents
| Agent | Role |
|---|---|
| **Rider Advocate** | Builds the rider's case from evidence |
| **Driver Advocate** | Builds the driver's defence |
| **Judge Agent** | Reviews both, applies Ryde policy, delivers verdict |

### MVP Dispute Types
1. **Route / Fare Deviation** — Refund if >20% above estimated distance with no rider consent
2. **No-Show Cancellation** — Waive fee if rider arrived within 5-minute grace period

### Sample cases and currencies
- Two fictional China cases use **CNY**. Their fare and refund amounts also show an approximate Singapore-dollar equivalent using a fixed demo conversion of **1 CNY ≈ S$0.19**.
- A third fictional case uses Singapore locations and **SGD** directly.
- The conversion is for demonstration only; it is not a live exchange rate.

## 🚀 How to Run
1. Install [Ollama for Windows](https://ollama.com/download) and start the Ollama app.
2. Download the local model once:

   ```powershell
   ollama pull qwen2.5:3b
   ```

3. In PowerShell, from this project folder, install the app dependency and start Streamlit:

   ```powershell
   python -m pip install -r requirements.txt
   python -m streamlit run app.py
   ```

4. Open http://localhost:8501.

The model download requires an internet connection and disk space. After setup, inference runs on your computer without a paid AI API. Performance depends on your computer; the first response may take longer while the model loads. If Ollama is unavailable, the app identifies that it used its deterministic offline fallback.