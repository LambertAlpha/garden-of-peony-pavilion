"""全园衔接修复脚本 — 逐个衔接点精确铺路/接台阶

按主动线顺序:
  1. 入口影壁通道 → 曲廊起点A
  2. 曲廊D → 翠轩东入口
  3. 曲廊E→H 爬山廊改造（Y=-60 渐升至 Y=-57）
  4. 曲廊终点H → 牡丹亭西踏步
  5. 牡丹亭南踏步 → 芍药阑北入口
  6. 廊桥两端 → 路网
  7. 画船 → 翠轩跳板
  8. 南面水乡衔接
  9. 全园地面填充

坐标全部从 config 计算，不硬编码。
"""

import sys; sys.path.insert(0, '/Users/lambertlin/minecraft-server/scripts')
from builder import MinecraftBuilder
from blocks import PALETTE, GROUND_Y, BUILD_Y
from config import (
    GARDEN, PAVILION, PEONY_RAIL, HALL, GATE_AREA,
    CORRIDOR, BRIDGE, BOAT, POND, WALL,
    TAIHU_ROCKS, SWING, FLOWER_CLUSTERS, WILLOWS,
)
import random
import math

# ── 常用方块 ──
STONE_BRICK       = PALETTE["base"]           # stone_bricks
STONE_BRICK_STAIR = PALETTE["base_step"]      # stone_brick_stairs
STONE_BRICK_SLAB  = PALETTE["base_slab"]      # stone_brick_slab
SMOOTH_STONE      = PALETTE["floor"]          # smooth_stone
FLOOR_ALT         = PALETTE["floor_alt"]      # stone_bricks
PATH_BLOCK        = PALETTE["path"]           # dirt_path
GRAVEL            = PALETTE["gravel"]         # gravel
COBBLE            = PALETTE["cobblestone"]
MOSSY_COBBLE      = PALETTE["mossy_cobblestone"]
SPRUCE_PLANKS     = PALETTE["floor_wood"]     # spruce_planks
OAK_PLANKS        = "minecraft:oak_planks"
OAK_SLAB          = "minecraft:oak_slab"
GRASS             = PALETTE["grass"]
DIRT              = PALETTE["dirt"]
AIR               = PALETTE["air"]
MOSS_CARPET       = PALETTE["moss_carpet"]
LANTERN           = PALETTE["lantern"]
PILLAR            = PALETTE["pillar"]         # stripped_crimson_stem
BEAM              = PALETTE["beam"]           # dark_oak_planks
RAIL              = PALETTE["rail"]           # crimson_fence
ROOF_SLAB         = PALETTE["roof_slab"]      # stone_brick_slab
BASE_COL          = PALETTE["base_col"]       # polished_andesite
TRAPDOOR          = PALETTE["trapdoor"]       # jungle_trapdoor


# ══════════════════════════════════════════════════════════════
#  1. 入口影壁通道 → 曲廊起点 A(55, 68)
# ══════════════════════════════════════════════════════════════

def fix_gate_to_corridor(b):
    """从影壁两侧通道铺石砖路到曲廊 A 点。

    影壁在 Z=70（庭院北端），两侧各留 3 格通道。
    曲廊 A 点 = (55, 68)，Y=BUILD_Y=-60。
    需要铺: 影壁通道出口(~Z=69) → A点(Z=68)，宽 3 格。
    """
    print("  [1/9] 入口 → 曲廊A...")

    cfg = GATE_AREA
    cx = cfg["cx"]              # 55
    cz = cfg["cz"]              # 80
    cw = cfg["court_width"]     # 16
    cd = cfg["court_depth"]     # 10
    gw = cfg["gate_width"]      # 5
    y0 = cfg["ground_y"]        # -60

    # 庭院范围
    cx1 = cx - cw // 2          # 47
    cx2 = cx + cw // 2          # 63
    cz_n = cz - cd              # 70 (影壁线Z)

    # 影壁宽度
    screen_hw = gw + 2          # 7
    scr_x1 = cx - screen_hw     # 48
    scr_x2 = cx + screen_hw     # 62

    # 曲廊 A 点
    ax, az = CORRIDOR["waypoints"][0]   # (55, 68)
    corridor_half = CORRIDOR["width"] // 2  # 2

    # ── 西侧通道: X = cx1(47) 到 scr_x1-1(47)，宽 3 格 ──
    # 实际通道: X 从 cx1(47) 到 scr_x1-3(45)...不对
    # 重新看 _build_courtyard:
    #   西段短墙: cx1 到 scr_x1-3-1 = 48-4 = 44
    #   也就是 cx1(47) 到 44 有短墙; 45~47 是通道
    # 通道是 scr_x1-3(45) 到 scr_x1-1(47), Z=cz_n(70), 3格宽

    # 西通道中心 X
    west_pass_x = scr_x1 - 2   # 46
    # 东通道: scr_x2+1(63) 到 scr_x2+3(65)
    east_pass_x = scr_x2 + 2   # 64

    # ── 西侧通道 → 向北铺到与曲廊A的Z对齐 ──
    # 从 Z=70 向北铺到 Z=68 (A点)
    # 路面中心沿 west_pass_x, 宽3格, Y=BUILD_Y
    for z in range(az, cz_n + 1):
        for dx in range(-1, 2):
            b.setblock(west_pass_x + dx, y0, z, SMOOTH_STONE)

    # 然后从西通道向东铺到 A 点 (X=55)
    # 沿 Z=68, 从 X=47 到 X=55
    for x in range(west_pass_x + 2, ax - corridor_half):
        for dz in range(-1, 2):
            b.setblock(x, y0, az + dz, SMOOTH_STONE)

    # ── 东侧通道 → 向北铺到与曲廊A的Z对齐 ──
    for z in range(az, cz_n + 1):
        for dx in range(-1, 2):
            b.setblock(east_pass_x + dx, y0, z, SMOOTH_STONE)

    # 然后从东通道向西铺到 A 点 (X=55+2=57 曲廊东边)
    for x in range(ax + corridor_half + 1, east_pass_x - 1):
        for dz in range(-1, 2):
            b.setblock(x, y0, az + dz, SMOOTH_STONE)

    # ── 花架下方（影壁北侧 Z=66~69）也需要地面 ──
    # 花架区域: bower_z2 = cz_n-1 = 69, bower_z1 = 69-4+1 = 66
    # 确保 Z=66~69 有地面可走
    bower_z2 = cz_n - 1   # 69
    bower_z1 = bower_z2 - 3  # 66
    for z in range(bower_z1, bower_z2 + 1):
        for dx in range(-1, 2):
            b.setblock(west_pass_x + dx, y0, z, SMOOTH_STONE)
            b.setblock(east_pass_x + dx, y0, z, SMOOTH_STONE)

    print(f"    影壁西通道 X={west_pass_x-1}~{west_pass_x+1}, "
          f"东通道 X={east_pass_x-1}~{east_pass_x+1}")


