"""景观收尾脚本 — 散布型景观元素一次性完成

大梅树 / 花木散植 / 垂杨 / 断井 / 全园做旧
"""

import sys; sys.path.insert(0, '/Users/lambertlin/minecraft-server/scripts')
from builder import MinecraftBuilder, filled_circle_points
from blocks import PALETTE, GROUND_Y, BUILD_Y
import random
import math

# ── 常量 ──

PLUM_TREE_POS = (8, 8)           # 大梅树中心 (x, z)
PLUM_CLEAR_RADIUS = 5            # 大梅树周围保持空旷的半径

POND_ELLIPSE = {"cx": 36, "cz": 29, "rx": 19, "rz": 10}  # 池塘椭圆参数

# 已有建筑矩形列表: (x_min, z_min, x_max, z_max)
# 曲廊范围 + 3格安全距离
OCCUPIED_ZONES = [
    (46, 4, 58, 16),       # 牡丹亭
    (47, 16, 57, 24),      # 芍药阑
    (5, 24, 19, 32),       # 翠轩
    (36, 38, 50, 62),      # 入口区
    (15, 5, 49, 43),       # 曲廊 + 3格安全距离
]

# 围墙占据的行列
WALL_LINES = {"x": [0, 80], "z": [0, 60]}

# 花丛中心及参数
FLOWER_CLUSTERS = [
    (30, 40),   # 池塘南岸
    (60, 25),   # 东侧空地
    (10, 45),   # 西南角
    (65, 35),   # 东侧
    (5, 15),    # 西北
]

# 垂杨位置（已修正：避开曲廊）
WILLOW_POSITIONS = [
    (15, 35),   # 翠轩南侧池塘边 — 翠轩西边，曲廊外
    (55, 35),   # 池塘东南岸 — 曲廊外
    (48, 20),   # 池塘北岸偏东 — 原 (45,20) 在曲廊内，东移
    (13, 20),   # 池塘西北岸 — 原 (25,22) 在曲廊内，西移到曲廊外
]

# 断井位置
WELL_POSITIONS = [
    (65, 45),   # 东南荒芜角落
    (70, 12),   # 东北
    (8, 40),    # 西侧
]

# 花卉方块列表（单格高 vs 双格高分别处理）
FLOWERS_SINGLE = [
    "minecraft:red_tulip",
    "minecraft:pink_tulip",
    "minecraft:cornflower",
    "minecraft:azure_bluet",         # 额外点缀
]
FLOWERS_DOUBLE = [
    "minecraft:peony",
    "minecraft:rose_bush",
]
FLOWERS_BUSH = [
    "minecraft:flowering_azalea",    # 这是方块不是花，直接放
    "minecraft:azalea",
]

# ── 工具函数 ──


def _is_occupied(x, z):
    """检查 (x, z) 是否在已有建筑/结构范围内"""
    for x1, z1, x2, z2 in OCCUPIED_ZONES:
        if x1 <= x <= x2 and z1 <= z <= z2:
            return True
    # 围墙
    if x in WALL_LINES["x"] or z in WALL_LINES["z"]:
        return True
    return False


def _in_pond(x, z):
    """检查 (x, z) 是否在池塘椭圆内"""
    p = POND_ELLIPSE
    return ((x - p["cx"]) / p["rx"]) ** 2 + ((z - p["cz"]) / p["rz"]) ** 2 <= 1.0


def _near_plum_tree(x, z):
    """检查是否在大梅树空旷范围内"""
    px, pz = PLUM_TREE_POS
    return (x - px) ** 2 + (z - pz) ** 2 <= PLUM_CLEAR_RADIUS ** 2


def _can_place(x, z):
    """综合检查：非建筑区、非池塘、非围墙"""
    if x < 1 or x > 79 or z < 1 or z > 59:
        return False
    return not _is_occupied(x, z) and not _in_pond(x, z)


def _can_place_flora(x, z):
    """可以种植花草的位置（额外排除大梅树范围）"""
    return _can_place(x, z) and not _near_plum_tree(x, z)


def _place_double_plant(b, x, y, z, block):
    """放置双格高植物（芍药/玫瑰丛/高草）"""
    b.setblock(x, y, z, f"{block}[half=lower]")
    b.setblock(x, y + 1, z, f"{block}[half=upper]")


# ── 1. 大梅树 ──


