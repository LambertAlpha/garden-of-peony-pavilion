"""phase5_landscape.py — 景观填充脚本 v2：春色满园

牡丹亭·游园惊梦 — v4 Phase 5 (重写)

设计理念:
  - 草地为主体，只在建筑周围和路径上铺石
  - "姹紫嫣红开遍" — 大量花卉、花丛、花带
  - 树木比例匹配建筑（8-12格高建筑 → 8-10格树）
  - 竹林密实，podzol地面
  - 碰撞安全：所有元素避开建筑（含树冠半径）、水面、船只

模块:
  1. build_paths — 仅小径+建筑散水带（不铺满空地！）
  2. build_revetment — 湖岸驳岸
  3. build_wall_planting — 围墙竹林+墙角石景
  4. build_rock_groups — 置石+花台+石凳
  5. build_trees — 大型柳树+梅树+松柏+中型树（比例放大）
  6. build_flower_meadows — 花带+花丛+牡丹芍药
  7. build_water_decor — 荷叶+菖蒲（碰撞安全）
  8. build_ground_cover — 蕨类+短草+苔藓
"""

import sys
import math
import random
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.builder import MinecraftBuilder, bresenham_3d, filled_circle_points
from config import config_v4 as cfg
from core.blocks import PALETTE

# ═══════════════════════════════════════════
# 常量
# ═══════════════════════════════════════════

GY = cfg.GROUND_Y          # -61
BY = cfg.BUILD_Y            # -60
WY = cfg.WATER_SURFACE_Y    # -61
HY = cfg.HIGHLAND_Y         # -57

RNG = random.Random(42)     # 固定种子，可重复


# ═══════════════════════════════════════════
# 几何/碰撞工具
# ═══════════════════════════════════════════

def point_in_polygon(x, z, polygon):
    """Ray casting"""
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


def ellipse_contains(x, z, cx, cz, rx, rz):
    dx = x - cx
    dz = z - cz
    return (dx * dx) / (rx * rx) + (dz * dz) / (rz * rz) <= 1.0


def _lerp(p1, p2):
    """简易 Bresenham XZ 插值"""
    x1, z1 = p1
    x2, z2 = p2
    pts = []
    dx, dz = abs(x2 - x1), abs(z2 - z1)
    sx = 1 if x2 > x1 else -1
    sz = 1 if z2 > z1 else -1
    if dx >= dz:
        err = 0
        x, z = x1, z1
        for _ in range(dx + 1):
            pts.append((x, z))
            err += dz
            if 2 * err >= dx:
                z += sz
                err -= dx
            x += sx
    else:
        err = 0
        x, z = x1, z1
        for _ in range(dz + 1):
            pts.append((x, z))
            err += dx
            if 2 * err >= dz:
                x += sx
                err -= dz
            z += sz
    if not pts:
        pts = [(x1, z1)]
    return pts


def _pmin(poly, idx):
    return min(p[idx] for p in poly)

def _pmax(poly, idx):
    return max(p[idx] for p in poly)


def _dist_sq(x1, z1, x2, z2):
    return (x1 - x2) ** 2 + (z1 - z2) ** 2


# ═══════════════════════════════════════════
# 预计算占用集合
# ═══════════════════════════════════════════

# ── 水面集合 ──

def _build_water_set():
    water = set()
    # 主湖
    sl = cfg.MAIN_LAKE["shoreline"]
    for z in range(_pmin(sl, 1), _pmax(sl, 1) + 1):
        for x in range(_pmin(sl, 0), _pmax(sl, 0) + 1):
            if point_in_polygon(x + 0.5, z + 0.5, sl):
                water.add((x, z))
    # 曲水溪流
    for seg in range(len(cfg.CREEK["centerline"]) - 1):
        p1 = cfg.CREEK["centerline"][seg]
        p2 = cfg.CREEK["centerline"][seg + 1]
        w = max(cfg.CREEK["widths"][seg], cfg.CREEK["widths"][seg + 1])
        hw = w // 2 + 1
        for t in _lerp(p1, p2):
            for dx in range(-hw, hw + 1):
                water.add((t[0] + dx, t[1]))
    # 翠轩前小池
    p = cfg.CREEK_POOL
    for x in range(p["cx"] - p["rx"] - 1, p["cx"] + p["rx"] + 2):
        for z in range(p["cz"] - p["rz"] - 1, p["cz"] + p["rz"] + 2):
            if ellipse_contains(x, z, p["cx"], p["cz"], p["rx"], p["rz"]):
                water.add((x, z))
    # 假山深潭
    dp = cfg.DEEP_POOL["shoreline"]
    for z in range(_pmin(dp, 1), _pmax(dp, 1) + 1):
        for x in range(_pmin(dp, 0), _pmax(dp, 0) + 1):
            if point_in_polygon(x + 0.5, z + 0.5, dp):
                water.add((x, z))
    # 深潭连接溪
    for seg in range(len(cfg.POOL_CREEK["centerline"]) - 1):
        p1 = cfg.POOL_CREEK["centerline"][seg]
        p2 = cfg.POOL_CREEK["centerline"][seg + 1]
        hw = cfg.POOL_CREEK["width"]
        for t in _lerp(p1, p2):
            for dx in range(-hw, hw + 1):
                water.add((t[0] + dx, t[1]))
    return water


# ── 建筑占用（含2格缓冲，用于避开种植）──

def _build_building_set():
    occ = set()
    for bld in cfg.ALL_BUILDINGS:
        cx = bld.get("cx", bld.get("x", 0))
        cz = bld.get("cz", bld.get("z", 0))
        sx = bld.get("size_x", 3)
        sz = bld.get("size_z", 3)
        hx, hz = sx // 2, sz // 2
        for x in range(cx - hx - 2, cx + hx + 3):
            for z in range(cz - hz - 2, cz + hz + 3):
                occ.add((x, z))
    return occ


# ── 建筑本体（无缓冲）──

def _build_building_core_set():
    core = set()
    for bld in cfg.ALL_BUILDINGS:
        cx = bld.get("cx", bld.get("x", 0))
        cz = bld.get("cz", bld.get("z", 0))
        sx = bld.get("size_x", 3)
        sz = bld.get("size_z", 3)
        hx, hz = sx // 2, sz // 2
        for x in range(cx - hx, cx + hx + 1):
            for z in range(cz - hz, cz + hz + 1):
                core.add((x, z))
    return core


# ── 建筑缓冲区（种大树用，含3格缓冲）──

