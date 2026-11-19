"""Panic score 0-100. Each signal saturates smoothly so no single one dominates."""
import math
from typing import List
from .models import Snapshot, Signals
from .analysis import extract_signals

# name -> (weight, scale k): contribution = weight * (1 - exp(-x/k))
WEIGHTS = {
    "rewrites":      (25, 12),
    "reverts":       (20, 5),
    "debug_thrash":  (20, 10),
    "freezes":       (12, 3),
    "error_streak":  (13, 6),
    "churn":         (10, 1.0),
}


def _sat(x: float, k: float) -> float:
    return 1 - math.exp(-max(x, 0) / k)


def score(sig: Signals) -> float:
    debug_thrash = sig.debug_added * 0.5 + sig.debug_removed  # add-then-delete is the tell
    total_edit = max(1, sig.chars_added)
    churn = sig.chars_deleted / total_edit  # deleting as much as you write
    xs = {
        "rewrites": sig.rewrites,
        "reverts": sig.reverts,
        "debug_thrash": debug_thrash,
        "freezes": sig.freezes,
        "error_streak": sig.max_error_streak,
        "churn": churn,
    }
    return round(sum(w * _sat(xs[n], k) for n, (w, k) in WEIGHTS.items()), 1)


def level(x: float) -> str:
    for limit, name in [(20, "calm"), (40, "nervous"), (60, "stressed"), (80, "panic")]:
        if x < limit:
            return name
    return "severe panic"


def timeline(snaps: List[Snapshot], step: int = 1) -> List[float]:
    """Cumulative score after each snapshot: shows panic *escalating*."""
    return [score(extract_signals(snaps[: i + 1])) for i in range(0, len(snaps), step)]
