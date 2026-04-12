"""A群：北岸梦境群 — 5栋建筑 + 假山高地 + 连接廊道

建筑清单:
  1. 牡丹亭     (58,8)   15×15  Y=-57  四角攒尖
  2. 太湖石组   (80,10)  15×10  Y=-57  不规则堆叠
  3. 秋千       (76,8)   3×3    Y=-58  嵌入太湖石空地
  4. 芍药阑     (50,26)  11×9   Y=-58  花圃围栏
  5. 濯缨水阁   (82,26)  11×7   Y=-59  半水半陆悬山顶

地形特征:
  - Z=0~20 区域 fill dirt 堆高到 Y=-57（假山高地）
  - Z=20~30 渐降到标准地面 Y=-60
  - 南侧 Z=30 矮墙 + 月洞门, 西侧 x=45 矮墙 + 月洞门
  - 牡丹亭→芍药阑 斜坡廊 (Y=-57 降→ -58)
  - 太湖石→濯缨水阁 坡道 (Y=-57 降→ -59)
"""

import sys
sys.path.insert(0, '/Users/lambertlin/minecraft-server/scripts')

import random
from builder import MinecraftBuilder
import config_v4 as cfg
from blocks import PALETTE


# ═══════════════════════════════════════════
# 材质快捷引用
# ═══════════════════════════════════════════

P = PALETTE
PILLAR      = P["pillar"]          # stripped_crimson_stem
BEAM        = P["beam"]            # dark_oak_planks
BEAM_LOG    = P["beam_log"]        # dark_oak_log
BASE        = P["base"]            # stone_bricks
BASE_COL    = P["base_col"]        # polished_andesite
BASE_STEP   = P["base_step"]       # stone_brick_stairs
FLOOR       = P["floor"]           # smooth_stone
FLOOR_ALT   = P["floor_alt"]       # stone_bricks
WALL_BLOCK  = P["wall"]            # white_concrete
WALL_BASE   = P["wall_base"]       # stone_bricks
WALL_CAP    = P["wall_cap"]        # stone_brick_slab
RAIL        = P["rail"]            # crimson_fence
RAIL_GATE   = P["rail_gate"]       # crimson_fence_gate
ROOF_STAIR  = P["roof"]            # stone_brick_stairs
ROOF_SLAB   = P["roof_slab"]       # stone_brick_slab
ROOF_BLOCK  = P["roof_block"]      # stone_bricks
EAVE_OUTER  = P["eave_outer"]      # dark_oak_stairs
EAVE_SLAB   = P["eave_slab"]       # dark_oak_slab
LANTERN     = P["lantern"]
WINDOW      = P["window"]          # iron_bars
AIR         = P["air"]
TAIHU_MAIN  = P["taihu_main"]      # dripstone_block
TAIHU_WHITE = P["taihu_white"]     # calcite
PEONY_FLOWER = P["peony"]
RED_CARPET  = P["red_carpet"]
FLOOR_WOOD  = P["floor_wood"]      # spruce_planks
MOSS        = P["moss"]
MOSS_CARPET = P["moss_carpet"]
DIRT        = P["dirt"]
GRASS       = P["grass"]
GRAVEL      = P["gravel"]
COBBLE      = P["cobblestone"]
MOSSY_CB    = P["mossy_cobblestone"]
WATER       = P["water"]

GROUND_Y = cfg.GROUND_Y        # -61
HIGHLAND_Y = cfg.HIGHLAND_Y    # -57


# ═══════════════════════════════════════════
# 工具函数
# ═══════════════════════════════════════════

def _stair(block_base, facing, half="bottom"):
    return f"{block_base}[facing={facing},half={half}]"


def _slab(block_base, stype="bottom"):
    return f"{block_base}[type={stype}]"


# ═══════════════════════════════════════════
# 主建造函数
# ═══════════════════════════════════════════

def build_cluster_a(b: MinecraftBuilder):
    """A群：北岸梦境群"""
    print("=" * 50)
    print("  A群：北岸梦境群 — 开始建造")
    print("=" * 50)

    # ── Step 1: 假山高地地形 ──
    _build_highland_terrain(b)

    # ── Step 2: 围合墙 ──
    _build_enclosure_walls(b)

    # ── Step 3: 牡丹亭 ──
    _build_peony_pavilion(b)

    # ── Step 4: 牡丹亭→芍药阑 斜坡廊 ──
    _build_slope_corridor_to_peony_rail(b)

    # ── Step 5: 芍药阑 ──
    _build_peony_rail(b)

    # ── Step 6: 太湖石组 ──
    _build_taihu_rocks(b)

    # ── Step 7: 秋千 ──
    _build_swing(b)

    # ── Step 8: 太湖石→濯缨水阁 坡道 ──
    _build_slope_to_zhuoying(b)

    # ── Step 9: 濯缨水阁 ──
    _build_zhuoying_pavilion(b)

    print("=" * 50)
    print(f"  A群完成！总命令数: {b.cmd_count}")
    print("=" * 50)


# ═══════════════════════════════════════════
# Step 1: 假山高地地形
# ═══════════════════════════════════════════

