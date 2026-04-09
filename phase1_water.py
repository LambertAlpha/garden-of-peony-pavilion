"""phase1_water.py — 水面系统建造脚本

牡丹亭·游园惊梦 — v3 水面系统
包含: 主湖(26锚点不规则多边形)、曲水溪流、翠轩前小池、假山深潭、深潭连接溪、北侧高地

坐标直接对应 Minecraft 世界坐标 (config_v3 中 X/Z 即 MC X/Z)
"""

import sys
import math
import random

sys.path.insert(0, '/Users/lambertlin/minecraft-server/scripts')

from builder import MinecraftBuilder
import config_v3 as cfg


# ═══════════════════════════════════════════
# 几何工具
# ═══════════════════════════════════════════

def point_in_polygon(x, z, polygon):
    """Ray casting algorithm — 判断点 (x,z) 是否在多边形内"""
    n = len(polygon)
    inside = False
    j = n - 1
    for i in range(n):
        xi, zi = polygon[i]
        xj, zj = polygon[j]
        if ((zi > z) != (zj > z)) and (x < (xj - xi) * (z - zi) / (zj - zi) + xi):
            inside = not inside
        j = i
    return inside


def polygon_bbox(polygon):
    """返回多边形的包围盒 (x_min, z_min, x_max, z_max)"""
    xs = [p[0] for p in polygon]
    zs = [p[1] for p in polygon]
    return min(xs), min(zs), max(xs), max(zs)


def scanline_x_ranges(z, polygon):
    """对给定 Z 行，找出多边形内的所有 X 连续区间。
    返回 [(x_start, x_end), ...] 的列表。
    """
    x_min, _, x_max, _ = polygon_bbox(polygon)
    ranges = []
    start = None
    for x in range(x_min - 1, x_max + 2):
        if point_in_polygon(x + 0.5, z + 0.5, polygon):
            if start is None:
                start = x
        else:
            if start is not None:
                ranges.append((start, x - 1))
                start = None
    if start is not None:
        ranges.append((start, x_max + 1))
    return ranges


def ellipse_contains(x, z, cx, cz, rx, rz):
    """判断 (x,z) 是否在椭圆 (cx,cz,rx,rz) 内"""
    dx = x - cx
    dz = z - cz
    return (dx * dx) / (rx * rx) + (dz * dz) / (rz * rz) <= 1.0


def lerp_points(p1, p2):
    """在两点间用 Bresenham 插值返回中间的整数格子坐标"""
    x1, z1 = p1
    x2, z2 = p2
    points = []
    dx = abs(x2 - x1)
    dz = abs(z2 - z1)
    sx = 1 if x2 > x1 else -1
    sz = 1 if z2 > z1 else -1
    if dx >= dz:
        if dx == 0:
            return [(x1, z1)]
        err = 0
        x, z = x1, z1
        for _ in range(dx + 1):
            points.append((x, z))
            err += dz
            if 2 * err >= dx:
                z += sz
                err -= dx
            x += sx
    else:
        err = 0
        x, z = x1, z1
        for _ in range(dz + 1):
            points.append((x, z))
            err += dx
            if 2 * err >= dz:
                x += sx
                err -= dz
            z += sz
    return points


def expand_polygon_outline(polygon, inside_set):
    """找到多边形内部格子的外扩1格——即不在 inside_set 中、但与 inside_set 相邻的格子"""
    outline = set()
    for (x, z) in inside_set:
        for dx, dz in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nx, nz = x + dx, z + dz
            if (nx, nz) not in inside_set:
                outline.add((nx, nz))
    return outline


# ═══════════════════════════════════════════
# 1. 北侧高地
# ═══════════════════════════════════════════

def build_highland(b: MinecraftBuilder):
    """北侧假山高地 + 东北假山
    从 config_v3.TERRAIN_ZONES 读取区域，用 dirt+grass_block 堆高。
    """
    print("=== Building Highland ===")

    for zone in cfg.TERRAIN_ZONES:
        if zone["name"] == "标准地面":
            continue  # 标准地面不需要堆高

        x_min, x_max = zone["x_range"]
        z_min, z_max = zone["z_range"]
        target_y = zone["ground_y"]  # e.g. -57

        slope = zone.get("slope")

        for z in range(z_min, z_max + 1):
            # 计算这一行的目标高度
            if slope and slope["z_start"] <= z <= slope["z_end"]:
                # 在缓坡区内，线性插值
                t = (z - slope["z_start"]) / (slope["z_end"] - slope["z_start"])
                row_y = round(slope["y_start"] + t * (slope["y_end"] - slope["y_start"]))
            elif slope and z > slope["z_end"]:
                # 超过缓坡区，用缓坡终点高度
                row_y = slope["y_end"]
            else:
                row_y = target_y

            if row_y <= cfg.GROUND_Y:
                continue  # 不高于地面，不需要堆高

            # 从 GROUND_Y+1 到 row_y 堆高
            # GROUND_Y = -61 是原始草块层，row_y 如 -57 比它高（数值更大）
            # 先把 GROUND_Y 层的草改成 dirt（因为上面要放方块了）
            b.fill(x_min, cfg.GROUND_Y, z, x_max, cfg.GROUND_Y, z,
                   "minecraft:dirt", "replace minecraft:grass_block")

            # 填充 dirt 从 GROUND_Y+1 到 row_y-1
            if row_y - 1 >= cfg.GROUND_Y + 1:
                b.fill(x_min, cfg.GROUND_Y + 1, z, x_max, row_y - 1, z,
                       "minecraft:dirt")

            # 顶层放 grass_block
            b.fill(x_min, row_y, z, x_max, row_y, z,
                   "minecraft:grass_block")

    print(f"  Highland done. Commands so far: {b.cmd_count}")