# ══════════════════════════════════════════════════════════════
#  2. 曲廊D(28,35) → 翠轩东入口
# ══════════════════════════════════════════════════════════════

def fix_corridor_to_hall(b):
    """曲廊D点通往翠轩。

    翠轩: cx=16, cz=35, width_x=17, width_z=11
      hx=8, hz=5 → base: X=8~24, Z=30~40
      front_x = cx+hx-1 = 23 (东面柱线)
      台基东边 X = cx+hx = 24
      floor_y = ground_y+1 = -59 (踩踏面)

    曲廊 D = (28,35), Y=-60, 宽5格 → 西侧柱 X=26
    间隙: X=25 (可能就一格空隙，或台基到26)

    从 X=24(台基边) 到 X=26(曲廊西柱), Z=33~37, Y=-60 铺地面，
    在台基处放东向踏步上到 floor_y=-59。
    """
    print("  [2/9] 曲廊D → 翠轩...")

    h_cfg = HALL
    h_cx, h_cz = h_cfg["cx"], h_cfg["cz"]       # 16, 35
    h_hx = h_cfg["width_x"] // 2                  # 8
    h_gy = h_cfg["ground_y"]                       # -60
    h_floor_y = h_gy + 1                           # -59 (踩踏面)

    hall_east_edge = h_cx + h_hx                   # 24 (台基东边)
    hall_front_x = h_cx + h_hx - 1                 # 23 (柱线)

    # 曲廊D
    dx, dz = CORRIDOR["waypoints"][3]              # (28, 35)
    corr_half = CORRIDOR["width"] // 2             # 2
    corr_west_x = dx - corr_half                   # 26

    # 路面宽: Z = dz-2 到 dz+2 = 33 到 37 (5格宽，与曲廊等宽)
    road_z1 = dz - corr_half                       # 33
    road_z2 = dz + corr_half                       # 37

    # ── 铺地面: X=24 到 X=26, Z=33~37, Y=BUILD_Y ──
    # 先清空上方可能的障碍
    b.fill(hall_east_edge, BUILD_Y, road_z1,
           corr_west_x, BUILD_Y + 3, road_z2, AIR)

    # 铺底层石砖地面 (Y=-60)
    b.fill(hall_east_edge, BUILD_Y, road_z1,
           corr_west_x, BUILD_Y, road_z2, SMOOTH_STONE)

    # ── 翠轩台基上踏步: X=24, Z=33~37, 从 Y=-60 上到 Y=-59 ──
    # facing=west → 低端朝东(曲廊侧), 高端朝西(翠轩侧)
    # 人从东面(曲廊 Y=-60)走上台阶到西面(翠轩 floor_y=-59)
    for z in range(road_z1, road_z2 + 1):
        b.setblock(hall_east_edge, BUILD_Y, z,
                   f"{STONE_BRICK_STAIR}[facing=west,half=bottom]")

    # 额外：翠轩东面入口区 (front_x=23) 确保无栏杆阻挡
    # 入口 5 格: cz-2 ~ cz+2 = 33~37 应已预留
    # 再明确清一遍入口区域的栏杆
    for z in range(road_z1, road_z2 + 1):
        b.setblock(hall_front_x, h_floor_y + 1, z, AIR)

    print(f"    铺路 X={hall_east_edge}~{corr_west_x}, "
          f"Z={road_z1}~{road_z2}, 台阶在 X={hall_east_edge}")


# ══════════════════════════════════════════════════════════════
#  3. 曲廊E→H 爬山廊改造
# ══════════════════════════════════════════════════════════════

