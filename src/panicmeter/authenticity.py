"""Anti-gaming checks: does the session look like natural behavior or a staged one?

Heuristics only. They flag suspicious patterns, they cannot prove anything.
"""
import difflib
import statistics
from collections import Counter
from dataclasses import dataclass, field
from typing import List
from .models import Snapshot
from .analysis import DEBUG_RE


@dataclass
class Authenticity:
    trust: float = 100.0
    flags: List[str] = field(default_factory=list)

    @property
    def verdict(self) -> str:
        if self.trust >= 70:
            return "consistent with natural behavior"
        if self.trust >= 40:
            return "SUSPICIOUS"
        return "LIKELY STAGED"


def check_authenticity(snaps: List[Snapshot]) -> Authenticity:
    a = Authenticity()
    n = len(snaps)
    if n < 6:
        a.flags.append("too few snapshots to judge")
        a.trust = 60.0
        return a
    penalty = 0
    gaps = [snaps[i].t - snaps[i - 1].t for i in range(1, n)]

    # 1. time must move forward
    if any(g < 0 for g in gaps):
        penalty += 40
        a.flags.append("timestamps go backwards")

    # 2. robotic timing: humans are irregular
    pos = [g for g in gaps if g > 0]
    if len(pos) >= 5 and statistics.mean(pos) > 0:
        cv = statistics.pstdev(pos) / statistics.mean(pos)
        if cv < 0.15:
            penalty += 30
            a.flags.append(f"robotic timing (edit intervals almost identical, variation {cv:.0%})")

    # 3. superhuman speed
    fast = sum(1 for g in gaps if 0 <= g < 0.5) / len(gaps)
    if fast > 0.3:
        penalty += 25
        a.flags.append("many edits faster than 0.5 s apart (script or macro?)")

    # 4. bulk paste of large blocks in a very short time
    pastes = 0
    for i in range(1, n):
        grown = len(snaps[i].text) - len(snaps[i - 1].text)
        if grown > 400 and snaps[i].t - snaps[i - 1].t < 3:
            pastes += 1
    if pastes >= 2:
        penalty += 20
        a.flags.append(f"{pastes} large instant pastes")

    # 5. looping between the same few versions
    distinct = len({s.text for s in snaps})
    if n >= 8 and distinct / n < 0.4:
        penalty += 30
        a.flags.append(f"only {distinct} distinct versions in {n} snapshots (looping)")

    # 6. the same edit repeated mechanically + 7. edits that are only debug noise
    diffs, debug_changes, all_changes = [], 0, 0
    for i in range(1, n):
        x, y = snaps[i - 1].text.splitlines(), snaps[i].text.splitlines()
        added, removed = [], []
        for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, x, y, autojunk=False).get_opcodes():
            if tag != "equal":
                removed += x[i1:i2]
                added += y[j1:j2]
        diffs.append((tuple(added), tuple(removed)))
        for line in added + removed:
            all_changes += 1
            debug_changes += bool(DEBUG_RE.match(line))
    common, count = Counter(d for d in diffs if d != ((), ())).most_common(1)[0] if any(
        d != ((), ()) for d in diffs) else (None, 0)
    if count >= 4 and count / len(diffs) >= 0.4:
        penalty += 25
        a.flags.append(f"the same edit repeated {count} times")
    if debug_changes >= 10 and all_changes and debug_changes / all_changes > 0.8:
        penalty += 25
        a.flags.append("almost all edits are debug prints (no real coding work)")

    a.trust = float(max(0, 100 - penalty))
    return a
