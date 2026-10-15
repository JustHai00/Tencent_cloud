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

## 📁 Project structure
```text
Hackerton Project/
├── agents.py          # Local Ollama calls, advocate prompts, and verdict confidence handling
├── app.py             # Streamlit interface and deterministic offline fallback
├── config.py          # Policy and local model configuration
├── mock_data.py       # Sample disputes, currencies, and display formatting
├── requirements.txt   # Python dependencies
├── test_verdictai.py  # Project tests
├── README.md          # Setup and usage guide
└── screenshots/       # Hackathon proposal and demo materials
```

## 📦 Install dependencies
1. Install Python, then open PowerShell in the project folder.
2. (Recommended) Create and activate a virtual environment:

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

3. Install the Python packages:

   ```powershell
   python -m pip install -r requirements.txt
   ```

`requirements.txt` installs Streamlit. Ollama is a separate application required for live local AI; it is not installed by pip. For the deterministic offline demo, you can skip the Ollama setup.

## 🚀 Run the app
1. For live local AI, install [Ollama for Windows](https://ollama.com/download), start the Ollama app, and download the model once:

   ```powershell
   ollama pull qwen2.5:3b
   ```

2. From the project folder, run:

   ```powershell
   python -m streamlit run app.py
   ```

3. Open http://localhost:8501.

The model download requires an internet connection and disk space. After setup, inference runs on your computer without a paid AI API. Performance depends on your computer; the first response may take longer while the model loads. If Ollama is unavailable, the app identifies that it used its deterministic offline fallback.

## ➕ Add a dispute type
1. In `mock_data.py`, create a dispute dictionary following the existing cases. Include a unique `case_id`, a `type`, trip details, fare currency and amounts, rider claim, driver response, and relevant evidence.
2. Add the dictionary to `SAMPLE_DISPUTES`. The Streamlit dispute selector picks it up automatically.
3. In `app.py`, add deterministic verdict logic for the new `type` inside `_mock_results()`. The live judge receives the dispute data automatically, but add or update the rules in `agents.py`'s `RYDE_POLICY` and judge prompt if the new type needs its own policy.
4. Keep refund amounts in the case's original currency and include that currency in the verdict. For CNY examples, the UI also displays the fixed approximate SGD conversion; SGD cases display SGD directly.
5. Run the app and process the new case to verify the summary, both arguments, verdict, confidence, and escalation display.