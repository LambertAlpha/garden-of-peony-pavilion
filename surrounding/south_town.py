"""江南水乡街巷 — 园林南面 Z=92~140

布局:
  Z=92~94   园墙外过渡带
  Z=94~96   北岸沿河步道 (石砖半砖)
  Z=97~101  主运河 (5格宽, 3格深, clay底, 水面睡莲)
  Z=102~103 南岸步道
  Z=104~107 商业街 (石砖路+摊位)
  Z=108~118 民居排 (5栋白墙灰瓦二层小楼)
  Z=119~121 后巷
  Z=125~135 第二排民居 (零星)
  Z=136~140 渐隐空地

X 范围: 约 20~100
"""

import sys; sys.path.insert(0, '/Users/lambertlin/minecraft-server/scripts')
from builder import MinecraftBuilder
from blocks import PALETTE, GROUND_Y, BUILD_Y
import random


# ══════════════════════════════════════════════════════════════
#  常量
# ══════════════════════════════════════════════════════════════

# 运河
CANAL_X1, CANAL_X2 = 20, 100
CANAL_Z1, CANAL_Z2 = 97, 101  # 5格宽
CANAL_DEPTH = 3                # 水面在 GROUND_Y, 底在 GROUND_Y-2

# 石拱桥位置
BRIDGE_POSITIONS = [45, 75]
BRIDGE_WIDTH = 3  # Z 方向宽度

# 民居位置 (X 起始, Z=108~118, 面宽9, 进深7~10)
HOUSE_X_STARTS = [35, 47, 58, 68, 78]
HOUSE_Z_FRONT = 108   # 面向运河（北面）
HOUSE_DEPTH = 10       # Z方向进深
HOUSE_WIDTH = 9        # X方向面宽
HOUSE_TOTAL_H = 11     # 总高: 台基1 + 一层4 + 二层4 + 屋顶2

# 码头
DOCK_X1, DOCK_X2 = 55, 62
DOCK_Z1, DOCK_Z2 = 94, 97

# 商业街
MARKET_X1, MARKET_X2 = 35, 85
MARKET_Z1, MARKET_Z2 = 104, 107

# 方块别名 (简化引用)
STONE_BRICK = "minecraft:stone_bricks"
STONE_BRICK_SLAB = "minecraft:stone_brick_slab"
STONE_BRICK_STAIRS = "minecraft:stone_brick_stairs"
WHITE_CONCRETE = "minecraft:white_concrete"
SPRUCE_LOG = "minecraft:spruce_log"
SPRUCE_STRIPPED = "minecraft:stripped_spruce_log"
SPRUCE_PLANKS = "minecraft:spruce_planks"
SPRUCE_SLAB = "minecraft:spruce_slab"
SPRUCE_STAIRS = "minecraft:spruce_stairs"
SPRUCE_TRAPDOOR = "minecraft:spruce_trapdoor"
SPRUCE_FENCE = "minecraft:spruce_fence"
SPRUCE_FENCE_GATE = "minecraft:spruce_fence_gate"
OAK_FENCE = "minecraft:oak_fence"
COBBLE_WALL = "minecraft:cobblestone_wall"
LANTERN = "minecraft:lantern[hanging=false]"
HANGING_LANTERN = "minecraft:lantern[hanging=true]"
WATER = "minecraft:water"
CLAY = "minecraft:clay"
LILY = "minecraft:lily_pad"
AIR = "minecraft:air"
OAK_LOG = "minecraft:oak_log"
OAK_LEAVES = "minecraft:oak_leaves[persistent=true]"
VINE = "minecraft:vine"
DARK_OAK_PLANKS = "minecraft:dark_oak_planks"
DARK_OAK_SLAB = "minecraft:dark_oak_slab"
DARK_OAK_STAIRS = "minecraft:dark_oak_stairs"


# ══════════════════════════════════════════════════════════════
#  1. 主运河
# ══════════════════════════════════════════════════════════════

