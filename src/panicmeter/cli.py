import argparse
from .recorder import Recorder
from .report import build_report, render_text, to_json


def main(argv=None):
    p = argparse.ArgumentParser(prog="panicmeter")
    sub = p.add_subparsers(dest="cmd", required=True)
    w = sub.add_parser("watch", help="record a file while you work")
    w.add_argument("file"); w.add_argument("--out", default="panic_log.jsonl")
    w.add_argument("--interval", type=float, default=1.0)
    r = sub.add_parser("report", help="analyze a recorded log")
    r.add_argument("log"); r.add_argument("--json", action="store_true")
    a = p.parse_args(argv)
    if a.cmd == "watch":
        Recorder(a.file, a.out).watch(a.interval)
    else:
        rep = build_report(a.log)
        print(to_json(rep) if a.json else render_text(rep))


if __name__ == "__main__":
    main()
