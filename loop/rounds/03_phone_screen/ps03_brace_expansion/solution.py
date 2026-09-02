"""ps03 Brace Expansion — reference solution.

Three levels of the same idea (glob-style `{a,b,c}` expansion, as in shell filenames or webhook
endpoint templates):
  Part 1 - one un-nested group, well-formed input assumed.
  Part 2 - same scope (at most one group, no nesting) but malformed input must be handled:
           unmatched braces, more than one group, or a group with < 2 comma-separated tokens ->
           the pattern is echoed back unchanged (see `_validate_single`).
  Part 3 - groups may nest and a pattern may contain several groups (cartesian product); the
           same malformed -> echo-unchanged contract now covers the richer grammar (`_validate`).

Order is always preserved (first token first) and duplicates are never deduped or sorted — that
is the deliberate difference from the sorted/deduped LC 1087 style (see `qA03_lc1087_brace_expansion`
in `problems/`): this is a phone-screen "glob expansion" question, not the LeetCode one.
"""
from __future__ import annotations

import sys


def _find_matching(s: str, i: int) -> int:
    """s[i] == '{'. Index of the matching '}' (brace-depth aware), or -1 if unterminated."""
    depth = 0
    for j in range(i, len(s)):
        if s[j] == "{":
            depth += 1
        elif s[j] == "}":
            depth -= 1
            if depth == 0:
                return j
    return -1  # unterminated


def _split_top_commas(s: str) -> list[str]:
    """Split s on ',' at brace-depth 0 (depth local to this substring)."""
    parts: list[str] = []
    depth = 0
    start = 0
    for i, c in enumerate(s):
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
        elif c == "," and depth == 0:
            parts.append(s[start:i])
            start = i + 1
    parts.append(s[start:])
    return parts


def _expand(s: str) -> list[str]:
    """Expand a well-formed pattern (balanced braces, every group has >= 2 alternatives; not
    re-checked here -- callers that need robustness validate first). Segments (literal runs and
    groups) are expanded left to right; within a group each comma-separated alternative is itself
    expanded recursively and the results are concatenated in written order (union, no dedup) --
    so nesting and multiple groups both fall out of one segment/cartesian-product walk."""
    segments: list[list[str]] = []
    buf: list[str] = []
    i, n = 0, len(s)
    while i < n:
        if s[i] == "{":
            j = _find_matching(s, i)
            if j == -1:  # unterminated group -- defensive only, not part of any documented contract
                j = n - 1
            if buf:
                segments.append(["".join(buf)])
                buf = []
            options: list[str] = []
            for alt in _split_top_commas(s[i + 1:j]):
                options.extend(_expand(alt))  # flatten in written order, duplicates kept
            segments.append(options)
            i = j + 1
        else:
            buf.append(s[i])
            i += 1
    if buf:
        segments.append(["".join(buf)])
    results = [""]
    for seg in segments:  # cartesian product; leftmost segment is the outer loop (bash order)
        results = [r + opt for r in results for opt in seg]
    return results


def _validate(s: str) -> bool:
    """General grammar (Part 3): braces balanced and properly nested, every group (at any depth)
    has >= 2 top-level alternatives, each of which is itself well-formed."""
    i, n = 0, len(s)
    while i < n:
        c = s[i]
        if c == "{":
            j = _find_matching(s, i)
            if j == -1:  # unterminated group
                return False
            inner = s[i + 1:j]
            alts = _split_top_commas(inner)
            if len(alts) < 2:
                return False
            if not all(_validate(alt) for alt in alts):
                return False
            i = j + 1
        elif c == "}":
            return False  # closing brace with nothing open
        else:
            i += 1
    return True


def _validate_single(s: str) -> bool:
    """Part 2's narrower grammar: at most one group in the whole pattern, no nesting inside it,
    braces balanced, and (if present) the group has >= 2 tokens. Anything richer (a second group,
    a nested group) is *also* malformed here -- that richer grammar is Part 3's new capability."""
    depth_seen = False
    in_group = False
    alt_count = 0
    for c in s:
        if c == "{":
            if depth_seen:  # a 2nd top-level group, or nesting inside the 1st -- out of scope
                return False
            depth_seen = True
            in_group = True
            alt_count = 1
        elif c == "}":
            if not in_group:
                return False  # unmatched close
            in_group = False
            if alt_count < 2:
                return False
        elif c == "," and in_group:
            alt_count += 1
    return not in_group  # False if the group was never closed


def expand_braces(pattern: str) -> list[str]:
    """Part 1: expand a pattern that has at most one, un-nested `{a,b,c}` group. Order preserved,
    prefix/suffix kept, empty tokens allowed (`read.txt{,.bak}`). Input assumed well-formed."""
    return _expand(pattern)


def expand_braces_safe(pattern: str) -> list[str]:
    """Part 2: like expand_braces, but a malformed pattern (unmatched brace, a second/nested
    group, or a group with < 2 tokens) is returned unchanged as the sole result."""
    if not _validate_single(pattern):
        return [pattern]
    return _expand(pattern)


def expand_braces_nested(pattern: str) -> list[str]:
    """Part 3: nested groups (`{a,{b,c}}d`) and multiple groups (`{a,b}{1,2}`, cartesian product,
    leftmost group outermost) are now valid input; malformed patterns (checked recursively at
    every depth) are still echoed back unchanged."""
    if not _validate(pattern):
        return [pattern]
    return _expand(pattern)


def part1(lines: list[str]) -> list[str]:
    return [",".join(expand_braces(p)) for p in lines]


def part2(lines: list[str]) -> list[str]:
    return [",".join(expand_braces_safe(p)) for p in lines]


def part3(lines: list[str]) -> list[str]:
    return [",".join(expand_braces_nested(p)) for p in lines]


PARTS = {1: part1, 2: part2, 3: part3}


def main(stdin=sys.stdin, stdout=sys.stdout) -> None:
    lines = [ln.strip() for ln in stdin.read().splitlines() if ln.strip()]
    out: list[str] = []
    if lines and lines[0].upper().startswith("PART"):
        part = int(lines[0].split()[1])
        out = PARTS[part](lines[1:])
    stdout.write("\n".join(out) + ("\n" if out else ""))


if __name__ == "__main__":
    main()