def build_canal(b):
    """X:20~100, Z:97~101, 深3格, clay底, 填水到 GROUND_Y"""
    print("  [1/7] 主运河...")

    # 先清空运河区域上方(移除 landscape_v3 的旧结构)
    b.fill(CANAL_X1 - 2, BUILD_Y, CANAL_Z1 - 3,
           CANAL_X2 + 2, BUILD_Y + 15, CANAL_Z2 + 3, AIR)

    # 挖运河: 3格深 (GROUND_Y, GROUND_Y-1, GROUND_Y-2)
    for depth in range(CANAL_DEPTH):
        y = GROUND_Y - depth
        b.fill(CANAL_X1, y, CANAL_Z1, CANAL_X2, y, CANAL_Z2, AIR)

    # 河底 clay
    b.fill(CANAL_X1, GROUND_Y - CANAL_DEPTH, CANAL_Z1,
           CANAL_X2, GROUND_Y - CANAL_DEPTH, CANAL_Z2, CLAY)

    # 填水到 GROUND_Y
    for depth in range(CANAL_DEPTH):
        y = GROUND_Y - depth
        b.fill(CANAL_X1, y, CANAL_Z1, CANAL_X2, y, CANAL_Z2, WATER)

    # 北岸 (Z=96): 石砖楼梯做斜坡入水
    for x in range(CANAL_X1, CANAL_X2 + 1):
        # 楼梯面朝南(facing=south)，形成缓坡入水
        b.setblock(x, GROUND_Y, CANAL_Z1 - 1,
                   f"{STONE_BRICK_STAIRS}[facing=south,half=bottom]")

    # 南岸 (Z=102): 石砖直壁(码头面)
    for x in range(CANAL_X1, CANAL_X2 + 1):
        for dy in range(CANAL_DEPTH):
            b.setblock(x, GROUND_Y - dy, CANAL_Z2 + 1, STONE_BRICK)

    # 水面睡莲 (稀疏随机)
    lily_count = 0
    for x in range(CANAL_X1 + 2, CANAL_X2 - 2, 3):
        for z in range(CANAL_Z1, CANAL_Z2 + 1):
            if random.random() < 0.08:
                b.setblock(x, GROUND_Y + 1, z, LILY)
                lily_count += 1

    print(f"    运河完成, 睡莲 {lily_count} 朵")


# ══════════════════════════════════════════════════════════════
#  2. 石拱桥
# ══════════════════════════════════════════════════════════════

def build_bridges(b):
    """2座石拱桥, X=45 和 X=75, 宽3格, 跨运河"""
    print("  [2/7] 石拱桥...")

    for bx in BRIDGE_POSITIONS:
        _build_one_bridge(b, bx)
        print(f"    拱桥 @ X={bx}")


def _build_one_bridge(b, center_x):
    """单座石拱桥: 跨 Z=97~101 (5格运河), 桥面宽3格(X方向)"""
    # 桥在 X 方向宽3格
    x1 = center_x - 1
    x2 = center_x + 1

    # 桥跨度: 从北岸 Z=95 到南岸 Z=103 (含引桥)
    # 运河: Z=97~101
    # 桥拱最高点在运河中心 Z=99, 高出水面2格 (BUILD_Y+1)

    bridge_top_y = BUILD_Y + 1  # 桥面高度
    arch_peak_y = BUILD_Y       # 拱顶(水面上1格)

    # --- 桥面 ---
    for x in range(x1, x2 + 1):
        # 北引桥 Z=95~96
        b.setblock(x, BUILD_Y, 95, f"{STONE_BRICK_STAIRS}[facing=south,half=bottom]")
        b.setblock(x, bridge_top_y, 96, STONE_BRICK_SLAB)

        # 桥面主体 Z=97~101
        for z in range(CANAL_Z1, CANAL_Z2 + 1):
            b.setblock(x, bridge_top_y, z, STONE_BRICK_SLAB)

        # 南引桥 Z=102~103
        b.setblock(x, bridge_top_y, 102, STONE_BRICK_SLAB)
        b.setblock(x, BUILD_Y, 103, f"{STONE_BRICK_STAIRS}[facing=north,half=bottom]")

    # --- 拱洞 (在桥面之下,让船通行) ---
    # 拱形: 运河中心Z=99处拱顶最高, 两端Z=97,Z=101处最低
    # 拱用石砖楼梯构造

    # 北侧拱脚 Z=97: 实心石砖柱
    for x in range(x1, x2 + 1):
        for dy in range(-CANAL_DEPTH + 1, 1):  # 从水底到水面
            b.setblock(x, GROUND_Y + dy, CANAL_Z1, STONE_BRICK)

    # 南侧拱脚 Z=101: 实心石砖柱
    for x in range(x1, x2 + 1):
        for dy in range(-CANAL_DEPTH + 1, 1):
            b.setblock(x, GROUND_Y + dy, CANAL_Z2, STONE_BRICK)

    # 拱弧线 (侧面, X=x1-1 和 X=x2+1 可见)
    # Z=98: 楼梯(向北倾斜)
    for x in range(x1, x2 + 1):
        b.setblock(x, GROUND_Y, 98,
                   f"{STONE_BRICK_STAIRS}[facing=north,half=bottom]")
    # Z=99: 拱顶(最高点), 留空让水面可见, 或放石砖
    for x in range(x1, x2 + 1):
        b.setblock(x, arch_peak_y, 99, STONE_BRICK)
    # Z=100: 楼梯(向南倾斜)
    for x in range(x1, x2 + 1):
        b.setblock(x, GROUND_Y, 100,
                   f"{STONE_BRICK_STAIRS}[facing=south,half=bottom]")

    # --- 栏杆 (桥两侧) ---
    for z in range(96, 103):
        b.setblock(x1 - 1, bridge_top_y + 1, z, COBBLE_WALL)
        b.setblock(x2 + 1, bridge_top_y + 1, z, COBBLE_WALL)

    # 桥头柱(略高)
    for x_side in [x1 - 1, x2 + 1]:
        for z_end in [95, 103]:
            b.setblock(x_side, bridge_top_y + 1, z_end, COBBLE_WALL)
            b.setblock(x_side, bridge_top_y + 2, z_end, COBBLE_WALL)


