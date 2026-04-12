"""主环廊 + 群组间连接路径

从 config_v4 读取 MAIN_CORRIDOR / WEST_CORRIDOR / HIGHLAND_PATH waypoints，
统一建造5格宽有顶廊道 + 群组间次路径。

结构:
  主环廊 (MAIN_CORRIDOR): 南段→东岸→东北角, 5格宽有顶
  西段主廊 (WEST_CORRIDOR): 翠轩→远香堂, 5格宽有顶
  北岸石径 (HIGHLAND_PATH): A群↔B群, 3格宽无顶
  西廊道: B群↔C群 (翠轩→听雨轩方向)
  荼蘼径: C群↔D群 (荼蘼花架→听雨轩)
"""

import sys
sys.path.insert(0, '/Users/lambertlin/minecraft-server/scripts')

from builder import MinecraftBuilder, bresenham_3d
from blocks import PALETTE
import config_v4 as cfg


# ── 材质 ──
PILLAR     = PALETTE["pillar"]       # stripped_crimson_stem
BEAM       = PALETTE["beam"]         # dark_oak_planks
RAIL       = PALETTE["rail"]         # crimson_fence
FLOOR      = PALETTE["floor"]        # smooth_stone
FLOOR_ALT  = PALETTE["floor_alt"]    # stone_bricks
ROOF_SLAB  = PALETTE["roof_slab"]    # stone_brick_slab
BASE_COL   = PALETTE["base_col"]     # polished_andesite
LANTERN    = PALETTE["lantern"]
PATH_BLOCK = PALETTE["path"]         # dirt_path
GRAVEL     = PALETTE["gravel"]


# ═══════════════════════════════════════════
# 地形 + 水面辅助
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


def _point_in_any_water(x, z, margin=1):
    """检查 (x,z) 是否在水面上"""
    from phase1_water import point_in_polygon
    for poly in [cfg.MAIN_LAKE["shoreline"], cfg.DEEP_POOL["shoreline"]]:
        if point_in_polygon(x, z, poly):
            return True
    for i, (cx, cz) in enumerate(cfg.CREEK["centerline"]):
        w = cfg.CREEK["widths"][i] / 2 + margin
        if abs(x - cx) <= w and abs(z - cz) <= w:
            return True
    p = cfg.CREEK_POOL
    dx = x - p["cx"]
    dz = z - p["cz"]
    rx = p["rx"] + margin
    rz = p["rz"] + margin
    if (dx * dx) / (rx * rx) + (dz * dz) / (rz * rz) <= 1.0:
        return True
    return False


# ═══════════════════════════════════════════
# 核心廊道建造函数
# ═══════════════════════════════════════════

def _corridor_segment(b, x1, z1, x2, z2, width, roofed, pillar_h, pillar_space):
    """在两个 waypoint 之间建造一段廊道。

    截面:
      地面: smooth_stone(走道) + stone_bricks(柱位)
      柱子: stripped_crimson_stem, 每 pillar_space 格, 高 pillar_h
      栏杆: crimson_fence, 柱间
      屋顶: stone_brick_slab (仅 roofed=True)
    """
    points_3d = bresenham_3d(x1, 0, z1, x2, 0, z2)
    centerline = []
    seen = set()
    for p in points_3d:
        key = (p[0], p[2])
        if key not in seen:
            seen.add(key)
            centerline.append(key)

    half_w = width // 2
    dx = abs(x2 - x1)
    dz = abs(z2 - z1)
    is_x_major = dx >= dz

    for idx, (cx, cz) in enumerate(centerline):
        gy = _ground_y_at(cx, cz)

        # 铺地面
        if is_x_major:
            b.fill(cx, gy, cz - half_w, cx, gy, cz + half_w, FLOOR)
        else:
            b.fill(cx - half_w, gy, cz, cx + half_w, gy, cz, FLOOR)

        is_pillar = (idx % pillar_space == 0)

        if is_pillar:
            if is_x_major:
                for side_z in [cz - half_w, cz + half_w]:
                    b.setblock(cx, gy, side_z, BASE_COL)
                    for dy in range(1, pillar_h + 1):
                        b.setblock(cx, gy + dy, side_z, PILLAR)
            else:
                for side_x in [cx - half_w, cx + half_w]:
                    b.setblock(side_x, gy, cz, BASE_COL)
                    for dy in range(1, pillar_h + 1):
                        b.setblock(side_x, gy + dy, cz, PILLAR)
        else:
            if roofed:
                if is_x_major:
                    for side_z in [cz - half_w, cz + half_w]:
                        b.setblock(cx, gy + 1, side_z, RAIL)
                else:
                    for side_x in [cx - half_w, cx + half_w]:
                        b.setblock(side_x, gy + 1, cz, RAIL)

        # 屋顶
        if roofed:
            roof_y = gy + pillar_h + 1
            if is_x_major:
                b.fill(cx, roof_y, cz - half_w - 1,
                       cx, roof_y, cz + half_w + 1,
                       f"{ROOF_SLAB}[type=bottom]")
            else:
                b.fill(cx - half_w - 1, roof_y, cz,
                       cx + half_w + 1, roof_y, cz,
                       f"{ROOF_SLAB}[type=bottom]")


