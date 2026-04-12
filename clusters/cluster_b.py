"""B群：西园 — 梅林→曲水→画船

大梅树(6,4) + 梅花庵(10,13) + 翠轩(16,28) + 池馆(34,20) + 画船(36,38)

动线: 梅林幽径 → 梅花庵小院 → 围墙石径 → 翠轩(悬山顶,面水) →
      短廊 → 池馆(半水半陆) → 码头栈道 → 画船(水上漂浮)

坐标系：X正=东, Z正=南, BUILD_Y=-60
"""

import sys
sys.path.insert(0, '/Users/lambertlin/minecraft-server/scripts')

import random
from builder import MinecraftBuilder
from blocks import PALETTE, GROUND_Y, BUILD_Y


# ══════════════════════════════════════════════════════════
# 材质常量
# ══════════════════════════════════════════════════════════

PILLAR     = PALETTE["pillar"]
BEAM       = PALETTE["beam"]
BEAM_LOG   = PALETTE["beam_log"]
ROOF       = PALETTE["roof"]
ROOF_BLOCK = PALETTE["roof_block"]
ROOF_SLAB  = PALETTE["roof_slab"]
EAVE       = PALETTE["eave_outer"]
EAVE_SLAB  = PALETTE["eave_slab"]
WALL       = PALETTE["wall"]
WALL_BASE  = PALETTE["wall_base"]
WALL_CAP   = PALETTE["wall_cap"]
BASE       = PALETTE["base"]
BASE_STEP  = PALETTE["base_step"]
BASE_SLAB  = PALETTE["base_slab"]
BASE_COL   = PALETTE["base_col"]
FLOOR      = PALETTE["floor"]
FLOOR_ALT  = PALETTE["floor_alt"]
FLOOR_WOOD = PALETTE["floor_wood"]
RAIL       = PALETTE["rail"]
WINDOW     = PALETTE["window"]
TRAPDOOR   = PALETTE["trapdoor"]
LANTERN    = PALETTE["lantern"]
GRAVEL     = PALETTE["gravel"]
CHERRY_LOG = PALETTE["cherry_log"]
CHERRY_LVS = PALETTE["cherry_leaves"]
OAK_PLANKS = "minecraft:oak_planks"
OAK_FENCE  = "minecraft:oak_fence"
RED_WOOL   = PALETTE["red_wool"]
WATER      = PALETTE["water"]
AIR        = PALETTE["air"]
COBBLE     = PALETTE["cobblestone"]
MOSSY_COBBLE = PALETTE["mossy_cobblestone"]

Y0 = BUILD_Y       # -60
WATER_Y = -61       # 水面


# ══════════════════════════════════════════════════════════
# 1. 梅林小院地面
# ══════════════════════════════════════════════════════════

def _build_plum_ground(b: MinecraftBuilder):
    """梅林小院碎石铺地: x=6~13, z=4~16"""
    print("  [1/10] 梅林小院地面...")
    random.seed(88)

    b.fill(6, Y0, 4, 13, Y0, 16, GRAVEL)
    # 随机苔石点缀
    for x in range(6, 14):
        for z in range(4, 17):
            if random.random() < 0.15:
                b.setblock(x, Y0, z, MOSSY_COBBLE)


# ══════════════════════════════════════════════════════════
# 2. 翠轩+池馆连续台基
# ══════════════════════════════════════════════════════════

def _build_continuous_platform(b: MinecraftBuilder):
    """连续台基: x=8~38, z=17~33, 石砖"""
    print("  [2/10] 翠轩+池馆连续台基...")
    b.fill(8, Y0, 17, 38, Y0, 33, BASE)


# ══════════════════════════════════════════════════════════
# 3. 大梅树 (6,4)
# ══════════════════════════════════════════════════════════

