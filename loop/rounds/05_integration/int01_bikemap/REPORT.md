# int01 BikeMap — report

## Summary
Stripe 目前被报道最频繁的 Integration 例题（Stripe 员工亲述题库随机抽题时点名它作为参照）。核心不是算法，
是三件事：① 陌生数据格式的坑（GeoJSON 坐标顺序 `[lng, lat]`）；② HTTP 客户端的错误归一化（网络错误 / 非
200 / 响应体不可信，全部收敛成一个 `MapError`）；③ 需求逐步加码时函数之间的复用关系（Part n 直接调用
Part n-1 的产出，不重写）。Part 5 的批处理 + 缓存 CLI 是"几乎没人做完"的部分，用来考察时间管理和工程判断
（先把前几个 part 做扎实，而不是平均分配时间导致每个 part 都是半成品）。

## Sources & confidence
High for 5-part 结构：oavoservice.com 的逐 part 拆解文章与 learncswithus.com 的 VO 面经独立给出几乎相同的
5 part 顺序（解析 → POST 拿 PNG → 渲染路线 → 标最近地标 → 批处理/缓存），且 Stripe 员工在 Blind
（`h8lemeaq`）亲口确认 BikeMap 是题库里被抽到的真实题目之一。**具体数据不是原题数据**——Stripe 出题仓库不
允许下载/复制题面（`cn_forums.md` 已确认），`data/ride-simple.json`/`data/landmarks.json` 是本仓库按来源
描述的结构（GeoJSON、约 500 点）用 `random.Random(0)` 重新生成的等价数据；`/render` 接口的具体字段名、错
误码、限流是本仓库设计（源材料只说"POST + JSON body + PNG 响应"）。

## Part-by-part approach
1. `load_coordinates`：读 `features[0].geometry.coordinates`（`[lng,lat]`），swap 成 `(lat,lng)`；对空
   `features`/非 `LineString`/少于 2 点显式抛 `ValueError`，不返回空列表掩盖问题。`first_n` 只是格式化，
   6 位小数、`lat,lng` 无空格。
2. `render_map`：`urllib.request` POST JSON，`urllib.error.HTTPError`（非 2xx）和 `URLError`/`OSError`
   （连接失败）统一包成 `MapError`，调用方不需要知道底层用的是哪个 HTTP 库。
3. `render_route`：复用 `_post_json`，额外把 `landmarks` 转成 `markers`；**在写盘前先检查 8 字节 PNG 魔数**
   ——状态码 200 不代表 body 可信，这是所有"调用外部服务后落盘"代码的通用防御模式。
4. `nearest_point`/`nearest_for_all`：教科书 Haversine（`R=6,371,000`），线性扫描；严格 `<` 比较保证并列
   时取最小下标。10 万点 × 10 地标在 O(n×m) 下仍 < 2s（见 perf），面试官追问会引导到 KD-tree/网格分桶的
   优化方向。
5. `cli`：`argparse` 定义 5 个 flag；缓存 key 是坐标内容的 sha256 前 16 位（不是文件路径），这样同一条路线
   换个文件名也能命中缓存；`index.json` 记录 hash → 来源路径，命中时直接从 `<hash>.png` 复制。

## Pitfalls hidden tests target
- GeoJSON 坐标顺序原样返回（不 swap）—— `test_lng_lat_order_is_swapped_not_identity`
- `load_coordinates` 对畸形输入返回空列表而不是报错，掩盖上游数据问题 —— `test_fewer_than_two_points_raises`
- 把 `urllib.error.URLError`/`HTTPError` 原样冒泡给调用方，而不是统一成 `MapError` —— 两个
  `test_render_map_*_raises_maperror`
- `render_route` 只看状态码 200 就直接落盘，不校验 body 真的是 PNG —— `test_render_route_rejects_non_png_response`
  （用一个假的本地 HTTP server 返回 200 + JSON body 来触发）
