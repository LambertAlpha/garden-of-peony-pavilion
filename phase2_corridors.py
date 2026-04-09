"""phase2_corridors.py — 廊道骨架 + 围墙 + 墙体分隔

牡丹亭·游园惊梦 — v3 Phase 2
包含: 外围墙、内部花墙(月洞门)、主环廊+西段廊、桥梁

命令预算 < 3000
"""

import sys
import math

sys.path.insert(0, '/Users/lambertlin/minecraft-server/scripts')

from builder import MinecraftBuilder, bresenham_3d, filled_circle_points
import config_v3 as cfg
from phase1_water import point_in_polygon


# ═══════════════════════════════════════════
# 水面检测
# ═══════════════════════════════════════════

def _all_water_polygons():
    """返回所有水面多边形（用于碰撞检测）"""
    return [
        cfg.MAIN_LAKE["shoreline"],
        cfg.DEEP_POOL["shoreline"],
    ]


def _point_in_any_water(x, z, margin=1):
    """检查 (x,z) 是否在任何水面多边形内（含 margin 格缓冲）"""
    for poly in _all_water_polygons():
        if point_in_polygon(x, z, poly):
            return True
    # 检查曲水溪流（用中心线 + 宽度近似）
    for i, (cx, cz) in enumerate(cfg.CREEK["centerline"]):
        w = cfg.CREEK["widths"][i] / 2 + margin
        if abs(x - cx) <= w and abs(z - cz) <= w:
            return True
    # 检查翠轩前小池（椭圆）
    p = cfg.CREEK_POOL
    dx = x - p["cx"]
    dz = z - p["cz"]
    rx = p["rx"] + margin
    rz = p["rz"] + margin
    if (dx * dx) / (rx * rx) + (dz * dz) / (rz * rz) <= 1.0:
        return True
    return False


# ═══════════════════════════════════════════
# 地面高度查询
# ═══════════════════════════════════════════

def _ground_y_at(x, z):
    """查询 (x,z) 处的地面高度"""
    for zone in cfg.TERRAIN_ZONES:
        if zone["name"] == "标准地面":
            continue
        x_min, x_max = zone["x_range"]
        z_min, z_max = zone["z_range"]
        if x_min <= x <= x_max and z_min <= z <= z_max:
            slope = zone.get("slope")
            if slope and slope["z_start"] <= z <= slope["z_end"]:
                t = (z - slope["z_start"]) / (slope["z_end"] - slope["z_start"])
                return round(slope["y_start"] + t * (slope["y_end"] - slope["y_start"]))
            elif slope and z > slope["z_end"]:
                return slope["y_end"]
            return zone["ground_y"]
    return cfg.BUILD_Y  # -60


# ═══════════════════════════════════════════
# 1. 外围墙
# ═══════════════════════════════════════════

