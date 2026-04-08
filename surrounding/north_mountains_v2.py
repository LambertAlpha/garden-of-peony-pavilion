"""北面青山 v2 — 高效版（fill 优先，目标 <3000 命令）

重写原因：v1 用 _scatter_replace 逐块 setblock 替换材质，
单座山 40 层 x 60 setblock = 2400 命令，7 座山总计超 9000 条导致 RCON 超时崩溃。

优化策略：
1. 每层椭圆按 Z 行扫描，一条 fill 搞定一行（不再逐点 setblock）
2. 材质变化用 fill ... replace 按区域批量替换，不用 setblock 散布
3. 减为 3 座山（主峰 + 2 副峰），不再精细建模小丘
4. 树木精简到每山 3-5 棵
"""

import sys
sys.path.insert(0, '/Users/lambertlin/minecraft-server/scripts')
from builder import MinecraftBuilder
from blocks import GROUND_Y
import random
import math


# ── 材质分层配置 ──
# 每层只用 fill 铺主材质，再用 1-2 条 fill replace 加次要材质
# 绝不使用 setblock 做材质散布

LAYER_MATERIALS = {
    # (progress_min, progress_max): (primary, [(secondary, replace_chance)])
    "foot":  ("minecraft:grass_block",  [("minecraft:coarse_dirt", 0.20)]),
    "lower": ("minecraft:stone",        [("minecraft:andesite", 0.30),
                                          ("minecraft:mossy_cobblestone", 0.10)]),
    "upper": ("minecraft:stone",        [("minecraft:andesite", 0.25),
                                          ("minecraft:cobblestone", 0.15)]),
    "peak":  ("minecraft:stone",        [("minecraft:andesite", 0.30)]),
}


def _get_layer_zone(progress: float) -> str:
    if progress < 0.3:
        return "foot"
    elif progress < 0.6:
        return "lower"
    elif progress < 0.85:
        return "upper"
    else:
        return "peak"


# ── 简易噪声 ──

def _noise(x: float, z: float, seed: int = 0) -> float:
    """伪随机噪声，返回 -1 ~ 1"""
    n = int(x * 73 + z * 179 + seed * 31) & 0xFFFFFF
    n = (n << 13) ^ n
    return (1.0 - ((n * (n * n * 15731 + 789221) + 1376312589) & 0x7FFFFFFF) / 1073741824.0)


# ── 核心：高效山体建造 ──