def _build_highland_terrain(b: MinecraftBuilder):
    """假山高地: Z=0~20 堆高到 Y=-57, Z=20~30 渐降到 Y=-60

    从 GROUND_Y(-61) 往上填 dirt 到目标高度，顶层铺 grass_block。
    x_range: 45~95 (覆盖牡丹亭+太湖石+濯缨水阁前沿)
    """
    print("  [1/9] 假山高地地形...")

    x_min, x_max = 45, 95

    # --- Z=0~20: 平台区，目标 Y=-57 ---
    # 从 GROUND_Y+1(-60) 填到 HIGHLAND_Y-1(-58)=dirt, HIGHLAND_Y(-57)=grass
    # GROUND_Y=-61 是原始草方块层
    # 需要填充 Y=-60, -59, -58 为 dirt, Y=-57 为 grass
    for z in range(0, 20):
        # 填 dirt 层 (GROUND_Y+1 到 HIGHLAND_Y-1)
        b.fill(x_min, GROUND_Y + 1, z, x_max, HIGHLAND_Y - 1, z, DIRT)
        # 顶面 grass
        b.fill(x_min, HIGHLAND_Y, z, x_max, HIGHLAND_Y, z, GRASS)

    # --- Z=20~30: 渐降斜坡 ---
    # Z=20: Y=-57, Z=22: Y=-58, Z=24: Y=-59, Z=26+: Y=-60(地面)
    for z in range(20, 30):
        # 每 2~3 格 Z 下降 1 格 Y
        progress = (z - 20) / 10.0  # 0.0 ~ 1.0
        target_y = round(HIGHLAND_Y + progress * (GROUND_Y - HIGHLAND_Y))
        # target_y: -57 → -61
        target_y = max(GROUND_Y, target_y)

        if target_y > GROUND_Y:
            b.fill(x_min, GROUND_Y + 1, z, x_max, target_y - 1, z, DIRT)
            b.fill(x_min, target_y, z, x_max, target_y, z, GRASS)

    # --- X 方向边缘软化 (x=42~45 和 x=95~98) ---
    for z in range(0, 25):
        progress_z = min(1.0, (z - 20) / 10.0) if z >= 20 else 0.0
        base_target = round(HIGHLAND_Y + progress_z * (GROUND_Y - HIGHLAND_Y))
        base_target = max(GROUND_Y, base_target)

        if base_target <= GROUND_Y:
            continue

        # 西侧软化 x=42~44
        for x in range(42, 45):
            edge_factor = (x - 41) / 4.0  # 0.25 ~ 0.75
            edge_y = round(GROUND_Y + (base_target - GROUND_Y) * edge_factor)
            if edge_y > GROUND_Y:
                b.fill(x, GROUND_Y + 1, z, x, edge_y - 1, z, DIRT)
                b.setblock(x, edge_y, z, GRASS)

        # 东侧软化 x=96~98
        for x in range(96, 99):
            edge_factor = (99 - x) / 4.0
            edge_y = round(GROUND_Y + (base_target - GROUND_Y) * edge_factor)
            if edge_y > GROUND_Y:
                b.fill(x, GROUND_Y + 1, z, x, edge_y - 1, z, DIRT)
                b.setblock(x, edge_y, z, GRASS)

    b.register_bbox("highland_terrain", 42, GROUND_Y, 0, 98, HIGHLAND_Y, 30)
    print(f"    地形完成. [{b.cmd_count} cmds]")


# ═══════════════════════════════════════════
# Step 2: 围合墙
# ═══════════════════════════════════════════

def _build_enclosure_walls(b: MinecraftBuilder):
    """南侧 Z=30 矮墙 + 月洞门(x=58)，西侧 x=45 矮墙 + 月洞门(z=15)

    矮墙: 3格高白墙 + 石砖基座 + 顶部石砖半砖收口
    月洞门: 半径3的圆形开口
    """
    print("  [2/9] 围合墙...")

    wall_h = 3  # 墙高3格（不含基座和帽）

    # ── 南墙 (Z=30, X=45~95) ──
    # 确定南墙的底部Y: 斜坡区Z=30处约Y=-60
    south_wall_y = -60  # 南墙底部
    sw_top = south_wall_y + wall_h  # -57

    # 基座层 (stone_bricks)
    b.fill(45, south_wall_y, 30, 95, south_wall_y, 30, WALL_BASE)
    # 白墙主体
    b.fill(45, south_wall_y + 1, 30, 95, sw_top - 1, 30, WALL_BLOCK)
    # 顶部帽 (stone_brick_slab)
    b.fill(45, sw_top, 30, 95, sw_top, 30, _slab(WALL_CAP, "bottom"))

    # 南墙月洞门 at x=58, 半径3
    # 圆心: (58, south_wall_y+2, 30) — XY平面圆
    moon_cx, moon_cy = 58, south_wall_y + 2
    for dx in range(-3, 4):
        for dy in range(-3, 4):
            if dx * dx + dy * dy <= 9:  # r=3
                bx = moon_cx + dx
                by = moon_cy + dy
                if by >= south_wall_y and by <= sw_top:
                    b.setblock(bx, by, 30, AIR)

    # ── 西墙 (X=45, Z=0~30) ──
    # 西墙沿假山地形，底部跟随地形高度
    # Z=0~20: 地形顶 Y=-57, 墙从 -57 起
    # Z=20~30: 渐降
    for z in range(0, 31):
        if z < 20:
            wall_base_y = HIGHLAND_Y  # -57
        else:
            progress = (z - 20) / 10.0
            wall_base_y = round(HIGHLAND_Y + progress * (GROUND_Y - HIGHLAND_Y))
            wall_base_y = max(GROUND_Y, wall_base_y)

        wt = wall_base_y + wall_h
        b.setblock(45, wall_base_y, z, WALL_BASE)
        if wt - 1 >= wall_base_y + 1:
            b.fill(45, wall_base_y + 1, z, 45, wt - 1, z, WALL_BLOCK)
        b.setblock(45, wt, z, _slab(WALL_CAP, "bottom"))

    # 西墙月洞门 at z=15, 半径3
    # 圆心: (45, HIGHLAND_Y+1, 15) — YZ平面圆
    moon_cz, moon_cy2 = 15, HIGHLAND_Y + 1
    for dz in range(-3, 4):
        for dy in range(-3, 4):
            if dz * dz + dy * dy <= 9:
                bz = moon_cz + dz
                by = moon_cy2 + dy
                if 0 <= bz <= 30:
                    b.setblock(45, by, bz, AIR)

    b.register_bbox("enclosure_walls", 45, GROUND_Y, 0, 95, HIGHLAND_Y + wall_h, 30)
    print(f"    围合墙完成. [{b.cmd_count} cmds]")


# ═══════════════════════════════════════════
# Step 3: 牡丹亭 — 15×15 四角攒尖
# ═══════════════════════════════════════════

