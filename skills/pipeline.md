# 4-Agent 建造管线 (Build Pipeline)

> 定位：单个建造任务（一栋建筑/一段廊道/一处景观）的标准化执行管线。
> 和 workflow.md 的关系：workflow 定义宏观 6 阶段（调研→定稿），本管线嵌套在 Stage 6 的每一个建造子任务中。

## 1. 管线总览

```
         ┌─────────────────────────────────────────────────┐
         │  预处理：扫描 config_v3.py 现有建筑坐标         │
         │         → 生成 occupied_zones 列表               │
         └────────────────────┬────────────────────────────┘
                              │
                    ┌─────────▼─────────┐
                    │  Agent 1: Designer │
                    │  (建筑设计师)       │
                    └─────────┬─────────┘
                              │ 蓝图 JSON
                    ┌─────────▼─────────┐
                    │  Agent 2: Planner  │
                    │  (空间规划师)       │
                    └─────────┬─────────┘
                              │ 建造计划（碰撞检查通过）
                    ┌─────────▼─────────┐
                    │  Agent 3: Executor │
                    │  (建造工程师)       │
                    └─────────┬─────────┘
                              │ Python 脚本执行完毕
                    ┌─────────▼─────────┐
                    │  Agent 4: QA       │
                    │  (建筑审查员)       │
                    └────────┬──────────┘
                             │
                    ┌────────▼──────────┐
                    │ 通过 → 完成        │
                    │ 失败 → 回退修复    │
                    └───────────────────┘
```

### 依赖关系（严格串行，不是并行）

```
预处理 → Designer → Planner → Executor → QA
```

**为什么不并行 Designer 和 Planner：**
Planner 的输入是 Designer 的蓝图。没有蓝图，Planner 无法做碰撞检查。
能并行的只有"预处理扫描"和"用户需求澄清"，这两个是前置步骤，不算管线内。

---

## 2. 四个 Agent 角色定义

### Agent 1: Designer（建筑设计师）

```
═══ 角色定义 ═══

你是中式园林建筑设计师，精通明代江南私家园林形制。
你的任务是把自然语言需求转化为精确的建筑蓝图。

═══ 必读文件 ═══

1. config_v3.py — 全园坐标系、已有建筑参数、水面轮廓
2. blocks.py — 材质映射表（PALETTE dict）
3. skills/chinese-garden-rules.md — 中式园林设计规则
4. skills/building-primitives.md — 可用的建筑原语

═══ 输入格式 ═══

用户会给出自然语言需求，例如：
- "在池塘东南岸建一个六角半亭"
- "翠轩西侧加一段花墙"
- "假山区加一个深潭旁的石亭"

═══ 输出格式：蓝图 JSON ═══

{
  "name": "建筑中文名",
  "type": "pavilion|hall|gallery|wall|bridge|landscape",
  "position": {
    "cx": 85, "cz": 62,
    "ground_y": -60,
    "rationale": "距池塘东南岸(82,60)偏东3格，避开半亭(82,58)"
  },
  "dimensions": {
    "size_x": 9, "size_z": 9,
    "pillar_h": 5,
    "bounding_box": {"x1": 80, "z1": 57, "x2": 90, "z2": 67}
  },
  "form": {
    "roof_type": "hip_pointed",
    "sides_open": ["northwest", "north", "west"],
    "sides_wall": ["south", "east", "southeast"],
    "entrance_width": 3,
    "facing": "northwest"
  },
  "materials": {
    "pillar": "pillar",
    "roof": "roof",
    "base": "base",
    "notes": "使用灰瓦，级别不超过歇山"
  },
  "connections": [
    {
      "target": "主廊道 L4",
      "from_point": [85, -60, 62],
      "path_type": "stone_path",
      "distance": 4
    }
  ],
  "literary_basis": "《牡丹亭·惊梦》: '朝飞暮卷，云霞翠轩'",
  "design_intent": "半亭面向西北朝池塘，呼应'水面风来'意境"
}

═══ 检查清单（设计师自检）═══

□ 屋顶等级不超过歇山（明代四品限制）
□ 和相邻建筑大小交替（大旁小、高旁低）
□ 至少一面与水对话（直接临水或可见水面）
□ 有《牡丹亭》文本依据或合理的园林功能
□ bounding_box 没有超出 GARDEN 边界 (0-120, 0-90)
□ 尺寸满足 MC 最小约束（亭子>=9x9，门洞>=3x3，柱高>=5）
□ 明确了和现有路网的连接方式
```

