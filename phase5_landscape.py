"""phase5_landscape.py — 景观填充脚本：填充建筑群之间的所有空地

牡丹亭·游园惊梦 — v4 Phase 5
铺地 + 驳岸 + 围墙植被 + 置石花台 + 树木地被 + 水面装饰
约 3,680 格空地处理。目标 < 4,000 命令。
"""

import sys
import math
import random

sys.path.insert(0, '/Users/lambertlin/minecraft-server/scripts')

from builder import MinecraftBuilder, bresenham_3d, filled_circle_points
import config_v4 as cfg
from blocks import PALETTE

# ═══════════════════════════════════════════
# 常量
# ═══════════════════════════════════════════

GY = cfg.GROUND_Y          # -61
BY = cfg.BUILD_Y            # -60
WY = cfg.WATER_SURFACE_Y    # -61
HY = cfg.HIGHLAND_Y         # -57

RNG = random.Random(42)     # 固定种子，可重复

# 铺地材质（冰裂纹混铺）
PAVING_BLOCKS = [
    "minecraft:stone_bricks",
    "minecraft:polished_andesite",
    "minecraft:andesite",
    "minecraft:smooth_stone",
]
PAVING_WEIGHTS = [0.35, 0.25, 0.25, 0.15]  # 累积分段用

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


# ── 建筑占用（含1格缓冲）──

def _build_building_set():
    occ = set()
    for bld in cfg.ALL_BUILDINGS:
        cx = bld.get("cx", bld.get("x", 0))
        cz = bld.get("cz", bld.get("z", 0))
        sx = bld.get("size_x", 3)
        sz = bld.get("size_z", 3)
        hx, hz = sx // 2, sz // 2
        for x in range(cx - hx - 1, cx + hx + 2):
            for z in range(cz - hz - 1, cz + hz + 2):
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
CORRIDOR_SET = None
BRIDGE_SET = None


def _init_sets():
    global WATER_SET, BUILDING_SET, BUILDING_CORE_SET, CORRIDOR_SET, BRIDGE_SET
    print("  Pre-computing occupancy sets...")
    WATER_SET = _build_water_set()
    BUILDING_SET = _build_building_set()
    BUILDING_CORE_SET = _build_building_core_set()
    CORRIDOR_SET = _build_corridor_set()
    BRIDGE_SET = _build_bridge_set()
    print(f"    water={len(WATER_SET)} building={len(BUILDING_SET)} "
          f"corridor={len(CORRIDOR_SET)} bridge={len(BRIDGE_SET)}")


def _is_occupied(x, z):
    """点 (x,z) 是否被建筑/水面/廊道/桥占用"""
    return ((x, z) in WATER_SET or (x, z) in BUILDING_SET
            or (x, z) in CORRIDOR_SET or (x, z) in BRIDGE_SET)


def _is_water(x, z):
    return (x, z) in WATER_SET


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


def _pick_paving():
    """按权重随机选铺地材质"""
    r = RNG.random()
    cum = 0.0
    for i, w in enumerate(PAVING_WEIGHTS):
        cum += w
        if r < cum:
            return PAVING_BLOCKS[i]
    return PAVING_BLOCKS[0]


# ═══════════════════════════════════════════
# 1. build_paving — 铺地（~1200格）
# ═══════════════════════════════════════════

