"""
mock_data.py — Sample dispute data for VerdictAI hackathon project.

Contains two realistic ride-hailing dispute cases stored as Python dictionaries:
  1) fare_route_dispute — rider claims the driver took a longer route to overcharge.
  2) no_show_dispute    — rider disputes a cancellation / no-show fee.

All values are fictional but realistic. Import this module directly:

    from mock_data import SAMPLE_DISPUTES, get_dispute_by_id

Sample monetary amounts are shown in SGD, converted from CNY at an approximate
rate of 0.19 SGD per CNY.
"""

from datetime import datetime, timedelta


# ---------------------------------------------------------------------------
# Helper: build ISO-8601 timestamps around a base time for readability
# ---------------------------------------------------------------------------
_BASE_TIME = datetime(2026, 10, 15, 9, 0, 0)  # 09:00 local


def _ts(minutes: int) -> str:
    """Return an ISO-8601 string offset from _BASE_TIME by `minutes`."""
    return (_BASE_TIME + timedelta(minutes=minutes)).isoformat()


# ===========================================================================
# Dispute 1 — fare_route_dispute
# Rider claims driver intentionally took a longer route, inflating the fare.
# ===========================================================================
fare_route_dispute = {
    # ---- identification ----
    "case_id": "VRD-2026-00104",
    "type": "fare_route_dispute",
    "status": "open",
    "priority": "medium",
    "filed_at": _ts(95),

    # ---- parties ----
    "rider": {
        "user_id": "RDR-78432",
        "name": "Chen Wei",
        "phone": "+86-138-0013-8888",
        "rating": 4.82,
        "rides_total": 214,
    },
    "driver": {
        "user_id": "DRV-12907",
        "name": "Zhang Lei",
        "phone": "+86-139-0066-2233",
        "rating": 4.61,
        "rides_total": 3402,
        "vehicle": {
            "plate": "Beijing·A2X9F7",
            "model": "BYD Qin Plus EV",
            "color": "white",
        },
    },

    # ---- trip metadata ----
    "trip": {
        "trip_id": "TRP-556677",
        "city": "Beijing",
        "pickup": {
            "label": "Zhongguancun Subway Station Exit C",
            "lat": 39.9832,
            "lng": 116.3168,
        },
        "dropoff": {
            "label": "Beijing South Railway Station (North Gate)",
            "lat": 39.8650,
            "lng": 116.3786,
        },
        "request_time": _ts(0),
        "pickup_time": _ts(8),
        "dropoff_time": _ts(55),
        "actual_distance_km": 17.8,   # actual (longer) route
        "expected_distance_km": 13.2, # shortest suggested route
    },

    # ---- fare breakdown ----
    "fare": {
        "currency": "SGD",
        "base_fare": 0.95,
        "per_km_rate": 0.44,
        "per_min_rate": 0.08,
        "estimated_fare": 6.72,
        "actual_fare": 9.30,       # charged amount
        "toll": 0.00,
        "surge_multiplier": 1.0,
        "paid_amount": 9.30,
        "payment_method": "credit_card",
    },

    # ---- rider's claim ----
    "claim": {
        "filed_by": "rider",
        "reason": "Driver took a significantly longer route (via Lianhuachi East Road) "
                  "instead of the GPS-suggested shortest path, inflating the fare by ~2.58 SGD.",
        "requested_refund": 2.58,
        "evidence_notes": [
            "Rider captured two screenshots of in-app navigation showing suggested route.",
            "Rider's phone GPS recorded a different path than the suggested route.",
        ],
    },

    # ---- driver's response ----
    "driver_response": {
        "statement": "Zhongguancun South Road had heavy congestion per the navigation app; "
                     "I detoured through Lianhuachi East Road to save time, which is a common alternative.",
        "evidence_notes": [
            "Driver's dashboard camera footage available (retention 7 days).",
        ],
    },

    # ---- GPS breadcrumbs (lat, lng, timestamp, speed_kmh) ----
    "gps_breadcrumbs": [
        {"lat": 39.9832, "lng": 116.3168, "ts": _ts(8),  "speed_kmh": 0.0},
        {"lat": 39.9801, "lng": 116.3210, "ts": _ts(10), "speed_kmh": 28.0},
        {"lat": 39.9768, "lng": 116.3275, "ts": _ts(12), "speed_kmh": 34.0},
        {"lat": 39.9710, "lng": 116.3352, "ts": _ts(15), "speed_kmh": 42.0},
        {"lat": 39.9640, "lng": 116.3410, "ts": _ts(18), "speed_kmh": 38.0},
        {"lat": 39.9550, "lng": 116.3460, "ts": _ts(21), "speed_kmh": 25.0},
        {"lat": 39.9440, "lng": 116.3520, "ts": _ts(25), "speed_kmh": 18.0},
        {"lat": 39.9320, "lng": 116.3580, "ts": _ts(29), "speed_kmh": 30.0},
        {"lat": 39.9180, "lng": 116.3640, "ts": _ts(33), "speed_kmh": 35.0},
        {"lat": 39.9030, "lng": 116.3700, "ts": _ts(37), "speed_kmh": 40.0},
        {"lat": 39.8880, "lng": 116.3740, "ts": _ts(41), "speed_kmh": 33.0},
        {"lat": 39.8760, "lng": 116.3770, "ts": _ts(45), "speed_kmh": 27.0},
        {"lat": 39.8650, "lng": 116.3786, "ts": _ts(55), "speed_kmh": 0.0},
    ],

    # ---- in-app chat log (timestamp, sender, text) ----
    "chat_log": [
        {"ts": _ts(0),  "sender": "rider",  "text": "I'm at Exit C, wearing a blue jacket."},
        {"ts": _ts(1),  "sender": "driver", "text": "Arriving in 3 min, white BYD."},
        {"ts": _ts(7),  "sender": "driver", "text": "Arrived, I see you."},
        {"ts": _ts(20), "sender": "rider",  "text": "Why are we going through Lianhuachi? "
                                                     "My map shows a shorter way."},
        {"ts": _ts(21), "sender": "driver", "text": "South Road is jammed, this is faster."},
        {"ts": _ts(56), "sender": "rider",  "text": "The fare is way higher than the estimate."},
        {"ts": _ts(57), "sender": "driver", "text": "It's by distance and time, nothing I can do."},
    ],
}