### Agent 2: Planner（空间规划师）

```
═══ 角色定义 ═══

你是空间规划师，负责碰撞检测、坐标精算和建造阶段排序。
你不做美学判断，只做空间可行性验证。

═══ 必读文件 ═══

1. config_v3.py — 所有建筑的 bounding box（从 cx/cz/size 推算）
2. Designer 输出的蓝图 JSON
3. skills/chinese-garden-rules.md — 水面占比、间距等硬约束

═══ 输入 ═══

Designer 的蓝图 JSON + config_v3.py 中的 ALL_BUILDINGS 列表。

═══ 输出格式：建造计划 ═══

## 碰撞检测报告

| 检查项 | 结果 | 详情 |
|--------|------|------|
| 水面碰撞 | ✅/❌ | 四角是否在 MAIN_LAKE shoreline 内 |
| 建筑碰撞 | ✅/❌ | 与最近建筑的距离和方向 |
| 廊道碰撞 | ✅/❌ | 是否穿越 MAIN_CORRIDOR/WEST_CORRIDOR 路径 |
| 围墙碰撞 | ✅/❌ | 是否超出 WALL perimeter |
| 地形适配 | ✅/❌ | ground_y 是否匹配 TERRAIN_ZONES |

## 碰撞修正（如有）

原始位置 (82, 58) 与 HALF_PAVILION_SE 完全重叠。
→ 建议修正为 (85, 62)，距半亭中心5格，无碰撞。
→ 修正后 ground_y = -60（标准地面区）。

## 建造阶段计划

Phase 1: 清除区域
  fill air: (80, -60, 57) to (90, -48, 67)  ← bounding_box + Y向上12格

Phase 2: 台基
  fill stone_bricks: (81, -60, 58) to (89, -59, 66)

Phase 3: 柱+梁
  4 根柱: [(82,-59,59), (88,-59,59), (82,-59,65), (88,-59,65)]
  高度: -59 to -54 (5格)

Phase 4: 屋顶
  攒尖顶 5 层缩进

Phase 5: 细节
  栏杆、灯笼、地面铺装

Phase 6: 连接
  石径从 (85,62) 到主廊道 (84,55)，宽 3 格

═══ 检查清单（规划师自检）═══

□ 四角+中心共 5 个点的水面碰撞检测（代入 shoreline 多边形）
□ 与 ALL_BUILDINGS 中每栋建筑的 bounding box 最近距离 ≥ 2 格
□ 不穿越任何 CORRIDOR waypoints 连线（在路径两侧各 3 格缓冲区内）
□ ground_y 和 TERRAIN_ZONES 一致
□ 建造总命令数预估 < 2000（单栋建筑）
□ fill 坐标顺序正确（x1 ≤ x2, y1 ≤ y2, z1 ≤ z2）
□ 连接路径不穿越水面（如穿越则必须用桥/汀步）
```

### Agent 3: Executor（建造工程师）

```
═══ 角色定义 ═══

你是 Minecraft 建造工程师，负责把建造计划转化为可执行的 Python 脚本。
你不做设计决策，严格按照 Planner 的建造计划执行。

═══ 必读文件 ═══

1. builder.py — MinecraftBuilder API（fill/setblock/line/circle 等）
2. blocks.py — PALETTE 材质映射
3. phase3_buildings.py — 已有建筑的代码风格参考
4. Planner 输出的建造计划

═══ 输入 ═══

Planner 验证通过的建造计划（含精确坐标、阶段排序、命令预算）。

═══ 输出格式：Python 脚本 ═══

文件名: structures/[building_name].py
或追加到: phase3_buildings.py（如果是小型结构）

代码规范:

```python
"""[建筑中文名] — [形制简述]

位置: (cx, cz), ground_y
蓝图来源: Designer Agent, [日期]
碰撞检查: Planner Agent, [日期], 通过
"""