def _build_plum_tree(b: MinecraftBuilder):
    """大梅树: cherry_log 2x2 高12格 + cherry_leaves 树冠"""
    print("  [3/10] 大梅树...")

    tx, tz = 6, 4
    trunk_h = 12

    # 树干 2x2
    b.fill(tx, Y0 + 1, tz, tx + 1, Y0 + trunk_h, tz + 1, CHERRY_LOG)

    # 树冠: 分3层球形
    crown_y = Y0 + trunk_h - 2  # 从树干上部开始
    crown_layers = [
        # (y_offset, radius)
        (0, 4),   # 底层大
        (1, 5),   # 中层最大
        (2, 5),
        (3, 4),
        (4, 3),   # 上层收
        (5, 2),
        (6, 1),   # 顶
    ]

    random.seed(66)
    crown_cx = tx + 0.5
    crown_cz = tz + 0.5

    for dy, r in crown_layers:
        y = crown_y + dy
        for dx in range(-r, r + 1):
            for dz in range(-r, r + 1):
                dist = (dx * dx + dz * dz) ** 0.5
                if dist <= r + 0.3:
                    # 外圈随机裁剪
                    if dist > r - 1 and random.random() < 0.3:
                        continue
                    lx = tx + dx
                    lz = tz + dz
                    b.setblock(lx, y, lz, CHERRY_LVS)

    # 补树干穿过树冠区域
    b.fill(tx, crown_y, tz, tx + 1, crown_y + 3, tz + 1, CHERRY_LOG)


# ══════════════════════════════════════════════════════════
# 4. 梅花庵 (7~13, 10~16)
# ══════════════════════════════════════════════════════════

def _build_plum_hermitage(b: MinecraftBuilder):
    """梅花庵: 小院+围墙, 朝南, 简朴禅意"""
    print("  [4/10] 梅花庵...")

    ax1, ax2 = 7, 13
    az1, az2 = 10, 16   # z1=北, z2=南
    cx = 10
    cz = 13
    pillar_h = 4

    # 地面
    b.fill(ax1, Y0, az1, ax2, Y0, az2, FLOOR_ALT)

    # 建筑主体(8~12, 11~15) — 小于院子1圈
    rx1, rx2 = 8, 12
    rz1, rz2 = 11, 15

    # 四角柱
    pillar_pos = [(rx1, rz1), (rx2, rz1), (rx1, rz2), (rx2, rz2)]
    beam_y = Y0 + pillar_h

    for px, pz in pillar_pos:
        b.setblock(px, Y0, pz, BASE_COL)
        b.fill(px, Y0 + 1, pz, px, Y0 + pillar_h, pz, PILLAR)

    # 额枋
    b.fill(rx1, beam_y, rz1, rx2, beam_y, rz1, BEAM)
    b.fill(rx1, beam_y, rz2, rx2, beam_y, rz2, BEAM)
    b.fill(rx1, beam_y, rz1, rx1, beam_y, rz2, BEAM)
    b.fill(rx2, beam_y, rz1, rx2, beam_y, rz2, BEAM)

    # 北墙+西墙+东墙
    for y in range(Y0 + 1, beam_y):
        for z in range(rz1 + 1, rz2):
            b.setblock(rx1, y, z, WALL)  # 西墙
        for x in range(rx1 + 1, rx2):
            b.setblock(x, y, rz1, WALL)  # 北墙
        for z in range(rz1 + 1, rz2):
            b.setblock(rx2, y, z, WALL)  # 东墙

    # 南面开敞(朝院子方向)
    # 南面中间留3格门洞, 两侧半墙
    for y in range(Y0 + 1, beam_y):
        for x in range(rx1 + 1, rx2):
            if cx - 1 <= x <= cx + 1:
                continue  # 门洞
            b.setblock(x, y, rz2, WALL)

    # 悬山顶(东西向脊)
    _build_gable_roof_ew(b, rx1 - 1, rx2 + 1, rz1 - 1, rz2 + 1, beam_y + 1)

    # 围墙(院子四周)
    for z in range(az1, az2 + 1):
        for wx in [ax1, ax2]:
            # 跳过建筑柱位
            if wx in [rx1, rx2] and rz1 <= z <= rz2:
                continue
            b.setblock(wx, Y0 + 1, z, WALL_BASE)
            b.setblock(wx, Y0 + 2, z, WALL)
            b.setblock(wx, Y0 + 3, z, WALL_CAP)
    # 北围墙
    for x in range(ax1, ax2 + 1):
        b.setblock(x, Y0 + 1, az1, WALL_BASE)
        b.setblock(x, Y0 + 2, az1, WALL)
        b.setblock(x, Y0 + 3, az1, WALL_CAP)
    # 南围墙(中间留门)
    for x in range(ax1, ax2 + 1):
        if cx - 1 <= x <= cx + 1:
            continue
        b.setblock(x, Y0 + 1, az2, WALL_BASE)
        b.setblock(x, Y0 + 2, az2, WALL)
        b.setblock(x, Y0 + 3, az2, WALL_CAP)

    # 灯笼
    b.setblock(cx, beam_y - 1, cz, f'{LANTERN}[hanging=true]')

    # 木地板
    b.fill(rx1 + 1, Y0, rz1 + 1, rx2 - 1, Y0, rz2 - 1, FLOOR_WOOD)