def _build_peony_pavilion(b: MinecraftBuilder):
    """牡丹亭: (51~65, 1~15), Y=-57
    - 须弥座台基 2格高
    - 6根绯红柱高6格（矩形四角+各面中间）
    - 攒尖顶 (stone_brick_stairs 逐层收缩)
    - 飞檐 (dark_oak_stairs)
    - 四面各留5格入口
    """
    print("  [3/9] 牡丹亭...")

    # 建筑边界 (cx=58, cz=8, 15×15)
    x1, z1, x2, z2 = 51, 1, 65, 15
    gy = -57  # 假山高地地面

    # ── 须弥座台基 (2格) ──
    # 散水带 (polished_andesite) 外围1格
    b.fill(x1 - 1, gy, z1 - 1, x2 + 1, gy, z2 + 1, BASE_COL)
    # 台基下层 — stone_brick_stairs 围一圈（须弥座特征：收分）
    # 底层实心 stone_bricks
    b.fill(x1, gy, z1, x2, gy, z2, BASE)
    # 第二层台基
    b.fill(x1, gy + 1, z1, x2, gy + 1, z2, BASE)
    # 须弥座装饰: 底层四周 stairs 面朝外
    b.fill(x1, gy, z1, x2, gy, z1, _stair(BASE_STEP, "south"))      # 北面
    b.fill(x1, gy, z2, x2, gy, z2, _stair(BASE_STEP, "north"))      # 南面
    b.fill(x1, gy, z1, x1, gy, z2, _stair(BASE_STEP, "east"))       # 西面
    b.fill(x2, gy, z1, x2, gy, z2, _stair(BASE_STEP, "west"))       # 东面

    floor_y = gy + 2  # 台基顶面 = 地面层

    # ── 地面铺装 (条纹) ──
    b.fill(x1, floor_y, z1, x2, floor_y, z2, FLOOR)
    for z in range(z1, z2 + 1):
        if (z - z1) % 2 == 1:
            b.fill(x1, floor_y, z, x2, floor_y, z, BASE_COL)

    # ── 柱子 (6根绯红柱, 高6格) ──
    pillar_h = 6
    pillar_top_y = floor_y + pillar_h

    # 柱位: 四角 + 每面中间点（15格跨度，中间加2根 → 间距5格）
    pillar_positions = []
    # 四角
    corners = [(x1, z1), (x1, z2), (x2, z1), (x2, z2)]
    pillar_positions.extend(corners)
    # 北面和南面中间柱 (x1+5, x1+10 即 56, 61)
    mid_x1 = x1 + 5  # 56
    mid_x2 = x1 + 10  # 61
    for z in [z1, z2]:
        pillar_positions.append((mid_x1, z))
        pillar_positions.append((mid_x2, z))
    # 西面和东面中间柱 (z1+5, z1+10 即 6, 11)
    mid_z1 = z1 + 5  # 6
    mid_z2 = z1 + 10  # 11
    for x in [x1, x2]:
        pillar_positions.append((x, mid_z1))
        pillar_positions.append((x, mid_z2))

    for (px, pz) in pillar_positions:
        # 柱础
        b.setblock(px, floor_y, pz, BASE_COL)
        # 柱身
        b.fill(px, floor_y + 1, pz, px, pillar_top_y, pz, PILLAR)

    # ── 梁枋 ──
    beam_y = pillar_top_y
    b.fill(x1, beam_y, z1, x2, beam_y, z1, BEAM)  # 北
    b.fill(x1, beam_y, z2, x2, beam_y, z2, BEAM)  # 南
    b.fill(x1, beam_y, z1, x1, beam_y, z2, BEAM)  # 西
    b.fill(x2, beam_y, z1, x2, beam_y, z2, BEAM)  # 东

    # ── 栏杆 (四面各留5格入口) ──
    rail_y = floor_y + 1
    cx = (x1 + x2) // 2  # 58
    cz = (z1 + z2) // 2  # 8
    # 先 fill 四面栏杆
    b.fill(x1, rail_y, z1, x2, rail_y, z1, RAIL)
    b.fill(x1, rail_y, z2, x2, rail_y, z2, RAIL)
    b.fill(x1, rail_y, z1, x1, rail_y, z2, RAIL)
    b.fill(x2, rail_y, z1, x2, rail_y, z2, RAIL)
    # 四面各开5格入口 (中心±2)
    b.fill(cx - 2, rail_y, z1, cx + 2, rail_y, z1, AIR)  # 北入口
    b.fill(cx - 2, rail_y, z2, cx + 2, rail_y, z2, AIR)  # 南入口
    b.fill(x1, rail_y, cz - 2, x1, rail_y, cz + 2, AIR)  # 西入口
    b.fill(x2, rail_y, cz - 2, x2, rail_y, cz + 2, AIR)  # 东入口

    # ── 攒尖顶 ──
    roof_base_y = beam_y + 1
    _build_cuanjian_roof(b, x1, z1, x2, z2, roof_base_y)

    # ── 灯笼 (四角内侧) ──
    lantern_y = beam_y - 1
    for (px, pz) in corners:
        dx = 1 if px < cx else -1
        dz = 1 if pz < cz else -1
        b.setblock(px + dx, lantern_y, pz + dz, f"{LANTERN}[hanging=true]")

    # ── 中央装饰: 红毯 + 灯笼柱 ──
    b.fill(cx - 1, floor_y + 1, cz - 1, cx + 1, floor_y + 1, cz + 1, RED_CARPET)
    b.fill(cx, floor_y + 1, cz, cx, floor_y + 3, cz, PILLAR)
    b.setblock(cx, floor_y + 4, cz, f"{LANTERN}[hanging=false]")

    b.register_bbox("peony_pavilion",
                     x1 - 2, gy, z1 - 2, x2 + 2, roof_base_y + 10, z2 + 2)
    print(f"    牡丹亭完成. [{b.cmd_count} cmds]")


def _build_cuanjian_roof(b, x1, z1, x2, z2, base_y):
    """攒尖顶 — 四面等坡收尖 + 宝顶(lightning_rod)"""
    cx = (x1 + x2) // 2
    cz = (z1 + z2) // 2
    layer = 0
    # 出檐1格
    cx1, cz1, cx2, cz2 = x1 - 1, z1 - 1, x2 + 1, z2 + 1
    y = base_y

    while cx1 <= cx2 and cz1 <= cz2:
        if cx1 == cx2 and cz1 == cz2:
            b.setblock(cx1, y, cz1, ROOF_BLOCK)
            b.setblock(cx1, y + 1, cz1, P["lightning_rod"])
            break
        elif cx1 == cx2:
            b.fill(cx1, y, cz1, cx1, y, cz2, ROOF_BLOCK)
            y += 1; cz1 += 1; cz2 -= 1; continue
        elif cz1 == cz2:
            b.fill(cx1, y, cz1, cx2, y, cz1, ROOF_BLOCK)
            y += 1; cx1 += 1; cx2 -= 1; continue

        # 四面 stairs
        b.fill(cx1 + 1, y, cz1, cx2 - 1, y, cz1,
               _stair(ROOF_STAIR, "south"))
        b.fill(cx1 + 1, y, cz2, cx2 - 1, y, cz2,
               _stair(ROOF_STAIR, "north"))
        b.fill(cx1, y, cz1 + 1, cx1, y, cz2 - 1,
               _stair(ROOF_STAIR, "east"))
        b.fill(cx2, y, cz1 + 1, cx2, y, cz2 - 1,
               _stair(ROOF_STAIR, "west"))
        # 四角实心
        for corner_x, corner_z in [(cx1, cz1), (cx1, cz2), (cx2, cz1), (cx2, cz2)]:
            b.setblock(corner_x, y, corner_z, ROOF_BLOCK)

        cx1 += 1; cz1 += 1; cx2 -= 1; cz2 -= 1
        y += 1; layer += 1
        if layer > 12:
            break

    # 飞檐 — 最外圈 dark_oak_stairs 翘角
    eave_y = base_y - 1
    ox1, oz1, ox2, oz2 = x1 - 2, z1 - 2, x2 + 2, z2 + 2
    b.fill(ox1 + 1, eave_y, oz1, ox2 - 1, eave_y, oz1,
           _stair(EAVE_OUTER, "south", "top"))
    b.fill(ox1 + 1, eave_y, oz2, ox2 - 1, eave_y, oz2,
           _stair(EAVE_OUTER, "north", "top"))
    b.fill(ox1, eave_y, oz1 + 1, ox1, eave_y, oz2 - 1,
           _stair(EAVE_OUTER, "east", "top"))
    b.fill(ox2, eave_y, oz1 + 1, ox2, eave_y, oz2 - 1,
           _stair(EAVE_OUTER, "west", "top"))
    for ccx, ccz in [(ox1, oz1), (ox1, oz2), (ox2, oz1), (ox2, oz2)]:
        b.setblock(ccx, eave_y, ccz, EAVE_SLAB)