import sys
sys.path.insert(0, '/Users/lambertlin/minecraft-server/scripts')
from builder import MinecraftBuilder
import config_v3 as cfg
from blocks import PALETTE

def build_xxx(b: MinecraftBuilder):
    """一体化建造函数 — 从清除到完成"""
    # ── 参数 ──
    cx, cz = 85, 62
    gy = -60
    # ... 从 config 或 Planner 计划读取

    # ── Phase 1: 清除 ──
    b.clear(x1, gy, z1, x2, gy+12, z2)

    # ── Phase 2: 台基 ──
    # ...

    # ── Phase 3: 柱+梁 ──
    # ...

    # ── Phase 4: 屋顶 ──
    # ...

    # ── Phase 5: 细节 ──
    # ...

    # ── Phase 6: 连接 ──
    # ...

    print(f"  完成: [建筑名], 命令数约 {b.cmd_count}")

if __name__ == "__main__":
    with MinecraftBuilder() as b:
        build_xxx(b)
```

═══ 代码检查清单（工程师自检）═══

□ 一个函数完成全部建造（不分步骤文件）
□ 先 clear 再建（避免残留）
□ 台基→柱→梁→墙→屋顶→细节 严格顺序
□ fill 坐标 x1 ≤ x2, y1 ≤ y2, z1 ≤ z2
□ 所有叶子方块加 [persistent=true]
□ 楼梯 facing 方向正确（低端朝 facing 方向）
□ 入口不放栏杆（≥ 3 格宽留空）
□ 总命令数在 Planner 预算内
□ 用 b.fill 而非 b.setblock 处理大面积（效率）
□ 地面连续无断裂
□ 脚本可独立运行（if __name__ == "__main__"）
```

### Agent 4: QA（建筑审查员）

```
═══ 角色定义 ═══

你是建筑审查员。你在 Executor 脚本执行后，验证建造结果是否符合蓝图。
你只负责发现问题和分类严重度，不负责设计修复方案。
（修复方案由 Planner 或 Executor 根据你的报告处理。）

═══ 必读文件 ═══

1. Designer 的蓝图 JSON（设计意图）
2. Planner 的建造计划（精确坐标）
3. Executor 的 Python 脚本（实际执行逻辑）
4. config_v3.py — 上下文

═══ 验证方法 ═══

1. 代码静态审查: 逐行对比脚本和建造计划的坐标
2. 游戏内验证（如有 MCP 连接）:
   - 用 minecraft-mcp get-block-info 抽查关键位置
   - 用 find-block 搜索指定范围内方块
3. 玩家视角巡检: tp 到建筑四面+内部+屋顶，截图对比蓝图

═══ 输出格式：验证报告 ═══

## 验证报告: [建筑名]

### 总体判定: ✅ 通过 / ❌ 不通过

### 逐项检查

| # | 检查项 | 结果 | 严重度 | 详情 |
|---|--------|------|--------|------|
| 1 | 台基完整性 | ✅ | - | 台基 (81,58)-(89,66), 高度2层 |
| 2 | 柱子数量 | ✅ | - | 4根，位置正确 |
| 3 | 屋顶覆盖 | ✅ | - | 5层攒尖，顶部有宝顶 |
| 4 | 入口通行 | ❌ | P0-阻塞 | 西北入口被栏杆挡住 |
| 5 | 地面连续 | ✅ | - | 台基→散水→石径连续 |
| 6 | 材质正确 | ✅ | - | 柱crimson_stem, 瓦stone_brick |

### 严重度分级

- P0-阻塞: 影响通行或结构完整性 → 必须修复
- P1-功能: 影响功能但不阻塞（如缺灯笼、栏杆缺口）→ 应该修复
- P2-美观: 纯美观问题（如楼梯方向微调）→ 建议修复

### 问题汇总（如有）

问题 4: 西北入口栏杆阻塞
  位置: (83, -58, 60) 到 (85, -58, 60)
  原因: Executor 脚本第 47 行栏杆 for 循环未跳过入口区域
  严重度: P0-阻塞
  → 交回 Executor 修复

═══ 检查清单 ═══

□ 台基: 尺寸正确、材质正确、散水带完整
□ 柱子: 数量正确、间距正确、有柱础
□ 屋顶: 类型正确、完整覆盖、飞檐翘角、有宝顶/脊兽
□ 入口: 所有朝向的入口 ≥ 3格宽 × 3格高、无障碍物
□ 栏杆: 该有的地方有、入口处没有
□ 地面: 连续无断裂、棋盘格对齐
□ 灯笼: 四柱或入口处有悬挂
□ 连接: 和已有路网衔接正确、高差有台阶
□ 碰撞: 没有侵入水面/相邻建筑/廊道
□ 代码: 命令数合理、无死代码、可重跑
```

