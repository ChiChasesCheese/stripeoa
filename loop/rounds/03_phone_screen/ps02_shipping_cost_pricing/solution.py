"""ps02 Shipping Cost Pricing — reference solution.

Three independent pricing engines over the same shape (a rate table + a list of orders):
  Part 1: flat per-unit price lookup.
  Part 2: quantity tiers, single matched-band rate applied to the whole order
          (this is exactly what Part 3 calls the 'fixed' tier type).
  Part 3: same tiers, each band additionally carries type in {incremental, fixed}; the type
          of the MATCHED band (the one containing the order's quantity) decides whether the
          whole quantity is billed at that one rate ('fixed') or billed progressively through
          every band from the first up to the matched one ('incremental' — tax-bracket style).

All money is integer cents (see parse_money_to_cents / fmt_cents) — no floats anywhere.
"""
from __future__ import annotations

import sys

Band = tuple[int, int | None, int, str]  # (min_qty, max_qty_or_None, cost_cents, type)


def parse_money_to_cents(raw: str) -> int:
    """Accepts '5', '5.0', '5.00', '-3.5' (no thousands separators). Exactly 0-2 decimal
    digits; more than 2 is a ValueError (kept strict — a rate table is not user free-text)."""
    s = raw.strip()
    neg = s.startswith("-")
    if neg:
        s = s[1:]
    if "." in s:
        whole, frac = s.split(".", 1)
        if len(frac) > 2:
            raise ValueError(f"too many decimal places: {raw!r}")
        frac = frac.ljust(2, "0")
    else:
        whole, frac = s, "00"
    cents = int(whole) * 100 + int(frac or "0")
    return -cents if neg else cents


def fmt_cents(cents: int) -> str:
    sign = "-" if cents < 0 else ""
    cents = abs(cents)
    return f"{sign}${cents // 100}.{cents % 100:02d}"


def parse_max_qty(raw: str) -> int | None:
    """'inf' (exact, lowercase) means open-ended; anything else must be an int."""
    raw = raw.strip()
    return None if raw == "inf" else int(raw)


def _nonblank(lines: list[str]) -> list[str]:
    return [ln.strip() for ln in lines if ln.strip()]


def _split_sections(lines: list[str]) -> tuple[list[str], list[str]]:
    """lines (already non-blank) = 'RATES', rate rows..., 'ORDERS', order rows...
    Returns (rate_lines, order_lines)."""
    lines = _nonblank(lines)
    assert lines and lines[0] == "RATES", "expected a RATES section"
    split = lines.index("ORDERS")
    return lines[1:split], lines[split + 1 :]


def _parse_flat_rates(rate_lines: list[str]) -> dict[tuple[str, str], int]:
    table: dict[tuple[str, str], int] = {}
    for ln in rate_lines:
        country, product, unit_cost = (p.strip() for p in ln.split(","))
        table[(country, product)] = parse_money_to_cents(unit_cost)
    return table


def _parse_tiered_rates(rate_lines: list[str], with_type: bool) -> dict[tuple[str, str], list[Band]]:
    table: dict[tuple[str, str], list[Band]] = {}
    for ln in rate_lines:
        fields = [p.strip() for p in ln.split(",")]
        if with_type:
            country, product, mn, mx, cost, typ = fields
            if typ not in ("incremental", "fixed"):
                raise ValueError(f"invalid tier type: {typ!r}")
        else:
            country, product, mn, mx, cost = fields
            typ = "fixed"  # Part 2 has no type column: behaves exactly like a 'fixed' band
        band: Band = (int(mn), parse_max_qty(mx), parse_money_to_cents(cost), typ)
        table.setdefault((country, product), []).append(band)
    for bands in table.values():
        bands.sort(key=lambda b: b[0])
    return table


def _find_band(bands: list[Band], qty: int) -> Band | None:
    for mn, mx, cost, typ in bands:
        if mn <= qty and (mx is None or qty <= mx):
            return (mn, mx, cost, typ)
    return None


def _price_flat(table: dict[tuple[str, str], int], country: str, product: str, qty: int) -> tuple[int | None, str | None]:
    key = (country, product)
    if key not in table:
        return None, f"unknown product {country}/{product}"
    return qty * table[key], None


def _price_tiered(
    table: dict[tuple[str, str], list[Band]], country: str, product: str, qty: int
) -> tuple[int | None, str | None]:
    key = (country, product)
    if key not in table:
        return None, f"unknown product {country}/{product}"
    if qty == 0:
        return 0, None  # zero items always costs zero, no tier lookup needed
    bands = table[key]
    matched = _find_band(bands, qty)
    if matched is None:
        return None, f"no tier for {country}/{product} at qty={qty}"
    _mn, _mx, cost, typ = matched
    if typ == "fixed":
        return qty * cost, None

    # incremental: walk bands ascending from qty 1, summing each band's own rate for the
    # units that fall inside it, stopping once we've covered the matched band.
    total = 0
    expected_start = 1
    for b_mn, b_mx, b_cost, _b_typ in bands:
        if b_mn > qty:
            break
        if b_mn != expected_start:
            return None, f"incremental gap for {country}/{product} at qty={qty}"
        upper = qty if b_mx is None else min(qty, b_mx)
        total += (upper - b_mn + 1) * b_cost
        if b_mx is None or b_mx >= qty:
            break
        expected_start = b_mx + 1
    return total, None


def _price_orders(order_lines: list[str], price_one) -> list[str]:
    out = []
    for ln in order_lines:
        order_id, country, product, qty = (p.strip() for p in ln.split(","))
        cost, err = price_one(country, product, int(qty))
        out.append(f"{order_id}: ERROR {err}" if err else f"{order_id}: {fmt_cents(cost)}")
    return out


def part1(lines: list[str]) -> list[str]:
    """Flat per-unit price: RATES rows 'country,product,unit_cost'; ORDERS rows
    'order_id,country,product,quantity'. Output 'order_id: $x.xx' (or ERROR), input order."""
    rate_lines, order_lines = _split_sections(lines)
    table = _parse_flat_rates(rate_lines)
    return _price_orders(order_lines, lambda c, p, q: _price_flat(table, c, p, q))


def part2(lines: list[str]) -> list[str]:
    """Quantity tiers: RATES rows 'country,product,min_qty,max_qty,cost' (closed interval
    [min_qty, max_qty]; max_qty may be the literal 'inf'). The whole order quantity is billed
    at the single matched band's rate (no cumulative summation — see Part 3 for that)."""
    rate_lines, order_lines = _split_sections(lines)
    table = _parse_tiered_rates(rate_lines, with_type=False)
    return _price_orders(order_lines, lambda c, p, q: _price_tiered(table, c, p, q))


def part3(lines: list[str]) -> list[str]:
    """Same tiers as Part 2 plus a trailing 'incremental'/'fixed' column per band. The type of
    the band that CONTAINS the order's quantity decides the whole order's pricing mode."""
    rate_lines, order_lines = _split_sections(lines)
    table = _parse_tiered_rates(rate_lines, with_type=True)
    return _price_orders(order_lines, lambda c, p, q: _price_tiered(table, c, p, q))


def main(stdin=sys.stdin, stdout=sys.stdout) -> None:
    raw = [ln.strip() for ln in stdin.read().splitlines() if ln.strip()]
    if not raw:
        return
    part = int(raw[0].split()[1])
    fn = {1: part1, 2: part2, 3: part3}[part]
    out = fn(raw[1:])
    stdout.write("\n".join(out) + ("\n" if out else ""))


if __name__ == "__main__":
    main()