def _build_gable_roof_ew(b: MinecraftBuilder, x1, x2, z1, z2, roof_y):
    """悬山顶(东西向脊线): 坡面向南北下降, 东西出檐

    与cluster_d的_build_gable_roof逻辑相同。
    """
    cz = (z1 + z2) // 2
    half_z = (z2 - z1) // 2

    layers = []
    cur_z_off = 0
    y_off = 0
    while cur_z_off < half_z:
        layers.append((y_off, cz - half_z + cur_z_off, cz + half_z - cur_z_off))
        cur_z_off += 1
        y_off += 1

    for dy, north_z, south_z in layers:
        y = roof_y + dy
        for x in range(x1, x2 + 1):
            b.setblock(x, y, north_z, f"{ROOF}[facing=south,half=bottom]")
            b.setblock(x, y, south_z, f"{ROOF}[facing=north,half=bottom]")
        if south_z - 1 >= north_z + 1:
            b.fill(x1, y, north_z + 1, x2, y, south_z - 1, ROOF_BLOCK)

    ridge_y = roof_y + y_off
    for x in range(x1, x2 + 1):
        b.setblock(x, ridge_y, cz, f"{ROOF_SLAB}[type=bottom]")


# ══════════════════════════════════════════════════════════
# 5. 梅花庵→翠轩 围墙石径 z=16→23
# ══════════════════════════════════════════════════════════

def _build_hermitage_to_cuixuan_path(b: MinecraftBuilder):
    """围墙石径: 从梅花庵南端(z=16)到翠轩北端(z=23), 沿x=10附近"""
    print("  [5/10] 梅花庵→翠轩围墙石径...")

    path_x = 10
    pz1, pz2 = 16, 23

    # 石径(碎石+泥径)
    for z in range(pz1, pz2 + 1):
        b.setblock(path_x, Y0, z, PALETTE["path"])
        b.setblock(path_x + 1, Y0, z, PALETTE["path"])

    # 西侧围墙(共享墙段)
    wall_x = path_x - 2  # x=8
    for z in range(pz1, pz2 + 1):
        b.setblock(wall_x, Y0 + 1, z, WALL_BASE)
        b.setblock(wall_x, Y0 + 2, z, WALL)
        b.setblock(wall_x, Y0 + 3, z, WALL_CAP)

    # 东侧围墙
    wall_x_e = path_x + 3  # x=13
    for z in range(pz1, pz2 + 1):
        b.setblock(wall_x_e, Y0 + 1, z, WALL_BASE)
        b.setblock(wall_x_e, Y0 + 2, z, WALL)
        b.setblock(wall_x_e, Y0 + 3, z, WALL_CAP)

    # 围墙花窗(居中)
    mid_z = (pz1 + pz2) // 2
    b.setblock(wall_x, Y0 + 2, mid_z, WINDOW)
    b.setblock(wall_x_e, Y0 + 2, mid_z, WINDOW)


