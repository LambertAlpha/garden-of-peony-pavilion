"""E群：东岸舫舟群 — 石舫 + 曲廊亭 + 半亭

"烟波画船"——东岸三栋建筑以石舫为核心，
水上栈桥北接曲廊亭，南向滨水廊通半亭，形成水岸游赏序列。

建筑:
  1. 石舫 (83~87, 40~52): 石砖船体，三段式(方亭+平榭+小阁)
  2. 石舫→曲廊亭 水上栈桥 (87~94, 40~44)
  3. 曲廊亭 (94~98, 40~44): 小方亭
  4. 石舫→半亭 南向滨水廊 (85~87, 52~59): 有顶柱廊
  5. 半亭 (85~91, 59~65): 朝西北面湖

坐标来自 config_v4:
  石舫:   cx=85, cz=46, size 5x12
  曲廊亭: cx=96, cz=42, size 5x5
  半亭:   cx=88, cz=62, size 7x7
"""

import sys
sys.path.insert(0, '/Users/lambertlin/minecraft-server/scripts')

from builder import MinecraftBuilder
from blocks import PALETTE
import config_v4 as cfg


# ── 材质快捷引用 ──
STONE_BR    = "minecraft:stone_bricks"
STONE_STAIR = "minecraft:stone_brick_stairs"
STONE_SLAB  = "minecraft:stone_brick_slab"
SMOOTH      = PALETTE["floor"]           # smooth_stone
PILLAR      = PALETTE["pillar"]          # stripped_crimson_stem
RAIL        = PALETTE["rail"]            # crimson_fence
WALL        = PALETTE["wall"]            # white_concrete
BEAM        = PALETTE["beam"]            # dark_oak_planks
BEAM_LOG    = PALETTE["beam_log"]        # dark_oak_log
LANTERN     = PALETTE["lantern"]
TRAPDOOR    = PALETTE["trapdoor"]        # jungle_trapdoor
ROOF_STAIR  = PALETTE["roof"]           # stone_brick_stairs
ROOF_SLAB   = PALETTE["roof_slab"]      # stone_brick_slab
ROOF_BLOCK  = PALETTE["roof_block"]     # stone_bricks
BASE_COL    = PALETTE["base_col"]       # polished_andesite
AIR         = "minecraft:air"

# ── Y 坐标常量 ──
WATER_Y = cfg.WATER_SURFACE_Y  # -61
DECK_Y  = cfg.BUILD_Y          # -60
HULL_Y  = -62                   # 船底(水下1格)


# ═══════════════════════════════════════════
# 1. 石舫 — 三段式石船
# ═══════════════════════════════════════════

