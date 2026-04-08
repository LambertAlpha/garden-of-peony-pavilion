"""东面景观 — 竹林坡地 + 远山 + 月洞门外小庭

布局 (X=122~180, Z=10~80):
  X=122~125  东墙外过渡草地
  X=125~135  缓坡渐升
  X=130~145  竹林带 (密植竹子 + 苔藓地面 + 林间小径)
  X=145~155  坡地继续升高
  X=155~180  远山 (1大1小, 椭球体堆叠)
  X=121~124  月洞门外小庭 (Z=43~47)
"""

import sys; sys.path.insert(0, '/Users/lambertlin/minecraft-server/scripts')
from builder import MinecraftBuilder, filled_circle_points
from blocks import PALETTE, GROUND_Y, BUILD_Y
import random
import math


# ── 常量 ──

SLOPE_X_MIN, SLOPE_X_MAX = 122, 155
SLOPE_Z_MIN, SLOPE_Z_MAX = 10, 80

BAMBOO_X_MIN, BAMBOO_X_MAX = 130, 145
BAMBOO_Z_MIN, BAMBOO_Z_MAX = 15, 70

# 远山参数
BIG_MOUNTAIN = {"cx": 165, "cz": 40, "rx": 20, "rz": 25, "height": 35}
SMALL_MOUNTAIN = {"cx": 170, "cz": 70, "rx": 12, "rz": 15, "height": 20}

# 竹林小径 Z 中心线（蜿蜒）
PATH_CENTER_Z = 42


# ── 1. 缓坡地形 ──

def _slope_height(x: int, z: int, rng: random.Random) -> int:
    """计算缓坡 (x, z) 处的目标 Y 高度。

    从 y=GROUND_Y (X=122) 缓升到 y=GROUND_Y+6 (X=155)
    使用 sin 波叠加 + 随机抖动，避免单调直线斜坡。
    Z 方向边缘渐消，中部略高。
    """
    # X 方向基础升高: 0 ~ 6
    if x < SLOPE_X_MIN:
        return GROUND_Y
    if x > SLOPE_X_MAX:
        x_progress = 1.0
    else:
        x_progress = (x - SLOPE_X_MIN) / (SLOPE_X_MAX - SLOPE_X_MIN)

    base_rise = 6.0 * x_progress

    # sin 波起伏 (两个频率叠加)
    wave1 = 0.8 * math.sin(x * 0.15 + 0.7)
    wave2 = 0.5 * math.sin(z * 0.12 + x * 0.08)
    wave3 = 0.3 * math.sin(x * 0.25 + z * 0.18 + 1.5)
    base_rise += wave1 + wave2 + wave3

    # Z 方向边缘渐消: Z=10~15 和 Z=75~80 高度递减
    if z < 15:
        z_factor = max(0.0, (z - SLOPE_Z_MIN) / 5.0)
        base_rise *= z_factor
    elif z > 75:
        z_factor = max(0.0, (SLOPE_Z_MAX - z) / 5.0)
        base_rise *= z_factor

    # Z 中部微微隆起
    z_mid = (SLOPE_Z_MIN + SLOPE_Z_MAX) / 2
    z_bulge = 0.5 * math.exp(-((z - z_mid) / 25.0) ** 2)
    base_rise += z_bulge

    # 随机抖动
    if base_rise > 2:
        jitter = rng.choice([-1, -1, 0, 0, 0, 1, 1, 2])
    elif base_rise > 0.5:
        jitter = rng.choice([-1, 0, 0, 0, 1])
    else:
        jitter = 0

    final_rise = max(0, round(base_rise + jitter))
    return GROUND_Y + final_rise


def _build_slope(b: MinecraftBuilder, rng: random.Random):
    """构建缓坡地形"""
    print("  [1/4] 缓坡地形...")
    cmd_before = b.cmd_count

    # 生成高度图
    height_map = {}
    for x in range(SLOPE_X_MIN, SLOPE_X_MAX + 1):
        for z in range(SLOPE_Z_MIN, SLOPE_Z_MAX + 1):
            target_y = _slope_height(x, z, rng)
            if target_y > GROUND_Y:
                height_map[(x, z)] = target_y

    # 按 X 列填充，合并连续同高 Z 段
    for x in range(SLOPE_X_MIN, SLOPE_X_MAX + 1):
        z = SLOPE_Z_MIN
        while z <= SLOPE_Z_MAX:
            if (x, z) not in height_map:
                z += 1
                continue

            target_y = height_map[(x, z)]
            z_start = z
            z_end = z
            while z_end + 1 <= SLOPE_Z_MAX and height_map.get((x, z_end + 1)) == target_y:
                z_end += 1

            # 填充 dirt 柱 (GROUND_Y 到 target_y - 1)
            if target_y - 1 >= GROUND_Y:
                b.fill(x, GROUND_Y, z_start,
                       x, target_y - 1, z_end,
                       PALETTE["dirt"])

            # 顶层 grass_block
            b.fill(x, target_y, z_start,
                   x, target_y, z_end,
                   PALETTE["grass"])

            z = z_end + 1

    print(f"    缓坡完成: {b.cmd_count - cmd_before} commands")
    return height_map


