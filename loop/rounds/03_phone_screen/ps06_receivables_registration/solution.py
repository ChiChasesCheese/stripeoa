"""ps06 Receivables registration — reference solution.

All money is integer cents internally; the only string<->cents conversions happen at the parse
and format boundaries. Part 1 assumes well-formed rows (no defensive parsing). Part 2 adds row
validation (skip + count), negative amounts, and rolling a weekend payout_date forward to the
following Monday *before* it becomes part of the aggregation key.
"""
from __future__ import annotations

import re
import sys
from collections import defaultdict
from datetime import datetime, timedelta

AMOUNT_RE = re.compile(r"^-?\d+\.\d{2}$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

GroupKey = tuple[str, str, str]  # (merchant_id, card_type, payout_date)


def _amount_to_cents(amount: str) -> int:
    """'150.00' -> 15000 ; '-15.50' -> -1550. Caller guarantees AMOUNT_RE already matched."""
    sign = -1 if amount.startswith("-") else 1
    whole, frac = amount.lstrip("-").split(".")
    return sign * (int(whole) * 100 + int(frac))


def _valid_amount(amount: str) -> bool:
    return bool(AMOUNT_RE.match(amount))


def _valid_date(date_str: str) -> bool:
    if not DATE_RE.match(date_str):
        return False
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        return False
    return True


def _roll_weekend(date_str: str) -> str:
    """Saturday -> +2 days, Sunday -> +1 day, weekday unchanged."""
    d = datetime.strptime(date_str, "%Y-%m-%d").date()
    weekday = d.weekday()  # Mon=0 .. Sun=6
    if weekday == 5:
        d += timedelta(days=2)
    elif weekday == 6:
        d += timedelta(days=1)
    return d.isoformat()


def _fmt_cents(cents: int) -> str:
    sign = "-" if cents < 0 else ""
    cents = abs(cents)
    return f"{sign}{cents // 100}.{cents % 100:02d}"


def _render(totals: dict[GroupKey, int]) -> list[str]:
    ordered = sorted(totals.items(), key=lambda kv: (kv[0][0], kv[0][2], kv[0][1]))
    return [f"{merchant},{card_type},{payout_date},{_fmt_cents(cents)}"
            for (merchant, card_type, payout_date), cents in ordered]


def part1(lines: list[str]) -> list[str]:
    totals: dict[GroupKey, int] = defaultdict(int)
    for raw in lines[1:]:
        raw = raw.strip()
        if not raw:
            continue
        _customer, merchant, payout_date, card_type, amount = (p.strip() for p in raw.split(","))
        totals[(merchant, card_type, payout_date)] += _amount_to_cents(amount)
    return _render(totals)


def part2(lines: list[str]) -> list[str]:
    totals: dict[GroupKey, int] = defaultdict(int)
    skipped = 0
    for raw in lines[1:]:
        raw = raw.strip()
        if not raw:
            continue
        fields = [p.strip() for p in raw.split(",")]
        if len(fields) != 5:
            skipped += 1
            continue
        _customer, merchant, payout_date, card_type, amount = fields
        if not _valid_date(payout_date) or not _valid_amount(amount):
            skipped += 1
            continue
        payout_date = _roll_weekend(payout_date)
        totals[(merchant, card_type, payout_date)] += _amount_to_cents(amount)
    return _render(totals) + [f"SKIPPED {skipped}"]


def main(stdin=sys.stdin, stdout=sys.stdout) -> None:
    raw = stdin.read().splitlines()
    if not raw:
        return
    header, body = raw[0].strip(), raw[1:]
    if header == "PART 1":
        out = part1(body)
    elif header == "PART 2":
        out = part2(body)
    else:
        raise ValueError(f"unknown header: {header!r}")
    stdout.write("\n".join(out) + ("\n" if out else ""))


if __name__ == "__main__":
    main()
