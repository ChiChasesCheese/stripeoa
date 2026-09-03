# 撞题率到底有多少 —— 用镜像数据算一遍（2026-09-03）

> 数据源：`catalog/raw/mirror_1p3a_stripe/` 168 条，带日期与 1p3a UUID。
> 方法：slug 按 token Jaccard + 字符级 SequenceMatcher 聚类（阈值 0.62）成"题族"，再按月做时间线。
> **结论先行：题型覆盖接近完备，但"撞上原题"的概率远达不到 80%。这两件事必须分开说。**

## 1. 原始数字

| 量 | 值 |
|---|---|
| 镜像记录 | 168 条 |
| 聚类后的**题族** | **117 个**（重复 51 条，30%） |
| 1p3a 自己的 OJ 清单 | 132 条 → 92 个不同题 |
| 候选人上报（thread/popular） | 36 条 → 28 个不同题 |
| 2025-09 起累计不同题 | **97 个**（9 个月） |
| 我们题库对镜像题族的自动匹配覆盖 | 90/117 = **77%** |

## 2. 但 77% 这个数字要往上修 —— 匹配器有明显漏判

手工过了那 27 条"未覆盖"，其中**至少 10 条是假阴性**（我们其实有）：

| 镜像题名 | 其实是我们的 |
|---|---|
| `shipping_cost_queries_with_direct_and_one_transit_routes` | q22 |
| `shipping_cost_lookup_and_transit_route_optimization` | q22 |
| `assigning_tasks_to_workers_based_on_skills_and_task_types` | q28 |
| `multiple_people_debt_minimization` | qA08 / q32（LC 465） |
| `feature_flag_library_with_environment_based_conditional_activation` | q38 |
| `kyc_compliance_pipeline_multi_part_implementation` | q15 |
| `bitfont_repository_implement_decoders_and_compose_them` | cd09 |
| `bitfont_render_letters_by_converting_bitmap_symbols` | cd08 |
| `bitmap_character_lookup_print_compress_decompress` | cd10 |
| `bitfront` | cd09（拼写变体） |

另有 **3 条属于 MLE / DS 赛道**（`tabular_data_neural_network`、`predicting_user_churn`、
`account_takeover_prediction_system`），本题库按 SWE 组织，**不在射程内，不该算进分母**。

修正后：**114 个 SWE 题族里覆盖 100 个 ≈ 88%**。

## 3. 然后是坏消息：题库churn 得很快

按题族**首次出现的月份**统计：

| 月份 | 当月不同题 | 其中首次出现 | 复现率 |
|---|---|---|---|
| 2025-10 | 13 | 11 | 15% |
| 2025-11 | 19 | 17 | 11% |
| 2025-12 | 19 | 15 | 21% |
| 2026-01 | 22 | 18 | 18% |
| 2026-02 | 14 | 12 | 14% |
| 2026-03 | 9 | 6 | 33% |
| 2026-04 | 14 | 13 | **7%** |

**每月约 13 道新题首次出现。跨 ≥2 个月复现的题族只有 10/117 = 9%。**

### 真正的常青题只有这些

| 跨月数 | 区间 | 题 |
|---|---|---|
| 7 | 2025-03 → 2026-03 | `parse_transaction_csv_and_calculate_fees`（≈ 我们 q20） |
| 4 | 2025-11 → 2026-05 | `csv_dataset_validation_multi_part` |
| 4 | 2025-10 → 2026-02 | `subscription_email_scheduler`（≈ q07 / cd01） |
| 2 | 2025-03 → 2026-03 | `subscription_based_scheduled_email_notifications` |
| 2 | 2026-01 → 2026-03 | `integration_exercise_bikemap_api_integration`（≈ int01） |
| 2 | 2025-03 → 2026-01 | `find_cheapest_shipping_route_with_up_to_one_transfer`（≈ q22） |
| 2 | 2025-12 → 2026-01 | `debug_mako_template_engine`（≈ bs01） |
| 2 | 2025-11 → 2025-12 | `account_balance_calculation_and_transaction_management`（≈ q13） |

**这 8 道我们全都有。** 这是最实在的一条好消息。

## 4. 一个必须说清的方法论坑

**9% 的跨月复现率不能直接当"撞题概率"读。**