# ═══════════════════════════════════════════
# 2. 主湖
# ═══════════════════════════════════════════

def build_main_lake(b: MinecraftBuilder):
    """26 锚点不规则主湖，深 3 格。
    按 Z 行扫描，用 fill 批量操作。
    """
    print("=== Building Main Lake ===")
    shoreline = cfg.MAIN_LAKE["shoreline"]
    bottom_y = cfg.MAIN_LAKE["bottom_y"]   # -64
    surface_y = cfg.WATER_SURFACE_Y        # -61

    x_min, z_min, x_max, z_max = polygon_bbox(shoreline)

    # 收集湖内所有格子（用于驳岸计算）
    lake_cells = set()

    # 按 Z 行扫描
    for z in range(z_min, z_max + 1):
        ranges = scanline_x_ranges(z, shoreline)
        for x_start, x_end in ranges:
            # 记录湖内格子
            for x in range(x_start, x_end + 1):
                lake_cells.add((x, z))

            # 挖掉: 从 surface_y 到 bottom_y 全部清空（air），然后填水和 clay
            # Step 1: 挖掉 — 从 bottom_y 到 surface_y 用 air 替换所有方块
            b.fill(x_start, bottom_y, z, x_end, surface_y, z, "minecraft:air")

            # Step 2: 底部铺 clay
            b.fill(x_start, bottom_y, z, x_end, bottom_y, z, "minecraft:clay")

            # Step 3: 填水 — 从 bottom_y+1 到 surface_y
            b.fill(x_start, bottom_y + 1, z, x_end, surface_y, z, "minecraft:water")

    # 驳岸: 湖边外扩 1 格铺石头
    print("  Building shoreline revetment...")
    outline = expand_polygon_outline(shoreline, lake_cells)
    rng = random.Random(42)  # 固定种子，可重复
    for (x, z) in outline:
        # 确保在园林范围内
        if 0 <= x <= 120 and 0 <= z <= 90:
            block = "minecraft:mossy_cobblestone" if rng.random() < 0.4 else "minecraft:cobblestone"
            b.setblock(x, surface_y, z, block)

    print(f"  Main lake done. Commands so far: {b.cmd_count}")


# ═══════════════════════════════════════════
# 3. 曲水溪流
# ═══════════════════════════════════════════

def build_creek(b: MinecraftBuilder):
    """从主湖西北角蜿蜒向西北的溪流。
    沿中心线插值，每格按宽度左右扩展挖深。
    """
    print("=== Building Creek ===")
    centerline = cfg.CREEK["centerline"]
    widths = cfg.CREEK["widths"]
    bottom_y = cfg.CREEK["bottom_y"]   # -63
    surface_y = cfg.WATER_SURFACE_Y    # -61

    creek_cells = set()

    # 在相邻锚点之间插值
    for seg_idx in range(len(centerline) - 1):
        p1 = centerline[seg_idx]
        p2 = centerline[seg_idx + 1]
        w1 = widths[seg_idx]
        w2 = widths[seg_idx + 1]

        interp = lerp_points(p1, p2)
        n = len(interp)
        for i, (cx, cz) in enumerate(interp):
            # 线性插值宽度
            t = i / max(n - 1, 1)
            w = w1 + (w2 - w1) * t
            half_w = int(w / 2)

            for dx in range(-half_w, half_w + 1):
                creek_cells.add((cx + dx, cz))

    # 批量操作: 按 Z 行分组
    z_groups = {}
    for (x, z) in creek_cells:
        z_groups.setdefault(z, []).append(x)

    for z in sorted(z_groups.keys()):
        xs = sorted(z_groups[z])
        # 合并连续 X 区间
        ranges = _merge_ranges(xs)
        for x_start, x_end in ranges:
            # 挖掉
            b.fill(x_start, bottom_y, z, x_end, surface_y, z, "minecraft:air")
            # 底部 clay
            b.fill(x_start, bottom_y, z, x_end, bottom_y, z, "minecraft:clay")
            # 填水
            b.fill(x_start, bottom_y + 1, z, x_end, surface_y, z, "minecraft:water")

    print(f"  Creek done. Commands so far: {b.cmd_count}")


# ═══════════════════════════════════════════
# 4. 翠轩前小池
# ═══════════════════════════════════════════

