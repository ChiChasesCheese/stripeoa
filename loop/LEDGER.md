# LEDGER — loop 套件账本（append-only；每任务验收后一行；commit = 检查点）

| 时间 | 任务 | 代理 | 产物 | 测试 | commit | 备注 |
|---|---|---|---|---|---|---|
| 2026-09-01 | T0a cn_forums | sonnet | loop/raw/cn_forums.md（269 行） | — | 0d8fe08 | 1p3a `__NEXT_DATA__` 拿到 10 道题库原题 |
| 2026-09-01 | T3 tree | fable | loop/tree/interview-loop.yaml + check_tree.py | check_tree: 8 rounds/38 skills/33 ids, 0 err | (this) | 84 warn = 目录未建 |
| 2026-09-01 | T0b raw github+official | sonnet | loop/raw/github_repos.md(251) + stripe_official_and_api.md(338) | — | (this) | femisowems repo; Mako #434/#435; stripe-mock |
| 2026-09-01 | T4 mock.py | sonnet+fable | loop/mock.py, loop/tests/test_mock.py, loop/README.md | 22 | (this) | bs 工作区改为整目录减 solution/ |
| 2026-09-01 | T1 CATALOG | fable | loop/CATALOG.md | check_tree --catalog 0 err | (this) | 33 ID + OA 交叉引用 |
| 2026-09-01 | T2 LOOP_GUIDE | fable | loop/LOOP_GUIDE.md | — | (this) | 8 轮 + 总图 + 4 周计划 |
| 2026-09-01 | T7 ps05 | sonnet | loop/rounds/03_phone_screen/ps05_numeronym_validation | 23 | (this) | Part2/3 契约为重建，已标注 |
| 2026-09-01 | T7 ps06 | sonnet | loop/rounds/03_phone_screen/ps06_receivables_registration | 21 | (this) | 周末顺延/坏行规则为重建 |
| 2026-09-01 | T5 ps01 | sonnet | loop/rounds/03_phone_screen/ps01_transaction_stream_levels | 27 | (this) | 滑窗取闭区间 [t-W,t]（来源样例强制） |
| 2026-09-01 | T5 ps02 | sonnet | loop/rounds/03_phone_screen/ps02_shipping_cost_pricing | 21 | (this) | 3 个定死错误串；incremental gap 仅在跨越时报错 |
| 2026-09-01 | T6 ps03 | sonnet | loop/rounds/03_phone_screen/ps03_brace_expansion | 19 | (this) | 与 qA03 区分：保序不去重 |
| 2026-09-01 | T6 ps04 | sonnet | loop/rounds/03_phone_screen/ps04_data_validation_fraud | 17 | (this) | 与 q15 区分：范围/黑名单/行为匹配/优先级 |
| 2026-09-01 | T13 mockserver | sonnet | loop/mockserver/ (maps, payments, _png, tests, README) | 40 | (this) | 纯 stdlib；管线 限流→fail-every→鉴权→路由 |
| 2026-09-01 | T8 ps07 | sonnet | loop/rounds/03_phone_screen/ps07_redact_card_numbers | 27 | (this) | 品牌表 +Discover +MC 2221–2720；原题仅一句话 |
| 2026-09-01 | T8 ps08 | sonnet | loop/rounds/03_phone_screen/ps08_minmax_comparator | 33 | (this) | 四段形状来自 rampatra，schema 为重建 |
| 2026-09-01 | 检查点 B | fable | 03_phone_screen 全 8 题 | pytest 03_phone_screen 全绿 | (this) | Phase 2 完成 |
| 2026-09-01 | T10 cd03 | sonnet | loop/rounds/06_coding_onsite/cd03_account_scheduler_lru | 18 | (this) | LRU tie-break 构造顺序，与 OA q26 区分 |
| 2026-09-01 | T10 cd04 | sonnet | loop/rounds/06_coding_onsite/cd04_rate_limiter_4part | 21 | (this) | 4-part 仅 TOC 可读，规则为重建；毫秒；回拨 clamp |
| 2026-09-01 | T11 cd05 | sonnet | loop/rounds/06_coding_onsite/cd05_business_account_verification | 21 | (this) | 1p3a 原题规格；三处补全已标注 |
| 2026-09-01 | T11 cd06 | sonnet | loop/rounds/06_coding_onsite/cd06_suspicious_users_window | 19 | (this) | 闭区间 [t-60,t]；perf 1.66s@1e6 |
