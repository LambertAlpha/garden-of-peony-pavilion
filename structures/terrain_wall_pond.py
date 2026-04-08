"""v3 地形 + 池塘 + 围墙 合并脚本

牡丹亭·游园惊梦 — 明代知府后花园
园林范围: X:0~120, Z:0~90（从 config 读取）

v2→v3 变更:
- 园林范围 80×60 → 120×90
- 围墙高度 4→5（墙基1+墙身3+压瓦1）
- 月洞门半径 2→3（净空 5×5）
- 南墙入口缺口 15格
- 北侧高地范围扩大到 X:30~90, Z:0~25
- 池塘参数从 config.POND 读取
- 围墙用 fill 批量操作
"""

import sys; sys.path.insert(0, '/Users/lambertlin/minecraft-server/scripts')
from builder import MinecraftBuilder, filled_circle_points
from blocks import PALETTE, GROUND_Y, BUILD_Y
from config import *
import random
import math


# ══════════════════════════════════════════════════════════════
# 1. 地形塑造
# ══════════════════════════════════════════════════════════════

def _north_hill_height(x, z, rng):
    """北侧高地 (X:30~90, Z:0~25) 的高度图。

    设计:
    - Z方向渐变: Z=0 最高, Z=25 与地面齐平
    - X方向分区: 西侧太湖石区(30~50)最高约6格,
      东侧牡丹亭区(65~90)中等约4格, 中间过渡
    - sin波叠加 + 随机抖动 → 自然起伏
    返回绝对 Y 坐标。
    """
    # Z 方向渐变: Z=0 → 1.0, Z=25 → 0.0
    z_factor = max(0.0, 1.0 - z / 25.0)

    # X 方向高度系数
    if x <= 50:
        # 太湖石区 — 最高 6 格
        x_max_rise = 6
    elif x <= 65:
        # 过渡区 — 6 线性降到 4
        t = (x - 50) / 15.0
        x_max_rise = 6 - 2 * t
    else:
        # 牡丹亭区 — 4 格
        x_max_rise = 4

    base_rise = x_max_rise * z_factor

    # X 方向边缘软化
    if x < 35:
        edge = (x - 30) / 5.0  # X=30→0, X=35→1
        base_rise *= max(0.0, edge)
    elif x > 85:
        edge = (90 - x) / 5.0  # X=85→1, X=90→0
        base_rise *= max(0.0, edge)

    # sin 波叠加 — 丘陵起伏
    wave = (0.6 * math.sin(x * 0.25) * math.sin(z * 0.35 + 1.0)
            + 0.3 * math.sin(x * 0.13 + 0.7) * math.sin(z * 0.5 + 0.3))
    base_rise += wave

    # 随机抖动
    if base_rise > 2:
        jitter = rng.choice([-1, -1, 0, 0, 0, 1, 1, 2])
    elif base_rise > 0.5:
        jitter = rng.choice([-1, 0, 0, 0, 1])
    else:
        jitter = 0

    final_rise = max(0, round(base_rise + jitter))
    return GROUND_Y + final_rise


def build_terrain(b):
    """Phase 1a: 北侧高地地形塑造。"""
    print("=== 地形塑造 ===")
    random.seed(42)
    rng = random.Random(42)

    x_min = GARDEN["x_min"]
    x_max = GARDEN["x_max"]

    # 北侧高地: X:30~90, Z:0~25
    hill_x1, hill_x2 = 30, 90
    hill_z1, hill_z2 = 0, 25

    print(f"  北侧高地 X:{hill_x1}~{hill_x2}, Z:{hill_z1}~{hill_z2}...")
    cmd_before = b.cmd_count

    # 生成高度图
    height_map = {}
    for x in range(hill_x1, hill_x2 + 1):
        for z in range(hill_z1, hill_z2 + 1):
            target_y = _north_hill_height(x, z, rng)
            if target_y > GROUND_Y:
                height_map[(x, z)] = target_y

    # 按 X 列 fill: 合并连续同高 Z 段
    for x in range(hill_x1, hill_x2 + 1):
        z = hill_z1
        while z <= hill_z2:
            if (x, z) not in height_map:
                z += 1
                continue

            target_y = height_map[(x, z)]
            z_start = z
            z_end = z
            while z_end + 1 <= hill_z2 and height_map.get((x, z_end + 1)) == target_y:
                z_end += 1

            # 内部 dirt
            if target_y - 1 >= GROUND_Y:
                b.fill(x, GROUND_Y, z_start,
                       x, target_y - 1, z_end,
                       PALETTE["dirt"])
            # 顶层 grass
            b.fill(x, target_y, z_start,
                   x, target_y, z_end,
                   PALETTE["grass"])

            z = z_end + 1

    print(f"    高地完成: {b.cmd_count - cmd_before} commands")

    b.register_bbox("terrain_north", hill_x1, GROUND_Y, hill_z1,
                    hill_x2, -55, hill_z2)
    print("=== 地形完成 ===")