def build_outer_wall(b: MinecraftBuilder):
    """围墙沿 120x90 边界
    结构: 墙基1(石砖) + 墙身2(白色混凝土) + 压瓦1(石砖半砖) = 高4格
    南墙留入口缺口，每面墙有漏窗(iron_bars)
    """
    print("=== Building Outer Wall ===")

    w = cfg.WALL
    base_y = cfg.BUILD_Y       # -60
    wall_base = "minecraft:stone_bricks"
    wall_body = "minecraft:white_concrete"
    wall_cap = "minecraft:stone_brick_slab[type=bottom]"
    lattice = "minecraft:iron_bars"

    gap_x_min, gap_x_max = w["south_gap"]  # (50, 66)

    # --- 北墙 (z=0, x=0..120) ---
    b.fill(0, base_y, 0, 120, base_y, 0, wall_base)          # 墙基
    b.fill(0, base_y + 1, 0, 120, base_y + 2, 0, wall_body)  # 墙身
    b.fill(0, base_y + 3, 0, 120, base_y + 3, 0, wall_cap)   # 压瓦

    # --- 南墙 (z=90, x=0..120) 留缺口 ---
    # 西段
    if gap_x_min > 0:
        b.fill(0, base_y, 90, gap_x_min - 1, base_y, 90, wall_base)
        b.fill(0, base_y + 1, 90, gap_x_min - 1, base_y + 2, 90, wall_body)
        b.fill(0, base_y + 3, 90, gap_x_min - 1, base_y + 3, 90, wall_cap)
    # 东段
    if gap_x_max < 120:
        b.fill(gap_x_max + 1, base_y, 90, 120, base_y, 90, wall_base)
        b.fill(gap_x_max + 1, base_y + 1, 90, 120, base_y + 2, 90, wall_body)
        b.fill(gap_x_max + 1, base_y + 3, 90, 120, base_y + 3, 90, wall_cap)

    # --- 西墙 (x=0, z=0..90) ---
    b.fill(0, base_y, 0, 0, base_y, 90, wall_base)
    b.fill(0, base_y + 1, 0, 0, base_y + 2, 90, wall_body)
    b.fill(0, base_y + 3, 0, 0, base_y + 3, 90, wall_cap)

    # --- 东墙 (x=120, z=0..90) ---
    b.fill(120, base_y, 0, 120, base_y, 90, wall_base)
    b.fill(120, base_y + 1, 0, 120, base_y + 2, 90, wall_body)
    b.fill(120, base_y + 3, 0, 120, base_y + 3, 90, wall_cap)

    # --- 漏窗 (每面墙 2-3 个) ---
    for lw in w["lattice_windows"]:
        wall_side = lw["wall"]
        if wall_side == "east":
            z = lw["z"]
            # 在墙身中间层开 3 格宽漏窗
            b.fill(120, base_y + 1, z - 1, 120, base_y + 2, z + 1, lattice)
        elif wall_side == "west":
            z = lw["z"]
            b.fill(0, base_y + 1, z - 1, 0, base_y + 2, z + 1, lattice)
        elif wall_side == "north":
            x = lw["x"]
            b.fill(x - 1, base_y + 1, 0, x + 1, base_y + 2, 0, lattice)

    # --- 东墙月洞门 ---
    for mg in w["moon_gates"]:
        if mg["wall"] == "east":
            z_c = mg["z"]
            r = mg["radius"]
            cy = base_y + r  # 圆心 Y
            # 用 circle_yz 开圆洞
            for dy, dz in filled_circle_points(0, 0, r):
                py = cy + dy
                pz = z_c + dz
                if base_y <= py <= base_y + 3 and 0 <= pz <= 90:
                    b.setblock(120, py, pz, "minecraft:air")

    print(f"  Outer wall done. Commands: {b.cmd_count}")


# ═══════════════════════════════════════════
# 2. 内部花墙 + 月洞门
# ═══════════════════════════════════════════

# 内部分隔定义（从总平面图推导）
# 前园(入口区 z=72..90) / 主园(湖区 z=20..72) / 后园(牡丹亭区 z=0..20)
INNER_WALLS = [
    {
        "name": "前/主园分隔墙",
        "axis": "x",             # 沿 X 方向延伸（Z 固定）
        "z": 72,
        "x_range": (40, 76),     # 不贯穿全宽，两端留通道
        "moon_gate": {"x": 58, "radius": 2},  # 正中月洞门
        "skip_water": True,
    },
    {
        "name": "牡丹亭园中园东墙",
        "axis": "z",             # 沿 Z 方向延伸（X 固定）
        "x": 72,
        "z_range": (4, 25),
        "moon_gate": {"z": 16, "radius": 2},
        "skip_water": True,
    },
    {
        "name": "牡丹亭园中园西墙",
        "axis": "z",
        "x": 44,
        "z_range": (4, 25),
        "moon_gate": {"z": 16, "radius": 2},
        "skip_water": True,
    },
    {
        "name": "牡丹亭园中园北墙",
        "axis": "x",
        "z": 4,
        "x_range": (44, 72),
        "moon_gate": {"x": 58, "radius": 2},
        "skip_water": False,
    },
]


