import json
from .models import Report
from .analysis import extract_signals
from .scoring import score, level, timeline
from .recorder import load_log, verify_log

BARS = "▁▂▃▄▅▆▇█"


def build_report(log_path: str) -> Report:
    snaps = load_log(log_path)
    sig = extract_signals(snaps)
    s = score(sig)
    return Report(s, level(s), sig, timeline(snaps), verify_log(log_path))


def _spark(vals, width=50):
    if not vals:
        return ""
    step = max(1, len(vals) // width)
    vals = vals[::step]
    return "".join(BARS[min(7, int(v / 100 * 8))] for v in vals)


def render_text(r: Report) -> str:
    g = r.signals
    m = int(g.duration_s // 60)
    return f"""PANICMETER REPORT
=================
Panic score : {r.score}/100  ({r.level})
Log integrity: {"VERIFIED (hash chain intact)" if r.integrity_ok else "BROKEN - log was modified!"}
Session     : {m} min, {g.snapshots} snapshots

Behavioral evidence
  Lines rewritten after writing : {g.rewrites}
  Reverts to older versions     : {g.reverts}
  Debug prints added / removed  : {g.debug_added} / {g.debug_removed}
  Freezes (long idle gaps)      : {g.freezes}
  Non-compiling snapshots       : {g.error_snapshots} (longest streak {g.max_error_streak})
  Chars written / deleted       : {g.chars_added} / {g.chars_deleted}

Panic over time (cumulative):
  {_spark(r.curve)}

Note: behavioral indicators only. Not a medical diagnosis.
"""


def to_json(r: Report) -> str:
    return json.dumps({"score": r.score, "level": r.level, "integrity_ok": r.integrity_ok,
                       "signals": r.signals.as_dict(), "curve": r.curve}, indent=2)
