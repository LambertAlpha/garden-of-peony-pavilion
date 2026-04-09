"""phase4_details.py — 收尾脚本：植被 / 水面装饰 / 路面 / 做旧 / 灯笼 / 家具

牡丹亭·游园惊梦 — v3 Phase 4
把 10,800 格的园林从"毛坯"推到"实景"。
目标 < 3,000 命令。
"""

import sys
import math
import random

sys.path.insert(0, '/Users/lambertlin/minecraft-server/scripts')

from builder import MinecraftBuilder, bresenham_3d, filled_circle_points
import config_v3 as cfg
from blocks import PALETTE

# ═══════════════════════════════════════════
# 常量
# ═══════════════════════════════════════════

GY = cfg.GROUND_Y        # -61
BY = cfg.BUILD_Y          # -60
WY = cfg.WATER_SURFACE_Y  # -61
HY = cfg.HIGHLAND_Y       # -57

RNG = random.Random(2026)  # 固定种子，可重复

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


# ── 水面集合（预计算）──

def _build_water_set():
    """返回所有水面格子 (x,z) 的集合"""
    water = set()
    # 主湖
    sl = cfg.MAIN_LAKE["shoreline"]
    for z in range(_pmin(sl, 1), _pmax(sl, 1) + 1):
        for x in range(_pmin(sl, 0), _pmax(sl, 0) + 1):
            if point_in_polygon(x + 0.5, z + 0.5, sl):
                water.add((x, z))
    # 曲水溪流 — 沿中心线扩展
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


def _lerp(p1, p2):
    """简易 Bresenham XZ 插值"""
    x1, z1 = p1
    x2, z2 = p2
    pts = []
    dx, dz = abs(x2 - x1), abs(z2 - z1)
    sx = 1 if x2 > x1 else -1
    sz = 1 if z2 > z1 else -1
    steps = max(dx, dz)
    if steps == 0:
        return [(x1, z1)]
    x, z = x1, z1
    err = 0
    if dx >= dz:
        for _ in range(dx + 1):
            pts.append((x, z))
            err += dz
            if 2 * err >= dx:
                z += sz
                err -= dx
            x += sx
    else:
        for _ in range(dz + 1):
            pts.append((x, z))
            err += dx
            if 2 * err >= dz:
                x += sx
                err -= dz
            z += sz
    return pts


def _pmin(poly, idx):
    return min(p[idx] for p in poly)

def _pmax(poly, idx):
    return max(p[idx] for p in poly)


# ── 建筑占用集合 ──

def _build_building_set():
    """返回所有建筑占用格子 (x,z) 的集合（含1格散水缓冲）"""
    occ = set()
    for bld in cfg.ALL_BUILDINGS:
        cx = bld.get("cx", bld.get("x", 0))
        cz = bld.get("cz", bld.get("z", 0))
        sx = bld.get("size_x", 3)
        sz = bld.get("size_z", 3)
        hx, hz = sx // 2, sz // 2
        # 含 1 格缓冲
        for x in range(cx - hx - 1, cx + hx + 2):
            for z in range(cz - hz - 1, cz + hz + 2):
                occ.add((x, z))
    return occ


# ── 廊道占用集合 ──

def _build_corridor_set():
    """返回所有廊道占用格子 (x,z) 的集合"""
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


# ── 综合占用判断 ──

WATER_SET = None
BUILDING_SET = None
CORRIDOR_SET = None
BRIDGE_SET = None


def _init_sets():
    global WATER_SET, BUILDING_SET, CORRIDOR_SET, BRIDGE_SET
    print("  Pre-computing occupancy sets...")
    WATER_SET = _build_water_set()
    BUILDING_SET = _build_building_set()
    CORRIDOR_SET = _build_corridor_set()
    BRIDGE_SET = _build_bridge_set()
    print(f"    water={len(WATER_SET)} building={len(BUILDING_SET)} "
          f"corridor={len(CORRIDOR_SET)} bridge={len(BRIDGE_SET)}")


def _is_occupied(x, z):
    """点 (x,z) 是否被建筑/水面/廊道/桥占用"""
    return ((x, z) in WATER_SET or (x, z) in BUILDING_SET
            or (x, z) in CORRIDOR_SET or (x, z) in BRIDGE_SET)