# ══════════════════════════════════════════════════════════
# 6. 翠轩 (8~24, 23~33) — 悬山顶, 东面朝曲水开敞
# ══════════════════════════════════════════════════════════

def _build_cui_xuan(b: MinecraftBuilder):
    """翠轩: 17x11悬山顶敞厅, 东面(面水)全开敞, 西墙封闭"""
    print("  [6/10] 翠轩...")

    hx1, hx2 = 8, 24
    hz1, hz2 = 23, 33  # z1=北, z2=南
    cx = 16
    cz = 28
    pillar_h = 5

    # 地面铺装
    b.fill(hx1, Y0, hz1, hx2, Y0, hz2, FLOOR)

    # 苍苔效果
    random.seed(43)
    for x in range(hx1, hx2 + 1):
        for z in range(hz1, hz2 + 1):
            if random.random() < 0.15:
                b.setblock(x, Y0, z, PALETTE["wall_mossy"])

    # 柱子: 前排(东面水)和后排(西背山), Z方向3等分
    front_x = hx2 - 1   # 23 (东面, 面水)
    back_x = hx1 + 1    # 9  (西面, 靠山)
    pillar_zs = [hz1 + 1, cz, hz2 - 1]  # 24, 28, 32

    floor_y = Y0
    beam_y = floor_y + pillar_h

    for pz in pillar_zs:
        for px in [front_x, back_x]:
            b.setblock(px, floor_y, pz, BASE_COL)
            b.fill(px, floor_y + 1, pz, px, floor_y + pillar_h, pz, PILLAR)

    # 额枋
    b.fill(front_x, beam_y, pillar_zs[0], front_x, beam_y, pillar_zs[-1], BEAM)
    b.fill(back_x, beam_y, pillar_zs[0], back_x, beam_y, pillar_zs[-1], BEAM)
    for pz in pillar_zs:
        b.fill(back_x, beam_y, pz, front_x, beam_y, pz, BEAM)

    # 西墙(背水面): 实墙
    for y in range(floor_y + 1, beam_y):
        for z in range(pillar_zs[0] + 1, pillar_zs[-1]):
            b.setblock(back_x, y, z, WALL)

    # 南北墙: 下半白墙, 上半花窗
    for y_offset in range(1, pillar_h):
        y = floor_y + y_offset
        for x in range(back_x + 1, front_x):
            for wz, face in [(pillar_zs[0], "south"), (pillar_zs[-1], "north")]:
                if y_offset <= 2:
                    b.setblock(x, y, wz, WALL)
                else:
                    b.setblock(x, y, wz,
                               f'{TRAPDOOR}[facing={face},half=top,open=true]')

    # 东面完全开敞 + 美人靠
    for z in range(pillar_zs[0] + 1, pillar_zs[1]):
        b.setblock(front_x, floor_y + 1, z,
                   "minecraft:acacia_stairs[facing=west,half=top]")
    for z in range(pillar_zs[1] + 1, pillar_zs[-1]):
        b.setblock(front_x, floor_y + 1, z,
                   "minecraft:acacia_stairs[facing=west,half=top]")

    # 悬山顶
    roof_z1 = pillar_zs[0] - 1
    roof_z2 = pillar_zs[-1] + 1
    roof_x1 = back_x - 1
    roof_x2 = front_x + 1

    # 东西坡: 脊线沿Z轴(南北), 坡面向东西
    _build_gable_roof_ns(b, roof_x1, roof_x2, roof_z1, roof_z2, beam_y + 1)

    # 灯笼
    b.setblock(front_x, beam_y - 1, cz, f'{LANTERN}[hanging=true]')
    b.setblock(back_x, beam_y - 1, cz, f'{LANTERN}[hanging=true]')
    b.setblock(cx, beam_y - 1, pillar_zs[0], f'{LANTERN}[hanging=true]')
    b.setblock(cx, beam_y - 1, pillar_zs[-1], f'{LANTERN}[hanging=true]')


