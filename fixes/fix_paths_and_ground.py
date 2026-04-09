"""次路网 + 扫底填充 — 消灭 60%+ 裸草地

目标: 裸草率从 60%+ 降至 <10%
方法:
  1. 5 条蜿蜒小径 (dirt_path + stone_brick_slab 踏步石 + coarse_dirt 路边)
  2. 分区扫底填充 (建筑过渡/湿生带/路边过渡/自然散植)
原则:
  - fill 做大面积操作，setblock 只用于随机点缀
  - 总命令 < 3000
"""

import sys
sys.path.insert(0, '/Users/lambertlin/minecraft-server/scripts')

from builder import MinecraftBuilder
from blocks import PALETTE, GROUND_Y, BUILD_Y
from config import (
    GARDEN, PAVILION, HALL, PEONY_RAIL, SWING,
    GATE_AREA, POND, CORRIDOR, BRIDGE, BOAT,
    TAIHU_ROCKS, PLUM_TREE, WALL, WILLOWS, WELLS,
    FLOWER_CLUSTERS,
)
import random
import math


# ══════════════════════════════════════════════════════════════
#  常量
# ══════════════════════════════════════════════════════════════

DIRT_PATH = PALETTE["path"]                  # minecraft:dirt_path
STONE_BRICK_SLAB = PALETTE["base_slab"]      # minecraft:stone_brick_slab
COARSE_DIRT = "minecraft:coarse_dirt"
MOSS_BLOCK = PALETTE["moss"]                 # minecraft:moss_block
MOSS_CARPET = PALETTE["moss_carpet"]         # minecraft:moss_carpet
FERN = PALETTE["fern"]                       # minecraft:fern
TALL_GRASS = PALETTE["tall_grass"]           # minecraft:tall_grass
AZALEA = PALETTE["azalea"]                   # minecraft:flowering_azalea
GRASS_BLOCK = PALETTE["grass"]               # minecraft:grass_block

FLOWERS = [
    "minecraft:red_tulip", "minecraft:pink_tulip",
    "minecraft:cornflower", "minecraft:azure_bluet",
    "minecraft:oxeye_daisy", "minecraft:allium",
    "minecraft:dandelion", "minecraft:poppy",
]

FLOWERS_DOUBLE = [
    "minecraft:peony", "minecraft:rose_bush", "minecraft:lilac",
]


# ══════════════════════════════════════════════════════════════
#  占用判定 — 排除建筑、池塘、已有路面、围墙
# ══════════════════════════════════════════════════════════════

# 曲廊路段 (中心线 +-2 保护)
_CORRIDOR_WPS = CORRIDOR["waypoints"]
_CORRIDOR_SEGMENTS = []
for i in range(len(_CORRIDOR_WPS) - 1):
    ax, az = _CORRIDOR_WPS[i]
    bx, bz = _CORRIDOR_WPS[i + 1]
    _CORRIDOR_SEGMENTS.append((ax, az, bx, bz))