# ══════════════════════════════════════════════════════════════
#  3. 沿河步道
# ══════════════════════════════════════════════════════════════

def build_promenades(b):
    """北岸 Z=94~96, 南岸 Z=102~103: 石砖半砖铺地 + 灯笼"""
    print("  [3/7] 沿河步道...")

    # 北岸步道 Z=94~96
    for x in range(CANAL_X1, CANAL_X2 + 1):
        for z in [94, 95]:
            b.setblock(x, GROUND_Y, z, STONE_BRICK)
            b.setblock(x, BUILD_Y, z, STONE_BRICK_SLAB)

    # 南岸步道 Z=102~103
    for x in range(CANAL_X1, CANAL_X2 + 1):
        for z in [102, 103]:
            b.setblock(x, GROUND_Y, z, STONE_BRICK)
            b.setblock(x, BUILD_Y, z, STONE_BRICK_SLAB)

    # 北岸灯笼: 每8格一个
    lantern_ct = 0
    for x in range(CANAL_X1 + 2, CANAL_X2, 8):
        # 灯笼柱: 栅栏 + 灯笼
        b.setblock(x, BUILD_Y, 94, SPRUCE_FENCE)
        b.setblock(x, BUILD_Y + 1, 94, SPRUCE_FENCE)
        b.setblock(x, BUILD_Y + 2, 94, LANTERN)
        lantern_ct += 1

    # 南岸灯笼
    for x in range(CANAL_X1 + 6, CANAL_X2, 8):
        b.setblock(x, BUILD_Y, 103, SPRUCE_FENCE)
        b.setblock(x, BUILD_Y + 1, 103, SPRUCE_FENCE)
        b.setblock(x, BUILD_Y + 2, 103, LANTERN)
        lantern_ct += 1

    print(f"    步道完成, 灯笼 {lantern_ct} 盏")


# ══════════════════════════════════════════════════════════════
#  4. 商业街
# ══════════════════════════════════════════════════════════════

def build_market_street(b):
    """Z=104~107, X:35~85, 石砖路面 + 摊位框架 + 旗帜"""
    print("  [4/7] 商业街...")

    # 路面
    b.fill(MARKET_X1, GROUND_Y, MARKET_Z1,
           MARKET_X2, GROUND_Y, MARKET_Z2, STONE_BRICK)
    b.fill(MARKET_X1, BUILD_Y, MARKET_Z1,
           MARKET_X2, BUILD_Y, MARKET_Z2, AIR)  # 清空路面上方

    # 路面铺石砖半砖(更平整)
    for x in range(MARKET_X1, MARKET_X2 + 1):
        for z in range(MARKET_Z1 + 1, MARKET_Z2):  # 路中间
            if random.random() < 0.3:
                b.setblock(x, BUILD_Y, z, STONE_BRICK_SLAB)

    # 摊位: 沿路南侧(Z=107)每隔6~8格一个
    stall_ct = 0
    x = MARKET_X1 + 2
    while x < MARKET_X2 - 4:
        _build_stall(b, x, MARKET_Z2)
        stall_ct += 1
        x += random.randint(6, 9)

    # 北侧(Z=104)也放几个
    x = MARKET_X1 + 5
    while x < MARKET_X2 - 4:
        if random.random() < 0.5:
            _build_stall(b, x, MARKET_Z1, facing_south=False)
            stall_ct += 1
        x += random.randint(7, 10)

    print(f"    商业街完成, 摊位 {stall_ct} 个")