def build_inner_walls(b: MinecraftBuilder):
    """内部花墙 — 白墙+月洞门
    花墙高3格（墙基1+墙身1+压瓦1），比外墙矮
    月洞门用 filled_circle 开圆
    """
    print("=== Building Inner Walls ===")

    wall_base = "minecraft:stone_bricks"
    wall_body = "minecraft:white_concrete"
    wall_cap = "minecraft:stone_brick_slab[type=bottom]"

    for wall_def in INNER_WALLS:
        name = wall_def["name"]
        axis = wall_def["axis"]
        skip_water = wall_def.get("skip_water", True)
        mg = wall_def.get("moon_gate")

        if axis == "x":
            # 墙沿 X 方向，Z 固定
            z = wall_def["z"]
            x_min, x_max = wall_def["x_range"]
            gy = _ground_y_at(x_min, z)
            base_y = gy

            # 用 fill 铺墙（后面再开月洞门）
            # 跳过水面格子 —— 先收集非水 x 区间
            if skip_water:
                safe_ranges = _safe_x_ranges(x_min, x_max, z)
            else:
                safe_ranges = [(x_min, x_max)]

            for sx, ex in safe_ranges:
                b.fill(sx, base_y, z, ex, base_y, z, wall_base)
                b.fill(sx, base_y + 1, z, ex, base_y + 1, z, wall_body)
                b.fill(sx, base_y + 2, z, ex, base_y + 2, z, wall_cap)

            # 月洞门 — 在 XY 平面开圆（朝南北方向）
            if mg:
                mg_x = mg["x"]
                r = mg["radius"]
                cy = base_y + r  # 圆心 Y
                for dx, dy in filled_circle_points(0, 0, r):
                    px = mg_x + dx
                    py = cy + dy
                    if x_min <= px <= x_max and base_y <= py <= base_y + 2:
                        b.setblock(px, py, z, "minecraft:air")

        elif axis == "z":
            # 墙沿 Z 方向，X 固定
            x = wall_def["x"]
            z_min, z_max = wall_def["z_range"]
            gy = _ground_y_at(x, z_min)
            base_y = gy

            if skip_water:
                safe_ranges = _safe_z_ranges(z_min, z_max, x)
            else:
                safe_ranges = [(z_min, z_max)]

            for sz, ez in safe_ranges:
                b.fill(x, base_y, sz, x, base_y, ez, wall_base)
                b.fill(x, base_y + 1, sz, x, base_y + 1, ez, wall_body)
                b.fill(x, base_y + 2, sz, x, base_y + 2, ez, wall_cap)

            # 月洞门 — 在 YZ 平面开圆（朝东西方向）
            if mg:
                mg_z = mg["z"]
                r = mg["radius"]
                cy = base_y + r
                for dy, dz in filled_circle_points(0, 0, r):
                    pz = mg_z + dz
                    py = cy + dy
                    if z_min <= pz <= z_max and base_y <= py <= base_y + 2:
                        b.setblock(x, py, pz, "minecraft:air")

        print(f"  {name} done.")

    print(f"  Inner walls done. Commands: {b.cmd_count}")


def _safe_x_ranges(x_min, x_max, z):
    """返回 [x_min, x_max] 中不在水面上的连续 X 区间"""
    safe = []
    start = None
    for x in range(x_min, x_max + 1):
        if not _point_in_any_water(x, z):
            if start is None:
                start = x
        else:
            if start is not None:
                safe.append((start, x - 1))
                start = None
    if start is not None:
        safe.append((start, x_max))
    return safe


def _safe_z_ranges(z_min, z_max, x):
    """返回 [z_min, z_max] 中不在水面上的连续 Z 区间"""
    safe = []
    start = None
    for z in range(z_min, z_max + 1):
        if not _point_in_any_water(x, z):
            if start is None:
                start = z
        else:
            if start is not None:
                safe.append((start, z - 1))
                start = None
    if start is not None:
        safe.append((start, z_max))
    return safe


# ═══════════════════════════════════════════
# 3. 廊道
# ═══════════════════════════════════════════

