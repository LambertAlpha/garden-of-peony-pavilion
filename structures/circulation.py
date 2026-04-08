"""v3 动线系统 — 曲廊 + 入口区 + 廊桥 + 画船

v2→v3 关键变更:
- 曲廊总宽 5格 (柱1+走道3+柱1)，v2仅3格走道1格人走不进去
- 柱高 4格，头顶净空3格（舒适）
- 柱间距 4格，柱间放 crimson_fence 栏杆 + jungle_trapdoor 挂落
- 路线从 (55,68) 出发，经翠轩到 (70,15)
- 入口区移至 (55,80)，影壁两端各留3格通道
- 廊桥 cx=45, 5格宽
- 画船 4x10，比v2略大
"""

import sys; sys.path.insert(0, '/Users/lambertlin/minecraft-server/scripts')
from builder import MinecraftBuilder
from blocks import PALETTE, GROUND_Y, BUILD_Y
from config import CORRIDOR, GATE_AREA, BRIDGE, BOAT
import random


# ── 材质常量 ──
PILLAR     = PALETTE["pillar"]        # stripped_crimson_stem
BEAM       = PALETTE["beam"]          # dark_oak_planks
BEAM_LOG   = PALETTE["beam_log"]      # dark_oak_log
RAIL       = PALETTE["rail"]          # crimson_fence
RAIL_GATE  = PALETTE["rail_gate"]     # crimson_fence_gate
ROOF_SLAB  = PALETTE["roof_slab"]     # stone_brick_slab
ROOF_STAIR = PALETTE["roof"]          # stone_brick_stairs
ROOF_BLOCK = PALETTE["roof_block"]    # stone_bricks
FLOOR      = PALETTE["floor"]         # smooth_stone
FLOOR_ALT  = PALETTE["floor_alt"]     # stone_bricks
FLOOR_WOOD = PALETTE["floor_wood"]    # spruce_planks
LANTERN    = PALETTE["lantern"]       # lantern
BASE_COL   = PALETTE["base_col"]      # polished_andesite
WALL       = PALETTE["wall"]          # white_concrete
WALL_BASE  = PALETTE["wall_base"]     # stone_bricks
WALL_CAP   = PALETTE["wall_cap"]      # stone_brick_slab
WINDOW     = PALETTE["window"]        # iron_bars
TRAPDOOR   = PALETTE["trapdoor"]      # jungle_trapdoor
RED_CARPET = PALETTE["red_carpet"]
RED_WOOL   = PALETTE["red_wool"]
PATH       = PALETTE["path"]          # dirt_path
GRAVEL     = PALETTE["gravel"]
VINE       = PALETTE["vine"]
FENCE_SPR  = "minecraft:spruce_fence"  # 云杉栅栏(花架用)


# ══════════════════════════════════════════════════════════════
#  1. 曲廊系统
# ══════════════════════════════════════════════════════════════

def _build_segment(b, x1, z1, x2, z2, axis, y):
    """建造一段直线廊道 (v3: 5格宽 = 柱1+走道3+柱1)

    axis='x': 东西走向，柱在南北两侧 (z偏移±2)
    axis='z': 南北走向，柱在东西两侧 (x偏移±2)
    """
    w = CORRIDOR["width"]          # 5
    half = w // 2                  # 2 (中心到柱的偏移)
    ph = CORRIDOR["pillar_h"]      # 4
    ps = CORRIDOR["pillar_space"]  # 4

    if axis == 'x':
        _segment_x(b, x1, z1, x2, z2, y, half, ph, ps)
    else:
        _segment_z(b, x1, z1, x2, z2, y, half, ph, ps)


