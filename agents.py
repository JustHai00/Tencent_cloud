"""
agents.py — Core CrewAI agents for VerdictAI (hackathon project).

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

import re
import sys
import textwrap
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from crewai import Agent, Task

from mock_data import SAMPLE_DISPUTES, get_dispute_by_id


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
        f"Estimated fare:  {d['fare']['estimated_fare']}",
        f"Actual fare:     {d['fare']['actual_fare']}",
        f"Cancellation fee:{d['fare'].get('cancellation_fee', 0.0)}",
        f"Paid amount:     {d['fare']['paid_amount']}",
        f"",
        f"--- Rider Claim ---",
        f"Reason: {d['claim']['reason']}",
        f"Requested refund: {d['claim']['requested_refund']}",
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


def _build_agents() -> tuple[Agent, Agent, Agent]:
    from crewai import Agent

    rider_advocate = Agent(
        role="Rider Advocate",
        goal=(
            "Build the strongest possible case for the rider based on the dispute "
            "data. Highlight evidence that supports the rider's claim, including "
            "GPS data, chat logs, timestamps, and fare discrepancies."
        ),
        backstory=(
            "You are a seasoned consumer-rights advocate specializing in "
            "ride-hailing disputes. You fight for fair treatment of riders."
        ),
        verbose=True,
        allow_delegation=False,
    )

    driver_advocate = Agent(
        role="Driver Advocate",
        goal=(
            "Build the strongest possible defence for the driver based on the "
            "dispute data. Highlight evidence that justifies the driver's actions, "
            "including routing decisions, wait times, call attempts, and policy compliance."
        ),
        backstory=(
            "You are a legal advocate for ride-hailing drivers. You ensure drivers "
            "are treated fairly and their side of the story is heard."
        ),
        verbose=True,
        allow_delegation=False,
    )

    judge = Agent(
        role="Judge Agent",
        goal=(
            "Review both the rider's and driver's arguments, apply the Ryde "
            "Dispute Resolution Policy, and deliver a clear, fair verdict with "
            "reasoning and a refund recommendation."
        ),
        backstory=(
            "You are an impartial adjudicator trained on the Ryde platform's "
            "policies. You weigh evidence objectively and produce structured verdicts."
        ),
        verbose=True,
        allow_delegation=False,
    )
    return rider_advocate, driver_advocate, judge


# ---------------------------------------------------------------------------
# Task builder — creates the 3 tasks for a given dispute
# ---------------------------------------------------------------------------
def build_tasks(dispute: dict) -> list[Task]:
    return _build_tasks(dispute)[0]


def _build_tasks(dispute: dict) -> tuple[list[Task], tuple[Agent, Agent, Agent]]:
    from crewai import Task

    rider_advocate, driver_advocate, judge = _build_agents()
    dispute_text = format_dispute(dispute)

    task_rider = Task(
        description=(
            "You are representing the RIDER in this ride-hailing dispute.\n\n"
            "Here is the full dispute data:\n\n"
            f"{dispute_text}\n\n"
            "Build the rider's case. Be specific: cite GPS points, chat "
            "timestamps, fare numbers, and any policy that supports the rider. "
            "Output a concise argument (under 300 words)."
        ),
        agent=rider_advocate,
        expected_output="A concise argument supporting the rider's claim.",
    )

    task_driver = Task(
        description=(
            "You are representing the DRIVER in this ride-hailing dispute.\n\n"
            "Here is the full dispute data:\n\n"
            f"{dispute_text}\n\n"
            "Build the driver's defence. Be specific: cite GPS points, chat "
            "timestamps, call attempts, and any justification for the driver's "
            "actions. Output a concise argument (under 300 words)."
        ),
        agent=driver_advocate,
        expected_output="A concise argument supporting the driver's defence.",
    )

    task_judge = Task(
        description=(
            "You are the JUDGE. Review the rider's argument and the driver's "
            "defence, then apply the Ryde Dispute Resolution Policy below.\n\n"
            f"{RYDE_POLICY}\n\n"
            "Dispute data for reference:\n\n"
            f"{dispute_text}\n\n"
            "Produce your verdict in this EXACT format:\n\n"
            "VERDICT: [UPHOLD_RIDER_CLAIM | DENY_RIDER_CLAIM | PARTIAL]\n"
            "REASONING: [2-4 sentences explaining the decision]\n"
            "POLICY_APPLIED: [name the specific rule used]\n"
            "REFUND_AMOUNT: [number or 0]\n"
            "REFUND_CURRENCY: [currency code]\n"
            "CONFIDENCE: [integer from 0 to 100, based on evidence completeness, "
            "reliability, and contradictions]"
        ),
        agent=judge,
        expected_output=(
            "A structured verdict with: VERDICT, REASONING, "
            "POLICY_APPLIED, REFUND_AMOUNT, REFUND_CURRENCY, and CONFIDENCE."
        ),
        context=[task_rider, task_driver],  # judge sees both advocates' outputs
    )

    return [task_rider, task_driver, task_judge], (rider_advocate, driver_advocate, judge)


# ---------------------------------------------------------------------------
# Run a single dispute through the crew
# ---------------------------------------------------------------------------
def run_dispute(dispute: dict) -> str:
    """Kick off a 3-agent crew for one dispute; return the judge's verdict."""
    from crewai import Crew, Process

    tasks, agents = _build_tasks(dispute)

    crew = Crew(
        agents=list(agents),
        tasks=tasks,
        process=Process.sequential,   # rider → driver → judge (in order)
        verbose=True,
    )

    result = crew.kickoff()
    # CrewAI returns a CrewOutput; .raw or str() gives the final task's output
    verdict, _, _ = apply_confidence_escalation(str(result))
    return verdict


def run_dispute_detailed(dispute: dict) -> dict:
    """Run the crew and return each agent's output separately.

    Returns a dict with keys: 'rider_case', 'driver_case', 'verdict'.
    Each value is the raw string output from that task.
    """
    from crewai import Crew, Process

    tasks, agents = _build_tasks(dispute)

    crew = Crew(
        agents=list(agents),
        tasks=tasks,
        process=Process.sequential,
        verbose=True,
    )

    crew.kickoff()

    # After execution, each Task object has .output (TaskOutput) with .raw
    def _extract(task) -> str:
        out = getattr(task, "output", None)
        if out is None:
            return ""
        return getattr(out, "raw", None) or str(out)

    verdict, confidence, escalated = apply_confidence_escalation(_extract(tasks[2]))
    return {
        "rider_case": _extract(tasks[0]),
        "driver_case": _extract(tasks[1]),
        "verdict": verdict,
        "confidence": confidence,
        "escalated": escalated,
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