def _build_tree_exclusion_set(buffer=3):
    """建筑边界 + buffer 格缓冲，种大树时不能把树干放在这里面。
    注意：树冠在高处，建筑屋顶也在高处，但2D碰撞检测足够。
    buffer=3 对中大型树比较合适，柳树等湖边树用更小的缓冲。"""
    exc = set()
    for bld in cfg.ALL_BUILDINGS:
        cx = bld.get("cx", bld.get("x", 0))
        cz = bld.get("cz", bld.get("z", 0))
        sx = bld.get("size_x", 3)
        sz = bld.get("size_z", 3)
        hx, hz = sx // 2, sz // 2
        for x in range(cx - hx - buffer, cx + hx + buffer + 1):
            for z in range(cz - hz - buffer, cz + hz + buffer + 1):
                exc.add((x, z))
    return exc


# ── 廊道占用 ──

def _build_corridor_set():
    corr = set()
    for corridor in [cfg.MAIN_CORRIDOR, cfg.WEST_CORRIDOR]:
        wp = corridor["waypoints"]
        hw = corridor["width"] // 2
        for i in range(len(wp) - 1):
            for px, pz in _lerp(wp[i], wp[i + 1]):
                for dx in range(-hw, hw + 1):
                    for dz in range(-hw, hw + 1):
                        corr.add((px + dx, pz + dz))
    # 北岸石径
    wp = cfg.HIGHLAND_PATH["waypoints"]
    hw = cfg.HIGHLAND_PATH["width"] // 2
    for i in range(len(wp) - 1):
        for px, pz in _lerp(wp[i], wp[i + 1]):
            for dx in range(-hw, hw + 1):
                for dz in range(-hw, hw + 1):
                    corr.add((px + dx, pz + dz))
    # 次路径
    for sp in cfg.SECONDARY_PATHS:
        wp = sp["waypoints"]
        hw = sp["width"] // 2
        for i in range(len(wp) - 1):
            for px, pz in _lerp(wp[i], wp[i + 1]):
                for dx in range(-hw, hw + 1):
                    for dz in range(-hw, hw + 1):
                        corr.add((px + dx, pz + dz))
    return corr


# ── 桥梁占用 ──

def _build_bridge_set():
    bridges = set()
    for br in cfg.ALL_BRIDGES:
        if "waypoints" in br:
            wp = br["waypoints"]
            hw = br.get("width", 3) // 2
            for i in range(len(wp) - 1):
                for px, pz in _lerp(wp[i], wp[i + 1]):
                    for dx in range(-hw, hw + 1):
                        bridges.add((px + dx, pz))
        elif "z_start" in br:
            cx = br["cx"]
            hw = br.get("width", 3) // 2
            for z in range(br["z_start"], br["z_end"] + 1):
                for dx in range(-hw, hw + 1):
                    bridges.add((cx + dx, z))
        elif "stones" in br:
            for sx, sz in br["stones"]:
                bridges.add((sx, sz))
    return bridges


# ── 全局集合 ──

WATER_SET = None
BUILDING_SET = None
BUILDING_CORE_SET = None
TREE_EXCLUSION_SET = None
CORRIDOR_SET = None
BRIDGE_SET = None


def _init_sets():
    global WATER_SET, BUILDING_SET, BUILDING_CORE_SET, TREE_EXCLUSION_SET
    global CORRIDOR_SET, BRIDGE_SET
    print("  Pre-computing occupancy sets...")
    WATER_SET = _build_water_set()
    BUILDING_SET = _build_building_set()
    BUILDING_CORE_SET = _build_building_core_set()
    TREE_EXCLUSION_SET = _build_tree_exclusion_set()
    CORRIDOR_SET = _build_corridor_set()
    BRIDGE_SET = _build_bridge_set()
    print(f"    water={len(WATER_SET)} building={len(BUILDING_SET)} "
          f"tree_excl={len(TREE_EXCLUSION_SET)} "
          f"corridor={len(CORRIDOR_SET)} bridge={len(BRIDGE_SET)}")


def _is_occupied(x, z):
    """点 (x,z) 是否被建筑/水面/廊道/桥占用"""
    return ((x, z) in WATER_SET or (x, z) in BUILDING_SET
            or (x, z) in CORRIDOR_SET or (x, z) in BRIDGE_SET)


def _is_water(x, z):
    return (x, z) in WATER_SET


def _is_building(x, z):
    """点是否在建筑本体内（无缓冲）"""
    return (x, z) in BUILDING_CORE_SET


def _is_on_structure(x, z):
    """点是否在建筑或桥梁上方（用于荷叶/水面装饰检测）"""
    return (x, z) in BUILDING_CORE_SET or (x, z) in BRIDGE_SET


def _can_place_tree(x, z):
    """树干位置是否安全（避开建筑+3格缓冲、水面、廊道）"""
    if (x, z) in WATER_SET:
        return False
    if (x, z) in TREE_EXCLUSION_SET:
        return False
    if (x, z) in CORRIDOR_SET:
        return False
    if (x, z) in BRIDGE_SET:
        return False
    return _in_garden(x, z)


def _can_place_lakeside_tree(x, z):
    """湖边树（柳树等）：只避开建筑本体+1格，不避开水面太远。
    柳树本来就该贴着水边种！"""
    if (x, z) in WATER_SET:
        return False
    if (x, z) in BUILDING_CORE_SET:
        return False
    # 只检查建筑本体 +1格缓冲
    for bld in cfg.ALL_BUILDINGS:
        cx = bld.get("cx", bld.get("x", 0))
        cz = bld.get("cz", bld.get("z", 0))
        sx = bld.get("size_x", 3)
        sz = bld.get("size_z", 3)
        hx, hz = sx // 2, sz // 2
        if cx - hx - 1 <= x <= cx + hx + 1 and cz - hz - 1 <= z <= cz + hz + 1:
            return False
    return _in_garden(x, z)


def _in_garden(x, z):
    return 1 <= x <= 119 and 1 <= z <= 89


def _ground_y(x, z):
    """返回 (x,z) 处的地面 Y"""
    for zone in cfg.TERRAIN_ZONES:
        if zone["name"] == "标准地面":
            continue
        xr, zr = zone["x_range"], zone["z_range"]
        if xr[0] <= x <= xr[1] and zr[0] <= z <= zr[1]:
            slope = zone.get("slope")
            if slope and slope["z_start"] <= z <= slope["z_end"]:
                t = (z - slope["z_start"]) / (slope["z_end"] - slope["z_start"])
                return round(slope["y_start"] + t * (slope["y_end"] - slope["y_start"]))
            elif slope and z > slope["z_end"]:
                return slope["y_end"]
            return zone["ground_y"]
    return GY


# ═══════════════════════════════════════════
# 1. build_paths — 仅小径+散水带（不铺满！）
# ═══════════════════════════════════════════

