"""v3 建筑集合 — 牡丹亭 + 芍药阑 + 翠轩

牡丹亭: 17×17须弥座台基, 4柱攒尖亭, 6格柱高, 飞檐翘角
芍药阑: 11×9围栏花圃, 芍药密植, 石径穿越
翠轩:   17×11悬山顶敞厅, 东面面水全开敞, 西墙封闭

v3 变更:
- 柱子: stripped_crimson_stem (红漆柱)
- 屋顶: stone_brick_stairs (灰瓦)
- 栏杆: crimson_fence
- 飞檐: dark_oak_stairs/slab 翘角
- 所有入口至少 3格宽 x 3格高, 可自由走入
"""

import sys; sys.path.insert(0, '/Users/lambertlin/minecraft-server/scripts')
import random
from builder import MinecraftBuilder
from blocks import PALETTE, GROUND_Y, BUILD_Y
from config import PAVILION, PEONY_RAIL, HALL


# ========================================================================
# 1. 牡丹亭 — 四角攒尖亭
# ========================================================================

def build_pavilion(b: MinecraftBuilder):
    """建造牡丹亭（四角攒尖亭）

    17×17 须弥座台基, 4 柱 (11×11 柱距), 6格柱高,
    攒尖屋顶逐层缩小, 飞檐翘角, 避雷针宝顶。
    四面各留 5 格宽入口（无栏杆）, 柱间净空 9×9。
    """
    cfg = PAVILION
    cx, cz = cfg["cx"], cfg["cz"]
    gy = cfg["ground_y"]
    R_BASE = cfg["r_base"]    # 8 → 17×17
    R_COL = cfg["r_col"]      # 5 → 11×11 柱距, 净空 9×9
    PILLAR_H = cfg["pillar_h"]  # 6

    print(f"=== 牡丹亭 v3 at ({cx}, {gy}, {cz}) ===")

    # ── 方块 ──
    BASE       = PALETTE["base"]           # stone_bricks
    BASE_STEP  = PALETTE["base_step"]      # stone_brick_stairs
    BASE_SLAB  = PALETTE["base_slab"]      # stone_brick_slab
    BASE_COL   = PALETTE["base_col"]       # polished_andesite
    PILLAR     = PALETTE["pillar"]         # stripped_crimson_stem
    BEAM       = PALETTE["beam"]           # dark_oak_planks
    ROOF       = PALETTE["roof"]           # stone_brick_stairs
    ROOF_BLOCK = PALETTE["roof_block"]     # stone_bricks
    ROOF_SLAB  = PALETTE["roof_slab"]      # stone_brick_slab
    FLOOR      = PALETTE["floor"]          # smooth_stone
    FLOOR_ALT  = PALETTE["floor_alt"]      # stone_bricks (棋盘格交替)
    RAIL       = PALETTE["rail"]           # crimson_fence
    ROD        = PALETTE["lightning_rod"]
    EAVE_STAIR = PALETTE["eave_outer"]     # dark_oak_stairs
    EAVE_SLAB  = PALETTE["eave_slab"]      # dark_oak_slab
    LANTERN    = PALETTE["lantern"]

    # ── Y 坐标体系 ──
    # gy      : 高地地面
    # gy+1    : 台基底层 (stone_bricks 满铺 17×17)
    # gy+2    : 台基上层 (楼梯围边 + 半砖) = 台面
    # gy+3    : 地面铺装 + 栏杆层
    # gy+3 ~ gy+3+PILLAR_H-1 = gy+8 : 柱子 (6格: +3,+4,+5,+6,+7,+8)
    # gy+9    : 额枋/梁层
    # gy+10~  : 屋顶层
    base_y   = gy          # 台基底面
    floor_y  = gy + 2      # 台面 (台基顶)
    pave_y   = gy + 3      # 铺装层 (踩踏面)
    pillar_b = gy + 3      # 柱底 (含柱础在 pave_y)
    pillar_t = gy + 3 + PILLAR_H - 1  # gy+8, 柱顶
    beam_y   = pillar_t + 1            # gy+9, 额枋
    roof_y   = beam_y + 1              # gy+10, 屋顶起始

    # 头顶净高 = beam_y - pave_y = gy+9 - gy+3 = 6格 (足够通行)

    # ================================================================
    # 1. 台基（须弥座）— 2格高
    # ================================================================
    print("  [1/8] 台基...")

    # 底层 (base_y+1): stone_bricks 满铺 17×17
    b.fill(cx - R_BASE, base_y + 1, cz - R_BASE,
           cx + R_BASE, base_y + 1, cz + R_BASE, BASE)

    # 上层 (base_y+2): 中间填 top-half slab
    b.fill(cx - R_BASE + 1, base_y + 2, cz - R_BASE + 1,
           cx + R_BASE - 1, base_y + 2, cz + R_BASE - 1,
           f"{BASE_SLAB}[type=top]")

    # 四面楼梯围边 (朝外)
    for x in range(cx - R_BASE, cx + R_BASE + 1):
        b.setblock(x, base_y + 2, cz - R_BASE,
                   f"{BASE_STEP}[facing=north,half=top]")
        b.setblock(x, base_y + 2, cz + R_BASE,
                   f"{BASE_STEP}[facing=south,half=top]")
    for z in range(cz - R_BASE, cz + R_BASE + 1):
        b.setblock(cx - R_BASE, base_y + 2, z,
                   f"{BASE_STEP}[facing=west,half=top]")
        b.setblock(cx + R_BASE, base_y + 2, z,
                   f"{BASE_STEP}[facing=east,half=top]")

    # 四面踏步 (每面中间 5 格)
    # 踏步从 base_y 到 base_y+2, 共 2 级
    step_half = 2  # 中间5格: cx-2 ~ cx+2

    # 北面踏步
    for x in range(cx - step_half, cx + step_half + 1):
        b.setblock(x, base_y + 1, cz - R_BASE - 1,
                   f"{BASE_STEP}[facing=south,half=bottom]")
        b.setblock(x, base_y + 2, cz - R_BASE,
                   f"{BASE_STEP}[facing=south,half=bottom]")
    # 南面踏步
    for x in range(cx - step_half, cx + step_half + 1):
        b.setblock(x, base_y + 1, cz + R_BASE + 1,
                   f"{BASE_STEP}[facing=north,half=bottom]")
        b.setblock(x, base_y + 2, cz + R_BASE,
                   f"{BASE_STEP}[facing=north,half=bottom]")
    # 西面踏步
    for z in range(cz - step_half, cz + step_half + 1):
        b.setblock(cx - R_BASE - 1, base_y + 1, z,
                   f"{BASE_STEP}[facing=east,half=bottom]")
        b.setblock(cx - R_BASE, base_y + 2, z,
                   f"{BASE_STEP}[facing=east,half=bottom]")
    # 东面踏步
    for z in range(cz - step_half, cz + step_half + 1):
        b.setblock(cx + R_BASE + 1, base_y + 1, z,
                   f"{BASE_STEP}[facing=west,half=bottom]")
        b.setblock(cx + R_BASE, base_y + 2, z,
                   f"{BASE_STEP}[facing=west,half=bottom]")

    # ================================================================
    # 2. 地面铺装 — 棋盘格 smooth_stone + polished_andesite
    # ================================================================
    print("  [2/8] 地面铺装...")

    for x in range(cx - R_BASE + 1, cx + R_BASE):
        for z in range(cz - R_BASE + 1, cz + R_BASE):
            if (x + z) % 2 == 0:
                b.setblock(x, pave_y, z, FLOOR)
            else:
                b.setblock(x, pave_y, z, FLOOR_ALT)

    # ================================================================
    # 3. 柱子 + 柱础 — 四角各一根
    # ================================================================
    print("  [3/8] 柱子 + 柱础...")

    col_positions = [
        (cx - R_COL, cz - R_COL),
        (cx + R_COL, cz - R_COL),
        (cx - R_COL, cz + R_COL),
        (cx + R_COL, cz + R_COL),
    ]

    for px, pz in col_positions:
        # 柱础 (磨制安山岩)
        b.setblock(px, pave_y, pz, BASE_COL)
        # 柱身 (6格高: pave_y+1 即 pillar_b+1? 不, pillar_b=pave_y=gy+3)
        # 实际柱子从 pave_y (柱础) 上面开始
        # 但柱础占了 pave_y, 柱身从 pave_y+1 到 pillar_t
        # pillar_b=gy+3, pillar_t=gy+8, 6格: +3 是柱础, +4~+8 是柱身(5格)
        # 不对 -- pillar_h=6 应该是柱身6格。重新算:
        # 柱础在 pave_y, 柱身 6 格从 pave_y+1 到 pave_y+6=gy+9
        # 但 beam_y=gy+9, 柱顶和梁齐平也可以, 柱身 pave_y+1 ~ beam_y-1 = 5格
        # 或者柱身 pave_y ~ pillar_t, 柱础在 pave_y 下面
        #
        # 让我重新定义清楚:
        # 柱础在 pave_y 层 (地面层)
        # 柱身从 pave_y+1 到 pave_y+PILLAR_H = gy+3+6 = gy+9
        # 额枋在 pave_y+PILLAR_H+1 = gy+10 (柱顶上方)
        # 不, 这样头高就是 PILLAR_H+1=7 格了, 太高
        #
        # 更合理: 柱身包含柱础位置, 6格从 pave_y 到 pave_y+5=gy+8
        # 额枋 beam_y = pave_y+6 = gy+9
        # 头顶净高 = beam_y - (pave_y+1) = 5 格 (走路层到梁底)
        # 5格净高够了 (玩家2格高)
        #
        # 实际上上面已算好: pillar_b=gy+3=pave_y, pillar_t=gy+8, beam_y=gy+9
        # 柱身: pillar_b ~ pillar_t = 6格 (gy+3,+4,+5,+6,+7,+8)
        # 柱础是柱底那格, 不额外占层
        b.fill(px, pillar_b, pz, px, pillar_t, pz, PILLAR)
        # 柱础覆盖柱底那格
        b.setblock(px, pillar_b, pz, BASE_COL)

    # ================================================================
    # 4. 额枋 + 斗拱
    # ================================================================
    print("  [4/8] 额枋 + 斗拱...")

    # 四条梁连接柱顶上方 (beam_y)
    b.fill(cx - R_COL, beam_y, cz - R_COL,
           cx + R_COL, beam_y, cz - R_COL, BEAM)  # 北梁
    b.fill(cx - R_COL, beam_y, cz + R_COL,
           cx + R_COL, beam_y, cz + R_COL, BEAM)  # 南梁
    b.fill(cx - R_COL, beam_y, cz - R_COL,
           cx - R_COL, beam_y, cz + R_COL, BEAM)  # 西梁
    b.fill(cx + R_COL, beam_y, cz - R_COL,
           cx + R_COL, beam_y, cz + R_COL, BEAM)  # 东梁

    # 斗拱: 每根柱子顶部四方向出挑 (dark_oak_stairs)
    dougong = EAVE_STAIR
    for px, pz in col_positions:
        b.setblock(px, beam_y, pz - 1,
                   f"{dougong}[facing=south,half=top]")
        b.setblock(px, beam_y, pz + 1,
                   f"{dougong}[facing=north,half=top]")
        b.setblock(px - 1, beam_y, pz,
                   f"{dougong}[facing=east,half=top]")
        b.setblock(px + 1, beam_y, pz,
                   f"{dougong}[facing=west,half=top]")

    # ================================================================
    # 5. 攒尖屋顶 — 逐层缩小
    # ================================================================
    print("  [5/8] 攒尖屋顶...")

    _build_pavilion_roof(b, cx, cz, roof_y, ROOF, ROOF_BLOCK, ROOF_SLAB,
                         EAVE_STAIR, EAVE_SLAB, ROD)

    # ================================================================
    # 6. 栏杆 — 四面各留中间 5 格入口不放栏杆
    # ================================================================
    print("  [6/8] 栏杆...")

    rail_y = pillar_b + 1  # 栏杆在地面上 1 格 (pave_y+1)
    entrance_half = 2      # 入口: cx-2 ~ cx+2 = 5格

    # 北面栏杆 (z = cz - R_COL)
    for x in range(cx - R_COL + 1, cx + R_COL):
        if cx - entrance_half <= x <= cx + entrance_half:
            continue  # 入口留空
        b.setblock(x, rail_y, cz - R_COL, RAIL)

    # 南面栏杆 (z = cz + R_COL)
    for x in range(cx - R_COL + 1, cx + R_COL):
        if cx - entrance_half <= x <= cx + entrance_half:
            continue
        b.setblock(x, rail_y, cz + R_COL, RAIL)

    # 西面栏杆 (x = cx - R_COL)
    for z in range(cz - R_COL + 1, cz + R_COL):
        if cz - entrance_half <= z <= cz + entrance_half:
            continue
        b.setblock(cx - R_COL, rail_y, z, RAIL)

    # 东面栏杆 (x = cx + R_COL)
    for z in range(cz - R_COL + 1, cz + R_COL):
        if cz - entrance_half <= z <= cz + entrance_half:
            continue
        b.setblock(cx + R_COL, rail_y, z, RAIL)

    # ================================================================
    # 7. 灯笼 — 四根柱子梁下各挂一盏
    # ================================================================
    print("  [7/8] 灯笼...")

    for px, pz in col_positions:
        b.setblock(px, beam_y - 1, pz,
                   f'{LANTERN}[hanging=true]')

    # ================================================================
    # 8. 注册边界框
    # ================================================================
    print("  [8/8] 注册边界框...")

    b.register_bbox("pavilion",
                    cx - R_BASE - 2, base_y, cz - R_BASE - 2,
                    cx + R_BASE + 2, roof_y + 6, cz + R_BASE + 2)

    print("  牡丹亭 v3 建造完成!")


