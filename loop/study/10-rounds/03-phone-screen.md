# 03 · Technical Phone Screen（60 min = 45 编码 + 15 Q&A）

> 事实层（形式 / 通过线 / 挂点）在 `loop/LOOP_GUIDE.md` §3，本章不重复。
> 本章回答的是：**明天坐下来练这一轮，具体做什么。**

## 这轮到底考什么（一句话）

**把一段啰嗦的业务描述，快速翻成好代码。** 不是算法题。

Stripe 员工的原话是 "Read in this JSON, transform it / do something interesting with it"。
难点有两个，都不在算法上：

1. **阅读理解** —— 题面故意写得长，规则藏在句子里
2. **为 part N+1 设计** —— 做完一个 part 才给下一个，而下一个会动你的数据结构

## 通过线

| 语言 | 通过线 |
|---|---|
| Python | ≈ 3/4 part |
| Java / C++ | ≈ 2/4 part |

面试官不完全按 rubric 判。四个真正打动人的点：**High code quality · Fast completion · Simple clear thought process · Humble attitude**。

注意"Fast completion"排第二 —— 但 prep 材料又说 "quality over speed"，**有候选人因为打磨太久而挂**。
这个矛盾的解法是：**Part 1 快，Part 3 慢**。前面的 part 都是后面的地基，越快锁死越好。

## 45 分钟怎么走

| 时间 | 做什么 | 出声说什么 |
|---|---|---|
| 0–5 | **读完全部 part 再动手** | "我先把三个 part 都读一遍，避免第一版结构撑不住后面" |
| 5–8 | 复述 + 确认假设 | "我理解是……；有两个地方想确认：空输入返回什么？相同分数怎么排序？" |
| 8–10 | 骨架先行 | `main()` 读入 → `parse()` → `part1()` 空实现 → 打印。**先让整条链路跑通** |
| 10–20 | Part 1 + 自测 | 写完立刻用题面样例验，再补 2–3 个自己的 `assert` |
| 20–33 | Part 2 | 复用 part 1 的 helper；改不动就说明分层错了 |
| 33–42 | Part 3 | 时间不够就**口头说思路**——这能过 |
| 42–45 | 收尾 | 排序 key 补全、格式集中到一个函数、跑一遍全部样例 |

**没有自动测例。** 你自己造输入、自己验证。这是最多人栽的地方（有人一直等系统给反馈，等到时间结束）。

## 挂点 → 对策

| 挂点 | 对策 |
|---|---|
| 追求最优复杂度，不先写能跑的 | 先写 O(n²) 能跑的版本，说一句"先跑通，需要的话我再优化"。复杂度"carry little weight" |
| 期待自动测例 | 开场就说"我会自己写几个 assert 来验" |
| 求助 ≥3 次 | 卡住先自己出声推演 30 秒再问；问的时候问**决策**（"这里我倾向 A，因为 X，你觉得呢"）不是问答案 |
| 只做到第一个 follow-up | Part 1 提速。你在 part 1 省的每一分钟都是 part 3 的 |
| 花太多时间打磨 | 变量名一次到位，别回头改；格式化集中一处，别散在各处 |

## 明天怎么练（具体到命令）

**热身梯度**（前两天，别一上来啃硬的）：

```bash
python3 loop/mock.py start ps08 -m 45   # Min/Max comparator，最轻
python3 loop/mock.py start ps05 -m 45   # Numeronym，规则干净
python3 loop/mock.py start ps07 -m 45   # 卡号脱敏，纯字符串
```

**主力**（refs 最高的电面题，撞题率也集中在这段）：

```bash
python3 drill.py start q19    # Accept-Language，4 part，2021→2026 常青
python3 drill.py start q21    # 汇率换算，图 + BFS
python3 drill.py start q22    # 运费，25 refs，全库最高
python3 drill.py start q25    # 发票对账
python3 drill.py start q20    # 手续费 + 对账，4 part
```

**loop 里的电面题**：

```bash
python3 loop/mock.py start ps01 -m 45   # 滑窗 + TopK
python3 loop/mock.py start ps06 -m 45   # 巴西应收款分组
python3 loop/mock.py start ps09 -m 45   # 记录关联（真实复原）
python3 loop/mock.py start ps12 -m 45   # CSV 建树 + 文件树输出（真实复原）
```

**冷启动专练**（每周 2 次，这是唯一能治"撞不上就写不出来"的训练）：
挑一道**没看过的**，45 分钟计时，全程 think loud（真的出声）。

每次跑完 `python3 drill.py status` 看趋势 —— **首个 part 通过的用时在不在下降**，那是手感恢复的客观证据。

## 复盘怎么写

做完一题，读 `loop/study/30-articles/<id>_*.md` 对照。重点不是看答案，是看**第 2 节「读题：把文字变成模型」**——
比较它的"一句话建模"和你当时脑子里的那句差在哪。差在哪，下次就赢在哪。

## 自检清单（进考场前）

- [ ] 我能在 3 分钟内把一段业务描述复述成"这是一个按 X 分组的 Y 问题"
- [ ] 我的解析永远是独立函数，不和业务逻辑揉在一起
- [ ] 我每个 `sorted` 都能说出完整的 tie-break key
- [ ] 我写完每个 part 都会立刻写 2–3 个 assert
- [ ] 我知道金额要用整数分，不用 float
- [ ] 我能一边写一边说，而不是沉默五分钟
- [ ] 我练过至少 5 次 45 分钟计时的冷启动

## 对应材料

- 题目：`loop/rounds/03_phone_screen/ps01`–`ps13`；OA 库里的电面高频 `q19 q21 q22 q25 q20 q08 q18`
- 卡片：`loop/study/20-cards/patterns.md`（跨题模式）
- 前置：`loop/study/00-prereq/04-字符串与解析`、`05-csv与json`
- **模板**：`loop/study/00-prereq/07-模板-常用模式.md` + `templates/`——多 part 骨架和九个高频模式，做题前先把骨架敲熟
- 事实与来源：`loop/LOOP_GUIDE.md` §3