# ═══════════════════════════════════════════
# Step 4: 牡丹亭→芍药阑 斜坡廊
# ═══════════════════════════════════════════

def _build_slope_corridor_to_peony_rail(b: MinecraftBuilder):
    """斜坡廊: 从牡丹亭南柱(Z=15)向南延伸, 再向西拐到芍药阑(Z=22), Y=-57降→-58

    路线:
    - 南段(直行): x=56~60, Z=16→22, Y=-57 降→ -58
    - 西转段(L拐): Z=22, x=55→50(芍药阑入口), Y=-58

    特征:
    - 从牡丹亭南面柱子直接延伸（零间隙）
    - 宽5格
    - 每2格Z下降1级台阶
    - 两侧绯红栏杆 + 有顶
    """
    print("  [4/9] 牡丹亭→芍药阑 斜坡廊...")

    # ── 南段: 直行部分 ──
    corridor_x1 = 56  # cx-2
    corridor_x2 = 60  # cx+2
    z_start = 16       # 牡丹亭南墙外第一格
    z_end = 22         # 拐弯处

    # Z=16~19: Y=-57 (高地), Z=20~22: Y=-58 (过渡后)

    for z in range(z_start, z_end + 1):
        if z <= 19:
            floor_y_here = -57
        else:
            floor_y_here = -58

        # 地面
        b.fill(corridor_x1, floor_y_here, z, corridor_x2, floor_y_here, z, BASE)

        # 台阶过渡 (Z=20 处设置下行台阶)
        if z == 20:
            b.fill(corridor_x1, -57, z, corridor_x2, -57, z,
                   _stair(BASE_STEP, "south"))

    # 两侧栏杆
    for z in range(z_start, z_end):  # z_end 不放栏杆(拐弯处)
        rail_base = -57 if z <= 19 else -58
        b.setblock(corridor_x1, rail_base + 1, z, RAIL)
        b.setblock(corridor_x2, rail_base + 1, z, RAIL)

    # 柱子 (每4格一根, 两侧)
    for z in [z_start, z_start + 4]:
        col_base = -57 if z <= 19 else -58
        for x in [corridor_x1, corridor_x2]:
            b.fill(x, col_base + 1, z, x, col_base + 4, z, PILLAR)

    # 顶部: 横梁 + dark_oak_slab
    for z in range(z_start, z_end + 1):
        col_base = -57 if z <= 19 else -58
        beam_here = col_base + 4
        b.fill(corridor_x1, beam_here, z, corridor_x2, beam_here, z, BEAM)
        b.fill(corridor_x1 - 1, beam_here + 1, z, corridor_x2 + 1, beam_here + 1, z,
               _slab(EAVE_SLAB, "bottom"))

    # ── 西转段: Z=22, x=55→50 向西连接芍药阑 ──
    turn_y = -58
    turn_z = 22
    turn_x_start = 55  # 南段西墙
    turn_x_end = 51    # 芍药阑入口(cx=50, 入口50±1)

    # 地面
    b.fill(turn_x_end, turn_y, turn_z, turn_x_start, turn_y, turn_z, BASE)
    # 扩展宽度: Z方向 ±1 (3格宽的东西走向廊道)
    b.fill(turn_x_end, turn_y, turn_z - 1, turn_x_start, turn_y, turn_z - 1, BASE)
    b.fill(turn_x_end, turn_y, turn_z + 1, turn_x_start, turn_y, turn_z + 1, BASE)

    # 北/南栏杆
    b.fill(turn_x_end, turn_y + 1, turn_z - 1, turn_x_start, turn_y + 1, turn_z - 1, RAIL)
    b.fill(turn_x_end, turn_y + 1, turn_z + 1, turn_x_start, turn_y + 1, turn_z + 1, RAIL)

    # 柱子 (两端)
    for x in [turn_x_end, turn_x_start]:
        b.fill(x, turn_y + 1, turn_z - 1, x, turn_y + 4, turn_z - 1, PILLAR)
        b.fill(x, turn_y + 1, turn_z + 1, x, turn_y + 4, turn_z + 1, PILLAR)

    # 顶
    beam_w = turn_y + 4
    b.fill(turn_x_end, beam_w, turn_z - 1, turn_x_start, beam_w, turn_z + 1, BEAM)
    b.fill(turn_x_end - 1, beam_w + 1, turn_z - 1, turn_x_start + 1, beam_w + 1, turn_z + 1,
           _slab(EAVE_SLAB, "bottom"))

    b.register_bbox("slope_corridor_peony",
                     turn_x_end - 1, -58, z_start, corridor_x2 + 1, -51, z_end + 1)
    print(f"    斜坡廊完成. [{b.cmd_count} cmds]")


# ═══════════════════════════════════════════
# Step 5: 芍药阑
# ═══════════════════════════════════════════