---

## 3. 管线编排规则

### 正常流程

```
规则 1: 严格串行
  Designer → Planner → Executor → QA
  每个 Agent 必须等上一个完成并输出结果后才能开始。

规则 2: Planner 有否决权
  如果 Planner 发现碰撞无法解决（如请求位置在湖中央），
  直接拒绝并附理由，回到 Designer 重新选址。
  不要勉强把建筑塞进不合适的位置。

规则 3: QA 只报告不修复
  QA 发现问题后，按严重度分类输出报告。
  修复决策权在 Planner（坐标问题）或 Executor（代码问题）。
```

### 失败回退流程

```
QA 失败回退:

  情况 A — P1/P2 级问题（代码 bug / 细节遗漏）:
    QA 报告 → Executor 修复 → QA 再验
    最多 3 轮。

  情况 B — P0 级问题（结构性错误，如位置偏了、屋顶类型错了）:
    QA 报告 → Planner 重新审查 → Executor 重写 → QA 再验
    最多 2 轮。

  情况 C — 连续 3 轮 QA 仍不通过:
    整个管线回到 Designer，重新出蓝图。
    上一轮所有 QA 报告作为 Designer 的输入约束。

回退计数器:
  executor_retry = 0  # Executor 修复次数
  pipeline_retry = 0  # 整条管线重启次数
  MAX_EXECUTOR_RETRY = 3
  MAX_PIPELINE_RETRY = 2  # 最多重启2次，超过则人工介入
```

### 流程图（含回退）

```
                      ┌─────────────┐
                      │  Designer   │ ◄──────────────────────────────┐
                      └──────┬──────┘                                │
                             │ 蓝图 JSON                             │
                      ┌──────▼──────┐                                │
                      │  Planner    │──── 碰撞不可解 ────► Designer  │
                      └──────┬──────┘                                │
                             │ 建造计划                               │
                      ┌──────▼──────┐                                │
               ┌─────►│  Executor   │ ◄─── P0 问题 ── Planner ◄─┐   │
               │      └──────┬──────┘                            │   │
               │             │ 脚本执行                           │   │
               │      ┌──────▼──────┐                            │   │
               │      │    QA       │                            │   │
               │      └──────┬──────┘                            │   │
               │             │                                   │   │
               │    ┌────────┼────────┐                          │   │
               │    │        │        │                          │   │
               │   ✅通过  P1/P2    P0级                         │   │
               │    │     问题      问题                          │   │
               │    │        │        │                          │   │
               │    ▼        │        └──────────────────────────┘   │
               │  完成!      │                                       │
               │             │ retry < 3                             │
               └─────────────┘                                       │
                             │ retry >= 3                             │
                             └───────────────────────────────────────┘
```

---

## 4. 实际使用示例：建造一栋临水半亭

### 用户输入

```
"在池塘东南岸建一个六角半亭，面朝池塘"
```

### Step 1: Designer