def _build_pavilion_roof(b, cx, cz, roof_y, ROOF, ROOF_BLOCK, ROOF_SLAB,
                         EAVE_STAIR, EAVE_SLAB, ROD):
    """攒尖顶: 11×11 → 9×9 → 7×7 → 5×5 → 3×3 → 宝顶

    含飞檐翘角（网易教程做法）:
    - 最外层 dark_oak_slab 延伸 2 格
    - 四角各 3 块倒置 dark_oak_stairs 上翘
    """

    def _roof_ring(y, half_size, stair_block):
        """放置一圈屋顶楼梯, 含四角 outer 形态"""
        n = cz - half_size
        s = cz + half_size
        w = cx - half_size
        e = cx + half_size

        # 北面
        for x in range(w + 1, e):
            b.setblock(x, y, n, f"{stair_block}[facing=south,half=bottom]")
        # 南面
        for x in range(w + 1, e):
            b.setblock(x, y, s, f"{stair_block}[facing=north,half=bottom]")
        # 西面
        for z in range(n + 1, s):
            b.setblock(w, y, z, f"{stair_block}[facing=east,half=bottom]")
        # 东面
        for z in range(n + 1, s):
            b.setblock(e, y, z, f"{stair_block}[facing=west,half=bottom]")

        # 四角转角
        b.setblock(w, y, n,
                   f"{stair_block}[facing=south,half=bottom,shape=outer_right]")
        b.setblock(e, y, n,
                   f"{stair_block}[facing=south,half=bottom,shape=outer_left]")
        b.setblock(w, y, s,
                   f"{stair_block}[facing=north,half=bottom,shape=outer_left]")
        b.setblock(e, y, s,
                   f"{stair_block}[facing=north,half=bottom,shape=outer_right]")

    # ── 飞檐层 (roof_y): 最外层 dark_oak_slab 延伸 ──
    # 檐口: 在 11×11 (half=5) 的外围再延伸 2 格 → half=7 (15×15)
    # 用 dark_oak_slab 铺一圈
    eave_hs = 7  # 飞檐外延半径
    for x in range(cx - eave_hs, cx + eave_hs + 1):
        for z in range(cz - eave_hs, cz + eave_hs + 1):
            on_edge = (x == cx - eave_hs or x == cx + eave_hs or
                       z == cz - eave_hs or z == cz + eave_hs)
            # 只放外围 2 圈 (半径 6~7 的格子)
            dx = abs(x - cx)
            dz = abs(z - cz)
            if dx >= 6 or dz >= 6:
                if on_edge or dx == 6 or dz == 6:
                    # 最外圈用 slab, 次外圈也用 slab
                    if dx >= 6 and dz >= 6:
                        continue  # 角落区域留给翘角
                    b.setblock(x, roof_y, z, f"{EAVE_SLAB}[type=top]")

    # ── 飞檐翘角: 四角各用 dark_oak_stairs 堆叠上翘 ──
    # 每角 9 块台阶 (3x3 区域, 角上倒置上翘)
    corners = [
        (-1, -1, "south", "east"),   # 西北角
        ( 1, -1, "south", "west"),   # 东北角
        (-1,  1, "north", "east"),   # 西南角
        ( 1,  1, "north", "west"),   # 东南角
    ]

    for sx, sz, fz, fx in corners:
        # 角顶点
        corner_x = cx + sx * eave_hs
        corner_z = cz + sz * eave_hs

        # 3x3 翘角区域
        for dx in range(3):
            for dz in range(3):
                ax = corner_x - sx * dx
                az = corner_z - sz * dz

                if dx == 0 and dz == 0:
                    # 角顶: 最高, 倒置外角楼梯
                    b.setblock(ax, roof_y, az,
                               f"{EAVE_STAIR}[facing={fz},half=top,shape=outer_right]"
                               if sx < 0 else
                               f"{EAVE_STAIR}[facing={fz},half=top,shape=outer_left]")
                elif dx == 0 or dz == 0:
                    # 边: 倒置楼梯
                    if dx == 0:
                        b.setblock(ax, roof_y, az,
                                   f"{EAVE_STAIR}[facing={fz},half=top]")
                    else:
                        b.setblock(ax, roof_y, az,
                                   f"{EAVE_STAIR}[facing={fx},half=top]")
                else:
                    # 内部: dark_oak_slab
                    b.setblock(ax, roof_y, az, f"{EAVE_SLAB}[type=top]")

    # ── 第1层 (roof_y+1): 11×11 (half=5) ──
    _roof_ring(roof_y + 1, 5, ROOF)
    # 填充内部
    b.fill(cx - 4, roof_y + 1, cz - 4,
           cx + 4, roof_y + 1, cz + 4, ROOF_BLOCK)

    # ── 第2层 (roof_y+2): 9×9 (half=4) ──
    _roof_ring(roof_y + 2, 4, ROOF)
    b.fill(cx - 3, roof_y + 2, cz - 3,
           cx + 3, roof_y + 2, cz + 3, ROOF_BLOCK)

    # ── 第3层 (roof_y+3): 7×7 (half=3) ──
    _roof_ring(roof_y + 3, 3, ROOF)
    b.fill(cx - 2, roof_y + 3, cz - 2,
           cx + 2, roof_y + 3, cz + 2, ROOF_BLOCK)

    # ── 第4层 (roof_y+4): 5×5 (half=2) ──
    _roof_ring(roof_y + 4, 2, ROOF)
    b.fill(cx - 1, roof_y + 4, cz - 1,
           cx + 1, roof_y + 4, cz + 1, ROOF_BLOCK)

    # ── 第5层 (roof_y+5): 3×3 实心 ──
    b.fill(cx - 1, roof_y + 5, cz - 1,
           cx + 1, roof_y + 5, cz + 1, ROOF_BLOCK)

    # ── 宝顶 (roof_y+6): 避雷针 ──
    b.setblock(cx, roof_y + 6, cz, ROD)


