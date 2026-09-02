"""ps05 Numeronym validation — reference solution.

Part 3's collision resolution: words that share (first letter, last letter, length) share a
base numeronym. We grow the kept literal prefix (2, 3, ...) until every word in the group has a
distinct form, capped at len(word) - 2 so the digit segment never drops below 1 (Part 1 requires
digit >= 1). If growing the prefix all the way to that cap still leaves a collision, the words
differ only in the character immediately before the last character -- no valid numeronym (digit
>= 1) can ever distinguish them, so every member of that group falls back to its literal spelling.
"""
from __future__ import annotations

import re
import sys

# first char a-z, then digits with no leading zero (value >= 1), then last char a-z.
NUMERONYM_RE = re.compile(r"^[a-z][1-9][0-9]*[a-z]$")
WORD_RE = re.compile(r"^[a-z]+$")


def is_valid(numeronym: str) -> bool:
    return bool(NUMERONYM_RE.fullmatch(numeronym))


def _clean_lines(lines: list[str]) -> list[str]:
    return [ln.strip() for ln in lines if ln.strip()]


def part1(lines: list[str]) -> list[str]:
    return ["VALID" if is_valid(ln) else "INVALID" for ln in _clean_lines(lines)]


def _expansion_len(numeronym: str) -> int | None:
    if not is_valid(numeronym):
        return None
    return int(numeronym[1:-1]) + 2  # digits between first/last letter + the 2 kept letters


def part2(lines: list[str]) -> list[str]:
    cleaned = _clean_lines(lines)
    if not cleaned:
        return ["NONE"]
    numeronym, words = cleaned[0], cleaned[1:]
    total_len = _expansion_len(numeronym)
    if total_len is None:
        return ["NONE"]
    first, last = numeronym[0], numeronym[-1]
    matches = sorted(
        w
        for w in words
        if WORD_RE.fullmatch(w) and len(w) == total_len and w[0] == first and w[-1] == last
    )
    return matches if matches else ["NONE"]


def _numeronym_for(word: str, prefix_len: int) -> str:
    digit = len(word) - prefix_len - 1
    return f"{word[:prefix_len]}{digit}{word[-1]}"


def _resolve_group(group: list[str]) -> dict[str, str]:
    """group: words sharing (first letter, last letter, length). Returns word -> numeronym."""
    length = len(group[0])
    cap = length - 2  # max prefix length that keeps digit >= 1
    for prefix_len in range(2, cap):  # 2 .. cap-1 (cap itself tried below, kept for readability)
        forms = [_numeronym_for(w, prefix_len) for w in group]
        if len(set(forms)) == len(group):
            return dict(zip(group, forms))
    if cap >= 2:
        forms = [_numeronym_for(w, cap) for w in group]
        if len(set(forms)) == len(group):
            return dict(zip(group, forms))
    # irreducible: words differ only in the character right before the last one.
    return {w: w for w in group}


def part3(lines: list[str]) -> list[str]:
    seen: dict[str, None] = {}
    for w in _clean_lines(lines):
        if WORD_RE.fullmatch(w):
            seen[w] = None
    words = list(seen)

    result: dict[str, str] = {}
    groups: dict[str, list[str]] = {}
    for w in words:
        if len(w) < 3:
            result[w] = w
            continue
        base = f"{w[0]}{len(w) - 2}{w[-1]}"
        groups.setdefault(base, []).append(w)

    for group in groups.values():
        if len(group) == 1:
            result[group[0]] = f"{group[0][0]}{len(group[0]) - 2}{group[0][-1]}"
        else:
            result.update(_resolve_group(group))

    return [f"{w} -> {result[w]}" for w in sorted(result)]


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
    else:
        raise ValueError(f"unknown header: {header!r}")
    stdout.write("\n".join(out) + ("\n" if out else ""))


if __name__ == "__main__":
    main()