def _is_hard_occupied(x, z):
    """严格占用: 只判建筑本体和水面（不含缓冲/廊道），用于种花"""
    if (x, z) in WATER_SET:
        return True
    # 建筑本体（无缓冲）
    for bld in cfg.ALL_BUILDINGS:
        cx = bld.get("cx", bld.get("x", 0))
        cz = bld.get("cz", bld.get("z", 0))
        sx = bld.get("size_x", 3)
        sz = bld.get("size_z", 3)
        hx, hz = sx // 2, sz // 2
        if cx - hx <= x <= cx + hx and cz - hz <= z <= cz + hz:
            return True
    return False


def _is_water(x, z):
    return (x, z) in WATER_SET


def _in_garden(x, z):
    return 1 <= x <= 119 and 1 <= z <= 89  # 围墙内


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
# 1. 植被系统
# ═══════════════════════════════════════════

def build_vegetation(b: MinecraftBuilder):
    print("=== 1. Vegetation ===")

    # ── 1a. 牡丹花圃: 牡丹亭 + 芍药阑 周围密植 peony / rose_bush ──
    print("  1a. Peony garden...")
    peony_centers = [
        (cfg.PEONY_PAVILION["cx"], cfg.PEONY_PAVILION["cz"]),
        (cfg.PEONY_RAIL["cx"], cfg.PEONY_RAIL["cz"]),
    ]
    peony_count = 0
    for ccx, ccz in peony_centers:
        for dx in range(-12, 13):
            for dz in range(-12, 13):
                x, z = ccx + dx, ccz + dz
                if not _in_garden(x, z) or _is_hard_occupied(x, z):
                    continue
                dist = math.sqrt(dx * dx + dz * dz)
                if dist > 12:
                    continue
                if RNG.random() < 0.35:
                    gy = _ground_y(x, z)
                    flower = PALETTE["peony"] if RNG.random() < 0.6 else PALETTE["rose"]
                    b.setblock(x, gy + 1, z, flower)
                    peony_count += 1
    print(f"    placed {peony_count} peonies/roses")

    # ── 1b. 梅林: 梅花庵旁 3-5 棵 cherry 树 ──
    print("  1b. Plum blossom grove...")
    plum_cx, plum_cz = cfg.PLUM_HERMITAGE["cx"], cfg.PLUM_HERMITAGE["cz"]
    plum_spots = [
        (plum_cx - 6, plum_cz - 2),
        (plum_cx - 4, plum_cz + 5),
        (plum_cx + 5, plum_cz - 4),
        (plum_cx + 6, plum_cz + 3),
    ]
    for tx, tz in plum_spots:
        if _is_occupied(tx, tz):
            continue
        gy = _ground_y(tx, tz)
        _place_cherry_tree(b, tx, gy, tz)
    print(f"    placed {len(plum_spots)} cherry trees")

    # ── 1c. 竹林: 翠轩旁 + 假山旁 ──
    print("  1c. Bamboo groves...")
    bamboo_zones = [
        (cfg.CUI_XUAN["cx"] - 12, cfg.CUI_XUAN["cz"] - 4,
         cfg.CUI_XUAN["cx"] - 6, cfg.CUI_XUAN["cz"] + 4),    # 翠轩西侧
        (cfg.TAIHU_ROCKS["cx"] - 10, cfg.TAIHU_ROCKS["cz"] - 2,
         cfg.TAIHU_ROCKS["cx"] - 4, cfg.TAIHU_ROCKS["cz"] + 4),  # 假山西侧
    ]
    bamboo_count = 0
    for bx1, bz1, bx2, bz2 in bamboo_zones:
        for x in range(bx1, bx2 + 1):
            for z in range(bz1, bz2 + 1):
                if not _in_garden(x, z) or _is_occupied(x, z):
                    continue
                if RNG.random() < 0.5:
                    gy = _ground_y(x, z)
                    h = RNG.randint(3, 6)
                    for dy in range(1, h + 1):
                        b.setblock(x, gy + dy, z, PALETTE["bamboo"])
                    bamboo_count += 1
    print(f"    placed {bamboo_count} bamboo stalks")

    # ── 1d. 垂杨: 湖岸 4-6 棵 ──
    print("  1d. Weeping willows...")
    for wx, wz in cfg.WILLOWS:
        if _is_occupied(wx, wz):
            continue
        gy = _ground_y(wx, wz)
        _place_willow(b, wx, gy, wz)
    print(f"    placed {len(cfg.WILLOWS)} willows")

    # ── 1e. 花丛: 5-6 处散花 ──
    print("  1e. Flower clusters...")
    flowers = [
        PALETTE["azalea"], PALETTE["tulip_red"], PALETTE["tulip_pink"],
        "minecraft:cornflower", "minecraft:oxeye_daisy",
    ]
    flower_count = 0
    for fcx, fcz in cfg.FLOWER_CLUSTERS:
        for dx in range(-3, 4):
            for dz in range(-3, 4):
                x, z = fcx + dx, fcz + dz
                if not _in_garden(x, z) or _is_occupied(x, z):
                    continue
                if RNG.random() < 0.4:
                    gy = _ground_y(x, z)
                    b.setblock(x, gy + 1, z, RNG.choice(flowers))
                    flower_count += 1
    print(f"    placed {flower_count} flowers")

    # ── 1f. 高草蕨: 空地 15% 覆盖 ──
    print("  1f. Tall grass & fern (sampling)...")
    grass_count = 0
    # 网格采样每 3 格一个候选点，降低循环量
    for x in range(2, 119, 3):
        for z in range(2, 89, 3):
            if _is_occupied(x, z) or not _in_garden(x, z):
                continue
            if RNG.random() < 0.15:
                gy = _ground_y(x, z)
                block = PALETTE["tall_grass"] if RNG.random() < 0.7 else PALETTE["fern"]
                b.setblock(x, gy + 1, z, block)
                grass_count += 1
    print(f"    placed {grass_count} grass/fern")

    print(f"  Vegetation done. Commands: {b.cmd_count}")


