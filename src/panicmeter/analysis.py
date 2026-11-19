"""Turn a list of file snapshots into behavioral signals."""
import difflib
import re
from typing import List
from .models import Snapshot, Signals

DEBUG_RE = re.compile(
    r"^\s*(print\s*\(|breakpoint\s*\(|import\s+pdb|pdb\.set_trace|"
    r"logging\.debug|#\s*(debug|test|\?+))", re.I)


def _is_debug(line: str) -> bool:
    return bool(DEBUG_RE.match(line))


def _compiles(text: str) -> bool:
    try:
        compile(text, "<exam>", "exec")
        return True
    except (SyntaxError, ValueError):
        return False


def extract_signals(snaps: List[Snapshot], freeze_s: float = 120.0) -> Signals:
    s = Signals(snapshots=len(snaps))
    if not snaps:
        return s
    s.duration_s = snaps[-1].t - snaps[0].t
    seen = {snaps[0].text}
    streak = 0

    for i, snap in enumerate(snaps):
        # --- compile state / error streaks
        if _compiles(snap.text):
            streak = 0
        else:
            s.error_snapshots += 1
            streak += 1
            s.max_error_streak = max(s.max_error_streak, streak)
        if i == 0:
            continue
        prev = snaps[i - 1]

        # --- freezes: long silence between edits
        if snap.t - prev.t >= freeze_s:
            s.freezes += 1

        # --- reverts: returning to a version seen before (not the previous one)
        if snap.text in seen and snap.text != prev.text:
            s.reverts += 1
        seen.add(snap.text)

        # --- line-level diff
        a, b = prev.text.splitlines(), snap.text.splitlines()
        for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
            old, new = a[i1:i2], b[j1:j2]
            if tag == "replace":
                s.rewrites += min(len(old), len(new))
            if tag in ("delete", "replace"):
                s.chars_deleted += sum(len(x) for x in old)
                s.debug_removed += sum(_is_debug(x) for x in old)
            if tag in ("insert", "replace"):
                s.chars_added += sum(len(x) for x in new)
                s.debug_added += sum(_is_debug(x) for x in new)
    return s
