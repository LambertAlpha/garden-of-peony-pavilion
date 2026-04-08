"""景观收尾 + 江南远景山水 — v3 重写

v2→v3 变更:
- 使用 config.py v3 坐标和范围 (GARDEN x_max=120, z_max=90)
- 大梅树: 2x2树干高6格，冠幅半径5格，树下落花
- 花丛: 每丛20~30朵，极坐标分布中心密边缘疏
- 垂杨: vine垂3~5格（核心特征强化）
- 断井: 3x3+中空+水底+苔藓覆盖
- 全园做旧覆盖新范围
- ★新增★ 江南远景山水: 北面青山、东西矮丘竹林、南面水边村落
"""

import sys; sys.path.insert(0, '/Users/lambertlin/minecraft-server/scripts')
from builder import MinecraftBuilder, filled_circle_points
from blocks import PALETTE, GROUND_Y, BUILD_Y
from config import (
    GARDEN, PLUM_TREE, FLOWER_CLUSTERS as CFG_FLOWER_CLUSTERS,
    WILLOWS as CFG_WILLOWS, WELLS as CFG_WELLS, POND, WALL,
)
import random
import math


# ── 常量 ──

# 园林边界
G = GARDEN  # x_min=0, x_max=120, z_min=0, z_max=90

# 池塘椭圆（从 config）
POND_ELLIPSE = {"cx": POND["cx"], "cz": POND["cz"],
                "rx": POND["rx"], "rz": POND["rz"]}

# 大梅树
PLUM_POS = (PLUM_TREE["x"], PLUM_TREE["z"])
PLUM_CLEAR_RADIUS = 6

# 花丛中心（从 config）
FLOWER_CENTERS = CFG_FLOWER_CLUSTERS

# 垂杨（从 config）
WILLOW_POS = CFG_WILLOWS

# 断井（从 config）
WELL_POS = CFG_WELLS

# 已有建筑占用区（v3 布局，安全距离 +3）
OCCUPIED_ZONES = [
    (70, 7, 86, 23),     # 牡丹亭
    (73, 25, 83, 33),    # 芍药阑
    (8, 27, 25, 43),     # 翠轩
    (47, 70, 63, 90),    # 入口区
    (37, 3, 73, 53),     # 太湖石+秋千+桥区域
]

# 花卉方块
FLOWERS_SINGLE = [
    "minecraft:red_tulip", "minecraft:pink_tulip",
    "minecraft:cornflower", "minecraft:azure_bluet",
]
FLOWERS_DOUBLE = ["minecraft:peony", "minecraft:rose_bush"]
FLOWERS_BUSH = ["minecraft:flowering_azalea", "minecraft:azalea"]


# ── 工具函数 ──

def _is_occupied(x, z):
    for x1, z1, x2, z2 in OCCUPIED_ZONES:
        if x1 <= x <= x2 and z1 <= z <= z2:
            return True
    return False


def _in_pond(x, z):
    p = POND_ELLIPSE
    return ((x - p["cx"]) / p["rx"]) ** 2 + ((z - p["cz"]) / p["rz"]) ** 2 <= 1.0


def _near_plum(x, z):
    px, pz = PLUM_POS
    return (x - px) ** 2 + (z - pz) ** 2 <= PLUM_CLEAR_RADIUS ** 2


def _can_place(x, z):
    if x < 1 or x > G["x_max"] - 1 or z < 1 or z > G["z_max"] - 1:
        return False
    return not _is_occupied(x, z) and not _in_pond(x, z)


def _can_place_flora(x, z):
    return _can_place(x, z) and not _near_plum(x, z)


def _place_double(b, x, y, z, block):
    """放置双格高植物"""
    b.setblock(x, y, z, f"{block}[half=lower]")
    b.setblock(x, y + 1, z, f"{block}[half=upper]")


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
#  1. 大梅树
# ══════════════════════════════════════════════════════════════