因为 168 条里有 132 条是 1p3a 的 **OJ 清单**——站方对每道题**只列一次**，结构上就不可能产生重复。
真正能反映"同一道题被不同人考到"的只有 36 条候选人上报，样本太小（f2=0，Chao1 算不出来）。

所以：

- **9% 是复现率的下限**，真实值更高（一道题被多人考到但只有一个人发帖，就看不见）
- 但也**没有理由认为它高到 80%**——每月 13 道新题这个流入速度是硬的

## 5. 最要命的一条：我们有 4 个月的盲区

- 镜像数据覆盖到 **2026-05**
- 镜像仓库自己最后一次 commit 是 **2026-06-01**
- 今天是 **2026-09-03**

**2026-05 → 2026-09 这 4 个月，我们一条镜像数据都没有。** 按每月 ~13 道新题算，
**这期间大约新增了 50 道我们从未见过的题**——而这正好是你面试前的那段时间。

catalog 里也有独立证据佐证 churn：A18 `Join Dataset` 标着 "new in April-2026 rotation"，
LOOP_GUIDE 记着"2024 起题库加速轮换，面试官警惕背题"。

## 6. 所以，回答"80% 目标"

拆成两个问题，答案完全不同：

### Q1：撞上原题（或近似变体）的概率有 80% 吗？

**没有。我给的估计是 35–50%，而且我对这个区间本身只有中等把握。**

推理：
- 常青题（8 道，我们全覆盖）在任何一个月的题池里占比看数据是 **7–33%**，取中位约 15–20%
- 加上"近似变体"（同族不同皮，比如 shipping cost 的三个变体）能再抬高一截
- 但每月 13 道新题的流入 + 4 个月盲区，压住了上限

**之前那个 82%（prachub 49/60）和这里的 88%，衡量的都是"历史记录的覆盖率"，
不是"你那天会拿到什么"。把它们当撞题率读是错的。**

### Q2：题型自包含、做完不露怯，达到了吗？

**基本达到了，这个我有较高把握。**

- 修正后 SWE 题族覆盖 **88%**
- 27 条未覆盖里，扣掉 10 条假阴性和 3 条 ML 赛道，剩下 14 条**几乎全是已覆盖技能的换皮**
  （`parse_and_aggregate` 是 S02+S04、`total_price_calculation` 是 q03/q22 族、
  `invoice_management_CRUD` 是 q25 族、`sendinvoicereminder` 是 q07 族、
  `for_all_intents_and_purposes` 是 PaymentIntent 状态机 = q10 族）
- 真正可能带来**新技能编号**的只有 1–2 条（`ordered_dictionary`、RPN 求值），量级很小
- 53 道题 + 20 轮次题 底下是 **25 个业务技能 + 16 个算法靶子**，这套骨架没有明显缺口

## 7. 结论与该做什么

**别再往"撞题率"上使劲了，边际收益已经很低。**

理由：题库每月流入 13 道新题，你不可能靠收集追上；而你已经覆盖了全部 8 道常青题和 88% 的历史题族。
再补 10 道冷门题，撞题率提升可能就 2–3 个百分点。

**该把力气挪到这三件事上：**

1. **冷启动能力** —— 每月 13 道新题意味着你**大概率会拿到一道没见过的题**。
   决定成败的是"没见过也能在 45 分钟里做出 2–3 个 part"，不是"背过多少道"。
2. **那 8 道常青题练到肌肉记忆** —— q20 · q07/cd01 · int01 · q22 · bs01 · q13 · csv 校验族。
   它们跨越 7 个月还在考，是命中率最高的投入。
3. **补最近 4 个月的盲区** —— 这是唯一还值得做的收集工作。Reddit RSS + HN 是目前唯二能拿到
   2026-06 之后一手材料的渠道（镜像已经停在 2026-06-01）。

## 8. 这份分析自己的局限

- 聚类阈值 0.62 是拍的，改阈值会让 117 这个数上下浮动约 ±10
- 手工修正的 10 条假阴性是我读题名判断的，没有逐条比对题面
- 1p3a 的 OJ 清单是否收全了 Stripe 的题，无从验证——**它自己也可能只是真实题库的一个子集**
- 因此第 6 节那个 35–50% 是**量级判断，不是精确估计**。任何人给你一个两位有效数字的撞题率，
  那个数字都是编的。