def build_paths(b: MinecraftBuilder):
    """只铺建筑散水带和步道，草地保留原样"""
    print("=== 1. Paths (散水带 + 步道，不铺满空地) ===")

    # ── 1a. 建筑台基外围1格 polished_andesite 散水带 ──
    print("  1a. Building aprons...")
    apron_count = 0
    for bld in cfg.ALL_BUILDINGS:
        cx = bld.get("cx", bld.get("x", 0))
        cz = bld.get("cz", bld.get("z", 0))
        sx = bld.get("size_x", 3)
        sz = bld.get("size_z", 3)
        hx, hz = sx // 2, sz // 2
        gy = bld.get("ground_y", GY)
        if bld.get("over_water"):
            continue
        ax1, ax2 = cx - hx - 1, cx + hx + 1
        az1, az2 = cz - hz - 1, cz + hz + 1
        apron = "minecraft:polished_andesite"
        b.fill(ax1, gy, az1, ax2, gy, az1, apron, "replace minecraft:grass_block")
        b.fill(ax1, gy, az2, ax2, gy, az2, apron, "replace minecraft:grass_block")
        b.fill(ax1, gy, az1 + 1, ax1, gy, az2 - 1, apron, "replace minecraft:grass_block")
        b.fill(ax2, gy, az1 + 1, ax2, gy, az2 - 1, apron, "replace minecraft:grass_block")
        apron_count += 4
    print(f"    {apron_count} apron fill ops")

    # ── 1b. 自然碎石小径（建筑间的草间步道）──
    # 沿次路径铺设不连续的石板，留出草缝
    print("  1b. Stepping stone paths...")
    step_count = 0
    stepping_blocks = [
        "minecraft:stone_bricks",
        "minecraft:mossy_stone_bricks",
        "minecraft:polished_andesite",
    ]
    for sp in cfg.SECONDARY_PATHS:
        if sp.get("surface") != "dirt_path":
            continue  # 入口轴线等正式路径由 phase2 处理
        wp = sp["waypoints"]
        hw = sp["width"] // 2
        for i in range(len(wp) - 1):
            pts = _lerp(wp[i], wp[i + 1])
            for j, (px, pz) in enumerate(pts):
                # 每隔 2-3 格放一块踏步石
                if j % 3 == 0 or (j % 3 == 1 and RNG.random() < 0.3):
                    gy = _ground_y(px, pz)
                    block = RNG.choice(stepping_blocks)
                    b.setblock(px, gy, pz, block)
                    step_count += 1
                    # 偶尔在旁边放一块
                    if RNG.random() < 0.3:
                        side = RNG.choice([-1, 1])
                        sx, sz = px + side, pz
                        if _in_garden(sx, sz) and not _is_water(sx, sz):
                            b.setblock(sx, gy, sz, RNG.choice(stepping_blocks))
                            step_count += 1
    print(f"    {step_count} stepping stones")
    print(f"  Paths done. Commands: {b.cmd_count}")


# ═══════════════════════════════════════════
# 2. build_revetment — 湖岸驳岸（分8段）
# ═══════════════════════════════════════════

_FORMAL_BUILDINGS = {"远香堂", "濯缨水阁", "入口门厅", "翠轩", "听雨轩"}
_HIGHLAND_BUILDINGS = {"太湖石组", "牡丹亭", "芍药阑", "池馆"}


def _nearest_building_type(x, z):
    min_dist = 99999
    nearest_name = ""
    for bld in cfg.ALL_BUILDINGS:
        bcx = bld.get("cx", bld.get("x", 0))
        bcz = bld.get("cz", bld.get("z", 0))
        d = _dist_sq(x, z, bcx, bcz)
        if d < min_dist:
            min_dist = d
            nearest_name = bld["name"]
    if nearest_name in _FORMAL_BUILDINGS:
        return "formal"
    if nearest_name in _HIGHLAND_BUILDINGS:
        return "highland"
    return "other"