def fix_corridor_climbing(b):
    """将曲廊 E(28,20)->F(55,20)->G(70,20)->H(70,15) 改为爬山廊。

    当前: 全部建在 Y=BUILD_Y=-60 (平地)
    目标: 从 Y=-60 (E点) 渐升到 Y=-57 (H点=牡丹亭ground_y)

    分段处理:
      E->F: (28,20)->(55,20) 沿X轴, 27格长, 升3格 → 每9格升1级
      F->G: (55,20)->(70,20) 沿X轴, 15格长, 保持已到达高度
      G->H: (70,20)->(70,15) 沿Z轴, 5格长, 微调到-57

    实际策略: 整段E->H水平距离 = 27+15+5 = 47格, 升3格
      每 ~15.7 格升1级。
      在E->F段: X=28 Y=-60, X=44 Y=-59, X=59 Y=-58 (进入F->G)
      在F->G段继续: X=70 Y=-57 (抵达G)
      G->H段: 维持 Y=-57
    """
    print("  [3/9] 爬山廊 E→H...")

    wps = CORRIDOR["waypoints"]
    ph = CORRIDOR["pillar_h"]           # 4
    half = CORRIDOR["width"] // 2       # 2
    ps = CORRIDOR["pillar_space"]       # 4

    # waypoints: E=index4, F=5, G=6, H=7
    ex, ez = wps[4]   # (28, 20)
    fx, fz = wps[5]   # (55, 20)
    gx, gz = wps[6]   # (70, 20)
    hx, hz = wps[7]   # (70, 15)

    start_y = BUILD_Y                   # -60
    end_y = PAVILION["ground_y"]        # -57
    total_rise = end_y - start_y        # 3

    # ── 先清除旧的平廊（E->F->G->H 全段）──
    # 清除范围 Y: start_y-1 到 end_y+ph+2 (覆盖爬升后最高屋顶)
    clear_top = end_y + ph + 2   # -57 + 4 + 2 = -51
    # E->F 段 (沿X, Z=20)
    b.fill(ex - half, start_y - 1, ez - half,
           fx + half, clear_top, ez + half, AIR)
    # F->G 段 (沿X, Z=20)
    b.fill(fx - half, start_y - 1, gz - half,
           gx + half, clear_top, gz + half, AIR)
    # G->H 段 (沿Z, X=70)
    b.fill(gx - half, start_y - 1, hz - half,
           gx + half, clear_top, gz + half, AIR)

    # ── 转角 E(28,20), F(55,20), G(70,20) 也清除 ──
    for ccx, ccz in [(ex, ez), (fx, fz), (gx, gz)]:
        b.fill(ccx - half, start_y - 1, ccz - half,
               ccx + half, clear_top, ccz + half, AIR)

    # ── 计算升阶点: 总水平距离 = |F-E|+|G-F|+|G_z-H_z| ──
    seg_ef = fx - ex     # 27
    seg_fg = gx - fx     # 15
    seg_gh = gz - hz     # 5
    total_dist = seg_ef + seg_fg + seg_gh  # 47

    # 升阶间距 (3次升阶)
    step_interval = total_dist // (total_rise + 1)  # ~11

    # 升阶累计距离: 在距离 ~12, ~24, ~36 处各升1级
    rise_at = []
    for i in range(1, total_rise + 1):
        rise_at.append(i * step_interval)
    # rise_at ≈ [11, 22, 33] (从E出发的水平距离)

    def _y_at_dist(d):
        """给定从 E 出发的水平距离，返回当前 Y"""
        y = start_y
        for rd in rise_at:
            if d >= rd:
                y += 1
        return y

    def _dist_at_pos(x, z):
        """给定坐标，计算从 E 出发的累计水平距离"""
        if z == ez:
            # E->F->G 段 (沿X轴)
            return x - ex
        else:
            # G->H 段 (沿Z轴，X=gx)
            return seg_ef + seg_fg + (gz - z)

    # ── 重建 E->F 段（沿X, Z=20）──
    print("    E->F 爬山段...")
    zc = ez  # 20
    for x in range(ex, fx + 1):
        d = x - ex
        y = _y_at_dist(d)

        # 检查是否在升阶位置（需要放楼梯）
        is_step_up = False
        for rd in rise_at:
            if d == rd:
                is_step_up = True
                break

        if is_step_up:
            # 台阶放在升阶前的Y（y-1），这样低端和前一格地面齐平
            # facing=east → 低端在西(小X), 高端在东(大X)
            for dz in range(-1, 2):
                b.setblock(x, y - 1, zc + dz,
                           f"{STONE_BRICK_STAIR}[facing=east,half=bottom]")
            b.setblock(x, y - 1, zc + half, FLOOR_ALT)
            b.setblock(x, y - 1, zc - half, FLOOR_ALT)
        else:
            # 普通地面
            for dz in range(-1, 2):
                b.setblock(x, y, zc + dz, SMOOTH_STONE)
            b.setblock(x, y, zc + half, FLOOR_ALT)
            b.setblock(x, y, zc - half, FLOOR_ALT)

        # ── 柱子（每 ps 格或起终点）──
        if (x - ex) % ps == 0 or x == ex or x == fx:
            for side_z in [zc + half, zc - half]:
                b.setblock(x, y, side_z, BASE_COL)  # 柱础
                for dy in range(1, ph + 1):
                    b.setblock(x, y + dy, side_z, PILLAR)
            # 横梁
            b.fill(x, y + ph, zc - half, x, y + ph, zc + half, BEAM)

        # ── 栏杆（非柱位）──
        if (x - ex) % ps != 0 and x != ex and x != fx:
            b.setblock(x, y + 1, zc + half, RAIL)
            b.setblock(x, y + 1, zc - half, RAIL)

        # ── 挂落 ──
        if (x - ex) % ps != 0 and x != ex and x != fx:
            b.setblock(x, y + ph, zc + half,
                       f'{TRAPDOOR}[facing=north,half=top,open=true]')
            b.setblock(x, y + ph, zc - half,
                       f'{TRAPDOOR}[facing=south,half=top,open=true]')

    # ── 转角 F(55,20) ──
    f_y = _y_at_dist(seg_ef)
    _build_climbing_corner(b, fx, fz, f_y, ph, half)

    # ── 重建 F->G 段（沿X, Z=20）──
    print("    F->G 爬山段...")
    for x in range(fx, gx + 1):
        d = seg_ef + (x - fx)
        y = _y_at_dist(d)

        is_step_up = False
        for rd in rise_at:
            if d == rd:
                is_step_up = True
                break

        if is_step_up:
            # 台阶放在 y-1（升阶前高度），低端和前格齐平
            for dz in range(-1, 2):
                b.setblock(x, y - 1, zc + dz,
                           f"{STONE_BRICK_STAIR}[facing=east,half=bottom]")
            b.setblock(x, y - 1, zc + half, FLOOR_ALT)
            b.setblock(x, y - 1, zc - half, FLOOR_ALT)
        else:
            for dz in range(-1, 2):
                b.setblock(x, y, zc + dz, SMOOTH_STONE)
            b.setblock(x, y, zc + half, FLOOR_ALT)
            b.setblock(x, y, zc - half, FLOOR_ALT)

        if (x - fx) % ps == 0 or x == fx or x == gx:
            for side_z in [zc + half, zc - half]:
                b.setblock(x, y, side_z, BASE_COL)
                for dy in range(1, ph + 1):
                    b.setblock(x, y + dy, side_z, PILLAR)
            b.fill(x, y + ph, zc - half, x, y + ph, zc + half, BEAM)
        else:
            b.setblock(x, y + 1, zc + half, RAIL)
            b.setblock(x, y + 1, zc - half, RAIL)
            b.setblock(x, y + ph, zc + half,
                       f'{TRAPDOOR}[facing=north,half=top,open=true]')
            b.setblock(x, y + ph, zc - half,
                       f'{TRAPDOOR}[facing=south,half=top,open=true]')

    # ── 转角 G(70,20) ──
    g_y = _y_at_dist(seg_ef + seg_fg)
    _build_climbing_corner(b, gx, gz, g_y, ph, half)

    # ── 重建 G->H 段（沿Z, X=70, 从Z=20向北到Z=15）──
    print("    G->H 段...")
    xc = gx  # 70
    for z in range(hz, gz + 1):
        d = seg_ef + seg_fg + (gz - z)
        y = _y_at_dist(d)

        is_step_up = False
        for rd in rise_at:
            if d == rd:
                is_step_up = True
                break

        if is_step_up:
            # 台阶放在 y-1（升阶前高度）
            # facing=north → 低端在南(大Z), 高端在北(小Z)
            for dx in range(-1, 2):
                b.setblock(xc + dx, y - 1, z,
                           f"{STONE_BRICK_STAIR}[facing=north,half=bottom]")
            b.setblock(xc + half, y - 1, z, FLOOR_ALT)
            b.setblock(xc - half, y - 1, z, FLOOR_ALT)
        else:
            for dx in range(-1, 2):
                b.setblock(xc + dx, y, z, SMOOTH_STONE)
            b.setblock(xc + half, y, z, FLOOR_ALT)
            b.setblock(xc - half, y, z, FLOOR_ALT)

        if (gz - z) % ps == 0 or z == gz or z == hz:
            for side_x in [xc + half, xc - half]:
                b.setblock(side_x, y, z, BASE_COL)
                for dy in range(1, ph + 1):
                    b.setblock(side_x, y + dy, z, PILLAR)
            b.fill(xc - half, y + ph, z, xc + half, y + ph, z, BEAM)
        else:
            b.setblock(xc + half, y + 1, z, RAIL)
            b.setblock(xc - half, y + 1, z, RAIL)
            b.setblock(xc + half, y + ph, z,
                       f'{TRAPDOOR}[facing=west,half=top,open=true]')
            b.setblock(xc - half, y + ph, z,
                       f'{TRAPDOOR}[facing=east,half=top,open=true]')

    # ── 屋顶: 逐格铺（跟随Y高度）──
    print("    爬山廊屋顶...")
    # E->F
    for x in range(ex, fx + 1):
        y = _y_at_dist(x - ex)
        roof_y = y + ph + 1
        b.fill(x, roof_y, zc - half, x, roof_y, zc + half,
               f'{ROOF_SLAB}[type=bottom]')
    # F->G
    for x in range(fx, gx + 1):
        y = _y_at_dist(seg_ef + x - fx)
        roof_y = y + ph + 1
        b.fill(x, roof_y, zc - half, x, roof_y, zc + half,
               f'{ROOF_SLAB}[type=bottom]')
    # G->H
    for z in range(hz, gz + 1):
        y = _y_at_dist(seg_ef + seg_fg + gz - z)
        roof_y = y + ph + 1
        b.fill(xc - half, roof_y, z, xc + half, roof_y, z,
               f'{ROOF_SLAB}[type=bottom]')

    # ── 记录终点高度供后续使用 ──
    h_y = _y_at_dist(total_dist)
    print(f"    爬山廊完成: E(Y={start_y}) → H(Y={h_y}), "
          f"升阶距离={rise_at}")