def _build_stone_boat(b: MinecraftBuilder):
    """石舫: 中心线 X=85, Z=40~52, 宽 X=83~87 (5格)
    船头(北) Z=40, 船尾(南) Z=52
    三段: 前舱方亭(40~43) + 中舱平榭(44~48) + 后舱小阁(49~52)
    """
    print("  [E-1] 石舫...")

    CX = 85
    X1, X2 = 83, 87
    Z_BOW = 40          # 船头(北)
    Z_STERN = 52        # 船尾(南)

    # 三段分区
    FORE_Z1, FORE_Z2 = 40, 43   # 前舱方亭
    MID_Z1, MID_Z2   = 44, 48   # 中舱平榭
    AFT_Z1, AFT_Z2   = 49, 52   # 后舱小阁

    # ── 1a. 船体 — 石砖基座 ──
    # 船底
    b.fill(X1, HULL_Y, Z_BOW, X2, HULL_Y, Z_STERN, STONE_BR)
    # 船舷 (两侧)
    b.fill(X1, WATER_Y, Z_BOW, X1, WATER_Y, Z_STERN, STONE_BR)
    b.fill(X2, WATER_Y, Z_BOW, X2, WATER_Y, Z_STERN, STONE_BR)
    # 船尾横封
    b.fill(X1, WATER_Y, Z_STERN, X2, WATER_Y, Z_STERN, STONE_BR)

    # ── 1b. 船头收窄 ──
    b.setblock(X1, HULL_Y, Z_BOW,
               f"{STONE_STAIR}[facing=north,half=bottom]")
    b.setblock(X2, HULL_Y, Z_BOW,
               f"{STONE_STAIR}[facing=north,half=bottom]")
    b.setblock(X1, WATER_Y, Z_BOW, AIR)
    b.setblock(X2, WATER_Y, Z_BOW, AIR)
    b.setblock(CX, WATER_Y, Z_BOW, STONE_BR)
    # 尖角
    b.setblock(CX, HULL_Y, Z_BOW - 1,
               f"{STONE_STAIR}[facing=north,half=bottom]")
    b.setblock(CX, WATER_Y, Z_BOW - 1,
               f"{STONE_STAIR}[facing=north,half=top]")

    # ── 1c. 甲板铺面 ──
    b.fill(X1, DECK_Y, Z_BOW, X2, DECK_Y, Z_STERN, SMOOTH)
    # 船头收窄甲板
    b.setblock(X1, DECK_Y, Z_BOW, AIR)
    b.setblock(X2, DECK_Y, Z_BOW, AIR)
    b.setblock(CX, DECK_Y, Z_BOW - 1, f"{STONE_SLAB}[type=top]")

    # 船头灯笼
    b.setblock(CX, DECK_Y + 1, Z_BOW - 1, RAIL)
    b.setblock(CX, DECK_Y + 2, Z_BOW - 1, LANTERN)

    # ── 1d. 前舱 — 方亭 (Z=40~43) ──
    fore_pillars = [
        (X1 + 1, FORE_Z1 + 1),
        (X2 - 1, FORE_Z1 + 1),
        (X1 + 1, FORE_Z2),
        (X2 - 1, FORE_Z2),
    ]
    for px, pz in fore_pillars:
        for y in range(DECK_Y + 1, DECK_Y + 4):
            b.setblock(px, y, pz, PILLAR)

    # 柱顶横梁
    beam_y = DECK_Y + 4
    b.fill(X1 + 1, beam_y, FORE_Z1 + 1, X2 - 1, beam_y, FORE_Z1 + 1, BEAM)
    b.fill(X1 + 1, beam_y, FORE_Z2, X2 - 1, beam_y, FORE_Z2, BEAM)
    b.fill(X1 + 1, beam_y, FORE_Z1 + 1, X1 + 1, beam_y, FORE_Z2, BEAM)
    b.fill(X2 - 1, beam_y, FORE_Z1 + 1, X2 - 1, beam_y, FORE_Z2, BEAM)

    # 攒尖小顶
    ry1 = beam_y + 1
    for x in range(X1, X2 + 1):
        b.setblock(x, ry1, FORE_Z1,
                   f"{STONE_STAIR}[facing=south,half=bottom]")
        b.setblock(x, ry1, FORE_Z2 + 1,
                   f"{STONE_STAIR}[facing=north,half=bottom]")
    for z in range(FORE_Z1, FORE_Z2 + 2):
        b.setblock(X1 - 1, ry1, z,
                   f"{STONE_STAIR}[facing=east,half=bottom]")
        b.setblock(X2 + 1, ry1, z,
                   f"{STONE_STAIR}[facing=west,half=bottom]")
    b.fill(X1, ry1, FORE_Z1 + 1, X2, ry1, FORE_Z2, ROOF_BLOCK)

    ry2 = ry1 + 1
    b.fill(X1 + 1, ry2, FORE_Z1 + 1, X2 - 1, ry2, FORE_Z2, ROOF_BLOCK)
    b.setblock(CX, ry2 + 1, (FORE_Z1 + FORE_Z2) // 2,
               f"{STONE_SLAB}[type=bottom]")

    # ── 1e. 中舱 — 平榭 (Z=44~48) ──
    for z in range(MID_Z1, MID_Z2 + 1):
        b.setblock(X1, DECK_Y + 1, z, RAIL)
        b.setblock(X2, DECK_Y + 1, z, RAIL)
    for x in range(X1, X2 + 1):
        b.setblock(x, DECK_Y + 1, MID_Z1, RAIL)
    # 中舱灯柱
    for z_lamp in [MID_Z1, MID_Z2]:
        for x_lamp in [X1, X2]:
            b.setblock(x_lamp, DECK_Y + 2, z_lamp, LANTERN)

    # ── 1f. 后舱 — 小阁 (Z=49~52) ──
    # 一层墙体 (3格高)
    b.fill(X1, DECK_Y + 1, AFT_Z1, X1, DECK_Y + 3, AFT_Z2, WALL)
    b.fill(X2, DECK_Y + 1, AFT_Z1, X2, DECK_Y + 3, AFT_Z2, WALL)
    b.fill(X1, DECK_Y + 1, AFT_Z2, X2, DECK_Y + 3, AFT_Z2, WALL)
    b.fill(X1, DECK_Y + 1, AFT_Z1, X2, DECK_Y + 3, AFT_Z1, WALL)
    # 门洞 (北墙中间)
    b.setblock(CX, DECK_Y + 1, AFT_Z1, AIR)
    b.setblock(CX, DECK_Y + 2, AFT_Z1, AIR)

    # 花窗 (两侧墙)
    for z_win in [AFT_Z1 + 1, AFT_Z1 + 3]:
        if z_win <= AFT_Z2:
            b.setblock(X1, DECK_Y + 2, z_win, AIR)
            b.setblock(X2, DECK_Y + 2, z_win, AIR)

    # 内柱
    aft_pillars = [
        (X1 + 1, AFT_Z1 + 1),
        (X2 - 1, AFT_Z1 + 1),
        (X1 + 1, AFT_Z2 - 1),
        (X2 - 1, AFT_Z2 - 1),
    ]
    for px, pz in aft_pillars:
        for y in range(DECK_Y + 1, DECK_Y + 4):
            b.setblock(px, y, pz, PILLAR)

    # 二层地板
    floor2_y = DECK_Y + 4
    b.fill(X1, floor2_y, AFT_Z1, X2, floor2_y, AFT_Z2, BEAM)

    # 二层栏杆
    rail2_y = floor2_y + 1
    for x in range(X1, X2 + 1):
        b.setblock(x, rail2_y, AFT_Z1, RAIL)
        b.setblock(x, rail2_y, AFT_Z2, RAIL)
    for z in range(AFT_Z1, AFT_Z2 + 1):
        b.setblock(X1, rail2_y, z, RAIL)
        b.setblock(X2, rail2_y, z, RAIL)

    # 二层角柱
    for px, pz in [(X1, AFT_Z1), (X2, AFT_Z1), (X1, AFT_Z2), (X2, AFT_Z2)]:
        b.setblock(px, rail2_y, pz, PILLAR)
        b.setblock(px, rail2_y + 1, pz, PILLAR)

    # 后舱歇山顶
    roof_base_y = rail2_y + 2
    rx1, rx2 = X1 - 1, X2 + 1
    rz1, rz2 = AFT_Z1 - 1, AFT_Z2 + 1

    for x in range(rx1, rx2 + 1):
        b.setblock(x, roof_base_y, rz1,
                   f"{STONE_STAIR}[facing=south,half=bottom]")
        b.setblock(x, roof_base_y, rz2,
                   f"{STONE_STAIR}[facing=north,half=bottom]")
    for z in range(rz1 + 1, rz2):
        b.setblock(rx1, roof_base_y, z,
                   f"{STONE_STAIR}[facing=east,half=bottom]")
        b.setblock(rx2, roof_base_y, z,
                   f"{STONE_STAIR}[facing=west,half=bottom]")
    b.fill(X1, roof_base_y, AFT_Z1, X2, roof_base_y, AFT_Z2, ROOF_BLOCK)

    # 歇山第二层
    ry = roof_base_y + 1
    for x in range(X1, X2 + 1):
        b.setblock(x, ry, AFT_Z1,
                   f"{STONE_STAIR}[facing=south,half=bottom]")
        b.setblock(x, ry, AFT_Z2,
                   f"{STONE_STAIR}[facing=north,half=bottom]")
    for z in range(AFT_Z1 + 1, AFT_Z2):
        b.setblock(X1, ry, z,
                   f"{STONE_STAIR}[facing=east,half=bottom]")
        b.setblock(X2, ry, z,
                   f"{STONE_STAIR}[facing=west,half=bottom]")
    b.fill(X1 + 1, ry, AFT_Z1 + 1, X2 - 1, ry, AFT_Z2 - 1, ROOF_BLOCK)

    # 歇山脊线
    ry3 = ry + 1
    for z in range(AFT_Z1 + 1, AFT_Z2):
        b.setblock(CX, ry3, z, f"{STONE_SLAB}[type=bottom]")
    b.setblock(CX, ry3, AFT_Z1,
               f"{STONE_STAIR}[facing=south,half=bottom]")
    b.setblock(CX, ry3, AFT_Z2,
               f"{STONE_STAIR}[facing=north,half=bottom]")

    # 后舱灯笼
    for px, pz in aft_pillars:
        b.setblock(px, floor2_y + 1, pz, LANTERN)

    b.register_bbox("cluster_e_stone_boat",
                    X1 - 1, HULL_Y, Z_BOW - 1,
                    X2 + 1, roof_base_y + 2, Z_STERN + 1)