def _place_cherry_tree(b, x, gy, z):
    """种一棵樱花树（模拟梅花），trunk 4 格 + 球形冠"""
    trunk_h = RNG.randint(4, 5)
    for dy in range(1, trunk_h + 1):
        b.setblock(x, gy + dy, z, PALETTE["cherry_log"])
    # 树冠: 半径 2 的球形 cherry_leaves
    top_y = gy + trunk_h
    for dx in range(-2, 3):
        for dy in range(-1, 3):
            for dz in range(-2, 3):
                if dx * dx + dy * dy + dz * dz <= 5:
                    b.setblock(x + dx, top_y + dy, z + dz, PALETTE["cherry_leaves"])


def _place_willow(b, x, gy, z):
    """种一棵垂杨: oak_log 主干 + oak_leaves 冠 + vine 垂挂"""
    trunk_h = RNG.randint(5, 7)
    for dy in range(1, trunk_h + 1):
        b.setblock(x, gy + dy, z, PALETTE["oak_log"])
    top_y = gy + trunk_h
    # 树冠
    for dx in range(-3, 4):
        for dy in range(0, 3):
            for dz in range(-3, 4):
                if dx * dx + dz * dz <= 9 and (dy == 0 or dx * dx + dz * dz <= 5):
                    b.setblock(x + dx, top_y + dy, z + dz, PALETTE["oak_leaves"])
    # 藤蔓: 冠缘向下垂 3-5 格
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
    """根据偏移计算 vine 的朝向（vine 需要贴附面）"""
    if abs(dx) >= abs(dz):
        return "west" if dx > 0 else "east"
    return "north" if dz > 0 else "south"


# ═══════════════════════════════════════════
# 2. 水面装饰
# ═══════════════════════════════════════════

