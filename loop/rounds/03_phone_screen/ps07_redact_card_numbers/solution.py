"""ps07 Redact card numbers from logs — reference solution.

Single-pass, no-backtracking scanner: `_scan_candidates` walks each log line once, producing
maximal (start, end, digit_count) spans -- a span always starts and ends on a digit; when
`allow_separators` is True a single ' ' or '-' between two digit groups is absorbed into the
span too, but never a leading/trailing/doubled separator. Parts only differ in two booleans
(`allow_separators`, `check_luhn_brand`) fed into one shared `_redact_line` engine -- this is
the incremental design the problem asks for (Part 1 subset of Part 2 subset of Part 3/4).
"""
from __future__ import annotations

import sys

# (network, length, prefix_len, prefix_min, prefix_max) -- a candidate matches a network iff its
# digit length equals `length` and its first `prefix_len` digits, read as an int, fall in
# [prefix_min, prefix_max]. Multiple rows per network cover disjoint prefix ranges/lengths.
NETWORK_RULES: tuple[tuple[str, int, int, int, int], ...] = (
    ("VISA", 13, 1, 4, 4),
    ("VISA", 16, 1, 4, 4),
    ("VISA", 19, 1, 4, 4),
    ("MASTERCARD", 16, 2, 51, 55),
    ("MASTERCARD", 16, 4, 2221, 2720),
    ("AMEX", 15, 2, 34, 34),
    ("AMEX", 15, 2, 37, 37),
    ("DISCOVER", 16, 4, 6011, 6011),
    ("DISCOVER", 16, 2, 65, 65),
)

MIN_PAN_DIGITS = 13
MAX_PAN_DIGITS = 19
KEEP_LAST = 4


def luhn_ok(digits: str) -> bool:
    """From the right: double every second digit (starting with the 2nd from the right),
    subtract 9 if > 9, sum all; valid iff sum % 10 == 0."""
    total = 0
    for i, ch in enumerate(reversed(digits)):
        d = int(ch)
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return total % 10 == 0


def brand_of(digits: str) -> str | None:
    """Network by length + prefix only (no checksum). None if no rule matches."""
    n = len(digits)
    for name, length, prefix_len, prefix_min, prefix_max in NETWORK_RULES:
        if n == length and prefix_min <= int(digits[:prefix_len]) <= prefix_max:
            return name
    return None


def is_card_number(digits: str) -> bool:
    """True iff digits is a real PAN: right (length, prefix) for some network AND Luhn passes."""
    return brand_of(digits) is not None and luhn_ok(digits)


def _scan_candidates(line: str, allow_separators: bool) -> list[tuple[int, int, int]]:
    """Single pass over `line`. Returns (start, end, digit_count) for every maximal run of
    digits (optionally chained through single ' '/'-' separators between two digit groups).
    `line[start:end]` always starts and ends on a digit. O(len(line)) total: `i` only ever
    advances, so the outer while touches each character a bounded number of times."""
    n = len(line)
    spans: list[tuple[int, int, int]] = []
    i = 0
    while i < n:
        if line[i].isdigit():
            start = i
            j = i
            count = 0
            last_digit_end = i
            while j < n:
                if line[j].isdigit():
                    j += 1
                    count += 1
                    last_digit_end = j
                elif allow_separators and line[j] in " -" and j + 1 < n and line[j + 1].isdigit():
                    j += 1  # absorb a single separator only if another digit follows
                else:
                    break
            spans.append((start, last_digit_end, count))
            i = last_digit_end
        else:
            i += 1
    return spans


def _mask_span(text: str, count: int) -> str:
    """Mask `text` (a candidate substring, digits + separators) in place: every digit except the
    last KEEP_LAST is replaced with '*'; non-digit separators are copied through unchanged."""
    mask_upto = count - KEEP_LAST
    out = []
    seen = 0
    for ch in text:
        if ch.isdigit():
            out.append("*" if seen < mask_upto else ch)
            seen += 1
        else:
            out.append(ch)
    return "".join(out)


def _redact_line(line: str, allow_separators: bool, check_luhn_brand: bool) -> tuple[str, int]:
    """Redact every qualifying candidate in one line. Returns (new_line, spans_redacted)."""
    spans = _scan_candidates(line, allow_separators)
    if not spans:
        return line, 0
    parts: list[str] = []
    cursor = 0
    redacted = 0
    for start, end, count in spans:
        if count < MIN_PAN_DIGITS or count > MAX_PAN_DIGITS:
            continue
        if check_luhn_brand:
            digits = "".join(ch for ch in line[start:end] if ch.isdigit())
            if not is_card_number(digits):
                continue
        parts.append(line[cursor:start])
        parts.append(_mask_span(line[start:end], count))
        cursor = end
        redacted += 1
    parts.append(line[cursor:])
    return "".join(parts), redacted


def part1(lines: list[str]) -> list[str]:
    """Bare digit runs only, no Luhn/brand filter. See problem.md Part 1."""
    return [_redact_line(ln, allow_separators=False, check_luhn_brand=False)[0] for ln in lines]


def part2(lines: list[str]) -> list[str]:
    """Bare + single space/'-'-separated digit chains, still no Luhn/brand filter."""
    return [_redact_line(ln, allow_separators=True, check_luhn_brand=False)[0] for ln in lines]


def part3(lines: list[str]) -> list[str]:
    """Same scanner as Part 2, but only redacts Luhn+brand-valid candidates."""
    return [_redact_line(ln, allow_separators=True, check_luhn_brand=True)[0] for ln in lines]


def part4(lines: list[str]) -> list[str]:
    """Same detection as Part 3, streaming-shaped (single pass per line, no re-scans), plus a
    trailing 'REDACTED n' stats line counting spans actually masked across all input."""
    out: list[str] = []
    total = 0
    for ln in lines:
        new_ln, n = _redact_line(ln, allow_separators=True, check_luhn_brand=True)
        out.append(new_ln)
        total += n
    out.append(f"REDACTED {total}")
    return out


def main(stdin=sys.stdin, stdout=sys.stdout) -> None:
    raw = stdin.read().splitlines()
    if not raw:
        return
    header, body = raw[0].strip(), raw[1:]
    if header == "PART 1":
        out = part1(body)
    elif header == "PART 2":
        out = part2(body)
    elif header == "PART 3":
        out = part3(body)
    elif header == "PART 4":
        out = part4(body)
    else:
        raise ValueError(f"unknown header: {header!r}")
    stdout.write("\n".join(out) + ("\n" if out else ""))


if __name__ == "__main__":
    main()