def _build_stall(b, x, z, facing_south=True):
    """摊位: 云杉栅栏框架(3x2x2) + 顶棚 + 旗帜幌子"""
    # 四根柱子
    dz_offset = 1 if facing_south else -1

    for dx in [0, 2]:
        b.setblock(x + dx, BUILD_Y, z, SPRUCE_FENCE)
        b.setblock(x + dx, BUILD_Y + 1, z, SPRUCE_FENCE)
        b.setblock(x + dx, BUILD_Y, z + dz_offset, SPRUCE_FENCE)
        b.setblock(x + dx, BUILD_Y + 1, z + dz_offset, SPRUCE_FENCE)

    # 顶棚: 云杉半砖
    for dx in range(3):
        b.setblock(x + dx, BUILD_Y + 2, z, SPRUCE_SLAB)
        b.setblock(x + dx, BUILD_Y + 2, z + dz_offset, SPRUCE_SLAB)

    # 柜台: 楼梯做展台
    facing = "north" if facing_south else "south"
    for dx in range(3):
        b.setblock(x + dx, BUILD_Y, z + dz_offset,
                   f"{SPRUCE_STAIRS}[facing={facing},half=bottom]")

    # 旗帜幌子(挂在柱子上) - 用红色羊毛块代替
    banner_dz = 0
    b.setblock(x + 1, BUILD_Y + 2, z + banner_dz, "minecraft:red_wool")


# ══════════════════════════════════════════════════════════════
#  5. 民居 (核心!)
# ══════════════════════════════════════════════════════════════

def build_houses(b):
    """5栋白墙灰瓦二层小楼, 江南典型粉墙黛瓦"""
    print("  [5/7] 民居...")

    for i, hx in enumerate(HOUSE_X_STARTS):
        # 每栋略有变化
        depth = HOUSE_DEPTH + random.choice([-1, 0, 0, 1])
        width = HOUSE_WIDTH + random.choice([-1, 0, 0])
        _build_one_house(b, hx, HOUSE_Z_FRONT, width, depth, i)
        print(f"    民居 {i+1} @ X={hx}, {width}x{depth}")


def _build_one_house(b, x_start, z_start, width, depth, index):
    """
    单栋民居外壳:
      台基1格 → 一层4格 → 二层4格 → 屋顶(硬山顶)
      面向北(运河方向), 只做外壳(正面+侧面), 背面简化
    """
    x1 = x_start
    x2 = x_start + width - 1
    z1 = z_start           # 北面(正面, 朝运河)
    z2 = z_start + depth - 1  # 南面(背面)

    y_base = BUILD_Y       # 台基顶面
    y_floor1 = y_base + 1  # 一层地面
    y_ceil1 = y_base + 4   # 一层顶/二层地面
    y_ceil2 = y_base + 8   # 二层顶
    y_ridge = y_base + 11  # 屋脊

    # ── 台基 (1格高石砖) ──
    b.fill(x1, y_base, z1, x2, y_base, z2, STONE_BRICK)

    # ── 一层 (4格高) ──
    _build_floor_walls(b, x1, x2, z1, z2, y_floor1, y_ceil1, is_ground=True)

    # ── 二层 (4格高) ──
    _build_floor_walls(b, x1, x2, z1, z2, y_ceil1, y_ceil2, is_ground=False)

    # ── 二层阳台 (正面挑出) ──
    _build_balcony(b, x1, x2, z1, y_ceil1)

    # ── 屋顶: 硬山顶 ──
    _build_gable_roof(b, x1, x2, z1, z2, y_ceil2, index)

    # ── 正面大门(一层中间) ──
    mid_x = (x1 + x2) // 2
    b.setblock(mid_x, y_floor1, z1, AIR)
    b.setblock(mid_x, y_floor1 + 1, z1, AIR)
    # 门框: 深色木
    b.setblock(mid_x, y_floor1 + 2, z1, DARK_OAK_PLANKS)
    # 门槛石
    b.setblock(mid_x, y_base, z1, STONE_BRICK)