def _corridor_segment(b, x1, z1, x2, z2, width, roofed, pillar_h, pillar_space):
    """在两个 waypoint 之间建造一段廊道。

    结构（截面）:
      - 地面: smooth_stone (走道) + stone_bricks (柱位)
      - 柱子: stripped_crimson_stem，每 pillar_space 格一根，高 pillar_h
      - 栏杆: crimson_fence，柱间
      - 屋顶: stone_brick_slab（仅 roofed=True）

    返回实际放置的命令数增量。
    """
    pillar = "minecraft:stripped_crimson_stem"
    rail = "minecraft:crimson_fence"
    floor_main = "minecraft:smooth_stone"
    floor_alt = "minecraft:stone_bricks"
    roof_slab = "minecraft:stone_brick_slab[type=bottom]"

    # 计算两点间的 Bresenham 线
    from builder import bresenham_3d
    points_3d = bresenham_3d(x1, 0, z1, x2, 0, z2)
    centerline = [(p[0], p[2]) for p in points_3d]

    # 去重
    seen = set()
    unique = []
    for p in centerline:
        if p not in seen:
            seen.add(p)
            unique.append(p)
    centerline = unique

    half_w = width // 2

    # 确定主方向（用于决定栏杆在哪一侧）
    dx = abs(x2 - x1)
    dz = abs(z2 - z1)
    # 主方向为位移较大的轴
    is_x_major = dx >= dz

    # 按中心线逐格建造
    for idx, (cx, cz) in enumerate(centerline):
        gy = _ground_y_at(cx, cz)

        # 铺地面（宽度范围）
        if is_x_major:
            b.fill(cx, gy, cz - half_w, cx, gy, cz + half_w, floor_main)
        else:
            b.fill(cx - half_w, gy, cz, cx + half_w, gy, cz, floor_main)

        # 每 pillar_space 格放柱子+栏杆
        is_pillar = (idx % pillar_space == 0)

        if is_pillar:
            if is_x_major:
                # 柱子在两侧 (cz - half_w, cz + half_w)
                for side_z in [cz - half_w, cz + half_w]:
                    # 柱础
                    b.setblock(cx, gy, side_z, floor_alt)
                    # 柱身
                    for dy in range(1, pillar_h + 1):
                        b.setblock(cx, gy + dy, side_z, pillar)
            else:
                for side_x in [cx - half_w, cx + half_w]:
                    b.setblock(side_x, gy, cz, floor_alt)
                    for dy in range(1, pillar_h + 1):
                        b.setblock(side_x, gy + dy, cz, pillar)
        else:
            # 非柱位：放栏杆（只在 roofed 的廊道两侧）
            if roofed:
                if is_x_major:
                    for side_z in [cz - half_w, cz + half_w]:
                        b.setblock(cx, gy + 1, side_z, rail)
                else:
                    for side_x in [cx - half_w, cx + half_w]:
                        b.setblock(side_x, gy + 1, cz, rail)

        # 屋顶
        if roofed:
            roof_y = gy + pillar_h + 1
            if is_x_major:
                # 屋顶比走道宽 1 格（出檐）
                b.fill(cx, roof_y, cz - half_w - 1, cx, roof_y, cz + half_w + 1, roof_slab)
            else:
                b.fill(cx - half_w - 1, roof_y, cz, cx + half_w + 1, roof_y, cz, roof_slab)


def _build_corridor_from_config(b, corridor_cfg):
    """从 config 的廊道定义建造整条廊道"""
    waypoints = corridor_cfg["waypoints"]
    width = corridor_cfg["width"]
    pillar_h = corridor_cfg.get("pillar_h", 4)
    pillar_space = corridor_cfg.get("pillar_space", 4)
    roofed = corridor_cfg.get("roofed", True)

    for i in range(len(waypoints) - 1):
        x1, z1 = waypoints[i]
        x2, z2 = waypoints[i + 1]

        # 验证 waypoint 不在水面上
        skip = False
        for wx, wz in [(x1, z1), (x2, z2)]:
            if _point_in_any_water(wx, wz, margin=0):
                print(f"  WARNING: waypoint ({wx},{wz}) is in water! Skipping segment.")
                skip = True
                break
        if skip:
            continue

        _corridor_segment(b, x1, z1, x2, z2, width, roofed, pillar_h, pillar_space)


def _build_corner_plaza(b, x, z, size=5):
    """在转角处建造小广场 + 灯笼"""
    gy = _ground_y_at(x, z)
    half = size // 2

    # 铺地面
    b.fill(x - half, gy, z - half, x + half, gy, z + half, "minecraft:smooth_stone")
    # 四角铺石砖
    for dx, dz in [(-half, -half), (-half, half), (half, -half), (half, half)]:
        b.setblock(x + dx, gy, z + dz, "minecraft:stone_bricks")
        # 柱子
        for dy in range(1, 5):
            b.setblock(x + dx, gy + dy, z + dz, "minecraft:stripped_crimson_stem")

    # 中央灯笼（挂在链子上或直接放地面）
    b.setblock(x, gy + 1, z, "minecraft:lantern")


