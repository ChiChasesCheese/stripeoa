# 接力断点 — 2026-09-03（会话 3）

> **这个文件的唯一目的：让下一个会话在零上下文的情况下接着干，不重复劳动、不丢结论。**
> 权威顺序：git 历史 > 本文件 > `loop/CHECKPOINT.md` > `loop/tasks/todo.md`。
> 分支 `claude/phone-interview-vo-difference-nr8kjn`，PR #3。

---

## 0. 一句话现状

题库本体已完成并可用（92 道题、check_tree 零告警）；**当前正在做的是"全网尽调第三轮"**，
目标是把撞题率做到 80%，或做到题型自包含。第三轮的四路里三路已回并落盘，**第四路（Reddit + HN）在跑**。

---

## 1. 已完成（不要重做）

### 题库本体
- **92 道可练题**：53 `problems/` + 39 `loop/rounds/`
- `check_tree.py`：**errors=0 warnings=0**
- `pytest problems` 1033 绿 / 1 红 · `pytest loop`（除 bug squash + prereq）714 绿 / 1 红
- **两条红都是 perf 预算且本分支开工前就红**：`q07::test_perf_100k`（单独跑也红，3.4s vs 2.0s）、
  `cd06::test_perf_1m_rows`（**单独跑是绿的**，只在全量并跑时被 CPU 争用挤超时）。
  **没有放宽任何预算**，也不要去放宽——预算按开发机定的。
- `loop/study/00-prereq/exercises/test_ex02.py` 的 3 红是**用户自己的作答文件**（满篇 `# TODO`），红是正常状态。

### 本轮新建
- 题：`ps09`–`ps13` · `q41` · `cd08`–`cd10`（Bitfont 三版本）· `int04` 收尾 · `sd01`–`sd06` · `bs02`–`bs05`
- 轮次题库：`01_recruiter`(14) / `02_hm`(30) / `08_behavioral`(50)，去重 66 题
- 学习材料：`DEBUG_101.md`（调试入门，实录真跑）· 20-cards 四份 224 张 · 30-articles 补 19 篇（共 38 篇 → 185 张 Anki 卡）· `study/10-rounds` 八章
- 技能：**S25 二进制帧解码**（附证据强度说明，JD 列故意留空）
- 工具：`drill.py status` / `mock.py status`（进度板）· `tools/refresh_check.py`（来源复验）·
  `tools/harvest.py`（Reddit/HN/小红书收割）· `tools/mirror.py`（镜像 → 题目标准化）

### 尽调第三轮（四路）
| 路 | 状态 | 报告 |
|---|---|---|
| 英文聚合站 + Blind + LC | ✅ 已落盘 | `catalog/discovery/2026-09-03b/aggregators_sweep.md` |
| 中文站 + 小红书可行性 | ✅ 已落盘 | `catalog/discovery/2026-09-03b/chinese_sites.md` |
| 1p3a 镜像 | ✅ 已落盘 | `catalog/raw/mirror_1p3a_stripe/` + `catalog/discovery/2026-09-03b/mirror/README.md` |
| **Reddit + HN 收割** | **🔄 进行中** | 目标 `catalog/discovery/2026-09-03b/reddit_harvest.md` |

---

## 2. 站点可达性台账（实测，别按直觉猜）

**教训贯穿三轮：一次抓取失败不能给一个站定终身。要具体到"哪条路径"失败。**
我们前后推翻了自己三次（teamblind、reddit、1point3acres），每次代价都是几百条一手材料。

| 站点 | 能不能 | 怎么进 |
|---|---|---|
| teamblind | ✅ | **浏览器 UA**（机器人 UA 一律 403） |
| reddit | ✅ | **`.rss`**：`r/<sub>/search.rss?q=&restrict_sr=1&sort=new`（25 条/次）+ 单帖 `/comments/<id>/.rss`（**含评论全文**）。HTML 是 JS 壳、`.json` 403、全站 search.rss 返回 0 |
| Hacker News | ✅ | Algolia 全开放：`hn.algolia.com/api/v1/search?query=&tags=comment` |
| leetcode | ⚠️ | discuss HTML 403，**GraphQL 端点 `POST /graphql` 可用** |
| GitHub | ⚠️ | `api.github.com` 403、HTML 403，**但 `git clone` 走 smart-HTTP 通**；`raw.githubusercontent.com` 也通 |
| prachub / interviewdb / csoahelp / programhelp / oavoservice / levels.fyi / nowcoder / CSDN | ✅ | 直接抓 |
| **1point3acres** | ❌ 直连 | Cloudflare 死锁。**走 `catalog/raw/mirror_1p3a_stripe/` 镜像** |
| 小红书 | ⚠️ | 正文能取（移动 UA + 分享链接，`__INITIAL_STATE__`，**保留 xsec_token**）；**搜索是死路**（站内需登录、搜索引擎不索引、RSSHub 需 cookie）；且**沙箱机房 IP 会被封到安全校验页** |
| medium / glassdoor / 知乎 / 脉脉 / reddit `.json` / 1024bbs | ❌ | 403 或不可达 |

