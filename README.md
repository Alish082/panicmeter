# panicmeter
Measures stress/panic from *real* coding behavior and records it in a tamper-evident log.

    pip install -e .
    panicmeter watch exam.py --out panic_log.jsonl   # run during the exam
    panicmeter report panic_log.jsonl                # score, signals, panic curve

Signals: rewritten lines, reverts, debug-print add/delete thrashing, freezes, broken-code streaks, write/delete churn.
Behavioral indicators only - not a medical diagnosis. Pair with a doctor/counselor note.
