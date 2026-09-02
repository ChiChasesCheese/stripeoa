# int03 Multi-JSON ETL — report

## Summary
linkjob 2025-12 面经原话是"reading three JSON files, converting them into dictionaries, and
performing bidirectional ETL operations"——一句话，没有给字段名、没有给异常规则、没有给 CLI 形状。这道题
把这句话展开成一个可测试的契约：三份字段名不一致的 JSON（当前系统 `customers.json` / 旧系统
`legacy_export.json` / 订单 `orders.json`）→ 按 email 统一去重 → 双向格式转换（`to_legacy`/`from_legacy`
往返等价）→ 订单 join → 报告 + 异常 CSV。考察点不是算法，是**防御性数据管道**的三件事：解析时不静默吞坏
数据（分类记录到 `anomalies`）、去重规则要经得起边界推敲（缺失日期不能靠字符串比较的偶然性"赢"）、格式转换
要真正可逆（不是"看起来差不多"）。

## Sources & confidence
Medium-high for题目形状：linkjob 2025-12 面经原话与 Exponent 收录的 Integration 题型清单（"读多个 JSON 文件
互转格式"作为独立一类，见 `loop/raw/en_forums.md` 第 269 行）相互印证，说明"多 JSON 互转"确实是 Stripe
Integration 题库的一个真实类别。**具体契约是本仓库复刻**：面经原文没有给出文件名、字段名、异常分类、CLI
参数——`data/*.json` 三份文件（用 `random.Random(0)` 生成，customers 315 条、legacy 250 条、orders 410 条，
含约 130 条制造的异常记录）、`EtlError` 的消息格式、`anomalies.csv` 的四类异常、`created` 最早胜出的去重规则
都是本仓库为了让"双向 ETL"可测试而设计，problem.md 的 Clarifications 节已注明。

## Part-by-part approach
1. **Part 1 读取与统一**：`load_json_file` 把 `OSError`/`json.JSONDecodeError` 统一包成 `EtlError`（含文件
   路径 + 行列号），调用方不需要关心底层是文件不存在还是语法错误。`parse_customers`/`parse_legacy` 各自把
   本文件格式的记录转换成统一的 `Customer` 四键字典，`email`/`mail` 规范化后为空的记录被**丢弃并记异常**
   （不是静默跳过）。`unify_customers` 接受任意多份列表（`*args`），按 email 合并，`created` 最早胜出
   ——这里最容易写反的边界是"缺失 created 该赢还是该输"，本仓库用哨兵值 `"9999-99-99"` 让缺失的一方永远
   排在最后，而不是让空字符串在字典序比较里意外获胜。
2. **Part 2 双向转换 + join**：`to_legacy`/`from_legacy` 是纯函数，互为逆运算；`parse_legacy` 复用
   `from_legacy` 而不是重新写一遍字段映射，保证"解析"和"序列化回旧格式"用的是同一份映射逻辑，不会日后各自
   漂移。`join_orders` 按规范化 email 关联订单，产生三类异常（缺 email、找不到客户、`order_id` 重复），
   重复订单**仍然计入金额**（只报告不去重）——这是"数据管道重跑导致重复导出"场景的忠实反映。
3. **Part 3 报告 + CLI**：`build_report` 按 `placed_at` 字符串比较取最近订单（ISO-8601 天然可排序）；
   `write_outputs` 用标准库 `csv.writer` 写异常表，避免手写字符串拼接导致的转义问题；`run_etl` 编排整个
   pipeline 并返回摘要，`main_cli` 只是给它包一层 `argparse`。

## Pitfalls hidden tests target
- 缺失 `created` 的记录在字符串比较里意外赢过有日期的记录（`test_unify_missing_created_never_beats_a_dated_record`
  双向验证，不管传参顺序）
- `email`/`mail` 缺失键、空字符串、纯空白三种"无邮箱"没有被同等对待（`test_parse_customers_missing_and_blank_email`）
- `to_legacy`/`from_legacy` 看起来对但其实不是真往返（`test_roundtrip_holds_for_every_generated_customer` 用
  50 组随机数据验证，不只测一个手工例子）
- `join_orders` 邮箱大小写不敏感匹配失败（`test_join_orders_case_insensitive_email_matches`）
- 重复 `order_id` 被去重导致金额少算，或者异常表里为每次出现都记一条而不是记一条"出现 N 次"
  （`test_join_orders_worked_example`、problem.md 明确定死"不影响 join"）