def _build_plum_tree(b: MinecraftBuilder):
    """一株大梅树 — 樱花原木+樱花树叶，孤独矗立"""
    print("  [1/5] 大梅树...")
    px, pz = PLUM_TREE_POS
    y_base = GROUND_Y  # -61 草方块层

    # --- 树干: 2x2 底座，高5格 ---
    trunk_height = 5
    for dy in range(trunk_height):
        y = BUILD_Y + dy  # -60 起
        for dx in range(2):
            for dz in range(2):
                b.setblock(px + dx, y, pz + dz, PALETTE["cherry_log"])

    # --- 树冠: 不规则球形，半径4~5 ---
    crown_cy = BUILD_Y + trunk_height + 1  # 树冠中心 y
    crown_cx = px + 0.5    # 树干中心
    crown_cz = pz + 0.5

    # 分层构造树冠（从下到上，每层半径不同）
    crown_layers = [
        (-2, 4),   # 底层，大半径
        (-1, 5),   # 最宽处
        (0, 5),    # 中心层
        (1, 4),
        (2, 3),    # 收窄
        (3, 2),    # 顶部
    ]

    for dy_offset, radius in crown_layers:
        y = crown_cy + dy_offset
        for dx in range(-radius, radius + 1):
            for dz in range(-radius, radius + 1):
                dist_sq = dx * dx + dz * dz
                # 基础圆形 + 随机扰动制造不规则感
                threshold = radius * radius
                if dist_sq <= threshold:
                    # 在边缘处随机去掉一些叶子
                    if dist_sq > threshold * 0.6 and random.random() < 0.3:
                        continue
                    lx = int(crown_cx + dx)
                    lz = int(crown_cz + dz)
                    b.setblock(lx, y, lz, PALETTE["cherry_leaves"])

    # --- 树下布置：苔藓和落花 ---
    for dx in range(-3, 4):
        for dz in range(-3, 4):
            tx = px + dx
            tz = pz + dz
            dist = math.sqrt(dx * dx + dz * dz)
            if dist > 3.5:
                continue
            # 跳过树干本身
            if 0 <= dx <= 1 and 0 <= dz <= 1:
                continue
            if not _can_place(tx, tz):
                continue

            r = random.random()
            if r < 0.25:
                # 苔藓块替换地面
                b.setblock(tx, GROUND_Y, tz, PALETTE["moss"])
            elif r < 0.4:
                # 落花 — 粉色地毯模拟花瓣
                b.setblock(tx, BUILD_Y, tz, "minecraft:pink_carpet")
            elif r < 0.5:
                # 苔藓地毯
                b.setblock(tx, BUILD_Y, tz, PALETTE["moss_carpet"])

    print(f"    梅树完成 @ ({px}, {pz})")


# ── 2. 花木散植 ──


def _build_flower_clusters(b: MinecraftBuilder):
    """姹紫嫣红开遍 — 簇状散植花卉"""
    print("  [2/5] 花木散植...")
    total = 0

    for cx, cz in FLOWER_CLUSTERS:
        # 每个花丛中心周围随机分布
        count = random.randint(15, 25)
        radius = random.randint(3, 5)

        # 靠近芍药阑的中心多放芍药
        near_shaoyao = (45 <= cx <= 60 and 15 <= cz <= 28)

        placed = 0
        attempts = 0
        while placed < count and attempts < count * 4:
            attempts += 1
            # 极坐标随机分布，距中心越远越稀疏
            angle = random.uniform(0, 2 * math.pi)
            dist = random.uniform(0, radius) ** 0.7  # 幂次<1 让中心更密
            fx = cx + int(round(dist * math.cos(angle)))
            fz = cz + int(round(dist * math.sin(angle)))

            if not _can_place_flora(fx, fz):
                continue

            # 确保下方是泥土/草方块（在石砖等表面先放泥土）
            b.setblock(fx, GROUND_Y, fz, PALETTE["grass"])

            # 选花
            r = random.random()
            if near_shaoyao and r < 0.4:
                # 芍药阑附近偏重芍药
                _place_double_plant(b, fx, BUILD_Y, fz, "minecraft:peony")
            elif r < 0.2:
                _place_double_plant(b, fx, BUILD_Y, fz,
                                    random.choice(FLOWERS_DOUBLE))
            elif r < 0.5:
                b.setblock(fx, BUILD_Y, fz, random.choice(FLOWERS_SINGLE))
            elif r < 0.7:
                # 杜鹃灌木（方块型，放在地面上）
                b.setblock(fx, BUILD_Y, fz, random.choice(FLOWERS_BUSH))
            else:
                # 低矮花卉
                b.setblock(fx, BUILD_Y, fz, random.choice(FLOWERS_SINGLE))

            placed += 1

        total += placed
        print(f"    花丛 ({cx},{cz}): {placed} 朵")

    print(f"    花卉总计: {total}")


# ── 3. 垂杨散植 ──