# ═══════════════════════════════════════════
# 2. 水上栈桥: 石舫→曲廊亭 (87~94, 40~44)
# ═══════════════════════════════════════════

def _build_north_bridge(b: MinecraftBuilder):
    """石舫东侧→曲廊亭的水上栈桥
    从石舫东壁(X=87) 向东到曲廊亭西壁(X=94)
    Z 中心 ~42, 宽3格 (Z=41~43)
    """
    print("  [E-2] 水上栈桥 (石舫→曲廊亭)...")

    BX1, BX2 = 88, 93   # 栈桥 X 范围 (船体外到亭子外)
    BZ_C = 42            # 中心 Z
    BZ1, BZ2 = 41, 43   # 宽3格

    # 桥面
    b.fill(BX1, DECK_Y, BZ1, BX2, DECK_Y, BZ2,
           f"{STONE_SLAB}[type=top]")

    # 桥墩 (每隔3格一对)
    for x in [BX1, BX1 + 3, BX2]:
        for z in [BZ1, BZ2]:
            for y in range(-63, DECK_Y):
                b.setblock(x, y, z, PILLAR)

    # 两侧栏杆
    for x in range(BX1, BX2 + 1):
        b.setblock(x, DECK_Y + 1, BZ1, RAIL)
        b.setblock(x, DECK_Y + 1, BZ2, RAIL)

    # 栈桥灯笼 (中点)
    mid_x = (BX1 + BX2) // 2
    b.setblock(mid_x, DECK_Y + 2, BZ1, LANTERN)
    b.setblock(mid_x, DECK_Y + 2, BZ2, LANTERN)

    b.register_bbox("cluster_e_north_bridge",
                    BX1, HULL_Y, BZ1, BX2, DECK_Y + 2, BZ2)


