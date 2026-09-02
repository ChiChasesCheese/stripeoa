"""ps05 Numeronym validation — YOUR implementation."""
from __future__ import annotations

import sys


def is_valid(numeronym: str) -> bool:
    """True iff numeronym matches ^[a-z][1-9][0-9]*[a-z]$ (see problem.md Part 1)."""
    # TODO
    return False


def part1(lines: list[str]) -> list[str]:
    """lines: raw candidate numeronym strings, one per line (blank lines ignored).
    Return ['VALID'/'INVALID', ...] per candidate, in input order."""
    # TODO
    return []


def part2(lines: list[str]) -> list[str]:
    """lines[0]: numeronym. lines[1:]: dictionary words, one per line.
    Return matching dictionary words sorted lexicographically, or ['NONE']."""
    # TODO
    return []


def part3(lines: list[str]) -> list[str]:
    """lines: dictionary words, one per line. Return ['word -> numeronym', ...] sorted by word,
    with collisions resolved per problem.md Part 3."""
    # TODO
    return []


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