def _build_climbing_corner(b, cx, cz, y, ph, half):
    """爬山廊转角（简化版，跟随当前Y高度）"""
    beam_y = y + ph
    roof_y = y + ph + 1

    # 5x5 地面
    b.fill(cx - half, y, cz - half, cx + half, y, cz + half, FLOOR_ALT)
    b.fill(cx - 1, y, cz - 1, cx + 1, y, cz + 1, SMOOTH_STONE)

    # 四角柱
    corners = [
        (cx - half, cz - half),
        (cx + half, cz - half),
        (cx - half, cz + half),
        (cx + half, cz + half),
    ]
    for pcx, pcz in corners:
        b.setblock(pcx, y, pcz, BASE_COL)
        for dy in range(1, ph + 1):
            b.setblock(pcx, y + dy, pcz, PILLAR)

    # 横梁十字
    b.fill(cx - half, beam_y, cz - half, cx + half, beam_y, cz - half, BEAM)
    b.fill(cx - half, beam_y, cz + half, cx + half, beam_y, cz + half, BEAM)
    b.fill(cx - half, beam_y, cz - half, cx - half, beam_y, cz + half, BEAM)
    b.fill(cx + half, beam_y, cz - half, cx + half, beam_y, cz + half, BEAM)
    b.fill(cx - half, beam_y, cz, cx + half, beam_y, cz, BEAM)
    b.fill(cx, beam_y, cz - half, cx, beam_y, cz + half, BEAM)

    # 5x5 屋顶
    b.fill(cx - half, roof_y, cz - half, cx + half, roof_y, cz + half,
           f'{ROOF_SLAB}[type=bottom]')

    # 灯笼
    b.setblock(cx, beam_y - 1, cz, f'{LANTERN}[hanging=true]')