def _build_peony_rail(b: MinecraftBuilder):
    """芍药阑: (45~55, 22~30), Y=-58
    crimson_fence 围栏 + peony 密植
    北面留入口对接斜坡廊
    """
    print("  [5/9] 芍药阑...")

    x1, z1, x2, z2 = 45, 22, 55, 30
    gy = -58

    # 地面铺草
    b.fill(x1, gy, z1, x2, gy, z2, GRASS)

    # 四周围栏
    cx = (x1 + x2) // 2  # 50
    rail_y = gy + 1

    # 北面 (留3格入口对接廊道, 中心偏东 cx=50 → 对接 x=56~60 的廊道)
    # 入口在 x=56~60 范围与芍药阑北墙的交集
    # 芍药阑 x 范围 45~55，廊道 x=56~60... 不重叠!
    # 修正: 廊道下端需要拐弯到芍药阑。北面中央开口即可。
    b.fill(x1, rail_y, z1, cx - 2, rail_y, z1, RAIL)
    b.fill(cx + 2, rail_y, z1, x2, rail_y, z1, RAIL)
    # 南面
    b.fill(x1, rail_y, z2, x2, rail_y, z2, RAIL)
    # 西面
    b.fill(x1, rail_y, z1, x1, rail_y, z2, RAIL)
    # 东面
    b.fill(x2, rail_y, z1, x2, rail_y, z2, RAIL)

    # 内部密植牡丹 (peony 是2格高花, 每隔1格种)
    for x in range(x1 + 1, x2, 2):
        for z in range(z1 + 1, z2, 2):
            b.setblock(x, gy + 1, z, PEONY_FLOWER)

    # 四角灯笼
    for lx, lz in [(x1, z1), (x1, z2), (x2, z1), (x2, z2)]:
        b.setblock(lx, gy + 2, lz, f"{LANTERN}[hanging=false]")

    # 围栏柱 (四角 + 入口两侧加高一格)
    for lx, lz in [(x1, z1), (x1, z2), (x2, z1), (x2, z2)]:
        b.setblock(lx, gy + 2, lz, RAIL)

    b.register_bbox("peony_rail", x1, gy, z1, x2, gy + 3, z2)
    print(f"    芍药阑完成. [{b.cmd_count} cmds]")


# ═══════════════════════════════════════════
# Step 6: 太湖石组
# ═══════════════════════════════════════════

def _build_taihu_rocks(b: MinecraftBuilder):
    """太湖石组: (73~87, 5~15), Y=-57
    不规则堆叠 dripstone_block + calcite
    主峰 + 次峰 + 散石，体现"瘦皱漏透"
    """
    print("  [6/9] 太湖石组...")

    cx, cz = 80, 10
    gy = -57

    random.seed(42)

    # ── 主峰 (中央偏东, 高10格) ──
    _build_taihu_main_peak(b, cx + 2, cz, gy)

    # ── 次峰 (西侧, 高5格) ──
    _build_taihu_sub_peak(b, cx - 4, cz + 2, gy, height=5)

    # ── 副石 (东北, 高3格) ──
    _build_taihu_small_rock(b, cx + 5, cz - 3, gy, height=3)

    # ── 散石 ──
    for sx, sz, sh in [(cx - 6, cz + 3, 2), (cx + 6, cz - 4, 2), (cx, cz + 5, 2)]:
        for dy in range(sh):
            block = TAIHU_WHITE if random.random() < 0.3 else TAIHU_MAIN
            b.setblock(sx, gy + dy + 1, sz, block)
            if dy == 0:
                b.setblock(sx + 1, gy + 1, sz, TAIHU_WHITE)

    # 底部苔藓散布
    for dx in range(-7, 8):
        for dz in range(-5, 6):
            if random.random() < 0.15:
                b.setblock(cx + dx, gy, cz + dz, MOSS)
                if random.random() < 0.4:
                    b.setblock(cx + dx, gy + 1, cz + dz, MOSS_CARPET)

    b.register_bbox("taihu_rocks", 73, gy, 5, 87, gy + 12, 15)
    print(f"    太湖石组完成. [{b.cmd_count} cmds]")