def build_water_decor(b: MinecraftBuilder):
    print("=== 2. Water Decoration ===")

    # ── 2a. 睡莲: 10-15% 水面覆盖 ──
    print("  2a. Lily pads...")
    lily_count = 0
    # 在配置指定的睡莲中心点周围散布
    for lcx, lcz in cfg.LILY_PADS:
        for dx in range(-5, 6):
            for dz in range(-5, 6):
                x, z = lcx + dx, lcz + dz
                if not _is_water(x, z):
                    continue
                dist_sq = dx * dx + dz * dz
                if dist_sq > 25:
                    continue
                if RNG.random() < 0.25:
                    b.setblock(x, WY + 1, z, PALETTE["lily"])
                    lily_count += 1
    print(f"    placed {lily_count} lily pads")

    # ── 2b. 湖心岛松树 ──
    # 偏离主桥 (x=58, z=38-50)，放在湖中偏西处
    print("  2b. Lake island spruce...")
    island_x, island_z = 50, 48  # 湖中偏西南，避开主桥
    # 小岛 3x3 草地
    for dx in range(-1, 2):
        for dz in range(-1, 2):
            b.setblock(island_x + dx, WY, island_z + dz, "minecraft:grass_block")
    # 松树
    trunk_h = 6
    for dy in range(1, trunk_h + 1):
        b.setblock(island_x, WY + dy, island_z, "minecraft:spruce_log")
    # 松树冠: 锥形
    for layer, (r, dy) in enumerate([
        (1, trunk_h + 2), (2, trunk_h + 1), (2, trunk_h),
        (3, trunk_h - 1), (3, trunk_h - 2), (1, trunk_h - 3),
    ]):
        for dx in range(-r, r + 1):
            for dz in range(-r, r + 1):
                if dx * dx + dz * dz <= r * r:
                    b.setblock(island_x + dx, WY + dy, island_z + dz,
                               PALETTE["spruce_leaves"])

    print(f"  Water decor done. Commands: {b.cmd_count}")


# ═══════════════════════════════════════════
# 3. 路面铺装
# ═══════════════════════════════════════════

def build_ground_cover(b: MinecraftBuilder):
    print("=== 3. Ground Cover ===")

    # ── 3a. 建筑散水带（每栋外围 1 格 polished_andesite, fill 四条边）──
    print("  3a. Building aprons...")
    apron_count = 0
    for bld in cfg.ALL_BUILDINGS:
        cx = bld.get("cx", bld.get("x", 0))
        cz = bld.get("cz", bld.get("z", 0))
        sx = bld.get("size_x", 3)
        sz = bld.get("size_z", 3)
        hx, hz = sx // 2, sz // 2
        gy = bld.get("ground_y", GY)
        if bld.get("over_water"):
            continue  # 水上建筑不需要散水

        ax1, ax2 = cx - hx - 1, cx + hx + 1
        az1, az2 = cz - hz - 1, cz + hz + 1
        # 四条边各一次 fill (1格宽条带)
        b.fill(ax1, gy, az1, ax2, gy, az1, PALETTE["base_col"],
               "replace minecraft:grass_block")  # 北边
        b.fill(ax1, gy, az2, ax2, gy, az2, PALETTE["base_col"],
               "replace minecraft:grass_block")  # 南边
        b.fill(ax1, gy, az1 + 1, ax1, gy, az2 - 1, PALETTE["base_col"],
               "replace minecraft:grass_block")  # 西边
        b.fill(ax2, gy, az1 + 1, ax2, gy, az2 - 1, PALETTE["base_col"],
               "replace minecraft:grass_block")  # 东边
        apron_count += 4
    print(f"    {apron_count} apron fill ops")

    # ── 3b. 建筑间路面（stone_bricks + andesite 混铺）──
    # 用 fill 沿廊道 waypoints 铺路面
    print("  3b. Corridor paving...")
    paving_count = 0
    for corridor in [cfg.MAIN_CORRIDOR, cfg.WEST_CORRIDOR]:
        wp = corridor["waypoints"]
        hw = corridor["width"] // 2
        for i in range(len(wp) - 1):
            # 逐段 fill
            x1, z1 = wp[i]
            x2, z2 = wp[i + 1]
            # 用包围盒 fill 更高效
            fx1, fx2 = min(x1, x2) - hw, max(x1, x2) + hw
            fz1, fz2 = min(z1, z2) - hw, max(z1, z2) + hw
            block = PALETTE["floor_alt"] if i % 2 == 0 else "minecraft:andesite"
            b.fill(fx1, BY, fz1, fx2, BY, fz2, block, "replace minecraft:grass_block")
            paving_count += 1
    # 次路径
    for sp in cfg.SECONDARY_PATHS:
        wp = sp["waypoints"]
        hw = sp["width"] // 2
        surface = sp.get("surface", "stone_bricks")
        mc_block = f"minecraft:{surface}"
        for i in range(len(wp) - 1):
            x1, z1 = wp[i]
            x2, z2 = wp[i + 1]
            fx1, fx2 = min(x1, x2) - hw, max(x1, x2) + hw
            fz1, fz2 = min(z1, z2) - hw, max(z1, z2) + hw
            b.fill(fx1, BY, fz1, fx2, BY, fz2, mc_block, "replace minecraft:grass_block")
            paving_count += 1
    # 北岸石径
    wp = cfg.HIGHLAND_PATH["waypoints"]
    hw = cfg.HIGHLAND_PATH["width"] // 2
    for i in range(len(wp) - 1):
        x1, z1 = wp[i]
        x2, z2 = wp[i + 1]
        fx1, fx2 = min(x1, x2) - hw, max(x1, x2) + hw
        fz1, fz2 = min(z1, z2) - hw, max(z1, z2) + hw
        b.fill(fx1, BY, fz1, fx2, BY, fz2, "minecraft:stone_bricks",
               "replace minecraft:grass_block")
        paving_count += 1
    print(f"    {paving_count} paving fill ops")

    # ── 3c. 空地用 coarse_dirt + moss_block 覆盖 ──
    # 网格采样，替换残留草地
    print("  3c. Open ground patching...")
    patch_count = 0
    for x in range(2, 119, 4):
        for z in range(2, 89, 4):
            if _is_occupied(x, z) or not _in_garden(x, z):
                continue
            gy = _ground_y(x, z)
            block = PALETTE["moss"] if RNG.random() < 0.3 else "minecraft:coarse_dirt"
            # 用 fill 2x2 覆盖更高效
            x2 = min(x + 1, 119)
            z2 = min(z + 1, 89)
            b.fill(x, gy, z, x2, gy, z2, block, "replace minecraft:grass_block")
            patch_count += 1
    print(f"    {patch_count} ground patches")

    print(f"  Ground cover done. Commands: {b.cmd_count}")