# ══════════════════════════════════════════════════════════════
# 2. 池塘
# ══════════════════════════════════════════════════════════════

def _in_pond(x, z, cx, cz, rx, rz):
    """不规则椭圆池塘边界判断。

    多频 sin 扰动边界，制造自然不规则形状。
    """
    # 缩小半轴留出岸线余量 (2格)
    a = rx - 2
    b = rz - 2

    dx = (x - cx) / a
    dz = (z - cz) / b
    dist_sq = dx * dx + dz * dz

    # 角度相关多频 sin 扰动
    angle = math.atan2(z - cz, x - cx)
    noise = (0.08 * math.sin(angle * 3 + 0.5)
             + 0.06 * math.sin(angle * 5 + 1.2)
             + 0.04 * math.sin(angle * 7 + 2.8)
             + 0.03 * math.sin(angle * 11 + 3.5))

    threshold = 1.0 + noise
    return dist_sq < threshold * threshold


def build_pond(b):
    """Phase 1b: 不规则椭圆池塘。"""
    print("=== 池塘 ===")
    random.seed(42)
    rng = random.Random(42)

    cx = POND["cx"]       # 52
    cz = POND["cz"]       # 45
    rx = POND["rx"]       # 23
    rz = POND["rz"]       # 12
    depth = POND["depth"]  # 3

    pond_bottom_y = GROUND_Y - depth  # -61 - 3 = -64
    water_top_y = GROUND_Y            # -61 (水面与地面齐平)

    # 扫描范围 (椭圆外接矩形 + 余量)
    scan_x1 = cx - rx - 2
    scan_x2 = cx + rx + 2
    scan_z1 = cz - rz - 2
    scan_z2 = cz + rz + 2

    print(f"  池塘中心 ({cx},{cz}), 半轴 rx={rx} rz={rz}")
    cmd_before = b.cmd_count

    # 记录池塘内坐标 (用于放睡莲)
    pond_surface = []

    for z in range(scan_z1, scan_z2 + 1):
        x = scan_x1
        while x <= scan_x2:
            if not _in_pond(x, z, cx, cz, rx, rz):
                x += 1
                continue

            # 找连续 X 段
            x_start = x
            while x + 1 <= scan_x2 and _in_pond(x + 1, z, cx, cz, rx, rz):
                x += 1
            x_end = x

            # 挖空: pond_bottom_y+1 到 GROUND_Y 填 air
            b.fill(x_start, pond_bottom_y + 1, z,
                   x_end, GROUND_Y, z,
                   PALETTE["air"])

            # 池底铺 clay
            b.fill(x_start, pond_bottom_y, z,
                   x_end, pond_bottom_y, z,
                   PALETTE["clay"])

            # 填水: pond_bottom_y+1 到 water_top_y
            b.fill(x_start, pond_bottom_y + 1, z,
                   x_end, water_top_y, z,
                   PALETTE["water"])

            # 记录水面坐标
            for px in range(x_start, x_end + 1):
                pond_surface.append((px, z))

            x = x_end + 1

    # 随机 6% 放睡莲
    print("  睡莲...")
    for px, pz in pond_surface:
        if rng.random() < 0.06:
            b.setblock(px, water_top_y + 1, pz, PALETTE["lily"])

    print(f"    池塘完成: {b.cmd_count - cmd_before} commands")

    b.register_bbox("pond", scan_x1, pond_bottom_y, scan_z1,
                    scan_x2, water_top_y + 1, scan_z2)
    print("=== 池塘完成 ===")