def _build_taihu_main_peak(b, cx, cz, gy):
    """主峰: 10层手工pattern, "瘦皱漏透"四字诀
    Pattern 10×10, 原点 (cx-4, cz-4)
    """
    random.seed(42)

    layers = [
        # Layer 0 — 窄底座
        [
            [0,0,0,0,0,0,0,0,0,0],
            [0,0,0,0,0,0,0,0,0,0],
            [0,0,0,0,1,1,0,0,0,0],
            [0,0,0,1,1,1,1,0,0,0],
            [0,0,0,1,1,1,1,0,0,0],
            [0,0,0,1,1,1,0,0,0,0],
            [0,0,0,0,1,0,0,0,0,0],
            [0,0,0,0,0,0,0,0,0,0],
            [0,0,0,0,0,0,0,0,0,0],
            [0,0,0,0,0,0,0,0,0,0],
        ],
        # Layer 1 — 略扩
        [
            [0,0,0,0,0,0,0,0,0,0],
            [0,0,0,0,1,0,0,0,0,0],
            [0,0,0,1,1,1,1,0,0,0],
            [0,0,1,1,1,1,1,0,0,0],
            [0,0,1,1,1,1,1,1,0,0],
            [0,0,0,1,1,1,1,0,0,0],
            [0,0,0,0,1,1,0,0,0,0],
            [0,0,0,0,0,0,0,0,0,0],
            [0,0,0,0,0,0,0,0,0,0],
            [0,0,0,0,0,0,0,0,0,0],
        ],
        # Layer 2 — 洞穴底层: 东西贯穿通道
        [
            [0,0,0,0,0,0,0,0,0,0],
            [0,0,0,1,1,1,1,0,0,0],
            [0,0,1,1,1,1,1,1,0,0],
            [0,1,1,1,1,1,1,1,1,0],
            [0,1,0,0,0,0,0,0,1,0],
            [0,1,0,0,0,0,0,0,1,0],
            [0,0,1,1,1,1,1,1,0,0],
            [0,0,0,1,1,1,0,0,0,0],
            [0,0,0,0,0,0,0,0,0,0],
            [0,0,0,0,0,0,0,0,0,0],
        ],
        # Layer 3 — 洞穴中层
        [
            [0,0,0,0,1,0,0,0,0,0],
            [0,0,1,1,1,1,1,0,0,0],
            [0,1,1,1,1,1,1,1,0,0],
            [0,1,1,1,1,1,1,1,1,0],
            [0,1,0,0,0,0,0,0,1,0],
            [0,1,0,0,0,0,0,0,1,0],
            [0,1,1,1,1,1,1,1,0,0],
            [0,0,1,1,1,1,1,0,0,0],
            [0,0,0,0,1,0,0,0,0,0],
            [0,0,0,0,0,0,0,0,0,0],
        ],
        # Layer 4 — 洞穴顶层: 通道缩窄("漏")
        [
            [0,0,0,0,1,1,0,0,0,0],
            [0,0,1,1,1,1,1,1,0,0],
            [0,1,1,1,1,1,1,1,1,0],
            [0,1,1,1,1,1,1,1,1,0],
            [0,1,1,0,0,0,1,1,1,0],
            [0,1,1,0,0,0,1,1,1,0],
            [0,1,1,1,1,1,1,1,0,0],
            [0,0,1,1,1,1,1,0,0,0],
            [0,0,0,0,1,0,0,0,0,0],
            [0,0,0,0,0,0,0,0,0,0],
        ],
        # Layer 5 — 上部外扩("瘦"= 上大下小)
        [
            [0,0,0,1,1,1,0,0,0,0],
            [0,0,1,1,1,1,1,1,0,0],
            [0,1,1,1,1,1,1,1,1,0],
            [1,1,1,1,1,1,1,1,1,1],
            [0,1,1,1,1,1,1,1,1,0],
            [1,1,1,1,1,1,1,1,1,0],
            [0,1,1,1,1,1,1,1,1,0],
            [0,0,1,1,1,1,1,1,0,0],
            [0,0,0,1,1,1,0,0,0,0],
            [0,0,0,0,0,0,0,0,0,0],
        ],
        # Layer 6 — 宽大, 小透孔
        [
            [0,0,1,1,1,1,1,0,0,0],
            [0,1,1,1,1,1,1,1,0,0],
            [1,1,1,1,1,1,1,1,1,0],
            [1,1,1,1,0,1,1,1,1,1],
            [1,1,1,1,1,1,1,1,1,1],
            [1,1,1,0,1,1,0,1,1,1],
            [0,1,1,1,1,1,1,1,1,0],
            [0,1,1,1,1,1,1,1,0,0],
            [0,0,0,1,1,1,1,0,0,0],
            [0,0,0,0,0,0,0,0,0,0],
        ],
        # Layer 7 — 最宽层, 多处透孔("透")
        [
            [0,0,1,1,1,1,1,0,0,0],
            [0,1,1,1,1,1,1,1,1,0],
            [1,1,1,0,1,1,0,1,1,1],
            [1,1,1,1,1,1,1,1,1,1],
            [1,1,0,1,1,1,1,0,1,1],
            [1,1,1,1,1,1,1,1,1,1],
            [1,1,1,1,0,1,1,1,1,0],
            [0,1,1,1,1,1,1,1,0,0],
            [0,0,1,1,1,1,0,0,0,0],
            [0,0,0,0,0,0,0,0,0,0],
        ],
        # Layer 8 — 收窄, 凹凸("皱")
        [
            [0,0,0,1,1,1,0,0,0,0],
            [0,0,1,1,1,1,1,0,0,0],
            [0,1,1,0,1,1,1,1,0,0],
            [0,1,1,1,1,1,1,0,0,0],
            [0,1,1,1,1,0,1,1,0,0],
            [0,0,1,1,1,1,1,1,0,0],
            [0,0,1,1,1,1,1,0,0,0],
            [0,0,0,1,1,0,0,0,0,0],
            [0,0,0,0,0,0,0,0,0,0],
            [0,0,0,0,0,0,0,0,0,0],
        ],
        # Layer 9 — 尖顶
        [
            [0,0,0,0,0,0,0,0,0,0],
            [0,0,0,0,1,0,0,0,0,0],
            [0,0,0,1,1,1,0,0,0,0],
            [0,0,0,0,1,0,0,0,0,0],
            [0,0,0,0,0,0,0,0,0,0],
            [0,0,0,0,0,0,0,0,0,0],
            [0,0,0,0,0,0,0,0,0,0],
            [0,0,0,0,0,0,0,0,0,0],
            [0,0,0,0,0,0,0,0,0,0],
            [0,0,0,0,0,0,0,0,0,0],
        ],
    ]

    ox = cx - 4
    oz = cz - 4

    for dy, layer in enumerate(layers):
        y = gy + dy + 1  # 从 gy+1 开始（gy 是地面）
        for dz_idx, row in enumerate(layer):
            for dx_idx, val in enumerate(row):
                if val == 1:
                    bx = ox + dx_idx
                    bz = oz + dz_idx
                    block = TAIHU_WHITE if random.random() < 0.30 else TAIHU_MAIN
                    b.setblock(bx, y, bz, block)

    # 洞穴内地面铺苔藓
    for dz_off in [0, 1]:
        for dx_off in range(-2, 4):
            bx = cx + dx_off
            bz = cz + dz_off
            b.setblock(bx, gy + 3, bz, MOSS)


def _build_taihu_sub_peak(b, sx, sz, gy, height=5):
    """次峰: 5层pattern, 上大下小"""
    random.seed(44)

    sub_layers = [
        [[0,0,0,0,0],
         [0,0,1,1,0],
         [0,1,1,1,0],
         [0,0,1,0,0],
         [0,0,0,0,0]],
        [[0,0,1,0,0],
         [0,1,1,1,0],
         [0,1,1,1,0],
         [0,0,1,1,0],
         [0,0,0,0,0]],
        [[0,1,1,0,0],
         [1,1,0,1,0],
         [1,1,1,1,1],
         [0,1,1,1,0],
         [0,0,0,0,0]],
        [[0,1,1,1,0],
         [1,1,1,1,1],
         [0,1,1,1,0],
         [0,0,1,0,0],
         [0,0,0,0,0]],
        [[0,0,0,0,0],
         [0,0,1,0,0],
         [0,1,1,0,0],
         [0,0,0,0,0],
         [0,0,0,0,0]],
    ]

    for dy, layer in enumerate(sub_layers):
        y = gy + dy + 1
        for dz_idx, row in enumerate(layer):
            for dx_idx, val in enumerate(row):
                if val == 1:
                    block = TAIHU_WHITE if random.random() < 0.30 else TAIHU_MAIN
                    b.setblock(sx + dx_idx, y, sz + dz_idx, block)


def _build_taihu_small_rock(b, sx, sz, gy, height=3):
    """小副石: 3~4层"""
    random.seed(45)

    sub_layers = [
        [[0,0,0],
         [0,1,0],
         [0,1,0]],
        [[0,1,0],
         [1,1,1],
         [0,1,0]],
        [[1,1,0],
         [1,1,1],
         [0,1,1]],
    ]

    for dy, layer in enumerate(sub_layers):
        y = gy + dy + 1
        for dz_idx, row in enumerate(layer):
            for dx_idx, val in enumerate(row):
                if val == 1:
                    block = TAIHU_WHITE if random.random() < 0.25 else TAIHU_MAIN
                    b.setblock(sx + dx_idx, y, sz + dz_idx, block)


