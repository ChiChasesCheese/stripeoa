# bs01 minimako (Mako-style template engine) — report

## Summary
A ~350-line Mako-style template engine (`lexer.py` → `ast.py` → `compiler.py`'s visitor-pattern
renderer, plus a `TemplateLookup`/`Template` pair for loading templates by URI and resolving
`<%include>`) with two independent, real-pattern bugs injected: a missing visitor method
(`visit_IncludeNode`), and a path-traversal bug from two URI-normalization functions that should
agree but don't. Both map directly to Stripe's own reported Mako bug-squash material ("path
handling validation, AST node traversal edge cases") and to real, historical Mako CVEs.

## Sources & confidence
High for "Mako is a reported Stripe bug-squash repo, with bugs in path handling and AST
traversal": `loop/raw/en_forums.md` §4.2 ("Python | **Mako**（模板引擎；'Python + Mako; no
hints'；bug 涉及 path handling validation、AST node traversal edge cases）", sourced from
programhelp VO 2025-08-07, linkjob technical 2025-12-08, staffengprep "Mako parser bug squash").
High for the specific real bugs used as templates: `sqlalchemy/mako` issue #434 ("slash handling
issue in template URI normalization", fixed in commit `e05ac61`, 2026-04-14) — root cause exactly
as described in `loop/raw/github_repos.md` §2.2: `Template.__init__` strips a single leading
slash while `TemplateLookup.get_template()` strips all of them, letting a URI like
`"//../../secret.txt"` bypass the directory-traversal check; fix diff is 1 line. The missing-
visitor bug pattern ("missing visitor function for an AST node type → runtime error") is named
directly in `en_forums.md`'s Exponent grading notes (line 167) as a known Mako bug-squash failure
mode, alongside "missing directory-path check" (the second bug here). Medium for this repo's exact
module layout (`lexer.py`/`ast.py`/`compiler.py`/`lookup.py`/`template.py` as five separate files)
— no source specifies real Mako's actual file boundaries; this repo's split is a reconstruction
chosen to make the two bugs land in cleanly separable, independently testable files.

## Bugs injected
1. **`compiler.py`: `visit_IncludeNode` missing.** `Compiler.visit()` dispatches by
   `type(node).__name__` to `visit_<Name>`; five of six node types have one, `IncludeNode` does
   not. Rendering any template containing `<%include file="..."/>` raises `AttributeError`
   instead of inlining the child template. Real-pattern match: Exponent's Mako bug-squash grading
   notes name exactly this failure mode ("missing visitor function for an AST node type → runtime
   error").
2. **`template.py`: `Template.resolve_include()` strips only one leading slash; `lookup.py`:
   `TemplateLookup.get_template()` strips all of them.** The discrepancy lets a `file` value with
   2+ leading slashes (e.g. `"//" + absolute_path_to_a_file`) survive `resolve_include`'s
   normalization with one slash intact, which `os.path.join(source_dir, "/abs/path")` then treats
   as absolute — discarding `source_dir` entirely and reading a file completely outside the
   template's own directory. Real-pattern match: `sqlalchemy/mako` issue #434 / commit `e05ac61`,
   nearly verbatim (same root cause, same fix shape: `x[1:] if x.startswith("/") else x` →
   `x.lstrip("/")`).

## Debugging path (from a failing assertion to the fix)
- Run `pytest tests -q`: 2 of 17 fail.
- `test_render_template_with_include_inlines_child_template` fails with `AttributeError: Compiler
  has no visitor for node type 'IncludeNode' (expected a method named 'visit_IncludeNode')`,
  raised from `Compiler.visit()`. Reading `compiler.py` top to bottom shows five `visit_*` methods
  (`visit_TemplateNode`, `visit_TextNode`, `visit_ExpressionNode`, `visit_IfNode`,
  `visit_ForNode`) and a comment where the sixth should be — the method is simply absent. Fix:
  add `visit_IncludeNode`, pattern-matched on `visit_ForNode`'s shape (resolve something, build a
  child `Compiler`, render, return the string).