def _build_willows(b: MinecraftBuilder):
    """一丝丝垂杨线 — 池塘岸边的垂柳"""
    print("  [3/5] 垂杨散植...")

    for wx, wz in WILLOW_POSITIONS:
        trunk_h = random.randint(4, 6)
        y_base = BUILD_Y  # -60

        # --- 树干 ---
        for dy in range(trunk_h):
            b.setblock(wx, y_base + dy, wz, "minecraft:oak_log")

        # --- 扁平宽冠（水平大于垂直）---
        crown_top = y_base + trunk_h
        # 扁冠: 水平半径3~4，垂直仅2~3层
        h_radius = random.randint(3, 4)
        v_layers = [
            (0, h_radius),       # 最宽层
            (1, h_radius - 1),   # 上收
            (-1, h_radius - 1),  # 下收
        ]

        vine_candidates = []  # 收集可以挂藤蔓的位置

        for dy_off, r in v_layers:
            y = crown_top + dy_off
            for dx in range(-r, r + 1):
                for dz in range(-r, r + 1):
                    dist_sq = dx * dx + dz * dz
                    if dist_sq <= r * r:
                        # 边缘随机去掉
                        if dist_sq > r * r * 0.5 and random.random() < 0.25:
                            continue
                        lx = wx + dx
                        lz = wz + dz
                        b.setblock(lx, y, lz, PALETTE["oak_leaves"])

                        # 树冠底部边缘是挂藤蔓的好位置
                        if dy_off == -1 and dist_sq > (r - 1) ** 2:
                            vine_candidates.append((lx, y, lz))

        # 补充: 最宽层边缘下方也挂藤
        for dy_off, r in v_layers:
            if dy_off != 0:
                continue
            y = crown_top + dy_off
            for dx in range(-r, r + 1):
                for dz in range(-r, r + 1):
                    dist_sq = dx * dx + dz * dz
                    if r * r * 0.7 < dist_sq <= r * r:
                        lx = wx + dx
                        lz = wz + dz
                        vine_candidates.append((lx, y, lz))

        # --- 垂枝: vine 从树叶下方垂挂 ---
        # 去重
        vine_candidates = list(set(vine_candidates))
        random.shuffle(vine_candidates)
        vine_count = min(len(vine_candidates), random.randint(8, 14))

        for vx, vy, vz in vine_candidates[:vine_count]:
            # 确定 vine 朝向：vine 需要附着在方块侧面
            # 找到一个相邻有树叶的方向
            facing = _get_vine_facing(vx, vy, vz, wx, wz)
            vine_len = random.randint(2, 3)
            for vdy in range(vine_len):
                b.setblock(vx, vy - 1 - vdy, vz, facing)

        print(f"    垂柳 @ ({wx},{wz}), 高{trunk_h}, 藤{vine_count}条")


def _get_vine_facing(vx, vy, vz, trunk_x, trunk_z):
    """根据vine位置相对树干的方向，生成正确的vine方块字符串
    vine 需要贴在相邻方块的侧面，朝向远离树干的方向"""
    dx = vx - trunk_x
    dz = vz - trunk_z

    # 主要朝向：vine面朝外（远离树干）
    # vine 的属性是指它贴附的那一面
    # 例如 north=true 表示 vine 贴在北面（即它南侧有方块支撑）
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
        faces.append("south=true")  # 默认

    state = ",".join(faces)
    return f"minecraft:vine[{state}]"


# ── 4. 断井 ──


def _build_ruined_wells(b: MinecraftBuilder):
    """断井颓垣 — 荒废的古井"""
    print("  [4/5] 断井...")

    for wx, wz in WELL_POSITIONS:
        y_base = GROUND_Y  # -61

        # --- 3x3 圆石外框，中间空洞 ---
        well_depth = random.randint(3, 4)

        # 挖洞（向下挖 well_depth 格）
        for dy in range(well_depth):
            b.setblock(wx, y_base - dy, wz, "minecraft:air")

        # 底部放水
        b.setblock(wx, y_base - well_depth, wz, "minecraft:water")

        # 围石（地面层）
        for dx in range(-1, 2):
            for dz in range(-1, 2):
                if dx == 0 and dz == 0:
                    continue  # 中间是洞
                sx = wx + dx
                sz = wz + dz
                b.setblock(sx, y_base, sz, "minecraft:cobblestone")
                # 井壁内侧（下方也用圆石围住防止坍塌）
                for dy in range(1, well_depth):
                    b.setblock(sx, y_base - dy, sz, "minecraft:cobblestone")

        # 顶部加一层（高出地面一格，模拟井栏）
        for dx in range(-1, 2):
            for dz in range(-1, 2):
                if dx == 0 and dz == 0:
                    continue
                sx = wx + dx
                sz = wz + dz
                b.setblock(sx, BUILD_Y, sz, "minecraft:cobblestone")

        # --- 部分覆盖苔藓 ---
        moss_positions = [(-1, -1), (1, 0), (0, 1)]
        for dx, dz in moss_positions:
            b.setblock(wx + dx, BUILD_Y, wz + dz, PALETTE["moss"])

        # --- 周围高草和蕨类 ---
        for dx in range(-2, 3):
            for dz in range(-2, 3):
                if abs(dx) <= 1 and abs(dz) <= 1:
                    continue  # 井本身
                gx = wx + dx
                gz = wz + dz
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


