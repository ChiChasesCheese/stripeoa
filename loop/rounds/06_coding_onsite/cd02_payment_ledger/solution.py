"""cd02 PaymentLedger — reference solution.

The interview asks for a class, not a `partN(lines)` pipeline, so the class *is* the product:
`add_payment` / `add_refund` / `get_total_revenue` / `get_payments_by_date` / `export_json` /
`load_json` are cumulative on one object exactly as an interviewer would reveal them part by
part. `part1`/`part2`/`part3` and `main()` are a thin command-stream harness around the same
class (see problem.md's "CONVENTIONS 对照" note in REPORT.md) so the suite still has the
`impl.partN(lines) -> list[str]` and `main(stdin, stdout)` surfaces this repo's tests expect.

Money is always integer cents. Timestamps are validated against one fixed profile,
`YYYY-MM-DDTHH:MM:SS` (naive, no offset/'Z' -- see problem.md "Variants" for why), via a regex
+ `strptime` so both shape and calendar validity are checked; invalid timestamps raise
`ValueError` wherever they are accepted (`add_payment`, `add_refund`, `get_payments_by_date`).
"""
from __future__ import annotations

import json
import re
import sys
from datetime import datetime

_TS_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$")


def _parse_ts(ts: str) -> datetime:
    if not isinstance(ts, str) or not _TS_RE.match(ts):
        raise ValueError(f"invalid timestamp: {ts!r}")
    try:
        return datetime.strptime(ts, "%Y-%m-%dT%H:%M:%S")
    except ValueError as e:
        raise ValueError(f"invalid timestamp: {ts!r}") from e


class PaymentLedger:
    def __init__(self) -> None:
        self._payments: dict[str, dict] = {}  # payment_id -> {amount, ts, customer, refunded}
        self._refund_ids: set[str] = set()

    # ---------------------------------------------------------------- Part 1
    def add_payment(self, payment_id: str, amount_cents: int, ts_iso: str, customer: str) -> bool:
        """Store a new payment. Returns False (no-op) if `payment_id` was already recorded --
        the caller's retry is idempotent, not an error."""
        _parse_ts(ts_iso)  # validate before touching state; a bad ts consumes nothing
        if payment_id in self._payments:
            return False
        self._payments[payment_id] = {"amount": amount_cents, "ts": ts_iso, "customer": customer, "refunded": 0}
        return True

    def get_total_revenue(self) -> int:
        return sum(p["amount"] - p["refunded"] for p in self._payments.values())

    # ---------------------------------------------------------------- Part 2
    def add_refund(self, refund_id: str, payment_id: str, amount_cents: int, ts_iso: str) -> bool:
        """Apply a (partial) refund. Returns False if `refund_id` was already applied (idempotent
        retry). Raises KeyError for an unknown `payment_id`, ValueError if cumulative refunds
        would exceed the original payment amount."""
        _parse_ts(ts_iso)
        if refund_id in self._refund_ids:
            return False
        if payment_id not in self._payments:
            raise KeyError(payment_id)
        pay = self._payments[payment_id]
        if pay["refunded"] + amount_cents > pay["amount"]:
            raise ValueError(f"refund exceeds remaining balance: {payment_id}")
        pay["refunded"] += amount_cents
        self._refund_ids.add(refund_id)
        return True

    # ---------------------------------------------------------------- Part 3
    def get_payments_by_date(self, start_iso: str, end_iso: str) -> list[dict]:
        """Payments whose `ts` falls in [start_iso, end_iso], both endpoints inclusive, sorted by
        (parsed ts, payment_id). Raises ValueError if either bound is not a valid timestamp."""
        lo, hi = _parse_ts(start_iso), _parse_ts(end_iso)
        rows = [
            (pid, p) for pid, p in self._payments.items()
            if lo <= _parse_ts(p["ts"]) <= hi
        ]
        rows.sort(key=lambda kv: (_parse_ts(kv[1]["ts"]), kv[0]))
        return [
            {
                "payment_id": pid,
                "amount_cents": p["amount"],
                "ts": p["ts"],
                "customer": p["customer"],
                "refunded_cents": p["refunded"],
            }
            for pid, p in rows
        ]

    def export_json(self) -> str:
        return json.dumps(
            {"payments": self._payments, "refund_ids": sorted(self._refund_ids)},
            sort_keys=True,
        )

    @classmethod
    def load_json(cls, blob: str) -> "PaymentLedger":
        data = json.loads(blob)
        ledger = cls()
        ledger._payments = {pid: dict(p) for pid, p in data["payments"].items()}
        ledger._refund_ids = set(data["refund_ids"])
        return ledger


# ------------------------------------------------------------ command-stream harness (io/perf)
def _process(lines: list[str], ledger: PaymentLedger) -> list[str]:
    out: list[str] = []
    for raw in lines:
        s = raw.strip()
        if not s:
            continue
        fields = s.split()
        cmd = fields[0]
        if cmd == "PAY":
            _, pid, amt, ts, cust = fields
            try:
                ok = ledger.add_payment(pid, int(amt), ts, cust)
                out.append(f"PAY {pid} {'OK' if ok else 'DUP'}")
            except ValueError as e:
                out.append(f"PAY {pid} ERROR {e}")
        elif cmd == "REFUND":
            _, rid, pid, amt, ts = fields
            try:
                ok = ledger.add_refund(rid, pid, int(amt), ts)
                out.append(f"REFUND {rid} {'OK' if ok else 'DUP'}")
            except ValueError as e:
                out.append(f"REFUND {rid} ERROR {e}")
            except KeyError:
                out.append(f"REFUND {rid} ERROR unknown_payment {pid}")
        elif cmd == "REVENUE":
            out.append(f"REVENUE {ledger.get_total_revenue()}")
        elif cmd == "RANGE":
            _, start, end = fields
            try:
                rows = ledger.get_payments_by_date(start, end)
                out.append(f"RANGE {len(rows)}")
                for r in rows:
                    out.append(f"{r['payment_id']} {r['amount_cents']} {r['ts']} {r['customer']} {r['refunded_cents']}")
            except ValueError as e:
                out.append(f"RANGE ERROR {e}")
    return out


def run_commands(lines: list[str]) -> list[str]:
    """Execute a command stream against a fresh PaymentLedger; return the output lines."""
    return _process(lines, PaymentLedger())


# The class is cumulative (one interviewer-revealed method set on one object), so all three parts
# run the identical full command engine -- they differ in which commands/tests exercise them, not
# in capability. See REPORT.md's CONVENTIONS note.
def part1(lines: list[str]) -> list[str]:
    return run_commands(lines)


def part2(lines: list[str]) -> list[str]:
    return run_commands(lines)


def part3(lines: list[str]) -> list[str]:
    return run_commands(lines)


def main(stdin=sys.stdin, stdout=sys.stdout) -> None:
    lines = [ln.strip() for ln in stdin.read().splitlines() if ln.strip()]
    out = run_commands(lines)
    stdout.write("\n".join(out) + ("\n" if out else ""))


if __name__ == "__main__":
    main()