# ========================================================================
# 2. 芍药阑 — 雕花围栏芍药圃
# ========================================================================

def build_peony_rail(b: MinecraftBuilder):
    """建造芍药阑（芍药花圃围栏）

    11×9 围栏, 北/南各留 5 格入口,
    内部密植芍药, 中间 3 格宽 dirt_path 石径穿越,
    四角灯笼点缀。
    """
    cfg = PEONY_RAIL
    cx, cz = cfg["cx"], cfg["cz"]
    gy = cfg["ground_y"]
    HX = cfg["hx"]   # 5 → 11格 (cx-5 ~ cx+5)
    HZ = cfg["hz"]   # 4 → 9格  (cz-4 ~ cz+4)

    print(f"=== 芍药阑 v3 at ({cx}, {gy}, {cz}) ===")
    random.seed(42)

    RAIL    = PALETTE["rail"]
    DIRT    = PALETTE["dirt"]
    PATH    = PALETTE["path"]
    PEONY   = PALETTE["peony"]
    LANTERN = PALETTE["lantern"]
    VINE    = PALETTE["vine"]

    rail_y = gy + 1  # 栏杆在地面上方 1 格

    # 石径宽度: 中间 3 格 (cx-1, cx, cx+1)
    path_xs = [cx - 1, cx, cx + 1]

    # 入口宽度: 中间 5 格 (cx-2 ~ cx+2)
    entrance_half = 2

    # ================================================================
    # 1. 地面基底 — 围栏内铺泥土
    # ================================================================
    print("  [1/5] 地面基底...")
    b.fill(cx - HX, gy, cz - HZ,
           cx + HX, gy, cz + HZ, DIRT)

    # ================================================================
    # 2. 石径 — 中间 3 格宽, 南北贯穿 (含入口外延 1 格)
    # ================================================================
    print("  [2/5] 石径...")
    for px in path_xs:
        for pz in range(cz - HZ - 1, cz + HZ + 2):
            b.setblock(px, gy, pz, PATH)

    # ================================================================
    # 3. 围合栏杆 — 北/南各留 5 格入口
    # ================================================================
    print("  [3/5] 围合栏杆...")

    # 北面 (z = cz - HZ)
    for x in range(cx - HX, cx + HX + 1):
        if cx - entrance_half <= x <= cx + entrance_half:
            continue
        b.setblock(x, rail_y, cz - HZ, RAIL)

    # 南面 (z = cz + HZ)
    for x in range(cx - HX, cx + HX + 1):
        if cx - entrance_half <= x <= cx + entrance_half:
            continue
        b.setblock(x, rail_y, cz + HZ, RAIL)

    # 西面 (x = cx - HX)
    for z in range(cz - HZ, cz + HZ + 1):
        b.setblock(cx - HX, rail_y, z, RAIL)

    # 东面 (x = cx + HX)
    for z in range(cz - HZ, cz + HZ + 1):
        b.setblock(cx + HX, rail_y, z, RAIL)

    # ================================================================
    # 4. 角落灯笼
    # ================================================================
    print("  [4/5] 角落灯笼...")
    for lx, lz in [(cx - HX, cz - HZ), (cx + HX, cz - HZ),
                    (cx - HX, cz + HZ), (cx + HX, cz + HZ)]:
        b.setblock(lx, rail_y + 1, lz, LANTERN)

    # ================================================================
    # 5. 芍药花圃 — 内部种花 (避开石径)
    # ================================================================
    print("  [5/5] 芍药花圃...")
    for x in range(cx - HX + 1, cx + HX):
        for z in range(cz - HZ + 1, cz + HZ):
            if x in path_xs:
                continue
            b.setblock(x, gy + 1, z, PEONY)

    # ── 注册边界框 ──
    b.register_bbox("peony_rail",
                    cx - HX - 1, gy, cz - HZ - 1,
                    cx + HX + 1, gy + 3, cz + HZ + 1)

    print("  芍药阑 v3 建造完成!")


