"""
config.py — Configuration for VerdictAI.

Separates all policy thresholds, constants, and tunable parameters from
the core agent logic so they can be adjusted without touching code.

Import anywhere:
    from config import RYDE_POLICY, LLM_CONFIG, APP_CONFIG
"""

# ---------------------------------------------------------------------------
# Ryde Dispute Resolution Policy
# ---------------------------------------------------------------------------
# These thresholds drive the Judge agent's decisions (both LLM and fallback).
RYDE_POLICY = {
    # --- Route Deviation Rule ---
    # If actual distance exceeds estimated by more than threshold_pct,
    # the rider is entitled to a refund of the fare difference
    # (unless a valid reason is documented).
    "route_deviation": {
        "threshold_pct": 20,        # % over estimated distance
        "action": "partial_refund",  # refund the fare difference
        "valid_reasons": [
            "road_closure",
            "heavy_congestion",
            "rider_requested_detour",
            "safety_incident",
        ],
    },

    # --- No-Show Cancellation Rule ---
    # The no-show fee is waived if the rider arrived at the pickup point
    # within grace_period_mins of the driver's arrival time.
    # The driver must wait at least grace_period_mins before declaring no-show.
    "no_show": {
        "grace_period_mins": 5,   # driver must wait this long
        "action": "waive_fee",   # refund / waive the cancellation fee
    },

    # --- Escalation ---
    # Disputes with a confidence score below this threshold are escalated
    # to a human reviewer.
    "escalation_threshold": 70,  # 0-100 confidence score
}

# ---------------------------------------------------------------------------
# CrewAI / LLM Configuration
# ---------------------------------------------------------------------------
LLM_CONFIG = {
    # Set your provider & model here.
    # Example values shown — uncomment and adjust for your environment.
    #
    # "provider": "openai",
    # "model": "gpt-4o-mini",
    # "temperature": 0.3,
    # "api_key_env": "OPENAI_API_KEY",  # reads from environment variable

    # If no API key is set, the app falls back to the deterministic
    # rule-based engine in app.py (_mock_results).
    "fallback_enabled": True,
    "max_tokens": 500,
    "verbose": True,
}

# ---------------------------------------------------------------------------
# Agent Configuration
# ---------------------------------------------------------------------------
AGENT_CONFIG = {
    "rider_advocate": {
        "role": "Rider Advocate",
        "goal": (
            "Build the strongest possible case for the rider based on the "
            "dispute data. Highlight evidence that supports the rider's "
            "claim, including GPS data, chat logs, timestamps, and fare "
            "discrepancies."
        ),
        "backstory": (
            "You are a seasoned consumer-rights advocate specializing in "
            "ride-hailing disputes. You fight for fair treatment of riders."
        ),
        "max_words": 300,
    },
    "driver_advocate": {
        "role": "Driver Advocate",
        "goal": (
            "Build the strongest possible defence for the driver based on "
            "the dispute data. Highlight evidence that justifies the "
            "driver's actions, including routing decisions, wait times, "
            "call attempts, and policy compliance."
        ),
        "backstory": (
            "You are a legal advocate for ride-hailing drivers. You ensure "
            "drivers are treated fairly and their side of the story is heard."
        ),
        "max_words": 300,
    },
    "judge": {
        "role": "Judge Agent",
        "goal": (
            "Review both the rider's and driver's arguments, apply the "
            "Ryde Dispute Resolution Policy, and deliver a clear, fair "
            "verdict with reasoning and a refund recommendation."
        ),
        "backstory": (
            "You are an impartial adjudicator trained on the Ryde platform's "
            "policies. You weigh evidence objectively and produce structured "
            "verdicts."
        ),
        "output_format": (
            "VERDICT: [UPHOLD_RIDER_CLAIM | DENY_RIDER_CLAIM | PARTIAL]\n"
            "REASONING: [2-4 sentences explaining the decision]\n"
            "POLICY_APPLIED: [name the specific rule used]\n"
            "REFUND_AMOUNT: [number or 0]\n"
            "REFUND_CURRENCY: [currency code]"
        ),
    },
}

# ---------------------------------------------------------------------------
# App / Streamlit Configuration
# ---------------------------------------------------------------------------
APP_CONFIG = {
    "title": "⚖️ VerdictAI — Multi-Agent Dispute Court",
    "subtitle": "Rider Advocate vs. Driver Advocate — Judge delivers the verdict.",
    "page_icon": "⚖️",
    "layout": "wide",
}

# ---------------------------------------------------------------------------
# Verdict display mapping (for UI color-coding)
# ---------------------------------------------------------------------------
VERDICT_STYLES = {
    "UPHOLD_RIDER_CLAIM": {"color": "error",   "icon": "🔴", "label": "Rider claim upheld — refund awarded."},
    "DENY_RIDER_CLAIM":   {"color": "success", "icon": "🟢", "label": "Rider claim denied — no refund."},
    "PARTIAL":            {"color": "warning", "icon": "🟡", "label": "Partial resolution."},
}

if __name__ == "__main__":
    import json
    print("RYDE_POLICY:")
    print(json.dumps(RYDE_POLICY, indent=2, ensure_ascii=False))
    print("\nLLM_CONFIG:")
    print(json.dumps(LLM_CONFIG, indent=2, ensure_ascii=False))