- `test_resolve_include_rejects_path_traversal_payload` fails with `Failed: DID NOT RAISE
  <class 'LookupError'>` — the test calls `Template.resolve_include()` **directly**, bypassing
  `render()`/`Compiler` entirely, so it fails independently of bug 1 (this is deliberate: it
  isolates bug 2 so a candidate who fixes only bug 1 still sees exactly one remaining failure,
  not zero). Reading `resolve_include()` shows `file[1:] if file.startswith("/") else file`;
  comparing against `lookup.py`'s `uri.lstrip("/")` (used by the always-safe top-level
  `TemplateLookup.get_template()`) shows the mismatch. Fix: one line, `file.lstrip("/")`.

## Minimal fix
`solution/FIX.patch` — 2 files, +7/-6 lines total (one new 4-line method in `compiler.py`; one
changed line + updated comment in `template.py`). Verified: `git apply solution/FIX.patch` against
a clean copy → all 17 tests pass.

## Real library correspondence
- Bug 1 (missing visitor): pattern named in `en_forums.md`'s Exponent Mako grading notes
  ("missing visitor function for an AST node type → runtime error"); not tied to one specific
  Mako issue number (this repo's `Compiler`/AST-visitor design is a simplification — real Mako
  compiles templates to Python source rather than tree-walking an AST at render time).
- Bug 2 (path traversal): https://github.com/sqlalchemy/mako/issues/434, fixed by commit
  https://github.com/sqlalchemy/mako/commit/e05ac61989a7fb9dd7dcde6cfd72dc48328719a3 (2026-04-14).
  The sibling issue #435 (backslash handling on Windows, CVE-2026-44307, commit `72e10c5`) is the
  same bug family but not reproduced here (this fixture is POSIX-path-only; no `posixpath`-vs-
  `os.path` split to exploit on a single-OS test suite).

## 面试官评分看什么
- Did the candidate actually run the tests first, or start reading/editing code blind?
- Root-cause each failure from its traceback/assertion, not by guessing-and-checking edits.
- Fix size stays proportional to the bug (bug 1: one new method; bug 2: one changed line) — a
  candidate who ends up touching the tokenizer, the parser, or `TemplateLookup` itself has gone
  looking for a bug that isn't there.
- Notices (even without being asked) that bug 2 is a *security* bug, not just a functional one —
  articulating "this lets you read files outside the template directory" is worth more than
  silently patching the string operation.
- For bug 2 specifically: understands *why* `os.path.join(base, "/abs/path")` discards `base`
  (Python's own documented `os.path.join` semantics), not just "adding `.lstrip` made the test
  pass" — this is the same mechanism as the real Mako CVE, and a candidate who can explain it has
  understood the bug, not pattern-matched the diff.

## 常见跑偏
- Rewriting `Compiler.visit()`'s dispatch mechanism (e.g. switching to a `dict` of node-type →
  handler) instead of just adding the missing method — functionally equivalent but a much larger,
  riskier diff for a 60-minute round, and it obscures that the *actual* bug is "one method is
  missing", not "the dispatch design is wrong".
- Fixing bug 2 by adding an `os.path.realpath` containment check (copying `lookup.py`'s full
  safety net) instead of just matching `lookup.py`'s normalization (`lstrip("/")`) — not wrong,
  but over-scoped for what the failing test actually requires; `solution/NOTES.md` addresses this
  directly as an acceptable-but-not-required "if a candidate raises it" discussion point.
- Editing `test_minimako.py` to make the two failures go away (e.g. relaxing the `pytest.raises`
  assertion, or deleting the include-rendering test) instead of fixing `src/minimako/` — the tests
  are the spec here; changing them defeats the exercise.
- Trying to "fix" `TemplateLookup.get_template()` — it is already correct (strips all leading
  slashes, has the `realpath` containment check); the bug is in `Template.resolve_include()`'s
  *separate*, independently-normalized code path, not in the lookup.

## Test inventory
17 tests, plain pytest (no `partN` markers — bug-squash rounds are single-scenario, not
multi-part). 15 pass as shipped; 2 fail, each isolating one bug
(`test_render_template_with_include_inlines_child_template` → bug 1;
`test_resolve_include_rejects_path_traversal_payload` → bug 2). After `git apply
solution/FIX.patch`: 17/17 pass.

## Skills exercised
S12 tree-walking interpreter / visitor pattern · S13 recursive-descent-over-tokens parsing ·
S18 path-traversal validation (matching two normalization functions) · S20 root-causing from a
traceback/failing assertion rather than guess-and-check · S24 real-open-source-bug pattern
matching (Mako path-handling CVE family)