def build_revetment(b: MinecraftBuilder):
    """湖岸驳岸: 根据最近建筑类型决定做法"""
    print("=== 2. Revetment ===")

    shoreline = cfg.MAIN_LAKE["shoreline"]
    n = len(shoreline) - 1

    seg_size = max(1, n // 8)
    revet_count = 0

    for seg_idx in range(8):
        start_i = seg_idx * seg_size
        end_i = min(start_i + seg_size, n)
        if start_i >= n:
            break

        mid_i = (start_i + end_i) // 2
        mx, mz = shoreline[mid_i]
        btype = _nearest_building_type(mx, mz)

        for i in range(start_i, end_i):
            p1 = shoreline[i]
            p2 = shoreline[(i + 1) % len(shoreline)]
            pts = _lerp(p1, p2)

            for px, pz in pts:
                if not _in_garden(px, pz):
                    continue
                gy = _ground_y(px, pz)

                if btype == "formal":
                    b.setblock(px, gy, pz, "minecraft:stone_bricks")
                    b.setblock(px, gy + 1, pz, "minecraft:stone_bricks")
                    revet_count += 2
                elif btype == "highland":
                    block = ("minecraft:dripstone_block"
                             if RNG.random() < 0.5 else "minecraft:cobblestone")
                    h = RNG.randint(1, 2)
                    for dy in range(h):
                        b.setblock(px, gy + dy, pz, block)
                        revet_count += 1
                    if RNG.random() < 0.3:
                        b.setblock(px, gy + h, pz, "minecraft:moss_carpet")
                        revet_count += 1
                else:
                    block = ("minecraft:mossy_cobblestone"
                             if RNG.random() < 0.4 else "minecraft:cobblestone")
                    b.setblock(px, gy, pz, block)
                    revet_count += 1
                    if RNG.random() < 0.2:
                        b.setblock(px, gy + 1, pz, "minecraft:fern")
                        revet_count += 1

    # 翠轩前小池驳岸
    pool = cfg.CREEK_POOL
    for angle in range(0, 360, 15):
        rad = math.radians(angle)
        px = round(pool["cx"] + pool["rx"] * math.cos(rad))
        pz = round(pool["cz"] + pool["rz"] * math.sin(rad))
        if _in_garden(px, pz) and not _is_building(px, pz):
            gy = _ground_y(px, pz)
            b.setblock(px, gy, pz, "minecraft:mossy_cobblestone")
            revet_count += 1

    print(f"    {revet_count} revetment blocks")
    print(f"  Revetment done. Commands: {b.cmd_count}")


# ═══════════════════════════════════════════
# 3. build_wall_planting — 围墙竹林+墙角石景
# ═══════════════════════════════════════════

def build_wall_planting(b: MinecraftBuilder):
    """围墙内侧: 密实竹林 + 墙角石景 + 漏窗框景"""
    print("=== 3. Wall Planting ===")

    # ── 3a. 竹林（更密实，间距2格，高度5-10格）──
    print("  3a. Dense bamboo groves along walls...")
    bamboo_segments = [
        # (起始x, 起始z, 方向'x'或'z', 长度, 深度)
        # 北墙内侧 (z=2~4, 2-3层深)
        (8, 2, 'x', 15, 3),
        (35, 2, 'x', 12, 2),
        (98, 2, 'x', 18, 3),
        # 东墙内侧 (x=115~117)
        (116, 10, 'z', 18, 2),
        (116, 50, 'z', 14, 3),
        (116, 72, 'z', 12, 2),
        # 西墙内侧 (x=3~5)
        (3, 35, 'z', 18, 3),
        (3, 60, 'z', 15, 2),
        # 南墙内侧 (z=86~88)
        (72, 86, 'x', 20, 2),
        (14, 86, 'x', 6, 2),
    ]
    bamboo_count = 0
    for bx, bz, axis, length, depth in bamboo_segments:
        for i in range(length):
            for d in range(depth):
                if axis == 'x':
                    x, z = bx + i, bz + d
                else:
                    x, z = bx - d, bz + i
                if not _in_garden(x, z) or _is_occupied(x, z):
                    continue
                gy = _ground_y(x, z)
                # podzol 地面
                b.setblock(x, gy, z, "minecraft:podzol")
                # 竹子间距约2格，70%概率种植
                if (i + d) % 2 == 0 and RNG.random() < 0.7:
                    h = RNG.randint(5, 10)
                    for dy in range(1, h + 1):
                        b.setblock(x, gy + dy, z, "minecraft:bamboo")
                    bamboo_count += 1
                elif RNG.random() < 0.3:
                    # 空位放蕨类
                    b.setblock(x, gy + 1, z, "minecraft:fern")
    print(f"    {bamboo_count} bamboo stalks")

    # ── 3b. 墙角石景 4组 ──
    print("  3b. Corner rock scenes...")
    corners = [(3, 3), (117, 3), (117, 87), (3, 87)]
    corner_count = 0
    for ccx, ccz in corners:
        if _is_occupied(ccx, ccz):
            continue
        gy = _ground_y(ccx, ccz)
        h = RNG.randint(1, 2)
        for dy in range(h):
            b.setblock(ccx, gy + 1 + dy, ccz, "minecraft:dripstone_block")
            corner_count += 1
        b.setblock(ccx, gy, ccz, "minecraft:moss_block")
        corner_count += 1
        for dx, dz in [(1, 0), (0, 1), (-1, 0), (0, -1)]:
            nx, nz = ccx + dx, ccz + dz
            if _in_garden(nx, nz) and not _is_occupied(nx, nz) and RNG.random() < 0.5:
                b.setblock(nx, gy + 1, nz, "minecraft:fern")
                corner_count += 1
    print(f"    {corner_count} corner stone blocks")

    # ── 3c. 漏窗下方框景 ──
    print("  3c. Lattice window vignettes...")
    vignette_count = 0
    for lw in cfg.WALL["lattice_windows"]:
        wall_side = lw["wall"]
        if wall_side == "east":
            wx, wz = 118, lw["z"]
        elif wall_side == "west":
            wx, wz = 2, lw["z"]
        elif wall_side == "north":
            wx, wz = lw["x"], 2
        else:
            wx, wz = lw["x"], 88
        if _is_occupied(wx, wz):
            continue
        gy = _ground_y(wx, wz)
        b.setblock(wx, gy + 1, wz, "minecraft:dripstone_block")
        vignette_count += 1
        for dx, dz in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            nx, nz = wx + dx, wz + dz
            if _in_garden(nx, nz) and not _is_occupied(nx, nz):
                flower = RNG.choice([
                    "minecraft:peony", "minecraft:rose_bush",
                    "minecraft:lilac", "minecraft:cornflower",
                ])
                b.setblock(nx, gy + 1, nz, flower)
                vignette_count += 1
                break
    print(f"    {vignette_count} vignette elements")
    print(f"  Wall planting done. Commands: {b.cmd_count}")


# ═══════════════════════════════════════════
# 4. build_rock_groups — 置石 + 花台 + 石凳
# ═══════════════════════════════════════════

def build_rock_groups(b: MinecraftBuilder):
    """置石12组 + 花台8个 + 石凳4组"""
    print("=== 4. Rock Groups & Flower Beds ===")

    # ── 4a. 太湖石 12组 ──
    print("  4a. Taihu rocks...")
    rock_positions = [
        (14, 44), (25, 60), (40, 72), (70, 74),
        (98, 50), (100, 30), (105, 15), (45, 10),
        (30, 14), (95, 70), (15, 70), (60, 80),
    ]
    rock_count = 0
    for rx, rz in rock_positions:
        if not _in_garden(rx, rz):
            continue
        blocked = False
        for dx in range(-1, 2):
            for dz in range(-1, 2):
                if _is_occupied(rx + dx, rz + dz):
                    blocked = True
                    break
            if blocked:
                break
        if blocked:
            continue

        gy = _ground_y(rx, rz)
        b.fill(rx - 1, gy, rz - 1, rx + 1, gy, rz + 1,
               "minecraft:moss_block", "replace minecraft:grass_block")
        rock_count += 1
        main_h = RNG.randint(2, 3)
        for dy in range(1, main_h + 1):
            block = ("minecraft:dripstone_block"
                     if dy <= main_h - 1 else "minecraft:calcite")
            b.setblock(rx, gy + dy, rz, block)
            rock_count += 1
        for dx, dz in RNG.sample([(1, 0), (-1, 0), (0, 1), (0, -1)], 2):
            side_h = RNG.randint(1, 2)
            b.setblock(rx + dx, gy + 1, rz + dz, "minecraft:dripstone_block")
            rock_count += 1
            if side_h > 1:
                b.setblock(rx + dx, gy + 2, rz + dz, "minecraft:calcite")
                rock_count += 1
        # 苔藓地毯 + 花
        for dx, dz in [(-1, -1), (1, -1), (-1, 1), (1, 1)]:
            if RNG.random() < 0.5:
                b.setblock(rx + dx, gy + 1, rz + dz, "minecraft:moss_carpet")
                rock_count += 1
        # 石旁种花
        for dx, dz in [(2, 0), (-2, 0), (0, 2), (0, -2)]:
            nx, nz = rx + dx, rz + dz
            if _in_garden(nx, nz) and not _is_occupied(nx, nz) and RNG.random() < 0.6:
                flower = RNG.choice([
                    "minecraft:peony", "minecraft:lilac",
                    "minecraft:azure_bluet", "minecraft:oxeye_daisy",
                ])
                gy2 = _ground_y(nx, nz)
                b.setblock(nx, gy2 + 1, nz, flower)
                rock_count += 1
    print(f"    {rock_count} rock blocks")

    # ── 4b. 花台 8个 ──
    print("  4b. Raised flower beds...")
    bed_positions = [
        (20, 50), (42, 76), (72, 76), (100, 42),
        (10, 20), (105, 60), (50, 4), (30, 82),
    ]
    bed_count = 0
    flowers_for_beds = [
        "minecraft:peony", "minecraft:rose_bush",
        "minecraft:lilac", "minecraft:peony",
    ]
    for bx, bz in bed_positions:
        if not _in_garden(bx, bz):
            continue
        blocked = False
        for dx in range(-1, 2):
            for dz in range(-1, 2):
                if _is_occupied(bx + dx, bz + dz):
                    blocked = True
                    break
            if blocked:
                break
        if blocked:
            continue

        gy = _ground_y(bx, bz)
        for dx in range(-1, 2):
            for dz in range(-1, 2):
                if abs(dx) == 1 or abs(dz) == 1:
                    b.setblock(bx + dx, gy + 1, bz + dz,
                               "minecraft:stone_brick_wall")
                    bed_count += 1
                else:
                    b.setblock(bx, gy + 1, bz, "minecraft:coarse_dirt")
                    flower = RNG.choice(flowers_for_beds)
                    b.setblock(bx, gy + 2, bz, flower)
                    bed_count += 2
    print(f"    {bed_count} flower bed blocks")

    # ── 4c. 石凳 4组 ──
    print("  4c. Stone benches...")
    bench_spots = [
        (26, 46, "south"), (72, 62, "west"),
        (46, 58, "north"), (16, 80, "east"),
    ]
    bench_count = 0
    for bx, bz, facing in bench_spots:
        if not _in_garden(bx, bz) or _is_building(bx, bz) or _is_water(bx, bz):
            continue
        gy = _ground_y(bx, bz)
        b.setblock(bx, gy + 1, bz,
                   f"minecraft:stone_brick_stairs[facing={facing}]")
        bench_count += 1
        if facing in ("south", "north"):
            nx, nz = bx + 1, bz
        else:
            nx, nz = bx, bz + 1
        if _in_garden(nx, nz) and not _is_occupied(nx, nz):
            b.setblock(nx, gy + 1, nz,
                       f"minecraft:stone_brick_stairs[facing={facing}]")
            bench_count += 1
    print(f"    {bench_count} bench blocks")
    print(f"  Rock groups done. Commands: {b.cmd_count}")


# ═══════════════════════════════════════════
# 5. build_trees — 大比例树木（匹配建筑高度）
# ═══════════════════════════════════════════

def _vine_facing(dx, dz):
    if abs(dx) >= abs(dz):
        return "west" if dx > 0 else "east"
    return "north" if dz > 0 else "south"


def _place_willow(b, x, gy, z):
    """大柳树: 10-13格树干 + 半径6冠 + 5-8格藤蔓"""
    trunk_h = RNG.randint(10, 13)
    # 2x2粗树干（底部4格）
    for dy in range(1, 5):
        for dx, dz in [(0, 0), (1, 0), (0, 1), (1, 1)]:
            b.setblock(x + dx, gy + dy, z + dz, "minecraft:oak_log")
    # 上部单干
    for dy in range(5, trunk_h + 1):
        b.setblock(x, gy + dy, z, "minecraft:oak_log")
    # 主枝分叉（3根水平枝）
    top_y = gy + trunk_h
    branches = RNG.sample([(3, 0), (-3, 0), (0, 3), (0, -3), (2, 2), (-2, -2)], 3)
    for bdx, bdz in branches:
        steps = max(abs(bdx), abs(bdz))
        for i in range(1, steps + 1):
            bx = x + round(bdx * i / steps)
            bz = z + round(bdz * i / steps)
            b.setblock(bx, top_y - 1, bz, "minecraft:oak_log")
    # 树冠 半径6, 3层
    crown_r = 6
    for dx in range(-crown_r, crown_r + 1):
        for dy in range(-1, 4):
            for dz in range(-crown_r, crown_r + 1):
                dist = dx * dx + dz * dz
                max_r = crown_r * crown_r if dy <= 1 else (crown_r - 2) * (crown_r - 2)
                if dist <= max_r and RNG.random() < 0.82:
                    b.setblock(x + dx, top_y + dy, z + dz,
                               "minecraft:oak_leaves[persistent=true]")
    # 藤蔓垂挂 5-8格
    for dx in range(-crown_r, crown_r + 1):
        for dz in range(-crown_r, crown_r + 1):
            dist = dx * dx + dz * dz
            if crown_r * crown_r * 0.4 <= dist <= crown_r * crown_r:
                if RNG.random() < 0.5:
                    vine_len = RNG.randint(5, 8)
                    facing = _vine_facing(dx, dz)
                    for dy in range(vine_len):
                        b.setblock(x + dx, top_y - 1 - dy, z + dz,
                                   f"minecraft:vine[{facing}=true]")


def _place_cherry_tree(b, x, gy, z):
    """樱花/梅树: 8-11格弯曲树干 + cherry_leaves 大冠"""
    trunk_h = RNG.randint(8, 11)
    cx, cz = x, z
    for dy in range(1, trunk_h + 1):
        b.setblock(cx, gy + dy, cz, "minecraft:dark_oak_log")
        if dy % 3 == 0:
            cx += RNG.choice([-1, 0, 1])
            cz += RNG.choice([-1, 0, 1])
    top_y = gy + trunk_h
    crown_r = RNG.randint(4, 5)
    for dx in range(-crown_r, crown_r + 1):
        for dy in range(-1, 4):
            for dz in range(-crown_r, crown_r + 1):
                dist = dx * dx + dz * dz
                if dist <= crown_r * crown_r and RNG.random() < 0.75:
                    b.setblock(cx + dx, top_y + dy, cz + dz,
                               "minecraft:cherry_leaves[persistent=true]")


def _place_pine(b, x, gy, z):
    """松/柏: 9-12格直干 + spruce_leaves 锥形冠"""
    trunk_h = RNG.randint(9, 12)
    for dy in range(1, trunk_h + 1):
        b.setblock(x, gy + dy, z, "minecraft:spruce_log")
    top_y = gy + trunk_h
    # 锥形树冠：7层，从顶到底半径递增
    for layer in range(7):
        y = top_y + 3 - layer
        r = layer  # 0,1,2,3,4,5,6
        if r == 0:
            b.setblock(x, y, z, "minecraft:spruce_leaves[persistent=true]")
        else:
            actual_r = min(r, 5)
            for dx in range(-actual_r, actual_r + 1):
                for dz in range(-actual_r, actual_r + 1):
                    if abs(dx) + abs(dz) <= actual_r and RNG.random() < 0.8:
                        b.setblock(x + dx, y, z + dz,
                                   "minecraft:spruce_leaves[persistent=true]")


def _place_medium_tree(b, x, gy, z):
    """中型观赏树: 8-10格干 + 半径4冠"""
    trunk_h = RNG.randint(8, 10)
    for dy in range(1, trunk_h + 1):
        b.setblock(x, gy + dy, z, "minecraft:oak_log")
    top_y = gy + trunk_h
    crown_r = 4
    for dx in range(-crown_r, crown_r + 1):
        for dy in range(-1, 4):
            for dz in range(-crown_r, crown_r + 1):
                dist = dx * dx + dz * dz
                if dist <= crown_r * crown_r and RNG.random() < 0.8:
                    b.setblock(x + dx, top_y + dy, z + dz,
                               "minecraft:oak_leaves[persistent=true]")


def _place_flowering_tree(b, x, gy, z):
    """花树 (杜鹃/山茶): 6-8格干 + azalea_leaves 大冠"""
    trunk_h = RNG.randint(6, 8)
    for dy in range(1, trunk_h + 1):
        b.setblock(x, gy + dy, z, "minecraft:oak_log")
    top_y = gy + trunk_h
    crown_r = 3
    for dx in range(-crown_r, crown_r + 1):
        for dy in range(-1, 3):
            for dz in range(-crown_r, crown_r + 1):
                if dx * dx + dz * dz <= crown_r * crown_r and RNG.random() < 0.8:
                    leaf = ("minecraft:flowering_azalea_leaves[persistent=true]"
                            if RNG.random() < 0.6
                            else "minecraft:azalea_leaves[persistent=true]")
                    b.setblock(x + dx, top_y + dy, z + dz, leaf)


def build_trees(b: MinecraftBuilder):
    """大型树木（比例匹配建筑8-12格高度）"""
    print("=== 5. Trees (比例放大) ===")

    # ── 5a. 大柳树沿湖岸（8-10格高，贴水边种）──
    print("  5a. Large weeping willows...")
    # 湖岸外侧2-3格处（确保在陆地上）
    willow_spots = [
        (26, 24),   # 西北湖岸
        (26, 40),   # 西岸中部
        (30, 56),   # 西南岸
        (44, 66),   # 南岸
        (64, 68),   # 南岸偏东
        (92, 42),   # 东岸（曲廊亭北）
        (92, 52),   # 东岸南
    ]
    willow_count = 0
    for wx, wz in willow_spots:
        if not _can_place_lakeside_tree(wx, wz):
            continue
        gy = _ground_y(wx, wz)
        _place_willow(b, wx, gy, wz)
        willow_count += 1
    print(f"    {willow_count} willows")

    # ── 5b. 梅花/樱花树（cherry_leaves，6-8格）──
    print("  5b. Cherry/plum trees...")
    cherry_spots = [
        (8, 8),     # 大梅树旁
        (12, 18),   # 梅花庵附近
        (18, 6),    # 北墙内
        (48, 46),   # 湖南岸
        (74, 68),   # 远香堂东
    ]
    cherry_count = 0
    for cx, cz in cherry_spots:
        if not _can_place_tree(cx, cz):
            continue
        gy = _ground_y(cx, cz)
        _place_cherry_tree(b, cx, gy, cz)
        cherry_count += 1
    print(f"    {cherry_count} cherry/plum trees")

    # ── 5c. 松柏（假山旁，7-9格）──
    print("  5c. Pine trees...")
    pine_spots = [
        (74, 6),     # 太湖石西
        (90, 8),     # 深潭旁
        (104, 18),   # 东北角
        (110, 40),   # 东岸
    ]
    pine_count = 0
    for px, pz in pine_spots:
        if not _can_place_tree(px, pz):
            continue
        gy = _ground_y(px, pz)
        _place_pine(b, px, gy, pz)
        pine_count += 1
    print(f"    {pine_count} pine trees")

    # ── 5d. 中型树（院间遮荫，6-8格）──
    print("  5d. Medium shade trees...")
    tree_spots = [
        (38, 64), (76, 64), (12, 48), (100, 55),
        (22, 70), (108, 68), (10, 55), (108, 26),
    ]
    tree_count = 0
    for tx, tz in tree_spots:
        if not _can_place_tree(tx, tz):
            continue
        gy = _ground_y(tx, tz)
        _place_medium_tree(b, tx, gy, tz)
        tree_count += 1
    print(f"    {tree_count} medium trees")

    # ── 5e. 花树/灌木树（杜鹃/山茶，4-5格）──
    print("  5e. Flowering trees...")
    flower_tree_spots = [
        (30, 70), (64, 74), (14, 38), (104, 48),
        (40, 84), (80, 78), (8, 78), (112, 58),
    ]
    ft_count = 0
    for fx, fz in flower_tree_spots:
        if not _can_place_tree(fx, fz):
            continue
        gy = _ground_y(fx, fz)
        _place_flowering_tree(b, fx, gy, fz)
        ft_count += 1
    print(f"    {ft_count} flowering trees")

    print(f"  Trees done. Commands: {b.cmd_count}")


# ═══════════════════════════════════════════
# 6. build_flower_meadows — 花带+花丛 (春色如许)
# ═══════════════════════════════════════════

def build_flower_meadows(b: MinecraftBuilder):
    """姹紫嫣红：大面积花带 + 散植花丛"""
    print("=== 6. Flower Meadows (姹紫嫣红) ===")

    # ── 6a. 大型花带（5-15格长的连续花丛）──
    print("  6a. Flower ribbons...")
    # 定义花带区域：起点、方向、长度、主花色
    flower_ribbons = [
        # (x, z, axis, length, flowers)
        # 远香堂前庭 — 牡丹+芍药
        (42, 70, 'x', 12, ["minecraft:peony", "minecraft:peony", "minecraft:rose_bush"]),
        (46, 72, 'x', 10, ["minecraft:peony", "minecraft:lilac"]),
        (62, 70, 'x', 10, ["minecraft:peony", "minecraft:rose_bush"]),
        # 闺塾旁 — 玫瑰丛
        (26, 82, 'x', 8, ["minecraft:rose_bush", "minecraft:lilac"]),
        # 入口两侧 — 牡丹迎客
        (48, 86, 'z', 4, ["minecraft:peony", "minecraft:rose_bush"]),
        (68, 86, 'z', 4, ["minecraft:peony", "minecraft:rose_bush"]),
        # 西园 — 梅花周围用淡色
        (8, 16, 'x', 8, ["minecraft:lilac", "minecraft:azure_bluet"]),
        # 东岸 — 色彩丰富
        (100, 36, 'z', 10, ["minecraft:rose_bush", "minecraft:peony", "minecraft:lilac"]),
        (106, 50, 'z', 8, ["minecraft:cornflower", "minecraft:allium"]),
        # 南侧空地
        (34, 78, 'x', 8, ["minecraft:peony", "minecraft:rose_bush"]),
        (74, 78, 'x', 8, ["minecraft:peony", "minecraft:lilac"]),
    ]
    ribbon_count = 0
    for rx, rz, axis, length, flowers in flower_ribbons:
        for i in range(length):
            if axis == 'x':
                x, z = rx + i, rz
            else:
                x, z = rx, rz + i
            if not _in_garden(x, z) or _is_occupied(x, z):
                continue
            gy = _ground_y(x, z)
            flower = RNG.choice(flowers)
            b.setblock(x, gy + 1, z, flower)
            ribbon_count += 1
            # 两侧也种一排（加宽花带到3格）
            for side in [-1, 1]:
                sx = x + (0 if axis == 'z' else 0)
                sz = z + (side if axis == 'x' else 0)
                sx2 = x + (side if axis == 'z' else 0)
                sz2 = z + (0 if axis == 'z' else 0)
                nx, nz = (sx2, sz) if axis == 'z' else (sx, sz)
                if _in_garden(nx, nz) and not _is_occupied(nx, nz) and RNG.random() < 0.6:
                    gy2 = _ground_y(nx, nz)
                    b.setblock(nx, gy2 + 1, nz, RNG.choice(flowers))
                    ribbon_count += 1
    print(f"    {ribbon_count} flower ribbon blocks")

    # ── 6b. 散植小花（空地上星星点点）──
    print("  6b. Scattered wildflowers...")
    small_flowers = [
        "minecraft:poppy", "minecraft:dandelion",
        "minecraft:azure_bluet", "minecraft:oxeye_daisy",
        "minecraft:cornflower", "minecraft:allium",
        "minecraft:lily_of_the_valley",
        "minecraft:pink_tulip", "minecraft:red_tulip",
        "minecraft:white_tulip", "minecraft:orange_tulip",
    ]
    scatter_count = 0
    for x in range(3, 118, 4):
        for z in range(3, 88, 4):
            if _is_occupied(x, z) or not _in_garden(x, z):
                continue
            if RNG.random() < 0.12:
                gy = _ground_y(x, z)
                flower = RNG.choice(small_flowers)
                b.setblock(x, gy + 1, z, flower)
                scatter_count += 1
    print(f"    {scatter_count} scattered flowers")

    # ── 6c. 灌木丛（flowering_azalea, azalea）──
    print("  6c. Azalea bushes...")
    shrub_count = 0
    # 廊道边缘
    for corridor in [cfg.MAIN_CORRIDOR, cfg.WEST_CORRIDOR]:
        wp = corridor["waypoints"]
        hw = corridor["width"] // 2 + 2
        for i in range(len(wp) - 1):
            pts = _lerp(wp[i], wp[i + 1])
            for j, (px, pz) in enumerate(pts):
                if j % 4 != 0:
                    continue
                for side_d in [hw, -hw]:
                    sx, sz = px + side_d, pz
                    if not _in_garden(sx, sz) or _is_occupied(sx, sz):
                        sx, sz = px, pz + side_d
                        if not _in_garden(sx, sz) or _is_occupied(sx, sz):
                            continue
                    if RNG.random() < 0.55:
                        gy = _ground_y(sx, sz)
                        bush = ("minecraft:flowering_azalea"
                                if RNG.random() < 0.6 else "minecraft:azalea")
                        b.setblock(sx, gy + 1, sz, bush)
                        shrub_count += 1
    print(f"    {shrub_count} azalea bushes")
    print(f"  Flower meadows done. Commands: {b.cmd_count}")


# ═══════════════════════════════════════════
# 7. build_water_decor — 水面装饰（碰撞安全）
# ═══════════════════════════════════════════

def build_water_decor(b: MinecraftBuilder):
    """lily_pad + sugar_cane，避开建筑和船只"""
    print("=== 7. Water Decoration (碰撞安全) ===")

    # ── 7a. 睡莲: 避开建筑/桥/船 ──
    print("  7a. Lily pads (safe placement)...")
    lily_centers = cfg.LILY_PADS
    lily_count = 0
    for lcx, lcz in lily_centers:
        for dx in range(-6, 7):
            for dz in range(-6, 7):
                x, z = lcx + dx, lcz + dz
                if not _is_water(x, z):
                    continue
                # 关键检测：不放在建筑/桥/船上方
                if _is_on_structure(x, z):
                    continue
                dist_sq = dx * dx + dz * dz
                if dist_sq > 36:
                    continue
                if RNG.random() < 0.18:
                    b.setblock(x, WY + 1, z, "minecraft:lily_pad")
                    lily_count += 1
    print(f"    {lily_count} lily pads")

    # ── 7b. 菖蒲（sugar_cane）──
    print("  7b. Sugar cane (iris/calamus)...")
    cane_count = 0
    shoreline = cfg.MAIN_LAKE["shoreline"]
    for i in range(len(shoreline) - 1):
        pts = _lerp(shoreline[i], shoreline[(i + 1) % len(shoreline)])
        for j, (px, pz) in enumerate(pts):
            if j % 8 != 0:
                continue
            if RNG.random() < 0.3:
                cx, cz = cfg.MAIN_LAKE["center"]
                ddx = cx - px
                ddz = cz - pz
                dist = max(1, math.sqrt(ddx * ddx + ddz * ddz))
                sx = px + round(ddx / dist)
                sz = pz + round(ddz / dist)
                if _is_water(sx, sz) and not _is_on_structure(sx, sz):
                    b.setblock(sx, WY, sz, "minecraft:sand")
                    h = RNG.randint(2, 3)
                    for dy in range(1, h + 1):
                        b.setblock(sx, WY + dy, sz, "minecraft:sugar_cane")
                    cane_count += 1

    # 溪旁
    creek_cl = cfg.CREEK["centerline"]
    for i in range(0, len(creek_cl) - 1, 2):
        px, pz = creek_cl[i]
        if _is_water(px, pz) and not _is_on_structure(px, pz) and RNG.random() < 0.5:
            b.setblock(px, WY, pz, "minecraft:sand")
            h = RNG.randint(2, 3)
            for dy in range(1, h + 1):
                b.setblock(px, WY + dy, pz, "minecraft:sugar_cane")
            cane_count += 1

    print(f"    {cane_count} sugar cane clusters")
    print(f"  Water decor done. Commands: {b.cmd_count}")


# ═══════════════════════════════════════════
# 8. build_ground_cover — 地被覆盖
# ═══════════════════════════════════════════

def build_ground_cover(b: MinecraftBuilder):
    """蕨类 + 短草 + 苔藓覆盖空地（春意盎然）"""
    print("=== 8. Ground Cover ===")

    cover_count = 0
    # 较密的地被覆盖: 25% 概率 (比原来15%更密)
    for x in range(2, 119, 2):
        for z in range(2, 89, 2):
            if _is_occupied(x, z) or not _in_garden(x, z):
                continue
            if RNG.random() < 0.25:
                gy = _ground_y(x, z)
                r = RNG.random()
                if r < 0.35:
                    block = "minecraft:short_grass"
                elif r < 0.55:
                    block = "minecraft:fern"
                elif r < 0.70:
                    block = "minecraft:large_fern"
                elif r < 0.82:
                    block = "minecraft:tall_grass"
                else:
                    block = "minecraft:moss_carpet"
                b.setblock(x, gy + 1, z, block)
                cover_count += 1
    print(f"    {cover_count} ground cover plants")
    print(f"  Ground cover done. Commands: {b.cmd_count}")


# ═══════════════════════════════════════════
# 9. build_atmosphere — 意境点睛（调研新增）
# ═══════════════════════════════════════════

def build_atmosphere(b: MinecraftBuilder):
    """落花瓣 + 树下土壤 + 墙上藤蔓 + 芭蕉"""
    print("=== 9. Atmosphere (意境点睛) ===")

    # ── 9a. 牡丹亭周围落花瓣（pink_petals）──
    # "原来姹紫嫣红开遍" — 落花比盛花更有戏剧张力
    print("  9a. Fallen petals around Peony Pavilion...")
    petal_count = 0
    pcx, pcz = 58, 8  # 牡丹亭中心
    pgy = HY  # -57，高地地面
    for dx in range(-10, 11):
        for dz in range(-10, 11):
            x, z = pcx + dx, pcz + dz
            dist = dx * dx + dz * dz
            if dist > 100:  # 半径10
                continue
            if not _in_garden(x, z) or _is_building(x, z):
                continue
            # 越靠近亭子概率越高
            prob = 0.3 if dist < 36 else 0.12
            if RNG.random() < prob:
                gy = _ground_y(x, z)
                b.setblock(x, gy + 1, z, "minecraft:pink_petals")
                petal_count += 1
    # 芍药阑附近也撒一些
    pcx2, pcz2 = 50, 26
    for dx in range(-6, 7):
        for dz in range(-5, 6):
            x, z = pcx2 + dx, pcz2 + dz
            if not _in_garden(x, z) or _is_building(x, z):
                continue
            if RNG.random() < 0.15:
                gy = _ground_y(x, z)
                b.setblock(x, gy + 1, z, "minecraft:pink_petals")
                petal_count += 1
    print(f"    {petal_count} fallen petals")

    # ── 9b. 大树下方土壤质感（podzol + moss_block + rooted_dirt）──
    print("  9b. Tree base soil...")
    soil_count = 0
    # 所有种过树的位置，周围3格换 podzol/moss
    tree_centers = [
        # 柳树
        (26, 24), (26, 40), (30, 56), (44, 66), (64, 68), (92, 42), (92, 52),
        # 梅花
        (8, 8), (12, 18), (18, 6), (48, 46), (74, 68),
        # 松柏
        (74, 6), (90, 8), (104, 18), (110, 40),
        # 中型树
        (38, 64), (76, 64), (12, 48), (100, 55), (22, 70), (108, 68), (10, 55), (108, 26),
    ]
    for tcx, tcz in tree_centers:
        for dx in range(-3, 4):
            for dz in range(-3, 4):
                x, z = tcx + dx, tcz + dz
                if not _in_garden(x, z) or _is_water(x, z) or _is_building(x, z):
                    continue
                dist = abs(dx) + abs(dz)
                if dist > 4:
                    continue
                gy = _ground_y(x, z)
                r = RNG.random()
                if dist <= 1:
                    block = "minecraft:rooted_dirt"
                elif r < 0.5:
                    block = "minecraft:podzol"
                else:
                    block = "minecraft:moss_block"
                b.setblock(x, gy, z, block)
                soil_count += 1
    print(f"    {soil_count} tree base soil blocks")

    # ── 9c. 墙上藤蔓（约30%墙段）──
    print("  9c. Wall vines...")
    vine_count = 0
    wall_segments = [
        # (x_start, z_start, x_end, z_end, vine_face)
        # 北墙内侧
        (20, 1, 45, 1, "south"),
        (65, 1, 90, 1, "south"),
        # 东墙内侧
        (119, 15, 119, 35, "west"),
        (119, 55, 119, 75, "west"),
        # 西墙内侧
        (1, 20, 1, 40, "east"),
        # 南墙内侧
        (20, 89, 50, 89, "north"),
    ]
    for xs, zs, xe, ze, face in wall_segments:
        pts = _lerp((xs, zs), (xe, ze))
        for px, pz in pts:
            if RNG.random() < 0.35:
                gy = _ground_y(px, pz)
                vine_h = RNG.randint(1, 3)
                for dy in range(vine_h):
                    b.setblock(px, gy + 2 + dy, pz,
                               f"minecraft:vine[{face}=true]")
                    vine_count += 1
    print(f"    {vine_count} wall vine blocks")

    # ── 9d. 听雨轩前芭蕉（jungle_leaves 模拟）──
    print("  9d. Banana plants (听雨轩)...")
    banana_spots = [(32, 52), (36, 52)]  # 听雨轩(34,54)前方
    banana_count = 0
    for bx, bz in banana_spots:
        if _is_occupied(bx, bz):
            continue
        gy = _ground_y(bx, bz)
        # 粗茎
        b.setblock(bx, gy + 1, bz, "minecraft:jungle_log")
        b.setblock(bx, gy + 2, bz, "minecraft:jungle_log")
        # 阔叶
        for dx, dz in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            b.setblock(bx + dx, gy + 3, bz + dz,
                       "minecraft:jungle_leaves[persistent=true]")
        b.setblock(bx, gy + 3, bz, "minecraft:jungle_leaves[persistent=true]")
        b.setblock(bx, gy + 4, bz, "minecraft:jungle_leaves[persistent=true]")
        banana_count += 1
    print(f"    {banana_count} banana plants")
    print(f"  Atmosphere done. Commands: {b.cmd_count}")


# ═══════════════════════════════════════════
# 主入口
# ═══════════════════════════════════════════

def build_all_landscape(b):
    _init_sets()
    build_paths(b)
    build_revetment(b)
    build_wall_planting(b)
    build_rock_groups(b)
    build_trees(b)
    build_flower_meadows(b)
    build_water_decor(b)
    build_ground_cover(b)
    build_atmosphere(b)


if __name__ == "__main__":
    with MinecraftBuilder() as b:
        build_all_landscape(b)
        print(f"\nDone! {b.cmd_count} commands")