# ══════════════════════════════════════════════════════════════
#  4. 曲廊终点 H(70,15) → 牡丹亭西踏步
# ══════════════════════════════════════════════════════════════

def fix_corridor_to_pavilion(b):
    """曲廊H(70,15) → 牡丹亭西踏步。

    爬山廊终点 H: X=70, Z=15, Y≈-57 (与牡丹亭 ground_y 齐平)
    牡丹亭: cx=78, cz=15, r_base=8 → 西边台基 X = 78-8 = 70
    台基底 base_y+1 = -57+1 = -56 (stone_bricks)
    台面 base_y+2 = -55 (slab)
    踩踏面 pave_y = gy+3 = -54

    西面踏步在 X=70-1=69, 从 base_y+1(-56) 到 base_y+2(-55)

    廊道 H 终点 (70,15) Y=-57
    → 铺石板路 X=71~69 到台基踏步位置
    """
    print("  [4/9] 曲廊H → 牡丹亭...")

    p_cfg = PAVILION
    p_cx, p_cz = p_cfg["cx"], p_cfg["cz"]     # 78, 15
    p_gy = p_cfg["ground_y"]                    # -57
    p_r_base = p_cfg["r_base"]                  # 8

    pav_west_base = p_cx - p_r_base             # 70

    # 曲廊 H 点
    hx, hz = CORRIDOR["waypoints"][7]           # (70, 15)
    corr_half = CORRIDOR["width"] // 2          # 2

    # 爬山廊终点 Y 应该是 -57 (与 pavilion ground_y 齐平)
    h_y = p_gy                                  # -57

    # 牡丹亭西踏步: 在 X = pav_west_base-1 = 69, Z = cz-2 ~ cz+2
    # 已有踏步从 base_y+1 到 base_y+2 (Y=-56 到 -55)
    # 我们需要从 H(X=70, Y=-57) 过渡到台基踏步(X=69, Y=-56)

    # 铺路: 从 H 终点 (X=70) 向东铺到台基
    # 实际上 H 在 X=70，台基西边也在 X=70，它们已经接触
    # 曲廊终点 H 结构的北开口在 Z=15-1=14

    # ── 铺过渡路面: X=70 到 X=71, Z=13~17, Y=-57 ──
    road_z1 = p_cz - 2  # 13
    road_z2 = p_cz + 2  # 17
    for x in range(hx, pav_west_base + 1):
        b.fill(x, h_y, road_z1, x, h_y, road_z2, STONE_BRICK)

    # ── 在台基边缘(X=70)放上升台阶 → 从 Y=-57 到 Y=-56 ──
    # 台阶放在爬山廊地面高度 p_gy=-57（升阶前），让低端和路面齐平
    # facing=east → 低端朝西(曲廊侧), 高端朝东(牡丹亭侧)
    for z in range(road_z1, road_z2 + 1):
        b.setblock(pav_west_base, p_gy, z,
                   f"{STONE_BRICK_STAIR}[facing=east,half=bottom]")

    # ── 再上一级到台面 base_y+2 = -55 ──
    # 这一级已由 build_pavilion 的西面踏步处理 (cz-2~cz+2, 5格)
    # 验证: 牡丹亭西踏步放在 X=pav_west_base, 只有中间5格(cz-2~cz+2)
    # 额外的 Z 范围(z=13,17) 可能没有踏步，补上
    # 但 step_half=2, 踏步范围 cz-2~cz+2 = 13~17, 正好覆盖

    print(f"    铺路 X={hx}~{pav_west_base}, "
          f"Z={road_z1}~{road_z2}, 台阶在 X={pav_west_base}")


# ══════════════════════════════════════════════════════════════
#  5. 牡丹亭南踏步 → 芍药阑北入口
# ══════════════════════════════════════════════════════════════

def fix_pavilion_to_peony_rail(b):
    """牡丹亭南 → 芍药阑北。

    牡丹亭:
      cx=78, cz=15, r_base=8
      南踏步底 Z = cz + r_base + 1 = 24, Y ≈ base_y+1 = -56
      pave_y = gy+3 = -54 (亭内踩踏面)

    芍药阑:
      cx=78, cz=29, hz=4
      北边 Z = cz - hz = 25
      ground_y = -58
      栏杆 rail_y = gy+1 = -57

    间距: Z=24 (踏步底) → Z=25 (芍药阑北边)
    Y差: 牡丹亭台基底 -56 → 芍药阑地面 -58, 差2格
    需要: 2~3级台阶从 -56 下降到 -58
    """
    print("  [5/9] 牡丹亭 → 芍药阑...")

    p_cfg = PAVILION
    p_cx, p_cz = p_cfg["cx"], p_cfg["cz"]     # 78, 15
    p_gy = p_cfg["ground_y"]                    # -57
    p_r_base = p_cfg["r_base"]                  # 8

    pr_cfg = PEONY_RAIL
    pr_cx, pr_cz = pr_cfg["cx"], pr_cfg["cz"]  # 78, 29
    pr_gy = pr_cfg["ground_y"]                   # -58
    pr_hz = pr_cfg["hz"]                         # 4

    # 牡丹亭南台基外 Z
    pav_south_step_z = p_cz + p_r_base + 1       # 24
    pav_base_y = p_gy + 1                         # -56 (台基第一层)

    # 芍药阑北边 Z
    peony_north_z = pr_cz - pr_hz                 # 25
    peony_y = pr_gy                               # -58

    # 路宽 5格 (与入口等宽): cx-2 ~ cx+2
    road_x1 = p_cx - 2                            # 76
    road_x2 = p_cx + 2                            # 80

    # ── 从牡丹亭台基底(Z=24, Y=-56) 下到芍药阑(Z=25+, Y=-58) ──
    # 高差: -56 → -58 = 下降2格, 跨越 Z=24 → Z=25+
    #
    # 牡丹亭已有南踏步: Z=24, Y=-56 (facing=north, bottom)
    # 从芍药阑(Y=-58)看: 需要2级台阶上到-56
    #
    # 布局 (从南到北/从低到高):
    #   Z=27: 芍药阑区域 Y=-58 (地面)
    #   Z=26: 台阶 Y=-58 (facing=north) → 低端南/高端北, 升到 ~-57
    #   Z=25: 台阶 Y=-57 (facing=north) → 升到 ~-56
    #   Z=24: 已有牡丹亭踏步 Y=-56 (facing=north) → 升到台基二层

    # 第1级: Z=26, Y=-58 (从芍药阑地面起步)
    for x in range(road_x1, road_x2 + 1):
        b.setblock(x, peony_y, peony_north_z + 1,
                   f"{STONE_BRICK_STAIR}[facing=north,half=bottom]")

    # 第2级: Z=25, Y=-57
    for x in range(road_x1, road_x2 + 1):
        b.setblock(x, peony_y + 1, peony_north_z,
                   f"{STONE_BRICK_STAIR}[facing=north,half=bottom]")

    # Z=24 的踏步(Y=-56)已由 build_pavilion 建好, 不重复放置
    # 但确保两侧也有踏步（原始只有 cx-2~cx+2 范围）
    # road_x1=76, road_x2=80, 原始 step: cx-2~cx+2 = 76~80, 正好覆盖

    # ── 确保 Z=27 地面平整 (芍药阑入口前广场) ──
    for x in range(road_x1, road_x2 + 1):
        b.setblock(x, peony_y, peony_north_z + 2, STONE_BRICK)

    print(f"    台阶 Z={pav_south_step_z}~{peony_north_z+1}, "
          f"Y: {pav_base_y}→{peony_y}")


