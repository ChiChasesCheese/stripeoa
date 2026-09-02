# loop/ 进度断点 — 2026-09-01（会话 2）

> OA 之后整套面试流程的 mock 套件。分支 `worktree-stripe-loop`，worktree `/Users/chizhang/Code/ITV/stripe-oa/.claude/worktrees/stripe-loop/`。
> **以 git + `loop/LEDGER.md`（账本）+ `loop/tasks/todo.md`（任务清单）为准**；本文件只是入口。

## 工作方式（用户约定）
- 编排/理解 = 主会话 Fable 5.1；产出 = `sonnet` 子代理；**并行 ≤ 5**；每代理只写自己名下目录（原子更新）；协调者验收 → commit → LEDGER 一行。
- 材料中文，专有名词/代码英文；密度优先，禁水文；不动 `catalog/`、`problems/`。
- `catalog/CATALOG.md` 与 `loop/study/00-prereq/exercises/ex02_structure.py` 有用户侧未提交改动：**不动、不提交**。

## 状态（详见 tasks/todo.md）
- [x] Phase 0 raw 6/6（en/cn/hr_hm/system_design/github/official）
- [x] Phase 1：T1 CATALOG（33 ID）· T2 LOOP_GUIDE · T3 tree.yaml + check_tree.py —— **检查点 A 达成**
- [~] Phase 2：T4 mock.py ✓ · T7 ps05/06 ✓ · T5 ps01/02、T6 ps03/04、T8 ps07/08 进行中
- [~] Phase 3：T13 mockserver、T9 cd01/02 进行中；待启动 T10 cd03/04、T11 cd05/06、T12 cd07+bs01/02、T14 int01/02（T13 后）
- [ ] Phase 4：T15 int03/04 · T17 bs03–05 · T18 sd01–06 · T19 rc/hm/bq · T21 study/10-rounds 01–04
- [ ] Phase 5：T22 10-rounds 05–08 · T23 20-cards · T20 TREE.md · T24 README/INDEX · T25 review + 全量测试

## 下一会话怎么接
1. `cd` 到 worktree，`git log --oneline -15` + `cat loop/LEDGER.md` 看已落盘的；`git status` 看是否有代理写了一半没提交的目录（有则跑其测试，绿就提交）。
2. 按 `loop/tasks/todo.md` 未勾选项，每次最多 5 个 sonnet 代理并行，任务书模板见本会话已用的（读 CONVENTIONS + 范例 + raw 行号 + 定死 I/O + 验证命令 + 只写自己目录 + 返回 LEDGER 行）。
3. 每收一份：`rtk proxy python3 -m pytest <dir> -q` 绿、`IMPL=starter` 红、`git status` 无越界 → commit → LEDGER。
4. 配额将近：先更新本文件 + LEDGER 并 commit，再停。