def _build_corridor_from_config(b, corridor_cfg):
    """从 config 廊道定义建造整条廊道"""
    waypoints = corridor_cfg["waypoints"]
    width = corridor_cfg["width"]
    pillar_h = corridor_cfg.get("pillar_h", 4)
    pillar_space = corridor_cfg.get("pillar_space", 4)
    roofed = corridor_cfg.get("roofed", True)

    for i in range(len(waypoints) - 1):
        x1, z1 = waypoints[i]
        x2, z2 = waypoints[i + 1]

        skip = False
        for wx, wz in [(x1, z1), (x2, z2)]:
            if _point_in_any_water(wx, wz, margin=0):
                print(f"    WARNING: waypoint ({wx},{wz}) in water, skipping.")
                skip = True
                break
        if skip:
            continue

        _corridor_segment(b, x1, z1, x2, z2,
                          width, roofed, pillar_h, pillar_space)


def _build_corner_plaza(b, x, z, size=5):
    """转角小广场 + 灯笼"""
    gy = _ground_y_at(x, z)
    half = size // 2

    b.fill(x - half, gy, z - half, x + half, gy, z + half, FLOOR)
    for dx, dz in [(-half, -half), (-half, half), (half, -half), (half, half)]:
        b.setblock(x + dx, gy, z + dz, FLOOR_ALT)
        for dy in range(1, 5):
            b.setblock(x + dx, gy + dy, z + dz, PILLAR)

    b.setblock(x, gy + 1, z, LANTERN)


# ═══════════════════════════════════════════
# 无顶石径建造
# ═══════════════════════════════════════════

def _build_stone_path(b, waypoints, width, surface_block):
    """建造无顶石径"""
    half_w = width // 2

    for i in range(len(waypoints) - 1):
        x1, z1 = waypoints[i]
        x2, z2 = waypoints[i + 1]

        if _point_in_any_water(x1, z1, margin=0) or \
           _point_in_any_water(x2, z2, margin=0):
            print(f"    WARNING: path waypoint in water, skipping.")
            continue

        points_3d = bresenham_3d(x1, 0, z1, x2, 0, z2)
        centerline = []
        seen = set()
        for p in points_3d:
            key = (p[0], p[2])
            if key not in seen:
                seen.add(key)
                centerline.append(key)

        dx = abs(x2 - x1)
        dz = abs(z2 - z1)
        is_x_major = dx >= dz

        for cx, cz in centerline:
            gy = _ground_y_at(cx, cz)
            if _point_in_any_water(cx, cz, margin=0):
                continue
            if is_x_major:
                b.fill(cx, gy, cz - half_w, cx, gy, cz + half_w,
                       surface_block)
            else:
                b.fill(cx - half_w, gy, cz, cx + half_w, gy, cz,
                       surface_block)


# ═══════════════════════════════════════════
# 主入口
# ═══════════════════════════════════════════

