# ps10 · RBAC Role Resolver

**类型：** Phone Screen（Technical Screen）· **阶段：** Technical Screen（电面）· **最近一次报告：** PracHub 2026-05-12 · **频率：** PracHub 与 1point3acres 两个独立站点各收录一道"账户层级 + 角色/权限解析"题，标题不完全相同但主题一致（PracHub: "Resolve User Roles Across Account Hierarchy"；1point3acres: "RBAC Role Resolver"）· **置信度：** low — 仅确认题目存在（标题级 + 一句话 Quick Overview），规则文本、输入输出格式、part 划分、覆盖优先级全部未公开，本题是**重建题**（见下方警示块与 Sources）。

> ⚠️ **重建题（非真题）**：本题面是根据 PracHub「Resolve User Roles Across Account Hierarchy」
> （2026-05-12，仅有一句话 Quick Overview 摘要）与 1point3acres「RBAC Role Resolver」（仅标题级
> 线索）**自拟**的训练题。
> 真实题面从未公开——规则、输入格式、输出格式、part 划分**全部是本仓库编的**。
> 练它是为了覆盖 **S03、S18、S08、S19**，**不要把这里的输出格式当成真题格式**去背。

## Context
Stripe's platform accounts sit above a hierarchy of connected accounts (a platform's users manage
one or more connected accounts, and a connected account can itself have sub-accounts). A single
user can hold different roles at different levels of that hierarchy — a support engineer might be
a read-only `viewer` on the whole platform but a full `admin` on one specific connected account
they're actively investigating. Given the account tree, a set of named roles, and which user holds
which role at which account, you need to resolve what a user can *actually* do at a given account
— accounting for inheritance up the chain, wildcard grants, and explicit denies that must never be
silently overridden by a broader grant.

## Input
`accounts`: a list of `{account_id, parent_id}` (a root account, e.g. a platform account, has
`parent_id = None`). `roles`: a list of `{role_id, permissions}` where `permissions` is a list of
permission strings. `assignments`: a list of `{user_id, account_id, role_id}` — a user may hold at
most **one** role at any single account (holding different roles at different accounts is normal
and expected). A permission string is one of: a literal permission (`"charges:read"`), a namespace
wildcard (`"charges:*"`, matching any `"charges:..."` permission), the global wildcard (`"*"`,
matching everything), or any of the above prefixed with `!` to mean an **explicit deny**
(`"!charges:refund"`, `"!charges:*"`). Wildcards and denies only appear starting Part 3 — Part 1
and Part 2's role data is always literal, non-prefixed permission strings.

## Rules

### Part 1 — direct role, no hierarchy
Return the sorted permissions of the role `user_id` is **directly** assigned at `account_id`
itself — `[]` if the user has no role there. Do not look at ancestors yet. Assume the input is
well-formed (no validation required in this part).

### Part 2 — hierarchy inheritance (union)
Accounts now form a tree via `parent_id`. A user's effective permissions at `account_id` are the
**union** of the permissions granted by every role the user holds anywhere along the chain from
the topmost ancestor down to `account_id` itself (a level where the user holds no role there
simply contributes nothing). Inheritance is additive only in this part — a role at a closer level
never removes a permission granted by a role at a farther level; there are no denies yet. Return
the sorted union.
**Validate** (raise `ValueError` — a clear message is enough, exact wording is not tested):
a duplicate `account_id` or `role_id` in the input; an assignment naming an unknown `account_id`
or `role_id`; two assignments for the same `(user_id, account_id)` pair; an `account_id` anywhere
in the ancestor chain that isn't in `accounts`; or a `parent_id` cycle (including an account that
is its own parent). A cycle must be **detected and rejected**, never walked forever.

### Part 3 — wildcards and deny-overrides-allow
`permissions` may now include namespace/global wildcards and `!`-prefixed denies (see Input).
Given a single `permission` string to check, return whether `user_id` effectively has it at
`account_id`. **Decided rule** (this repo's own choice — not derivable from the source, see
Sources): an explicit deny **anywhere** in the ancestor chain wins over a grant from **any**
level, including a grant at a level *closer* to `account_id` than the deny. This is
deny-overrides-allow **globally**, not "the nearest scope to the account wins" — the two rules
agree whenever the deny happens to be the closer one, but they disagree (and this problem tests
that disagreement) when the closer level grants and a farther ancestor denies. Same validation
and cycle detection as Part 2.

