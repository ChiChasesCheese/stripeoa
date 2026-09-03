# ps10 RBAC Role Resolver — 报告

## 摘要
这是一道**重建题**：账户层级（platform -> connected account -> ...）上的角色/权限解析，Stripe
场景下非常典型的"树形结构 + 集合运算"题型。四个 part 依次要求：直接角色（无继承）、沿祖先链的
权限继承（并集）、通配符与显式拒绝（deny 全局优先于 grant）、批量高效解析。设计上刻意让后面的
part"反噬"前面的实现——Part 2 逼你从"一次线性扫描"换成"带环检测的索引化图遍历"，Part 3 逼你从
"能枚举的权限列表"换成"只能按需匹配的通配符模式"，Part 4 逼你从"每次查询都重新算一遍"换成"按
account 和 (user,account) 对分别缓存"。这正是任务要求里点名的"Stripe 题的核心特征"。

## 来源与置信度
**low，重建题**。两个独立来源（PracHub「Resolve User Roles Across Account Hierarchy」，
2026-05-12；1point3acres「RBAC Role Resolver」）只确认了题目存在和一句话主题描述——"账户层级+
角色/权限解析"，没有任何规则文本、样例数据、函数签名可用。1point3acres 全站对未登录请求 403，
正文从未拿到；搜索引擎自带的规则释义被判定为泛化释义、不采信（措辞与教科书式 RBAC 介绍雷同，且
搜索工具自己承认"完整内容未被抓到"）。因此本题的全部规则细节——字段名、通配符语法、deny 覆盖
规则、4 个 part 的具体划分、stdin 协议、worked examples 的具体数值——都是本仓库为覆盖
S03/S08/S18/S19 而自拟的训练题，problem.md 开头已放置警示块，不能当成真题格式去背。

## 分 part 思路
1. **Part 1**：完全不建索引，直接线性扫描 `assignments` 找 `(user_id, account_id)` 的直接角色，
   找到就返回排序后的权限列表，找不到返回 `[]`。故意保持"幼稚"实现，为 Part 2 的"反噬"做铺垫。
2. **公共索引 `_index`**（Part 2 起复用）：把 `accounts`/`roles`/`assignments` 转成三个字典
   （`account_id -> account`、`role_id -> role`、`(user_id, account_id) -> role_id`），过程中
   做结构性校验（重复 id、未知引用、同一 `(user,account)` 重复分配）。
3. **`_ancestor_chain`**（Part 2 起复用）：从某个 `account_id` 出发沿 `parent_id` 向上走，用一个
   `visiting` 集合做环检测（走到已经在本次遍历路径里的节点就报错），走到已缓存的祖先或走到根为止；
   结果按"从根到该账户"的顺序缓存进传入的 `cache` 字典，供后续调用复用。
4. **Part 2**：调用 `_ancestor_chain` 拿到整条链，逐层查该用户在该层有没有角色，把所有层的权限
   取并集（`set`），排序返回。
5. **Part 3**：把"并集成一个列表"换成"分别累积 grants 集合和 denies 集合（模式字符串，不展开）"，
   查询时先看 denies 里有没有能匹配上的模式（有则直接 `False`），再看 grants 里有没有匹配的模式。
   `_matches` 实现三种模式：精确匹配、`ns:*` 前缀匹配（要求冒号后有内容）、全局 `*`。
6. **Part 4**：在 Part 3 的基础上加两层缓存——`chain_cache`（按 `account_id` 缓存祖先链，整个
   batch 共享）和 `pair_cache`（按 `(user_id, account_id)` 缓存聚合后的 grants/denies，整个
   batch 共享）。同一批查询里重复出现的 `(user, account)` 对只聚合一次。

## 隐藏测试可能针对的坑
- Part 1 被写成"直接查该账户自己的角色"，如果误加了继承逻辑会在
  `test_no_inheritance_from_ancestor` 上暴露。
- Part 2 的并集被写成"取最后一层覆盖前面"而不是并集——`test_inherits_union_of_ancestor_permissions`
  和 `test_union_deduplicates_permission_appearing_at_two_levels` 一起覆盖这两种错误方向。
- 环检测缺失导致死循环——`test_two_node_cycle_raises` 和 `test_self_parent_cycle_raises` 分别测
  两种环的形状（自环容易被"parent != self"这种局部判断漏掉更大的环）。
- 未知 account 和未知 user 被同等对待（要么都报错要么都不报错）——
  `test_batch_unknown_account_in_a_query_raises` 和
  `test_batch_unknown_user_returns_false_not_an_error` 专门验证这个不对称规则被正确实现，而不是
  两边行为一致。
- Part 3 的"deny 优先"被实现成"就近覆盖"（更靠近账户的层级说了算）而不是"deny 全局优先"——
  `test_deny_at_a_farther_level_still_beats_a_grant_at_a_closer_level` 是本题设计上最容易被面试
  官/候选人搞反的一条规则，专门构造"近处 grant、远处 deny"的场景来区分两种规则。