# ══════════════════════════════════════════════════════════════
#  6. 廊桥两端 → 路网
# ══════════════════════════════════════════════════════════════

def fix_bridge_connections(b):
    """廊桥两端接到路网。

    廊桥: cx=45, z_start=35(北端), z_end=55(南端), width=5
    北端(Z=35): 连到曲廊C(28,50)→D(28,35)方向，或翠轩区域
      翠轩 base 东边 X=24, 廊桥 X=43~47
      曲廊 D=(28,35) 的东柱 X=30
    南端(Z=55): 连到入口区石径方向 (cx=55附近)

    北端: 铺路 Z=34, X=43~47 向西延伸到曲廊附近 X=30
    南端: 铺路 Z=56, X=43~47 向东延伸到入口石径区 X=55
    """
    print("  [6/9] 廊桥端部...")

    b_cfg = BRIDGE
    b_cx = b_cfg["cx"]         # 45
    b_zs = b_cfg["z_start"]    # 35
    b_ze = b_cfg["z_end"]      # 55
    b_half = b_cfg["width"] // 2  # 2

    bx_w = b_cx - b_half       # 43
    bx_e = b_cx + b_half       # 47

    # 曲廊 D 点
    dx, dz = CORRIDOR["waypoints"][3]  # (28, 35)
    corr_half = CORRIDOR["width"] // 2  # 2
    corr_east = dx + corr_half          # 30

    # ── 北端: Z=34, 从桥面向西铺到曲廊东柱 ──
    # 铺路 X=30~47, Z=33~35, Y=-60
    road_z1 = b_zs - 1  # 34
    road_z2 = b_zs + 1  # 36
    for x in range(corr_east + 1, bx_w):
        for z in range(road_z1, road_z2 + 1):
            b.setblock(x, BUILD_Y, z, SMOOTH_STONE)

    # 边上放碎石装饰
    for x in range(corr_east + 2, bx_w, 2):
        b.setblock(x, BUILD_Y, road_z1 - 1, GRAVEL)
        b.setblock(x, BUILD_Y, road_z2 + 1, GRAVEL)

    # ── 南端: Z=56, 从桥面向东南铺到入口石径区 ──
    # 石径大约在 cx=55 附近, Z=55~65
    # 铺路 Z=55~56, X=47→55, Y=-60
    # 先铺桥南端到东边
    gate_cx = GATE_AREA["cx"]  # 55
    for x in range(bx_e + 1, gate_cx + 1):
        for dz in range(-1, 2):
            b.setblock(x, BUILD_Y, b_ze + dz, SMOOTH_STONE)

    # 从 Z=56 向南延伸到 Z=65 (与石径汇合)
    for z in range(b_ze + 1, b_ze + 6):
        for dx in range(-1, 2):
            b.setblock(gate_cx + dx, BUILD_Y, z, SMOOTH_STONE)

    # 南端到石径区域碎石
    for z in range(b_ze + 2, b_ze + 6, 2):
        b.setblock(gate_cx - 2, GROUND_Y, z, GRAVEL)
        b.setblock(gate_cx + 2, GROUND_Y, z, GRAVEL)

    print(f"    北端: X={corr_east+1}~{bx_w-1}, Z={road_z1}~{road_z2}")
    print(f"    南端: X={bx_e+1}~{gate_cx}, Z={b_ze-1}~{b_ze+5}")


# ══════════════════════════════════════════════════════════════
#  7. 画船 → 翠轩跳板
# ══════════════════════════════════════════════════════════════