# ═══════════════════════════════════════════
# 4. 做旧效果
# ═══════════════════════════════════════════

def build_weathering(b: MinecraftBuilder):
    print("=== 4. Weathering ===")
    wall = cfg.WALL
    perimeter = wall["perimeter"]
    h = wall["height"]  # 5

    # 围墙段: 北(z=0), 东(x=120), 南(z=90), 西(x=0)
    wall_segments = [
        # (x1, z1, x2, z2)
        (0, 0, 120, 0),     # 北墙
        (120, 0, 120, 90),  # 东墙
        (0, 90, 120, 90),   # 南墙
        (0, 0, 0, 90),      # 西墙
    ]

    # ── 4a. 围墙 10% → mossy_stone_bricks (散点) ──
    print("  4a. Mossy wall bricks...")
    mossy_count = 0
    for x1, z1, x2, z2 in wall_segments:
        for x in range(min(x1, x2), max(x1, x2) + 1):
            for z in range(min(z1, z2), max(z1, z2) + 1):
                for y in range(BY, BY + h):
                    if RNG.random() < 0.10:
                        b.setblock(x, y, z, PALETTE["wall_mossy"])
                        mossy_count += 1
    print(f"    placed {mossy_count} mossy bricks")

    # ── 4b. 围墙 5% → cracked_stone_bricks ──
    print("  4b. Cracked bricks...")
    cracked_count = 0
    for x1, z1, x2, z2 in wall_segments:
        for x in range(min(x1, x2), max(x1, x2) + 1):
            for z in range(min(z1, z2), max(z1, z2) + 1):
                for y in range(BY, BY + h):
                    if RNG.random() < 0.05:
                        b.setblock(x, y, z, PALETTE["wall_cracked"])
                        cracked_count += 1
    print(f"    placed {cracked_count} cracked bricks")

    # ── 4c. 围墙内侧 5% 挂 vine ──
    print("  4c. Wall vines...")
    vine_count = 0
    # 内侧面: 北墙内侧=z=1 south facing, 南墙内侧=z=89 north facing,
    #          东墙内侧=x=119 west facing, 西墙内侧=x=1 east facing
    inner_walls = [
        (1, 120, 1, 1, "south"),    # 北墙内侧
        (1, 120, 89, 89, "north"),  # 南墙内侧
    ]
    for xi1, xi2, zi1, zi2, facing in inner_walls:
        for x in range(xi1, xi2):
            z = zi1
            for y in range(BY + 1, BY + h):
                if RNG.random() < 0.05:
                    b.setblock(x, y, z, f"minecraft:vine[{facing}=true]")
                    vine_count += 1
    # 东西墙内侧
    for z in range(1, 90):
        for y in range(BY + 1, BY + h):
            if RNG.random() < 0.05:
                b.setblock(119, y, z, "minecraft:vine[west=true]")
                vine_count += 1
            if RNG.random() < 0.05:
                b.setblock(1, y, z, "minecraft:vine[east=true]")
                vine_count += 1
    print(f"    placed {vine_count} vines")

    # ── 4d. 断井 2-3 口 ──
    print("  4d. Ruined wells...")
    for wx, wz in cfg.WELLS:
        gy = _ground_y(wx, wz)
        # 3x3 cobblestone 围，中空，深 3 格
        for dx in range(-1, 2):
            for dz in range(-1, 2):
                if dx == 0 and dz == 0:
                    # 中空部分: 挖深
                    for dy in range(-2, 1):
                        b.setblock(wx, gy + dy, wz, "minecraft:air")
                    b.setblock(wx, gy - 3, wz, "minecraft:water")
                else:
                    # 围壁
                    wall_block = (PALETTE["mossy_cobblestone"]
                                  if RNG.random() < 0.4 else PALETTE["cobblestone"])
                    b.setblock(wx + dx, gy, wz + dz, wall_block)
                    b.setblock(wx + dx, gy + 1, wz + dz, wall_block)
    print(f"    placed {len(cfg.WELLS)} wells")

    print(f"  Weathering done. Commands: {b.cmd_count}")


