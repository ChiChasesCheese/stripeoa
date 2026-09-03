# ps10 · RBAC Role Resolver：账户树 + 角色继承，练的是"每个 Part 逼你换一次数据表示"

> [!tldr]
> - 这题考的是：在账户层级树上解析用户的有效权限——从"直接角色"到"沿祖先链继承（并集）"到"通配符 + 显式拒绝（deny 全局优先）"到"批量查询要缓存"
> - 三步套路：先写一个不建索引的幼稚 Part 1 → Part 2 起补 `_index`（校验）+ `_ancestor_chain`（带环检测、按 id 缓存）→ Part 3 起把"能枚举的权限列表"换成"按需匹配的 grant/deny 模式集合"
> - 最值得带走的一个模式：**后一个 Part 不是加规则，而是让前一个 Part 的表示方式失效**——列表遇到通配符就得改成模式集合，逐条查询遇到批量就得加缓存，写代码前先想清楚"这一步会不会让上一步的返回值类型不够用了"

这题是**重建题**：两个来源（PracHub「Resolve User Roles Across Account Hierarchy」、1point3acres「RBAC Role Resolver」）都只确认了"账户层级 + 角色/权限解析"这个主题，规则文本、通配符语法、deny 覆盖规则、4 个 Part 的具体划分全部是本仓库自拟。**练的是里面的 S03/S08/S18/S19 技能，别背格式。**

## 1. 题目在说什么（人话版）
Stripe 的平台账户下挂连接账户，连接账户下还能有子账户，形成一棵树。同一个用户在不同层级可能持有不同角色（比如整体只读，但在正在调查的某个连接账户上是全权 admin）。给定账户树、角色定义（权限字符串列表）、用户在哪个账户持有哪个角色，要解析出"这个用户在某个账户到底能做什么"——要考虑向上继承、通配符授权、以及"显式拒绝不能被更宽泛的授权悄悄覆盖"。

三层账户 `platform -> connected -> submerchant`，`alice` 在 `platform` 是 `viewer`、在 `connected` 是 `admin`：
```
part1(alice, submerchant) -> []                       # 自己在 submerchant 没有角色，Part1 不看祖先
part2(alice, submerchant) -> [charges:read, ...]       # 继承 viewer@platform 和 admin@connected 的并集
```

## 2. 读题：把文字变成模型
- **实体**：账户（树，`parent_id`）、角色（`role_id -> permissions`）、分配（`(user, account) -> role`，一对最多一个角色）。
- **输入长什么样**：三张扁平表；权限字符串可以是字面量、`ns:*` 通配、全局 `*`，也可以带 `!` 前缀表示拒绝（Part 3 起才出现）。
- **输出要什么**：Part 1/2 是排序后的权限列表；Part 3 是单个布尔值；Part 4 是一批布尔值，顺序与查询顺序一致。
- **状态**：Part 2 起需要"账户 id -> 祖先链"和"(user, account) -> 聚合后的 grants/denies"两类可缓存的中间结果。
- **一句话建模**：这是一个 **树上路径聚合 + 集合运算** 问题，四个 Part 依次改变"聚合结果该用什么数据结构表示"。

> [!note] 为什么 Part 3 起不能再返回"枚举的权限列表"
> Part 2 的自然做法是把继承到的权限并成一个 `set` 再排序返回——但 `"*"` 或 `"charges:*"` 没法展开成具体权限（不知道全宇宙有哪些权限字符串）。所以 Part 3 起换成保留原始的 grant/deny **模式**字符串，查询某个具体权限时才用 `_matches` 现场匹配，而不是提前算出一份"完整列表"。

## 3. 下笔顺序（面试里就按这个顺序敲）
1. **骨架先行**：`main()` 按 `PART n` 分发，读三段表 + 一个 query 段。Part 1 先不建任何索引，直接线性扫描 `assignments`——故意"幼稚"，为 Part 2 的重构做对比。
2. **Part 2 叠加，换表示**：写 `_index`（三张字典 + 结构性校验：重复 id、未知引用、重复分配）；写 `_ancestor_chain`（沿 `parent_id` 走，`visiting` 集合做环检测，按 id 缓存）；`_grants_denies_for_pair` 沿链聚合，本 Part 只用 grants 那一半。
3. **Part 3 叠加**：`_grants_denies_for_pair` 分出 denies 集合；写 `_matches`（精确/`ns:*`/`*` 三种模式）；`_has_permission` 先查 denies 再查 grants，deny 直接短路返回 `False`。
4. **Part 4 叠加**：把 `chain_cache`/`pair_cache` 提到 batch 级别传入 `_ancestor_chain`/`_grants_denies_for_pair`，同一批查询里重复的 `(user, account)` 对只聚合一次。
5. **收尾**：确认"未知 account 报错、未知 user 不报错"这条不对称规则真的实现了；权限列表显式 `sorted`，不依赖角色定义里的原始顺序。

