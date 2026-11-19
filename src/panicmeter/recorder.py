"""Records real snapshots to a tamper-evident log (SHA-256 hash chain)."""
import hashlib
import json
import os
import time
from typing import List
from .models import Snapshot


def _h(prev: str, t: float, text: str) -> str:
    return hashlib.sha256(f"{prev}|{t}|{text}".encode()).hexdigest()


class Recorder:
    def __init__(self, target: str, log: str = "panic_log.jsonl"):
        self.target, self.log = target, log
        self.t0 = time.time()
        self.prev_hash = "GENESIS"
        self.last_text = None

    def snap(self, text: str, t: float = None):
        if text == self.last_text:
            return
        t = round(time.time() - self.t0 if t is None else t, 2)
        h = _h(self.prev_hash, t, text)
        with open(self.log, "a", encoding="utf-8") as f:
            f.write(json.dumps({"t": t, "text": text, "prev": self.prev_hash, "hash": h}) + "\n")
        self.prev_hash, self.last_text = h, text

    def watch(self, interval: float = 1.0):
        print(f"Watching {self.target} -> {self.log} (Ctrl+C to stop)")
        try:
            while True:
                if os.path.exists(self.target):
                    with open(self.target, encoding="utf-8", errors="replace") as f:
                        self.snap(f.read())
                time.sleep(interval)
        except KeyboardInterrupt:
            print("Stopped.")


def load_log(path: str) -> List[Snapshot]:
    with open(path, encoding="utf-8") as f:
        return [Snapshot(r["t"], r["text"]) for r in map(json.loads, f if True else [])]


def verify_log(path: str) -> bool:
    """False if any entry was edited, removed or reordered after recording."""
    prev = "GENESIS"
    with open(path, encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            if r["prev"] != prev or r["hash"] != _h(prev, r["t"], r["text"]):
                return False
            prev = r["hash"]
    return True