# ═══════════════════════════════════════════
# 5. 灯笼补充
# ═══════════════════════════════════════════

def build_lanterns(b: MinecraftBuilder):
    print("=== 5. Lanterns ===")
    lantern_count = 0

    # ── 5a. 廊道每 8 格一盏 ──
    print("  5a. Corridor lanterns...")
    for corridor in [cfg.MAIN_CORRIDOR, cfg.WEST_CORRIDOR]:
        wp = corridor["waypoints"]
        pillar_h = corridor.get("pillar_h", 4)
        for i in range(len(wp) - 1):
            pts = _lerp(wp[i], wp[i + 1])
            for j, (px, pz) in enumerate(pts):
                if j % 8 == 0:
                    gy = _ground_y(px, pz)
                    # 挂在廊顶下方 (pillar_h - 1)
                    b.setblock(px, gy + pillar_h, pz,
                               "minecraft:lantern[hanging=true]")
                    lantern_count += 1

    # ── 5b. 桥头各 1 盏 ──
    print("  5b. Bridge lanterns...")
    for br in cfg.ALL_BRIDGES:
        if "z_start" in br:
            cx = br["cx"]
            b.setblock(cx, BY + 2, br["z_start"], PALETTE["lantern"])
            b.setblock(cx, BY + 2, br["z_end"], PALETTE["lantern"])
            lantern_count += 2
        elif "waypoints" in br:
            wp = br["waypoints"]
            sx, sz = wp[0]
            ex, ez = wp[-1]
            b.setblock(sx, BY + 2, sz, PALETTE["lantern"])
            b.setblock(ex, BY + 2, ez, PALETTE["lantern"])
            lantern_count += 2
        elif "stones" in br:
            # 汀步石头旁放一盏
            sx, sz = br["stones"][1]
            b.setblock(sx, BY + 2, sz, PALETTE["lantern"])
            lantern_count += 1

    # ── 5c. 建筑入口各 1 盏 ──
    print("  5c. Building entrance lanterns...")
    for bld in cfg.ALL_BUILDINGS:
        facing = bld.get("facing")
        if facing is None or facing == "all":
            continue
        cx = bld.get("cx", bld.get("x", 0))
        cz = bld.get("cz", bld.get("z", 0))
        sx = bld.get("size_x", 3)
        sz = bld.get("size_z", 3)
        hx, hz = sx // 2, sz // 2
        gy = bld.get("ground_y", GY)
        ph = bld.get("pillar_h", 4)

        # 入口侧中心放一盏灯
        if facing == "south":
            lx, lz = cx, cz + hz + 1
        elif facing == "north":
            lx, lz = cx, cz - hz - 1
        elif facing == "east":
            lx, lz = cx + hx + 1, cz
        elif facing == "west":
            lx, lz = cx - hx - 1, cz
        elif facing == "northwest":
            lx, lz = cx - hx - 1, cz - hz - 1
        else:
            continue

        if _in_garden(lx, lz) and not _is_water(lx, lz):
            b.setblock(lx, gy + ph, lz, "minecraft:lantern[hanging=true]")
            lantern_count += 1

    print(f"    total {lantern_count} lanterns")
    print(f"  Lanterns done. Commands: {b.cmd_count}")