## 4. 代码怎么组织
```
_index(accounts, roles, assignments) -> (accounts_by_id, roles_by_id, assignment_by_ua)  # 索引 + 结构校验
_ancestor_chain(accounts_by_id, account_id, cache) -> list[str]   # 环检测 + 按 id 缓存
_grants_denies_for_pair(..., cache, user, account) -> (grants, denies)   # 沿链聚合成两个模式集合
_matches(pattern, permission) -> bool             # 精确 / ns:* / * 三种匹配
_has_permission(grants, denies, permission) -> bool   # deny 全局优先
part1..part4(...)                                 # 只做"要不要继承 / 要不要模式匹配 / 要不要批量缓存"
main(stdin, stdout)
```
拆分原则：**索引/遍历、聚合、匹配、批量缓存四层各自独立**，让"这一步会不会让上一层的返回类型不够用"这件事在函数边界上就能看出来——`_grants_denies_for_pair` 从 Part 2 到 Part 4 签名完全不变，只是多传一个共享缓存字典。

## 5. 核心代码（骨架，≤ 40 行，带注释）
```python
# 只放主线：索引 -> 祖先链 -> 聚合 -> 匹配。省略校验的具体错误信息与 stdin 解析。
def _ancestor_chain(accounts_by_id, account_id, cache):
    if account_id in cache:
        return cache[account_id]
    path, visiting, current = [], set(), account_id
    while current not in cache:
        if current in visiting:                       # 环检测：走回本次路径上已见过的节点
            raise ValueError(f"cycle at {current!r}")
        visiting.add(current); path.append(current)
        parent = accounts_by_id[current].get("parent_id")
        if not parent:
            current = None; break
        current = parent
    path.reverse()                                     # 叶 -> 根 变成 根 -> 叶
    full = (cache[current] if current else []) + path
    cache[account_id] = full
    return full

def _grants_denies_for_pair(accounts_by_id, roles_by_id, assign_by_ua, cache, user, account):
    grants, denies = set(), set()
    for level in _ancestor_chain(accounts_by_id, account, cache):    # 根 -> 该账户，逐层聚合
        role_id = assign_by_ua.get((user, level))
        if role_id is None:
            continue
        for perm in roles_by_id[role_id]["permissions"]:
            (denies if perm.startswith("!") else grants).add(perm.lstrip("!"))
    return grants, denies

def _matches(pattern, permission):
    if pattern in ("*", permission):
        return True
    return pattern.endswith(":*") and permission.startswith(pattern[:-1]) and len(permission) > len(pattern) - 1

def _has_permission(grants, denies, permission):        # deny 全局优先，不管哪一层更"近"
    if any(_matches(p, permission) for p in denies):
        return False
    return any(_matches(p, permission) for p in grants)
# Part 4 = 同一套函数外面套两个字典缓存（chain_cache 按 account、pair_cache 按 (user,account)），
# 逐条查询前先查缓存命不命中，命中就跳过 _ancestor_chain / _grants_denies_for_pair 的重新计算。
```

## 6. 面试里怎么说（边写边讲）
- 开始前：「这是一道账户树上的权限继承题——我先确认继承是并集还是覆盖，通配符和 deny 是什么时候出现的。」
- 写 Part 2 时：「我用一个带环检测的祖先链遍历，链本身按 account_id 缓存，因为后面 Part 4 要批量查询，同一个账户的链不该重复走。」
- 写 Part 3 时：「这里我决定不再枚举权限列表，因为通配符没法展开——改成保留原始模式，查询时才匹配。deny 我做成全局优先，不管它在哪一层，这是我自己定的规则，不是唯一合理的选择，如果你们的产品要求'就近层级优先'我可以改一行。」
- 写 Part 4 时：「两个缓存分别按账户和按 (user, account) 对存，保证同一批查询里重复出现的祖先链和聚合结果只算一次；我会用逐条调用 Part 3 的结果去对拍批量结果，确认缓存只影响速度不影响正确性。」
- 交付时：「未知账户我报错，未知用户我不报错——因为用户不存在只是'零权限'，账户不存在是数据本身有问题，这个不对称是我特意设计的。」

## 7. 常见跑偏（方法层面，3 条）
- **Part 2 只加了个 for 循环，没意识到要换索引结构**：继续对 `assignments` 做线性扫描但套一层"查父账户"的递归，写出来的是 O(depth × n) 且没有环检测——读题时就该问自己"这一步会不会让我需要一个新的索引/缓存"，而不是先写了再说。
- **Part 3 把权限列表提前展开**：试图把 `"*"` 也塞进一个"最终权限集合"里，结果发现展不开只能特判。正确做法是从"列表"换成"模式 + 按需匹配"这个表示，越早换越省事。
- **Part 4 加了缓存但没验证正确性不变**：只测了"变快了"，没有把批量结果和逐条调用 Part 3 的结果对拍——缓存类的优化最容易在边界（缓存没命中时的默认值、缓存 key 漏了一个维度）上悄悄改变结果。

## 8. 同族题 / 延伸
- 这题的"树上路径聚合"结构和 ps01 的"按用户分组、按时间线扫描"是同一类"先建索引/分组，再在结构上跑规则"的方法论，只是这里的分组维度是账户树而不是时间线。
- 延伸思考：如果要支持"用户组"（组也能持有角色，用户属于多个组），只需要在 `_grants_denies_for_pair` 里把"查询用户自己的角色"换成"查询用户 + 用户所在的所有组的角色"，账户树遍历和 deny 优先逻辑完全不变——这是检验"分层是否真的分对了"的一个好问题。
- 练习命令：`python3 loop/mock.py start ps10 -m 45`