def fix_boat_access(b):
    """画船 ↔ 翠轩木板跳板。

    画船: cx=25, cz=42, sx1=23, sx2=26, deck_y=-60
      船体西侧 X=23
    翠轩: front_x = 23 (东面柱线), base东边 X=24
      floor_y = -59

    画船甲板在 Y=-60, 翠轩 floor 在 Y=-59
    跳板: 从翠轩 floor(X=24, Y=-59) → 画船(X=23, Y=-60)
    用木板搭跳板 + 半砖过渡
    """
    print("  [7/9] 画船 → 翠轩...")

    boat_cfg = BOAT
    b_cx = boat_cfg["cx"]       # 25
    b_cz = boat_cfg["cz"]       # 42
    sw = 4
    sx1 = b_cx - sw // 2        # 23
    deck_y = BUILD_Y            # -60

    h_cfg = HALL
    h_cx = h_cfg["cx"]          # 16
    h_hx = h_cfg["width_x"] // 2  # 8
    h_floor_y = h_cfg["ground_y"] + 1  # -59

    hall_east_base = h_cx + h_hx       # 24
    hall_front_x = h_cx + h_hx - 1     # 23

    # 跳板区: 从翠轩东台基(X=24) 到画船西舷(X=23)
    # Z 范围: 画船中段几格 (Z=39~44)
    plank_z1 = b_cz - 3   # 39
    plank_z2 = b_cz + 2   # 44

    # ── 翠轩 floor 在 X=24 Y=-59, 画船 deck 在 X=23 Y=-60 ──
    # 高差 1 格。用台阶做无缝过渡:
    # X=24, Y=-60: 石砖台阶 facing=west → 低端朝东(画船), 高端朝西(翠轩)
    # 人从翠轩(Y=-59, X<24)走到 X=24 的台阶高端(west侧, ~Y=-59),
    # 再到低端(east侧, ~Y=-59.5), 然后踏上 X=23 画船甲板(Y=-60)
    for z in range(plank_z1, plank_z2 + 1):
        b.setblock(hall_east_base, deck_y, z,
                   f"{STONE_BRICK_STAIR}[facing=west,half=bottom]")

    # ── 木板跳板: X=23, Y=-60, 连接翠轩和画船 ──
    # 画船西舷在 X=23，已有 OAK_PLANKS
    # 在 X=23 铺一排 spruce_planks (跳板感)
    for z in range(plank_z1, plank_z2 + 1):
        b.setblock(sx1, deck_y, z, SPRUCE_PLANKS)

    # 跳板栏杆 (两侧)
    b.setblock(sx1, deck_y + 1, plank_z1, RAIL)
    b.setblock(sx1, deck_y + 1, plank_z2, RAIL)

    print(f"    跳板 X={sx1}, Z={plank_z1}~{plank_z2}")


# ══════════════════════════════════════════════════════════════
#  8. 南面水乡衔接
# ══════════════════════════════════════════════════════════════

def fix_south_town_connections(b):
    """园墙南门(Z=90) → 运河北岸(Z=94~96) 之间铺路。

    南墙缺口: X=48~62 (config WALL south_gap)
    南墙 Z = GARDEN z_max = 90
    运河北岸步道 Z=94~96

    需要: Z=90~94 之间铺石板路, 宽约 15 格
    """
    print("  [8/9] 南墙 → 水乡...")

    z_max = GARDEN["z_max"]                 # 90
    gap_x1, gap_x2 = WALL["south_gap"]      # (48, 62)

    # 运河北岸步道 Z 起始
    bank_z = 94

    # ── 铺路: Z=91~94, X=gap_x1~gap_x2, Y=BUILD_Y ──
    # 先确保地面平整
    road_x1 = gap_x1
    road_x2 = gap_x2
    road_z1 = z_max + 1  # 91
    road_z2 = bank_z     # 94

    # 主路面 (石砖)
    b.fill(road_x1, BUILD_Y, road_z1,
           road_x2, BUILD_Y, road_z2, STONE_BRICK)

    # 路面中央 3 格用 smooth_stone 区分
    mid_x = (road_x1 + road_x2) // 2  # 55
    b.fill(mid_x - 1, BUILD_Y, road_z1,
           mid_x + 1, BUILD_Y, road_z2, SMOOTH_STONE)

    # 两侧边石 (半砖)
    for z in range(road_z1, road_z2 + 1):
        b.setblock(road_x1 - 1, BUILD_Y, z,
                   f"{STONE_BRICK_SLAB}[type=bottom]")
        b.setblock(road_x2 + 1, BUILD_Y, z,
                   f"{STONE_BRICK_SLAB}[type=bottom]")

    # 门外台阶 (Z=90→91, 可能有高差)
    # 南墙在 BUILD_Y, 门外也是 BUILD_Y, 应该平齐
    # 在门洞两侧放灯笼柱
    for lx in [road_x1, road_x2]:
        b.setblock(lx, BUILD_Y + 1, z_max + 1, STONE_BRICK)
        b.setblock(lx, BUILD_Y + 2, z_max + 1, STONE_BRICK)
        b.setblock(lx, BUILD_Y + 3, z_max + 1, LANTERN)

    print(f"    路面 X={road_x1}~{road_x2}, Z={road_z1}~{road_z2}")


# ══════════════════════════════════════════════════════════════
#  9. 全园地面填充 — 消灭裸草地/空旷感
# ══════════════════════════════════════════════════════════════

