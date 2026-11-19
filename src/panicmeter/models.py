from dataclasses import dataclass, field, asdict
from typing import List


@dataclass
class Snapshot:
    t: float      # seconds since session start
    text: str     # full file content at that moment


@dataclass
class Signals:
    snapshots: int = 0
    rewrites: int = 0          # lines replaced (written, then rewritten)
    reverts: int = 0           # file jumped back to an older version (undo loops)
    debug_added: int = 0       # print()/breakpoint()/pdb/logging.debug lines added
    debug_removed: int = 0     # ...and then deleted again
    freezes: int = 0           # long idle gaps mid-session
    error_snapshots: int = 0   # snapshots that did not even compile
    max_error_streak: int = 0  # longest run of broken snapshots
    chars_added: int = 0
    chars_deleted: int = 0
    duration_s: float = 0.0

    def as_dict(self):
        return asdict(self)


@dataclass
class Report:
    score: float
    level: str
    signals: Signals
    curve: List[float] = field(default_factory=list)
    integrity_ok: bool = True