# ═══════════════════════════════════════════
# Step 7: 秋千
# ═══════════════════════════════════════════

def _build_swing(b: MinecraftBuilder):
    """秋千: (75~77, 7~9), Y=-58
    嵌入太湖石空地
    两根绯红柱(间距2格) + 横梁 + 铁栏杆链条 + 橡木半砖座板
    """
    print("  [7/9] 秋千...")

    cx, cz = 76, 8
    gy = -58  # 秋千地面略低于太湖石

    # 清出空地（确保太湖石没有占据这里）
    b.fill(75, gy + 1, 7, 77, gy + 7, 9, AIR)

    # 地面平整
    b.fill(75, gy, 7, 77, gy, 9, GRASS)

    # 两根柱子 (X方向两端, Z=cz)
    pillar_h = 5
    top_y = gy + pillar_h
    b.fill(75, gy + 1, cz, 75, top_y, cz, PILLAR)
    b.fill(77, gy + 1, cz, 77, top_y, cz, PILLAR)

    # 横梁
    b.fill(75, top_y, cz, 77, top_y, cz, BEAM)

    # 链条 (iron_bars, 从横梁内侧垂下)
    chain_len = 3
    for dy in range(1, chain_len + 1):
        b.setblock(76, top_y - dy, cz, WINDOW)  # 中间一根链

    # 座板 (oak_slab)
    seat_y = top_y - chain_len
    b.setblock(76, seat_y, cz, _slab("minecraft:oak_slab", "bottom"))

    # 柱脚碎石装饰
    random.seed(46)
    for bx in [75, 77]:
        for ddx in [-1, 0, 1]:
            for ddz in [-1, 0, 1]:
                if ddx == 0 and ddz == 0:
                    continue
                nx, nz = bx + ddx, cz + ddz
                if 75 <= nx <= 77 and 7 <= nz <= 9:
                    continue  # 不覆盖秋千本体区域
                if random.random() < 0.4:
                    b.setblock(nx, gy, nz, GRAVEL)

    b.register_bbox("swing", 74, gy, 6, 78, top_y + 1, 10)
    print(f"    秋千完成. [{b.cmd_count} cmds]")


# ═══════════════════════════════════════════
# Step 8: 太湖石→濯缨水阁 坡道
# ═══════════════════════════════════════════

def _build_slope_to_zhuoying(b: MinecraftBuilder):
    """坡道: 从太湖石南缘(Z=15)到濯缨水阁北缘(Z=23), Y=-57降→-59

    宽3格石阶, 沿 x=82 居中 (x=81~83)
    Z=15~17: Y=-57, Z=18~19: Y=-58, Z=20~23: Y=-59
    """
    print("  [8/9] 太湖石→濯缨水阁 坡道...")

    slope_x1, slope_x2 = 81, 83
    z_start, z_end = 15, 23

    for z in range(z_start, z_end + 1):
        if z <= 17:
            floor_y = -57
        elif z <= 19:
            floor_y = -58
        else:
            floor_y = -59

        # 铺石阶面
        b.fill(slope_x1, floor_y, z, slope_x2, floor_y, z, BASE)

        # 台阶过渡
        if z == 18:
            b.fill(slope_x1, -57, z, slope_x2, -57, z,
                   _stair(BASE_STEP, "south"))
        elif z == 20:
            b.fill(slope_x1, -58, z, slope_x2, -58, z,
                   _stair(BASE_STEP, "south"))

    # 两侧栏杆
    for z in range(z_start, z_end + 1):
        if z <= 17:
            ry = -57
        elif z <= 19:
            ry = -58
        else:
            ry = -59
        b.setblock(slope_x1 - 1, ry + 1, z, RAIL)
        b.setblock(slope_x2 + 1, ry + 1, z, RAIL)

    # 填充坡道下方（防止空洞）
    for z in range(18, z_end + 1):
        if z <= 19:
            b.fill(slope_x1, -59, z, slope_x2, -59, z, DIRT)
            b.fill(slope_x1, -58, z, slope_x2, -58, z, BASE)
        else:
            b.fill(slope_x1, -60, z, slope_x2, -60, z, DIRT)
            b.fill(slope_x1, -59, z, slope_x2, -59, z, BASE)

    b.register_bbox("slope_to_zhuoying", slope_x1 - 1, -60, z_start, slope_x2 + 1, -56, z_end)
    print(f"    坡道完成. [{b.cmd_count} cmds]")


# ═══════════════════════════════════════════
# Step 9: 濯缨水阁
# ═══════════════════════════════════════════

