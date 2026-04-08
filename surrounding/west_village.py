"""西面田园村落 — 园林西墙外的江南农家风光

布局 (X 从远到近):
  X=-60~-45  矮丘群
  X=-55~-30  农田区 (水稻田 + 田埂)
  X=-25      水渠 (2格宽)
  X=-22~-14  小村落 (2栋民居)
  X=-5~-2    果树/柳树
"""

import sys; sys.path.insert(0, '/Users/lambertlin/minecraft-server/scripts')
from builder import MinecraftBuilder, filled_circle_points
from blocks import PALETTE, GROUND_Y, BUILD_Y
import random
import math


# ── 常量 ──

FARMLAND = "minecraft:farmland[moisture=7]"
WHEAT = "minecraft:wheat[age=7]"
WATER = "minecraft:water"
DIRT_PATH = "minecraft:dirt_path"
STONE_BRICK_SLAB = "minecraft:stone_brick_slab"
STONE_BRICKS = "minecraft:stone_bricks"
STONE_BRICK_STAIRS = "minecraft:stone_brick_stairs"
WHITE_CONCRETE = "minecraft:white_concrete"
SPRUCE_PLANKS = "minecraft:spruce_planks"
SPRUCE_LOG = "minecraft:spruce_log"
SPRUCE_TRAPDOOR = "minecraft:spruce_trapdoor"
SPRUCE_DOOR = "minecraft:spruce_door"
SPRUCE_SLAB = "minecraft:spruce_slab"
COBBLESTONE_WALL = "minecraft:cobblestone_wall"
OAK_LOG = "minecraft:oak_log"
OAK_LEAVES = "minecraft:oak_leaves"
CHERRY_LOG = "minecraft:cherry_log"
CHERRY_LEAVES = "minecraft:cherry_leaves"
VINE_SOUTH = "minecraft:vine[south=true]"
VINE_NORTH = "minecraft:vine[north=true]"
VINE_EAST = "minecraft:vine[east=true]"
VINE_WEST = "minecraft:vine[west=true]"
GRASS_BLOCK = "minecraft:grass_block"
DIRT = "minecraft:dirt"
AIR = "minecraft:air"
LANTERN = "minecraft:lantern[hanging=true]"
FLOWER_POT = "minecraft:potted_cornflower"


# ══════════════════════════════════════════
# 1. 农田区
# ══════════════════════════════════════════

def build_farmland(b):
    """X:-55~-30, Z:20~70 — 水田分区，每8格Z一条水渠"""
    print("  [农田区]")
    x1, x2 = -55, -30
    z1, z2 = 20, 70

    # 整体铺耕地层（先铺 dirt 再转 farmland，因为 farmland 需要下方支撑）
    b.fill(x1, GROUND_Y, z1, x2, GROUND_Y, z2, DIRT)
    b.fill(x1, GROUND_Y, z1, x2, GROUND_Y, z2, FARMLAND)

    # 种满小麦
    b.fill(x1, BUILD_Y, z1, x2, BUILD_Y, z2, WHEAT)

    # 每8格Z方向一条2格宽水渠 + 田埂
    z = z1
    while z <= z2:
        # 水渠: 2格宽, 挖1格深
        b.fill(x1, GROUND_Y, z, x2, GROUND_Y, z + 1, WATER)
        # 清掉水渠上方的小麦
        b.fill(x1, BUILD_Y, z, x2, BUILD_Y, z + 1, AIR)

        # 田埂: 水渠两侧各1格 dirt_path
        if z - 1 >= z1:
            b.fill(x1, GROUND_Y, z - 1, x2, GROUND_Y, z - 1, DIRT_PATH)
            b.fill(x1, BUILD_Y, z - 1, x2, BUILD_Y, z - 1, AIR)
        if z + 2 <= z2:
            b.fill(x1, GROUND_Y, z + 2, x2, GROUND_Y, z + 2, DIRT_PATH)
            b.fill(x1, BUILD_Y, z + 2, x2, BUILD_Y, z + 2, AIR)

        z += 8

    # X方向田埂（东西两端边界）
    b.fill(x1, GROUND_Y, z1, x1, GROUND_Y, z2, DIRT_PATH)
    b.fill(x1, BUILD_Y, z1, x1, BUILD_Y, z2, AIR)
    b.fill(x2, GROUND_Y, z1, x2, GROUND_Y, z2, DIRT_PATH)
    b.fill(x2, BUILD_Y, z1, x2, BUILD_Y, z2, AIR)