# ===========================================================================
# Dispute 2 — no_show_dispute
# Rider disputes the cancellation fee, claiming they arrived on time but the
# driver left and marked them as a no-show.
# ===========================================================================
no_show_dispute = {
    # ---- identification ----
    "case_id": "VRD-2026-00105",
    "type": "no_show_dispute",
    "status": "open",
    "priority": "high",
    "filed_at": _ts(120),

    # ---- parties ----
    "rider": {
        "user_id": "RDR-55031",
        "name": "Liu Yang",
        "phone": "+86-137-2255-1100",
        "rating": 4.91,
        "rides_total": 387,
    },
    "driver": {
        "user_id": "DRV-22841",
        "name": "Wang Bin",
        "phone": "+86-135-7788-9900",
        "rating": 4.35,
        "rides_total": 1180,
        "vehicle": {
            "plate": "Shanghai·F6T2K8",
            "model": "Geely Emgrand EV",
            "color": "silver",
        },
    },

    # ---- trip metadata ----
    "trip": {
        "trip_id": "TRP-889900",
        "city": "Shanghai",
        "pickup": {
            "label": "Shanghai Hongqiao Airport T2 — Ride-hail Pickup Point B",
            "lat": 31.1960,
            "lng": 121.3360,
        },
        "dropoff": {
            "label": "Jing'an Temple, Nanjing West Road",
            "lat": 31.2270,
            "lng": 121.4480,
        },
        "request_time": _ts(40),
        "pickup_window_start": _ts(50),   # driver arrived window opens
        "pickup_window_end": _ts(58),     # no-show can be declared after this
        "driver_arrived_time": _ts(51),
        "driver_left_time": _ts(56),      # driver left before the window expired
        "cancellation_time": _ts(56),
        "actual_distance_km": 0.0,        # trip never started
        "expected_distance_km": 18.5,
    },

    # ---- fare / fee breakdown ----
    "fare": {
        "currency": "SGD",
        "base_fare": 1.52,
        "per_km_rate": 0.48,
        "per_min_rate": 0.09,
        "estimated_fare": 7.56,
        "actual_fare": 0.00,              # trip didn't happen
        "cancellation_fee": 2.85,         # charged to rider
        "no_show_fee": 2.85,
        "paid_amount": 2.85,
        "payment_method": "alipay",
    },

    # ---- rider's claim ----
    "claim": {
        "filed_by": "rider",
        "reason": "I arrived at Pickup Point B at 09:53, within the grace period, "
                  "but the driver left at 09:56 and marked me as a no-show. "
                  "The 2.85 SGD cancellation fee is unjustified.",
        "requested_refund": 2.85,
        "evidence_notes": [
            "Boarding pass shows flight landed at 09:42.",
            "Rider has a timestamped photo of Pickup Point B taken at 09:53.",
        ],
    },

    # ---- driver's response ----
    "driver_response": {
        "statement": "I waited from 09:51 to 09:56. Could not reach the rider by phone; "
                     "passenger at the pickup point did not match the order. "
                     "I followed the no-show protocol.",
        "evidence_notes": [
            "Driver app log shows 5 call attempts between 09:52 and 09:56.",
        ],
    },

    # ---- GPS breadcrumbs (lat, lng, timestamp, speed_kmh) ----
    "gps_breadcrumbs": [
        {"lat": 31.1900, "lng": 121.3350, "ts": _ts(48), "speed_kmh": 30.0},
        {"lat": 31.1930, "lng": 121.3355, "ts": _ts(50), "speed_kmh": 15.0},
        {"lat": 31.1960, "lng": 121.3360, "ts": _ts(51), "speed_kmh": 0.0},   # arrived
        {"lat": 31.1960, "lng": 121.3360, "ts": _ts(53), "speed_kmh": 0.0},   # waiting
        {"lat": 31.1960, "lng": 121.3360, "ts": _ts(55), "speed_kmh": 0.0},   # still waiting
        {"lat": 31.1965, "lng": 121.3365, "ts": _ts(56), "speed_kmh": 12.0},  # departed
        {"lat": 31.1985, "lng": 121.3380, "ts": _ts(57), "speed_kmh": 28.0},
    ],

    # ---- in-app chat log ----
    "chat_log": [
        {"ts": _ts(40), "sender": "rider",  "text": "Just landed, heading to Pickup Point B."},
        {"ts": _ts(41), "sender": "driver", "text": "OK, I'll be at B in ~3 min, silver Geely."},
        {"ts": _ts(51), "sender": "driver", "text": "I'm here at Point B."},
        {"ts": _ts(53), "sender": "rider",  "text": "Almost there, 1 min."},
        {"ts": _ts(55), "sender": "driver", "text": "Can't see you, which side are you on?"},
        {"ts": _ts(57), "sender": "driver", "text": "I waited 5 min, had to leave. "
                                                      "Marked as no-show per policy."},
        {"ts": _ts(58), "sender": "rider",  "text": "I was right there! Why did you leave?"},
    ],

    # ---- phone call attempts (from driver) ----
    "call_attempts": [
        {"ts": _ts(52), "caller": "driver", "duration_sec": 0,  "status": "unanswered"},
        {"ts": _ts(53), "caller": "driver", "duration_sec": 0,  "status": "unanswered"},
        {"ts": _ts(54), "caller": "driver", "duration_sec": 3,  "status": "answered_then_dropped"},
        {"ts": _ts(55), "caller": "driver", "duration_sec": 0,  "status": "unanswered"},
        {"ts": _ts(56), "caller": "driver", "duration_sec": 0,  "status": "unanswered"},
    ],
}


# ===========================================================================
# Convenience exports
# ===========================================================================
SAMPLE_DISPUTES = [fare_route_dispute, no_show_dispute]


def get_dispute_by_id(case_id: str):
    """Return the dispute dict matching case_id, or raise KeyError."""
    for d in SAMPLE_DISPUTES:
        if d["case_id"] == case_id:
            return d
    raise KeyError(f"No dispute found with case_id={case_id!r}")


if __name__ == "__main__":
    # Quick sanity check — prints a summary so you can verify it runs.
    for d in SAMPLE_DISPUTES:
        print(f"[{d['case_id']}] {d['type']:20s}  "
              f"claim={d['claim']['requested_refund']} {d['fare']['currency']}  "
              f"filed_by={d['claim']['filed_by']}")
    print(f"\nTotal sample disputes: {len(SAMPLE_DISPUTES)}")