def _build_gable_roof_ns(b: MinecraftBuilder, x1, x2, z1, z2, roof_y):
    """悬山顶(南北向脊线): 坡面向东西下降, 南北出檐

    脊线沿Z轴, 东西两面坡。
    """
    cx = (x1 + x2) // 2
    half_x = (x2 - x1) // 2

    layers = []
    cur_x_off = 0
    y_off = 0
    while cur_x_off < half_x:
        layers.append((y_off, cx - half_x + cur_x_off, cx + half_x - cur_x_off))
        cur_x_off += 1
        y_off += 1

    for dy, west_x, east_x in layers:
        y = roof_y + dy
        for z in range(z1, z2 + 1):
            b.setblock(west_x, y, z, f"{ROOF}[facing=east,half=bottom]")
            b.setblock(east_x, y, z, f"{ROOF}[facing=west,half=bottom]")
        if east_x - 1 >= west_x + 1:
            b.fill(west_x + 1, y, z1, east_x - 1, y, z2, ROOF_BLOCK)

    ridge_y = roof_y + y_off
    for z in range(z1, z2 + 1):
        b.setblock(cx, ridge_y, z, f"{ROOF_SLAB}[type=bottom]")


# ══════════════════════════════════════════════════════════
# 7. 翠轩→池馆 短廊 x=24→30
# ══════════════════════════════════════════════════════════

def _build_cuixuan_to_chiguan_corridor(b: MinecraftBuilder):
    """短廊: 从翠轩东端到池馆西端, 沿z=23(共享北墙线附近), 柱子复用"""
    print("  [7/10] 翠轩→池馆短廊...")

    lx1, lx2 = 24, 30
    lz = 23  # 走廊中心Z(翠轩北缘=池馆南缘附近区域)
    pillar_h = 4
    pillar_space = 3

    # 地面
    b.fill(lx1, Y0, lz - 1, lx2, Y0, lz + 1, FLOOR_ALT)
    b.fill(lx1, Y0, lz, lx2, Y0, lz, FLOOR)

    # 柱子+梁
    beam_y = Y0 + pillar_h
    roof_y = beam_y + 1

    for x in range(lx1, lx2 + 1, pillar_space):
        for dz in [-1, 1]:
            pz = lz + dz
            b.setblock(x, Y0, pz, BASE_COL)
            b.fill(x, Y0 + 1, pz, x, Y0 + pillar_h, pz, PILLAR)
        b.fill(x, beam_y, lz - 1, x, beam_y, lz + 1, BEAM)

    # 纵梁
    b.fill(lx1, beam_y, lz - 1, lx2, beam_y, lz - 1, BEAM)
    b.fill(lx1, beam_y, lz + 1, lx2, beam_y, lz + 1, BEAM)

    # 顶
    b.fill(lx1, roof_y, lz - 1, lx2, roof_y, lz + 1,
           f"{ROOF_SLAB}[type=bottom]")

    # 栏杆(柱间)
    for x in range(lx1, lx2 + 1):
        if (x - lx1) % pillar_space != 0:
            b.setblock(x, Y0 + 1, lz - 1, RAIL)
            b.setblock(x, Y0 + 1, lz + 1, RAIL)


# ══════════════════════════════════════════════════════════
# 8. 池馆 (30~38, 17~23) — 半水半陆
# ══════════════════════════════════════════════════════════