# ═══════════════════════════════════════════
# 6. 家具 / 小品
# ═══════════════════════════════════════════

def build_furniture(b: MinecraftBuilder):
    print("=== 6. Furniture ===")

    # ── 6a. 石桌石凳 3-4 组 ──
    print("  6a. Stone table sets...")
    table_spots = [
        (cfg.CUI_XUAN["cx"] + 10, cfg.CUI_XUAN["cz"]),       # 翠轩东侧
        (cfg.YUAN_XIANG["cx"] - 12, cfg.YUAN_XIANG["cz"]),    # 远香堂西侧
        (cfg.TING_YU_XUAN["cx"] + 6, cfg.TING_YU_XUAN["cz"]), # 听雨轩旁
        (cfg.GUI_SHU["cx"] + 6, cfg.GUI_SHU["cz"]),           # 闺塾旁
    ]
    for tx, tz in table_spots:
        if _is_occupied(tx, tz):
            continue
        gy = _ground_y(tx, tz)
        # 桌: 中心一个 stone_brick_slab
        b.setblock(tx, gy + 1, tz, "minecraft:stone_brick_slab")
        # 凳: 四方向 stairs (面朝桌子)
        seats = [
            (tx - 1, tz, "east"), (tx + 1, tz, "west"),
            (tx, tz - 1, "south"), (tx, tz + 1, "north"),
        ]
        for sx, sz, face in seats:
            if _in_garden(sx, sz) and not _is_occupied(sx, sz):
                b.setblock(sx, gy + 1, sz,
                           f"minecraft:stone_brick_stairs[facing={face}]")
    print(f"    placed {len(table_spots)} table sets")

    # ── 6b. 花盆 5-6 个 ──
    print("  6b. Flower pots...")
    pot_spots = [
        (cfg.PEONY_PAVILION["cx"] + 2, cfg.PEONY_PAVILION["cz"] + 2),
        (cfg.YUAN_XIANG["cx"] + 2, cfg.YUAN_XIANG["cz"] - 2),
        (cfg.CUI_XUAN["cx"] + 2, cfg.CUI_XUAN["cz"] - 2),
        (cfg.GATE["cx"] - 3, cfg.GATE["cz"]),
        (cfg.GATE["cx"] + 3, cfg.GATE["cz"]),
        (cfg.GUI_SHU["cx"] - 2, cfg.GUI_SHU["cz"] + 2),
    ]
    for px, pz in pot_spots:
        gy = _ground_y(px, pz)
        b.setblock(px, gy + 1, pz, "minecraft:flower_pot")
    print(f"    placed {len(pot_spots)} flower pots")

    print(f"  Furniture done. Commands: {b.cmd_count}")


# ═══════════════════════════════════════════
# main
# ═══════════════════════════════════════════

if __name__ == "__main__":
    with MinecraftBuilder() as b:
        _init_sets()
        build_vegetation(b)
        build_water_decor(b)
        build_ground_cover(b)
        build_weathering(b)
        build_lanterns(b)
        build_furniture(b)
        print(f"Done! {b.cmd_count} commands")
