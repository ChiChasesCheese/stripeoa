# cd07 Transactions + rules (AI Programming Exercise) — report

## Summary
A three-stage rule engine (`ALLOW|BLOCK if <condition>`) over a batch of transactions: keyword
equality, then comparison operators + `in [...]`, then a full `and`/`or`/`not`/parens
recursive-descent grammar with per-rule error reporting. It is the AI-assisted-round sibling of
`problems/q12_platform_balance_radar_rules`'s Radar grammar, deliberately smaller (no quoted
constants, no `:field:` markers, no balance ledger) since the real round budgets ~30 min with an
AI assistant instead of 75 min hand-written.

## Sources & confidence
Medium. Two independent sources (interviewdb.io's AI-programming-exercise guide, 2026-06-09;
interviewfox.ai's HackerRank OA guide, 2026) agree on the round's existence, format (HackerRank +
embedded AI chat, ~30 min), grading axis ("can you direct/verify/debug AI, do you write your own
tests"), and the problem's shape ("transactions + rules, ALLOW/BLOCK if condition, keyword match
progressing to AND/OR boolean logic"). Neither publishes a verbatim I/O sample, field list, or
exact grammar — the `RULES`/`TRANSACTIONS` stdin protocol, six-field transaction schema, `(rule
k)` output suffix, and Part 3's `ERROR line k:` reporting are this repo's reconstruction, built to
parallel `problems/q12`'s own parse→model→evaluate house style rather than invent a fourth
convention for the same skill.

## Approach by part
1. `RULE_RE` splits `ALLOW|BLOCK if <condition>` per line; Part 1's grammar restricts `<condition>`
   to a single `field == value` comparison via the `part` argument threaded through the parser.
2. Same tokenizer/parser, `part=2` unlocks `!=`, `>`, `<`, `>=`, `<=`, and `field in [v1, v2, ...]`.
   `_compare` reuses q12's own numeric-vs-string fallback rule (both sides int-parseable → compare
   numerically; else compare trimmed strings) so `amount == 0100` matches `amount == 100`.
3. `part=3` unlocks the boolean grammar (`_or` → `_and` → `_not` → `_primary`), giving `not` >
   `and` > `or` precedence for free from the recursion structure itself, and parenthesized
   sub-expressions via `_primary`'s `LP` branch. A rule that fails to tokenize or parse raises
   `RuleError`, caught per-rule so one bad line doesn't take down the batch; only Part 3 surfaces
   it as `ERROR line k: <reason>` (Parts 1/2 silently skip, since the spec's error-handling
   requirement is scoped to Part 3 only).
   Field-vs-literal resolution (`_resolve`) is per-operand, not per-rule: a bare token that names a
   known transaction column (`id`, `amount`, `currency`, `country`, `card_brand`, `merchant`) is
   looked up in the transaction; anything else is a literal string. This is what lets the grammar
   skip quoting entirely (unlike q12's `:field:`/`"const"` markers) while still supporting
   field-vs-field comparisons (`country == country`) without special-casing them.

## Pitfalls hidden tests target
- `(rule k)` line numbers must count every `RULES` line, including later-`ERROR`'d ones — a rule
  after a skipped one does not renumber down
- default (no match) has **no** `(rule k)` suffix at all, distinct from a matched rule at any k
- operator whitespace tolerance (`amount>=5000` vs `amount >= 5000`) — a naive `line.split(" ")`
  parser (the AI-generated failure mode called out in the problem's own "common mistakes" section)
  breaks on the no-space form
- `and` binding tighter than `or`, and `not` binding to only the immediately following unary/primary
  rather than an entire `and`/`or` chain — both are exercised with test cases chosen to disagree
  with the wrong-precedence reading, not just to happen to produce the same answer either way
- `in [...]` as true set membership vs. accidental substring matching (`USA` must not satisfy
  `country in [US]`)
- malformed Part 3 rules (unbalanced parens, missing operand, keyword-as-operand, bad action
  keyword) each produce exactly one `ERROR line k:` and are skipped, not fatal to the run
- 2,000 compiled rules × 20,000 transactions must not re-parse rule text per transaction (rules are
  compiled to an AST once, reused across the whole batch)

## Complexity & measured cost
O(rules) to compile once + O(transactions × matched-rule-position) to evaluate (each transaction
stops at its first matching rule). 2,000 rules / 20,000 transactions (Part 3, worst case: many
rules never match so most transactions scan deep): ~0.3 s, well under the 5 s / 256 MB budget.

## Test inventory
23 tests — part1: 6 (incl. 1 io) · part2: 5 · part3: 12 (incl. 1 io, 1 perf). edge: 14 · fmt: 1 ·
io: 3 · perf: 1.

## Skills exercised
S02 tokenizing/parsing condition strings · S06 numeric-vs-string comparison fallback · S10 ordered
rule evaluation with first-match-wins · S18 validation (per-rule `ERROR` reporting without crashing
the batch) · S19 incremental grammar (each part a strict subset of the next) · S24 Radar rule-engine
vocabulary (shared with q12, at AI-assisted-round scope) · S25 directing/reviewing AI-generated code
