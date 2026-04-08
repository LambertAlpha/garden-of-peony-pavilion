"""园林填充修复 — 消灭裸草地，实现零裸草中式园林

目标: 裸草地从 30%+ 降至 <5%
方法: 散水带 + 铺装 + 石组 + 种植带 + 竹林 + 驳岸加强

原则:
  1. 零裸草: 每块草地替换为铺装/种植/碎石
  2. 三层过渡: 建筑→台基→散水带(gravel)→铺装→种植
  3. 材质混铺: 石砖+安山岩+磨制安山岩
  4. 角落放石组: 3-5块 cobblestone/mossy_cobblestone 不规则堆叠
  5. 有边界的种植: 石砖墙围边，内铺 coarse_dirt 再种花
"""

import sys
sys.path.insert(0, '/Users/lambertlin/minecraft-server/scripts')

from builder import MinecraftBuilder, filled_circle_points
from blocks import PALETTE, GROUND_Y, BUILD_Y
from config import (
    GARDEN, PAVILION, HALL, PEONY_RAIL, SWING,
    GATE_AREA, POND, CORRIDOR, BRIDGE, BOAT,
    TAIHU_ROCKS, PLUM_TREE, WALL,
)
import random
import math


# ══════════════════════════════════════════════════════════════
#  建筑排除区 — 所有 setblock/fill 前必须检查
# ══════════════════════════════════════════════════════════════

