# ps04 Transaction Data Validation / Fraud Report — report

## Summary
Four-stage transaction triage: is the record complete, does it break a hard rule (amount range,
blocked payment method), does it match the user's own history, and — when several things are
wrong — which two to print and in what order. The whole difficulty is state management across a
sectioned stdin protocol (rules/blocklist/profiles/transactions) and getting the priority-and-
truncation rule exactly right in Part 4, not any single algorithm.

## Sources & confidence
High for the four-part shape: a 2025-11-30 LeetCode Discuss write-up (via programhelp) names all
four parts with one-line rules each, including the load-bearing phrases "at least 50% of the
behavioral attributes" (Part 3) and "up to two error codes... maintaining column alignment" (Part
4). interviewdb.io corroborates the question (as two separately-tracked listings, "Data
Validation" and "Fraud Reports") is still active in 2026. The exact input protocol (section
names/order), the profile schema, and the priority order are this repo's reconstruction — no
verbatim I/O sample is available, unlike q03/q05's repo-sourced examples.

## Approach by part
1. `check_row(fields, checks=1, ...)`: any of the 7 trimmed fields empty (including a padded-in
   missing trailing column) -> `MISSING_FIELD`.
2. `checks=2` adds: `Decimal` amount inclusive-range check against `RULES`, and a case-insensitive
   `BLOCKLIST` membership check on `payment_method`. Both evaluated independently of each other
   and of `MISSING_FIELD`.
3. `checks=3` adds a 3-attribute compare against the user's `PROFILES` row (country membership,
   hour-of-day range, profile-specific amount range); `< 2` matches -> `SUSPICIOUS`. No profile
   for the user -> the check is skipped entirely (never flagged).
4. `part4` reuses `checks=3`'s full evaluation, then truncates to `codes[:2]` (already in priority
   order by construction, so no re-sort needed) and column-aligns `txn_id` to the widest id
   actually present in that call.

## Pitfalls hidden tests target
- computing width from a fixed constant instead of the actual batch's longest `txn_id`
- treating "2 of 3 matches" as suspicious (off-by-one on ">= 2" vs "> 2" — 50% of 3 rounds to 2,
  not to "more than half" which would also be 2, so this is subtle only in the code, not the math)
- crashing (or wrongly flagging `AMOUNT_OUT_OF_RANGE`) on a transaction whose `user_id` has no
  profile row when evaluating `SUSPICIOUS`
- re-sorting or deduping the code list before truncating in Part 4 instead of relying on
  insertion order already being priority order
- evaluating Part 3/4's rules under `PART 1`/`PART 2` (the `checks` gate must actually gate)
- float accumulation on money — this solution never touches `float`, only `Decimal`

## Complexity & measured cost
O(n) in transaction count, O(u) in profile count, both single passes with dict lookups (no nested
scans). 100,000 transactions / 2,000 profiles (Part 4, full evaluation): ~0.4 s, ~15 MB RSS
(budget 2 s / 256 MB).

## Test inventory
17 tests — part1: 3 · part2: 3 · part3: 3 · part4: 5 (incl. 1 io, 1 perf, 1 fmt) · plus 1 io test
filed under part1 (empty stdin). edge: 6 · fmt: 1 · io: 2 · perf: 1.

## Skills exercised
S02 sectioned-stdin parsing · S05 inclusive range checks · S06 `Decimal` money · S08 deterministic
ordering · S09 exact column-aligned formatting · S18 validation & prioritized error codes · S19
incremental rule categories (`checks` gate) · S24 domain (fraud triage, distinct from q15's KYC)

## 电面话术：边写边说什么
- 先把优先级和"最多两个错误码"复述给面试官确认："如果一笔交易同时命中三四条规则，Part 4 只保留优先级最高
  的两个，对吗？其余的丢弃，不是合并展示。"——这类"最多 N 个"的截断规则最容易漏测，先确认能省后面返工。
- 设计 `check_row` 时说明为什么用一个 `checks` 整数而不是四个布尔开关："这样 Part n 的语义就是'评估类别
  1..n'，Part 4 复用 Part 3 的判定逻辑，只是输出格式不同——不用为每个 part 重写一遍规则。"
- 讲 SUSPICIOUS 规则时用具体数字过一遍："3 个属性里 ≥2 个匹配才算 OK，也就是 0 或 1 个匹配才 SUSPICIOUS——
  这是'at least 50%'在整数属性个数下的直接写法，不需要算百分比再四舍五入。"
- 遇到"用户没有历史画像怎么办"的追问，主动给出默认假设并说明理由："没有画像就没法比较，我选择不标记
  suspicious——如果面试官希望反过来（没画像更可疑），改一行判断就行，我先按更保守的假设写。"
- 收尾如果还有时间：主动提出加一个 `--part 4` 的列宽在流式场景下如何处理（要不要固定宽度而不是动态计算，
  因为流式场景取不到"最长 id"）——展示对边界条件的延伸思考。
