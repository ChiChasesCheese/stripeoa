"""cd01 Subscription email scheduler — reference solution.

Model: each user has at most one subscription state (plan, expire date, canceled flag) plus a
small per-user list of committed/pending emails (welcome / expiring / expired / renewed /
canceled). Every state-changing event at date `d` first discards that user's emails scheduled
**strictly after** `d` (not yet "sent") and then appends the freshly computed schedule — this one
rule implements Part 2's rescheduling of pending `expiring`/`expired` emails and Part 3's
cancellation. Events always process in (date, input order) regardless of input order; the final
query window filters by date only, and output order is (date, user, fixed email-type priority),
never event-processing order — see TYPE_ORDER.
"""
from __future__ import annotations

import re
import sys
from datetime import date, timedelta

PERIOD_DAYS = {"monthly": 30, "annual": 365}
# Fixed output tie-break priority, independent of when an email was scheduled.
TYPE_ORDER = {"welcome": 0, "expiring": 1, "expired": 2, "renewed": 3, "canceled": 4}
_RANGE_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})\.\.(\d{4}-\d{2}-\d{2})$")


class _Sub:
    __slots__ = ("plan", "expire", "canceled")

    def __init__(self, plan: str, expire: date, canceled: bool = False):
        self.plan, self.expire, self.canceled = plan, expire, canceled


def _period(plan: str) -> int:
    return PERIOD_DAYS[plan]


def _add_schedule(lst: list[tuple[date, str]], expire: date, cutoff: date) -> None:
    """Append the (expiring, expiring, expired) triple for a period ending on `expire`.
    `expiring` emails dated on or before `cutoff` (the event day) are dropped — they would fall
    in the past/on the event day itself, which this rule treats as never sent. `expired` is
    always appended: by construction every caller passes expire >= cutoff."""
    for delta in (7, 1):
        d = expire - timedelta(days=delta)
        if d > cutoff:
            lst.append((d, "expiring"))
    lst.append((expire, "expired"))


def _parse(lines: list[str]):
    rows = [ln.strip() for ln in lines if ln.strip()]
    query = None
    if rows and _RANGE_RE.match(rows[-1]):
        query = rows.pop()
    events = []
    for i, raw in enumerate(rows):
        parts = [p.strip() for p in raw.split(",")]
        d = date.fromisoformat(parts[0])
        user, action = parts[1], parts[2]
        plan = parts[3] if len(parts) > 3 else None
        events.append((d, i, user, action, plan))
    events.sort(key=lambda r: (r[0], r[1]))  # chronological; ties keep input order
    if query:
        m = _RANGE_RE.match(query)
        lo, hi = date.fromisoformat(m.group(1)), date.fromisoformat(m.group(2))
    else:
        lo, hi = date.min, date.max
    return events, lo, hi


def _run(lines: list[str], allow_change: bool, allow_renew_cancel: bool) -> list[str]:
    events, lo, hi = _parse(lines)
    state: dict[str, _Sub] = {}
    emails: dict[str, list[tuple[date, str]]] = {}

    for d, _, user, action, plan in events:
        if action == "subscribe":
            lst = emails.setdefault(user, [])
            lst[:] = [e for e in lst if e[0] <= d]  # a resubscribe wipes any pending future email
            expire = d + timedelta(days=_period(plan))
            lst.append((d, "welcome"))
            _add_schedule(lst, expire, d)
            state[user] = _Sub(plan, expire)
        elif action == "change" and allow_change:
            sub = state.get(user)
            if sub is None or sub.canceled or d >= sub.expire:
                continue  # unknown user, canceled, or already at/after expiry: ignored
            lst = emails.setdefault(user, [])
            lst[:] = [e for e in lst if e[0] <= d]
            remaining_old = (sub.expire - d).days
            # remaining days recomputed under the NEW plan's period, floored (never rounded up)
            new_remaining = remaining_old * _period(plan) // _period(sub.plan)
            new_expire = d + timedelta(days=new_remaining)
            _add_schedule(lst, new_expire, d)
            sub.plan, sub.expire = plan, new_expire
        elif action == "renew" and allow_renew_cancel:
            sub = state.get(user)
            if sub is None or sub.canceled:
                continue  # unknown or canceled user: ignored
            lst = emails.setdefault(user, [])
            lst[:] = [e for e in lst if e[0] <= d]
            if d < sub.expire:  # renewing before expiry: extend the term from the OLD end
                new_expire = sub.expire + timedelta(days=_period(sub.plan))
                lst.append((d, "renewed"))
            else:  # renewing on/after the expiry day: treated as a brand new subscription
                new_expire = d + timedelta(days=_period(sub.plan))
                lst.append((d, "welcome"))
            _add_schedule(lst, new_expire, d)
            sub.expire = new_expire
        elif action == "cancel" and allow_renew_cancel:
            sub = state.get(user)
            if sub is None or sub.canceled:
                continue  # unknown or already-canceled user: ignored (idempotent)
            lst = emails.setdefault(user, [])
            lst[:] = [e for e in lst if e[0] <= d]  # revokes every pending expiring/expired
            lst.append((d, "canceled"))
            sub.canceled = True
        # any other (action, allow_*) combination -- e.g. `change` in part1 -- is silently ignored

    out = []
    for user, lst in emails.items():
        for d, typ in lst:
            if lo <= d <= hi:
                out.append((d, user, TYPE_ORDER[typ], typ))
    out.sort(key=lambda t: (t[0], t[1], t[2]))
    return [f"{d.isoformat()} {user} {typ}" for d, user, _, typ in out]


def part1(lines: list[str]) -> list[str]:
    return _run(lines, allow_change=False, allow_renew_cancel=False)


def part2(lines: list[str]) -> list[str]:
    return _run(lines, allow_change=True, allow_renew_cancel=False)


def part3(lines: list[str]) -> list[str]:
    return _run(lines, allow_change=True, allow_renew_cancel=True)


def main(stdin=sys.stdin, stdout=sys.stdout) -> None:
    lines = [ln.strip() for ln in stdin.read().splitlines() if ln.strip()]
    if not lines:
        return
    part = 3  # no PART header -> full rule set (part3 is a superset of part1/part2)
    if lines[0].upper().startswith("PART"):
        part = int(lines[0].split()[1])
        lines = lines[1:]
    out = {1: part1, 2: part2, 3: part3}[part](lines)
    stdout.write("\n".join(out) + ("\n" if out else ""))


if __name__ == "__main__":
    main()
