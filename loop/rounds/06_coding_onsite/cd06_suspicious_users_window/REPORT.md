# cd06 Suspicious Users Sliding Window — report

## Summary
Classic fraud-triage sliding window: flag a user if any 60-second window anchored at one of their
own transactions contains more than 3 transactions. The interview explicitly asks for the
O(n^2) -> O(n log n) upgrade (naive per-transaction count -> sort + two-pointer), which is the
actual skill being tested — the domain framing (Radar-style burst detection) is secondary to
demonstrating that upgrade and reasoning about window boundaries precisely.

## Sources & confidence
high for the core rule ("> 3 transactions in a 1-minute window", naive-then-hashmap/window
upgrade) — one source, but an almost-verbatim interview-experience recap (rare for this repo).
The exact I/O protocol (`PART n` header, CSV row shape, `user_id: count in [start, end]` format
for Part 2, closed-interval `[t-60, t]` window definition, "first trigger" semantics) is this
repo's own reconstruction, since the source is one recap sentence with no I/O sample at all —
flagged explicitly in problem.md's Clarifications.

## Approach by part
1. Part 1: interview-legal naive approach is O(n^2) per user (for every transaction, count how
   many of the user's own transactions fall in its trailing 60s window). The reference solution
   instead reuses the Part 2 engine (see below) since it's strictly cheaper and gives identical
   results — noted in solution.py's module docstring so it doesn't read as "the naive answer was
   secretly skipped".
2. Part 2: group by `user_id`, sort each user's timestamps, then a single forward-only two-pointer
   scan (`_first_trigger`): the left pointer only ever advances past timestamps that fall outside
   `[t-60, t]` as the right pointer `t` walks forward. The first `t` where `count = j - i + 1`
   reaches 4 is returned immediately — this is provably the earliest-triggering window in time
   order because the left pointer never moves backward and every earlier `t` was already checked
   and found `< 4`.

## Pitfalls hidden tests target
- `> 3` means `>= 4`, not `>= 3` — a single off-by-one flips every boundary case.
- The window is closed (`<= 60` inclusive), so two transactions exactly 60s apart both count, but
  61s apart does not — tested with an otherwise-identical 4-transaction cluster that differs only
  in whether the last gap is 60s or 61s.
- Duplicate timestamps: several transactions sharing one instant all count individually, and the
  reported window can collapse to `start_ts == end_ts`; the *count* reported at first trigger is
  exactly the threshold (4), not the eventual burst size (5), because Part 2 must report the
  FIRST trigger, not the largest one it could eventually observe.
- A user with two separate qualifying bursts (an early modest one, a later much denser one) must
  report the early one — a naive "find the window with the maximum count" implementation would
  silently report the wrong (denser, later) burst instead of the first one.
- Input arrives out of order, both across users and within one user's own records — grouping and
  per-user sorting is mandatory, not an optimization; a solution that windows over raw input order
  will miscount.
- Part 1 and Part 2 have deliberately different output shapes (bare `user_id` vs.
  `user_id: count in [start, end]`) — not a subset/superset of one another.

## Complexity & measured cost
O(n log n): one global parse O(n), a sort per user (sum of per-user sorts is O(n log n) in the
worst case when one user holds most of the rows, still bounded by the overall n log n), then one
O(n) two-pointer pass total across all users. Perf test: 1,000,000 rows across 200,000 users,
random timestamps over a 10,000,000s range — measured well under the 2 s / 256 MB budget on
CPython 3.12 (typically ~0.6-0.9 s, well under 100 MB), dominated by string parsing, not the
windowing itself.

## Test inventory
19 tests — part1: 8 (incl. 1 io) · part2: 10 (incl. 1 io, 1 perf); edge: 6 · fmt: 2 · io: 2 ·
perf: 1.

## Skills exercised
S02 parsing (CSV, out-of-order) · S04 grouping by key · S05 sliding-window / two-pointer ·
S08 deterministic tie-break under sort · S09 exact output formatting · S17 complexity upgrade
(O(n^2) -> O(n log n), justified not just coded) · S19 incremental design (naive -> optimal, same
detection rule)