def _segment_x(b, x1, z1, x2, z2, y, half, ph, ps):
    """东西走向段: 沿X轴, 走道中心z=z1, 柱在z1-2和z1+2"""
    sx, ex = min(x1, x2), max(x1, x2)
    zc = z1
    z_s = zc + half   # 南侧柱线
    z_n = zc - half   # 北侧柱线

    # ── 地面: 走道3格 smooth_stone + 柱位2格 stone_bricks ──
    b.fill(sx, y, zc - 1, ex, y, zc + 1, FLOOR)           # 走道3格
    b.fill(sx, y, z_s, ex, y, z_s, FLOOR_ALT)             # 南柱基线
    b.fill(sx, y, z_n, ex, y, z_n, FLOOR_ALT)             # 北柱基线

    # ── 柱子 + 横梁 + 挂落 ──
    length = ex - sx
    pillar_xs = set()
    for i in range(0, length + 1, ps):
        px = sx + i
        if px > ex:
            break
        pillar_xs.add(px)
    # 确保末端有柱
    last_p = sx + (length // ps) * ps
    if last_p < ex:
        pillar_xs.add(ex)

    for px in sorted(pillar_xs):
        _place_pillar_pair_x(b, px, zc, y, half, ph)

    # ── 柱间栏杆 (1格高, 地面+1) ──
    for x in range(sx, ex + 1):
        if x not in pillar_xs:
            b.setblock(x, y + 1, z_s, RAIL)
            b.setblock(x, y + 1, z_n, RAIL)

    # ── 柱间挂落 (jungle_trapdoor 打开挂在梁下) ──
    beam_y = y + ph
    for x in range(sx, ex + 1):
        if x not in pillar_xs:
            # 挂落: 在梁下方(beam_y), 两侧柱线位置
            b.setblock(x, beam_y, z_s,
                       f'{TRAPDOOR}[facing=north,half=top,open=true]')
            b.setblock(x, beam_y, z_n,
                       f'{TRAPDOOR}[facing=south,half=top,open=true]')

    # ── 屋顶: 5格宽 stone_brick_slab ──
    roof_y = y + ph + 1
    b.fill(sx, roof_y, z_n, ex, roof_y, z_s,
           f'{ROOF_SLAB}[type=bottom]')


def _segment_z(b, x1, z1, x2, z2, y, half, ph, ps):
    """南北走向段: 沿Z轴, 走道中心x=x1, 柱在x1-2和x1+2"""
    sz, ez = min(z1, z2), max(z1, z2)
    xc = x1
    x_e = xc + half   # 东侧柱线
    x_w = xc - half   # 西侧柱线

    # ── 地面 ──
    b.fill(xc - 1, y, sz, xc + 1, y, ez, FLOOR)           # 走道3格
    b.fill(x_e, y, sz, x_e, y, ez, FLOOR_ALT)             # 东柱基线
    b.fill(x_w, y, sz, x_w, y, ez, FLOOR_ALT)             # 西柱基线

    # ── 柱子 ──
    length = ez - sz
    pillar_zs = set()
    for i in range(0, length + 1, ps):
        pz = sz + i
        if pz > ez:
            break
        pillar_zs.add(pz)
    last_p = sz + (length // ps) * ps
    if last_p < ez:
        pillar_zs.add(ez)

    for pz in sorted(pillar_zs):
        _place_pillar_pair_z(b, xc, pz, y, half, ph)

    # ── 柱间栏杆 ──
    for z in range(sz, ez + 1):
        if z not in pillar_zs:
            b.setblock(x_e, y + 1, z, RAIL)
            b.setblock(x_w, y + 1, z, RAIL)

    # ── 柱间挂落 ──
    beam_y = y + ph
    for z in range(sz, ez + 1):
        if z not in pillar_zs:
            b.setblock(x_e, beam_y, z,
                       f'{TRAPDOOR}[facing=west,half=top,open=true]')
            b.setblock(x_w, beam_y, z,
                       f'{TRAPDOOR}[facing=east,half=top,open=true]')

    # ── 屋顶 ──
    roof_y = y + ph + 1
    b.fill(x_w, roof_y, sz, x_e, roof_y, ez,
           f'{ROOF_SLAB}[type=bottom]')


def _place_pillar_pair_x(b, px, zc, y, half, ph):
    """东西走向: 在px处放南北两根柱子+柱础+横梁"""
    z_s = zc + half
    z_n = zc - half
    beam_y = y + ph

    for pz in (z_s, z_n):
        b.setblock(px, y, pz, BASE_COL)                   # 柱础
        for dy in range(1, ph + 1):
            b.setblock(px, y + dy, pz, PILLAR)            # 柱身4格

    # 横梁: 连接南北柱(跨走道5格)
    b.fill(px, beam_y, z_n, px, beam_y, z_s, BEAM)


def _place_pillar_pair_z(b, xc, pz, y, half, ph):
    """南北走向: 在pz处放东西两根柱子+柱础+横梁"""
    x_e = xc + half
    x_w = xc - half
    beam_y = y + ph

    for px in (x_e, x_w):
        b.setblock(px, y, pz, BASE_COL)
        for dy in range(1, ph + 1):
            b.setblock(px, y + dy, pz, PILLAR)

    b.fill(x_w, beam_y, pz, x_e, beam_y, pz, BEAM)


def _build_corner(b, cx, cz, y, ph, half):
    """转角: 角柱 + 十字横梁 + 5x5屋顶"""
    beam_y = y + ph
    roof_y = y + ph + 1

    # ── 5x5 地面 ──
    b.fill(cx - half, y, cz - half, cx + half, y, cz + half, FLOOR_ALT)
    b.fill(cx - 1, y, cz - 1, cx + 1, y, cz + 1, FLOOR)  # 中心走道3x3

    # ── 四角柱 ──
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

    # ── 十字横梁 ──
    # 东西向 (两条, z=cz-half 和 z=cz+half)
    b.fill(cx - half, beam_y, cz - half, cx + half, beam_y, cz - half, BEAM)
    b.fill(cx - half, beam_y, cz + half, cx + half, beam_y, cz + half, BEAM)
    # 南北向 (两条, x=cx-half 和 x=cx+half)
    b.fill(cx - half, beam_y, cz - half, cx - half, beam_y, cz + half, BEAM)
    b.fill(cx + half, beam_y, cz - half, cx + half, beam_y, cz + half, BEAM)
    # 中心十字梁
    b.fill(cx - half, beam_y, cz, cx + half, beam_y, cz, BEAM)
    b.fill(cx, beam_y, cz - half, cx, beam_y, cz + half, BEAM)

    # ── 5x5 屋顶 ──
    b.fill(cx - half, roof_y, cz - half, cx + half, roof_y, cz + half,
           f'{ROOF_SLAB}[type=bottom]')

    # ── 四角楼梯转角 ──
    b.setblock(cx - half, roof_y, cz - half,
               f'{ROOF_STAIR}[facing=south,half=bottom,shape=outer_right]')
    b.setblock(cx + half, roof_y, cz - half,
               f'{ROOF_STAIR}[facing=south,half=bottom,shape=outer_left]')
    b.setblock(cx - half, roof_y, cz + half,
               f'{ROOF_STAIR}[facing=north,half=bottom,shape=outer_left]')
    b.setblock(cx + half, roof_y, cz + half,
               f'{ROOF_STAIR}[facing=north,half=bottom,shape=outer_right]')

    # ── 转角灯笼 ──
    b.setblock(cx, beam_y - 1, cz, f'{LANTERN}[hanging=true]')


def build_corridors(b):
    """建造完整曲廊系统 (v3: 5格宽, 9个waypoint)"""
    print("=== 曲廊系统 v3 ===")

    wps = CORRIDOR["waypoints"]
    ph = CORRIDOR["pillar_h"]        # 4
    half = CORRIDOR["width"] // 2    # 2
    y = BUILD_Y

    # ── 路段: 相邻waypoint间的直线段 ──
    segments = []
    for i in range(len(wps) - 1):
        x1, z1 = wps[i]
        x2, z2 = wps[i + 1]
        # 判断轴向
        if z1 == z2:
            axis = 'x'
        elif x1 == x2:
            axis = 'z'
        else:
            # 斜线段不应该出现, 但防御一下
            print(f"  [WARN] 斜线段 ({x1},{z1})->({x2},{z2}), 跳过")
            continue
        segments.append(((x1, z1), (x2, z2), axis))

    # ── 建造直线段 ──
    print("  [1/3] 廊道直线段...")
    labels = "ABCDEFGHIJ"
    for i, ((x1, z1), (x2, z2), axis) in enumerate(segments):
        l1 = labels[i] if i < len(labels) else str(i)
        l2 = labels[i + 1] if i + 1 < len(labels) else str(i + 1)
        print(f"    段 {l1}->{l2}: ({x1},{z1})->({x2},{z2}) [{axis}]")
        _build_segment(b, x1, z1, x2, z2, axis, y)

    # ── 转角: 中间waypoint (不含首尾) ──
    print("  [2/3] 转角...")
    for i in range(1, len(wps) - 1):
        cx, cz = wps[i]
        # 判断前后段是否同轴 (直行则跳过转角)
        px, pz = wps[i - 1]
        nx, nz = wps[i + 1]
        prev_axis = 'x' if pz == cz else 'z'
        next_axis = 'x' if nz == cz else 'z'
        if prev_axis == next_axis:
            # 同轴直行, 不需要转角, 但可能需要侧门(如C2->翠轩)
            continue
        print(f"    转角 ({cx},{cz})")
        _build_corner(b, cx, cz, y, ph, half)

    # ── 起终点装饰 ──
    print("  [3/3] 起终点装饰...")
    _build_endpoints(b, wps, y, ph, half)

    # 注册边界框 (覆盖所有waypoint的范围)
    all_x = [p[0] for p in wps]
    all_z = [p[1] for p in wps]
    b.register_bbox("corridors",
                    min(all_x) - half, GROUND_Y, min(all_z) - half,
                    max(all_x) + half, y + ph + 2, max(all_z) + half)

    print("  曲廊建造完成!")


def _build_endpoints(b, wps, y, ph, half):
    """起点A和终点H的装饰柱+灯笼"""
    beam_y = y + ph

    # ── A点: 入口端, 向东开口(从入口区过来) ──
    ax, az = wps[0]
    # 东侧入口柱 (x+1处)
    for dz in (-half, half):
        b.setblock(ax + 1, y, az + dz, BASE_COL)
        for dy in range(1, ph + 1):
            b.setblock(ax + 1, y + dy, az + dz, PILLAR)
    b.fill(ax + 1, beam_y, az - half, ax + 1, beam_y, az + half, BEAM)
    b.setblock(ax + 1, beam_y - 1, az, f'{LANTERN}[hanging=true]')

    # ── H点: 终点端, 向北开口(通往牡丹亭) ──
    hx, hz = wps[-1]
    for dx in (-half, half):
        b.setblock(hx + dx, y, hz - 1, BASE_COL)
        for dy in range(1, ph + 1):
            b.setblock(hx + dx, y + dy, hz - 1, PILLAR)
    b.fill(hx - half, beam_y, hz - 1, hx + half, beam_y, hz - 1, BEAM)
    b.setblock(hx, beam_y - 1, hz - 1, f'{LANTERN}[hanging=true]')


# ══════════════════════════════════════════════════════════════
#  2. 入口区
# ══════════════════════════════════════════════════════════════

def _build_gate(b, cfg):
    """园门: 宽5格净空, 两根绯红柱+横梁+硬山顶小屋顶"""
    print("  [1/5] 园门...")

    cx = cfg["cx"]          # 55
    gz = cfg["cz"]          # 80 (南墙线Z)
    gw = cfg["gate_width"]  # 5 (净空宽度)
    y0 = cfg["ground_y"]

    # 两柱X坐标 (净空5格: 柱在 cx-3 和 cx+3, 净空 cx-2..cx+2)
    pw = cx - (gw // 2) - 1   # 西柱
    pe = cx + (gw // 2) + 1   # 东柱

    # ── 门槛 (石砖半砖) ──
    b.fill(pw + 1, y0, gz, pe - 1, y0, gz,
           f"{PALETTE['base_slab']}[type=bottom]")

    # ── 两根柱子 (5格高: y0..y0+4) ──
    for pillar_x in (pw, pe):
        b.setblock(pillar_x, y0, gz, BASE_COL)            # 柱础
        for dy in range(1, 5):
            b.setblock(pillar_x, y0 + dy, gz, PILLAR)     # 柱身4格

    # ── 横梁 (柱顶y0+5, 连接两柱) ──
    b.fill(pw, y0 + 5, gz, pe, y0 + 5, gz, BEAM)

    # ── 硬山顶小屋顶 ──
    roof_y = y0 + 6
    # 南坡
    for x in range(pw - 1, pe + 2):
        b.setblock(x, roof_y, gz + 1,
                   f"{ROOF_STAIR}[facing=north,half=bottom]")
    # 北坡
    for x in range(pw - 1, pe + 2):
        b.setblock(x, roof_y, gz - 1,
                   f"{ROOF_STAIR}[facing=south,half=bottom]")
    # 屋脊
    for x in range(pw - 1, pe + 2):
        b.setblock(x, roof_y, gz, ROOF_BLOCK)
    # 屋脊半砖收顶
    for x in range(pw - 1, pe + 2):
        b.setblock(x, roof_y + 1, gz, f"{ROOF_SLAB}[type=bottom]")

    # 两端山墙封板
    for gable_x in (pw - 1, pe + 1):
        b.setblock(gable_x, roof_y, gz, ROOF_BLOCK)


def _build_courtyard(b, cfg):
    """小庭院: 16x10, 石砖铺地, 矮墙围合(4格=墙基+墙身2+压瓦)"""
    print("  [2/5] 小庭院...")

    cx = cfg["cx"]
    cz = cfg["cz"]
    cw = cfg["court_width"]     # 16
    cd = cfg["court_depth"]     # 10
    gw = cfg["gate_width"]      # 5
    y0 = cfg["ground_y"]

    # 庭院范围
    cx1 = cx - cw // 2          # 55 - 8 = 47
    cx2 = cx + cw // 2          # 55 + 8 = 63
    cz_n = cz - cd              # 80 - 10 = 70  (北端=影壁线)
    cz_s = cz                   # 80 (南端=园门线)

    # ── 地面铺装 ──
    b.fill(cx1, y0, cz_n, cx2, y0, cz_s, FLOOR_ALT)

    # ── 矮墙 (4格高 = 墙基1+墙身2+压瓦1) ──
    def _wall_col(x, z):
        b.setblock(x, y0 + 1, z, WALL_BASE)
        b.setblock(x, y0 + 2, z, WALL)
        b.setblock(x, y0 + 3, z, WALL)
        b.setblock(x, y0 + 4, z, f"{WALL_CAP}[type=top]")

    # 东墙
    for z in range(cz_n, cz_s + 1):
        _wall_col(cx2, z)
    # 西墙
    for z in range(cz_n, cz_s + 1):
        _wall_col(cx1, z)

    # 南墙 (中段留门洞)
    gate_w = cx - gw // 2       # 门洞西端
    gate_e = cx + gw // 2       # 门洞东端
    for x in range(cx1, cx2 + 1):
        if gate_w <= x <= gate_e:
            continue
        _wall_col(x, cz_s)

    # 北墙 (影壁两端的短墙段, 中间留给影壁)
    # 影壁占中间, 两端各留3格通道
    screen_hw = (gw + 2)        # 影壁半宽: 稍宽于门
    scr_x1 = cx - screen_hw     # 影壁西端
    scr_x2 = cx + screen_hw     # 影壁东端
    # 西段短墙: cx1 到 scr_x1-3-1
    for x in range(cx1, scr_x1 - 3):
        _wall_col(x, cz_n)
    # 东段短墙: scr_x2+3+1 到 cx2
    for x in range(scr_x2 + 4, cx2 + 1):
        _wall_col(x, cz_n)

    # 花窗 (东西墙各一, 墙身中段)
    wz = (cz_n + cz_s) // 2
    b.setblock(cx2, y0 + 3, wz,
               f"{TRAPDOOR}[facing=west,half=bottom,open=true]")
    b.setblock(cx1, y0 + 3, wz,
               f"{TRAPDOOR}[facing=east,half=bottom,open=true]")

    return cx1, cx2, cz_n, cz_s, scr_x1, scr_x2


def _build_screen_wall(b, cfg, scr_x1, scr_x2, scr_z):
    """粉画垣/影壁: 5格高白墙+漏窗, 两端各留3格通道"""
    print("  [3/5] 粉画垣（影壁）...")

    y0 = cfg["ground_y"]

    # ── 影壁主体: 5格高 ──
    for x in range(scr_x1, scr_x2 + 1):
        b.setblock(x, y0 + 1, scr_z, WALL_BASE)       # 墙基
        b.setblock(x, y0 + 2, scr_z, WALL)             # 墙身
        b.setblock(x, y0 + 3, scr_z, WALL)             # 墙身
        b.setblock(x, y0 + 4, scr_z, WALL)             # 墙身
        b.setblock(x, y0 + 5, scr_z, f"{WALL_CAP}[type=top]")  # 压瓦

    # ── 漏窗: y0+3和y0+4层, 中间段用铁栏杆 ──
    for x in range(scr_x1 + 1, scr_x2):
        b.setblock(x, y0 + 4, scr_z, WINDOW)
    for x in range(scr_x1 + 1, scr_x2):
        if (x - scr_x1) % 2 == 0:
            b.setblock(x, y0 + 3, scr_z, WINDOW)

    # ── 底座加宽 (前后各出挑1格石砖) ──
    for x in range(scr_x1, scr_x2 + 1):
        b.setblock(x, y0, scr_z - 1, WALL_BASE)
        b.setblock(x, y0, scr_z + 1, WALL_BASE)
        b.setblock(x, y0 + 1, scr_z - 1,
                   f"{PALETTE['base_slab']}[type=top]")
        b.setblock(x, y0 + 1, scr_z + 1,
                   f"{PALETTE['base_slab']}[type=top]")


def _build_flower_bower(b, cfg, bx1, bx2, bz1, bz2):
    """荼蘼花架: 云杉栅栏搭架+藤蔓"""
    print("  [4/5] 荼蘼花架...")

    y0 = cfg["ground_y"]

    # ── 花架立柱 (四角+中间, 3格高) ──
    mid_x = (bx1 + bx2) // 2
    pillar_pos = [
        (bx1, bz1), (bx2, bz1), (bx1, bz2), (bx2, bz2),
        (mid_x, bz1), (mid_x, bz2),
    ]
    for px, pz in pillar_pos:
        for dy in range(1, 4):
            b.setblock(px, y0 + dy, pz, FENCE_SPR)

    # ── 顶部横梁+纵梁 (栅栏网格) ──
    for x in range(bx1, bx2 + 1):
        b.setblock(x, y0 + 3, bz1, FENCE_SPR)
        b.setblock(x, y0 + 3, bz2, FENCE_SPR)
    for x in range(bx1, bx2 + 1, 2):
        for z in range(bz1, bz2 + 1):
            b.setblock(x, y0 + 3, z, FENCE_SPR)

    # ── 藤蔓 ──
    for x in range(bx1 + 1, bx2):
        for z in range(bz1, bz2 + 1):
            if random.random() < 0.45:
                vine_len = random.choice([1, 2])
                for dy in range(vine_len):
                    vy = y0 + 2 - dy
                    face = random.choice(["north", "south", "east", "west"])
                    b.setblock(x, vy, z, f"{VINE}[{face}=true]")


def _build_winding_path(b, cfg, start_z, end_z):
    """蜿蜒石径: 2格宽dirt_path, 左右轻微偏移"""
    print("  [5/5] 石径...")

    cx = cfg["cx"]
    center_x = cx
    offset = 0
    direction = 1

    for z in range(start_z, end_z - 1, -1):
        b.setblock(center_x + offset, GROUND_Y, z, PATH)
        b.setblock(center_x + offset + 1, GROUND_Y, z, PATH)

        if random.random() < 0.45:
            offset += direction
            if abs(offset) >= 2:
                direction = -direction

    # 两侧随机碎石
    offset = 0
    direction = 1
    for z in range(start_z, end_z - 1, -1):
        if random.random() < 0.2:
            side = random.choice([-1, 2])
            b.setblock(center_x + offset + side, GROUND_Y, z, GRAVEL)
        if random.random() < 0.45:
            offset += direction
            if abs(offset) >= 2:
                direction = -direction


def build_gate_area(b):
    """建造入口区: 园门->小庭院->影壁->荼蘼花架->石径"""
    print("=== 入口区 v3 ===")
    random.seed(44)

    cfg = GATE_AREA

    # 1. 园门
    _build_gate(b, cfg)

    # 2. 小庭院 (返回范围用于后续组件定位)
    cx1, cx2, cz_n, cz_s, scr_x1, scr_x2 = _build_courtyard(b, cfg)

    # 3. 影壁
    _build_screen_wall(b, cfg, scr_x1, scr_x2, cz_n)

    # 4. 荼蘼花架 (影壁北侧)
    bower_depth = 4
    bower_z2 = cz_n - 1                          # 紧贴影壁北侧
    bower_z1 = bower_z2 - bower_depth + 1         # 北端
    bower_x1 = scr_x1
    bower_x2 = scr_x2
    _build_flower_bower(b, cfg, bower_x1, bower_x2, bower_z1, bower_z2)

    # 5. 石径 (从花架通向池塘)
    path_start_z = bower_z1 - 1
    path_end_z = path_start_z - 12                # 向北延伸约12格
    _build_winding_path(b, cfg, path_start_z, path_end_z)

    # 注册边界框
    b.register_bbox("gate_area",
                    cx1 - 2, GROUND_Y, path_end_z - 1,
                    cx2 + 2, BUILD_Y + 8, cz_s + 2)

    print("  入口区建造完成。")


# ══════════════════════════════════════════════════════════════
#  3. 廊桥
# ══════════════════════════════════════════════════════════════

def build_bridge(b):
    """廊桥: 5格宽(走道3+栏杆各1), 微拱, 石砖瓦顶"""
    print("=== 廊桥 v3 ===")

    cfg = BRIDGE
    cx = cfg["cx"]           # 45
    z_s = cfg["z_start"]     # 35 (北端, Z较小)
    z_e = cfg["z_end"]       # 55 (南端, Z较大)
    w = cfg["width"]         # 5
    half = w // 2            # 2

    bx_w = cx - half         # 43 (西边)
    bx_e = cx + half         # 47 (东边)
    # 走道: cx-1 到 cx+1 (3格)
    # 栏杆: bx_w 和 bx_e

    OAK = "minecraft:oak_planks"

    # ── 辅助: 桥面Y坐标 (微拱) ──
    def deck_y(z):
        """两端平直y=-60, 中段抬高y=-59"""
        mid = (z_s + z_e) // 2
        dist_from_mid = abs(z - mid)
        half_span = (z_e - z_s) // 2
        # 中间1/3抬高
        if dist_from_mid <= half_span // 3:
            return -59
        return -60

    # ── 过渡楼梯Z坐标 ──
    mid = (z_s + z_e) // 2
    half_span = (z_e - z_s) // 2
    arch_boundary = half_span // 3
    stair_z_n = mid - arch_boundary - 1   # 北侧过渡
    stair_z_s = mid + arch_boundary + 1   # 南侧过渡

    # ── 1. 桥面 ──
    print("  [1/6] 桥面...")
    for z in range(z_s, z_e + 1):
        dy = deck_y(z)
        b.fill(bx_w, dy, z, bx_e, dy, z, OAK)

    # ── 2. 过渡楼梯 ──
    print("  [2/6] 拱桥过渡...")
    for x in range(bx_w, bx_e + 1):
        b.setblock(x, -60, stair_z_s,
                   "minecraft:stone_brick_stairs[facing=south,half=bottom]")
        b.setblock(x, -60, stair_z_n,
                   "minecraft:stone_brick_stairs[facing=north,half=bottom]")

    # ── 3. 桥柱 (从水底到桥面) ──
    print("  [3/6] 桥柱...")
    pillar_zs = list(range(z_s, z_e + 1, 4))
    if pillar_zs[-1] != z_e:
        pillar_zs.append(z_e)
    for z in pillar_zs:
        dy = deck_y(z)
        for x in [bx_w, bx_e]:
            for yy in range(-63, dy):
                b.setblock(x, yy, z, PILLAR)

    # ── 4. 栏杆 + 红地毯 ──
    print("  [4/6] 栏杆+地毯...")
    for z in range(z_s, z_e + 1):
        dy = deck_y(z)
        # 两侧栏杆
        b.setblock(bx_w, dy + 1, z, RAIL)
        b.setblock(bx_e, dy + 1, z, RAIL)
        # 走道中间铺红地毯
        b.setblock(cx, dy + 1, z, RED_CARPET)

    # ── 5. 廊顶结构 ──
    print("  [5/6] 廊顶...")
    ph = 4  # 廊柱高
    for z in range(z_s, z_e + 1):
        dy = deck_y(z)
        roof_y = dy + ph + 1

        # 柱位处加顶柱+横梁
        if z in pillar_zs:
            for x in [bx_w, bx_e]:
                for yy in range(dy + 2, dy + ph + 1):
                    b.setblock(x, yy, z, PILLAR)
            b.fill(bx_w, dy + ph, z, bx_e, dy + ph, z, BEAM)

        # 顶棚 (5格宽)
        b.fill(bx_w, roof_y, z, bx_e, roof_y, z,
               f"{ROOF_SLAB}[type=top]")

    # ── 6. 端部衔接 ──
    print("  [6/6] 端部衔接...")
    for x in range(bx_w, bx_e + 1):
        b.setblock(x, -60, z_s - 1, OAK)
        b.setblock(x, -60, z_e + 1, OAK)

    b.register_bbox("bridge",
                    bx_w - 1, -63, z_s - 1,
                    bx_e + 1, -54, z_e + 1)

    print("  廊桥建造完成!")


# ══════════════════════════════════════════════════════════════
#  4. 画船
# ══════════════════════════════════════════════════════════════

def build_boat(b):
    """画船: 4x10, 橡木船体, 船头楼梯收尖, 红色羊毛顶棚, 船头灯笼"""
    print("=== 画船 v3 ===")

    cfg = BOAT
    cx = cfg["cx"]           # 25
    cz = cfg["cz"]           # 42

    OAK = "minecraft:oak_planks"
    OAK_STAIR_N = "minecraft:oak_stairs[facing=north,half=bottom]"
    OAK_STAIR_S = "minecraft:oak_stairs[facing=south,half=bottom]"
    OAK_FENCE = "minecraft:oak_fence"

    # 船体范围: 4x10
    sw = 4
    sl = 10
    sx1 = cx - sw // 2       # 23
    sx2 = cx + sw // 2 - 1   # 26  (4格: 23,24,25,26)
    sz_bow = cz - sl // 2    # 37  (船头=北)
    sz_stern = cz + sl // 2 - 1  # 46  (船尾=南)
    hull_y = GROUND_Y         # -61 (水面层)
    deck_y = BUILD_Y          # -60 (甲板)

    # ── 1. 船底 (4x10) ──
    print("  [1/5] 船底...")
    b.fill(sx1, hull_y, sz_bow, sx2, hull_y, sz_stern, OAK)

    # ── 2. 船舷 (两侧+船尾) ──
    print("  [2/5] 船舷...")
    for z in range(sz_bow + 1, sz_stern + 1):  # 跳过船头Z
        b.setblock(sx1, deck_y, z, OAK)
        b.setblock(sx2, deck_y, z, OAK)
    # 船尾封板
    b.fill(sx1, deck_y, sz_stern, sx2, deck_y, sz_stern, OAK)

    # ── 3. 船头收尖 ──
    print("  [3/5] 船头...")
    # 船头Z=sz_bow: 两侧用楼梯收尖, 中间2格保留
    b.setblock(sx1, hull_y, sz_bow, OAK_STAIR_N)
    b.setblock(sx2, hull_y, sz_bow, OAK_STAIR_N)
    # 中间2格平底
    b.setblock(sx1 + 1, hull_y, sz_bow, OAK)
    b.setblock(sx2 - 1, hull_y, sz_bow, OAK)

    # 船头不放船舷, 清除 (如果有)
    b.setblock(sx1, deck_y, sz_bow, "minecraft:air")
    b.setblock(sx2, deck_y, sz_bow, "minecraft:air")
    # 船头中间2格的船舷
    b.setblock(sx1 + 1, deck_y, sz_bow, OAK)
    b.setblock(sx2 - 1, deck_y, sz_bow, OAK)

    # Z=sz_bow+1 过渡: 两侧楼梯
    b.setblock(sx1, deck_y, sz_bow + 1, OAK_STAIR_N)
    b.setblock(sx2, deck_y, sz_bow + 1, OAK_STAIR_N)

    # ── 4. 顶棚 (中段6格, 红色羊毛) ──
    print("  [4/5] 顶棚...")
    canopy_z1 = sz_bow + 3
    canopy_z2 = sz_stern - 1
    canopy_y_base = deck_y + 1    # -59
    canopy_y_top = deck_y + 2     # -58
    roof_y = deck_y + 3           # -57

    # 4根角柱 (橡木栅栏, 2格高)
    for x in [sx1, sx2]:
        for z in [canopy_z1, canopy_z2]:
            b.setblock(x, canopy_y_base, z, OAK_FENCE)
            b.setblock(x, canopy_y_top, z, OAK_FENCE)

    # 红色羊毛顶棚 (4格宽 x 顶棚长度)
    b.fill(sx1, roof_y, canopy_z1, sx2, roof_y, canopy_z2, RED_WOOL)

    # ── 5. 装饰 ──
    print("  [5/5] 装饰...")
    # 船头灯笼: 中心位置竖一根短柱+灯笼
    bow_cx = (sx1 + sx2) // 2  # 船头中心X
    b.setblock(bow_cx, deck_y + 1, sz_bow, OAK_FENCE)
    b.setblock(bow_cx, deck_y + 2, sz_bow, LANTERN)

    # 船尾灯笼
    stern_cx = (sx1 + sx2) // 2
    b.setblock(stern_cx, deck_y + 1, sz_stern, OAK_FENCE)
    b.setblock(stern_cx, deck_y + 2, sz_stern, LANTERN)

    b.register_bbox("boat",
                    sx1 - 1, hull_y, sz_bow - 1,
                    sx2 + 1, roof_y + 1, sz_stern + 1)

    print("  画船建造完成!")


# ══════════════════════════════════════════════════════════════
#  主入口
# ══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    with MinecraftBuilder() as b:
        build_corridors(b)
        build_gate_area(b)
        build_bridge(b)
        build_boat(b)
        print(f"Done! {b.cmd_count} commands")
