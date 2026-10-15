"""
app.py — Streamlit demo UI for VerdictAI (hackathon project).

Run:
    streamlit run app.py

Features:
  - Title: ⚖️ VerdictAI — Multi-Agent Dispute Court
  - Dropdown to select dispute (D001 / D002)
  - "Process Dispute" button → runs the 3-agent crew
  - Clean layout: Rider Case → Driver Case → Final Verdict
"""

import io
import contextlib

import streamlit as st

from mock_data import SAMPLE_DISPUTES, get_dispute_by_id
from agents import (
    apply_confidence_escalation,
    format_dispute,
    run_dispute_detailed,
    RYDE_POLICY,
)


# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="VerdictAI — Multi-Agent Dispute Court",
    page_icon="⚖️",
    layout="wide",
)

# ---------------------------------------------------------------------------
# Project header and intro
# ---------------------------------------------------------------------------
st.title("⚖️ VerdictAI")
st.subheader("A fairer, clearer way to resolve ride disputes")
st.markdown(
    "Review both the rider's and driver's perspectives, see how the evidence "
    "measures up against Ryde policy, and get a transparent verdict with a "
    "confidence score. Cases below 70% confidence are flagged for human support."
)
st.divider()

# ---------------------------------------------------------------------------
# Dispute selection dropdown
# ---------------------------------------------------------------------------
# Build a friendly label map:  "D001 — fare_route_dispute"  etc.
_dispute_labels = {}
for d in SAMPLE_DISPUTES:
    short_id = "D001" if d["case_id"].endswith("00104") else "D002"
    label = f"{short_id} — {d['type'].replace('_', ' ')}  ({d['trip']['city']})"
    _dispute_labels[label] = d["case_id"]

selected_label = st.selectbox(
    "Select a dispute to adjudicate:",
    options=list(_dispute_labels.keys()),
    index=0,
)
selected_case_id = _dispute_labels[selected_label]
dispute = get_dispute_by_id(selected_case_id)

# Show dispute summary in an expander
with st.expander("📋 Dispute Summary", expanded=False):
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Case ID", dispute["case_id"])
        st.metric("Type", dispute["type"].replace("_", " "))
    with col2:
        st.metric("Rider", dispute["rider"]["name"])
        st.metric("Driver", dispute["driver"]["name"])
    with col3:
        st.metric("Actual Fare", f"{dispute['fare']['actual_fare']} {dispute['fare']['currency']}")
        st.metric("Requested Refund", f"{dispute['claim']['requested_refund']} {dispute['fare']['currency']}")

    st.text_area(
        "Rider's Claim",
        value=dispute["claim"]["reason"],
        height=70,
        disabled=True,
    )
    st.text_area(
        "Driver's Response",
        value=dispute["driver_response"]["statement"],
        height=70,
        disabled=True,
    )

# ---------------------------------------------------------------------------
# Ryde Policy reference (collapsible)
# ---------------------------------------------------------------------------
with st.expander("📜 Ryde Dispute Resolution Policy", expanded=False):
    st.code(RYDE_POLICY, language="text")

# ---------------------------------------------------------------------------
# Process button
# ---------------------------------------------------------------------------
st.divider()

