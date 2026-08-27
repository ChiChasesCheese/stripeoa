# Adversarial review findings (part 2)

Scope: q06, q07, q08, q10, q17, q18. Reviewer: Claude (adversarial pass). Date: 2026-08-26.

Severity: high = wrong answer on a valid input; medium = spec ambiguity that could flip a hidden test; low = style/clarity.
Method per problem: independent brute-force oracle written from problem.md, >= 2000 random cases (`random.Random(2)`), every edge case in problem.md, stdin/stdout worked examples byte-for-byte, the suite on the empty starter, and timing at 10^4 / 10^5 lines. Throwaway scripts live under `~/.claude/jobs/86efc7a0/tmp/review2/`.