- Haversine 距离并列时下标选择不确定（`<=` vs `<`）—— `test_nearest_point_ties_pick_first_index`
- CLI 缓存按文件路径而不是坐标内容做 key，导致同内容换名字不能命中缓存 —— `test_cli_cache_hit_avoids_second_render`
- `--landmarks` 缺省时崩溃（试图打开 `None` 路径）—— 未显式建测例，但 `test_cli_renders_and_prints_summary`
  的姊妹调用路径（`test_cli_batch_multiple_inputs` 不传 `--landmarks`）间接覆盖
- 批处理时多个 `--input` 只处理了第一个，或者输出文件名冲突 —— `test_cli_batch_multiple_inputs`

## Complexity + measured time/memory
`nearest_point` / `nearest_for_all`：O(n) 每个地标，O(n×m) 总体（n=路线点数，m=地标数），纯 Python 循环 +
`math.asin/sqrt`，无第三方依赖。测得：10 万点 × 10 地标 < 1s（本机测量，预算 2s，见 `test_perf_nearest_for_all_100k_points`）。
`render_map`/`render_route` 的耗时由 mockserver 决定（本地环回，单次请求通常 < 50ms）；`cli` 的整体开销
随 `--input` 数量线性增长，每个输入独立走一次渲染或缓存命中。

## Test inventory
20 tests — part1: 7（1 worked example + 3 edge + 1 fmt + 2 io）· part2: 3（1 happy + 2 edge）·
part3: 2（1 happy + 1 edge）· part4: 5（3 happy/worked + 1 io + 1 perf）· part5: 3（1 happy + 1 edge +
1 batch）。
按 marker 统计：part1 7 · part2 3 · part3 2 · part4 5 · part5 3 · edge 7 · fmt 1 · io 3 · perf 1。
`rtk proxy python3 -m pytest loop/rounds/05_integration/int01_bikemap -q` → 20 passed；
`IMPL=starter` 同一命令 → 17 failed / 3 passed（`test_io_empty_stdin` 与
`test_nearest_point_ties_pick_first_index` 对空 starter 的默认返回值恰好也成立，其余全部按预期失败）。

## Skills exercised
S02 嵌套 JSON/GeoJSON 解析 · S18 网络错误分类与归一化（MapError） · S19 增量设计（Part n 复用 Part n-1）·
S20 自测（坐标顺序陷阱要自己先验证一遍再往下写）· S24 领域知识（HTTP 客户端 ergonomics：防御性响应校验、
内容哈希缓存），对照 `skills_matrix.md`。

## 边写边说什么（onsite 话术）
- 打开 `ride-simple.json` 第一件事复述给面试官确认坐标顺序："GeoJSON 标准是 `[lng, lat]`，我在
  `load_coordinates` 里会显式 swap 成 `(lat, lng)`，并在注释里写清楚，防止后面自己或者同事又搞反。"
- 写 `render_map` 时主动说明为什么要包一层 `MapError`："调用方不应该关心我用的是 `urllib` 还是别的 HTTP
  库，统一异常类型能让上层重试逻辑更简单。"
- Part 3 加 PNG 魔数校验时主动提："状态码 200 不代表响应体一定是我期望的格式，尤其是这种二进制响应，我加一
  个最小的防御性校验，避免把损坏文件写到磁盘上。"
- Part 4 讲复杂度时主动带出优化方向："当前是线性扫描 O(n×m)，如果地标或路线点规模再大一个量级，可以用网
  格分桶按经纬度粗筛，或者 KD-tree，把每次查询降到接近 O(log n)。"
- 时间不够时优先保证 Part 1-3 的正确性和错误处理完整，Part 5 的缓存/批处理宁可口头描述设计（内容哈希 key、
  `index.json` 结构）也不要仓促写一个有 bug 的实现——多份面经强调"前几个 part 的质量比做完几个 part 更重
  要"。