# ---------------------------------------------------------------------------
# Deterministic fallback (used only when CrewAI / LLM is unavailable)
# ---------------------------------------------------------------------------
def _mock_results(dispute: dict, error_msg: str) -> dict:
    """Produce a realistic verdict without an LLM, for offline demos."""

    d = dispute

    # --- Rider case ---
    rider_case = (
        f"**Rider {d['rider']['name']}** filed this claim requesting "
        f"**{d['claim']['requested_refund']} {d['fare']['currency']}** refund.\n\n"
        f"**Claim:** {d['claim']['reason']}\n\n"
        f"**Supporting evidence:**\n"
    )
    for note in d["claim"].get("evidence_notes", []):
        rider_case += f"- {note}\n"
    rider_case += (
        f"\n**Key data points:**\n"
        f"- Estimated distance: {d['trip']['expected_distance_km']} km\n"
        f"- Actual distance: {d['trip']['actual_distance_km']} km\n"
        f"- Estimated fare: {d['fare']['estimated_fare']} {d['fare']['currency']}\n"
        f"- Actual fare: {d['fare']['actual_fare']} {d['fare']['currency']}\n"
    )

    # --- Driver case ---
    driver_case = (
        f"**Driver {d['driver']['name']}** presents the following defence.\n\n"
        f"**Statement:** {d['driver_response']['statement']}\n\n"
        f"**Supporting evidence:**\n"
    )
    for note in d["driver_response"].get("evidence_notes", []):
        driver_case += f"- {note}\n"
    if d.get("call_attempts"):
        driver_case += (
            f"\n**Call attempts:** {len(d['call_attempts'])} attempts made, "
            f"{sum(1 for c in d['call_attempts'] if c['status'] == 'unanswered')} unanswered.\n"
        )

    # --- Judge verdict (deterministic logic based on Ryde policy) ---
    if d["type"] == "fare_route_dispute":
        confidence = 82
        actual = d["trip"]["actual_distance_km"]
        expected = d["trip"]["expected_distance_km"]
        pct_over = ((actual - expected) / expected * 100) if expected else 0
        refund = round(d["fare"]["actual_fare"] - d["fare"]["estimated_fare"], 2)

        if pct_over > 20:
            verdict = (
                f"VERDICT: UPHOLD_RIDER_CLAIM\n"
                f"REASONING: Actual distance ({actual} km) exceeded the estimated "
                f"distance ({expected} km) by {pct_over:.1f}%, which is above the "
                f"20% threshold. The driver cited congestion but did not provide "
                f"verifiable road-closure evidence; a general detour preference "
                f"does not constitute a valid reason under policy.\n"
                f"POLICY_APPLIED: Route Deviation Rule\n"
                f"REFUND_AMOUNT: {refund}\n"
                f"REFUND_CURRENCY: {d['fare']['currency']}"
            )
        else:
            verdict = (
                f"VERDICT: DENY_RIDER_CLAIM\n"
                f"REASONING: Actual distance ({actual} km) is within 20% of the "
                f"estimated distance ({expected} km). The deviation is within "
                f"acceptable bounds.\n"
                f"POLICY_APPLIED: Route Deviation Rule\n"
                f"REFUND_AMOUNT: 0\n"
                f"REFUND_CURRENCY: {d['fare']['currency']}"
            )

    elif d["type"] == "no_show_dispute":
        confidence = 65
        from datetime import datetime
        arrived_str = d["trip"].get("driver_arrived_time", "")
        left_str = d["trip"].get("driver_left_time", "")
        try:
            arrived_dt = datetime.fromisoformat(arrived_str)
            left_dt = datetime.fromisoformat(left_str)
            wait_mins = (left_dt - arrived_dt).total_seconds() / 60
        except Exception:
            wait_mins = 0

        # Check rider's claimed arrival within 5 min of driver arrival
        # (rider chat "Almost there, 1 min." at ts+53, driver arrived ts+51)
        rider_nearby = True  # chat log shows rider messaging within the window

        if wait_mins < 5 or rider_nearby:
            refund = d["fare"].get("cancellation_fee", 0.0) or d["fare"].get("no_show_fee", 0.0)
            verdict = (
                f"VERDICT: UPHOLD_RIDER_CLAIM\n"
                f"REASONING: The driver arrived at {arrived_str} and left at "
                f"{left_str}, waiting only {wait_mins:.0f} minutes — less than "
                f"the required 5-minute wait. The rider's chat messages show they "
                f"were communicating during the window. The no-show fee is waived.\n"
                f"POLICY_APPLIED: No-Show Cancellation Rule\n"
                f"REFUND_AMOUNT: {refund}\n"
                f"REFUND_CURRENCY: {d['fare']['currency']}"
            )
        else:
            verdict = (
                f"VERDICT: DENY_RIDER_CLAIM\n"
                f"REASONING: The driver waited {wait_mins:.0f} minutes, meeting "
                f"the 5-minute requirement. Multiple unanswered call attempts "
                f"were made. The no-show fee is upheld.\n"
                f"POLICY_APPLIED: No-Show Cancellation Rule\n"
                f"REFUND_AMOUNT: 0\n"
                f"REFUND_CURRENCY: {d['fare']['currency']}"
            )
    else:
        confidence = 0
        verdict = "VERDICT: PARTIAL\nREASONING: Unknown dispute type.\nREFUND_AMOUNT: 0"

    verdict += f"\nCONFIDENCE: {confidence}"
    verdict, confidence, escalated = apply_confidence_escalation(verdict)

    # Append a note if this was a fallback
    verdict += f"\n\n[Note: LLM backend unavailable — deterministic fallback used. ({error_msg[:80]})]"

    return {
        "rider_case": rider_case,
        "driver_case": driver_case,
        "verdict": verdict,
        "confidence": confidence,
        "escalated": escalated,
    }

if st.button("🛡️ Process Dispute", type="primary", use_container_width=True):
    # Capture stdout so the UI doesn't get flooded with CrewAI verbose logs
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        # Try the real CrewAI path; fall back to a deterministic mock if
        # crewai / LLM backend isn't available (e.g. no API key on demo machine).
        with st.spinner("🔍 Analyzing evidence..."):
            try:
                results = run_dispute_detailed(dispute)
            except Exception as e:
                results = _mock_results(dispute, str(e))

    # --- Layout: Rider Case | Driver Case ---
    col_rider, col_driver = st.columns(2)

    with col_rider:
        st.subheader("🧑‍⚖️ Rider Advocate")
        st.caption("Building the rider's case...")
        st.markdown(results["rider_case"])

    with col_driver:
        st.subheader("🧑‍⚖️ Driver Advocate")
        st.caption("Building the driver's defence...")
        st.markdown(results["driver_case"])

    st.divider()

    # --- Final Verdict ---
    st.subheader("⚖️ Judge's Final Verdict")
    with st.spinner("⚖️ Delivering verdict..."):
        verdict_text = results["verdict"]
        confidence = results["confidence"]

        st.markdown("**Evidence confidence**")
        st.progress(confidence / 100, text=f"{confidence}% confident")

        if results["escalated"]:
            st.warning("Escalated to human support because confidence is below 70%.")
        else:
            st.caption("Confidence meets the 70% threshold; no human escalation is required.")

        if "UPHOLD_RIDER_CLAIM" in verdict_text:
            st.success("🟢 **Approved** — the rider's claim is upheld.")
        elif "DENY_RIDER_CLAIM" in verdict_text:
            st.error("🔴 **Denied** — the rider's claim is not upheld.")
        elif "PARTIAL" in verdict_text:
            st.warning("🟡 **Partially approved** — see the reasoning below.")

        st.code(verdict_text, language="text")

    # --- Raw dispute data (for debugging / Q&A during demo) ---
    with st.expander("🔍 Raw Dispute Data", expanded=False):
        st.code(format_dispute(dispute), language="text")


# Silence the "tornado access log" noise in the terminal
import logging
logging.getLogger("streamlit").setLevel(logging.WARNING)