def build_paving(b: MinecraftBuilder):
    """铺地: 散水带 + 建筑群间空地冰裂纹混铺"""
    print("=== 1. Paving ===")

    # ── 1a. 建筑台基外围1格 polished_andesite 散水带 ──
    print("  1a. Building aprons (polished_andesite)...")
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
        # 四条边各一次 fill
        b.fill(ax1, gy, az1, ax2, gy, az1, apron, "replace minecraft:grass_block")
        b.fill(ax1, gy, az2, ax2, gy, az2, apron, "replace minecraft:grass_block")
        b.fill(ax1, gy, az1 + 1, ax1, gy, az2 - 1, apron, "replace minecraft:grass_block")
        b.fill(ax2, gy, az1 + 1, ax2, gy, az2 - 1, apron, "replace minecraft:grass_block")
        apron_count += 4
    print(f"    {apron_count} apron fill ops")

    # ── 1b. 空地冰裂纹混铺 ──
    # 策略: 按行扫描，找连续空地段，每段用 fill 铺随机材质
    # 同一行的连续空地用同一材质 fill，换段换材质 → 自然冰裂纹效果
    print("  1b. Open ground paving (cracked-ice pattern)...")
    pave_fills = 0
    for z in range(1, 90):
        run_start = None
        run_block = None
        for x in range(1, 121):  # 多跑1格触发末尾 flush
            in_bounds = x <= 119
            is_free = in_bounds and _in_garden(x, z) and not _is_occupied(x, z)

            if is_free:
                if run_start is None:
                    # 开新段: 随机选材质
                    run_start = x
                    run_block = _pick_paving()
                else:
                    # 随机概率断段 → 换材质（模拟冰裂纹不规则）
                    if RNG.random() < 0.08:
                        # flush 当前段
                        gy = _ground_y(run_start, z)
                        b.fill(run_start, gy, z, x - 1, gy, z,
                               run_block, "replace minecraft:grass_block")
                        pave_fills += 1
                        run_start = x
                        run_block = _pick_paving()
            else:
                if run_start is not None:
                    gy = _ground_y(run_start, z)
                    b.fill(run_start, gy, z, x - 1, gy, z,
                           run_block, "replace minecraft:grass_block")
                    pave_fills += 1
                    run_start = None
                    run_block = None
    print(f"    {pave_fills} paving fill ops")
    print(f"  Paving done. Commands so far: {b.cmd_count}")


# ═══════════════════════════════════════════
# 2. build_revetment — 湖岸驳岸（分8段）
# ═══════════════════════════════════════════

# 正式建筑列表（决定驳岸做法用）
_FORMAL_BUILDINGS = {"远香堂", "濯缨水阁", "入口门厅", "翠轩", "听雨轩"}
_HIGHLAND_BUILDINGS = {"太湖石组", "牡丹亭", "芍药阑", "池馆"}