# ── 2. 竹林带 ──

def _build_bamboo_forest(b: MinecraftBuilder, height_map: dict, rng: random.Random):
    """密植竹林 + 苔藓地面 + 林间蜿蜒小径"""
    print("  [2/4] 竹林带...")
    cmd_before = b.cmd_count
    bamboo_count = 0
    fern_count = 0

    # 先铺苔藓地面（替换竹林范围内的草方块顶层）
    for x in range(BAMBOO_X_MIN, BAMBOO_X_MAX + 1):
        for z in range(BAMBOO_Z_MIN, BAMBOO_Z_MAX + 1):
            top_y = height_map.get((x, z), GROUND_Y)

            # 判断是否在小径上
            if _is_on_path(x, z):
                b.setblock(x, top_y, z, "minecraft:dirt_path")
                continue

            # 苔藓地面
            if rng.random() < 0.7:
                b.setblock(x, top_y, z, PALETTE["moss"])
            # else 保留草方块

            # 蕨类散植 (地面装饰)
            if rng.random() < 0.15:
                b.setblock(x, top_y + 1, z, PALETTE["fern"])
                fern_count += 1

    # 种竹子 (每隔 1~2 格)
    for x in range(BAMBOO_X_MIN, BAMBOO_X_MAX + 1):
        for z in range(BAMBOO_Z_MIN, BAMBOO_Z_MAX + 1):
            if _is_on_path(x, z):
                continue

            # 间距控制: 每隔 1~2 格种一棵
            if (x + z) % 2 == 0 and rng.random() < 0.65:
                top_y = height_map.get((x, z), GROUND_Y)
                # 竹子高度 3~8 格
                bamboo_h = rng.randint(3, 8)
                for dy in range(bamboo_h):
                    age = "1" if dy == bamboo_h - 1 else "0"
                    leaves = "large" if dy >= bamboo_h - 1 else ("small" if dy >= bamboo_h - 2 else "none")
                    stage = "1" if dy == bamboo_h - 1 else "0"
                    b.setblock(x, top_y + 1 + dy, z,
                               f"minecraft:bamboo[age={age},leaves={leaves},stage={stage}]")
                bamboo_count += 1

    print(f"    竹林完成: {bamboo_count} 棵竹子, {fern_count} 蕨类, "
          f"{b.cmd_count - cmd_before} commands")


def _is_on_path(x: int, z: int) -> bool:
    """判断是否在蜿蜒小径上 (2格宽)"""
    # 小径沿 Z 方向蜿蜒，X 中心线随 Z 做 sin 偏移
    path_center_x = 137 + 2.0 * math.sin(z * 0.1)
    return abs(x - path_center_x) < 1.2


# ── 3. 远山 ──