# 矩形排除区: (x1, z1, x2, z2)
_RECT_ZONES = [
    # 翠轩 (cx=16, cz=35, 17x11) + 安全2格
    (HALL["cx"] - HALL["width_x"] // 2 - 2,
     HALL["cz"] - HALL["width_z"] // 2 - 2,
     HALL["cx"] + HALL["width_x"] // 2 + 2,
     HALL["cz"] + HALL["width_z"] // 2 + 2),
    # 芍药阑 (cx=78, cz=29, 11x9) + 安全2格
    (PEONY_RAIL["cx"] - PEONY_RAIL["hx"] - 2,
     PEONY_RAIL["cz"] - PEONY_RAIL["hz"] - 2,
     PEONY_RAIL["cx"] + PEONY_RAIL["hx"] + 2,
     PEONY_RAIL["cz"] + PEONY_RAIL["hz"] + 2),
    # 入口区庭院 + 安全
    (GATE_AREA["cx"] - GATE_AREA["court_width"] // 2 - 2,
     GATE_AREA["cz"] - GATE_AREA["court_depth"] // 2 - 2,
     GATE_AREA["cx"] + GATE_AREA["court_width"] // 2 + 2,
     GATE_AREA["cz"] + GATE_AREA["court_depth"] // 2 + 2),
    # 廊桥 (cx=45, z35~55, w=5) + 安全
    (BRIDGE["cx"] - BRIDGE["width"] // 2 - 2,
     BRIDGE["z_start"] - 2,
     BRIDGE["cx"] + BRIDGE["width"] // 2 + 2,
     BRIDGE["z_end"] + 2),
    # 画船
    (BOAT["cx"] - 5, BOAT["cz"] - 4, BOAT["cx"] + 5, BOAT["cz"] + 4),
    # 太湖石
    (TAIHU_ROCKS["cx"] - 6, TAIHU_ROCKS["cz"] - 6,
     TAIHU_ROCKS["cx"] + 6, TAIHU_ROCKS["cz"] + 6),
    # 秋千
    (SWING["cx"] - 4, SWING["cz"] - 4, SWING["cx"] + 4, SWING["cz"] + 4),
    # 大梅树
    (PLUM_TREE["x"] - 7, PLUM_TREE["z"] - 7,
     PLUM_TREE["x"] + 7, PLUM_TREE["z"] + 7),
]

# 断井 (各±3)
for wx, wz in WELLS:
    _RECT_ZONES.append((wx - 3, wz - 3, wx + 3, wz + 3))


def _in_pond(x, z):
    """椭圆池塘判定 (稍微外扩 1 格)"""
    cx, cz = POND["cx"], POND["cz"]
    rx, rz = POND["rx"], POND["rz"]
    return ((x - cx) / (rx + 1)) ** 2 + ((z - cz) / (rz + 1)) ** 2 <= 1.0


def _in_pond_exact(x, z):
    """精确池塘边界"""
    cx, cz = POND["cx"], POND["cz"]
    rx, rz = POND["rx"], POND["rz"]
    return ((x - cx) / rx) ** 2 + ((z - cz) / rz) ** 2 <= 1.0


def _in_pavilion(x, z):
    """牡丹亭圆形台基 (r_base + 安全2格)"""
    cx, cz = PAVILION["cx"], PAVILION["cz"]
    r = PAVILION["r_base"] + 2
    return (x - cx) ** 2 + (z - cz) ** 2 <= r * r


def _on_corridor(x, z):
    """是否在曲廊上 (中心线 +-3 格)"""
    for ax, az, bx, bz in _CORRIDOR_SEGMENTS:
        if ax == bx:  # Z 方向段
            z_lo, z_hi = min(az, bz), max(az, bz)
            if z_lo - 1 <= z <= z_hi + 1 and abs(x - ax) <= 3:
                return True
        else:  # X 方向段
            x_lo, x_hi = min(ax, bx), max(ax, bx)
            if x_lo - 1 <= x <= x_hi + 1 and abs(z - az) <= 3:
                return True
    return False


def _in_garden(x, z):
    """园内 (留围墙 2 格)"""
    return (GARDEN["x_min"] + 2 <= x <= GARDEN["x_max"] - 2 and
            GARDEN["z_min"] + 2 <= z <= GARDEN["z_max"] - 2)


def _is_occupied(x, z):
    """判断 (x,z) 是否已被建筑/结构/池塘/廊道占据"""
    if not _in_garden(x, z):
        return True
    if _in_pond(x, z):
        return True
    if _in_pavilion(x, z):
        return True
    if _on_corridor(x, z):
        return True
    for x1, z1, x2, z2 in _RECT_ZONES:
        if x1 <= x <= x2 and z1 <= z <= z2:
            return True
    return False


# ══════════════════════════════════════════════════════════════
#  距离计算
# ══════════════════════════════════════════════════════════════

def _dist_to_pond(x, z):
    """到池塘边缘的近似距离"""
    cx, cz = POND["cx"], POND["cz"]
    rx, rz = POND["rx"], POND["rz"]
    # 归一化距离
    norm = math.sqrt(((x - cx) / rx) ** 2 + ((z - cz) / rz) ** 2)
    if norm < 0.01:
        return 0
    # 池塘边缘上最近点的近似距离
    ex = cx + rx * (x - cx) / (rx * norm)
    ez = cz + rz * (z - cz) / (rz * norm)
    return math.sqrt((x - ex) ** 2 + (z - ez) ** 2)


def _dist_to_buildings(x, z):
    """到最近建筑边缘的距离"""
    min_d = 999
    # 翠轩
    hx1 = HALL["cx"] - HALL["width_x"] // 2
    hx2 = HALL["cx"] + HALL["width_x"] // 2
    hz1 = HALL["cz"] - HALL["width_z"] // 2
    hz2 = HALL["cz"] + HALL["width_z"] // 2
    dx = max(hx1 - x, 0, x - hx2)
    dz = max(hz1 - z, 0, z - hz2)
    min_d = min(min_d, math.sqrt(dx * dx + dz * dz))

    # 芍药阑
    px1 = PEONY_RAIL["cx"] - PEONY_RAIL["hx"]
    px2 = PEONY_RAIL["cx"] + PEONY_RAIL["hx"]
    pz1 = PEONY_RAIL["cz"] - PEONY_RAIL["hz"]
    pz2 = PEONY_RAIL["cz"] + PEONY_RAIL["hz"]
    dx = max(px1 - x, 0, x - px2)
    dz = max(pz1 - z, 0, z - pz2)
    min_d = min(min_d, math.sqrt(dx * dx + dz * dz))

    # 牡丹亭 (圆形)
    d_pav = math.sqrt((x - PAVILION["cx"]) ** 2 + (z - PAVILION["cz"]) ** 2) - PAVILION["r_base"]
    min_d = min(min_d, max(0, d_pav))

    # 入口区
    gx1 = GATE_AREA["cx"] - GATE_AREA["court_width"] // 2
    gx2 = GATE_AREA["cx"] + GATE_AREA["court_width"] // 2
    gz1 = GATE_AREA["cz"] - GATE_AREA["court_depth"] // 2
    gz2 = GATE_AREA["cz"] + GATE_AREA["court_depth"] // 2
    dx = max(gx1 - x, 0, x - gx2)
    dz = max(gz1 - z, 0, z - gz2)
    min_d = min(min_d, math.sqrt(dx * dx + dz * dz))

    return min_d


# ══════════════════════════════════════════════════════════════
#  1. 蜿蜒小径生成
# ══════════════════════════════════════════════════════════════

def _catmull_rom(p0, p1, p2, p3, t, alpha=0.5):
    """Catmull-Rom 样条插值，生成平滑蜿蜒曲线"""
    def tj(ti, pi, pj):
        dx = pj[0] - pi[0]
        dz = pj[1] - pi[1]
        return ti + (dx * dx + dz * dz) ** (alpha / 2)

    t0 = 0
    t1 = tj(t0, p0, p1)
    t2 = tj(t1, p1, p2)
    t3 = tj(t2, p2, p3)

    # 将 t 映射到 [t1, t2]
    tt = t1 + t * (t2 - t1)

    # 防止除零
    if abs(t1 - t0) < 0.001 or abs(t2 - t1) < 0.001 or abs(t3 - t2) < 0.001:
        # fallback 线性插值
        return (p1[0] + t * (p2[0] - p1[0]),
                p1[1] + t * (p2[1] - p1[1]))

    a1 = [(t1 - tt) / (t1 - t0) * p0[i] + (tt - t0) / (t1 - t0) * p1[i] for i in range(2)]
    a2 = [(t2 - tt) / (t2 - t1) * p1[i] + (tt - t1) / (t2 - t1) * p2[i] for i in range(2)]
    a3 = [(t3 - tt) / (t3 - t2) * p2[i] + (tt - t2) / (t3 - t2) * p3[i] for i in range(2)]

    if abs(t2 - t0) < 0.001 or abs(t3 - t1) < 0.001:
        return (a2[0], a2[1])

    b1 = [(t2 - tt) / (t2 - t0) * a1[i] + (tt - t0) / (t2 - t0) * a2[i] for i in range(2)]
    b2 = [(t3 - tt) / (t3 - t1) * a2[i] + (tt - t1) / (t3 - t1) * a3[i] for i in range(2)]

    if abs(t2 - t1) < 0.001:
        return (b1[0], b1[1])

    c = [(t2 - tt) / (t2 - t1) * b1[i] + (tt - t1) / (t2 - t1) * b2[i] for i in range(2)]
    return (c[0], c[1])


def _generate_winding_path(waypoints, width=2):
    """根据经过点生成蜿蜒路径的坐标集合。
    返回三个集合:
      - path_center: 路面中心 (dirt_path)
      - step_stones: 踏步石位置 (stone_brick_slab)
      - path_edge: 路边过渡 (coarse_dirt)
    """
    path_center = set()
    step_stones = set()
    path_edge = set()

    # 扩展首尾控制点使 Catmull-Rom 能覆盖整条路
    pts = list(waypoints)
    # 镜像延伸首尾
    p_start = (2 * pts[0][0] - pts[1][0], 2 * pts[0][1] - pts[1][1])
    p_end = (2 * pts[-1][0] - pts[-2][0], 2 * pts[-1][1] - pts[-2][1])
    pts = [p_start] + pts + [p_end]

    # 沿样条采样
    all_points = []
    for seg in range(1, len(pts) - 2):
        p0, p1, p2, p3 = pts[seg - 1], pts[seg], pts[seg + 1], pts[seg + 2]
        # 采样密度：根据段长度
        seg_len = math.sqrt((p2[0] - p1[0]) ** 2 + (p2[1] - p1[1]) ** 2)
        num_samples = max(int(seg_len * 1.5), 10)
        for i in range(num_samples):
            t = i / num_samples
            cx, cz = _catmull_rom(p0, p1, p2, p3, t)
            all_points.append((round(cx), round(cz)))
    # 加上终点
    all_points.append((round(pts[-2][0]), round(pts[-2][1])))

    # 去重保持顺序
    seen = set()
    unique_points = []
    for p in all_points:
        if p not in seen:
            seen.add(p)
            unique_points.append(p)

    # 生成宽度和踏步石
    step_counter = 0
    for idx, (cx, cz) in enumerate(unique_points):
        # 路面中心 (2格宽: 中心 + 根据前进方向偏移)
        if idx < len(unique_points) - 1:
            nx, nz = unique_points[idx + 1]
            dx, dz = nx - cx, nz - cz
        else:
            dx, dz = 0, 0

        # 2格宽: 在垂直于行进方向的两侧各展开
        if abs(dx) >= abs(dz):
            # 主要沿X走，宽度在Z方向
            offsets = [(cx, cz), (cx, cz + 1)]
        else:
            # 主要沿Z走，宽度在X方向
            offsets = [(cx, cz), (cx + 1, cz)]

        for px, pz in offsets:
            if _is_occupied(px, pz):
                continue
            # 每 3-4 格放一块踏步石
            if step_counter % 4 == 0 and (px, pz) == offsets[0]:
                step_stones.add((px, pz))
            else:
                path_center.add((px, pz))

        # 路边过渡 (宽度外扩 1 格)
        if abs(dx) >= abs(dz):
            edge_offsets = [(cx, cz - 1), (cx, cz + 2)]
        else:
            edge_offsets = [(cx - 1, cz), (cx + 2, cz)]

        for ex, ez in edge_offsets:
            if not _is_occupied(ex, ez) and (ex, ez) not in path_center:
                path_edge.add((ex, ez))

        step_counter += 1

    # 从 path_edge 移除已在 path_center 或 step_stones 中的
    path_edge -= path_center
    path_edge -= step_stones

    return path_center, step_stones, path_edge


# 五条小径的经过点
PATH_DEFINITIONS = [
    # 1. 曲廊→秋千: (22,15) 经 (40,22) 到 (62,25)
    ("曲廊→秋千", [(22, 15), (30, 17), (40, 22), (52, 24), (62, 25)]),
    # 2. 廊桥→芍药阑: (48,33) 经 (60,28) 到 (73,29)
    ("廊桥→芍药阑", [(50, 30), (54, 28), (60, 28), (67, 28), (73, 29)]),  # 起点从(48,33)改避池塘
    # 3. 大梅树→翠轩: (12,14) 经 (10,22) 到 (8,30)
    ("大梅树→翠轩", [(12, 14), (11, 18), (10, 22), (9, 26), (8, 30)]),
    # 4. 牡丹亭→月洞门: 起点从(86,15)改(90,15)避牡丹亭保护区
    ("牡丹亭→月洞门", [(90, 15), (95, 19), (100, 25), (110, 35), (115, 40), (118, 45)]),
    # 5. 池塘南岸漫步道: Z从58改60多留余量避池塘
    ("池塘南岸漫步道", [(30, 60), (38, 61), (45, 62), (52, 61), (60, 60), (70, 60)]),
]


def _build_paths(b):
    """建造 5 条蜿蜒小径"""
    print("  [1/2] 建造次路网...")
    total_cmds = 0

    all_path_points = set()   # 记录所有路面点，供扫底排除
    all_edge_points = set()   # 记录所有路边点

    for name, waypoints in PATH_DEFINITIONS:
        center, stones, edges = _generate_winding_path(waypoints)

        # ── 用 fill 铺路面 ──
        # 策略: 将连续的路面点按行/列分组，用 fill 批量铺设
        # 先整体用 fill 按 bounding box 铺 dirt_path (replace grass_block)
        if center or stones:
            all_pts = center | stones
            xs = [p[0] for p in all_pts]
            zs = [p[1] for p in all_pts]
            x_min, x_max = min(xs), max(xs)
            z_min, z_max = min(zs), max(zs)

            # 用 replace 把路径 bbox 里的草地换成 dirt_path
            # 但这会改太多，所以我们按 Z 行扫描用小段 fill
            for z in range(z_min, z_max + 1):
                row_xs = sorted([p[0] for p in all_pts if p[1] == z])
                if not row_xs:
                    continue
                # 找连续段
                segments = []
                seg_start = row_xs[0]
                seg_end = row_xs[0]
                for rx in row_xs[1:]:
                    if rx <= seg_end + 1:
                        seg_end = rx
                    else:
                        segments.append((seg_start, seg_end))
                        seg_start = rx
                        seg_end = rx
                segments.append((seg_start, seg_end))

                for sx, ex in segments:
                    b.fill(sx, GROUND_Y, z, ex, GROUND_Y, z, DIRT_PATH)
                    total_cmds += 1

        # 踏步石用 setblock (稀疏)
        for sx, sz in stones:
            b.setblock(sx, GROUND_Y, sz, f"{STONE_BRICK_SLAB}[type=bottom]")
            total_cmds += 1

        # 路边过渡: 按行 fill
        if edges:
            for z in range(min(e[1] for e in edges), max(e[1] for e in edges) + 1):
                row_xs = sorted([p[0] for p in edges if p[1] == z])
                if not row_xs:
                    continue
                segments = []
                seg_start = row_xs[0]
                seg_end = row_xs[0]
                for rx in row_xs[1:]:
                    if rx <= seg_end + 1:
                        seg_end = rx
                    else:
                        segments.append((seg_start, seg_end))
                        seg_start = rx
                        seg_end = rx
                segments.append((seg_start, seg_end))
                for sx, ex in segments:
                    b.fill(sx, GROUND_Y, z, ex, GROUND_Y, z, COARSE_DIRT)
                    total_cmds += 1

        all_path_points |= center | stones
        all_edge_points |= edges

        print(f"    {name}: 路面{len(center)}+踏步{len(stones)}, 路边{len(edges)}")

    print(f"    次路网总计: ~{total_cmds} commands")
    return all_path_points, all_edge_points


# ══════════════════════════════════════════════════════════════
#  2. 扫底填充
# ══════════════════════════════════════════════════════════════

def _build_ground_fill(b, path_points, edge_points):
    """对园内所有剩余裸草地做分区填充。

    策略:
      - 大面积分区用 fill replace 批量操作 (一条命令换一整片)
      - 植物点缀严格控 setblock 总量 (上限 ~1500)
      - 开放地面分 10x10 网格块，每块一条 fill 做苔藓/粗泥底
    """
    print("  [2/2] 扫底填充...")
    total_cmds = 0

    x_lo = GARDEN["x_min"] + 2
    x_hi = GARDEN["x_max"] - 2
    z_lo = GARDEN["z_min"] + 2
    z_hi = GARDEN["z_max"] - 2

    # ── 预扫描: 分类所有空地点 ──
    building_trans = []     # 距建筑 < 3
    pond_wet = []           # 距池塘 < 4
    open_ground = []        # 其他空地

    for x in range(x_lo, x_hi + 1):
        for z in range(z_lo, z_hi + 1):
            if _is_occupied(x, z):
                continue
            if (x, z) in path_points or (x, z) in edge_points:
                continue

            d_bld = _dist_to_buildings(x, z)
            d_pond = _dist_to_pond(x, z)

            if d_bld < 3:
                building_trans.append((x, z))
            elif d_pond < 4 and not _in_pond_exact(x, z):
                pond_wet.append((x, z))
            else:
                open_ground.append((x, z))

    # ══════════════════════════════════════════════
    #  2a. 建筑过渡带: fill coarse_dirt + 稀疏 fern
    # ══════════════════════════════════════════════
    print(f"    建筑过渡带: {len(building_trans)} 点")
    total_cmds += _fill_by_rows(b, building_trans, COARSE_DIRT, GROUND_Y)
    # 15% 种 fern (控制数量)
    fern_spots = [p for p in building_trans if random.random() < 0.15]
    for fx, fz in fern_spots:
        b.setblock(fx, BUILD_Y, fz, FERN)
        total_cmds += 1

    # ══════════════════════════════════════════════
    #  2b. 池塘湿生带: fill moss_block + 稀疏 fern
    # ══════════════════════════════════════════════
    print(f"    池塘湿生带: {len(pond_wet)} 点")
    total_cmds += _fill_by_rows(b, pond_wet, MOSS_BLOCK, GROUND_Y)
    # 20% 种 fern
    fern_wet = [p for p in pond_wet if random.random() < 0.20]
    for px, pz in fern_wet:
        b.setblock(px, BUILD_Y, pz, FERN)
        total_cmds += 1

    # ══════════════════════════════════════════════
    #  2c. 开放地面: 分网格块 fill + 稀疏点缀
    # ══════════════════════════════════════════════
    print(f"    开放地面: {len(open_ground)} 点")
    open_set = set(open_ground)

    # --- 地面层: 用 10x10 网格块做 fill replace ---
    # 把部分草地块换成 moss_block 或 coarse_dirt (大面积操作)
    CHUNK = 10
    for gx in range(x_lo, x_hi + 1, CHUNK):
        for gz in range(z_lo, z_hi + 1, CHUNK):
            cx2 = min(gx + CHUNK - 1, x_hi)
            cz2 = min(gz + CHUNK - 1, z_hi)
            # 统计这个块里有多少空地
            chunk_open = 0
            for xx in range(gx, cx2 + 1):
                for zz in range(gz, cz2 + 1):
                    if (xx, zz) in open_set:
                        chunk_open += 1
            chunk_area = (cx2 - gx + 1) * (cz2 - gz + 1)
            if chunk_open < chunk_area * 0.3:
                continue  # 空地太少，跳过

            # 30% 的网格块铺苔藓底 (replace grass_block → moss_block)
            # 20% 的网格块铺粗泥底
            r = random.random()
            if r < 0.25:
                b.replace(gx, GROUND_Y, gz, cx2, GROUND_Y, cz2,
                          MOSS_BLOCK, GRASS_BLOCK)
                total_cmds += 1
            elif r < 0.40:
                b.replace(gx, GROUND_Y, gz, cx2, GROUND_Y, cz2,
                          COARSE_DIRT, GRASS_BLOCK)
                total_cmds += 1

    # --- 植物点缀: 严格控制 setblock 数量 ---
    # 目标: ~1200 个 setblock (每 5 个开放点种 1 个)
    plant_budget = min(1200, len(open_ground) // 5)
    # 随机抽样
    plant_candidates = random.sample(open_ground,
                                     min(plant_budget, len(open_ground)))

    for x, z in plant_candidates:
        r = random.random()
        if r < 0.35:
            # short_grass (单格，不是 tall_grass 避免双倍命令)
            b.setblock(x, BUILD_Y, z, "minecraft:short_grass")
            total_cmds += 1
        elif r < 0.55:
            # fern
            b.setblock(x, BUILD_Y, z, FERN)
            total_cmds += 1
        elif r < 0.70:
            # 随机花
            flower = random.choice(FLOWERS)
            b.setblock(x, BUILD_Y, z, flower)
            total_cmds += 1
        elif r < 0.80:
            # tall_grass (双格高，仅 10% 概率)
            b.setblock(x, BUILD_Y, z, f"{TALL_GRASS}[half=lower]")
            b.setblock(x, BUILD_Y + 1, z, f"{TALL_GRASS}[half=upper]")
            total_cmds += 2
        elif r < 0.90:
            # azalea 灌木 (地面改粗泥)
            b.setblock(x, GROUND_Y, z, COARSE_DIRT)
            b.setblock(x, BUILD_Y, z, AZALEA)
            total_cmds += 2
        else:
            # moss_carpet 覆盖
            b.setblock(x, BUILD_Y, z, MOSS_CARPET)
            total_cmds += 1

    print(f"    植物点缀: {len(plant_candidates)} spots")
    print(f"    扫底总计: ~{total_cmds} commands")
    return total_cmds


def _fill_by_rows(b, points, block, y):
    """将散点按 Z 行分组，每行内找连续 X 段用 fill 命令。
    返回使用的命令数。
    """
    if not points:
        return 0

    cmd_count = 0
    # 按 Z 分组
    by_z = {}
    for x, z in points:
        by_z.setdefault(z, []).append(x)

    for z in sorted(by_z.keys()):
        xs = sorted(by_z[z])
        # 找连续段 (允许 1 格间隔合并，减少命令)
        segments = []
        seg_start = xs[0]
        seg_end = xs[0]
        for x in xs[1:]:
            if x <= seg_end + 2:  # 允许 1 格间隔
                seg_end = x
            else:
                segments.append((seg_start, seg_end))
                seg_start = x
                seg_end = x
        segments.append((seg_start, seg_end))

        for sx, ex in segments:
            b.fill(sx, y, z, ex, y, z, block)
            cmd_count += 1

    return cmd_count


# ══════════════════════════════════════════════════════════════
#  主入口
# ══════════════════════════════════════════════════════════════

def fix_paths_and_ground(b):
    """次路网 + 扫底填充 总入口"""
    print("=== 次路网 + 扫底填充 ===")
    random.seed(2026_0408)

    # 1. 建造 5 条蜿蜒小径
    path_pts, edge_pts = _build_paths(b)

    # 2. 扫底填充
    _build_ground_fill(b, path_pts, edge_pts)

    b.register_bbox("paths_and_ground",
                    GARDEN["x_min"], GROUND_Y, GARDEN["z_min"],
                    GARDEN["x_max"], BUILD_Y + 2, GARDEN["z_max"])

    print("=== 次路网 + 扫底填充完成 ===")


if __name__ == "__main__":
    with MinecraftBuilder() as b:
        fix_paths_and_ground(b)
        print(f"Done! {b.cmd_count} commands")