# ═══════════════════════════════════════════
# 3. 曲廊亭 (94~98, 40~44) — 小方亭
# ═══════════════════════════════════════════

def _build_corridor_pavilion(b: MinecraftBuilder):
    """曲廊亭: 中心(96,42), 5x5 方亭
    范围 X=94~98, Z=40~44
    4根角柱 + 攒尖小顶，连接东岸廊道转折
    """
    print("  [E-3] 曲廊亭...")

    CX, CZ = 96, 42
    X1, X2 = 94, 98
    Z1, Z2 = 40, 44
    GY = DECK_Y  # -60

    # 台基 (1层石砖)
    b.fill(X1, GY, Z1, X2, GY, Z2, STONE_BR)
    # 台面铺装
    b.fill(X1 + 1, GY, Z1 + 1, X2 - 1, GY, Z2 - 1, SMOOTH)

    # 4根角柱 (4格高)
    pillar_h = 4
    for px, pz in [(X1, Z1), (X2, Z1), (X1, Z2), (X2, Z2)]:
        b.setblock(px, GY, pz, BASE_COL)
        for dy in range(1, pillar_h + 1):
            b.setblock(px, GY + dy, pz, PILLAR)

    # 栏杆 (四面, 柱间)
    for x in range(X1 + 1, X2):
        b.setblock(x, GY + 1, Z1, RAIL)
        b.setblock(x, GY + 1, Z2, RAIL)
    for z in range(Z1 + 1, Z2):
        b.setblock(X1, GY + 1, z, RAIL)
        b.setblock(X2, GY + 1, z, RAIL)

    # 横梁
    beam_y = GY + pillar_h
    b.fill(X1, beam_y, Z1, X2, beam_y, Z1, BEAM)
    b.fill(X1, beam_y, Z2, X2, beam_y, Z2, BEAM)
    b.fill(X1, beam_y, Z1, X1, beam_y, Z2, BEAM)
    b.fill(X2, beam_y, Z1, X2, beam_y, Z2, BEAM)

    # 攒尖顶 — 3层递缩
    # 第1层: 7x7 出檐 (含楼梯边)
    ry1 = beam_y + 1
    for x in range(X1 - 1, X2 + 2):
        b.setblock(x, ry1, Z1 - 1,
                   f"{ROOF_STAIR}[facing=south,half=bottom]")
        b.setblock(x, ry1, Z2 + 1,
                   f"{ROOF_STAIR}[facing=north,half=bottom]")
    for z in range(Z1 - 1, Z2 + 2):
        b.setblock(X1 - 1, ry1, z,
                   f"{ROOF_STAIR}[facing=east,half=bottom]")
        b.setblock(X2 + 1, ry1, z,
                   f"{ROOF_STAIR}[facing=west,half=bottom]")
    b.fill(X1, ry1, Z1, X2, ry1, Z2, ROOF_BLOCK)

    # 第2层: 3x3
    ry2 = ry1 + 1
    for x in range(X1 + 1, X2):
        b.setblock(x, ry2, Z1 + 1,
                   f"{ROOF_STAIR}[facing=south,half=bottom]")
        b.setblock(x, ry2, Z2 - 1,
                   f"{ROOF_STAIR}[facing=north,half=bottom]")
    b.setblock(X1 + 1, ry2, CZ,
               f"{ROOF_STAIR}[facing=east,half=bottom]")
    b.setblock(X2 - 1, ry2, CZ,
               f"{ROOF_STAIR}[facing=west,half=bottom]")
    b.setblock(CX, ry2, CZ, ROOF_BLOCK)

    # 宝顶
    b.setblock(CX, ry2 + 1, CZ, f"{STONE_SLAB}[type=bottom]")

    # 亭中灯笼
    b.setblock(CX, beam_y - 1, CZ, f"{LANTERN}[hanging=true]")

    b.register_bbox("cluster_e_corridor_pavilion",
                    X1 - 1, GY, Z1 - 1, X2 + 1, ry2 + 2, Z2 + 1)