def fix_garden_ground_cover(b):
    """在建筑间铺碎石小径、驳岸加强、高地坡面植被。

    分区处理:
    a) 曲廊沿线裸地: 碎石+苔藓地毯
    b) 池塘驳岸: 石砖+半砖加强
    c) 高地坡面: 草径+碎石过渡
    d) 主动线石径(入口→曲廊→翠轩→牡丹亭)沿线碎石装饰
    """
    print("  [9/9] 地面填充...")
    random.seed(45)

    # ── a) 池塘驳岸加强 ──
    print("    池塘驳岸...")
    pond_cx = POND["cx"]       # 52
    pond_cz = POND["cz"]       # 45
    pond_rx = POND["rx"]       # 23
    pond_rz = POND["rz"]       # 12

    # 在池塘椭圆外 1~3 格的区域铺石砖驳岸
    for x in range(pond_cx - pond_rx - 3, pond_cx + pond_rx + 4):
        for z in range(pond_cz - pond_rz - 3, pond_cz + pond_rz + 4):
            # 检查范围
            if x < GARDEN["x_min"] or x > GARDEN["x_max"]:
                continue
            if z < GARDEN["z_min"] or z > GARDEN["z_max"]:
                continue

            # 到椭圆中心的归一化距离
            dx = (x - pond_cx) / pond_rx
            dz = (z - pond_cz) / pond_rz
            dist = math.sqrt(dx * dx + dz * dz)

            # 椭圆边缘外 1.0 ~ 1.15 的环带
            if 1.0 < dist <= 1.15:
                # 石砖驳岸
                b.setblock(x, BUILD_Y, z, STONE_BRICK)
            elif 1.15 < dist <= 1.25:
                # 外圈碎石
                if random.random() < 0.5:
                    b.setblock(x, GROUND_Y, z, GRAVEL)

    # ── b) 高地南缘过渡带 (Z=20~25 之间, 高地渐降到平地) ──
    print("    高地南缘...")
    # 在 Z=22~26 区域（高地和平地的过渡区）铺碎石+苔藓
    for x in range(30, 91):
        for z in range(22, 27):
            if random.random() < 0.3:
                b.setblock(x, GROUND_Y, z,
                           random.choice([GRAVEL, COBBLE, MOSSY_COBBLE]))

    # ── c) 主动线碎石铺装 ──
    print("    主动线碎石...")

    # 曲廊两侧碎石装饰带 (曲廊A→B→C→D段, 在曲廊 width+1 格外)
    wps = CORRIDOR["waypoints"]
    corr_half = CORRIDOR["width"] // 2  # 2

    # A->B (Z=68, X=28~55): 曲廊南北两侧
    for x in range(wps[1][0], wps[0][0] + 1):
        for side in [-corr_half - 1, corr_half + 1]:
            z = wps[0][1] + side  # 68 ± 3
            if random.random() < 0.4:
                b.setblock(x, GROUND_Y, z,
                           random.choice([GRAVEL, PATH_BLOCK]))

    # B->C (X=28, Z=50~68): 东西两侧
    for z in range(wps[2][1], wps[1][1] + 1):
        for side in [-corr_half - 1, corr_half + 1]:
            x = wps[1][0] + side  # 28 ± 3
            if random.random() < 0.4:
                b.setblock(x, GROUND_Y, z,
                           random.choice([GRAVEL, PATH_BLOCK]))

    # C->D (X=28, Z=35~50): 东西两侧
    for z in range(wps[3][1], wps[2][1] + 1):
        for side in [-corr_half - 1, corr_half + 1]:
            x = wps[2][0] + side
            if random.random() < 0.35:
                b.setblock(x, GROUND_Y, z,
                           random.choice([GRAVEL, PATH_BLOCK]))

    # ── d) 翠轩周围铺装 ──
    print("    翠轩周围...")
    h_cfg = HALL
    h_cx, h_cz = h_cfg["cx"], h_cfg["cz"]
    h_hx = h_cfg["width_x"] // 2
    h_hz = h_cfg["width_z"] // 2

    # 翠轩西面 (靠山面, X=8~9) 碎石
    for z in range(h_cz - h_hz - 2, h_cz + h_hz + 3):
        for x in range(h_cx - h_hx - 3, h_cx - h_hx):
            if random.random() < 0.5:
                b.setblock(x, GROUND_Y, z,
                           random.choice([GRAVEL, COBBLE, MOSSY_COBBLE]))

    # 翠轩南北两端碎石
    for x in range(h_cx - h_hx, h_cx + h_hx + 1):
        for z in [h_cz - h_hz - 1, h_cz - h_hz - 2,
                  h_cz + h_hz + 1, h_cz + h_hz + 2]:
            if random.random() < 0.4:
                b.setblock(x, GROUND_Y, z,
                           random.choice([GRAVEL, PATH_BLOCK]))

    # ── e) 牡丹亭→芍药阑之间补种 ──
    print("    亭阑之间...")
    p_cfg = PAVILION
    pr_cfg = PEONY_RAIL
    # Z=23~25 (台基南到芍药阑北), X=73~83
    for x in range(p_cfg["cx"] - 5, p_cfg["cx"] + 6):
        for z in range(p_cfg["cz"] + p_cfg["r_base"] + 2,
                       pr_cfg["cz"] - pr_cfg["hz"]):
            if random.random() < 0.3:
                b.setblock(x, GROUND_Y, z,
                           random.choice([GRAVEL, PATH_BLOCK]))

    # ── f) 入口区石径两侧 ──
    print("    入口石径两侧...")
    g_cfg = GATE_AREA
    # 石径在约 X=55, Z=54~65 之间 (花架到入口)
    for z in range(54, 66):
        for dx in [-3, -2, 3, 4]:
            x = g_cfg["cx"] + dx
            if random.random() < 0.35:
                b.setblock(x, GROUND_Y, z,
                           random.choice([GRAVEL, MOSSY_COBBLE]))

    print("    地面填充完成!")


# ══════════════════════════════════════════════════════════════
#  主入口
# ══════════════════════════════════════════════════════════════

def fix_all_connections(b):
    print("=== 全面衔接修复 ===")
    fix_gate_to_corridor(b)
    fix_corridor_to_hall(b)
    fix_corridor_climbing(b)
    fix_corridor_to_pavilion(b)
    fix_pavilion_to_peony_rail(b)
    fix_bridge_connections(b)
    fix_boat_access(b)
    fix_south_town_connections(b)
    fix_garden_ground_cover(b)
    print("=== 衔接修复完成 ===")


if __name__ == "__main__":
    with MinecraftBuilder() as b:
        fix_all_connections(b)
        print(f"Done! {b.cmd_count} commands")