def build_corridors(b: MinecraftBuilder):
    """建造所有有顶廊道 + 石径
    - 主环廊 (MAIN_CORRIDOR): 南段到东北角
    - 西段主廊 (WEST_CORRIDOR): 翠轩到远香堂
    - 北岸石径 (HIGHLAND_PATH): 无顶，3格宽
    """
    print("=== Building Corridors ===")

    # --- 主环廊 ---
    print("  Building main corridor (east loop)...")
    _build_corridor_from_config(b, cfg.MAIN_CORRIDOR)

    # 主环廊转角广场（在关键转折点）
    corner_points = [
        (74, 65),   # L3 东南转角
        (92, 42),   # L6 曲廊亭
    ]
    for cx, cz in corner_points:
        if not _point_in_any_water(cx, cz, margin=0):
            _build_corner_plaza(b, cx, cz)

    # --- 西段主廊 ---
    print("  Building west corridor...")
    _build_corridor_from_config(b, cfg.WEST_CORRIDOR)

    # 西段转角广场
    west_corners = [
        (25, 48),   # L11
        (38, 60),   # L13 听雨轩旁
    ]
    for cx, cz in west_corners:
        if not _point_in_any_water(cx, cz, margin=0):
            _build_corner_plaza(b, cx, cz)

    # --- 北岸石径（无顶）---
    print("  Building highland path...")
    _build_highland_path(b)

    # --- 入口轴线（次路径，5格宽石径）---
    print("  Building entrance axis...")
    entrance_path = cfg.SECONDARY_PATHS[0]  # 入口轴线
    wps = entrance_path["waypoints"]
    for i in range(len(wps) - 1):
        x1, z1 = wps[i]
        x2, z2 = wps[i + 1]
        _corridor_segment(b, x1, z1, x2, z2,
                          width=entrance_path["width"],
                          roofed=False, pillar_h=4, pillar_space=99)

    print(f"  Corridors done. Commands: {b.cmd_count}")


def _build_highland_path(b: MinecraftBuilder):
    """北岸假山石径 — 无顶，3格宽，石砖铺面
    用 fill 按段建造，效率高于逐格。
    """
    path = cfg.HIGHLAND_PATH
    waypoints = path["waypoints"]
    width = path["width"]
    half_w = width // 2
    surface = path.get("surface", "minecraft:stone_bricks")

    for i in range(len(waypoints) - 1):
        x1, z1 = waypoints[i]
        x2, z2 = waypoints[i + 1]

        # 验证不在水面
        if _point_in_any_water(x1, z1, margin=0) or _point_in_any_water(x2, z2, margin=0):
            print(f"  WARNING: highland path waypoint in water, skipping.")
            continue

        # 简化：用 Bresenham 线 + 宽度扩展
        points_3d = bresenham_3d(x1, 0, z1, x2, 0, z2)
        centerline = []
        seen = set()
        for p in points_3d:
            key = (p[0], p[2])
            if key not in seen:
                seen.add(key)
                centerline.append(key)

        dx_total = abs(x2 - x1)
        dz_total = abs(z2 - z1)
        is_x_major = dx_total >= dz_total

        for cx, cz in centerline:
            gy = _ground_y_at(cx, cz)
            if _point_in_any_water(cx, cz, margin=0):
                continue
            if is_x_major:
                b.fill(cx, gy, cz - half_w, cx, gy, cz + half_w, surface)
            else:
                b.fill(cx - half_w, gy, cz, cx + half_w, gy, cz, surface)


# ═══════════════════════════════════════════
# 4. 桥梁
# ═══════════════════════════════════════════

def build_bridges(b: MinecraftBuilder):
    """从 config 读取桥梁定义并建造
    - 石拱桥 (stone_arch): 平板桥面 + 拱洞
    - 九曲桥 (zigzag): 折线平桥
    - 汀步 (stepping_stones): 单格石头
    """
    print("=== Building Bridges ===")

    for bridge in cfg.ALL_BRIDGES:
        btype = bridge.get("bridge_type", "")
        name = bridge["name"]

        if btype == "stone_arch":
            _build_arch_bridge(b, bridge)
        elif btype == "zigzag":
            _build_zigzag_bridge(b, bridge)
        elif name == "汀步石":
            _build_stepping_stones(b, bridge)
        else:
            print(f"  Unknown bridge type: {btype}, skipping {name}")

        print(f"  {name} done.")

    print(f"  Bridges done. Commands: {b.cmd_count}")