# ═══════════════════════════════════════════
# 4. 南向滨水廊: 石舫→半亭 (85~87, 52~59)
# ═══════════════════════════════════════════

def _build_south_corridor(b: MinecraftBuilder):
    """石舫南端→半亭的有顶滨水廊
    X=84~86 (宽3格, 中心X=85), Z=53~58
    柱间距3格，有屋顶
    """
    print("  [E-4] 南向滨水廊 (石舫→半亭)...")

    CX = 85
    X_W, X_E = 84, 86   # 宽3格
    Z1, Z2 = 53, 58     # 石舫南端+1 到 半亭北端-1
    GY = DECK_Y          # -60
    PILLAR_H = 4
    PILLAR_SPACE = 3

    # 地面
    b.fill(CX, GY, Z1, CX, GY, Z2, SMOOTH)
    b.fill(X_W, GY, Z1, X_W, GY, Z2, STONE_BR)
    b.fill(X_E, GY, Z1, X_E, GY, Z2, STONE_BR)

    # 柱子+栏杆+屋顶
    length = Z2 - Z1
    pillar_positions = set()
    for i in range(0, length + 1, PILLAR_SPACE):
        pz = Z1 + i
        if pz > Z2:
            break
        pillar_positions.add(pz)
    # 确保末端有柱
    pillar_positions.add(Z2)

    for pz in pillar_positions:
        for side_x in [X_W, X_E]:
            b.setblock(side_x, GY, pz, BASE_COL)
            for dy in range(1, PILLAR_H + 1):
                b.setblock(side_x, GY + dy, pz, PILLAR)
        # 横梁
        b.fill(X_W, GY + PILLAR_H, pz, X_E, GY + PILLAR_H, pz, BEAM)

    # 柱间栏杆
    for z in range(Z1, Z2 + 1):
        if z not in pillar_positions:
            b.setblock(X_W, GY + 1, z, RAIL)
            b.setblock(X_E, GY + 1, z, RAIL)

    # 屋顶
    roof_y = GY + PILLAR_H + 1
    b.fill(X_W - 1, roof_y, Z1, X_E + 1, roof_y, Z2,
           f"{ROOF_SLAB}[type=bottom]")

    # 廊中灯笼 (中点)
    mid_z = (Z1 + Z2) // 2
    b.setblock(CX, GY + PILLAR_H - 1, mid_z, f"{LANTERN}[hanging=true]")

    b.register_bbox("cluster_e_south_corridor",
                    X_W - 1, GY, Z1, X_E + 1, roof_y + 1, Z2)