def _build_mountain(b: MinecraftBuilder, cx: int, cz: int,
                    base_y: int, height: int, rx: int, rz: int,
                    name: str, south_gentle: bool = False):
    """用逐层 fill 行扫描建造一座山

    关键优化：每一层的椭圆截面，按 Z 行扫描，每行一条 fill。
    材质替换用 fill replace 对整层包围盒操作，一条命令替换一种材质。

    参数:
        south_gentle: 如果 True，南面（正 Z 方向）做缓坡
    """
    print(f"  建造 {name}: 中心({cx},{cz}), 高{height}, 半径({rx},{rz})")
    cmd_before = b.cmd_count

    for dy in range(height):
        y = base_y + dy
        progress = dy / height

        # 半径随高度缩小（底宽顶窄）
        taper = 1.0 - progress ** 0.7 * 0.85

        # 南面缓坡：南侧 Z 半径多保留一些
        curr_rx = max(1, int(rx * taper))
        curr_rz = max(1, int(rz * taper))

        if south_gentle and progress > 0.3:
            # 南侧（dz > 0）额外延伸，形成缓坡
            south_bonus = int(rz * 0.3 * (1.0 - progress))
        else:
            south_bonus = 0

        zone = _get_layer_zone(progress)
        primary = LAYER_MATERIALS[zone][0]

        # 记录本层包围盒（用于后续 replace）
        layer_x_min = cx + curr_rx  # 会被更新
        layer_x_max = cx - curr_rx
        layer_z_min = cz + curr_rz
        layer_z_max = cz - curr_rz

        # 按 Z 行扫描椭圆
        z_start = -curr_rz
        z_end = curr_rz + south_bonus

        for dz in range(z_start, z_end + 1):
            # 判断用哪个 rz 来计算椭圆
            if dz > curr_rz:
                # 南面缓坡延伸区域
                effective_rz = curr_rz + south_bonus
            else:
                effective_rz = curr_rz

            if effective_rz == 0:
                frac_z = 0
            else:
                frac_z = (dz / effective_rz) ** 2
            if frac_z > 1.0:
                continue

            half_x = int(curr_rx * math.sqrt(1.0 - frac_z))
            if half_x < 0:
                continue

            # 边缘噪声（轻微，±1 格）
            noise_val = _noise(cx + half_x, cz + dz, dy)
            noise_offset = int(noise_val * 1.5)
            half_x = max(0, half_x + noise_offset)

            x1 = cx - half_x
            x2 = cx + half_x
            z = cz + dz

            if x1 > x2:
                continue

            # 一条 fill 搞定这一行
            b.fill(x1, y, z, x2, y, z, primary)

            # 更新包围盒
            layer_x_min = min(layer_x_min, x1)
            layer_x_max = max(layer_x_max, x2)
            layer_z_min = min(layer_z_min, z)
            layer_z_max = max(layer_z_max, z)

        # 材质替换：对整层包围盒用 fill replace
        # 每种次要材质只需一条命令（Minecraft 会随机替换匹配的方块中的一部分——
        # 不对，replace 会替换所有匹配的。所以我们不能直接用 replace 做概率替换。
        # 改为：只在特定高度段做少量整行替换，用 fill replace 替换小区域）

        # 简化策略：每 3 层做一次材质替换，对包围盒的一小块区域替换
        if dy % 3 == 1 and layer_x_max >= layer_x_min:
            secondaries = LAYER_MATERIALS[zone][1]
            for sec_block, _ in secondaries:
                # 把包围盒分成随机小条带来替换
                # 选 2-3 个随机 Z 行，整行替换为次要材质
                num_strips = min(2, (layer_z_max - layer_z_min + 1) // 3)
                for _ in range(num_strips):
                    rz_pick = random.randint(layer_z_min, layer_z_max)
                    # 替换这一行中的主材质为次要材质
                    b.fill(layer_x_min, y, rz_pick,
                           layer_x_max, y, rz_pick,
                           sec_block, f"replace {primary}")

    cmd_used = b.cmd_count - cmd_before
    print(f"    {name} 完成: {cmd_used} 命令")


# ── 植被（精简版）──

def _place_simple_tree(b: MinecraftBuilder, x: int, y: int, z: int,
                       tree_type: str = "oak"):
    """简易树：树干 + 一层树冠，最多 3 条命令"""
    if tree_type == "oak":
        log = "minecraft:oak_log"
        leaves = "minecraft:oak_leaves"
        trunk_h = random.randint(4, 5)
    else:
        log = "minecraft:spruce_log"
        leaves = "minecraft:spruce_leaves"
        trunk_h = random.randint(5, 6)

    # 树干：1 条 fill
    b.fill(x, y, z, x, y + trunk_h - 1, z, log)
    # 树冠：2 层，每层 1 条 fill
    top = y + trunk_h
    b.fill(x - 2, top, z - 2, x + 2, top, z + 2,
           leaves, "replace minecraft:air")
    b.fill(x - 1, top + 1, z - 1, x + 1, top + 1, z + 1,
           leaves, "replace minecraft:air")


def _place_vegetation(b: MinecraftBuilder, cx: int, cz: int,
                      base_y: int, height: int, rx: int, rz: int,
                      name: str):
    """每座山种 3-5 棵树 + 少量花丛"""
    print(f"  种植 {name} 植被...")

    # 山脚橡树 3-4 棵
    num_oaks = random.randint(3, 4)
    for _ in range(num_oaks):
        angle = random.uniform(0, 2 * math.pi)
        r_frac = random.uniform(0.5, 0.9)
        dy = random.randint(0, int(height * 0.2))
        taper = 1.0 - (dy / height) ** 0.7 * 0.85
        tx = int(cx + rx * taper * r_frac * math.cos(angle))
        tz = int(cz + rz * taper * r_frac * math.sin(angle))
        ty = base_y + dy + 1
        _place_simple_tree(b, tx, ty, tz, "oak")

    # 山腰云杉 1-2 棵
    if height >= 20:
        num_spruce = random.randint(1, 2)
        for _ in range(num_spruce):
            angle = random.uniform(0, 2 * math.pi)
            r_frac = random.uniform(0.3, 0.6)
            dy = random.randint(int(height * 0.3), int(height * 0.5))
            taper = 1.0 - (dy / height) ** 0.7 * 0.85
            sx = int(cx + rx * taper * r_frac * math.cos(angle))
            sz = int(cz + rz * taper * r_frac * math.sin(angle))
            sy = base_y + dy + 1
            _place_simple_tree(b, sx, sy, sz, "spruce")

    # 山脚花丛 2-3 个（每个 1 条 setblock，可以接受）
    for _ in range(random.randint(2, 3)):
        angle = random.uniform(0, 2 * math.pi)
        r_frac = random.uniform(0.6, 0.95)
        fx = int(cx + rx * 0.9 * r_frac * math.cos(angle))
        fz = int(cz + rz * 0.9 * r_frac * math.sin(angle))
        b.setblock(fx, base_y + 1, fz, "minecraft:flowering_azalea")


# ── 山间溪流（精简版）──

def _build_stream(b: MinecraftBuilder, base_y: int):
    """主峰与副峰1之间的小溪，用 fill 段落而非逐点"""
    print("  建造山间溪流...")

    # 溪流分 5 段，每段一条 fill 水 + 一条 fill 溪床 = 10 命令
    segments = [
        # (x1, z1, x2, z2, y_offset) — 每段一个矩形
        (33, -32, 35, -28, 8),
        (31, -27, 34, -23, 6),
        (30, -22, 33, -18, 4),
        (29, -17, 32, -13, 2),
        (28, -12, 31, -8,  0),
    ]

    for x1, z1, x2, z2, dy in segments:
        y = base_y + dy
        # 溪床
        b.fill(x1 - 1, y - 1, z1, x2 + 1, y - 1, z2, "minecraft:mossy_cobblestone")
        # 水面
        b.fill(x1, y, z1, x2, y, z2, "minecraft:water")


# ── 主函数 ──

def build_north_mountains(b: MinecraftBuilder):
    print("=== 北面青山 v2 ===")
    random.seed(200)

    base_y = GROUND_Y  # -61

    # 注册边界框以便撤销
    b.register_bbox("north_mountains", -10, base_y, -70, 130, base_y + 40, 0)

    # ── 1) 主峰 ──
    print("\n[1/3] 主峰")
    _build_mountain(b, cx=50, cz=-40, base_y=base_y,
                    height=35, rx=18, rz=13, name="主峰",
                    south_gentle=True)
    _place_vegetation(b, cx=50, cz=-40, base_y=base_y,
                      height=35, rx=18, rz=13, name="主峰")

    # ── 2) 副峰1（西侧）──
    print("\n[2/3] 副峰1")
    _build_mountain(b, cx=20, cz=-30, base_y=base_y,
                    height=20, rx=12, rz=10, name="副峰1")
    _place_vegetation(b, cx=20, cz=-30, base_y=base_y,
                      height=20, rx=12, rz=10, name="副峰1")

    # ── 3) 副峰2（东侧）──
    print("\n[3/3] 副峰2")
    _build_mountain(b, cx=90, cz=-35, base_y=base_y,
                    height=25, rx=15, rz=11, name="副峰2")
    _place_vegetation(b, cx=90, cz=-35, base_y=base_y,
                      height=25, rx=15, rz=11, name="副峰2")

    # ── 4) 山间溪流 ──
    print("\n[4] 溪流")
    _build_stream(b, base_y)

    # ── 5) 山脚苔藓带（用 fill 而非逐点 setblock）──
    print("\n[5] 山脚苔藓带")
    # 几条苔藓带，每条一个 fill
    moss_strips = [
        (10, -12, 45, -8),
        (55, -10, 85, -7),
        (90, -11, 115, -9),
    ]
    for x1, z1, x2, z2 in moss_strips:
        b.fill(x1, base_y, z1, x2, base_y, z2, "minecraft:moss_block")
        b.fill(x1, base_y + 1, z1, x2, base_y + 1, z2,
               "minecraft:moss_carpet", "replace minecraft:air")

    print("\n=== 北面青山 v2 完成 ===")


if __name__ == "__main__":
    with MinecraftBuilder() as b:
        # 先铺地面
        b.fill(-10, -63, -70, 130, -63, -1, 'minecraft:dirt')
        b.fill(-10, -62, -70, 130, -62, -1, 'minecraft:dirt')
        b.fill(-10, -61, -70, 130, -61, -1, 'minecraft:grass_block')
        build_north_mountains(b)
        print(f"Done! {b.cmd_count} commands")