# ── 5. 全园做旧 ──


def _apply_garden_weathering(b: MinecraftBuilder):
    """最后一步：藤蔓、苔藓、高草、碎石 — 让园林显出岁月痕迹"""
    print("  [5/5] 全园做旧...")
    vine_count = 0
    moss_count = 0
    grass_count = 0
    gravel_count = 0

    for x in range(1, 80):
        for z in range(1, 60):
            # ---- 空地上的高草和蕨类 (10%) ----
            if _can_place_flora(x, z) and not _in_pond(x, z):
                r = random.random()
                if r < 0.07:
                    # 普通高草（单格）
                    b.setblock(x, GROUND_Y, z, PALETTE["grass"])
                    b.setblock(x, BUILD_Y, z, "minecraft:short_grass")
                    grass_count += 1
                elif r < 0.10:
                    # 蕨类
                    b.setblock(x, GROUND_Y, z, PALETTE["grass"])
                    b.setblock(x, BUILD_Y, z, PALETTE["fern"])
                    grass_count += 1

            # ---- 草地上偶尔放碎石 (2%) ----
            if _can_place_flora(x, z) and not _in_pond(x, z):
                if random.random() < 0.02:
                    b.setblock(x, GROUND_Y, z, PALETTE["gravel"])
                    gravel_count += 1

    # ---- 围墙和建筑墙面贴藤蔓 (5%) ----
    # 围墙: X=0, X=80 (南北走向), Z=0, Z=60 (东西走向)
    # 在墙的内侧贴藤蔓
    for y in range(BUILD_Y, BUILD_Y + 4):
        # 西墙内侧 (X=0 的墙，藤蔓贴在 X=1 面朝西)
        for z in range(1, 60):
            if random.random() < 0.05:
                b.setblock(1, y, z, "minecraft:vine[west=true]")
                vine_count += 1
        # 东墙内侧
        for z in range(1, 60):
            if random.random() < 0.05:
                b.setblock(79, y, z, "minecraft:vine[east=true]")
                vine_count += 1
        # 北墙内侧
        for x in range(1, 80):
            if random.random() < 0.05:
                b.setblock(x, y, 1, "minecraft:vine[north=true]")
                vine_count += 1
        # 南墙内侧
        for x in range(1, 80):
            if random.random() < 0.05:
                b.setblock(x, y, 59, "minecraft:vine[south=true]")
                vine_count += 1

    # ---- 石砖地面替换苔藓石砖 (3%) ----
    # 扫描全园地面层，石砖 → 苔藓石砖
    # 用 replace 命令效率更高，但需要分区域执行
    # 全园地面分块替换
    for x_start in range(0, 81, 20):
        x_end = min(x_start + 19, 80)
        for z_start in range(0, 61, 20):
            z_end = min(z_start + 19, 60)
            # 在这个区块内逐格判断（因为只有3%概率）
            for x in range(x_start, x_end + 1):
                for z in range(z_start, z_end + 1):
                    if random.random() < 0.03:
                        # 尝试替换（如果当前是石砖就换成苔藓石砖）
                        b.cmd(f"execute if block {x} {GROUND_Y} {z} "
                              f"minecraft:stone_bricks run setblock "
                              f"{x} {GROUND_Y} {z} minecraft:mossy_stone_bricks")
                        moss_count += 1

    print(f"    藤蔓: {vine_count}, 苔砖: {moss_count}, "
          f"草/蕨: {grass_count}, 碎石: {gravel_count}")


# ── 主入口 ──


def build_landscape(b: MinecraftBuilder):
    print("=== 景观收尾 ===")
    random.seed(88)
    _build_plum_tree(b)
    _build_flower_clusters(b)
    _build_willows(b)
    _build_ruined_wells(b)
    _apply_garden_weathering(b)
    b.register_bbox("landscape", 0, -63, 0, 80, -50, 60)
    print("=== 景观收尾完成 ===")


if __name__ == "__main__":
    with MinecraftBuilder() as b:
        build_landscape(b)
        print(f"Done! {b.cmd_count} commands")
