# Stripe OA drill kit

Self-contained practice kit for Stripe's 60-minute, language-agnostic, multi-part HackerRank
challenge. Everything here is Python 3.11+ / pytest, no third-party deps.

```
catalog/            CATALOG.md — every Stripe OA/phone-screen problem found online, deduped,
                    with sources, confidence, frequency and variants
problems/qNN_slug/  problem.md · starter.py (yours) · solution.py (reference) · test_qNN.py · REPORT.md
skills_matrix.md    test targets / knowledge / experience  ↔  problems  ↔  Stripe JD lines
reports/            OVERALL_REPORT.md (+ per-problem REPORT.md lives next to each problem)
drill.py            60-minute drill runner
conftest.py         shared fixtures (`impl`, `run_script` with time+RSS measurement)
```

## Drill protocol (do this, in this order)

```bash
python drill.py list                # pick one
python drill.py start q01           # prints the WHOLE statement, resets starter.py, starts a 60-min timer
#   ... write your code in problems/q01_*/starter.py ...
python drill.py test q01 -k part1   # lock Part 1 before touching Part 2
python drill.py test q01            # full suite (edge + fmt + perf + io) against YOUR code
python drill.py time q01            # minutes left
python drill.py ref q01             # sanity: reference solution passes everything
```

Rules that mirror the real thing: no debugger (print to **stderr**), stdout must be exact,
read every part before writing a line of code, and keep the first 5 / last 5 minutes for
reading / boundary checks respectively. See `reports/OVERALL_REPORT.md` for the play-book.

## Running the whole kit

```bash
make test          # all reference solutions, all tests
make perf          # only perf tests (time + memory budgets)
make test-starter Q=q01
```