def _build_zhuoying_pavilion(b: MinecraftBuilder):
    """濯缨水阁: (77~87, 23~29), Y=-59
    半水半陆 — 北半(Z=23~25)在陆上, 南半(Z=26~29)架在水面上
    悬山顶, 朝南敞开, 其余面半封闭
    柱高5格
    """
    print("  [9/9] 濯缨水阁...")

    x1, z1, x2, z2 = 77, 23, 87, 29
    gy = -59
    cx = (x1 + x2) // 2  # 82
    cz = (z1 + z2) // 2  # 26
    pillar_h = 5

    # ── 台基: 北半陆上实心, 南半水上架空 ──
    # 北半 (Z=23~25): 实心台基
    b.fill(x1 - 1, gy, z1 - 1, x2 + 1, gy, 25, BASE_COL)  # 散水
    b.fill(x1, gy, z1, x2, gy, 25, BASE)
    b.fill(x1, gy + 1, z1, x2, gy + 1, 25, BASE)

    # 南半 (Z=26~29): 水下柱础 + 水面上台基
    # 水面 Y=-61, 柱础从 -63 开始打到 -59
    water_y = cfg.WATER_SURFACE_Y  # -61
    # 架空柱: 四角 + 每面中间(共约8根支撑柱)
    water_pillar_positions = [
        (x1, z2), (x2, z2),          # 南面两角
        (x1, 26), (x2, 26),          # 水陆交界
        (cx, z2), (cx, 26),           # 中间柱
    ]
    for (px, pz) in water_pillar_positions:
        # 从水底到台基面的支撑柱
        b.fill(px, water_y - 2, pz, px, gy, pz, BASE)

    # 南半台基面
    b.fill(x1, gy, 26, x2, gy, z2, BASE)
    b.fill(x1, gy + 1, 26, x2, gy + 1, z2, BASE)

    # 南半散水 (在水面上用 slab 表现)
    b.fill(x1 - 1, gy, 26, x1 - 1, gy, z2 + 1, BASE_COL)
    b.fill(x2 + 1, gy, 26, x2 + 1, gy, z2 + 1, BASE_COL)
    b.fill(x1, gy, z2 + 1, x2, gy, z2 + 1, BASE_COL)

    floor_y = gy + 2  # 台基顶面 + 1 = 地面层

    # ── 地面铺装 ──
    b.fill(x1, floor_y, z1, x2, floor_y, z2, FLOOR)
    for z in range(z1, z2 + 1):
        if (z - z1) % 2 == 1:
            b.fill(x1, floor_y, z, x2, floor_y, z, BASE_COL)
    # 南半靠水侧铺木地板
    b.fill(x1, floor_y, 27, x2, floor_y, z2, FLOOR_WOOD)

    # ── 柱子 ──
    pillar_top_y = floor_y + pillar_h
    pillar_positions = [
        (x1, z1), (x1, z2), (x2, z1), (x2, z2),  # 四角
        (cx, z1), (cx, z2),                         # 南北面中间
        (x1, cz), (x2, cz),                         # 东西面中间
    ]

    for (px, pz) in pillar_positions:
        b.setblock(px, floor_y, pz, BASE_COL)  # 柱础
        b.fill(px, floor_y + 1, pz, px, pillar_top_y, pz, PILLAR)

    # ── 梁枋 ──
    beam_y = pillar_top_y
    b.fill(x1, beam_y, z1, x2, beam_y, z1, BEAM)
    b.fill(x1, beam_y, z2, x2, beam_y, z2, BEAM)
    b.fill(x1, beam_y, z1, x1, beam_y, z2, BEAM)
    b.fill(x2, beam_y, z1, x2, beam_y, z2, BEAM)

    # ── 墙体 (半封闭: 南面敞开, 北/东/西面有墙+窗) ──
    wall_h = pillar_h - 1
    wall_top = floor_y + wall_h

    # 北墙
    b.fill(x1, floor_y + 1, z1, x2, wall_top, z1, WALL_BLOCK)
    b.fill(cx - 1, floor_y + 2, z1, cx + 1, min(floor_y + 3, wall_top), z1, WINDOW)
    # 北墙门 (对接坡道)
    b.fill(cx - 1, floor_y + 1, z1, cx + 1, floor_y + 2, z1, AIR)

    # 西墙
    b.fill(x1, floor_y + 1, z1, x1, wall_top, z2, WALL_BLOCK)
    b.fill(x1, floor_y + 2, cz - 1, x1, min(floor_y + 3, wall_top), cz + 1, WINDOW)

    # 东墙
    b.fill(x2, floor_y + 1, z1, x2, wall_top, z2, WALL_BLOCK)
    b.fill(x2, floor_y + 2, cz - 1, x2, min(floor_y + 3, wall_top), cz + 1, WINDOW)

    # 南面敞开 — 栏杆
    b.fill(x1, floor_y + 1, z2, x2, floor_y + 1, z2, RAIL)
    # 南面留中间入口
    b.fill(cx - 1, floor_y + 1, z2, cx + 1, floor_y + 1, z2, AIR)

    # ── 悬山顶 (屋脊沿X, 南北两面坡) ──
    roof_base_y = beam_y + 1
    _build_gable_roof_x(b, x1, z1, x2, z2, roof_base_y)

    # ── 灯笼 ──
    lantern_y = beam_y - 1
    for (px, pz) in [(x1, z1), (x1, z2), (x2, z1), (x2, z2)]:
        dx = 1 if px < cx else -1
        dz = 1 if pz < cz else -1
        b.setblock(px + dx, lantern_y, pz + dz, f"{LANTERN}[hanging=true]")

    # ── 水面装饰: 南侧水面放荷叶 ──
    for lx, lz in [(x1 + 2, z2 + 2), (x2 - 2, z2 + 3), (cx, z2 + 4)]:
        b.setblock(lx, water_y, lz, P["lily"])

    roof_top_est = roof_base_y + (z2 - z1) // 2 + 3
    b.register_bbox("zhuoying_pavilion",
                     x1 - 2, water_y - 2, z1 - 1, x2 + 2, roof_top_est, z2 + 2)
    print(f"    濯缨水阁完成. [{b.cmd_count} cmds]")


def _build_gable_roof_x(b, x1, z1, x2, z2, base_y):
    """悬山顶 — 屋脊沿X方向, 南北两面坡"""
    cz = (z1 + z2) // 2
    half_span = cz - z1 + 1
    y = base_y

    # 出檐
    ox1, ox2 = x1 - 1, x2 + 1

    for layer in range(half_span + 1):
        nz = z1 - 1 + layer   # 北坡当前Z
        sz = z2 + 1 - layer   # 南坡当前Z

        if nz > cz:
            break

        if nz == sz:
            # 屋脊
            b.fill(ox1, y, nz, ox2, y, nz, _slab(ROOF_SLAB, "bottom"))
        else:
            if nz == cz or sz == cz:
                if nz <= cz:
                    b.fill(ox1, y, nz, ox2, y, nz, ROOF_BLOCK)
                if sz >= cz:
                    b.fill(ox1, y, sz, ox2, y, sz, ROOF_BLOCK)
            else:
                b.fill(ox1, y, nz, ox2, y, nz,
                       _stair(ROOF_STAIR, "south"))
                b.fill(ox1, y, sz, ox2, y, sz,
                       _stair(ROOF_STAIR, "north"))
        y += 1

    # 山墙三角 (x=x1 和 x=x2)
    for wall_x in [x1, x2]:
        for dy in range(half_span):
            inner_z1 = z1 + dy
            inner_z2 = z2 - dy
            if inner_z1 < inner_z2:
                b.fill(wall_x, base_y + dy, inner_z1,
                       wall_x, base_y + dy, inner_z2, WALL_BLOCK)

    # 飞檐
    eave_y = base_y - 1
    b.fill(ox1, eave_y, z1 - 2, ox2, eave_y, z1 - 2,
           _stair(EAVE_OUTER, "south", "top"))
    b.fill(ox1, eave_y, z2 + 2, ox2, eave_y, z2 + 2,
           _stair(EAVE_OUTER, "north", "top"))


# ═══════════════════════════════════════════
# 独立运行入口
# ═══════════════════════════════════════════

if __name__ == "__main__":
    with MinecraftBuilder() as b:
        build_cluster_a(b)
        print(f"\nDone! Total commands: {b.cmd_count}")