def _build_mountain(b: MinecraftBuilder, params: dict, rng: random.Random, name: str):
    """用椭球体逐层堆叠建造一座山

    材质分层:
      山脚 (底部 30%) → grass_block
      山腰 (30%~70%) → stone + andesite 混合
      山顶 (70%~100%) → stone (裸岩)
    """
    cx = params["cx"]
    cz = params["cz"]
    rx = params["rx"]
    rz = params["rz"]
    height = params["height"]
    base_y = GROUND_Y  # 山脚起始 Y

    print(f"    建造 {name}: 中心({cx},{cz}), 高{height}, 半径({rx},{rz})...")
    cmd_before = b.cmd_count

    # 逐层从底到顶
    for dy in range(height):
        y = base_y + dy
        y_ratio = dy / height  # 0.0 (底) ~ 1.0 (顶)

        # 当前层的椭圆半径 (越高越小，用椭球公式)
        # 椭球: (x-cx)^2/rx^2 + (z-cz)^2/rz^2 + (y-base_y)^2/ry^2 <= 1
        # 当前层: layer_factor = sqrt(1 - (dy/height)^2)
        layer_factor = math.sqrt(max(0, 1.0 - (dy / height) ** 2))

        # 加一点随机扰动让山形不那么规则
        noise_amp = 0.08
        layer_rx = rx * layer_factor
        layer_rz = rz * layer_factor

        if layer_rx < 0.5 or layer_rz < 0.5:
            continue

        # 材质选择
        if y_ratio < 0.3:
            # 山脚: 草地
            block_choices = [PALETTE["grass"]]
        elif y_ratio < 0.7:
            # 山腰: 石头 + 安山岩混合
            block_choices = [
                PALETTE["stone"], PALETTE["stone"], PALETTE["stone"],
                "minecraft:andesite", "minecraft:andesite",
                PALETTE["cobblestone"],
            ]
        else:
            # 山顶: 裸岩
            block_choices = [
                PALETTE["stone"], PALETTE["stone"],
                "minecraft:andesite",
            ]

        # 扫描当前层椭圆范围
        int_rx = int(math.ceil(layer_rx)) + 1
        int_rz = int(math.ceil(layer_rz)) + 1

        for dx in range(-int_rx, int_rx + 1):
            for dz in range(-int_rz, int_rz + 1):
                # 椭圆判定 + 噪声扰动
                ex = dx / layer_rx if layer_rx > 0 else 999
                ez = dz / layer_rz if layer_rz > 0 else 999
                dist_sq = ex * ex + ez * ez

                # 边界噪声
                angle = math.atan2(dz, dx)
                noise = noise_amp * math.sin(angle * 5 + dy * 0.3)
                threshold = 1.0 + noise

                if dist_sq <= threshold * threshold:
                    bx = cx + dx
                    bz = cz + dz

                    # 选材质
                    block = rng.choice(block_choices)

                    # 只有最外层顶面用 grass，内部填 dirt/stone
                    if y_ratio < 0.3:
                        # 山脚层: 顶面 grass, 内部 dirt
                        # 检查上方是否还有方块 (简单近似: 上一层同位置是否在椭圆内)
                        next_layer_factor = math.sqrt(max(0, 1.0 - ((dy + 1) / height) ** 2))
                        next_rx = rx * next_layer_factor
                        next_rz = rz * next_layer_factor
                        if next_rx > 0.5 and next_rz > 0.5:
                            nex = dx / next_rx
                            nez = dz / next_rz
                            if nex * nex + nez * nez <= 1.0:
                                block = PALETTE["dirt"]
                            # else: 这是露出的表面，用 grass
                    else:
                        # 山腰山顶: 表面用选定的石头，内部填 stone
                        next_layer_factor = math.sqrt(max(0, 1.0 - ((dy + 1) / height) ** 2))
                        next_rx = rx * next_layer_factor
                        next_rz = rz * next_layer_factor
                        if next_rx > 0.5 and next_rz > 0.5:
                            nex = dx / next_rx
                            nez = dz / next_rz
                            if nex * nex + nez * nez <= 1.0:
                                block = PALETTE["stone"]

                    b.setblock(bx, y, bz, block)

    print(f"    {name} 完成: {b.cmd_count - cmd_before} commands")


def _build_mountains(b: MinecraftBuilder, rng: random.Random):
    """建造远山 (1大1小)"""
    print("  [3/4] 远山...")
    cmd_before = b.cmd_count

    # 先铺山区地基 (X=155~180 的 dirt 和 grass 层已在 main 中完成)
    _build_mountain(b, BIG_MOUNTAIN, rng, "大山")
    _build_mountain(b, SMALL_MOUNTAIN, rng, "小山")

    # 山脚种树 (大山脚下)
    tree_positions = [
        (150, 30), (152, 50), (148, 55), (155, 25),
        (153, 60), (149, 38), (156, 48),
    ]
    for tx, tz in tree_positions:
        _build_oak_tree(b, tx, tz, rng)

    print(f"    远山总计: {b.cmd_count - cmd_before} commands")


def _build_oak_tree(b: MinecraftBuilder, x: int, z: int, rng: random.Random):
    """在坡面上种一棵橡树"""
    # 获取该位置的地面高度 (简单近似: 用坡面公式)
    base_y = _slope_height(x, z, rng)
    if base_y <= GROUND_Y:
        base_y = GROUND_Y

    trunk_h = rng.randint(4, 6)
    y_start = base_y + 1  # 草方块上方

    # 树干
    for dy in range(trunk_h):
        b.setblock(x, y_start + dy, z, PALETTE["oak_log"])

    # 树冠 (简单球形)
    crown_y = y_start + trunk_h
    crown_r = rng.randint(2, 3)
    for dy in range(-1, crown_r + 1):
        r = crown_r if dy < crown_r - 1 else crown_r - 1
        if dy == -1:
            r = crown_r - 1
        for dx in range(-r, r + 1):
            for dz in range(-r, r + 1):
                if dx * dx + dz * dz <= r * r + 1:
                    if rng.random() < 0.85:  # 边缘随机缺口
                        b.setblock(x + dx, crown_y + dy, z + dz,
                                   PALETTE["oak_leaves"])