# 矩形排除区: (x1, z1, x2, z2) 含安全边距
_RECT_ZONES = [
    # 翠轩本体 (cx=16, cz=35, 17x11) + 安全1格
    (16 - 17 // 2 - 1, 35 - 11 // 2 - 1, 16 + 17 // 2 + 1, 35 + 11 // 2 + 1),
    # 芍药阑 (cx=78, cz=29, 11x9) + 安全1格
    (78 - 5 - 1, 29 - 4 - 1, 78 + 5 + 1, 29 + 4 + 1),
    # 入口区庭院 (从 gate.py: COURT 38~48, 53~59 + 门楼 41~45, Z=60)
    (37, 48, 49, 61),
    # 曲廊各段 (宽3格，中心线+-1，再留1格安全距离=+-2)
    # A(38,38)→B(20,38) X段
    (19, 36, 39, 40),
    # B(20,38)→C(20,28) Z段
    (18, 27, 22, 39),
    # C(20,28)→D(20,15) Z段
    (18, 14, 22, 29),
    # D(20,15)→E(35,15) X段
    (19, 13, 36, 17),
    # E(35,15)→F(35,10) Z段
    (33, 9, 37, 16),
    # F(35,10)→G(45,10) X段
    (34, 8, 46, 12),
    # 廊桥 (cx=45, z35~55, w=5)
    (45 - 3, 34, 45 + 3, 56),
    # 画船
    (25 - 4, 42 - 3, 25 + 4, 42 + 3),
    # 太湖石区域
    (45 - 5, 12 - 5, 45 + 5, 12 + 5),
    # 秋千区域
    (62 - 3, 25 - 3, 62 + 3, 25 + 3),
    # 大梅树
    (10 - 6, 10 - 6, 10 + 6, 10 + 6),
    # 断井 (3处，各±3)
    (90 - 3, 60 - 3, 90 + 3, 60 + 3),
    (95 - 3, 15 - 3, 95 + 3, 15 + 3),
    (10 - 3, 55 - 3, 10 + 3, 55 + 3),
]


def _in_pond(x, z):
    """椭圆池塘判定"""
    cx, cz = POND["cx"], POND["cz"]
    rx, rz = POND["rx"], POND["rz"]
    return ((x - cx) / rx) ** 2 + ((z - cz) / rz) ** 2 <= 1.05


def _in_pavilion_circle(x, z):
    """牡丹亭圆形台基判定 (r_base=8 + 安全1格)"""
    cx, cz = PAVILION["cx"], PAVILION["cz"]
    r = PAVILION["r_base"] + 1
    return (x - cx) ** 2 + (z - cz) ** 2 <= r * r


def _is_building(x, z):
    """检查 (x,z) 是否在已有建筑/结构范围内，是则返回 True"""
    # 圆形区域
    if _in_pavilion_circle(x, z):
        return True
    # 池塘
    if _in_pond(x, z):
        return True
    # 矩形区域
    for x1, z1, x2, z2 in _RECT_ZONES:
        if x1 <= x <= x2 and z1 <= z <= z2:
            return True
    # 围墙线 (X=0, X=120, Z=0, Z=90 各1格厚)
    if x <= 1 or x >= GARDEN["x_max"] - 1:
        return True
    if z <= 1 or z >= GARDEN["z_max"] - 1:
        return True
    return False


def _in_garden(x, z):
    """是否在园林范围内"""
    return (GARDEN["x_min"] + 2 <= x <= GARDEN["x_max"] - 2 and
            GARDEN["z_min"] + 2 <= z <= GARDEN["z_max"] - 2)


def _safe(x, z):
    """可安全放置: 在园内且不在建筑上"""
    return _in_garden(x, z) and not _is_building(x, z)


# ══════════════════════════════════════════════════════════════
#  材质常量
# ══════════════════════════════════════════════════════════════

GRAVEL = PALETTE["gravel"]                         # minecraft:gravel
STONE_BRICKS = PALETTE["base"]                     # minecraft:stone_bricks
ANDESITE = "minecraft:andesite"
POLISHED_ANDESITE = PALETTE["base_col"]            # minecraft:polished_andesite
COBBLESTONE = PALETTE["cobblestone"]               # minecraft:cobblestone
MOSSY_COBBLESTONE = PALETTE["mossy_cobblestone"]   # minecraft:mossy_cobblestone
COARSE_DIRT = "minecraft:coarse_dirt"
STONE_BRICK_WALL = "minecraft:stone_brick_wall"
SMOOTH_STONE = PALETTE["floor"]                    # minecraft:smooth_stone
GRASS_BLOCK = PALETTE["grass"]                     # minecraft:grass_block

# 混铺材质池 (地面层)
PAVING_BLOCKS = [STONE_BRICKS, ANDESITE, POLISHED_ANDESITE]
# 权重: 石砖50%, 安山岩30%, 磨制安山岩20%
PAVING_WEIGHTS = [0.50, 0.80, 1.00]

# 花卉
FLOWERS_SINGLE = [
    "minecraft:red_tulip", "minecraft:pink_tulip",
    "minecraft:cornflower", "minecraft:azure_bluet",
    "minecraft:oxeye_daisy", "minecraft:allium",
]
FLOWERS_DOUBLE = ["minecraft:peony", "minecraft:rose_bush", "minecraft:lilac"]


def _random_paving():
    """按权重随机选铺装材质"""
    r = random.random()
    for block, threshold in zip(PAVING_BLOCKS, PAVING_WEIGHTS):
        if r < threshold:
            return block
    return STONE_BRICKS


def _place_double(b, x, y, z, block):
    """放置双格高植物"""
    b.setblock(x, y, z, f"{block}[half=lower]")
    b.setblock(x, y + 1, z, f"{block}[half=upper]")


# ══════════════════════════════════════════════════════════════
#  1. 建筑散水带 — 所有建筑台基外围1格 gravel
# ══════════════════════════════════════════════════════════════

def _build_sanshui(b):
    """散水带: 建筑外围1格碎石层，防止雨水冲刷台基"""
    print("  [1/6] 建筑散水带...")
    count = 0

    # --- 牡丹亭 圆形散水 (r_base=8, 散水在 r=9 的圆环) ---
    cx, cz = PAVILION["cx"], PAVILION["cz"]
    pav_y = PAVILION["ground_y"]   # -57 (高地)
    r_inner = PAVILION["r_base"]
    r_outer = r_inner + 1
    for dx in range(-r_outer - 1, r_outer + 2):
        for dz in range(-r_outer - 1, r_outer + 2):
            dist_sq = dx * dx + dz * dz
            # 在 r_inner^2 < dist <= r_outer^2+1 的环上
            if r_inner * r_inner < dist_sq <= (r_outer + 0.5) ** 2:
                gx, gz = cx + dx, cz + dz
                if _in_garden(gx, gz) and not _in_pond(gx, gz):
                    b.setblock(gx, pav_y, gz, GRAVEL)
                    count += 1

    # --- 翠轩 矩形散水 ---
    hcx, hcz = HALL["cx"], HALL["cz"]
    hw, hz = HALL["width_x"] // 2, HALL["width_z"] // 2
    hall_y = HALL["ground_y"]  # -60
    # 台基边界
    hx1, hz1 = hcx - hw, hcz - hz
    hx2, hz2 = hcx + hw, hcz + hz
    # 散水在台基外围1格
    for x in range(hx1 - 1, hx2 + 2):
        for z in range(hz1 - 1, hz2 + 2):
            # 只取外围环 (在外扩范围内但不在原台基内)
            in_base = (hx1 <= x <= hx2 and hz1 <= z <= hz2)
            in_outer = (hx1 - 1 <= x <= hx2 + 1 and hz1 - 1 <= z <= hz2 + 1)
            if in_outer and not in_base:
                if _in_garden(x, z) and not _in_pond(x, z):
                    b.setblock(x, hall_y, z, GRAVEL)
                    count += 1

    # --- 入口区庭院散水 ---
    # 庭院边界 (38~48, 48~61)
    court_x1, court_z1 = 37, 48
    court_x2, court_z2 = 49, 61
    gate_y = BUILD_Y  # -60
    for x in range(court_x1 - 1, court_x2 + 2):
        for z in range(court_z1 - 1, court_z2 + 2):
            in_court = (court_x1 <= x <= court_x2 and court_z1 <= z <= court_z2)
            in_outer = (court_x1 - 1 <= x <= court_x2 + 1 and
                        court_z1 - 1 <= z <= court_z2 + 1)
            if in_outer and not in_court:
                if _in_garden(x, z) and not _in_pond(x, z):
                    b.setblock(x, gate_y, z, GRAVEL)
                    count += 1

    print(f"    散水带: {count} blocks")


# ══════════════════════════════════════════════════════════════
#  2. 主路网铺装
# ══════════════════════════════════════════════════════════════

def _build_paving(b):
    """路网铺装: 曲廊两侧碎石过渡 + 转角广场 + 翠轩前庭"""
    print("  [2/6] 主路网铺装...")
    count = 0

    # --- 曲廊两侧外扩1格碎石过渡 ---
    # 曲廊段: 中心线 +-1 是廊道，+-2 是碎石过渡带
    corridor_segments = [
        # (x1, z1, x2, z2, axis)
        (20, 38, 38, 38, 'x'),   # A→B
        (20, 28, 20, 38, 'z'),   # B→C
        (20, 15, 20, 28, 'z'),   # C→D
        (20, 15, 35, 15, 'x'),   # D→E
        (35, 10, 35, 15, 'z'),   # E→F
        (35, 10, 45, 10, 'x'),   # F→G
    ]

    for sx, sz, ex, ez, axis in corridor_segments:
        if axis == 'x':
            x_lo, x_hi = min(sx, ex), max(sx, ex)
            z_center = sz
            # 外扩带在 z_center-2 和 z_center+2
            for x in range(x_lo, x_hi + 1):
                for z_off in [-2, 2]:
                    gz = z_center + z_off
                    if _safe(x, gz):
                        b.setblock(x, BUILD_Y, gz, GRAVEL)
                        count += 1
        else:  # axis == 'z'
            z_lo, z_hi = min(sz, ez), max(sz, ez)
            x_center = sx
            for z in range(z_lo, z_hi + 1):
                for x_off in [-2, 2]:
                    gx = x_center + x_off
                    if _safe(gx, z):
                        b.setblock(gx, BUILD_Y, z, GRAVEL)
                        count += 1

    # --- 曲廊转角处扩大为 5x5 小广场 ---
    corner_points = [
        (20, 38),  # B
        (20, 15),  # D
        (35, 15),  # E
        (35, 10),  # F
    ]
    for ccx, ccz in corner_points:
        for dx in range(-2, 3):
            for dz in range(-2, 3):
                px, pz = ccx + dx, ccz + dz
                # 跳过廊道本体占据的3x3中心
                if abs(dx) <= 1 and abs(dz) <= 1:
                    continue
                if _in_garden(px, pz) and not _in_pond(px, pz):
                    # 角落用铺装，边缘用碎石
                    if abs(dx) == 2 and abs(dz) == 2:
                        # 四角: 随机铺装
                        b.setblock(px, BUILD_Y, pz, _random_paving())
                    else:
                        b.setblock(px, BUILD_Y, pz, _random_paving())
                    count += 1

    # --- 翠轩前庭铺装 ---
    # 翠轩南面 (Z=41~44 区域, X=8~24)
    hcx, hcz = HALL["cx"], HALL["cz"]
    hw = HALL["width_x"] // 2
    # 前庭在翠轩南侧 (Z增大方向)，从台基边到散水外
    front_x1 = hcx - hw - 1   # 7
    front_x2 = hcx + hw + 1   # 25
    front_z1 = hcz + HALL["width_z"] // 2 + 2   # 43
    front_z2 = front_z1 + 3                       # 46

    for x in range(front_x1, front_x2 + 1):
        for z in range(front_z1, front_z2 + 1):
            if _safe(x, z):
                b.setblock(x, BUILD_Y, z, _random_paving())
                count += 1

    # 翠轩北面也铺一小块 (Z=28~29, X=8~24)
    north_z1 = hcz - HALL["width_z"] // 2 - 3   # 27
    north_z2 = hcz - HALL["width_z"] // 2 - 2   # 28
    for x in range(front_x1, front_x2 + 1):
        for z in range(north_z1, north_z2 + 1):
            if _safe(x, z):
                b.setblock(x, BUILD_Y, z, _random_paving())
                count += 1

    print(f"    铺装: {count} blocks")


# ══════════════════════════════════════════════════════════════
#  3. 角落石组 (假山石)
# ══════════════════════════════════════════════════════════════

def _build_rock_groups(b):
    """6组假山石: 3-5块 cobblestone/mossy_cobblestone 不规则堆叠"""
    print("  [3/6] 角落石组...")

    rock_positions = [
        (100, 50),  # 东南角
        (5, 60),    # 西南角
        (95, 25),   # 东侧
        (60, 60),   # 南侧空地
        (40, 30),   # 池塘北岸
        (85, 15),   # 牡丹亭东侧
    ]

    for rx, rz in rock_positions:
        _place_rock_group(b, rx, rz)

    print(f"    石组: {len(rock_positions)} groups")


def _place_rock_group(b, cx, cz):
    """放置一组假山石 (3~5块不规则堆叠)"""
    if not _in_garden(cx, cz):
        return

    num_rocks = random.randint(3, 5)

    # 底层: 2-3块平铺
    base_offsets = [(0, 0), (1, 0), (0, 1), (-1, 0), (0, -1)]
    random.shuffle(base_offsets)
    base_count = random.randint(2, 3)

    placed_base = []
    for dx, dz in base_offsets[:base_count]:
        bx, bz = cx + dx, cz + dz
        if _safe(bx, bz):
            mat = random.choice([COBBLESTONE, MOSSY_COBBLESTONE, COBBLESTONE])
            b.setblock(bx, BUILD_Y, bz, mat)
            placed_base.append((bx, bz))

    # 第二层: 在底层上方1-2块
    if len(placed_base) >= 2:
        for bx, bz in placed_base[:random.randint(1, 2)]:
            mat = random.choice([COBBLESTONE, MOSSY_COBBLESTONE])
            b.setblock(bx, BUILD_Y + 1, bz, mat)

    # 第三层: 偶尔最高处加1块
    if len(placed_base) >= 1 and random.random() < 0.5:
        bx, bz = placed_base[0]
        b.setblock(bx, BUILD_Y + 2, bz, MOSSY_COBBLESTONE)

    # 基座周围: 碎石散布 (模拟碎石散落)
    for dx in range(-2, 3):
        for dz in range(-2, 3):
            if abs(dx) <= 1 and abs(dz) <= 1:
                continue  # 跳过石组核心
            bx, bz = cx + dx, cz + dz
            if _safe(bx, bz) and random.random() < 0.35:
                b.setblock(bx, GROUND_Y, bz, GRAVEL)

    # 石组旁边的苔藓点缀
    for dx, dz in [(-1, -1), (1, 1), (-1, 1), (1, -1)]:
        bx, bz = cx + dx, cz + dz
        if _safe(bx, bz) and random.random() < 0.4:
            b.setblock(bx, GROUND_Y, bz, PALETTE["moss"])


# ══════════════════════════════════════════════════════════════
#  4. 种植带 (花坛式)
# ══════════════════════════════════════════════════════════════

def _build_planting_beds(b):
    """种植带: 石砖墙围边 + coarse_dirt + 混合花"""
    print("  [4/6] 种植带...")
    count = 0

    # --- 4a. 翠轩南侧花坛 (X:10~20, Z:42~48) ---
    bed_x1, bed_x2 = 10, 20
    bed_z1, bed_z2 = 43, 47
    count += _build_bordered_bed(b, bed_x1, bed_z1, bed_x2, bed_z2,
                                 plant_type="mixed_flowers")

    # --- 4b. 秋千周围杜鹃花丛 (X:58~66, Z:22~28) ---
    # 不做围边，散植 flowering_azalea
    azalea_cx, azalea_cz = 62, 25
    azalea_r = 5
    for dx in range(-azalea_r, azalea_r + 1):
        for dz in range(-azalea_r, azalea_r + 1):
            dist_sq = dx * dx + dz * dz
            if dist_sq > azalea_r * azalea_r:
                continue
            ax, az = azalea_cx + dx, azalea_cz + dz
            if not _safe(ax, az):
                continue
            # 密度: 中心密边缘疏
            density = 0.45 if dist_sq < (azalea_r * 0.6) ** 2 else 0.25
            if random.random() < density:
                plant = random.choice([
                    PALETTE["azalea"], PALETTE["azalea"],
                    "minecraft:flowering_azalea",
                ])
                b.setblock(ax, GROUND_Y, az, COARSE_DIRT)
                b.setblock(ax, BUILD_Y, az, plant)
                count += 1

    # --- 4c. 入口区石径两侧低矮灌木 ---
    # 从入口 (Z=60) 向北到曲廊起点 (Z=38)
    # 沿 X=43 (入口中轴线) 两侧各2-3格
    path_x = 43
    for z in range(39, 53):
        for x_off in [-3, -2, 3, 2]:
            bx = path_x + x_off
            if _safe(bx, z) and random.random() < 0.35:
                plant = random.choice([
                    "minecraft:azalea", "minecraft:azalea",
                    "minecraft:fern", "minecraft:short_grass",
                ])
                b.setblock(bx, GROUND_Y, z, COARSE_DIRT)
                b.setblock(bx, BUILD_Y, z, plant)
                count += 1

    print(f"    种植带: {count} blocks")


def _build_bordered_bed(b, x1, z1, x2, z2, plant_type="mixed_flowers"):
    """建造围边花坛: 石砖墙围边 + coarse_dirt 填充 + 种花"""
    count = 0

    # 围边: 石砖墙 (BUILD_Y 层)
    for x in range(x1, x2 + 1):
        for z in [z1, z2]:
            if _safe(x, z):
                b.setblock(x, BUILD_Y, z, STONE_BRICK_WALL)
                count += 1
    for z in range(z1, z2 + 1):
        for x in [x1, x2]:
            if _safe(x, z):
                b.setblock(x, BUILD_Y, z, STONE_BRICK_WALL)
                count += 1

    # 内部填充: coarse_dirt 地面 + 种花
    for x in range(x1 + 1, x2):
        for z in range(z1 + 1, z2):
            if not _safe(x, z):
                continue
            # 地面改 coarse_dirt
            b.setblock(x, GROUND_Y, z, COARSE_DIRT)
            count += 1

            # 种花 (70% 密度)
            if random.random() < 0.70:
                if plant_type == "mixed_flowers":
                    r = random.random()
                    if r < 0.35:
                        flower = random.choice(FLOWERS_SINGLE)
                        b.setblock(x, BUILD_Y, z, flower)
                    elif r < 0.60:
                        flower = random.choice(FLOWERS_DOUBLE)
                        _place_double(b, x, BUILD_Y, z, flower)
                    elif r < 0.80:
                        b.setblock(x, BUILD_Y, z, PALETTE["azalea"])
                    else:
                        b.setblock(x, BUILD_Y, z, "minecraft:flowering_azalea")
                count += 1

    return count


# ══════════════════════════════════════════════════════════════
#  5. 竹林补充
# ══════════════════════════════════════════════════════════════

def _build_bamboo(b):
    """竹林补充: 翠轩西侧加密 + 西南角新增竹丛"""
    print("  [5/6] 竹林补充...")
    count = 0
    bamboo_block = PALETTE["bamboo"]

    # --- 5a. 翠轩西侧补竹 (X:3~8, Z:24~30) ---
    for x in range(3, 9):
        for z in range(24, 31):
            if not _safe(x, z):
                continue
            if random.random() < 0.40:
                # 竹子: 地面dirt + 竹秆3~6格高
                b.setblock(x, GROUND_Y, z, "minecraft:dirt")
                bamboo_h = random.randint(3, 6)
                for dy in range(bamboo_h):
                    stage = "1" if dy == bamboo_h - 1 else "0"
                    leaves = "large" if dy >= bamboo_h - 2 else ("small" if dy == bamboo_h - 3 else "none")
                    b.setblock(x, BUILD_Y + dy, z,
                               f"minecraft:bamboo[age={stage},leaves={leaves}]")
                count += 1

    # --- 5b. 西南角新增竹丛 (X:2~8, Z:50~58) ---
    for x in range(3, 9):
        for z in range(50, 58):
            if not _safe(x, z):
                continue
            if random.random() < 0.35:
                b.setblock(x, GROUND_Y, z, "minecraft:dirt")
                bamboo_h = random.randint(4, 7)
                for dy in range(bamboo_h):
                    stage = "1" if dy == bamboo_h - 1 else "0"
                    leaves = "large" if dy >= bamboo_h - 2 else ("small" if dy == bamboo_h - 3 else "none")
                    b.setblock(x, BUILD_Y + dy, z,
                               f"minecraft:bamboo[age={stage},leaves={leaves}]")
                count += 1

    # 竹林地面铺粗泥 (不种竹的间隙)
    for x in range(3, 9):
        for z in list(range(24, 31)) + list(range(50, 58)):
            if _safe(x, z) and random.random() < 0.30:
                b.setblock(x, GROUND_Y, z, COARSE_DIRT)

    print(f"    竹林: {count} 根竹子")


# ══════════════════════════════════════════════════════════════
#  6. 池塘驳岸加强
# ══════════════════════════════════════════════════════════════

def _build_bank_reinforcement(b):
    """池塘驳岸: 北岸高地堆石 + 西岸太湖石点缀"""
    print("  [6/6] 池塘驳岸加强...")
    count = 0

    pond_cx, pond_cz = POND["cx"], POND["cz"]
    pond_rx, pond_rz = POND["rx"], POND["rz"]

    # --- 6a. 北岸堆叠石头 (Z < pond_cz, 靠近高地) ---
    # 在池塘北缘(Z=33~36)沿X=35~70, 放1-2格高的石头
    for x in range(35, 71):
        for z in range(pond_cz - pond_rz - 2, pond_cz - pond_rz + 2):
            # 只在池塘边缘外侧
            if _in_pond(x, z):
                continue
            if not _in_garden(x, z):
                continue
            # 越靠近水边概率越高
            dist_to_edge = 0
            for dz in range(1, 4):
                if _in_pond(x, z + dz):
                    dist_to_edge = dz
                    break
            if dist_to_edge == 0:
                continue  # 不够近

            if random.random() < 0.55:
                mat = random.choice([
                    COBBLESTONE, MOSSY_COBBLESTONE, COBBLESTONE,
                    "minecraft:stone", ANDESITE,
                ])
                b.setblock(x, BUILD_Y, z, mat)
                count += 1
                # 30% 概率加第二层
                if random.random() < 0.30:
                    mat2 = random.choice([COBBLESTONE, MOSSY_COBBLESTONE])
                    b.setblock(x, BUILD_Y + 1, z, mat2)
                    count += 1

    # --- 6b. 西岸太湖石点缀 (翠轩方向, X=25~32) ---
    taihu_spots = [
        (30, 42),
        (28, 47),
        (32, 50),
    ]

    for tx, tz in taihu_spots:
        if not _in_garden(tx, tz):
            continue
        # 太湖石: dripstone_block + calcite 混合, 高2-3格
        h = random.randint(2, 3)
        for dy in range(h):
            mat = PALETTE["taihu_main"] if random.random() < 0.6 else PALETTE["taihu_white"]
            b.setblock(tx, BUILD_Y + dy, tz, mat)
            count += 1
            # 旁边偏移1格加底座
            if dy == 0:
                for ddx, ddz in [(1, 0), (-1, 0), (0, 1)]:
                    sx, sz = tx + ddx, tz + ddz
                    if _safe(sx, sz) and random.random() < 0.5:
                        b.setblock(sx, BUILD_Y, sz,
                                   random.choice([PALETTE["taihu_main"],
                                                  COBBLESTONE]))
                        count += 1

    print(f"    驳岸: {count} blocks")


# ══════════════════════════════════════════════════════════════
#  主入口
# ══════════════════════════════════════════════════════════════

def fix_garden_fill(b):
    """园林填充总入口 — 消灭裸草地"""
    print("=== 园林填充修复 (零裸草) ===")
    random.seed(2026)

    _build_sanshui(b)
    _build_paving(b)
    _build_rock_groups(b)
    _build_planting_beds(b)
    _build_bamboo(b)
    _build_bank_reinforcement(b)

    b.register_bbox("garden_fill", GARDEN["x_min"], GROUND_Y,
                    GARDEN["z_min"], GARDEN["x_max"],
                    BUILD_Y + 5, GARDEN["z_max"])

    print("=== 园林填充完成 ===")


if __name__ == "__main__":
    with MinecraftBuilder() as b:
        fix_garden_fill(b)
        print(f"Done! {b.cmd_count} commands")