def _nearest_building_type(x, z):
    """判断 (x,z) 最近的建筑类型: 'formal', 'highland', 'other'"""
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
    n = len(shoreline) - 1  # 最后一点和第一点重合

    # 将岸线分成8段
    seg_size = max(1, n // 8)
    revet_count = 0

    for seg_idx in range(8):
        start_i = seg_idx * seg_size
        end_i = min(start_i + seg_size, n)
        if start_i >= n:
            break

        # 取这段的中点判断建筑类型
        mid_i = (start_i + end_i) // 2
        mx, mz = shoreline[mid_i]
        btype = _nearest_building_type(mx, mz)

        # 遍历这段的岸线点
        for i in range(start_i, end_i):
            p1 = shoreline[i]
            p2 = shoreline[(i + 1) % len(shoreline)]
            pts = _lerp(p1, p2)

            for px, pz in pts:
                if not _in_garden(px, pz):
                    continue
                gy = _ground_y(px, pz)

                if btype == "formal":
                    # 条石直壁: stone_bricks 2格高
                    b.setblock(px, gy, pz, "minecraft:stone_bricks")
                    b.setblock(px, gy + 1, pz, "minecraft:stone_bricks")
                    revet_count += 2
                elif btype == "highland":
                    # 叠石入水: dripstone_block + cobblestone
                    block = ("minecraft:dripstone_block"
                             if RNG.random() < 0.5 else "minecraft:cobblestone")
                    h = RNG.randint(1, 2)
                    for dy in range(h):
                        b.setblock(px, gy + dy, pz, block)
                        revet_count += 1
                    # 苔藓填缝
                    if RNG.random() < 0.3:
                        b.setblock(px, gy + h, pz, "minecraft:moss_carpet")
                        revet_count += 1
                else:
                    # 自然石块
                    block = ("minecraft:mossy_cobblestone"
                             if RNG.random() < 0.4 else "minecraft:cobblestone")
                    b.setblock(px, gy, pz, block)
                    revet_count += 1
                    # fern 填缝
                    if RNG.random() < 0.2:
                        b.setblock(px, gy + 1, pz, "minecraft:fern")
                        revet_count += 1

    # 翠轩前小池驳岸（简单 cobblestone 一圈）
    pool = cfg.CREEK_POOL
    for angle in range(0, 360, 15):
        rad = math.radians(angle)
        px = round(pool["cx"] + pool["rx"] * math.cos(rad))
        pz = round(pool["cz"] + pool["rz"] * math.sin(rad))
        if _in_garden(px, pz) and not (px, pz) in BUILDING_SET:
            gy = _ground_y(px, pz)
            b.setblock(px, gy, pz, "minecraft:mossy_cobblestone")
            revet_count += 1

    print(f"    {revet_count} revetment blocks")
    print(f"  Revetment done. Commands so far: {b.cmd_count}")


# ═══════════════════════════════════════════
# 3. build_wall_planting — 围墙内侧植被
# ═══════════════════════════════════════════

def build_wall_planting(b: MinecraftBuilder):
    """围墙内侧: 竹林 + 墙角石景 + 漏窗框景，白墙留白40-50%"""
    print("=== 3. Wall Planting ===")

    # ── 3a. 竹林 5-6段（每段8-15格长）──
    print("  3a. Bamboo groves along walls...")
    # 沿四面墙内侧2-3格处布置竹林段
    bamboo_segments = [
        # (起始x, 起始z, 方向'x'或'z', 长度, 沿墙位置)
        # 北墙内侧 (z=2)
        (8, 2, 'x', 12),
        (35, 2, 'x', 10),
        # 东墙内侧 (x=117)
        (117, 10, 'z', 14),
        (117, 50, 'z', 10),
        # 西墙内侧 (x=3)
        (3, 40, 'z', 12),
        # 南墙内侧 (z=87)
        (80, 87, 'x', 15),
    ]
    bamboo_count = 0
    for bx, bz, axis, length in bamboo_segments:
        for i in range(length):
            if axis == 'x':
                x, z = bx + i, bz
            else:
                x, z = bx, bz + i
            if not _in_garden(x, z) or _is_occupied(x, z):
                continue
            gy = _ground_y(x, z)
            # podzol 地面
            b.setblock(x, gy, z, "minecraft:podzol")
            # 竹子 3-7格高，间隔种植
            if RNG.random() < 0.7:
                h = RNG.randint(3, 7)
                for dy in range(1, h + 1):
                    b.setblock(x, gy + dy, z, "minecraft:bamboo")
                bamboo_count += 1
    print(f"    {bamboo_count} bamboo stalks")

    # ── 3b. 墙角石景 4组 ──
    print("  3b. Corner rock scenes...")
    corners = [
        (3, 3),       # 西北角
        (117, 3),     # 东北角
        (117, 87),    # 东南角
        (3, 87),      # 西南角
    ]
    corner_count = 0
    for ccx, ccz in corners:
        if _is_occupied(ccx, ccz):
            continue
        gy = _ground_y(ccx, ccz)
        # 1-2格高 dripstone_block
        h = RNG.randint(1, 2)
        for dy in range(h):
            b.setblock(ccx, gy + 1 + dy, ccz, "minecraft:dripstone_block")
            corner_count += 1
        # 苔藓点缀
        b.setblock(ccx, gy, ccz, "minecraft:moss_block")
        corner_count += 1
        # 蕨类
        if RNG.random() < 0.6:
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
        # 小石 + 花
        b.setblock(wx, gy + 1, wz, "minecraft:dripstone_block")
        vignette_count += 1
        # 旁边放一丛花
        for dx, dz in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            nx, nz = wx + dx, wz + dz
            if _in_garden(nx, nz) and not _is_occupied(nx, nz):
                flower = RNG.choice([
                    "minecraft:peony", "minecraft:rose_bush",
                    "minecraft:lilac", "minecraft:cornflower",
                ])
                b.setblock(nx, gy + 1, nz, flower)
                vignette_count += 1
                break  # 只放一丛
    print(f"    {vignette_count} vignette elements")
    print(f"  Wall planting done. Commands so far: {b.cmd_count}")


# ═══════════════════════════════════════════
# 4. build_rock_groups — 置石 + 花台 + 石凳
# ═══════════════════════════════════════════

def build_rock_groups(b: MinecraftBuilder):
    """置石10-12组 + 花台6-8个 + 石凳3-4组"""
    print("=== 4. Rock Groups & Flower Beds ===")

    # ── 4a. 孤赏石 10-12组 (3x3, dripstone+calcite+moss) ──
    print("  4a. Solitary rocks...")
    rock_positions = [
        (14, 44),    # 西岸
        (25, 60),    # 西南
        (40, 72),    # 南侧
        (70, 74),    # 东南
        (98, 50),    # 东岸
        (100, 30),   # 东北
        (105, 15),   # 远东北
        (45, 10),    # 北侧
        (30, 14),    # 西北
        (95, 70),    # 东南角落
        (15, 70),    # 西南角落
        (60, 80),    # 远香堂南
    ]
    rock_count = 0
    for rx, rz in rock_positions:
        if not _in_garden(rx, rz):
            continue
        # 检查 3x3 区域是否全空
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
        # 底层 3x3 moss_block
        b.fill(rx - 1, gy, rz - 1, rx + 1, gy, rz + 1,
               "minecraft:moss_block", "replace minecraft:grass_block")
        rock_count += 1
        # 中心主石 2-3格高
        main_h = RNG.randint(2, 3)
        for dy in range(1, main_h + 1):
            block = ("minecraft:dripstone_block"
                     if dy <= main_h - 1 else "minecraft:calcite")
            b.setblock(rx, gy + dy, rz, block)
            rock_count += 1
        # 侧石 1-2格
        for dx, dz in RNG.sample([(1, 0), (-1, 0), (0, 1), (0, -1)], 2):
            side_h = RNG.randint(1, 2)
            b.setblock(rx + dx, gy + 1, rz + dz, "minecraft:dripstone_block")
            rock_count += 1
            if side_h > 1:
                b.setblock(rx + dx, gy + 2, rz + dz, "minecraft:calcite")
                rock_count += 1
        # 苔藓地毯
        for dx, dz in [(-1, -1), (1, -1), (-1, 1), (1, 1)]:
            if RNG.random() < 0.5:
                b.setblock(rx + dx, gy + 1, rz + dz, "minecraft:moss_carpet")
                rock_count += 1
    print(f"    {rock_count} rock blocks")

    # ── 4b. 花台 6-8个 (stone_brick_wall 围边 + coarse_dirt + 花) ──
    print("  4b. Raised flower beds...")
    bed_positions = [
        (20, 50),    # 西侧路边
        (42, 76),    # 远香堂西南
        (72, 76),    # 远香堂东南
        (100, 42),   # 东岸
        (10, 20),    # 西北
        (105, 60),   # 东侧
        (50, 4),     # 北部
        (30, 82),    # 闺塾附近
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
        # stone_brick_wall 围边 (3x3 外围)
        for dx in range(-1, 2):
            for dz in range(-1, 2):
                if abs(dx) == 1 or abs(dz) == 1:
                    # 边沿
                    b.setblock(bx + dx, gy + 1, bz + dz,
                               "minecraft:stone_brick_wall")
                    bed_count += 1
                else:
                    # 中心: coarse_dirt + 花
                    b.setblock(bx, gy + 1, bz, "minecraft:coarse_dirt")
                    flower = RNG.choice(flowers_for_beds)
                    b.setblock(bx, gy + 2, bz, flower)
                    bed_count += 2
    print(f"    {bed_count} flower bed blocks")

    # ── 4c. 石凳 3-4组 ──
    print("  4c. Stone benches...")
    bench_spots = [
        (26, 46, "south"),    # 西岸观湖
        (72, 62, "west"),     # 东南望湖
        (46, 58, "north"),    # 荼蘼花架旁
        (16, 80, "east"),     # 闺塾西侧
    ]
    bench_count = 0
    for bx, bz, facing in bench_spots:
        if not _in_garden(bx, bz) or _is_occupied(bx, bz):
            continue
        gy = _ground_y(bx, bz)
        # 2格宽石凳
        b.setblock(bx, gy + 1, bz,
                   f"minecraft:stone_brick_stairs[facing={facing}]")
        bench_count += 1
        # 旁边加一个
        if facing in ("south", "north"):
            nx = bx + 1
            nz = bz
        else:
            nx = bx
            nz = bz + 1
        if _in_garden(nx, nz) and not _is_occupied(nx, nz):
            b.setblock(nx, gy + 1, nz,
                       f"minecraft:stone_brick_stairs[facing={facing}]")
            bench_count += 1
    print(f"    {bench_count} bench blocks")
    print(f"  Rock groups done. Commands so far: {b.cmd_count}")


# ═══════════════════════════════════════════
# 5. build_trees_and_plants — 树木 + 灌木 + 地被
# ═══════════════════════════════════════════

def _place_willow(b, x, gy, z):
    """垂柳: oak_log 主干 + oak_leaves 冠 + vine 垂挂"""
    trunk_h = RNG.randint(5, 7)
    for dy in range(1, trunk_h + 1):
        b.setblock(x, gy + dy, z, "minecraft:oak_log")
    top_y = gy + trunk_h
    # 树冠
    for dx in range(-3, 4):
        for dy in range(0, 3):
            for dz in range(-3, 4):
                if dx * dx + dz * dz <= 9 and (dy == 0 or dx * dx + dz * dz <= 5):
                    b.setblock(x + dx, top_y + dy, z + dz,
                               "minecraft:oak_leaves[persistent=true]")
    # 藤蔓: 冠缘垂 3-5 格
    for dx in range(-3, 4):
        for dz in range(-3, 4):
            if dx * dx + dz * dz >= 6 and dx * dx + dz * dz <= 10:
                if RNG.random() < 0.5:
                    vine_len = RNG.randint(3, 5)
                    facing = _vine_facing(dx, dz)
                    for dy in range(vine_len):
                        b.setblock(x + dx, top_y - dy, z + dz,
                                   f"minecraft:vine[{facing}=true]")


def _vine_facing(dx, dz):
    """根据偏移计算 vine 的朝向"""
    if abs(dx) >= abs(dz):
        return "west" if dx > 0 else "east"
    return "north" if dz > 0 else "south"


def _place_medium_tree(b, x, gy, z):
    """中型树: oak_log 4格 + oak_leaves 球冠"""
    trunk_h = RNG.randint(4, 5)
    for dy in range(1, trunk_h + 1):
        b.setblock(x, gy + dy, z, "minecraft:oak_log")
    top_y = gy + trunk_h
    # 球形冠 半径 2
    for dx in range(-2, 3):
        for dy in range(-1, 3):
            for dz in range(-2, 3):
                if dx * dx + dy * dy + dz * dz <= 5:
                    b.setblock(x + dx, top_y + dy, z + dz,
                               "minecraft:oak_leaves[persistent=true]")


def build_trees_and_plants(b: MinecraftBuilder):
    """5棵垂柳 + 3-5棵中型树 + 灌木 + 地被"""
    print("=== 5. Trees & Plants ===")

    # ── 5a. 垂柳沿湖岸 ──
    print("  5a. Weeping willows (lakeside)...")
    willow_spots = [
        (26, 36),    # 西岸
        (34, 50),    # 西南岸
        (70, 58),    # 东南岸
        (78, 36),    # 东岸
        (50, 60),    # 南岸
    ]
    willow_count = 0
    for wx, wz in willow_spots:
        if not _in_garden(wx, wz) or (wx, wz) in BUILDING_CORE_SET:
            continue
        gy = _ground_y(wx, wz)
        _place_willow(b, wx, gy, wz)
        willow_count += 1
    print(f"    {willow_count} willows")

    # ── 5b. 中型树（院中遮荫）──
    print("  5b. Medium shade trees...")
    tree_spots = [
        (40, 62),    # 远香堂前庭西
        (76, 62),    # 远香堂前庭东
        (12, 48),    # 西侧空地
        (100, 55),   # 东南角
        (22, 70),    # 闺塾附近
    ]
    tree_count = 0
    for tx, tz in tree_spots:
        if not _in_garden(tx, tz) or _is_occupied(tx, tz):
            continue
        gy = _ground_y(tx, tz)
        _place_medium_tree(b, tx, gy, tz)
        tree_count += 1
    print(f"    {tree_count} shade trees")

    # ── 5c. 灌木（flowering_azalea, azalea 散植石旁路边）30-40丛 ──
    print("  5c. Shrubs (azalea)...")
    shrub_count = 0
    # 沿廊道边缘每 5 格有概率种灌木
    for corridor in [cfg.MAIN_CORRIDOR, cfg.WEST_CORRIDOR]:
        wp = corridor["waypoints"]
        hw = corridor["width"] // 2 + 2  # 廊道边外2格
        for i in range(len(wp) - 1):
            pts = _lerp(wp[i], wp[i + 1])
            for j, (px, pz) in enumerate(pts):
                if j % 5 != 0:
                    continue
                # 廊道两侧
                for side_d in [hw, -hw]:
                    # 垂直于路径方向放置
                    sx, sz = px + side_d, pz
                    if not _in_garden(sx, sz) or _is_occupied(sx, sz):
                        sx, sz = px, pz + side_d
                        if not _in_garden(sx, sz) or _is_occupied(sx, sz):
                            continue
                    if RNG.random() < 0.5:
                        gy = _ground_y(sx, sz)
                        bush = ("minecraft:flowering_azalea"
                                if RNG.random() < 0.6 else "minecraft:azalea")
                        b.setblock(sx, gy + 1, sz, bush)
                        shrub_count += 1
    # 补充: 置石旁边也散植
    for rx, rz in rock_positions_for_shrubs():
        for dx, dz in [(2, 0), (-2, 0), (0, 2), (0, -2)]:
            sx, sz = rx + dx, rz + dz
            if _in_garden(sx, sz) and not _is_occupied(sx, sz) and RNG.random() < 0.4:
                gy = _ground_y(sx, sz)
                bush = ("minecraft:flowering_azalea"
                        if RNG.random() < 0.5 else "minecraft:azalea")
                b.setblock(sx, gy + 1, sz, bush)
                shrub_count += 1
    print(f"    {shrub_count} shrubs")

    # ── 5d. 地被覆盖: 空地15% fern/short_grass ──
    print("  5d. Ground cover (15% fern/short_grass)...")
    cover_count = 0
    # 网格采样每 3 格，概率15%
    for x in range(2, 119, 3):
        for z in range(2, 89, 3):
            if _is_occupied(x, z) or not _in_garden(x, z):
                continue
            if RNG.random() < 0.15:
                gy = _ground_y(x, z)
                block = ("minecraft:short_grass"
                         if RNG.random() < 0.6 else "minecraft:fern")
                b.setblock(x, gy + 1, z, block)
                cover_count += 1
    print(f"    {cover_count} ground cover plants")
    print(f"  Trees & plants done. Commands so far: {b.cmd_count}")


def rock_positions_for_shrubs():
    """返回置石位置子集（用于灌木布置参考）"""
    return [
        (14, 44), (25, 60), (40, 72), (70, 74),
        (98, 50), (100, 30), (45, 10), (30, 14),
    ]


# ═══════════════════════════════════════════
# 6. build_water_decor — 水面装饰
# ═══════════════════════════════════════════

def build_water_decor(b: MinecraftBuilder):
    """lily_pad 覆盖 10-15% + 浅水处 sugar_cane 菖蒲意象"""
    print("=== 6. Water Decoration ===")

    # ── 6a. 睡莲: 在指定中心点周围散布 ──
    print("  6a. Lily pads (10-15% water surface)...")
    lily_centers = cfg.LILY_PADS  # [(38,34), (36,40), (55,48), (70,44), (14,28)]
    lily_count = 0
    for lcx, lcz in lily_centers:
        for dx in range(-6, 7):
            for dz in range(-6, 7):
                x, z = lcx + dx, lcz + dz
                if not _is_water(x, z):
                    continue
                dist_sq = dx * dx + dz * dz
                if dist_sq > 36:
                    continue
                if RNG.random() < 0.18:
                    b.setblock(x, WY + 1, z, "minecraft:lily_pad")
                    lily_count += 1
    print(f"    {lily_count} lily pads")

    # ── 6b. 菖蒲（sugar_cane）: 浅水/岸边 ──
    print("  6b. Sugar cane (iris/calamus)...")
    # 在湖岸线内侧1-2格浅水处种
    cane_count = 0
    shoreline = cfg.MAIN_LAKE["shoreline"]
    for i in range(len(shoreline) - 1):
        pts = _lerp(shoreline[i], shoreline[(i + 1) % len(shoreline)])
        for j, (px, pz) in enumerate(pts):
            if j % 8 != 0:  # 每8格一丛
                continue
            if RNG.random() < 0.3:
                # 向湖心偏移1格
                cx, cz = cfg.MAIN_LAKE["center"]
                # 归一化方向向湖心
                ddx = cx - px
                ddz = cz - pz
                dist = max(1, math.sqrt(ddx * ddx + ddz * ddz))
                sx = px + round(ddx / dist)
                sz = pz + round(ddz / dist)
                if _is_water(sx, sz):
                    # sugar_cane 需要底下有沙子/泥土
                    b.setblock(sx, WY, sz, "minecraft:sand")
                    h = RNG.randint(2, 3)
                    for dy in range(1, h + 1):
                        b.setblock(sx, WY + dy, sz, "minecraft:sugar_cane")
                    cane_count += 1

    # 曲水溪旁也放几丛
    creek_cl = cfg.CREEK["centerline"]
    for i in range(0, len(creek_cl) - 1, 2):
        px, pz = creek_cl[i]
        if _is_water(px, pz) and RNG.random() < 0.5:
            b.setblock(px, WY, pz, "minecraft:sand")
            h = RNG.randint(2, 3)
            for dy in range(1, h + 1):
                b.setblock(px, WY + dy, pz, "minecraft:sugar_cane")
            cane_count += 1

    print(f"    {cane_count} sugar cane clusters")
    print(f"  Water decor done. Commands so far: {b.cmd_count}")


# ═══════════════════════════════════════════
# 主入口
# ═══════════════════════════════════════════

def build_all_landscape(b):
    _init_sets()
    build_paving(b)
    build_revetment(b)
    build_wall_planting(b)
    build_rock_groups(b)
    build_trees_and_plants(b)
    build_water_decor(b)


if __name__ == "__main__":
    with MinecraftBuilder() as b:
        build_all_landscape(b)
        print(f"\nDone! {b.cmd_count} commands")
