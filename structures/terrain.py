"""地形塑造 — 北侧山丘 + 池塘预挖

《牡丹亭·游园惊梦》庭院 Phase 1a
园林范围: X: 0~80, Z: 0~60
"""

import sys; sys.path.insert(0, '/Users/lambertlin/minecraft-server/scripts')
from builder import MinecraftBuilder
from blocks import PALETTE, GROUND_Y, BUILD_Y
import math
import random


# ── 高度图生成 ──

def _north_hill_height(x: int, z: int, rng: random.Random) -> int:
    """计算北侧山丘 (x, z) 处的目标 Y 高度。

    设计逻辑：
    - Z 方向渐变：Z=0 最高，Z=18 与地面齐平
    - X 方向分区：西侧(20-30)最高（太湖石区），中部过渡，东侧(45-65)中等高度（牡丹亭区）
    - 随机偏移：+/- 1~2 格，制造自然不规则感
    """
    # Z 方向的基础渐变系数: Z=0 → 1.0, Z=18 → 0.0
    z_factor = max(0.0, 1.0 - z / 18.0)

    # X 方向的高度系数：西高东低
    if x <= 30:
        # 太湖石区域 — 最高，6 格
        x_max_rise = 6
    elif x <= 40:
        # 过渡区 — 线性插值从 6 降到 4
        t = (x - 30) / 10.0
        x_max_rise = 6 - 2 * t
    else:
        # 牡丹亭区域 — 中等，4 格
        x_max_rise = 4

    # 基础高度（相对于 GROUND_Y 的抬升量）
    base_rise = x_max_rise * z_factor

    # 边缘软化：X 方向两端渐消
    if x < 25:
        edge = (x - 20) / 5.0  # X=20→0, X=25→1
        base_rise *= max(0.0, edge)
    elif x > 60:
        edge = (65 - x) / 5.0  # X=60→1, X=65→0
        base_rise *= max(0.0, edge)

    # 用 sin 叠加制造丘陵起伏（不是平面斜坡）
    wave = 0.5 * math.sin(x * 0.3) * math.sin(z * 0.4 + 1.0)
    base_rise += wave

    # 随机偏移: -1 ~ +1（山丘中心区域偶尔 +2）
    if base_rise > 2:
        jitter = rng.choice([-1, -1, 0, 0, 0, 1, 1, 2])
    elif base_rise > 0.5:
        jitter = rng.choice([-1, 0, 0, 0, 1])
    else:
        jitter = 0

    final_rise = max(0, round(base_rise + jitter))
    return GROUND_Y + final_rise  # 返回绝对 Y 坐标


# ── 池塘椭圆判断 ──

def _in_pond(x: int, z: int, rng: random.Random) -> bool:
    """判断 (x, z) 是否在不规则椭圆池塘内。

    池塘近似范围: X: 18~55, Z: 20~38
    椭圆中心: (36.5, 29)  半长轴 a=18.5(X), 半短轴 b=9(Z)
    加 Perlin-like 噪声扰动边界，让形状不规则。
    """
    cx, cz = 36.5, 29.0
    a, b = 17.0, 8.0  # 略小于范围，留岸线余量

    # 基础椭圆距离
    dx = (x - cx) / a
    dz = (z - cz) / b
    dist_sq = dx * dx + dz * dz

    # 用角度相关的 sin 叠加扰动边界半径（模拟不规则形状）
    angle = math.atan2(z - cz, x - cx)
    # 多频叠加
    noise = (0.08 * math.sin(angle * 3 + 0.5)
             + 0.06 * math.sin(angle * 5 + 1.2)
             + 0.04 * math.sin(angle * 7 + 2.8))

    threshold = 1.0 + noise
    return dist_sq < threshold * threshold


# ── 主构建函数 ──