def _build_floor_walls(b, x1, x2, z1, z2, y_bottom, y_top, is_ground):
    """一层或二层的墙体: 云杉框架 + 白色混凝土 + 窗"""
    height = y_top - y_bottom

    # 四角柱(云杉原木)
    for x in [x1, x2]:
        for z in [z1, z2]:
            for dy in range(height):
                b.setblock(x, y_bottom + dy, z, SPRUCE_LOG)

    # 正面中间柱(每3~4格一根)
    mid_pillars_x = []
    step = 3 if (x2 - x1) <= 8 else 4
    px = x1 + step
    while px < x2:
        mid_pillars_x.append(px)
        for dy in range(height):
            b.setblock(px, y_bottom + dy, z1, SPRUCE_LOG)
        px += step

    # 侧面(东西)中间柱
    mid_z = (z1 + z2) // 2
    for x_side in [x1, x2]:
        for dy in range(height):
            b.setblock(x_side, y_bottom + dy, mid_z, SPRUCE_LOG)

    # ── 正面墙 (Z=z1) ──
    for x in range(x1 + 1, x2):
        if x in mid_pillars_x:
            continue
        for dy in range(height):
            y = y_bottom + dy
            b.setblock(x, y, z1, WHITE_CONCRETE)

    # 正面窗: 每个柱间隔放窗(活板门模拟)
    # 窗在 y_bottom+1 和 y_bottom+2 高度
    win_y1 = y_bottom + 1
    win_y2 = y_bottom + 2
    for x in range(x1 + 1, x2):
        if x in mid_pillars_x:
            continue
        # 每隔一格做窗
        rel = x - x1
        if rel % 2 == 0:
            b.setblock(x, win_y1, z1,
                       f"{SPRUCE_TRAPDOOR}[facing=south,half=bottom,open=true]")
            b.setblock(x, win_y2, z1,
                       f"{SPRUCE_TRAPDOOR}[facing=south,half=top,open=true]")

    # ── 侧面墙 (X=x1, X=x2) ──
    for z in range(z1 + 1, z2):
        if z == mid_z:
            continue
        for dy in range(height):
            b.setblock(x1, y_bottom + dy, z, WHITE_CONCRETE)
            b.setblock(x2, y_bottom + dy, z, WHITE_CONCRETE)

    # 侧面窗
    for z in range(z1 + 2, z2 - 1, 3):
        b.setblock(x1, win_y1, z,
                   f"{SPRUCE_TRAPDOOR}[facing=east,half=bottom,open=true]")
        b.setblock(x1, win_y2, z,
                   f"{SPRUCE_TRAPDOOR}[facing=east,half=top,open=true]")
        b.setblock(x2, win_y1, z,
                   f"{SPRUCE_TRAPDOOR}[facing=west,half=bottom,open=true]")
        b.setblock(x2, win_y2, z,
                   f"{SPRUCE_TRAPDOOR}[facing=west,half=top,open=true]")

    # ── 背面墙 (Z=z2) 简化: 全白混凝土 ──
    for x in range(x1 + 1, x2):
        for dy in range(height):
            b.setblock(x, y_bottom + dy, z2, WHITE_CONCRETE)

    # ── 楼板/天花 ──
    # 顶部横梁
    for x in range(x1, x2 + 1):
        b.setblock(x, y_top - 1, z1, SPRUCE_LOG)
        b.setblock(x, y_top - 1, z2, SPRUCE_LOG)


def _build_balcony(b, x1, x2, z_front, y_floor):
    """二层正面挑出阳台: 栅栏栏杆, 挑出1格"""
    balcony_z = z_front - 1  # 挑出到运河方向

    # 阳台地板(云杉半砖)
    for x in range(x1, x2 + 1):
        b.setblock(x, y_floor, balcony_z, SPRUCE_SLAB)

    # 栏杆: 两端和前沿
    b.setblock(x1, y_floor + 1, balcony_z, SPRUCE_FENCE)
    b.setblock(x2, y_floor + 1, balcony_z, SPRUCE_FENCE)
    for x in range(x1, x2 + 1):
        b.setblock(x, y_floor + 1, balcony_z, SPRUCE_FENCE)

    # 阳台下方托架(斜撑): 活板门
    for x in [x1 + 1, x2 - 1]:
        b.setblock(x, y_floor - 1, balcony_z,
                   f"{SPRUCE_TRAPDOOR}[facing=south,half=top,open=true]")


