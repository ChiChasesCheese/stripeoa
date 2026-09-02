# loop/ 进度断点 — 2026-09-01

> 这是 OA 之后整套面试流程（recruiter → HM → 电面 → onsite：bug squash / integration / coding / system design → behavioral）的 mock 面试套件。
> 若会话中断，从这里继续。分支：`worktree-stripe-loop`。
> worktree：`/Users/chizhang/Code/ITV/stripe-oa/.claude/worktrees/stripe-loop/`

## 顺序（用户要求）
1. 尽调（中英文论坛 + GitHub + 官方）→ `catalog/raw/loop/*.md`
2. 汇总 → `loop/CATALOG.md`、`loop/LOOP_GUIDE.md`
3. 知识树 → `loop/tree/interview-loop.yaml` + `loop/tree/TREE.md`
4. 环境 → `loop/rounds/<round>/<id>/`，`loop/mock.py`
5. 解答/测试（TDD）→ 全绿
6. 学习材料 → `loop/study/`（前置课、每轮准备模版、卡片）

## 约束（用户后来纠正）
- Python LeetCode 已刷 ~1300 题；缺的是工作向框架、parse、LLD，不是语法入门。前置课要高密度，禁止水文。
- 子代理最多 **2 个**，**串行**执行。不要一次 fan-out 6 路（会打爆 session limit）。
- 材料中文；专有名词和代码可英文。

## 状态
- [x] 目录骨架
- [x] 尽调 3/6 raw（rewind 后已从会话恢复并入库）
  - 有：`catalog/raw/loop/en_forums.md`、`hr_hm_behavioral.md`、`system_design.md`
  - 缺：`cn_forums.md`、`github_repos.md`、`stripe_official_and_api.md`（对应子代理当时撞上 session limit，文件没写成；transcript 还在 `~/.claude/projects/-Users-chizhang-Code-ITV-stripe-oa--claude-worktrees-stripe-loop/`）
- [ ] CATALOG / LOOP_GUIDE
- [ ] 知识树
- [ ] rounds 环境 + mock.py
- [ ] TDD 解答
- [x] study 00-prereq 第 01–06 章 + ex01/ex02 骨架（ex01 用户已作答，5 测全绿；ex02 仍是 TODO stub，参考答案 4 绿）
- [ ] study：10-rounds · 20-cards

## 下一会话怎么接 Claude 进度

`/rewind` **没有 redo**。对话 UI 回不去 rewind 之前，但磁盘进度以本文件 + git 为准。

1. 在 worktree 里开 Claude：  
   `cd /Users/chizhang/Code/ITV/stripe-oa/.claude/worktrees/stripe-loop && claude`
2. 可选：`/resume` 选 session `bdcd361b-987b-4794-9260-bc3363b3d48b`（jsonl 还在，但 rewind 后模型看到的上下文可能已截断）。更稳的是 **新开会话**，把本 CHECKPOINT 丢给它。
3. 下一刀（串行，最多 2 个 subagent）：补 3 份缺失 raw → 再写 `loop/CATALOG.md` + `loop/LOOP_GUIDE.md`。不要重写已有的 3 份 raw 和 00-prereq。
4. 配额将近时先更新本文件并 commit，再停。
