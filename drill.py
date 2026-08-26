#!/usr/bin/env python3
"""60-minute drill runner.

  python drill.py list                 # list problems
  python drill.py show q01             # print the problem statement (read ALL parts first!)
  python drill.py start q01 [-m 60]    # print statement, reset starter.py from template, start timer file
  python drill.py test q01 [-k part1]  # run the test-suite against YOUR problems/q01/starter.py
  python drill.py ref q01              # run the test-suite against the reference solution.py
  python drill.py time q01             # how much of the 60 minutes is left
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PROBLEMS = ROOT / "problems"


def _dir(q: str) -> Path:
    matches = sorted(PROBLEMS.glob(f"{q}*"))
    if not matches:
        sys.exit(f"no problem matching {q!r}; try `python drill.py list`")
    if len(matches) > 1:
        sys.exit(f"ambiguous {q!r}: {[m.name for m in matches]}")
    return matches[0]


def cmd_list(_):
    for d in sorted(PROBLEMS.iterdir()):
        if d.is_dir() and (d / "problem.md").exists():
            first = (d / "problem.md").read_text().splitlines()[0].lstrip("# ").strip()
            print(f"{d.name:32s} {first}")


def cmd_show(a):
    print((_dir(a.q) / "problem.md").read_text())


def cmd_start(a):
    d = _dir(a.q)
    tpl = d / "starter_template.py"
    if tpl.exists():
        shutil.copy(tpl, d / "starter.py")
    (d / ".drill.json").write_text(json.dumps({"t0": time.time(), "minutes": a.minutes}))
    print((d / "problem.md").read_text())
    print("\n" + "=" * 70)
    print(f"Timer started: {a.minutes} minutes. Edit {d / 'starter.py'} and run: python drill.py test {d.name}")


def cmd_time(a):
    d = _dir(a.q)
    f = d / ".drill.json"
    if not f.exists():
        sys.exit("no timer; run `python drill.py start ...` first")
    st = json.loads(f.read_text())
    left = st["minutes"] * 60 - (time.time() - st["t0"])
    print(f"{int(left // 60):02d}:{int(left % 60):02d} left" if left > 0 else "TIME IS UP")


def _pytest(d: Path, which: str, extra: list[str]):
    env = dict(os.environ, IMPL=which)
    cmd = [sys.executable, "-m", "pytest", str(d), "-q", "-p", "no:cacheprovider", "--no-header", "-rN", *extra]
    return subprocess.call(cmd, cwd=str(ROOT), env=env)


def cmd_test(a):
    d = _dir(a.q)
    extra = ["-k", a.k] if a.k else []
    rc = _pytest(d, "starter", extra)
    f = d / ".drill.json"
    if f.exists():
        cmd_time(a)
    sys.exit(rc)


def cmd_ref(a):
    d = _dir(a.q)
    sys.exit(_pytest(d, "solution", ["-k", a.k] if a.k else []))


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list").set_defaults(fn=cmd_list)
    s = sub.add_parser("show"); s.add_argument("q"); s.set_defaults(fn=cmd_show)
    s = sub.add_parser("start"); s.add_argument("q"); s.add_argument("-m", "--minutes", type=int, default=60); s.set_defaults(fn=cmd_start)
    s = sub.add_parser("time"); s.add_argument("q"); s.set_defaults(fn=cmd_time)
    s = sub.add_parser("test"); s.add_argument("q"); s.add_argument("-k", default=None); s.set_defaults(fn=cmd_test)
    s = sub.add_parser("ref"); s.add_argument("q"); s.add_argument("-k", default=None); s.set_defaults(fn=cmd_ref)
    a = p.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