def _build_arch_bridge(b, bridge):
    """石拱桥 — 石砖桥面 + 石砖栏杆 + 拱洞(空气)
    简化版: 平板桥面（不做真正的拱形结构，减少命令数）
    """
    cx = bridge["cx"]
    z_start = bridge["z_start"]
    z_end = bridge["z_end"]
    width = bridge["width"]
    half_w = width // 2
    arches = bridge.get("arches", 1)

    surface_y = cfg.WATER_SURFACE_Y  # -61
    bridge_y = surface_y + 1         # -60, 桥面在水面上1格

    # 桥面
    b.fill(cx - half_w, bridge_y, z_start, cx + half_w, bridge_y, z_end,
           "minecraft:stone_bricks")

    # 两侧栏杆 (石墙)
    b.fill(cx - half_w, bridge_y + 1, z_start, cx - half_w, bridge_y + 1, z_end,
           "minecraft:stone_brick_wall")
    b.fill(cx + half_w, bridge_y + 1, z_start, cx + half_w, bridge_y + 1, z_end,
           "minecraft:stone_brick_wall")

    # 桥头柱子
    for z in [z_start, z_end]:
        for side_x in [cx - half_w, cx + half_w]:
            b.setblock(side_x, bridge_y + 1, z, "minecraft:stone_bricks")
            b.setblock(side_x, bridge_y + 2, z, "minecraft:stone_brick_slab[type=bottom]")

    # 拱洞（水面层开口，让水流通）
    span = z_end - z_start
    arch_spacing = span // (arches + 1)
    for a in range(arches):
        arch_z = z_start + arch_spacing * (a + 1)
        # 在桥面下方开一个 3 格宽的空气缺口
        inner_half = max(1, half_w - 1)
        b.fill(cx - inner_half, surface_y, arch_z - 1,
               cx + inner_half, surface_y, arch_z + 1, "minecraft:air")


def _build_zigzag_bridge(b, bridge):
    """九曲桥 — 沿 waypoints 折线铺设平桥"""
    waypoints = bridge["waypoints"]
    width = bridge["width"]
    half_w = width // 2

    surface_y = cfg.WATER_SURFACE_Y
    bridge_y = surface_y + 1

    for i in range(len(waypoints) - 1):
        x1, z1 = waypoints[i]
        x2, z2 = waypoints[i + 1]

        points_3d = bresenham_3d(x1, 0, z1, x2, 0, z2)
        dx = abs(x2 - x1)
        dz = abs(z2 - z1)
        is_x_major = dx >= dz

        for p in points_3d:
            px, pz = p[0], p[2]
            if is_x_major:
                b.fill(px, bridge_y, pz - half_w, px, bridge_y, pz + half_w,
                       "minecraft:spruce_planks")
            else:
                b.fill(px - half_w, bridge_y, pz, px + half_w, bridge_y, pz,
                       "minecraft:spruce_planks")

    # 九曲桥栏杆（两侧木栅栏，沿中心线简化处理）
    for i in range(len(waypoints) - 1):
        x1, z1 = waypoints[i]
        x2, z2 = waypoints[i + 1]
        points_3d = bresenham_3d(x1, 0, z1, x2, 0, z2)
        dx = abs(x2 - x1)
        dz = abs(z2 - z1)
        is_x_major = dx >= dz
        for p in points_3d:
            px, pz = p[0], p[2]
            if is_x_major:
                b.setblock(px, bridge_y + 1, pz - half_w, "minecraft:spruce_fence")
                b.setblock(px, bridge_y + 1, pz + half_w, "minecraft:spruce_fence")
            else:
                b.setblock(px - half_w, bridge_y + 1, pz, "minecraft:spruce_fence")
                b.setblock(px + half_w, bridge_y + 1, pz, "minecraft:spruce_fence")


def _build_stepping_stones(b, bridge):
    """汀步石 — 水面上单格石头"""
    surface_y = cfg.WATER_SURFACE_Y
    for x, z in bridge["stones"]:
        b.setblock(x, surface_y, z, "minecraft:smooth_stone")


# ═══════════════════════════════════════════
# 主入口
# ═══════════════════════════════════════════

if __name__ == "__main__":
    with MinecraftBuilder() as b:
        build_outer_wall(b)
        build_inner_walls(b)
        build_corridors(b)
        build_bridges(b)
        print(f"Done! {b.cmd_count} commands")