```json
{
  "name": "东南半亭",
  "type": "pavilion",
  "position": {
    "cx": 82, "cz": 58,
    "ground_y": -60,
    "rationale": "紧贴池塘东南岸(82,60)，面向西北朝水面"
  },
  "dimensions": {
    "size_x": 7, "size_z": 7,
    "pillar_h": 5,
    "bounding_box": {"x1": 78, "z1": 54, "x2": 86, "z2": 62}
  },
  "form": {
    "roof_type": "hip_pointed",
    "sides_open": ["northwest", "north", "west"],
    "sides_wall": ["south", "east", "southeast"],
    "entrance_width": 3,
    "facing": "northwest"
  },
  "connections": [
    {
      "target": "主廊道 L4 (82,58)",
      "from_point": [82, -60, 56],
      "path_type": "direct",
      "distance": 0
    }
  ],
  "literary_basis": "游园惊梦场景中水边休憩之所",
  "design_intent": "半亭三面开敞面向池塘，背墙靠廊道，形成观水节点"
}
```

### Step 2: Planner

```
## 碰撞检测报告

| 检查项 | 结果 | 详情 |
|--------|------|------|
| 水面碰撞 | ⚠️ | (78,62)在岸线边缘，需确认不入水 |
| 建筑碰撞 | ❌ | cx=82, cz=58 与 HALF_PAVILION_SE 完全重叠！ |
| 廊道碰撞 | ✅ | 主廊道 L4 就在此处，可直接衔接 |
| 围墙碰撞 | ✅ | 在园内 |
| 地形适配 | ✅ | 标准地面区，ground_y=-60 正确 |

## 碰撞修正

config_v3.py 第203-211行: HALF_PAVILION_SE 已经定义在 (82, 58)。
→ 方案A: 这就是那个半亭，Designer 只需确认参数然后交给 Executor 重建
→ 方案B: 如果要新增第二个半亭，建议移到 (78, 64)，主廊 L3(74,65) 旁

采用方案A（重建已有半亭，增加六角形制）。

## 建造阶段计划

Phase 1: 清除 (78,-60,54) to (86,-48,62)
Phase 2: 台基 7x7 石砖，高1层
Phase 3: 柱子 3 根（半亭只有前排3柱，后靠墙）
  位置: (80,-59,56), (82,-59,56), (84,-59,56)
  高度: 5格
Phase 4: 后墙 — 南面+东南面 white_concrete
Phase 5: 攒尖顶 — 3层缩进
Phase 6: 前排栏杆 — 入口正面 3 格留空
Phase 7: 衔接 — 主廊道 L4 直接连接，无需额外铺路

命令预算: ~400
```

### Step 3: Executor

```python
def build_half_pavilion_se(b: MinecraftBuilder):
    """东南半亭 — 六角攒尖半亭，面向西北朝池塘

    位置: (82, 58), ground_y=-60
    蓝图: Designer Agent, 2026-04-08
    碰撞: Planner Agent, 2026-04-08, 方案A（重建）
    """
    cx, cz, gy = 82, 58, -60
    # ... 建造代码 ...
    # Phase 1: clear
    b.clear(78, gy, 54, 86, gy+12, 62)
    # Phase 2-7: 按计划执行
    # ...
```

### Step 4: QA

```
## 验证报告: 东南半亭

### 总体判定: ❌ 不通过 (1 个 P0 问题)

| # | 检查项 | 结果 | 严重度 | 详情 |
|---|--------|------|--------|------|
| 1 | 台基 | ✅ | - | 7x7, stone_bricks |
| 2 | 柱子 | ✅ | - | 3根前柱，位置正确 |
| 3 | 后墙 | ✅ | - | 南+东南面 white_concrete |
| 4 | 屋顶 | ✅ | - | 3层攒尖，完整 |
| 5 | 入口通行 | ❌ | P0-阻塞 | 西北入口 (80,-58,56)-(82,-58,56) 有栏杆 |
| 6 | 灯笼 | ❌ | P1-功能 | 无灯笼 |

### 问题详情

问题 5 (P0): 入口栏杆阻塞
  位置: x=80 到 x=82, y=-58, z=56
  原因: 栏杆循环没有判断 facing 方向跳过入口
  → 交回 Executor 修复（删除该段栏杆）

问题 6 (P1): 缺灯笼
  建议: 前排两根外柱 (80,-54,56) 和 (84,-54,56) 各挂一个
  → 交回 Executor 补充
```

### Step 5: Executor 修复（第 1 轮）

```
修复内容:
1. 删除 (80,-58,56) 到 (82,-58,56) 的栏杆 → fill air
2. 在 (80,-54,56) 和 (84,-54,56) 放灯笼

→ QA 再验 → ✅ 全部通过
```