def _build_chi_guan(b: MinecraftBuilder):
    """池馆: 半水半陆, 北半(z=17~19)架于水上, 南半(z=20~23)落地"""
    print("  [8/10] 池馆...")

    px1, px2 = 30, 38
    pz1, pz2 = 17, 23  # z1=北(水上), z2=南(陆地)
    cx = 34
    cz = 20
    pillar_h = 5

    # 南半台基(陆地部分)
    b.fill(px1, Y0, 20, px2, Y0, pz2, BASE)
    floor_y = Y0

    # 北半水上: 柱子从水底撑起, 架空地板
    water_bottom = -63
    for x in [px1, px1 + 4, px2]:
        for z in [pz1, pz1 + 2]:
            b.fill(x, water_bottom, z, x, Y0, z, PILLAR)

    # 北半地板
    b.fill(px1, Y0, pz1, px2, Y0, pz1 + 2, FLOOR_WOOD)

    # 柱子
    beam_y = floor_y + pillar_h
    pillar_xs = [px1 + 1, cx, px2 - 1]
    pillar_zs_list = [pz1 + 1, pz2 - 1]

    for ppx in pillar_xs:
        for ppz in pillar_zs_list:
            b.setblock(ppx, floor_y, ppz, BASE_COL)
            b.fill(ppx, floor_y + 1, ppz, ppx, floor_y + pillar_h, ppz, PILLAR)

    # 额枋
    for ppz in pillar_zs_list:
        b.fill(pillar_xs[0], beam_y, ppz, pillar_xs[-1], beam_y, ppz, BEAM)
    for ppx in pillar_xs:
        b.fill(ppx, beam_y, pillar_zs_list[0], ppx, beam_y, pillar_zs_list[-1], BEAM)

    # 南墙(朝陆)
    for y in range(floor_y + 1, beam_y):
        for x in range(pillar_xs[0] + 1, pillar_xs[-1]):
            if cx - 1 <= x <= cx + 1:
                continue  # 门洞
            b.setblock(x, y, pz2 - 1, WALL)

    # 北面开敞(朝水), 栏杆
    for x in range(pillar_xs[0] + 1, pillar_xs[-1]):
        if x in pillar_xs:
            continue
        b.setblock(x, floor_y + 1, pz1 + 1, RAIL)

    # 东西半墙
    for y in range(floor_y + 1, floor_y + 3):
        for z in range(pillar_zs_list[0] + 1, pillar_zs_list[-1]):
            b.setblock(pillar_xs[0], y, z, WALL)
            b.setblock(pillar_xs[-1], y, z, WALL)

    # 悬山顶(南北向脊)
    _build_gable_roof_ns(b, px1 - 1, px2 + 1, pz1 - 1, pz2 + 1, beam_y + 1)

    # 灯笼
    b.setblock(cx, beam_y - 1, cz, f'{LANTERN}[hanging=true]')


# ══════════════════════════════════════════════════════════
# 9. 池馆→画船 码头栈道 z=23→33
# ══════════════════════════════════════════════════════════

def _build_dock(b: MinecraftBuilder):
    """码头栈道: 从池馆南端(z=23)到画船北端(z=33), 沿x=36附近"""
    print("  [9/10] 码头栈道...")

    dock_x = 36
    dz1, dz2 = 23, 33

    # 栈道主体: 3格宽木板, 水面以上
    for z in range(dz1, dz2 + 1):
        for dx in range(-1, 2):
            x = dock_x + dx
            b.setblock(x, Y0, z, OAK_PLANKS)

    # 栈道柱(每4格一对, 从水底支撑)
    water_bottom = -63
    for z in range(dz1, dz2 + 1, 4):
        for dx in [-1, 1]:
            x = dock_x + dx
            b.fill(x, water_bottom, z, x, Y0 - 1, z, PILLAR)

    # 两侧栏杆
    for z in range(dz1, dz2 + 1):
        b.setblock(dock_x - 1, Y0 + 1, z, OAK_FENCE)
        b.setblock(dock_x + 1, Y0 + 1, z, OAK_FENCE)

    # 灯笼(两端)
    b.setblock(dock_x, Y0 + 2, dz1, f'{LANTERN}[hanging=false]')
    b.setblock(dock_x, Y0 + 2, dz2, f'{LANTERN}[hanging=false]')


# ══════════════════════════════════════════════════════════
# 10. 画船 (34~38, 33~43) — 水上
# ══════════════════════════════════════════════════════════