CSDN 可达但**混有 AI 内容农场**（日期造假，2012 年的帖子讨论"2026 OA"），逐条辨伪。
`lodely.com` / `vervecopilot.com` 已判定为 AI 题目农场，**一律不采信**。

---

## 3. 下一步该做什么（按优先级，附具体动作）

### P0 · 等 Reddit + HN 那一路回来
落盘后做**跨信源统一去重**，再给一个有分母的覆盖率数字。
**目前唯一有分母的数字是 82%（49/60，prachub 单站标题级），它是子集下限，不是总体撞题概率**——
不要把它当成"我们达到 80% 目标了"。

### P1 · `ps10_rbac_role_resolver` 按真实结构重写
镜像确认 C6 的真实四阶段是：
Phase 1 直接角色查询 → Phase 2 继承 → **Phase 3 找出拥有某权限的所有用户** → **Phase 4 按角色过滤用户**。
后两个是**反向查询**。我们 ps10 自拟的 part 3/4 是"通配符 + deny 全局优先"和"批量查询双层缓存"，**跟真题不一样**。
原文：`catalog/raw/mirror_1p3a_stripe/coding/*rbac_role_resolver*.txt`

### P2 · 镜像 gap 逐条判重立项
`python3 tools/mirror.py gaps` 列出 16 条题名关键词在 CATALOG 命中率 <34% 的条目。**粗筛，需人工判重**。
已知值得立项的：
- `parse_and_aggregate_records_with_potentially_unknown_fields`（FULL，2026-04-13）——
  `key=value` 松散记录，重复 key 取最后一个，PART1 按币种汇总 / PART2 任意 key 分组 / PART3 schema 推断
- `incremental_filtering_and_transformation_on_tabular_user_records`（FULL，2026-04-11）
- `transaction_fee_with_status_and_type_specific_rates`（FULL，2026-04-20）= **C11**，catalog 原记"题面未公开"
- `for_all_intents_and_purposes` 四个 part（SUMM，2025-03-04）——名字像 PaymentIntent 族但 catalog 无对应
- 两道 bug squash：`bug_bash_fix_301_redirect_handling_for_streaming_binary_post_requests`、
  `repo_debugging_fix_failing_tests_in_a_failsafe_project`
- `integration_task_read_json_file_make_http_requests_compare_responses`（request replay）
- `ordered_dictionary` · `domain_contact` · `sendinvoicereminder` · `message_processing_from_input`

立项方式：`python3 tools/mirror.py scaffold <slug 片段> --as <目录名> [--round <轮次>]`
**工具会按档位自动写警示块**，不要手写。

### P3 · C8 移出 Table C，升级为 Table A 行
证据已是 high（prachub 候选人原始转载）。本仓库已有实现 `int04_review_assignment_gitdiff`。

### P4 · 决定 DS/DA 赛道要不要建
聚合站那路发现了 Data Scientist / DA 岗的 SQL/建模面试线（6 条，含完整 onsite 报告）。
**本题库此前完全按 SWE 组织**。要不要覆盖是用户的决定，不要自己扩。

### P5 · 小红书需要用户配合
搜索走不通。要用户在 App 内搜"Stripe 面经" → 分享 → 复制链接 → 原样发过来（**保留 `xsec_token`**）。
拿到链接后：`python3 tools/harvest.py xhs "<链接>"`。
**诚实提醒**：就算给了链接，沙箱机房 IP 也可能被小红书挡回安全校验页。

---

## 4. 用户约定（按时间最新为准）

- **并行子代理 ≤ 3**。2026-09-03 用户一度说"spawn more than three"，随后明确恢复上限 3，
  之后再次强调不要回到 5 个。**≤3 是默认值，只有用户当次明确要求才可突破。**
- **频繁存盘防 usage limit**：每完成一个可验收单元就 commit + push，不要攒着。
  长时间运行的收割任务必须**增量落盘**，不能只在结尾写文件。
- 产出型子代理用 `sonnet`；每代理只写自己名下目录；协调者验收 → commit。
- 材料中文；代码与专有名词英文。`problems/` 的 `problem.md` **正文保持英文**
  （真实 OA 是英文，读长英文题面本身是被打分的能力），警示块 / Sources / REPORT.md 用中文。
- pytest 注意：`pytest.ini` 已带 `-q`，命令行**别再加 `-q`**（会吞汇总行）。
- **不放宽任何 perf 预算**去让容器看起来绿。

---

## 5. 三条记账纪律（这份题库能不能长期可信，全在这）

1. **不编 URL。** 只写实际抓取过、或搜索真实返回过的链接。
2. **不把猜测写成事实。** 找不到就写"未找到"，并记下试过的检索式。
3. **转引要标明。** 复用旧材料标"复用 + 原采集日期"，**不冒用今天的访问日期**。

重建题的边界不能糊：**练里面的技能，不背输出格式。** 把自拟格式当真题背，比不练更糟。