- `load_json_file` 让裸 `json.JSONDecodeError`/`FileNotFoundError` 冒泡给调用方，而不是统一成 `EtlError`
  （`test_load_json_file_empty_file_raises_etlerror_with_position`、`test_load_all_missing_file_raises_etlerror`）
- `customers.json` 顶层不是列表时在遍历深处抛出语义不清的 `TypeError`，而不是在 `load_all` 里显式校验
  （`test_load_all_customers_not_a_list_raises_etlerror`）
- `most_recent_order` 对零订单客户返回 `None` 还是缺键或抛异常（`test_build_report_worked_example`）
- `join_orders`/`build_report` 对大规模数据用了 O(n×m) 扫描而不是 dict 查找（perf 测试用 2000 客户 × 10 万
  订单验证 < 2s）

## Complexity + measured time/memory
`parse_customers`/`parse_legacy`：O(n)。`unify_customers`：O(Σn)（多份列表各遍历一次，dict 查找摊还 O(1)）。
`join_orders`：O(m)（m=订单数，dict 查找关联客户）。`build_report`：O(m log k)（每个客户的订单按
`placed_at` 取 max，k=平均每客户订单数，可忽略）。测得：2000 客户 × 10 万订单的 `join_orders + build_report`
< 1s（本机测量，预算 2s，见 `test_perf_join_and_report_100k_orders`）。

## Test inventory
26 tests — part1: 12（含 8 edge）· part2: 7（含 2 edge，2 fmt）· part3: 7（含 1 edge，1 fmt）· edge: 13 ·
fmt: 2 · io: 5 · perf: 1（marker 有重叠，按 `@pytest.mark` 出现次数统计，非互斥求和）。
`rtk proxy python3 -m pytest loop/rounds/05_integration/int03_multi_json_etl -q` → 26 passed；
`IMPL=starter` 同一命令 → 15 failed（其余 11 个对空 starter 的默认返回值 `{}`/`[]`/`""` 恰好也满足断言，如
`test_normalize_email` 的部分子句、`test_io_empty_stdin`，其余全部按预期失败）。

## Skills exercised
S02 防御性 JSON 解析 · S04 多源数据按 key 合并去重 · S06 整数分金额 · S08 确定性排序 · S18 自定义异常归一化
（`EtlError` 含文件名+位置）· S19 增量设计（Part 2 复用 Part 1 的 `Customer` 形状，`parse_legacy` 复用
`from_legacy`）· S24 领域知识（ETL 幂等性、双向格式转换的往返测试），对照 `skills_matrix.md`。

## 时间分配（extrabrain 模板，60 min）
- 0-5 min：读题，确认三份文件的字段映射（数据字典），口头向面试官复述一遍映射关系，防止理解错。
- 5-20 min：Part 1（`load_json_file`/`EtlError`/`parse_customers`/`parse_legacy`/`unify_customers`/
  `load_all`），边写边跑 worked example 里的三文件小样例。
- 20-35 min：Part 2（`to_legacy`/`from_legacy`/`join_orders`），先写往返测试再写实现（往返等价是这题唯一
  容易"看起来对但实际不对"的地方）。
- 35-50 min：Part 3（`build_report`/`write_outputs`/`run_etl`/`main_cli`），跑一遍针对 `data/` 大文件的
  sanity check，确认没有异常、报告字段类型对。
- 50-60 min：补边界测试（缺失字段、重复、空文件），口头过一遍 anomalies 分类设计的取舍。

## 边写边说什么（onsite 话术）
- 打开三份文件先说："这三份数据字段名不一致，我先建一张映射表再动手，不然容易在 `parse_legacy` 里手滑写错
  键名。"
- 写 `EtlError` 时主动说明："文件解析失败不应该让调用方看到 `json.JSONDecodeError` 这种实现细节，我统一包
  一层，并且把文件名和出错位置带上，方便排查是哪个文件的第几行坏了。"
- 写 `unify_customers` 的去重比较时主动提："缺失 `created` 不能直接拿空字符串去比较大小，那样会在字典序下
  意外'赢'，我用一个哨兵值让它永远排最后。"
- 写 `to_legacy`/`from_legacy` 时主动说："双向转换最容易犯的错是'看起来能转回去'但其实丢了信息，我会先写
  一个往返测试再写实现。"
- Part 3 时间紧的话，优先保证 `build_report`/`write_outputs` 的正确性，`main_cli` 的参数校验（比如 `--in-dir`
  不存在时的报错文案）可以口头说明设计但先不做防御性增强——多份 Stripe Integration 面经强调"前几步的质量
  比做完所有 part 更重要"。