def _build_plum_tree(b: MinecraftBuilder):
    """2x2 cherry_log 树干高6格 + cherry_leaves 大冠幅半径5格"""
    print("  [1/6] 大梅树...")
    px, pz = PLUM_POS

    # 树干: 2x2, 高6格
    trunk_h = 6
    for dy in range(trunk_h):
        y = BUILD_Y + dy
        for dx in range(2):
            for dz in range(2):
                b.setblock(px + dx, y, pz + dz, PALETTE["cherry_log"])

    # 树冠: 分层构造，最大半径5格
    crown_cy = BUILD_Y + trunk_h + 1
    crown_cx = px + 0.5
    crown_cz = pz + 0.5

    crown_layers = [
        (-2, 4),   # 底层
        (-1, 5),   # 次宽
        (0,  5),   # 最宽
        (1,  5),   # 最宽
        (2,  4),   # 收窄
        (3,  3),   # 顶部
        (4,  1),   # 尖顶
    ]

    for dy_off, radius in crown_layers:
        y = crown_cy + dy_off
        for dx in range(-radius, radius + 1):
            for dz in range(-radius, radius + 1):
                dist_sq = dx * dx + dz * dz
                threshold = radius * radius
                if dist_sq <= threshold:
                    # 边缘随机缺失，制造自然不规则
                    if dist_sq > threshold * 0.55 and random.random() < 0.28:
                        continue
                    lx = int(crown_cx + dx)
                    lz = int(crown_cz + dz)
                    b.setblock(lx, y, lz, PALETTE["cherry_leaves"])

    # 树下: 苔藓 + 落花 (pink_carpet 散块)
    for dx in range(-4, 5):
        for dz in range(-4, 5):
            tx, tz = px + dx, pz + dz
            dist = math.sqrt(dx * dx + dz * dz)
            if dist > 4.5:
                continue
            if 0 <= dx <= 1 and 0 <= dz <= 1:
                continue  # 树干
            if not _can_place(tx, tz):
                continue

            r = random.random()
            if r < 0.22:
                b.setblock(tx, GROUND_Y, tz, PALETTE["moss"])
            elif r < 0.38:
                b.setblock(tx, BUILD_Y, tz, "minecraft:pink_carpet")
            elif r < 0.48:
                b.setblock(tx, BUILD_Y, tz, PALETTE["moss_carpet"])

    print(f"    梅树完成 @ ({px}, {pz})")


# ══════════════════════════════════════════════════════════════
#  2. 花木散植
# ══════════════════════════════════════════════════════════════

def _build_flower_clusters(b: MinecraftBuilder):
    """5个花丛，每丛20~30朵，极坐标分布中心密边缘疏"""
    print("  [2/6] 花木散植...")
    total = 0

    for cx, cz in FLOWER_CENTERS:
        count = random.randint(20, 30)
        radius = random.randint(4, 6)
        placed = 0
        attempts = 0

        while placed < count and attempts < count * 5:
            attempts += 1
            # 极坐标：中心密、边缘疏
            angle = random.uniform(0, 2 * math.pi)
            dist = random.uniform(0, radius) ** 0.65  # 幂次<1 中心更密
            fx = cx + int(round(dist * math.cos(angle)))
            fz = cz + int(round(dist * math.sin(angle)))

            if not _can_place_flora(fx, fz):
                continue

            b.setblock(fx, GROUND_Y, fz, PALETTE["grass"])

            r = random.random()
            if r < 0.25:
                _place_double(b, fx, BUILD_Y, fz, random.choice(FLOWERS_DOUBLE))
            elif r < 0.55:
                b.setblock(fx, BUILD_Y, fz, random.choice(FLOWERS_SINGLE))
            elif r < 0.75:
                b.setblock(fx, BUILD_Y, fz, random.choice(FLOWERS_BUSH))
            else:
                b.setblock(fx, BUILD_Y, fz, random.choice(FLOWERS_SINGLE))

            placed += 1

        total += placed
        print(f"    花丛 ({cx},{cz}): {placed}/{count}")

    print(f"    花卉总计: {total}")


# ══════════════════════════════════════════════════════════════
#  3. 垂杨
# ══════════════════════════════════════════════════════════════