# ═══════════════════════════════════════════
# 5. 半亭 (85~91, 59~65) — 朝西北面湖
# ═══════════════════════════════════════════

def _build_half_pavilion(b: MinecraftBuilder):
    """半亭: 中心(88,62), 7x7, 朝西北面湖
    范围 X=85~91, Z=59~65
    三面墙(东、南、东南) + 西北开敞面湖
    """
    print("  [E-5] 半亭...")

    CX, CZ = 88, 62
    X1, X2 = 85, 91
    Z1, Z2 = 59, 65
    GY = DECK_Y  # -60
    PILLAR_H = 5

    # 台基
    b.fill(X1, GY, Z1, X2, GY, Z2, STONE_BR)
    b.fill(X1 + 1, GY, Z1 + 1, X2 - 1, GY, Z2 - 1, SMOOTH)

    # 柱子 — 半亭只在后半(东+南)设全柱，西北开敞
    # 后排柱 (东侧 X2, 南侧 Z2)
    full_pillars = [
        (X2, Z1),      # 东北角
        (X2, Z2),      # 东南角
        (X1, Z2),      # 西南角
        (X2, CZ),      # 东侧中柱
    ]
    # 前排柱 (西北开敞面，只设2根)
    open_pillars = [
        (X1, Z1),      # 西北角
        (CX, Z1),      # 北侧中柱
    ]

    all_pillars = full_pillars + open_pillars
    for px, pz in all_pillars:
        b.setblock(px, GY, pz, BASE_COL)
        for dy in range(1, PILLAR_H + 1):
            b.setblock(px, GY + dy, pz, PILLAR)

    # 后墙 (东墙 + 南墙 — 半围合)
    beam_y = GY + PILLAR_H
    # 东墙: 白墙 (X2, Z1~Z2, GY+1~GY+3)
    b.fill(X2, GY + 1, Z1 + 1, X2, GY + 3, Z2 - 1, WALL)
    # 南墙: 白墙 (X1~X2, Z2, GY+1~GY+3)
    b.fill(X1 + 1, GY + 1, Z2, X2 - 1, GY + 3, Z2, WALL)
    # 东墙花窗
    b.setblock(X2, GY + 2, CZ, AIR)
    # 南墙花窗
    b.setblock(CX, GY + 2, Z2, AIR)

    # 西面+北面: 栏杆 (开敞面)
    for z in range(Z1 + 1, Z2):
        b.setblock(X1, GY + 1, z, RAIL)
    for x in range(X1 + 1, X2):
        b.setblock(x, GY + 1, Z1, RAIL)

    # 横梁 (四面)
    b.fill(X1, beam_y, Z1, X2, beam_y, Z1, BEAM)
    b.fill(X1, beam_y, Z2, X2, beam_y, Z2, BEAM)
    b.fill(X1, beam_y, Z1, X1, beam_y, Z2, BEAM)
    b.fill(X2, beam_y, Z1, X2, beam_y, Z2, BEAM)

    # 歇山顶
    ry1 = beam_y + 1
    rx1, rx2 = X1 - 1, X2 + 1
    rz1, rz2 = Z1 - 1, Z2 + 1

    for x in range(rx1, rx2 + 1):
        b.setblock(x, ry1, rz1,
                   f"{ROOF_STAIR}[facing=south,half=bottom]")
        b.setblock(x, ry1, rz2,
                   f"{ROOF_STAIR}[facing=north,half=bottom]")
    for z in range(rz1 + 1, rz2):
        b.setblock(rx1, ry1, z,
                   f"{ROOF_STAIR}[facing=east,half=bottom]")
        b.setblock(rx2, ry1, z,
                   f"{ROOF_STAIR}[facing=west,half=bottom]")
    b.fill(X1, ry1, Z1, X2, ry1, Z2, ROOF_BLOCK)

    # 第二层
    ry2 = ry1 + 1
    for x in range(X1 + 1, X2):
        b.setblock(x, ry2, Z1 + 1,
                   f"{ROOF_STAIR}[facing=south,half=bottom]")
        b.setblock(x, ry2, Z2 - 1,
                   f"{ROOF_STAIR}[facing=north,half=bottom]")
    for z in range(Z1 + 2, Z2 - 1):
        b.setblock(X1 + 1, ry2, z,
                   f"{ROOF_STAIR}[facing=east,half=bottom]")
        b.setblock(X2 - 1, ry2, z,
                   f"{ROOF_STAIR}[facing=west,half=bottom]")
    b.fill(X1 + 2, ry2, Z1 + 2, X2 - 2, ry2, Z2 - 2, ROOF_BLOCK)

    # 脊线
    ry3 = ry2 + 1
    for z in range(Z1 + 2, Z2 - 1):
        b.setblock(CX, ry3, z, f"{STONE_SLAB}[type=bottom]")

    # 灯笼 (亭中悬挂)
    b.setblock(CX, beam_y - 1, CZ, f"{LANTERN}[hanging=true]")

    # 美人靠 (西北面湖方向，X1+1~CX-1, Z1+1, GY+1 放座椅模拟)
    for x in range(X1 + 1, CX):
        b.setblock(x, GY, Z1 + 1, BEAM)
        b.setblock(x, GY + 1, Z1 + 1,
                   f"{ROOF_STAIR}[facing=south,half=bottom]")

    b.register_bbox("cluster_e_half_pavilion",
                    rx1, GY, rz1, rx2, ry3 + 1, rz2)


# ═══════════════════════════════════════════
# 总入口
# ═══════════════════════════════════════════

def build_cluster_e(b: MinecraftBuilder):
    """E群：东岸 — 石舫+曲廊亭+半亭"""
    print("=" * 50)
    print("=== E群: 东岸舫舟群 ===")
    print("=" * 50)

    cmd_start = b.cmd_count

    _build_stone_boat(b)
    _build_north_bridge(b)
    _build_corridor_pavilion(b)
    _build_south_corridor(b)
    _build_half_pavilion(b)

    print(f"  E群完成! ({b.cmd_count - cmd_start} commands)")


# ── 独立测试入口 ──

if __name__ == "__main__":
    with MinecraftBuilder() as b:
        build_cluster_e(b)
        print(f"Done! Total commands: {b.cmd_count}")