---

## 5. 和现有系统的集成

### 共享状态层: config_v3.py

```
config_v3.py 是全园的单一真相源 (Single Source of Truth)。

Designer 读取:
  - GARDEN 边界 → 确保不越界
  - ALL_BUILDINGS → 确保大小交替、高低错落
  - MAIN_LAKE shoreline → 确保与水对话
  - TERRAIN_ZONES → 确定 ground_y

Planner 读取:
  - ALL_BUILDINGS → 碰撞检测（逐一计算 bounding box）
  - MAIN_CORRIDOR / WEST_CORRIDOR / HIGHLAND_PATH → 廊道碰撞
  - ALL_BRIDGES → 桥梁碰撞
  - MAIN_LAKE / CREEK / DEEP_POOL → 水面碰撞

管线完成后更新:
  新建筑参数追加到 config_v3.py 的 ALL_BUILDINGS 列表中。
  这一步由人工确认后执行，管线不自动修改 config。
```

### 执行层: builder.py

```
Executor 的唯一输出接口。

关键 API:
  b.fill()      — 大面积填充（台基、墙、屋顶），自动分片
  b.setblock()  — 单方块放置（灯笼、宝顶、特殊位置）
  b.clear()     — 区域清除（建造前清理）
  b.line()      — 画线（不规则路径、斜梁）
  b.circle_xz() — 圆形结构（六角亭底座）
  b.register_bbox() — 注册 bounding box（支持撤销）

Executor 输出的脚本必须:
  1. 用 MinecraftBuilder 的 context manager (with 语句)
  2. 所有坐标硬编码或从 config 计算，不用 input()
  3. 可独立运行 (if __name__ == "__main__")
  4. 可通过 b.undo(name) 撤销
```

### QA 层: 验证工具

```
QA 目前没有独立的 verifier.py，验证靠:

1. 代码审查 — 逐行对比 Executor 脚本 vs Planner 计划的坐标
2. MCP 验证 — 通过 minecraft-mcp 工具:
   - get-block-info: 抽查指定坐标的方块是否正确
   - find-block: 搜索范围内特定方块数量
   - get-position + look-at: 模拟巡检视角
3. 截图对比 — browser_take_screenshot 截取游戏画面

未来可以封装为 verifier.py:
  verify_building(name, blueprint_json) → VerifyReport
  verify_collision(name, config) → CollisionReport
  verify_connectivity(name, corridors) → ConnectivityReport
```

### 知识库层: skills/

```
管线中各 Agent 按需加载的 skill 文件:

Designer 加载:
  - chinese-garden-rules.md → 设计规则约束
  - building-primitives.md → 了解可用的建筑原语

Planner 加载:
  - chinese-garden-rules.md → 水面占比等硬约束

Executor 加载:
  - building-primitives.md → L1/L2/L3 原语 API
  - prompt-templates.md → 代码风格参考

QA 加载:
  - workflow.md → 验证检查清单
  - chinese-garden-rules.md → MC 特有规则（门洞尺寸等）
```

---

## 6. 快速启动模板

复制以下内容作为启动一次管线的 prompt：

```
我要用 4-Agent 建造管线来 [建造任务描述]。

请按以下顺序执行：

1. **Designer**: 读 config_v3.py 和 chinese-garden-rules.md，
   输出蓝图 JSON（位置、尺寸、形制、连接、文学依据）。

2. **Planner**: 读蓝图 + config_v3.py ALL_BUILDINGS，
   做碰撞检测（水面/建筑/廊道/围墙/地形），
   输出建造计划（阶段排序 + 精确坐标 + 命令预算）。

3. **Executor**: 读建造计划 + builder.py + blocks.py，
   写一体化建造函数，输出 Python 脚本。

4. **QA**: 对比蓝图和脚本，逐项检查
   （台基/柱/屋顶/入口/栏杆/地面/灯笼/连接/碰撞/代码质量），
   输出验证报告。

如有 QA 失败，按回退规则处理（P1/P2→Executor修复，P0→Planner重审）。
```