def _build_painted_boat(b: MinecraftBuilder):
    """画船: 水上漂浮小舟, 船头朝北(z=33), 船尾朝南(z=43)"""
    print("  [10/10] 画船...")

    sx1, sx2 = 34, 38   # 5格宽
    sz_bow = 33          # 船头(北)
    sz_stern = 43        # 船尾(南)
    hull_y = WATER_Y     # -61 船底=水面
    deck_y = Y0          # -60 甲板

    # 船底
    b.fill(sx1, hull_y, sz_bow, sx2, hull_y, sz_stern, OAK_PLANKS)

    # 船舷(两侧)
    for z in range(sz_bow, sz_stern + 1):
        b.setblock(sx1, deck_y, z, OAK_PLANKS)
        b.setblock(sx2, deck_y, z, OAK_PLANKS)
    # 船尾封板
    for x in range(sx1, sx2 + 1):
        b.setblock(x, deck_y, sz_stern, OAK_PLANKS)

    # 船头尖角: z=33收窄, 用楼梯
    stair_n = "minecraft:oak_stairs[facing=north,half=bottom]"
    b.setblock(sx1, hull_y, sz_bow, stair_n)
    b.setblock(sx2, hull_y, sz_bow, stair_n)
    b.setblock(sx1, deck_y, sz_bow, AIR)
    b.setblock(sx2, deck_y, sz_bow, AIR)
    # z=34也稍微收
    b.setblock(sx1, deck_y, sz_bow + 1, stair_n)
    b.setblock(sx2, deck_y, sz_bow + 1, stair_n)

    # 顶棚(中段 z=36~41): 4柱 + 红色羊毛顶
    canopy_z1, canopy_z2 = 36, 41
    canopy_y_base = deck_y + 1
    canopy_y_top = deck_y + 2
    roof_y = deck_y + 3

    for x in [sx1 + 1, sx2 - 1]:
        for z in [canopy_z1, canopy_z2]:
            b.setblock(x, canopy_y_base, z, OAK_FENCE)
            b.setblock(x, canopy_y_top, z, OAK_FENCE)

    # 红色顶棚
    b.fill(sx1 + 1, roof_y, canopy_z1, sx2 - 1, roof_y, canopy_z2, RED_WOOL)

    # 船头灯笼
    cx_boat = (sx1 + sx2) // 2
    b.setblock(cx_boat, deck_y + 1, sz_bow + 1, OAK_FENCE)
    b.setblock(cx_boat, deck_y + 2, sz_bow + 1, LANTERN)

    # 船尾灯笼
    b.setblock(cx_boat, deck_y + 1, sz_stern, OAK_FENCE)
    b.setblock(cx_boat, deck_y + 2, sz_stern, LANTERN)


# ══════════════════════════════════════════════════════════
# 主入口
# ══════════════════════════════════════════════════════════

def build_cluster_b(b: MinecraftBuilder):
    """B群：西园 — 梅林→曲水→画船"""
    print("=== B群：西园群 ===")
    random.seed(77)

    _build_plum_ground(b)
    _build_continuous_platform(b)
    _build_plum_tree(b)
    _build_plum_hermitage(b)
    _build_hermitage_to_cuixuan_path(b)
    _build_cui_xuan(b)
    _build_cuixuan_to_chiguan_corridor(b)
    _build_chi_guan(b)
    _build_dock(b)
    _build_painted_boat(b)

    # 注册边界框
    b.register_bbox("cluster_b_plum", 4, GROUND_Y, 2, 14, Y0 + 16, 16)
    b.register_bbox("cluster_b_cuixuan", 7, GROUND_Y, 22, 25, Y0 + 12, 34)
    b.register_bbox("cluster_b_chiguan", 29, -63, 16, 39, Y0 + 10, 24)
    b.register_bbox("cluster_b_boat", 33, WATER_Y, 32, 39, Y0 + 4, 44)

    print(f"  B群建造完成!")


if __name__ == "__main__":
    with MinecraftBuilder() as b:
        build_cluster_b(b)
        print(f"Done! {b.cmd_count} commands")