def _build_willows(b: MinecraftBuilder):
    """4棵垂柳：oak_log 高5~7, oak_leaves 扁平宽冠, vine 垂3~5格"""
    print("  [3/6] 垂杨散植...")

    for wx, wz in WILLOW_POS:
        trunk_h = random.randint(5, 7)

        # 树干
        for dy in range(trunk_h):
            b.setblock(wx, BUILD_Y + dy, wz, PALETTE["oak_log"])

        # 扁平宽冠
        crown_top = BUILD_Y + trunk_h
        h_radius = random.randint(3, 4)
        v_layers = [
            (0,  h_radius),       # 最宽
            (1,  h_radius - 1),   # 上收
            (-1, h_radius - 1),   # 下收
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
                        b.setblock(lx, y, lz, PALETTE["oak_leaves"])

                        # 收集可挂藤位置（底层和最宽层边缘）
                        if dy_off <= 0 and dist_sq > (r - 1) ** 2:
                            vine_candidates.append((lx, y, lz))

        # 去重并随机选取
        vine_candidates = list(set(vine_candidates))
        random.shuffle(vine_candidates)
        vine_count = min(len(vine_candidates), random.randint(10, 18))

        for vx, vy, vz in vine_candidates[:vine_count]:
            facing = _get_vine_facing(vx, vy, vz, wx, wz)
            vine_len = random.randint(3, 5)  # 垂3~5格！核心特征
            for vdy in range(vine_len):
                b.setblock(vx, vy - 1 - vdy, vz, facing)

        print(f"    垂柳 @ ({wx},{wz}), 高{trunk_h}, 藤{vine_count}条")


# ══════════════════════════════════════════════════════════════
#  4. 断井
# ══════════════════════════════════════════════════════════════

def _build_wells(b: MinecraftBuilder):
    """3口断井：cobblestone 3x3 + 中空 + 水底 + 苔藓覆盖"""
    print("  [4/6] 断井...")

    for wx, wz in WELL_POS:
        well_depth = random.randint(3, 4)

        # 中心挖洞
        for dy in range(well_depth):
            b.setblock(wx, GROUND_Y - dy, wz, "minecraft:air")
        # 底部水
        b.setblock(wx, GROUND_Y - well_depth, wz, "minecraft:water")

        # 3x3 围石（包括井壁下沉部分）
        for dx in range(-1, 2):
            for dz in range(-1, 2):
                if dx == 0 and dz == 0:
                    continue  # 中空
                sx, sz = wx + dx, wz + dz
                # 地面层
                b.setblock(sx, GROUND_Y, sz, "minecraft:cobblestone")
                # 井壁
                for dy in range(1, well_depth):
                    b.setblock(sx, GROUND_Y - dy, sz, "minecraft:cobblestone")
                # 井栏（高出地面一格）
                b.setblock(sx, BUILD_Y, sz, "minecraft:cobblestone")

        # 苔藓覆盖：井栏顶部随机替换
        moss_spots = [(-1, -1), (1, 0), (0, 1), (-1, 1), (1, -1)]
        for dx, dz in moss_spots:
            if random.random() < 0.6:
                b.setblock(wx + dx, BUILD_Y, wz + dz, PALETTE["moss"])

        # 周围高草蕨类
        for dx in range(-2, 3):
            for dz in range(-2, 3):
                if abs(dx) <= 1 and abs(dz) <= 1:
                    continue
                gx, gz = wx + dx, wz + dz
                if not _can_place(gx, gz):
                    continue
                r = random.random()
                if r < 0.3:
                    b.setblock(gx, GROUND_Y, gz, PALETTE["grass"])
                    b.setblock(gx, BUILD_Y, gz, "minecraft:short_grass")
                elif r < 0.45:
                    b.setblock(gx, GROUND_Y, gz, PALETTE["grass"])
                    b.setblock(gx, BUILD_Y, gz, PALETTE["fern"])

        print(f"    断井 @ ({wx},{wz}), 深{well_depth}")


# ══════════════════════════════════════════════════════════════
#  5. 全园做旧
# ══════════════════════════════════════════════════════════════

def _apply_weathering(b: MinecraftBuilder):
    """藤蔓、苔藓、高草、苔藓石砖 — 全园岁月痕迹"""
    print("  [5/6] 全园做旧...")
    vine_ct = moss_ct = grass_ct = 0

    x_max, z_max = G["x_max"], G["z_max"]

    # 空地10%高草蕨类
    for x in range(1, x_max):
        for z in range(1, z_max):
            if _can_place_flora(x, z):
                r = random.random()
                if r < 0.07:
                    b.setblock(x, GROUND_Y, z, PALETTE["grass"])
                    b.setblock(x, BUILD_Y, z, "minecraft:short_grass")
                    grass_ct += 1
                elif r < 0.10:
                    b.setblock(x, GROUND_Y, z, PALETTE["grass"])
                    b.setblock(x, BUILD_Y, z, PALETTE["fern"])
                    grass_ct += 1

    # 围墙5%藤蔓（内侧）
    for y in range(BUILD_Y, BUILD_Y + 4):
        # 西墙
        for z in range(1, z_max):
            if random.random() < 0.05:
                b.setblock(1, y, z, "minecraft:vine[west=true]")
                vine_ct += 1
        # 东墙
        for z in range(1, z_max):
            if random.random() < 0.05:
                b.setblock(x_max - 1, y, z, "minecraft:vine[east=true]")
                vine_ct += 1
        # 北墙
        for x in range(1, x_max):
            if random.random() < 0.05:
                b.setblock(x, y, 1, "minecraft:vine[north=true]")
                vine_ct += 1
        # 南墙
        for x in range(1, x_max):
            if random.random() < 0.05:
                b.setblock(x, y, z_max - 1, "minecraft:vine[south=true]")
                vine_ct += 1

    # 石砖3%替换苔藓石砖
    for x in range(0, x_max + 1):
        for z in range(0, z_max + 1):
            if random.random() < 0.03:
                b.cmd(f"execute if block {x} {GROUND_Y} {z} "
                      f"minecraft:stone_bricks run setblock "
                      f"{x} {GROUND_Y} {z} minecraft:mossy_stone_bricks")
                moss_ct += 1

    print(f"    藤蔓: {vine_ct}, 苔砖: {moss_ct}, 草/蕨: {grass_ct}")


# ══════════════════════════════════════════════════════════════
#  6. ★ 江南远景山水 ★
# ══════════════════════════════════════════════════════════════

def _build_north_mountains(b: MinecraftBuilder):
    """北面远景青山：3~4座不规则山丘，高8~15格，山上点树，山间小溪"""
    print("    [远景] 北面青山...")

    # 山丘定义: (中心x, 中心z, 宽x, 宽z, 高度)
    mountains = [
        (20,  -8,  20, 10, 13),   # 大山
        (55,  -6,  25, 8,  10),   # 中山
        (90,  -9,  18, 10, 15),   # 高山
        (110, -5,  15, 8,   8),   # 矮丘
    ]

    for mcx, mcz, w_half_x, w_half_z, height in mountains:
        # 用椭球体模型堆山
        rx = w_half_x // 2
        rz = w_half_z // 2

        for dy in range(height):
            y = GROUND_Y + dy
            # 每层半径按高度递减（山形轮廓）
            progress = dy / height
            layer_rx = int(rx * (1 - progress ** 0.8))
            layer_rz = int(rz * (1 - progress ** 0.8))

            if layer_rx < 1 or layer_rz < 1:
                # 顶部只放一两块
                b.setblock(mcx, y, mcz, "minecraft:grass_block")
                continue

            for dx in range(-layer_rx, layer_rx + 1):
                for dz in range(-layer_rz, layer_rz + 1):
                    # 椭圆判定 + 噪声
                    dist = (dx / layer_rx) ** 2 + (dz / layer_rz) ** 2
                    noise = random.uniform(-0.15, 0.15)
                    if dist + noise > 1.0:
                        continue

                    bx = mcx + dx
                    bz = mcz + dz

                    # 选材质：顶层草方块，中层石/安山岩，底层石
                    if dy == height - 1 or (dy > height * 0.7 and random.random() < 0.6):
                        block = "minecraft:grass_block"
                    elif dy > height * 0.4:
                        block = random.choice(["minecraft:stone", "minecraft:andesite"])
                    else:
                        block = "minecraft:stone"

                    b.setblock(bx, y, bz, block)

        # 山顶种树（1~3棵）
        tree_count = random.randint(1, 3)
        for _ in range(tree_count):
            tx = mcx + random.randint(-rx // 2, rx // 2)
            tz = mcz + random.randint(-rz // 2, rz // 2)
            ty_base = GROUND_Y + height
            _place_simple_tree(b, tx, ty_base, tz)

    # 山间小溪：两座山之间铺2格宽水道
    stream_z = -6
    for x in range(35, 60):
        for dz in range(2):
            b.setblock(x, GROUND_Y, stream_z + dz, "minecraft:water")
            # 水底泥土
            b.setblock(x, GROUND_Y - 1, stream_z + dz, "minecraft:dirt")


def _build_east_west_hills(b: MinecraftBuilder):
    """东面/西面：矮丘+竹林"""
    print("    [远景] 东西矮丘竹林...")

    # 西面矮丘: X=-10~0 区域
    west_hills = [
        (-8, 20, 8, 6, 4),
        (-6, 50, 10, 6, 5),
        (-10, 75, 8, 8, 3),
    ]

    # 东面矮丘: X=120~135 区域
    east_hills = [
        (128, 15, 10, 6, 5),
        (130, 45, 8, 6, 4),
        (126, 70, 12, 8, 3),
    ]

    for hills in [west_hills, east_hills]:
        for hcx, hcz, wx, wz, height in hills:
            rx = wx // 2
            rz = wz // 2

            for dy in range(height):
                y = GROUND_Y + dy
                progress = dy / height
                lr = int(rx * (1 - progress ** 0.7))
                lrz = int(rz * (1 - progress ** 0.7))
                if lr < 1:
                    lr = 1
                if lrz < 1:
                    lrz = 1

                for dx in range(-lr, lr + 1):
                    for dz in range(-lrz, lrz + 1):
                        dist = (dx / lr) ** 2 + (dz / lrz) ** 2
                        if dist + random.uniform(-0.1, 0.1) > 1.0:
                            continue
                        bx, bz = hcx + dx, hcz + dz

                        if dy >= height - 1:
                            block = "minecraft:grass_block"
                        else:
                            block = "minecraft:stone"
                        b.setblock(bx, y, bz, block)

            # 丘顶种竹林（3~6根）
            bamboo_count = random.randint(3, 6)
            for _ in range(bamboo_count):
                bx = hcx + random.randint(-rx // 2, rx // 2)
                bz = hcz + random.randint(-rz // 2, rz // 2)
                bamboo_h = random.randint(3, 6)
                by = GROUND_Y + height
                # 竹子需要泥土基础
                b.setblock(bx, by - 1, bz, "minecraft:grass_block")
                for bdy in range(bamboo_h):
                    b.setblock(bx, by + bdy, bz, PALETTE["bamboo"])


def _build_south_waterfront(b: MinecraftBuilder):
    """南面：水边村落暗示 — 河流+垂柳+石桥"""
    print("    [远景] 南面水乡...")

    # 河流: Z=95~105, X=30~90, 宽10格
    river_z_start = 95
    river_z_end = 105

    for x in range(30, 91):
        for z in range(river_z_start, river_z_end + 1):
            # 水面
            b.setblock(x, GROUND_Y, z, "minecraft:water")
            # 河底
            b.setblock(x, GROUND_Y - 1, z, "minecraft:clay")
            b.setblock(x, GROUND_Y - 2, z, "minecraft:dirt")

    # 河岸: 稍高一格的草地
    for x in range(28, 93):
        for z in [river_z_start - 1, river_z_start - 2]:
            b.setblock(x, GROUND_Y, z, "minecraft:grass_block")
        for z in [river_z_end + 1, river_z_end + 2]:
            b.setblock(x, GROUND_Y, z, "minecraft:grass_block")

    # 河边垂柳: 3棵
    south_willows = [(40, 93), (60, 93), (80, 107)]
    for swx, swz in south_willows:
        trunk_h = random.randint(4, 6)
        for dy in range(trunk_h):
            b.setblock(swx, BUILD_Y + dy, swz, PALETTE["oak_log"])

        # 扁平冠
        crown_top = BUILD_Y + trunk_h
        r = 3
        for dy_off in [-1, 0, 1]:
            cr = r if dy_off == 0 else r - 1
            y = crown_top + dy_off
            for dx in range(-cr, cr + 1):
                for dz in range(-cr, cr + 1):
                    if dx * dx + dz * dz <= cr * cr:
                        if dx * dx + dz * dz > cr * cr * 0.5 and random.random() < 0.2:
                            continue
                        b.setblock(swx + dx, y, swz + dz, PALETTE["oak_leaves"])

        # 垂藤
        for dx in range(-r, r + 1):
            for dz in range(-r, r + 1):
                if r * r * 0.6 < dx * dx + dz * dz <= r * r:
                    if random.random() < 0.5:
                        facing = _get_vine_facing(swx + dx, crown_top, swz + dz, swx, swz)
                        vine_len = random.randint(3, 5)
                        for vdy in range(vine_len):
                            b.setblock(swx + dx, crown_top - 2 - vdy, swz + dz, facing)

    # 石桥: X=55~65 跨河，简单拱桥
    bridge_x_start = 55
    bridge_x_end = 65
    bridge_cx = (bridge_x_start + bridge_x_end) // 2

    for x in range(bridge_x_start, bridge_x_end + 1):
        # 桥面：简单平桥，中间略高（微拱）
        dist_from_center = abs(x - bridge_cx)
        bridge_y = BUILD_Y + 1 + max(0, 2 - dist_from_center // 2)

        for dz in range(river_z_start, river_z_end + 1):
            # 只在桥面宽度内（3格宽）
            mid_z = (river_z_start + river_z_end) // 2
            if abs(dz - mid_z) <= 1:
                b.setblock(x, bridge_y, dz, "minecraft:stone_brick_slab")
                # 桥墩: 每隔3格一根
                if (x - bridge_x_start) % 3 == 0:
                    for py in range(GROUND_Y, bridge_y):
                        b.setblock(x, py, mid_z, "minecraft:cobblestone")

        # 桥栏杆
        mid_z = (river_z_start + river_z_end) // 2
        for side_dz in [-2, 2]:
            rz = mid_z + side_dz
            b.setblock(x, bridge_y + 1, rz, "minecraft:cobblestone_wall")


def _place_simple_tree(b: MinecraftBuilder, tx: int, ty: int, tz: int):
    """放置一棵简单的小树（远景用，不需要太精细）"""
    trunk_h = random.randint(3, 5)
    for dy in range(trunk_h):
        b.setblock(tx, ty + dy, tz, PALETTE["oak_log"])

    crown_y = ty + trunk_h
    r = 2
    for dy_off in [-1, 0, 1]:
        cr = r if dy_off == 0 else r - 1
        if cr < 1:
            cr = 1
        y = crown_y + dy_off
        for dx in range(-cr, cr + 1):
            for dz in range(-cr, cr + 1):
                if dx * dx + dz * dz <= cr * cr + 1:
                    if random.random() < 0.8:
                        b.setblock(tx + dx, y, tz + dz, PALETTE["oak_leaves"])


# ══════════════════════════════════════════════════════════════
#  主入口
# ══════════════════════════════════════════════════════════════

def build_landscape(b: MinecraftBuilder):
    """园内景观收尾：大梅树 / 花丛 / 垂杨 / 断井 / 做旧"""
    print("=== 景观收尾 (v3) ===")
    random.seed(88)
    _build_plum_tree(b)
    _build_flower_clusters(b)
    _build_willows(b)
    _build_wells(b)
    _apply_weathering(b)
    b.register_bbox("landscape", 0, GROUND_Y - 5, 0,
                    G["x_max"], BUILD_Y + 15, G["z_max"])
    print("=== 景观收尾完成 ===")


def build_surrounding_landscape(b: MinecraftBuilder):
    """围墙外围江南远景山水"""
    print("=== 江南远景山水 ===")
    random.seed(99)
    _build_north_mountains(b)
    _build_east_west_hills(b)
    _build_south_waterfront(b)
    b.register_bbox("surrounding", -15, GROUND_Y - 3, -15,
                    G["x_max"] + 15, BUILD_Y + 20, G["z_max"] + 15)
    print("=== 江南远景完成 ===")


if __name__ == "__main__":
    with MinecraftBuilder() as b:
        build_landscape(b)
        build_surrounding_landscape(b)
        print(f"Done! {b.cmd_count} commands")