### Part 4 — batch resolution
Given a list of `(user_id, account_id, permission)` queries (the same pair may repeat with
different permissions, and different users may query the same account), return one bool per query
in the same order, using the same rule as Part 3. The queries must be answered **without
re-walking the same account's ancestor chain, or re-aggregating the same `(user_id, account_id)`
pair's grants/denies, once it has already been done earlier in the same batch** — a large account
tree with many users checking permissions is the normal case, not a corner case.

## Why later parts break earlier assumptions
This progression is deliberately not just "add more rules" — each part invalidates a structural
choice a straightforward Part-N implementation would make:
- **Part 1 -> Part 2**: a Part 1 solution can get away with a flat, one-shot scan over
  `assignments` (no indexing, no tree at all). Part 2 makes that insufficient — you now need an
  indexed graph walk with cycle protection, not a bigger scan.
- **Part 2 -> Part 3**: Part 2's natural return shape is "the fully resolved, enumerable list of
  granted permissions." Wildcards break that representation outright — `"*"` cannot be expanded
  into a concrete list without knowing every permission string that could ever be checked. Part 3
  forces you to keep raw grant/deny *patterns* and match one queried permission against them on
  demand, instead of materializing a list up front.
- **Part 3 -> Part 4**: Part 3's per-query chain walk is correct but, run once per query in a
  batch, it repeats the same ancestor-chain walk and the same per-user aggregation many times over
  for accounts and users that reappear across queries. Part 4 forces caching both the resolved
  ancestor chain (per `account_id`) and the resolved grants/denies (per `(user_id, account_id)`
  pair) across the whole batch.