# ========================================================================
# 3. 翠轩 — 临水赏景敞厅 (悬山顶)
# ========================================================================

def build_hall(b: MinecraftBuilder):
    """建造翠轩/池馆（悬山顶敞厅）

    17(X进深) × 11(Z面阔), 6根柱子 (前3+后3), 6格柱高。
    西墙封闭白墙, 南北墙下3白墙+上3花窗, 东面完全开敞面水。
    东面美人靠中间留 5 格入口, 南/北各开 3 格门洞。
    """
    cfg = HALL
    cx, cz = cfg["cx"], cfg["cz"]
    gy = cfg["ground_y"]
    W_X = cfg["width_x"]     # 17
    W_Z = cfg["width_z"]     # 11
    PILLAR_H = cfg["pillar_h"]  # 6

    print(f"=== 翠轩 v3 at ({cx}, {gy}, {cz}) ===")
    random.seed(43)

    # ── 方块 ──
    BASE      = PALETTE["base"]
    BASE_MOSSY = PALETTE["wall_mossy"]
    BASE_COL  = PALETTE["base_col"]
    PILLAR    = PALETTE["pillar"]
    BEAM      = PALETTE["beam"]
    WALL      = PALETTE["wall"]
    TRAPDOOR  = PALETTE["trapdoor"]
    ROOF_S    = PALETTE["roof"]
    ROOF_B    = PALETTE["roof_block"]
    ROOF_SL   = PALETTE["roof_slab"]
    FLOOR     = PALETTE["floor"]
    LANTERN   = PALETTE["lantern"]
    RAIL      = PALETTE["rail"]

    # ── 坐标 ──
    # 台基 17(X) × 11(Z), 中心 (cx, cz)
    hx = W_X // 2   # 8
    hz = W_Z // 2   # 5

    base_x1, base_x2 = cx - hx, cx + hx   # 17格
    base_z1, base_z2 = cz - hz, cz + hz   # 11格

    floor_y = gy + 1   # 台基顶面 (踩踏面)

    # 柱子: 前排(东) x = cx + hx - 1 = cx+7, 后排(西) x = cx - hx + 1 = cx-7
    # 前后柱距 = 14 格 (很宽裕)
    # 但等等, 你说间距5格, 3根柱子在Z方向: cz-5, cz, cz+5
    # 但 hz=5, Z范围 cz-5~cz+5, 柱子在边缘上
    # 前排(东面水) 和 后排(西靠山) X 位置:
    # 要让东面是开敞的, 后排(西) 封墙
    front_x = cx + hx - 1   # cx+7 (东侧, 面水) -- 柱子内缩1格给出檐
    back_x  = cx - hx + 1   # cx-7 (西侧, 靠山)
    # 前后柱距 = front_x - back_x = 14 格

    pillar_zs = [cz - hz, cz, cz + hz]  # cz-5, cz, cz+5

    pillar_top_y = floor_y + PILLAR_H   # gy+1+6 = gy+7
    beam_y = pillar_top_y               # 梁在柱顶

    # 头顶净高 = pillar_top_y - (floor_y+1) = PILLAR_H - 1 = 5格
    # 足够通行 (玩家2格高)

    # ================================================================
    # 1. 台基 — 17×11, 1格高, 20% mossy
    # ================================================================
    print("  [1/7] 台基...")
    b.fill(base_x1, gy, base_z1, base_x2, gy, base_z2, BASE)
    for x in range(base_x1, base_x2 + 1):
        for z in range(base_z1, base_z2 + 1):
            if random.random() < 0.20:
                b.setblock(x, gy, z, BASE_MOSSY)

    # 台基顶面铺地
    b.fill(base_x1, floor_y, base_z1, base_x2, floor_y, base_z2, FLOOR)

    # ================================================================
    # 2. 柱子 — 6根 (前3东面水 + 后3西靠山), 间距5格
    # ================================================================
    print("  [2/7] 柱子...")
    for pz in pillar_zs:
        # 前排 (东/面水)
        b.setblock(front_x, floor_y, pz, BASE_COL)  # 柱础
        b.fill(front_x, floor_y + 1, pz,
               front_x, pillar_top_y, pz, PILLAR)

        # 后排 (西/靠山)
        b.setblock(back_x, floor_y, pz, BASE_COL)
        b.fill(back_x, floor_y + 1, pz,
               back_x, pillar_top_y, pz, PILLAR)

    # ================================================================
    # 3. 梁枋 — 柱顶连接
    # ================================================================
    print("  [3/7] 梁枋...")
    # Z方向横梁 (前排、后排各一道)
    b.fill(front_x, beam_y, pillar_zs[0],
           front_x, beam_y, pillar_zs[-1], BEAM)
    b.fill(back_x, beam_y, pillar_zs[0],
           back_x, beam_y, pillar_zs[-1], BEAM)
    # X方向横梁 (3道, 连接前后柱)
    for pz in pillar_zs:
        b.fill(back_x, beam_y, pz,
               front_x, beam_y, pz, BEAM)

    # ================================================================
    # 4. 墙体与花窗
    # ================================================================
    print("  [4/7] 墙体与花窗...")

    wall_z1 = pillar_zs[0]    # cz-5 (南面)
    wall_z2 = pillar_zs[-1]   # cz+5 (北面)

    # -- 西墙 (封闭白墙, x = back_x) --
    for y in range(floor_y + 1, pillar_top_y + 1):
        for z in range(wall_z1 + 1, wall_z2):
            b.setblock(back_x, y, z, WALL)

    # -- 南墙 (z = wall_z1): 下3格白墙 + 上3格花窗, 但留门洞 --
    # 门洞位置: 靠近中间, 3格宽 (back_x+3 ~ back_x+5 之间)
    # 让门洞在 X 方向中间偏西: 从 cx-2 到 cx (3格宽)
    door_x_start = cx - 1
    door_x_end = cx + 1   # 3格宽门洞

    for y_off in range(1, PILLAR_H + 1):
        y = floor_y + y_off
        for x in range(back_x + 1, front_x):
            # 门洞: 下3格空, 3格宽
            if y_off <= 3 and door_x_start <= x <= door_x_end:
                continue  # 门洞留空
            if y_off <= 3:
                b.setblock(x, y, wall_z1, WALL)
            else:
                b.setblock(x, y, wall_z1,
                           f'{TRAPDOOR}[facing=south,half=top,open=true]')

    # -- 北墙 (z = wall_z2): 同南墙布局 --
    for y_off in range(1, PILLAR_H + 1):
        y = floor_y + y_off
        for x in range(back_x + 1, front_x):
            if y_off <= 3 and door_x_start <= x <= door_x_end:
                continue  # 门洞留空
            if y_off <= 3:
                b.setblock(x, y, wall_z2, WALL)
            else:
                b.setblock(x, y, wall_z2,
                           f'{TRAPDOOR}[facing=north,half=top,open=true]')

    # 东面完全开敞 (不建墙)

    # ================================================================
    # 5. 美人靠 (东面/面水, 柱间, 中间5格留空做入口)
    # ================================================================
    print("  [5/7] 美人靠...")

    meiren_y = floor_y + 1
    # 用 crimson_fence 做美人靠 (比倒置楼梯更通透)
    entrance_half = 2  # 入口 5 格: cz-2 ~ cz+2

    # 前排柱1(cz-5) 到 柱2(cz) 之间
    for z in range(pillar_zs[0] + 1, pillar_zs[1]):
        if cz - entrance_half <= z <= cz + entrance_half:
            continue  # 入口留空
        b.setblock(front_x, meiren_y, z, RAIL)

    # 前排柱2(cz) 到 柱3(cz+5) 之间
    for z in range(pillar_zs[1] + 1, pillar_zs[2]):
        if cz - entrance_half <= z <= cz + entrance_half:
            continue
        b.setblock(front_x, meiren_y, z, RAIL)

    # ================================================================
    # 6. 悬山顶 — 两面坡
    # ================================================================
    print("  [6/7] 悬山顶...")

    _build_hall_roof(b, cx, cz, back_x, front_x, pillar_zs,
                     beam_y, ROOF_S, ROOF_B, ROOF_SL)

    # ================================================================
    # 7. 装饰 — 灯笼 4 盏挂梁下
    # ================================================================
    print("  [7/7] 灯笼...")

    # 前排居中、后排居中、南北横梁居中
    b.setblock(front_x, beam_y - 1, cz,
               f'{LANTERN}[hanging=true]')
    b.setblock(back_x, beam_y - 1, cz,
               f'{LANTERN}[hanging=true]')
    b.setblock(cx, beam_y - 1, pillar_zs[0],
               f'{LANTERN}[hanging=true]')
    b.setblock(cx, beam_y - 1, pillar_zs[-1],
               f'{LANTERN}[hanging=true]')

    # ── 注册边界框 ──
    b.register_bbox("hall",
                    base_x1 - 1, gy, base_z1 - 2,
                    base_x2 + 1, beam_y + 5, base_z2 + 2)

    print("  翠轩 v3 建造完成!")


