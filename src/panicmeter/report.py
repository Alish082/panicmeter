import json
from .models import Report
from .analysis import extract_signals
from .scoring import score, level, timeline
from .recorder import load_log, verify_log
from .authenticity import check_authenticity

BARS = "▁▂▃▄▅▆▇█"


def build_report(log_path: str) -> Report:
    snaps = load_log(log_path)
    sig = extract_signals(snaps)
    s = score(sig)
    return Report(s, level(s), sig, timeline(snaps), verify_log(log_path), check_authenticity(snaps))


def _spark(vals, width=50):
    if not vals:
        return ""
    step = max(1, len(vals) // width)
    vals = vals[::step]
    return "".join(BARS[min(7, int(v / 100 * 8))] for v in vals)


def render_text(r: Report) -> str:
    g = r.signals
    m = int(g.duration_s // 60)
    au = r.authenticity
    au_txt = ""
    if au is not None:
        au_txt = f"Authenticity : {au.trust:.0f}/100 ({au.verdict})\n"
        for fl in au.flags:
            au_txt += f"  ! {fl}\n"
        if au.trust < 40:
            au_txt += "  WARNING: score above is NOT reliable - session looks staged.\n"
    return f"""PANICMETER REPORT
=================
Panic score : {r.score}/100  ({r.level})
Log integrity: {"VERIFIED (hash chain intact)" if r.integrity_ok else "BROKEN - log was modified!"}
{au_txt}Session     : {m} min, {g.snapshots} snapshots

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
    au = r.authenticity
    return json.dumps({"score": r.score, "level": r.level, "integrity_ok": r.integrity_ok,
                       "authenticity": None if au is None else {"trust": au.trust, "verdict": au.verdict, "flags": au.flags},
                       "signals": r.signals.as_dict(), "curve": r.curve}, indent=2)
