import os, tempfile, json
from panicmeter import Snapshot, extract_signals, score, level, Recorder, verify_log, build_report, render_text

CALM = [Snapshot(0, "x = 1\n"), Snapshot(30, "x = 1\ny = 2\n"), Snapshot(60, "x = 1\ny = 2\nprint(x+y)\n")]

PANIC = [Snapshot(0, "def f(a):\n    return a\n")]
for i in range(12):
    t = 20 * (i + 1) + (200 if i == 6 else 0)
    body = ["def f(a):", f"    return a + {i}", "    print('here', a)" if i % 2 == 0 else "    return a * ("]
    PANIC.append(Snapshot(t, "\n".join(body) + "\n"))
PANIC.append(Snapshot(400, "def f(a):\n    return a\n"))  # revert

def test_calm_lower_than_panic():
    assert score(extract_signals(CALM)) < score(extract_signals(PANIC))
    assert level(score(extract_signals(CALM))) in ("calm", "nervous")

def test_signals_detected():
    s = extract_signals(PANIC)
    assert s.rewrites > 0 and s.reverts >= 1 and s.freezes >= 1 and s.debug_added > 0
    assert s.max_error_streak >= 1

def test_log_integrity_and_tamper():
    d = tempfile.mkdtemp(); p = os.path.join(d, "log.jsonl")
    rec = Recorder("x.py", p)
    for sn in PANIC: rec.snap(sn.text, sn.t)
    assert verify_log(p)
    rep = build_report(p); assert rep.integrity_ok and "PANICMETER" in render_text(rep)
    lines = open(p).read().splitlines(); r = json.loads(lines[3]); r["text"] += "#fake"
    lines[3] = json.dumps(r); open(p, "w").write("\n".join(lines) + "\n")
    assert not verify_log(p)