def _build_hall_roof(b, cx, cz, back_x, front_x, pillar_zs,
                     beam_y, ROOF_S, ROOF_B, ROOF_SL):
    """悬山顶: 两面坡, 每层内缩 2 格, 3 层 + 脊线

    东坡 (面水) facing=west, 西坡 (靠山) facing=east
    Z方向悬山各超出柱位 1 格
    """
    roof_z1 = pillar_zs[0] - 1   # 悬山出檐
    roof_z2 = pillar_zs[-1] + 1

    # 从下到上:
    #   层1 (beam_y+1): 最宽, 东坡 front_x+1, 西坡 back_x-1
    #   层2 (beam_y+2): 内缩2, 东 front_x-1, 西 back_x+1
    #   层3 (beam_y+3): 内缩2, 东 front_x-3, 西 back_x+3
    #   脊线 (beam_y+4): cx 处半砖

    roof_layers = [
        (1, front_x + 1, back_x - 1, False),
        (2, front_x - 1, back_x + 1, False),
        (3, front_x - 3, back_x + 3, False),
        (4, cx, cx, True),
    ]

    for y_off, east_x, west_x, is_ridge in roof_layers:
        y = beam_y + y_off

        if is_ridge:
            for z in range(roof_z1, roof_z2 + 1):
                b.setblock(east_x, y, z, f'{ROOF_SL}[type=bottom]')
        else:
            # 东坡
            for z in range(roof_z1, roof_z2 + 1):
                b.setblock(east_x, y, z,
                           f'{ROOF_S}[facing=west,half=bottom]')
            # 西坡
            for z in range(roof_z1, roof_z2 + 1):
                b.setblock(west_x, y, z,
                           f'{ROOF_S}[facing=east,half=bottom]')

            # 两坡之间填实心
            if west_x + 1 < east_x:
                b.fill(west_x + 1, y, roof_z1,
                       east_x - 1, y, roof_z2, ROOF_B)


# ========================================================================
# 入口
# ========================================================================

if __name__ == "__main__":
    with MinecraftBuilder() as b:
        build_pavilion(b)
        build_peony_rail(b)
        build_hall(b)
        print(f"Done! {b.cmd_count} commands")