## Worked examples
Shared setup:
```
accounts: platform (root) -> connected (parent: platform) -> submerchant (parent: connected)
roles:
  viewer: [payouts:read, charges:read]
  admin:  [charges:read, charges:write, payouts:read, payouts:write]
assignments:
  alice @ platform  -> viewer
  alice @ connected -> admin
  bob   @ submerchant -> viewer
```
- `part1(..., "alice", "connected")` -> `["charges:read","charges:write","payouts:read","payouts:write"]`
  (alice's own role at connected, no inheritance needed)
- `part1(..., "alice", "submerchant")` -> `[]` (alice has no role AT submerchant itself; Part 1
  never looks at ancestors)
- `part2(..., "alice", "submerchant")` -> `["charges:read","charges:write","payouts:read","payouts:write"]`
  (nothing at submerchant itself, but union of viewer@platform + admin@connected reaches down to it)
- `part2(..., "bob", "submerchant")` -> `["charges:read","payouts:read"]` (bob has no assignment at
  connected or platform — only his own submerchant-level viewer role applies)

Add for Part 3:
```
roles += support: [charges:*, !charges:refund]
assignments += dave @ connected -> support
```
- `part3(..., "dave", "submerchant", "charges:read")` -> `True` (wildcard `charges:*` inherited
  from connected)
- `part3(..., "dave", "submerchant", "charges:refund")` -> `False` (the explicit deny at the SAME
  level as the wildcard wins)

Now the rule that actually distinguishes "deny wins globally" from "nearest level wins":
```
roles: grant_close: [charges:read]   deny_far: [!charges:read]
assignments: erin @ submerchant -> grant_close   erin @ platform -> deny_far
```
- `part3(..., "erin", "submerchant", "charges:read")` -> `False` — the grant is at the *closer*
  level (submerchant) and the deny is *farther away* (platform), and deny still wins. Under a
  "nearest scope wins" rule this would instead be `True`; this problem's decided rule is the
  opposite, and this is the example to reach for if a follow-up asks "why not nearest-wins?"

## Edge cases
- a user with no role anywhere in the chain: Part 1/2 return `[]`, Part 3/4 return `False`
  (default deny, not an error — a real user simply having no access is normal)
- `account_id` unknown to the system (not in `accounts`, referenced only by a query or by another
  account's `parent_id`) -> `ValueError`, from Part 2 onward
- `user_id` unknown to the system (never appears in `assignments`) -> **not** an error, just no
  effective permissions anywhere — this asymmetry (bad account = error, unknown user = normal) is
  deliberate and tested
- a two-node cycle (`x`'s parent is `y`, `y`'s parent is `x`) and a one-node cycle (`x` is its own
  parent) both must raise `ValueError`, not recurse forever
- the same permission granted at two different levels in the chain is still listed once (Part 2's
  union, not concatenation)
- a wildcard like `"charges:*"` must not match the bare string `"charges"` (no colon, nothing
  after it) — only `"charges:something"`
- deny beats grant even when the grant is a more specific/narrower pattern and the deny is a
  broader wildcard at a farther level (or vice versa) — specificity never matters, only "was there
  any matching deny anywhere in the chain"
- Part 4: the same `(user_id, account_id)` pair queried for many different permissions must give
  answers consistent with calling Part 3 once per query — caching must never change the answer,
  only the speed
- Part 4: a batch large enough that re-walking a deep ancestor chain once per query (instead of
  once per distinct account/pair) would blow the time budget

## What this tests
skills: S03 record modeling (accounts/roles/assignments as small dicts, indexed by id) · S08
deterministic sorting (permission lists sorted, ties never left to insertion order) · S18
validation and error paths (unknown references, duplicate assignments, cycle detection, and the
deliberate unknown-account-vs-unknown-user asymmetry) · S19 layered/incremental design (each part
forces a genuine representation change, not just a bigger rule set — see "Why later parts break
earlier assumptions" above)

## Sources
- https://www.1point3acres.com/interview/problems/post/7100148（标题 "RBAC Role Resolver"，访问
  日期 2026-09-03）——仅确认标题存在（多次独立 WebSearch 命中同一 URL）；1point3acres 全站对未登录
  请求返回 403，正文从未被抓取到。搜索引擎自带的"design and implement a Role-Based Access Control
  (RBAC) system..."描述被判定为**搜索引擎的泛化释义**（措辞与教科书式 RBAC 介绍高度雷同，且该描述
  本身承认"完整内容未被抓到"），本题**不采信**这段描述作为规则来源。
- https://prachub.com/coding-questions/resolve-user-roles-across-account-hierarchy（访问日期
  2026-09-03）——PracHub 自动生成的 Quick Overview 摘要："This question evaluates understanding of
  hierarchical data structures, role-based access control semantics, and set/map operations for
  computing effective permissions across account ancestors."正文因登录墙/异步加载多次重试均未获取
  到。发布信息：Software Engineer / Coding & Algorithms / Medium / **Technical Screen (Phone)** /
  2026-05-12。
- https://www.interviewdb.io/question/stripe/user-roles（访问日期 2026-09-03）——页面 `<title>`
  确认"User Roles"这个标题独立存在，正文未加载（占位符）。
- https://www.interviewdb.io/question/stripe/rbac-role-resolver（访问日期 2026-09-03）——该 slug
  不存在独立页面，请求被重定向到通用列表页——证明"RBAC Role Resolver"这个具体标题只在
  1point3acres 出现，不是 interviewdb 的独立词条。
- `catalog/discovery/2026-09/C_batchA.md` `## C6` 一节（本仓库 2026-09-03 的二轮排查记录，含完整
  检索方法与失败检索式列表）。
- **本题面自拟的部分（即全部规则/格式细节）**：账户层级的具体字段名（`account_id`/`parent_id`）、
  角色权限的字符串格式（含通配符 `*`/`ns:*` 与显式拒绝 `!perm`）、"deny 全局优先于 grant"这条覆盖
  规则、4 个 part 的具体划分与递进方式、输入输出的 stdin 协议、以及全部 worked examples 中的具体
  数值——两份原始来源都只给出了"账户层级 + 角色/权限解析"这个主题级描述，没有任何一处规则文本、
  样例数据或函数签名，因此以上全部内容都是本仓库为覆盖 S03/S08/S18/S19 而设计，不是任何逐字转录。