# ══════════════════════════════════════════════════════════════
# 3. 围墙
# ══════════════════════════════════════════════════════════════

def _north_terrain_y(x):
    """北墙(Z=0)地形高度 — 用二次曲线近似高地轮廓。

    X:30~90 隆起, 两端平地 BUILD_Y, 中间最高约 -55。
    """
    peak_y = -55
    base_y = BUILD_Y  # -60

    # 高地范围 X:30~90, 中心 x=60
    hill_cx = 60
    hill_half = 30  # 半宽

    if x < 30 or x > 90:
        return base_y

    rise = peak_y - base_y  # 5
    t = (x - hill_cx) / hill_half  # -1 ~ 1
    y = base_y + rise * (1 - t * t)

    # 西侧(太湖石)略高
    if x <= 50:
        y += 1

    return int(round(min(y, peak_y)))


def build_walls(b):
    """Phase 1c: 围墙（粉墙黛瓦，漏窗月洞）。

    高度5格: 墙基1(stone_bricks) + 墙身3(white_concrete) + 压瓦1(stone_brick_slab)
    """
    print("=== 围墙 ===")
    random.seed(42)
    rng = random.Random(42)

    x_min = GARDEN["x_min"]   # 0
    x_max = GARDEN["x_max"]   # 120
    z_min = GARDEN["z_min"]   # 0
    z_max = GARDEN["z_max"]   # 90

    wall_h = WALL["height"]           # 5
    moon_r = WALL["moon_gate_radius"]  # 3
    moon_z = WALL["moon_gate_pos"]     # 45
    gap_x1, gap_x2 = WALL["south_gap"]  # (48, 62)

    base_block = PALETTE["wall_base"]    # stone_bricks
    wall_block = PALETTE["wall"]         # white_concrete
    cap_block = PALETTE["wall_cap"]      # stone_brick_slab

    # ── 南墙 (Z=z_max) ──
    print(f"  南墙 (Z={z_max}), 入口缺口 X:{gap_x1}~{gap_x2}...")
    # 西段: x_min ~ gap_x1-1
    if gap_x1 > x_min:
        _fill_wall_segment(b, x_min, z_max, gap_x1 - 1, z_max,
                           BUILD_Y, base_block, wall_block, cap_block)
    # 东段: gap_x2+1 ~ x_max
    if gap_x2 < x_max:
        _fill_wall_segment(b, gap_x2 + 1, z_max, x_max, z_max,
                           BUILD_Y, base_block, wall_block, cap_block)

    # ── 北墙 (Z=z_min) — 跟随地形 ──
    print(f"  北墙 (Z={z_min}), 跟随地形...")
    # 北墙地形起伏，按 X 分段: 找连续同 base_y 的段 fill
    x = x_min
    while x <= x_max:
        base_y = _north_terrain_y(x)
        x_start = x
        while x + 1 <= x_max and _north_terrain_y(x + 1) == base_y:
            x += 1
        x_end = x

        _fill_wall_segment(b, x_start, z_min, x_end, z_min,
                           base_y, base_block, wall_block, cap_block)
        x = x_end + 1

    # ── 西墙 (X=x_min) ──
    print(f"  西墙 (X={x_min})...")
    _fill_wall_segment(b, x_min, z_min, x_min, z_max,
                       BUILD_Y, base_block, wall_block, cap_block)

    # ── 东墙 (X=x_max) ──
    print(f"  东墙 (X={x_max})...")
    _fill_wall_segment(b, x_max, z_min, x_max, z_max,
                       BUILD_Y, base_block, wall_block, cap_block)

    # ── 月洞门 (东墙 X=x_max, Z=moon_z) ──
    print(f"  月洞门 (东墙 Z={moon_z}, 半径{moon_r})...")
    _build_moon_gate(b, x_max, moon_z, moon_r)

    # ── 漏窗 ──
    print("  漏窗...")
    _build_leak_windows(b, x_min, x_max, z_min, z_max,
                        gap_x1, gap_x2, moon_z, moon_r)

    # ── 做旧 ──
    print("  做旧效果...")
    _apply_weathering(b, rng, x_min, x_max, z_min, z_max, gap_x1, gap_x2)

    # 注册边界框: 最高处北墙顶 = -55 + 4 = -51
    b.register_bbox("walls",
                    x_min, GROUND_Y - 1, z_min,
                    x_max, -51, z_max)

    print("=== 围墙完成 ===")


