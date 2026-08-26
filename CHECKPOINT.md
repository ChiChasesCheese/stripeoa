# Progress checkpoint — updated 2026-08-26 (resume from here)

## Status 2026-08-26
Green (tests pass, REPORT.md present): q01 q02 q03 q04 q07 q09 q10 q11 q12 q14 q21 q25
Green, REPORT missing: q13 · 1 failing test + no REPORT: q05
In flight (3 resumed agents): q05→q06→q08 · q13 REPORT→q16 · q17→q18→q19→q15
Next batches: q20 q22 q23 q24 · q26 q27 q28 q29(deployment windows) · new finds q30–q36 (Stripe Capital loans,
wishlist/mutual rank, money transfer rebalancing, analytical DB min_by_key, compress URL, user points FIFO,
MultiTimeMap) · algo set qA01–qA11 · CATALOG merge agent · OVERALL_REPORT

## Done (committed) — earlier snapshot
- Skeleton: `conftest.py` (impl / run_script fixtures with time+RSS), `drill.py`, `Makefile`, `pytest.ini`, `CONVENTIONS.md`, `README.md`, `catalog/IMPLEMENTATION_BRIEF.md`
- Research raw files in `catalog/raw/` (all five; en_forums / github_repos / algo_questions were cut off mid-write and are PARTIAL but usable):
  cn_sources.md (24 OA + 17 phone problems) · process_and_jd.md (format, loop, JD skills, glossary, 24 test targets S01–S24) · en_forums.md · github_repos.md (1005 lines, verbatim repo statements/tests) · algo_questions.md (LC/algo frequency table)
- Problem sets and test status (`rtk proxy python3 -m pytest problems/<dir> -o addopts="" -q`):

| dir | status |
|---|---|
| q01_fraud_mcc_disputes | 21 pass, REPORT.md done |
| q03_chat_billing | 20 pass, REPORT.md done (exemplar) |
| q04_card_range_obfuscation | 24 pass, REPORT.md missing |
| q07_subscription_notifications | 3 FAIL / 20 pass (agent was mid-fix), REPORT.md missing |
| q09_jupyter_load_balancer | 24 pass, REPORT.md missing |
| q10_payment_intent_commands | 24 pass, REPORT.md missing |
| q14_join_dataset | problem.md + solution.py only; no starter.py, no tests |
| q21_currency_conversion | 19 pass, REPORT.md missing |
| q25_invoice_reconciliation | 19 pass, REPORT.md missing |

## Not started (assigned slugs — keep them)
q02_merchant_fraud_score · q05_card_validation_luhn · q06_atlas_company_name · q08_store_closing_penalty ·
q11_subscription_database · q12_platform_balance_radar_rules · q13_account_balance_ledger ·
q15_kyc_verification · q16_chargeback_parsing · q17_datacenter_router_haversine · q18_collusion_ring ·
q19_accept_language · q20_transaction_fees_reconciliation · q22_shipping_cost · q23_rate_limiter ·
q24_server_allocator · q26_account_scheduler_lru · q27_payment_ledger · q28_worker_task_assignment ·
algo/LC set `qA01…` (from catalog/raw/algo_questions.md)

## Resume plan (constraint: max 3 subagents at a time)
1. Fix q07 (3 failing tests), finish q14 (starter + tests), write missing REPORT.md ×6 — 1 agent.
2. Remaining bespoke problems in batches of 3 agents × 3–4 problems each, using
   `catalog/IMPLEMENTATION_BRIEF.md` prompts (the original per-batch prompts are in this job's transcript;
   the brief + cn_sources.md sections are sufficient to regenerate them).
3. Algo/LC set from algo_questions.md (one agent).
4. Coordinator: `catalog/CATALOG.md` (dedup table: title · type bespoke/algo · stage · #refs · URLs · year ·
   confidence · problem dir), `skills_matrix.md` (S01–S24 ↔ problems ↔ JD lines), `reports/OVERALL_REPORT.md`,
   then `make test` green, commit, publish report artifact.
