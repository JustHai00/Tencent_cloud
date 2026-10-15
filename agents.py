"""
agents.py — Local Ollama-powered agents for VerdictAI (hackathon project).

Three agents collaborate to resolve ride-hailing disputes:
  1) Rider Advocate  — builds the rider's case from mock data.
  2) Driver Advocate — builds the driver's defence from mock data.
  3) Judge Agent     — reviews both arguments, applies Ryde policy, outputs a verdict.

Ryde Policy:
  • Route Deviation: Refund if actual distance > 20% above estimated with no valid reason.
  • No-Show:         Waive fee if rider arrived within 5 mins of pickup time.

Usage:
    python agents.py                # runs both sample disputes automatically
    python agents.py VRD-2026-00104 # runs a single dispute by case_id
"""

from __future__ import annotations

import json
import os
import re
import sys
import textwrap
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from config import LLM_CONFIG
from mock_data import SAMPLE_DISPUTES, format_money, get_dispute_by_id


# ---------------------------------------------------------------------------
# Ryde Policy (embedded so the Judge can reference it explicitly)
# ---------------------------------------------------------------------------
RYDE_POLICY = """
Ryde Dispute Resolution Policy:

1. Route Deviation Rule
   - If the actual trip distance exceeds the estimated distance by MORE THAN 20%,
     AND no valid reason (e.g. road closures, heavy congestion, rider-requested detour)
     is documented, the rider is entitled to a refund of the fare difference
     between estimated and actual fare.

2. No-Show Cancellation Rule
   - The cancellation / no-show fee is waived if the rider arrived at the pickup
     point within 5 minutes of the driver's arrival time.
   - "Arrived" is determined by: rider chat timestamp, rider GPS, or photo evidence.
   - The driver must have waited at least 5 minutes before declaring a no-show.
""".strip()

CONFIDENCE_ESCALATION_THRESHOLD = 70
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", LLM_CONFIG["ollama_host"]).rstrip("/")
OLLAMA_MODEL = os.environ.get("VERDICTAI_OLLAMA_MODEL", LLM_CONFIG["ollama_model"])


def apply_confidence_escalation(verdict_text: str) -> tuple[str, int, bool]:
    """Normalize the judge's confidence and enforce the human-escalation threshold."""
    confidence_match = re.search(
        r"(?im)^CONFIDENCE:\s*(?:Based on evidence[:,]?\s*)?"
        r"(\d{1,3})\s*%?(?:\s+confident)?\s*$",
        verdict_text,
    )
    if confidence_match is None:
        raise ValueError("Judge verdict must include a numeric CONFIDENCE from 0 to 100.")

    confidence = int(confidence_match.group(1))
    if confidence > 100:
        raise ValueError(f"Judge confidence must be between 0 and 100, got {confidence}.")

    escalated = confidence < CONFIDENCE_ESCALATION_THRESHOLD
    confidence_line = f"CONFIDENCE: Based on evidence: {confidence}% confident"
    escalation_line = (
        "ESCALATION: Escalated to human support"
        if escalated
        else "ESCALATION: Not required"
    )

    verdict_text = re.sub(
        r"(?im)^CONFIDENCE:.*$",
        confidence_line,
        verdict_text,
        count=1,
    )
    if re.search(r"(?im)^ESCALATION:", verdict_text):
        verdict_text = re.sub(
            r"(?im)^ESCALATION:.*$",
            escalation_line,
            verdict_text,
            count=1,
        )
    else:
        verdict_text = f"{verdict_text.rstrip()}\n{escalation_line}"

    return verdict_text, confidence, escalated


# ---------------------------------------------------------------------------
# Helper: format dispute data into a readable string for the LLM
# ---------------------------------------------------------------------------
def format_dispute(d: dict) -> str:
    """Flatten the dispute dict into a human / LLM-readable text block."""
    lines = [
        f"Case ID:      {d['case_id']}",
        f"Dispute Type: {d['type']}",
        f"City:         {d['trip']['city']}",
        f"",
        f"Rider:  {d['rider']['name']} (id={d['rider']['user_id']}, rating={d['rider']['rating']})",
        f"Driver: {d['driver']['name']} (id={d['driver']['user_id']}, rating={d['driver']['rating']})",
        f"",
        f"--- Trip ---",
        f"Pickup:   {d['trip']['pickup']['label']} ({d['trip']['pickup']['lat']}, {d['trip']['pickup']['lng']})",
        f"Dropoff:  {d['trip']['dropoff']['label']} ({d['trip']['dropoff']['lat']}, {d['trip']['dropoff']['lng']})",
        f"Request time:     {d['trip']['request_time']}",
        f"Pickup time:       {d['trip'].get('pickup_time', 'N/A')}",
        f"Dropoff time:      {d['trip'].get('dropoff_time', 'N/A')}",
        f"Driver arrived:    {d['trip'].get('driver_arrived_time', 'N/A')}",
        f"Driver left:       {d['trip'].get('driver_left_time', 'N/A')}",
        f"Pickup window end: {d['trip'].get('pickup_window_end', 'N/A')}",
        f"Actual distance:    {d['trip']['actual_distance_km']} km",
        f"Expected distance:  {d['trip']['expected_distance_km']} km",
        f"",
        f"--- Fare ---",
        f"Currency:        {d['fare']['currency']}",
        f"Estimated fare:  {format_money(d['fare']['estimated_fare'], d['fare']['currency'])}",
        f"Actual fare:     {format_money(d['fare']['actual_fare'], d['fare']['currency'])}",
        f"Cancellation fee:{format_money(d['fare'].get('cancellation_fee', 0.0), d['fare']['currency'])}",
        f"Paid amount:     {format_money(d['fare']['paid_amount'], d['fare']['currency'])}",
        f"",
        f"--- Rider Claim ---",
        f"Reason: {d['claim']['reason']}",
        f"Requested refund: {format_money(d['claim']['requested_refund'], d['fare']['currency'])}",
    ]
    for note in d["claim"].get("evidence_notes", []):
        lines.append(f"  Evidence: {note}")

    lines.append("")
    lines.append("--- Driver Response ---")
    lines.append(f"Statement: {d['driver_response']['statement']}")
    for note in d["driver_response"].get("evidence_notes", []):
        lines.append(f"  Evidence: {note}")

    lines.append("")
    lines.append("--- Chat Log ---")
    for msg in d.get("chat_log", []):
        lines.append(f"  [{msg['ts']}] {msg['sender']}: {msg['text']}")

    lines.append("")
    lines.append("--- GPS Breadcrumbs ---")
    for pt in d.get("gps_breadcrumbs", []):
        lines.append(f"  {pt['ts']}  lat={pt['lat']} lng={pt['lng']} speed={pt['speed_kmh']} km/h")

    if d.get("call_attempts"):
        lines.append("")
        lines.append("--- Call Attempts ---")
        for call in d["call_attempts"]:
            lines.append(f"  {call['ts']}  caller={call['caller']}  "
                         f"duration={call['duration_sec']}s  status={call['status']}")

    return "\n".join(lines)