def build_main_corridors(b: MinecraftBuilder):
    """主环廊 + 群组间连接路径"""
    print("=" * 50)
    print("=== 主环廊 + 群组间连接 ===")
    print("=" * 50)

    cmd_start = b.cmd_count

    # ── 1. 主环廊 (东段) ──
    print("  [1/6] 主环廊 (东段)...")
    _build_corridor_from_config(b, cfg.MAIN_CORRIDOR)

    # 主环廊关键转角广场
    main_corners = [
        (74, 63),   # L3 东南转角
        (96, 42),   # L6 曲廊亭 (与E群曲廊亭重合，增强节点感)
        (90, 34),   # L7 东岸转角
    ]
    for cx, cz in main_corners:
        if not _point_in_any_water(cx, cz, margin=0):
            _build_corner_plaza(b, cx, cz)

    # ── 2. 西段主廊 ──
    print("  [2/6] 西段主廊...")
    _build_corridor_from_config(b, cfg.WEST_CORRIDOR)

    west_corners = [
        (25, 48),   # L11
        (34, 56),   # L13 听雨轩旁
    ]
    for cx, cz in west_corners:
        if not _point_in_any_water(cx, cz, margin=0):
            _build_corner_plaza(b, cx, cz)

    # ── 3. 北岸石径 (A群↔B群) ──
    print("  [3/6] 北岸石径 (A群<->B群)...")
    hp = cfg.HIGHLAND_PATH
    _build_stone_path(b, hp["waypoints"], hp["width"],
                      f"minecraft:{hp.get('surface', 'stone_bricks')}")

    # ── 4. 入口轴线 ──
    print("  [4/6] 入口轴线...")
    entrance_path = cfg.SECONDARY_PATHS[0]
    wps = entrance_path["waypoints"]
    for i in range(len(wps) - 1):
        x1, z1 = wps[i]
        x2, z2 = wps[i + 1]
        _corridor_segment(b, x1, z1, x2, z2,
                          width=entrance_path["width"],
                          roofed=False, pillar_h=4, pillar_space=99)

    # ── 5. 西廊道 (B群↔C群, 翠轩→听雨轩区域) ──
    # 从翠轩东侧 (22,28)→(22,38)→(25,48) 已在西段主廊覆盖
    # 补充: 从 B群边缘向 C群方向的短连接径
    print("  [5/6] 西廊道补充 (B群<->C群)...")
    west_link_wps = [
        (16, 28),   # 翠轩中心附近
        (22, 28),   # 翠轩东侧 (主廊起点)
    ]
    _build_stone_path(b, west_link_wps, 3, "minecraft:stone_bricks")

    # ── 6. 荼蘼径 (C群↔D群) ──
    print("  [6/6] 荼蘼径 (C群<->D群)...")
    tumi_path = None
    for sp in cfg.SECONDARY_PATHS:
        if sp["name"] == "荼蘼径":
            tumi_path = sp
            break

    if tumi_path:
        surface = f"minecraft:{tumi_path.get('surface', 'dirt_path')}"
        _build_stone_path(b, tumi_path["waypoints"],
                          tumi_path["width"], surface)
    else:
        # fallback: 手动定义荼蘼径
        tumi_wps = [(50, 56), (46, 56), (38, 56), (34, 54)]
        _build_stone_path(b, tumi_wps, 2, f"minecraft:dirt_path")

    # ── 其余次路径 (梅花小径、闺塾径) ──
    for sp in cfg.SECONDARY_PATHS:
        if sp["name"] in ("入口轴线", "荼蘼径"):
            continue  # 已处理
        print(f"    次路径: {sp['name']}...")
        surface = f"minecraft:{sp.get('surface', 'dirt_path')}"
        _build_stone_path(b, sp["waypoints"], sp["width"], surface)

    print(f"  主环廊完成! ({b.cmd_count - cmd_start} commands)")


# ── 独立测试入口 ──

if __name__ == "__main__":
    with MinecraftBuilder() as b:
        build_main_corridors(b)
        print(f"Done! Total commands: {b.cmd_count}")