# ── 4. 月洞门外小庭 ──

def _build_moon_gate_courtyard(b: MinecraftBuilder, rng: random.Random):
    """月洞门 (X=120, Z=45) 外面的小庭院

    X=121~124, Z=43~47
    石砖地面 + 小松树 + 石凳
    """
    print("  [4/4] 月洞门外小庭...")
    cmd_before = b.cmd_count

    # 石砖地面
    b.fill(121, GROUND_Y, 43, 124, GROUND_Y, 47, PALETTE["base"])

    # 小松树 @ (123, 44)
    tree_x, tree_z = 123, 44
    tree_base_y = GROUND_Y + 1

    # 树干 (3格高)
    for dy in range(4):
        b.setblock(tree_x, tree_base_y + dy, tree_z, "minecraft:spruce_log")

    # 树冠 (锥形，从宽到窄)
    crown_layers = [
        (1, 2),   # dy_offset=1, radius=2
        (2, 2),   # dy_offset=2, radius=2
        (3, 1),   # dy_offset=3, radius=1
        (4, 1),   # dy_offset=4, radius=1
        (5, 0),   # dy_offset=5, 顶部单格
    ]
    for dy_off, r in crown_layers:
        y = tree_base_y + dy_off
        if r == 0:
            b.setblock(tree_x, y, tree_z, "minecraft:spruce_leaves")
        else:
            for dx in range(-r, r + 1):
                for dz in range(-r, r + 1):
                    if abs(dx) + abs(dz) <= r + 1:
                        if rng.random() < 0.9:
                            b.setblock(tree_x + dx, y, tree_z + dz,
                                       "minecraft:spruce_leaves")

    # 石凳 (石砖楼梯) @ (122, Z=46) 面朝东(facing=east)
    b.setblock(122, GROUND_Y + 1, 46,
               "minecraft:stone_brick_stairs[facing=east,half=bottom]")
    b.setblock(122, GROUND_Y + 1, 47,
               "minecraft:stone_brick_stairs[facing=east,half=bottom]")

    # 苔藓点缀
    b.setblock(124, GROUND_Y, 43, PALETTE["moss"])
    b.setblock(121, GROUND_Y, 47, PALETTE["moss"])

    # 灯笼
    b.setblock(121, GROUND_Y + 1, 43, PALETTE["lantern"])

    print(f"    月洞门外小庭完成: {b.cmd_count - cmd_before} commands")


# ── 主函数 ──

def build_east_landscape(b: MinecraftBuilder):
    print("=== 东面竹林坡地 ===")
    random.seed(400)
    rng = random.Random(400)

    # 1. 缓坡
    height_map = _build_slope(b, rng)

    # 2. 竹林
    _build_bamboo_forest(b, height_map, rng)

    # 3. 远山
    _build_mountains(b, rng)

    # 4. 月洞门外小庭
    _build_moon_gate_courtyard(b, rng)

    # 注册边界框
    b.register_bbox("east_slope", SLOPE_X_MIN, GROUND_Y, SLOPE_Z_MIN,
                     SLOPE_X_MAX, GROUND_Y + 6, SLOPE_Z_MAX)
    b.register_bbox("east_bamboo", BAMBOO_X_MIN, GROUND_Y, BAMBOO_Z_MIN,
                     BAMBOO_X_MAX, GROUND_Y + 15, BAMBOO_Z_MAX)
    b.register_bbox("east_mountains", 145, GROUND_Y, 10,
                     190, GROUND_Y + 35, 90)
    b.register_bbox("east_courtyard", 121, GROUND_Y, 43, 124, GROUND_Y + 6, 47)

    print("=== 东面景观完成 ===")


if __name__ == "__main__":
    with MinecraftBuilder() as b:
        # 先铺地面基底
        b.fill(122, -63, 0, 180, -63, 90, PALETTE['dirt'])
        b.fill(122, -62, 0, 180, -62, 90, PALETTE['dirt'])
        b.fill(122, GROUND_Y, 0, 180, GROUND_Y, 90, PALETTE['grass'])
        build_east_landscape(b)
        print(f"Done! {b.cmd_count} commands")