def _ollama_chat(prompt: str) -> str:
    """Send a prompt to the local Ollama server and return its response text."""
    payload = json.dumps(
        {
            "model": OLLAMA_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
            "options": {"temperature": 0.2},
        }
    ).encode("utf-8")
    request = Request(
        f"{OLLAMA_HOST}/api/chat",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urlopen(request, timeout=300) as response:
            result = json.loads(response.read().decode("utf-8"))
    except HTTPError as error:
        details = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(
            f"Ollama returned HTTP {error.code}: {details or error.reason}"
        ) from error
    except URLError as error:
        raise RuntimeError(
            f"Cannot connect to Ollama at {OLLAMA_HOST}. Start Ollama and ensure "
            f"the {OLLAMA_MODEL!r} model is installed."
        ) from error
    except json.JSONDecodeError as error:
        raise RuntimeError("Ollama returned an invalid JSON response.") from error

    content = result.get("message", {}).get("content")
    if not isinstance(content, str) or not content.strip():
        raise RuntimeError("Ollama returned an empty response.")
    return content.strip()


# ---------------------------------------------------------------------------
# Run a single dispute through the crew
# ---------------------------------------------------------------------------
def run_dispute(dispute: dict) -> str:
    """Run the local three-role deliberation and return the judge's verdict."""
    return run_dispute_detailed(dispute)["verdict"]


def run_dispute_detailed(dispute: dict) -> dict:
    """Run the three agent roles with a local Ollama model.

    Returns a dict with keys: 'rider_case', 'driver_case', 'verdict'.
    Each value is the raw string output from that task.
    """
    dispute_text = format_dispute(dispute)
    rider_case = _ollama_chat(
        "You are the Rider Advocate in a fair dispute review. Make the strongest "
        "evidence-based case for the rider. Cite relevant details from the dispute. "
        "Do not invent evidence. Keep your argument concise.\n\n"
        f"Dispute data:\n{dispute_text}"
    )
    driver_case = _ollama_chat(
        "You are the Driver Advocate in a fair dispute review. Make the strongest "
        "evidence-based defence for the driver. Cite relevant details from the "
        "dispute. Do not invent evidence. Keep your argument concise.\n\n"
        f"Dispute data:\n{dispute_text}"
    )
    verdict_text = _ollama_chat(
        "You are the neutral Judge. Review the dispute data and both advocates' "
        "arguments, then apply the policy. Base confidence on evidence completeness, "
        "reliability, and contradictions; it is an evidence estimate, not a statistical "
        "probability. For CNY amounts, the dispute data includes an approximate SGD "
        "equivalent for reference; base the verdict and refund on the original trip "
        "currency. Do not invent facts. Return exactly these fields, each on its "
        "own line:\n"
        "VERDICT: [UPHOLD_RIDER_CLAIM | DENY_RIDER_CLAIM | PARTIAL]\n"
        "REASONING: [2-4 concise sentences]\n"
        "POLICY_APPLIED: [policy rule]\n"
        "REFUND_AMOUNT: [number or 0]\n"
        "REFUND_CURRENCY: [currency code]\n"
        "CONFIDENCE: [integer from 0 to 100]\n\n"
        f"Policy:\n{RYDE_POLICY}\n\n"
        f"Dispute data:\n{dispute_text}\n\n"
        f"Rider Advocate:\n{rider_case}\n\n"
        f"Driver Advocate:\n{driver_case}"
    )
    verdict, confidence, escalated = apply_confidence_escalation(verdict_text)
    return {
        "rider_case": rider_case,
        "driver_case": driver_case,
        "verdict": verdict,
        "confidence": confidence,
        "escalated": escalated,
        "engine": f"Ollama local model ({OLLAMA_MODEL})",
    }


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------
def main():
    # Pick dispute(s) — accept an optional case_id from CLI
    if len(sys.argv) > 1:
        case_id = sys.argv[1]
        disputes = [get_dispute_by_id(case_id)]
    else:
        disputes = SAMPLE_DISPUTES

    for d in disputes:
        print("=" * 72)
        print(f"  CASE: {d['case_id']}  |  TYPE: {d['type']}")
        print("=" * 72)

        verdict = run_dispute(d)

        print("\n" + "-" * 72)
        print("  JUDGE'S VERDICT")
        print("-" * 72)
        print(textwrap.indent(verdict, "  "))
        print("\n")


if __name__ == "__main__":
    main()