def build_creek_pool(b: MinecraftBuilder):
    """曲水末端扩大的小椭圆池"""
    print("=== Building Creek Pool ===")
    pool = cfg.CREEK_POOL
    cx, cz = pool["cx"], pool["cz"]
    rx, rz = pool["rx"], pool["rz"]
    bottom_y = pool["bottom_y"]        # -63
    surface_y = cfg.WATER_SURFACE_Y    # -61

    # 按 Z 行扫描椭圆
    for z in range(cz - rz, cz + rz + 1):
        x_start = None
        x_end = None
        for x in range(cx - rx, cx + rx + 1):
            if ellipse_contains(x + 0.5, z + 0.5, cx, cz, rx, rz):
                if x_start is None:
                    x_start = x
                x_end = x
        if x_start is not None:
            # 挖掉
            b.fill(x_start, bottom_y, z, x_end, surface_y, z, "minecraft:air")
            # 底部 clay
            b.fill(x_start, bottom_y, z, x_end, bottom_y, z, "minecraft:clay")
            # 填水
            b.fill(x_start, bottom_y + 1, z, x_end, surface_y, z, "minecraft:water")

    print(f"  Creek pool done. Commands so far: {b.cmd_count}")


# ═══════════════════════════════════════════
# 5. 假山深潭
# ═══════════════════════════════════════════

def build_deep_pool(b: MinecraftBuilder):
    """东北角假山深潭 — 多边形，深 4 格"""
    print("=== Building Deep Pool ===")
    shoreline = cfg.DEEP_POOL["shoreline"]
    bottom_y = cfg.DEEP_POOL["bottom_y"]   # -65
    surface_y = cfg.WATER_SURFACE_Y        # -61

    x_min, z_min, x_max, z_max = polygon_bbox(shoreline)

    for z in range(z_min, z_max + 1):
        ranges = scanline_x_ranges(z, shoreline)
        for x_start, x_end in ranges:
            # 挖掉
            b.fill(x_start, bottom_y, z, x_end, surface_y, z, "minecraft:air")
            # 底部 clay
            b.fill(x_start, bottom_y, z, x_end, bottom_y, z, "minecraft:clay")
            # 填水
            b.fill(x_start, bottom_y + 1, z, x_end, surface_y, z, "minecraft:water")

    print(f"  Deep pool done. Commands so far: {b.cmd_count}")


# ═══════════════════════════════════════════
# 6. 深潭连接溪
# ═══════════════════════════════════════════

def build_pool_creek(b: MinecraftBuilder):
    """从主湖东北角连接到假山深潭的窄溪"""
    print("=== Building Pool Creek ===")
    centerline = cfg.POOL_CREEK["centerline"]
    width = cfg.POOL_CREEK["width"]
    bottom_y = cfg.LAKE_BOTTOM_Y  # -64，与主湖一致（比深潭浅）
    surface_y = cfg.WATER_SURFACE_Y

    creek_cells = set()
    half_w = width // 2

    for seg_idx in range(len(centerline) - 1):
        p1 = centerline[seg_idx]
        p2 = centerline[seg_idx + 1]
        interp = lerp_points(p1, p2)
        for (cx, cz) in interp:
            for dx in range(-half_w, half_w + 1):
                creek_cells.add((cx + dx, cz))
            for dz in range(-half_w, half_w + 1):
                creek_cells.add((cx, cz + dz))

    # 按 Z 行分组
    z_groups = {}
    for (x, z) in creek_cells:
        z_groups.setdefault(z, []).append(x)

    for z in sorted(z_groups.keys()):
        xs = sorted(z_groups[z])
        ranges = _merge_ranges(xs)
        for x_start, x_end in ranges:
            # 使用 -63 作为连接溪底部（介于主湖 -64 和深潭 -65 之间）
            b.fill(x_start, -63, z, x_end, surface_y, z, "minecraft:air")
            b.fill(x_start, -63, z, x_end, -63, z, "minecraft:clay")
            b.fill(x_start, -62, z, x_end, surface_y, z, "minecraft:water")

    print(f"  Pool creek done. Commands so far: {b.cmd_count}")


# ═══════════════════════════════════════════
# 辅助函数
# ═══════════════════════════════════════════

def _merge_ranges(xs):
    """将一组 X 坐标合并成连续区间 [(start, end), ...]"""
    if not xs:
        return []
    xs = sorted(set(xs))
    ranges = []
    start = xs[0]
    end = xs[0]
    for x in xs[1:]:
        if x == end + 1:
            end = x
        else:
            ranges.append((start, end))
            start = x
            end = x
    ranges.append((start, end))
    return ranges


# ═══════════════════════════════════════════
# 主入口
# ═══════════════════════════════════════════

if __name__ == "__main__":
    with MinecraftBuilder() as b:
        b.tp_player("LambertLin", 60, -30, 45)
        build_highland(b)
        build_main_lake(b)
        build_creek(b)
        build_creek_pool(b)
        build_deep_pool(b)
        build_pool_creek(b)
        print(f"Done! {b.cmd_count} commands")