- `ns:*` 通配符被实现成前缀匹配（`"charges"` 也能匹配 `"charges:*"`），而不是要求冒号后有内容——
  `_matches` 的 `len(permission) > len(prefix)` 检查是这条的实现要点，虽然本次测试套件没有专门
  对着裸字符串 `"charges"` 写断言，但 problem.md 的 Edge cases 明确列出这一条，供后续补测试。
- Part 4 的缓存改变了查询结果（而不仅仅是速度）——`test_batch_matches_individual_part3_results`
  直接拿逐条调用 Part 3 的结果去对照批量结果，保证缓存是纯粹的性能优化、不引入正确性偏差。
- 批量场景下对同一个很深的祖先链重复完整遍历——`test_perf_deep_chain_repeated_pair_queries` 用
  3000 层链 + 25000 条重复 `(user,account)` 对、只变权限字符串的查询来卡这一点：不缓存的朴素实现
  在数量级上会明显更慢。

## 复杂度与实测性能
`_ancestor_chain` 单次调用最坏 O(depth)，但结果按账户缓存，一次 batch 内同一账户只会真正走一次；
`_grants_denies_for_pair` 单次最坏 O(depth)，同样按 `(user,account)` 缓存。Part 4 整体近似
O(distinct pairs × depth + queries)，而不是 O(queries × depth)。实测：3000 层单链、25000 条查询
（全部指向同一个 `(user, account)` 对、只变权限字符串）——参考实现在纯 Python 内部计算约 0.04
秒，`run_script` 全程（含子进程启动、stdin 解析 3000+25000 行）约 0.17 秒，远低于 2 秒预算；一个
不做 `pair_cache` 的朴素实现在同等规模下的独立测算约 0.77 秒（更贴近真实候选人代码、带更多函数
调用开销的实现会明显更慢）——见 `test_perf_deep_chain_repeated_pair_queries`。

## 测试清单
28 个测试 —— part1: 5（含 1 io、1 fmt）· part2: 9（含 1 io、1 fmt、4 edge）· part3: 7（含 1 io、
3 edge）· part4: 7（含 1 io、1 perf、2 edge）。按 marker 计数：edge 9 · fmt 2 · io 4 · perf 1。

## 覆盖的技能点
S03 记录建模（accounts/roles/assignments 建成 id 索引字典） · S08 确定性排序（权限列表始终排序
输出，不依赖角色定义里的原始顺序） · S18 校验与错误路径（未知引用、重复分配、环检测、"未知账户
报错 vs 未知用户不报错"的显式不对称规则） · S19 分层设计（每个 part 都强迫改变上一层的数据表示，
而不只是加规则——见 problem.md"Why later parts break earlier assumptions"）

## 本题覆盖的知识点
- **S03（记录建模）**：`accounts`/`roles`/`assignments` 都是扁平的字典列表，`_index` 把它们转成
  三张按 id 查找的哈希表（`account_id -> account`、`role_id -> role`、
  `(user_id, account_id) -> role_id`）——练习"面试官给你的通常是列表，你自己决定索引结构"这个
  几乎每道 Stripe 题都会用到的基本功。
- **S18（校验与错误路径）**：本题在 S18 上刻意做得比一般题更细——不只是"输入不合法就报错"，而是
  显式区分了三类不同的错误/非错误情况：结构性错误（重复 id、未知引用、重复分配）必须报错；环
  必须被检测出来而不是死循环；"查询一个不存在的用户"则**不是**错误，只是"没有权限"。三者混在一起
  最容易被写成"任何查不到的情况都报错"或者"任何查不到的情况都返回 False"这两种偷懒的一刀切。
- **S08（确定性排序）**：Part 1/2 的权限列表在角色定义里刻意写成乱序（`ROLES` 测试夹具里
  `viewer` 的两个权限就是反着写的），返回值必须显式排序——`test_permissions_are_sorted_even_though_role_lists_them_unsorted`
  直接命中"返回值顺序等于输入定义顺序"这种偷懒实现。
- **S19（分层设计）**：这是本题的设计重心——四个 part 不是简单的"规则叠加"，而是三次真正的表示
  层重构（扁平扫描 -> 索引化图遍历 -> 模式而非枚举列表 -> 双重缓存）。problem.md 专门用一节
  "Why later parts break earlier assumptions"把这三次重构逐条写清楚，REPORT 的"分 part 思路"
  一节和它一一对应，练习的是"预判后面的 part 会怎么反噬现在的设计"这个 Stripe 电面反复强调的能力，
  而不是"能不能把当前这个 part 做对"。

## Open points
- 真实题目的规则（尤其是"继承是并集还是覆盖""deny 是否真的存在""通配符语法具体是什么"）完全未知
  ——本 REPORT 和 problem.md 已经反复标注这是重建题，如果后续拿到 PracHub 该页面的完整正文或
  1point3acres 的真实内容，应该回来核对本题的规则设计是否需要推倒重来，而不是小修小补。
- 未覆盖"同一账户下不同用户的权限是否有优先级/继承关系"（例如用户组），本题的 `assignments` 只到
  "用户直接持有角色"这一层，没有引入用户组/角色继承角色这类更复杂的间接层级——真实题目是否需要
  这一层完全未知，本仓库选择不加，保持题目规模适合电面时间盒。