# ══════════════════════════════════════════
# 2. 水渠
# ══════════════════════════════════════════

def build_canal(b):
    """X=-25, Z:15~75, 2格宽, 1格深, 两岸 stone_brick_slab"""
    print("  [水渠]")
    # 挖渠: 2格宽(X=-25, -24), 1格深
    b.fill(-25, GROUND_Y, 15, -24, GROUND_Y, 75, WATER)
    # 清除上方可能的方块
    b.fill(-25, BUILD_Y, 15, -24, BUILD_Y, 75, AIR)

    # 两岸石砖半砖（放在地面层，作为护岸）
    # 西岸 X=-26
    b.fill(-26, GROUND_Y, 15, -26, GROUND_Y, 75, STONE_BRICK_SLAB)
    # 东岸 X=-23
    b.fill(-23, GROUND_Y, 15, -23, GROUND_Y, 75, STONE_BRICK_SLAB)


# ══════════════════════════════════════════
# 3. 小村落 — 2栋江南民居
# ══════════════════════════════════════════

def _build_house(b, x1, z1, x2, z2, door_z, label="房屋"):
    """建造单栋江南农家民居 — 白墙灰瓦硬山顶

    参数:
        x1, z1, x2, z2: 地基边界
        door_z: 门的Z坐标（门开在东面 X=x2 侧）
    """
    print(f"  [{label}]")
    width_x = x2 - x1 + 1   # X方向宽度
    width_z = z2 - z1 + 1   # Z方向长度
    wall_h = 4               # 墙高（含地基到屋檐）
    y_floor = BUILD_Y        # 地板层
    y_roof_base = y_floor + wall_h  # 屋顶起始

    # ── 地基台基 ──
    b.fill(x1, GROUND_Y, z1, x2, GROUND_Y, z2, STONE_BRICKS)
    b.fill(x1, y_floor, z1, x2, y_floor, z2, SPRUCE_PLANKS)

    # ── 四面墙体: 云杉木框架 + 白色混凝土填充 ──
    for y in range(y_floor + 1, y_floor + wall_h + 1):
        # 四面外墙框
        b.fill(x1, y, z1, x2, y, z1, WHITE_CONCRETE)  # 南墙
        b.fill(x1, y, z2, x2, y, z2, WHITE_CONCRETE)  # 北墙
        b.fill(x1, y, z1, x1, y, z2, WHITE_CONCRETE)  # 西墙
        b.fill(x2, y, z1, x2, y, z2, WHITE_CONCRETE)  # 东墙

    # 框架柱（四角 + 中间）用云杉原木
    corners = [
        (x1, z1), (x1, z2), (x2, z1), (x2, z2),
        (x1, (z1 + z2) // 2), (x2, (z1 + z2) // 2),
    ]
    for cx, cz in corners:
        for y in range(y_floor + 1, y_floor + wall_h + 1):
            b.setblock(cx, y, cz, SPRUCE_LOG)

    # 内部清空
    b.fill(x1 + 1, y_floor + 1, z1 + 1, x2 - 1, y_floor + wall_h, z2 - 1, AIR)

    # ── 窗户: 活板门 ──
    win_y = y_floor + 2  # 窗户在第2层
    # 南墙窗
    for wx in range(x1 + 2, x2 - 1, 3):
        if wx <= x2 - 2:
            b.setblock(wx, win_y, z1, f"minecraft:spruce_trapdoor[facing=south,open=true]")
    # 北墙窗
    for wx in range(x1 + 2, x2 - 1, 3):
        if wx <= x2 - 2:
            b.setblock(wx, win_y, z2, f"minecraft:spruce_trapdoor[facing=north,open=true]")
    # 西墙窗
    for wz in range(z1 + 2, z2 - 1, 3):
        if wz <= z2 - 2:
            b.setblock(x1, win_y, wz, f"minecraft:spruce_trapdoor[facing=west,open=true]")

    # ── 门（东面） ──
    b.setblock(x2, y_floor + 1, door_z, AIR)
    b.setblock(x2, y_floor + 2, door_z, AIR)
    b.setblock(x2, y_floor + 1, door_z, f"minecraft:spruce_door[facing=east,half=lower]")
    b.setblock(x2, y_floor + 2, door_z, f"minecraft:spruce_door[facing=east,half=upper]")

    # ── 屋顶: 硬山顶 (沿X方向起脊, Z方向对称坡) ──
    # 脊线在 Z 中间
    mid_z = (z1 + z2) // 2
    half_span = mid_z - z1  # 从边到脊的距离

    for layer in range(half_span + 1):
        y = y_roof_base + layer
        zs = z1 + layer      # 南侧坡面Z
        zn = z2 - layer      # 北侧坡面Z

        if zs > zn:
            break

        if zs == zn:
            # 脊顶 — 用石砖方块
            b.fill(x1 - 1, y, zs, x2 + 1, y, zs, STONE_BRICKS)
        else:
            # 南坡: 朝南的阶梯
            b.fill(x1 - 1, y, zs, x2 + 1, y, zs,
                   f"minecraft:stone_brick_stairs[facing=south]")
            # 北坡: 朝北的阶梯
            b.fill(x1 - 1, y, zn, x2 + 1, y, zn,
                   f"minecraft:stone_brick_stairs[facing=north]")

        # 两坡之间填充石砖（封实屋顶内部）
        if zs + 1 <= zn - 1:
            b.fill(x1 - 1, y, zs + 1, x2 + 1, y, zn - 1, STONE_BRICKS)

    # 山墙三角（东西两端封山）— 白色混凝土填充三角区
    for layer in range(half_span + 1):
        y = y_roof_base + layer
        zs = z1 + layer
        zn = z2 - layer
        if zs > zn:
            break
        # 西山墙
        b.fill(x1, y, zs, x1, y, zn, WHITE_CONCRETE)
        # 东山墙
        b.fill(x2, y, zs, x2, y, zn, WHITE_CONCRETE)

    # ── 门前台阶 ──
    b.setblock(x2 + 1, y_floor, door_z, f"minecraft:stone_brick_stairs[facing=east]")

    # ── 室内灯笼 ──
    b.setblock((x1 + x2) // 2, y_floor + wall_h, (z1 + z2) // 2, LANTERN)


def build_village(b):
    """建造2栋民居"""
    print("  [小村落]")
    # 房屋1: X:-22~-14, Z:35~42 (8x8)
    _build_house(b, -22, 35, -14, 42, door_z=38, label="房屋1")

    # 房屋2: X:-22~-14, Z:50~57 (8x8, 略同)
    _build_house(b, -22, 50, -14, 57, door_z=53, label="房屋2")

    # ── 房屋之间铺小路 ──
    for z in range(43, 50):
        b.setblock(-18, GROUND_Y, z, DIRT_PATH)
        b.setblock(-17, GROUND_Y, z, DIRT_PATH)

    # ── 房前通往水渠的小路 ──
    for x in range(-24, -13):
        b.setblock(x, GROUND_Y, 38, DIRT_PATH)
        b.setblock(x, GROUND_Y, 53, DIRT_PATH)


# ══════════════════════════════════════════
# 4. 矮丘
# ══════════════════════════════════════════

def build_hills(b):
    """X:-60~-45, Z:10~80 — 3~5个矮丘, 高5~10格, 草覆盖"""
    print("  [矮丘]")
    rng = random.Random(501)

    hill_centers = [
        (-55, 25, 7),   # (cx, cz, max_height)
        (-50, 45, 9),
        (-58, 60, 6),
        (-48, 70, 8),
        (-53, 15, 5),
    ]

    for cx, cz, max_h in hill_centers:
        radius = max_h + rng.randint(2, 4)  # 底面半径略大于高度
        _build_single_hill(b, cx, cz, max_h, radius, rng)

        # 丘顶种 1~2 棵树
        tree_count = rng.randint(1, 2)
        for _ in range(tree_count):
            tx = cx + rng.randint(-2, 2)
            tz = cz + rng.randint(-2, 2)
            ty = GROUND_Y + max_h
            _place_oak_tree(b, tx, ty + 1, tz, rng)


def _build_single_hill(b, cx, cz, max_h, radius, rng):
    """堆一个自然矮丘 — 从底层到顶层逐层缩小的圆"""
    for layer in range(max_h + 1):
        y = GROUND_Y + layer
        # 每层半径递减，加随机扰动
        layer_radius = radius * (1.0 - layer / (max_h + 1)) + rng.uniform(-0.5, 0.5)
        layer_radius = max(1, int(layer_radius))

        for dx in range(-layer_radius, layer_radius + 1):
            for dz in range(-layer_radius, layer_radius + 1):
                dist = math.sqrt(dx * dx + dz * dz)
                if dist <= layer_radius + rng.uniform(-0.3, 0.3):
                    x = cx + dx
                    z = cz + dz
                    # 边界检查
                    if -60 <= x <= -45 and 10 <= z <= 80:
                        if layer == max_h or (dist > layer_radius - 1):
                            b.setblock(x, y, z, GRASS_BLOCK)
                        else:
                            b.setblock(x, y, z, DIRT)

    # 顶层覆盖草
    for dx in range(-2, 3):
        for dz in range(-2, 3):
            x = cx + dx
            z = cz + dz
            if -60 <= x <= -45 and 10 <= z <= 80:
                b.setblock(x, GROUND_Y + max_h, z, GRASS_BLOCK)


def _place_oak_tree(b, x, y, z, rng):
    """放一棵简单橡树"""
    trunk_h = rng.randint(4, 6)
    # 树干
    for dy in range(trunk_h):
        b.setblock(x, y + dy, z, OAK_LOG)
    # 树冠 — 简单球形
    crown_y = y + trunk_h - 1
    crown_r = 2
    for dx in range(-crown_r, crown_r + 1):
        for dz in range(-crown_r, crown_r + 1):
            for dy in range(-1, crown_r + 1):
                dist = math.sqrt(dx * dx + dy * dy + dz * dz)
                if dist <= crown_r + 0.5 and rng.random() > 0.15:
                    bx, bz, by = x + dx, z + dz, crown_y + dy
                    b.setblock(bx, by, bz, OAK_LEAVES)


# ══════════════════════════════════════════
# 5. 果树和柳树
# ══════════════════════════════════════════

def build_trees_near_wall(b):
    """X:-5~-2, 种 4~5 棵混合树"""
    print("  [果树/柳树]")
    rng = random.Random(502)

    tree_specs = [
        (-4, 20, "oak"),      # 果树
        (-3, 32, "cherry"),   # 梅花
        (-4, 45, "willow"),   # 垂柳
        (-3, 58, "oak"),      # 果树
        (-4, 70, "cherry"),   # 梅花
    ]

    for tx, tz, kind in tree_specs:
        ty = BUILD_Y
        if kind == "oak":
            _place_fruit_tree(b, tx, ty, tz, rng)
        elif kind == "cherry":
            _place_cherry_tree(b, tx, ty, tz, rng)
        elif kind == "willow":
            _place_willow_tree(b, tx, ty, tz, rng)


def _place_fruit_tree(b, x, y, z, rng):
    """果树 — 橡树造型，矮胖"""
    trunk_h = rng.randint(3, 4)
    for dy in range(trunk_h):
        b.setblock(x, y + dy, z, OAK_LOG)
    crown_y = y + trunk_h - 1
    for dx in range(-2, 3):
        for dz in range(-2, 3):
            for dy in range(0, 3):
                dist = math.sqrt(dx * dx + dy * dy + dz * dz)
                if dist <= 2.5 and rng.random() > 0.1:
                    b.setblock(x + dx, crown_y + dy, z + dz, OAK_LEAVES)


def _place_cherry_tree(b, x, y, z, rng):
    """樱花/梅花树"""
    trunk_h = rng.randint(3, 5)
    for dy in range(trunk_h):
        b.setblock(x, y + dy, z, CHERRY_LOG)
    crown_y = y + trunk_h - 1
    for dx in range(-2, 3):
        for dz in range(-2, 3):
            for dy in range(0, 3):
                dist = math.sqrt(dx * dx + dy * dy + dz * dz)
                if dist <= 2.5 and rng.random() > 0.12:
                    b.setblock(x + dx, crown_y + dy, z + dz, CHERRY_LEAVES)


def _place_willow_tree(b, x, y, z, rng):
    """垂柳 — 橡树叶 + vine 下垂"""
    trunk_h = rng.randint(5, 7)
    for dy in range(trunk_h):
        b.setblock(x, y + dy, z, OAK_LOG)
    crown_y = y + trunk_h - 1
    # 树冠
    crown_r = 3
    for dx in range(-crown_r, crown_r + 1):
        for dz in range(-crown_r, crown_r + 1):
            for dy in range(0, 3):
                dist = math.sqrt(dx * dx + dy * dy + dz * dz)
                if dist <= crown_r + 0.3 and rng.random() > 0.15:
                    bx, bz, by = x + dx, z + dz, crown_y + dy
                    b.setblock(bx, by, bz, OAK_LEAVES)

    # 垂藤 — 从树冠边缘向下挂
    vine_faces = [
        (VINE_SOUTH, 0, 1),
        (VINE_NORTH, 0, -1),
        (VINE_EAST, 1, 0),
        (VINE_WEST, -1, 0),
    ]
    for dx in range(-crown_r, crown_r + 1):
        for dz in range(-crown_r, crown_r + 1):
            dist = math.sqrt(dx * dx + dz * dz)
            if crown_r - 1 <= dist <= crown_r + 0.5:
                # 从树冠底部向下挂藤
                vine_len = rng.randint(3, 6)
                # 选择朝外的面
                if abs(dx) >= abs(dz):
                    vine_block = VINE_EAST if dx > 0 else VINE_WEST
                else:
                    vine_block = VINE_SOUTH if dz > 0 else VINE_NORTH
                for vdy in range(vine_len):
                    b.setblock(x + dx, crown_y - 1 - vdy, z + dz, vine_block)


# ══════════════════════════════════════════
# 6. 小石桥
# ══════════════════════════════════════════

def build_stone_bridge(b):
    """跨水渠石桥 — X=-25, Z=45, 3格宽桥面, cobblestone_wall 栏杆"""
    print("  [小石桥]")
    # 桥面: 石砖半砖, 跨越 X=-26 到 X=-23 (覆盖水渠+两岸)
    # 桥宽3格: Z=44, 45, 46
    bridge_x1, bridge_x2 = -27, -22
    bridge_z1, bridge_z2 = 44, 46

    # 桥面（石砖半砖，top 型放在 BUILD_Y）
    for x in range(bridge_x1, bridge_x2 + 1):
        for z in range(bridge_z1, bridge_z2 + 1):
            b.setblock(x, BUILD_Y, z, f"minecraft:stone_brick_slab[type=bottom]")

    # 清除桥面上一格（确保通行）
    b.fill(bridge_x1, BUILD_Y + 1, bridge_z1, bridge_x2, BUILD_Y + 2, bridge_z2, AIR)

    # 栏杆（桥两侧）
    for x in range(bridge_x1, bridge_x2 + 1):
        b.setblock(x, BUILD_Y + 1, bridge_z1, COBBLESTONE_WALL)
        b.setblock(x, BUILD_Y + 1, bridge_z2, COBBLESTONE_WALL)

    # 桥两端柱子加高
    for z in [bridge_z1, bridge_z2]:
        b.setblock(bridge_x1, BUILD_Y + 2, z, f"minecraft:stone_brick_slab[type=bottom]")
        b.setblock(bridge_x2, BUILD_Y + 2, z, f"minecraft:stone_brick_slab[type=bottom]")


# ══════════════════════════════════════════
# 主函数
# ══════════════════════════════════════════

def build_west_village(b):
    print("=== 西面田园村落 ===")
    random.seed(500)

    # 按从远到近的顺序建造
    build_hills(b)          # 1. 远处矮丘
    build_farmland(b)       # 2. 农田区
    build_canal(b)          # 3. 水渠
    build_village(b)        # 4. 小村落
    build_stone_bridge(b)   # 5. 小石桥
    build_trees_near_wall(b)  # 6. 墙外果树/柳树

    print("=== 西面田园村落完成 ===")


if __name__ == "__main__":
    with MinecraftBuilder() as b:
        # 先铺地面
        b.fill(-60, -63, 0, -1, -63, 90, PALETTE['dirt'])
        b.fill(-60, -62, 0, -1, -62, 90, PALETTE['dirt'])
        b.fill(-60, GROUND_Y, 0, -1, GROUND_Y, 90, PALETTE['grass'])
        build_west_village(b)
        print(f"Done! {b.cmd_count} commands")