def build_terrain(b: MinecraftBuilder):
    print("=== Phase 1a: 地形塑造 ===")
    rng = random.Random(42)

    # ──────────────────────────────────────
    # 1. 北侧高地 (X: 20~65, Z: 0~18)
    # ──────────────────────────────────────
    print("  [1/2] 北侧山丘...")

    # 策略：按 X 列批量 fill，每列从 GROUND_Y 到目标高度填 dirt，
    # 顶层替换为 grass_block。比逐块 setblock 快几十倍。
    # 先按 X 分组：相邻 X 列如果同高度可以合并成一个 fill。

    # 生成高度图
    height_map = {}  # (x, z) -> target_y
    for x in range(20, 66):
        for z in range(0, 19):
            target_y = _north_hill_height(x, z, rng)
            if target_y > GROUND_Y:
                height_map[(x, z)] = target_y

    # 按 X 列填充：每列(x, z)从 GROUND_Y+1 到 target_y 填 dirt
    # 然后顶层放 grass_block
    # 为了用 fill 而非 setblock，我们对每个 x 按 z 扫描，
    # 把连续 z 且同高度的合并成一条 fill
    cmd_before = b.cmd_count

    for x in range(20, 66):
        z = 0
        while z < 19:
            if (x, z) not in height_map:
                z += 1
                continue

            # 找连续 z 段（同高度可合并）
            target_y = height_map[(x, z)]
            z_start = z
            z_end = z
            while z_end + 1 < 19 and height_map.get((x, z_end + 1)) == target_y:
                z_end += 1

            # fill dirt 柱: GROUND_Y 到 target_y - 1（内部用 dirt）
            if target_y - 1 >= GROUND_Y:
                b.fill(x, GROUND_Y, z_start,
                       x, target_y - 1, z_end,
                       PALETTE["dirt"])

            # fill grass_block 顶层
            b.fill(x, target_y, z_start,
                   x, target_y, z_end,
                   PALETTE["grass"])

            z = z_end + 1

    print(f"    北侧山丘完成: {b.cmd_count - cmd_before} commands")

    # ──────────────────────────────────────
    # 2. 池塘预挖 (大约 X: 18~55, Z: 20~38)
    # ──────────────────────────────────────
    print("  [2/2] 池塘预挖...")
    cmd_before = b.cmd_count

    # 策略：按 Z 行扫描，对每行找出连续在椭圆内的 X 段，
    # 用 fill 批量挖掘（填 air 到 GROUND_Y，底层填 clay）

    pond_depth_y = -63  # 挖到 y=-63（深 2 格）

    for z in range(18, 40):  # 略宽于预期范围，让椭圆公式自己裁剪
        x = 16
        while x < 57:
            if not _in_pond(x, z, rng):
                x += 1
                continue

            # 找连续 X 段
            x_start = x
            while x + 1 < 57 and _in_pond(x + 1, z, rng):
                x += 1
            x_end = x

            # 挖空: 从 pond_depth_y+1 到 GROUND_Y 填 air
            # （GROUND_Y 是草方块层，也要挖掉）
            b.fill(x_start, pond_depth_y + 1, z,
                   x_end, GROUND_Y, z,
                   PALETTE["air"])

            # 池底铺 clay (y = pond_depth_y)
            b.fill(x_start, pond_depth_y, z,
                   x_end, pond_depth_y, z,
                   PALETTE["clay"])

            x = x_end + 1

    print(f"    池塘预挖完成: {b.cmd_count - cmd_before} commands")

    # ── 注册 bounding boxes ──
    b.register_bbox("terrain_north", 20, GROUND_Y, 0, 65, -55, 18)
    b.register_bbox("terrain_pond", 18, -63, 20, 55, GROUND_Y, 38)

    print("=== Phase 1a 完成 ===")


if __name__ == "__main__":
    with MinecraftBuilder() as b:
        # 先传送玩家到概览位置
        b.tp_player("LambertLin", 40, -45, 30)
        build_terrain(b)
        print(f"Done! Total commands: {b.cmd_count}")