def _fill_wall_segment(b, x1, z1, x2, z2, base_y,
                       base_block, wall_block, cap_block):
    """用 fill 批量建造一段墙 (5格高)。

    base_y:   墙基 Y
    base_y+1 ~ base_y+3: 墙身 (3格)
    base_y+4: 压瓦
    """
    # 墙基 (1格)
    b.fill(x1, base_y, z1, x2, base_y, z2, base_block)
    # 墙身 (3格)
    b.fill(x1, base_y + 1, z1, x2, base_y + 3, z2, wall_block)
    # 压瓦 (1格)
    b.fill(x1, base_y + 4, z1, x2, base_y + 4, z2, cap_block)


def _build_moon_gate(b, wall_x, center_z, radius):
    """在东墙开月洞门 (YZ 平面圆, 半径3 → 直径7)。

    圆心: Y = BUILD_Y + radius (使底部齐地面), Z = center_z
    先用 filled_circle 清空, 再画圆框装饰。
    """
    # 圆心 Y: 底部刚好在地面
    cy = BUILD_Y + radius  # -60 + 3 = -57
    cz = center_z

    # 清空圆内 (含圆上) → 通道
    for dy, dz in filled_circle_points(cy, cz, radius):
        b.setblock(wall_x, dy, dz, PALETTE["air"])

    # 圆框装饰 (用墙基材质)
    b.circle_yz(wall_x, cy, cz, radius, PALETTE["wall_base"])

    # 再次清空内部 (radius-1), 确保通道干净
    for dy, dz in filled_circle_points(cy, cz, radius - 1):
        b.setblock(wall_x, dy, dz, PALETTE["air"])

    # 确保地面层清空 (可走过)
    for dz_off in range(-radius, radius + 1):
        b.setblock(wall_x, BUILD_Y, cz + dz_off, PALETTE["air"])


def _build_leak_windows(b, x_min, x_max, z_min, z_max,
                        gap_x1, gap_x2, moon_z, moon_r):
    """四面墙漏窗: 每面长墙 3~4 个, 宽3格, 用 iron_bars。

    漏窗位于墙身第 2~3 层 (base_y+2, base_y+3), 高2格宽3格。
    """
    window_block = PALETTE["window"]  # iron_bars

    # ── 南墙 (Z=z_max, 沿X轴): 4个, 避开入口缺口 ──
    south_positions = _distribute_windows(x_min + 3, gap_x1 - 5, 2)  # 西半段 2个
    south_positions += _distribute_windows(gap_x2 + 5, x_max - 3, 2)  # 东半段 2个
    for wx in south_positions:
        for dx in range(3):
            b.setblock(wx + dx, BUILD_Y + 2, z_max, window_block)
            b.setblock(wx + dx, BUILD_Y + 3, z_max, window_block)

    # ── 北墙 (Z=z_min, 沿X轴): 3个, 选平坦区段 ──
    # X:0~29 和 X:91~120 是平地, 适合开窗
    north_positions = [5, 15, 100]
    for wx in north_positions:
        local_base_y = _north_terrain_y(wx + 1)
        for dx in range(3):
            b.setblock(wx + dx, local_base_y + 2, z_min, window_block)
            b.setblock(wx + dx, local_base_y + 3, z_min, window_block)

    # ── 西墙 (X=x_min, 沿Z轴): 4个 ──
    west_positions = _distribute_windows(z_min + 5, z_max - 5, 4)
    for wz in west_positions:
        for dz in range(3):
            b.setblock(x_min, BUILD_Y + 2, wz + dz, window_block)
            b.setblock(x_min, BUILD_Y + 3, wz + dz, window_block)

    # ── 东墙 (X=x_max, 沿Z轴): 3个, 避开月洞门 ──
    east_candidates = _distribute_windows(z_min + 5, z_max - 5, 5)
    east_positions = [p for p in east_candidates
                      if abs(p + 1 - moon_z) > moon_r + 3][:3]
    for wz in east_positions:
        for dz in range(3):
            b.setblock(x_max, BUILD_Y + 2, wz + dz, window_block)
            b.setblock(x_max, BUILD_Y + 3, wz + dz, window_block)


