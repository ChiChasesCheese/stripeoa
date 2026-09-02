"""ps01 Transaction Stream Levels — reference solution.

Four independent levels over the same input shape (`user_id,amount,timestamp`):
  Part 1: per-user totals (order-independent grouping).
  Part 2: "which users ever hit >= T within any 60s window" — one deque per user.
  Part 3: "top K users by 60s-window sum as of time t" — a single sweep + sort.
  Part 4: "[small, large, small] pattern" over each user's timestamp-ordered stream.

All amounts/timestamps are plain integers (no currency formatting here — see ps02 for money).
Every window in this problem is the **closed** interval [t - W, t] (both ends inclusive); see
problem.md "Rules" for why (it's pinned by the raw worked example, which only matches closed).
"""
from __future__ import annotations

import sys
from collections import defaultdict, deque

WINDOW_P3 = 60  # Part 3's window is fixed at 60s, not a parameter


def _parse_params(line: str) -> dict[str, int]:
    out: dict[str, int] = {}
    for tok in line.split():
        k, _, v = tok.partition("=")
        out[k] = int(v)
    return out


def _pop_params_line(lines: list[str]) -> tuple[dict[str, int], list[str]]:
    """A params line has no comma and at least one '='; a data line always has exactly two
    commas. If lines[0] looks like params, consume it and return (params, rest)."""
    if lines and "," not in lines[0] and "=" in lines[0]:
        return _parse_params(lines[0]), lines[1:]
    return {}, lines


def _parse_tx(lines: list[str]) -> list[tuple[str, int, int, int]]:
    """Return [(user_id, amount, timestamp, input_index), ...], blank lines dropped.
    input_index is the tie-break for equal timestamps (stable: keep input order)."""
    out = []
    for i, raw in enumerate(lines):
        raw = raw.strip()
        if not raw:
            continue
        user, amt, ts = (p.strip() for p in raw.split(","))
        out.append((user, int(amt), int(ts), i))
    return out


def _by_user_sorted(tx: list[tuple[str, int, int, int]]) -> dict[str, list[tuple[int, int]]]:
    """user_id -> [(timestamp, amount), ...] sorted by (timestamp, input_index)."""
    grouped: dict[str, list[tuple[int, int, int]]] = defaultdict(list)
    for user, amt, ts, idx in tx:
        grouped[user].append((ts, amt, idx))
    out: dict[str, list[tuple[int, int]]] = {}
    for user, events in grouped.items():
        events.sort(key=lambda e: (e[0], e[2]))
        out[user] = [(ts, amt) for ts, amt, _ in events]
    return out


def part1(lines: list[str]) -> list[str]:
    """Sum of amount per user, sorted by user_id (plain string order)."""
    lines = [ln.strip() for ln in lines if ln.strip()]
    totals: dict[str, int] = {}
    for user, amt, _ts, _idx in _parse_tx(lines):
        totals[user] = totals.get(user, 0) + amt
    return [f"{u}: {totals[u]}" for u in sorted(totals)]


def part2(lines: list[str]) -> list[str]:
    """Users who ever had a 60s-window (closed, [ts-W, ts]) cumulative sum >= T.
    Output 'user_id: sum' where sum is the window total the FIRST time (in timestamp order)
    the threshold was crossed."""
    lines = [ln.strip() for ln in lines if ln.strip()]
    params, lines = _pop_params_line(lines)
    T = params["T"]
    W = params.get("W", 60)
    by_user = _by_user_sorted(_parse_tx(lines))

    flagged: dict[str, int] = {}
    for user, events in by_user.items():
        window: deque[tuple[int, int]] = deque()
        total = 0
        for ts, amt in events:
            window.append((ts, amt))
            total += amt
            while window[0][0] < ts - W:
                _old_ts, old_amt = window.popleft()
                total -= old_amt
            if total >= T:
                flagged[user] = total
                break
    return [f"{u}: {flagged[u]}" for u in sorted(flagged)]


def part3(lines: list[str]) -> list[str]:
    """Top K users by sum of amounts in [t - 60, t] (closed), ties: sum desc, user_id asc.
    Users with no transaction in the window are not candidates (never zero-padded)."""
    lines = [ln.strip() for ln in lines if ln.strip()]
    params, lines = _pop_params_line(lines)
    t = params["t"]
    K = params["K"]
    lo = t - WINDOW_P3

    sums: dict[str, int] = {}
    for user, amt, ts, _idx in _parse_tx(lines):
        if lo <= ts <= t:
            sums[user] = sums.get(user, 0) + amt
    ranked = sorted(sums.items(), key=lambda kv: (-kv[1], kv[0]))
    return [f"{u}: {s}" for u, s in ranked[:K]]


def part4(lines: list[str]) -> list[str]:
    """[small, large, small] pattern over each user's timestamp-ordered stream.
    small := amount < S, large := amount >= S. Checked over every window of 3 CONSECUTIVE
    (adjacent, after sorting) transactions per user — overlapping matches all count.
    Output 'user_id: t1,t2,...' (start timestamp of each match, ascending); users with zero
    matches are omitted entirely."""
    lines = [ln.strip() for ln in lines if ln.strip()]
    params, lines = _pop_params_line(lines)
    S = params["S"]
    by_user = _by_user_sorted(_parse_tx(lines))

    out: list[str] = []
    for user in sorted(by_user):
        events = by_user[user]
        labels = ["small" if amt < S else "large" for _ts, amt in events]
        starts = [
            events[i][0]
            for i in range(len(events) - 2)
            if labels[i] == "small" and labels[i + 1] == "large" and labels[i + 2] == "small"
        ]
        if starts:
            out.append(f"{user}: " + ",".join(str(s) for s in starts))
    return out


def main(stdin=sys.stdin, stdout=sys.stdout) -> None:
    raw = [ln.strip() for ln in stdin.read().splitlines() if ln.strip()]
    if not raw:
        return
    part = int(raw[0].split()[1])
    fn = {1: part1, 2: part2, 3: part3, 4: part4}[part]
    out = fn(raw[1:])
    stdout.write("\n".join(out) + ("\n" if out else ""))


if __name__ == "__main__":
    main()