def _build_gable_roof(b, x1, x2, z1, z2, y_base, index):
    """
    硬山顶: 沿X方向的山墙在两端, 屋脊平行于X轴
    屋檐外挑2格
    灰瓦: stone_brick_stairs
    """
    # 屋脊在 Z 方向的中心
    z_mid = (z1 + z2) // 2
    half_span = z_mid - z1  # 从屋脊到墙边的格数

    # 屋檐外挑: X方向各挑出1格, Z方向各挑出2格
    overhang_x = 1
    overhang_z = 2

    roof_x1 = x1 - overhang_x
    roof_x2 = x2 + overhang_x

    # 逐层向上收，形成人字形屋顶
    for layer in range(half_span + 2):
        y = y_base + layer
        z_north = z_mid - (half_span + overhang_z - layer)
        z_south = z_mid + (half_span + overhang_z - layer)

        if z_north >= z_south:
            # 屋脊: 用石砖半砖
            for x in range(roof_x1, roof_x2 + 1):
                b.setblock(x, y, z_mid, STONE_BRICK_SLAB)
            break

        # 北坡: 楼梯朝北
        for x in range(roof_x1, roof_x2 + 1):
            b.setblock(x, y, z_north,
                       f"{STONE_BRICK_STAIRS}[facing=south,half=bottom]")

        # 南坡: 楼梯朝南
        for x in range(roof_x1, roof_x2 + 1):
            b.setblock(x, y, z_south,
                       f"{STONE_BRICK_STAIRS}[facing=north,half=bottom]")

        # 中间填充(防漏光)
        if z_south - z_north > 1:
            for x in range(roof_x1, roof_x2 + 1):
                for z in range(z_north + 1, z_south):
                    b.setblock(x, y, z, STONE_BRICK)

    # ── 山墙 (东西两端的三角形墙面) ──
    for x_gable in [x1, x2]:
        for layer in range(half_span + 1):
            y = y_base + layer
            z_n = z_mid - (half_span - layer)
            z_s = z_mid + (half_span - layer)
            for z in range(z_n, z_s + 1):
                b.setblock(x_gable, y, z, WHITE_CONCRETE)
            # 顶部横梁
            b.setblock(x_gable, y, z_n, SPRUCE_LOG)
            b.setblock(x_gable, y, z_s, SPRUCE_LOG)

    # ── 屋檐下挂灯笼(随机1~2个) ──
    lantern_positions = [x1 + 1, x2 - 1, (x1 + x2) // 2]
    random.shuffle(lantern_positions)
    for lx in lantern_positions[:random.randint(1, 2)]:
        b.setblock(lx, y_base - 1, z1 - overhang_z, HANGING_LANTERN)


# ══════════════════════════════════════════════════════════════
#  6. 码头
# ══════════════════════════════════════════════════════════════

def build_dock(b):
    """X=55~62, Z=94~97, 去皮云杉原木甲板 + 橡木栅栏支撑柱"""
    print("  [6/7] 码头...")

    dock_y = BUILD_Y  # 甲板高度

    # 甲板: 去皮云杉原木
    for x in range(DOCK_X1, DOCK_X2 + 1):
        for z in range(DOCK_Z1, DOCK_Z2 + 1):
            b.setblock(x, dock_y, z, SPRUCE_STRIPPED)

    # 支撑柱: 角上和中间, 入水
    pillar_positions = [
        (DOCK_X1, DOCK_Z2), (DOCK_X2, DOCK_Z2),
        (DOCK_X1, DOCK_Z1), (DOCK_X2, DOCK_Z1),
        ((DOCK_X1 + DOCK_X2) // 2, DOCK_Z2),
        ((DOCK_X1 + DOCK_X2) // 2, DOCK_Z1),
    ]

    for px, pz in pillar_positions:
        for dy in range(4):  # 从水底到甲板下
            b.setblock(px, dock_y - 1 - dy, pz, OAK_FENCE)

    # 栏杆: 码头外沿(Z=94, 靠运河侧 Z=97)
    for x in range(DOCK_X1, DOCK_X2 + 1):
        b.setblock(x, dock_y + 1, DOCK_Z2, OAK_FENCE)

    # 灯笼: 2个
    b.setblock(DOCK_X1 + 1, dock_y + 1, DOCK_Z2, SPRUCE_FENCE)
    b.setblock(DOCK_X1 + 1, dock_y + 2, DOCK_Z2, LANTERN)
    b.setblock(DOCK_X2 - 1, dock_y + 1, DOCK_Z2, SPRUCE_FENCE)
    b.setblock(DOCK_X2 - 1, dock_y + 2, DOCK_Z2, LANTERN)

    # 系船桩(栅栏门模拟绳桩)
    b.setblock(DOCK_X1 + 3, dock_y + 1, DOCK_Z2,
               f"{SPRUCE_FENCE_GATE}[facing=south,open=false]")

    print("    码头完成")


# ══════════════════════════════════════════════════════════════
#  7. 垂柳
# ══════════════════════════════════════════════════════════════

def build_willows(b):
    """沿运河两岸种4~6棵垂柳"""
    print("  [7/7] 垂柳...")

    willow_positions = [
        # 北岸 (Z=93~94)
        (28, 93), (50, 93), (70, 94), (90, 93),
        # 南岸 (Z=103~104)
        (38, 104), (82, 104),
    ]

    for wx, wz in willow_positions:
        _build_willow(b, wx, wz)
        print(f"    垂柳 @ ({wx}, {wz})")


def _build_willow(b, wx, wz):
    """单棵垂柳: oak_log树干 + oak_leaves扁冠 + vine垂3~5格"""
    trunk_h = random.randint(5, 7)

    # 树干
    for dy in range(trunk_h):
        b.setblock(wx, BUILD_Y + dy, wz, OAK_LOG)

    # 扁平宽冠
    crown_top = BUILD_Y + trunk_h
    h_radius = random.randint(3, 4)
    v_layers = [
        (0,  h_radius),
        (1,  h_radius - 1),
        (-1, h_radius - 1),
    ]

    vine_candidates = []

    for dy_off, r in v_layers:
        y = crown_top + dy_off
        for dx in range(-r, r + 1):
            for dz in range(-r, r + 1):
                dist_sq = dx * dx + dz * dz
                if dist_sq <= r * r:
                    if dist_sq > r * r * 0.5 and random.random() < 0.25:
                        continue
                    lx, lz = wx + dx, wz + dz
                    b.setblock(lx, y, lz, OAK_LEAVES)

                    if dy_off <= 0 and dist_sq > (r - 1) ** 2:
                        vine_candidates.append((lx, y, lz))

    # 垂藤
    vine_candidates = list(set(vine_candidates))
    random.shuffle(vine_candidates)
    vine_count = min(len(vine_candidates), random.randint(10, 18))

    for vx, vy, vz in vine_candidates[:vine_count]:
        facing = _get_vine_facing(vx, vy, vz, wx, wz)
        vine_len = random.randint(3, 5)
        for vdy in range(vine_len):
            b.setblock(vx, vy - 1 - vdy, vz, facing)


def _get_vine_facing(vx, vy, vz, trunk_x, trunk_z):
    """根据位置相对树干方向生成 vine 方块字符串"""
    dx = vx - trunk_x
    dz = vz - trunk_z
    faces = []
    if dx > 0:
        faces.append("east=true")
    elif dx < 0:
        faces.append("west=true")
    if dz > 0:
        faces.append("south=true")
    elif dz < 0:
        faces.append("north=true")
    if not faces:
        faces.append("south=true")
    return f"minecraft:vine[{','.join(faces)}]"


# ══════════════════════════════════════════════════════════════
#  附加: 后巷 + 第二排零星民居 + 渐隐
# ══════════════════════════════════════════════════════════════

def build_back_alley(b):
    """Z=119~121 后巷: 碎石路, 零散装饰"""
    print("  [附加] 后巷...")

    # 后巷路面
    for x in range(30, 90):
        for z in range(119, 122):
            b.setblock(x, GROUND_Y, z, "minecraft:gravel")
            # 偶尔石砖
            if random.random() < 0.2:
                b.setblock(x, GROUND_Y, z, STONE_BRICK)

    # 零散物件: 箱子/堆叠物(用木板台阶模拟)
    for x in range(35, 85, 7):
        if random.random() < 0.5:
            b.setblock(x, BUILD_Y, 120, SPRUCE_PLANKS)
            if random.random() < 0.4:
                b.setblock(x, BUILD_Y + 1, 120, SPRUCE_SLAB)


def build_second_row(b):
    """Z=125~135 第二排零星民居(2~3栋, 更小更简朴)"""
    print("  [附加] 第二排民居...")

    # 2~3栋小屋
    positions = [40, 60, 78]
    for i, hx in enumerate(positions):
        if i == 2 and random.random() < 0.4:
            continue  # 第三栋有概率不建
        _build_small_house(b, hx, 125)
        print(f"    小屋 @ X={hx}")


def _build_small_house(b, x_start, z_start):
    """简朴小屋: 7x6, 单层+阁楼, 同样白墙灰瓦"""
    w, d = 7, 6
    x1, x2 = x_start, x_start + w - 1
    z1, z2 = z_start, z_start + d - 1

    y0 = BUILD_Y

    # 台基
    b.fill(x1, y0, z1, x2, y0, z2, STONE_BRICK)

    # 墙体(4格高)
    wall_h = 4
    for dy in range(1, wall_h + 1):
        y = y0 + dy
        # 四面墙
        for x in range(x1, x2 + 1):
            b.setblock(x, y, z1, WHITE_CONCRETE)
            b.setblock(x, y, z2, WHITE_CONCRETE)
        for z in range(z1, z2 + 1):
            b.setblock(x1, y, z, WHITE_CONCRETE)
            b.setblock(x2, y, z, WHITE_CONCRETE)

    # 角柱
    for x in [x1, x2]:
        for z in [z1, z2]:
            for dy in range(1, wall_h + 1):
                b.setblock(x, y0 + dy, z, SPRUCE_LOG)

    # 简单窗
    mid_x = (x1 + x2) // 2
    b.setblock(mid_x, y0 + 2, z1,
               f"{SPRUCE_TRAPDOOR}[facing=south,half=bottom,open=true]")
    b.setblock(mid_x, y0 + 3, z1,
               f"{SPRUCE_TRAPDOOR}[facing=south,half=top,open=true]")

    # 门
    b.setblock(mid_x - 1, y0 + 1, z1, AIR)
    b.setblock(mid_x - 1, y0 + 2, z1, AIR)

    # 屋顶(简单硬山)
    z_mid = (z1 + z2) // 2
    for layer in range(d // 2 + 2):
        y = y0 + wall_h + 1 + layer
        z_n = z_mid - (d // 2 + 1 - layer)
        z_s = z_mid + (d // 2 + 1 - layer)
        if z_n >= z_s:
            for x in range(x1 - 1, x2 + 2):
                b.setblock(x, y, z_mid, STONE_BRICK_SLAB)
            break
        for x in range(x1 - 1, x2 + 2):
            b.setblock(x, y, z_n,
                       f"{STONE_BRICK_STAIRS}[facing=south,half=bottom]")
            b.setblock(x, y, z_s,
                       f"{STONE_BRICK_STAIRS}[facing=north,half=bottom]")
        if z_s - z_n > 1:
            for x in range(x1 - 1, x2 + 2):
                for z in range(z_n + 1, z_s):
                    b.setblock(x, y, z, STONE_BRICK)

    # 山墙填充
    for x_gable in [x1, x2]:
        for layer in range(d // 2):
            y = y0 + wall_h + 1 + layer
            z_n = z_mid - (d // 2 - 1 - layer)
            z_s = z_mid + (d // 2 - 1 - layer)
            if z_n > z_s:
                break
            for z in range(z_n, z_s + 1):
                b.setblock(x_gable, y, z, WHITE_CONCRETE)


def build_fade_zone(b):
    """Z=136~140 渐隐到空地: 稀疏草/土/碎石过渡"""
    print("  [附加] 渐隐区...")

    for x in range(20, 100):
        for z in range(136, 141):
            r = random.random()
            fade = (z - 136) / 4.0  # 0~1, 越远越荒
            if r < 0.3 - fade * 0.2:
                b.setblock(x, GROUND_Y, z, "minecraft:gravel")
            elif r < 0.5 - fade * 0.2:
                b.setblock(x, GROUND_Y, z, "minecraft:coarse_dirt")
            # 偶尔一簇草
            if random.random() < 0.05:
                b.setblock(x, BUILD_Y, z, "minecraft:short_grass")


# ══════════════════════════════════════════════════════════════
#  主入口
# ══════════════════════════════════════════════════════════════

def build_south_town(b):
    """南面江南水乡街巷 — 总控"""
    print("=== 南面江南水乡 ===")
    random.seed(300)

    # 先清空整个区域上方(移除 landscape_v3 旧结构)
    print("  [准备] 清空旧结构...")
    b.fill(15, BUILD_Y, 92, 105, BUILD_Y + 20, 140, AIR)

    build_canal(b)
    build_bridges(b)
    build_promenades(b)
    build_market_street(b)
    build_houses(b)
    build_dock(b)
    build_willows(b)
    build_back_alley(b)
    build_second_row(b)
    build_fade_zone(b)

    b.register_bbox("south_town", 15, GROUND_Y - 5, 92,
                    105, BUILD_Y + 20, 140)
    print("=== 南面江南水乡完成 ===")


if __name__ == "__main__":
    with MinecraftBuilder() as b:
        # 先确保区域有地面
        b.fill(0, GROUND_Y, 92, 120, GROUND_Y, 140, PALETTE['grass'])
        b.fill(0, -62, 92, 120, -62, 140, PALETTE['dirt'])
        b.fill(0, -63, 92, 120, -63, 140, PALETTE['dirt'])
        build_south_town(b)
        print(f"Done! {b.cmd_count} commands")