def _distribute_windows(start, end, count):
    """在 [start, end] 范围内均匀分布 count 个漏窗起始坐标。"""
    if count <= 0 or end - start < 3:
        return []
    span = end - start - 3  # 减去漏窗宽度
    if count == 1:
        return [start + span // 2]
    step = span / (count - 1)
    return [int(start + i * step) for i in range(count)]


def _apply_weathering(b, rng, x_min, x_max, z_min, z_max, gap_x1, gap_x2):
    """做旧: 10% mossy + 5% cracked 替换白墙, 8% 藤蔓。"""
    mossy_block = PALETTE["wall_mossy"]
    cracked_block = PALETTE["wall_cracked"]

    # 收集所有墙身白墙坐标 (base_y+1 ~ base_y+3)
    wall_coords = []

    # 南墙 (跳过入口)
    for x in range(x_min, x_max + 1):
        if gap_x1 <= x <= gap_x2:
            continue
        for dy in range(1, 4):
            wall_coords.append((x, BUILD_Y + dy, z_max, "north"))

    # 北墙
    for x in range(x_min, x_max + 1):
        base_y = _north_terrain_y(x)
        for dy in range(1, 4):
            wall_coords.append((x, base_y + dy, z_min, "south"))

    # 西墙
    for z in range(z_min, z_max + 1):
        for dy in range(1, 4):
            wall_coords.append((x_min, BUILD_Y + dy, z, "east"))

    # 东墙
    for z in range(z_min, z_max + 1):
        for dy in range(1, 4):
            wall_coords.append((x_max, BUILD_Y + dy, z, "west"))

    # 替换: 10% mossy, 5% cracked
    for x, y, z, side in wall_coords:
        roll = rng.random()
        if roll < 0.10:
            b.setblock(x, y, z, mossy_block)
        elif roll < 0.15:
            b.setblock(x, y, z, cracked_block)

    # 藤蔓 (8%, 贴内侧)
    vine = PALETTE["vine"]

    # 南墙内侧 (Z=z_max, 藤蔓在 Z=z_max-1, 朝 south)
    for x in range(x_min + 1, x_max):
        if gap_x1 <= x <= gap_x2:
            continue
        if rng.random() < 0.08:
            b.setblock(x, BUILD_Y + 1, z_max - 1, f'{vine}[south=true]')

    # 北墙内侧 (Z=z_min, 藤蔓在 Z=z_min+1, 朝 north)
    for x in range(x_min + 1, x_max):
        if rng.random() < 0.08:
            base_y = _north_terrain_y(x)
            b.setblock(x, base_y + 1, z_min + 1, f'{vine}[north=true]')

    # 西墙内侧 (X=x_min, 藤蔓在 X=x_min+1, 朝 west)
    for z in range(z_min + 1, z_max):
        if rng.random() < 0.08:
            b.setblock(x_min + 1, BUILD_Y + 1, z, f'{vine}[west=true]')

    # 东墙内侧 (X=x_max, 藤蔓在 X=x_max-1, 朝 east)
    for z in range(z_min + 1, z_max):
        if rng.random() < 0.08:
            b.setblock(x_max - 1, BUILD_Y + 1, z, f'{vine}[east=true]')


# ══════════════════════════════════════════════════════════════
# 主入口
# ══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    with MinecraftBuilder() as b:
        b.tp_player("LambertLin", 60, -40, 45)
        build_terrain(b)
        build_pond(b)
        build_walls(b)
        print(f"Done! {b.cmd_count} commands")
