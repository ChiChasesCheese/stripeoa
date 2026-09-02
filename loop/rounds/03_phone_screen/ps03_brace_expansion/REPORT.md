# ps03 Brace Expansion — report

## Summary
Glob-style `{a,b,c}` template expansion — the same shape as shell filename expansion, webhook
endpoint templates, or price-ID patterns. Stripe's phone-screen version of this progresses
happy-path → malformed input → nesting/multiple groups, in three roughly-15-minute steps, which
maps directly onto this repo's `part1/part2/part3` convention. The one thing to get right before
writing any code: this version preserves order and keeps duplicates — it is **not** the sorted,
deduplicated LC 1087 contract already implemented in `problems/qA03_lc1087_brace_expansion`.

## Sources & confidence
High for Part 1: a verbatim LeetCode Discuss report (Bangalore backend screen, 2024-06) gives the
exact three example patterns used here, plus the follow-up wording almost verbatim ("handle
incomplete/mismatched brackets, fewer than 2 comma-separated values, or no brackets at all —
return string as-is"; "nested brackets"). interviewdb.io and hackerprep.io corroborate the
question is still active in the 2026 rotation. Parts 2/3's exact malformed-detection scope (what
counts as "in scope" for Part 2 vs. Part 3) and the output serialization are this repo's own
reconstruction — the source describes returned lists, not stdout format.

## Approach by part
1. **Segment + cartesian-product engine** (`_expand`): scan the pattern left to right; each
   `{...}` group becomes a "segment" whose options are the (recursively expanded) comma-separated
   alternatives; literal runs are single-option segments. The final result is the cartesian
   product of all segments, left segment as the outer loop — this one function handles a bare
   literal, a single group, multiple groups, and arbitrary nesting without special-casing any of
   them, because they are all "some segments, expand and multiply."
2. **Part 2 malformed check** (`_validate_single`): single linear scan tracking brace depth and a
   per-group token count; flags unmatched braces, a second top-level group, a nested `{`, or a
   group with `< 2` tokens. Deliberately narrower than Part 3's grammar (rejects nesting and
   multiple groups too) so that Part 3 is a real, testable capability increase rather than a
   no-op.
3. **Part 3 malformed check** (`_validate`): the same idea, generalized recursively — a group's
   alternatives are validated by re-invoking `_validate` on each one, so a `< 2`-token group
   buried three levels deep still invalidates the whole pattern.

## Pitfalls hidden tests target
- reaching for `sorted(set(...))` out of LC-1087 muscle memory — breaks order and multiplicity
- treating "malformed" narrowly (only unmatched braces) and missing the `< 2` tokens case or the
  "second group is out of Part 2's scope" case
- getting the cartesian-product order backwards (`a1,b1,a2,b2` instead of the bash-compatible
  `a1,a2,b1,b2`) — easy to get wrong if the loops are nested in the wrong direction
- forgetting empty tokens are valid (`{,x}`, `read.txt{,.bak}`) and filtering them out
- validating only the top-level group's token count in Part 3 and missing a nested violation

## Complexity & measured cost
`_expand` is O(output size) — each segment's options are produced once and combined by the
cartesian product, so cost scales with the number of expansions actually produced, not with any
redundant re-scanning. `_validate`/`_validate_single` are O(pattern length), one linear pass (plus
one recursive call per nested group in `_validate`, still linear overall since groups don't
overlap). 10,000 patterns (1-3 groups of 2-4 tokens each, `/seg{...}` repeated): ~0.05 s, well
under the budget.

## Test inventory
20 tests — part1: 5 (incl. 1 io, 1 fmt) · part2: 5 · part3: 8 (incl. 1 io, 1 perf) · plus the
empty-stdin io test filed under part1. edge: 8 · fmt: 1 · io: 2 · perf: 1.

## Skills exercised
S02 parsing (brace/segment scanning) · S14 order-preserving, non-deduplicating output · S18 input
validation without exceptions · S19 incremental design (Part 2's scope is deliberately narrower
than Part 3's) · S21 recursion / cartesian product

## 电面话术：边写边说什么
- 读题时先复述边界条件给面试官听："所以顺序要保留、重复要保留，对吗？不是 LeetCode 1087 那种排序去重。"——
  确认这一点能避免写完才发现方向反了。
- Part 1 写的时候说明设计选择："我打算把字面量段和分组段都看成'segment'，最后统一做笛卡尔积——这样待会儿
  Part 3 的多组/嵌套本质上是同一段代码，不用重写。"——提前给出可扩展性的信号。
- Part 2 遇到"要不要支持嵌套/多组"的问题时主动说清楚："我把 Part 2 的'合法'范围定义为最多一组、不嵌套，
  超出这个范围的输入按'畸形'处理、原样返回——这样 Part 3 才是一次真正新增的能力，而不是没做事。"
- Part 3 讲嵌套语义时用具体例子过一遍："`{a,{b,c}}d` 里外层的第一个选项是字面量 `a`，第二个选项本身是个组
  `{b,c}`——我对每个选项递归调用同一个展开函数，展开完拼接顺序不变。"
- 如果时间只够做完 Part 2：主动提出"如果还有时间，我会怎么扩展到嵌套"，说出笛卡尔积的思路，即使没时间写代码，
  这在面试官反馈里往往被算作"沟通清晰"的加分项。
