"""D群：南部中轴 — 入口仪式序列

入口门厅(58,87) + 小庭深院(58,80) + 远香堂(58,67) + 闺塾(22,78)

仪式轴线：门厅→影壁→天井→抄手游廊→远香堂(北面朝湖全开敞)
闺塾偏西独立小院，经西廊道连回小庭。

坐标系：X正=东, Z正=南, BUILD_Y=-60
"""

import sys
sys.path.insert(0, '/Users/lambertlin/minecraft-server/scripts')

from builder import MinecraftBuilder
from blocks import PALETTE, GROUND_Y, BUILD_Y


# ══════════════════════════════════════════════════════════
# 材质常量
# ══════════════════════════════════════════════════════════

PILLAR     = PALETTE["pillar"]        # stripped_crimson_stem
BEAM       = PALETTE["beam"]          # dark_oak_planks
BEAM_LOG   = PALETTE["beam_log"]      # dark_oak_log
ROOF       = PALETTE["roof"]          # stone_brick_stairs
ROOF_BLOCK = PALETTE["roof_block"]    # stone_bricks
ROOF_SLAB  = PALETTE["roof_slab"]     # stone_brick_slab
EAVE       = PALETTE["eave_outer"]    # dark_oak_stairs
EAVE_SLAB  = PALETTE["eave_slab"]     # dark_oak_slab
WALL       = PALETTE["wall"]          # white_concrete
WALL_BASE  = PALETTE["wall_base"]     # stone_bricks
WALL_CAP   = PALETTE["wall_cap"]      # stone_brick_slab
BASE       = PALETTE["base"]          # stone_bricks
BASE_STEP  = PALETTE["base_step"]     # stone_brick_stairs
BASE_SLAB  = PALETTE["base_slab"]     # stone_brick_slab
BASE_COL   = PALETTE["base_col"]      # polished_andesite
FLOOR      = PALETTE["floor"]         # smooth_stone
FLOOR_ALT  = PALETTE["floor_alt"]     # stone_bricks
FLOOR_WOOD = PALETTE["floor_wood"]    # spruce_planks
RAIL       = PALETTE["rail"]          # crimson_fence
WINDOW     = PALETTE["window"]        # iron_bars
TRAPDOOR   = PALETTE["trapdoor"]      # jungle_trapdoor
LANTERN    = PALETTE["lantern"]
GRAVEL     = PALETTE["gravel"]
AIR        = PALETTE["air"]

Y0 = BUILD_Y  # -60


# ══════════════════════════════════════════════════════════
# 1. 中轴大台基
# ══════════════════════════════════════════════════════════

def _build_central_platform(b: MinecraftBuilder):
    """中轴大台基：一条 fill 命令，x=49~67, z=62~89"""
    print("  [1/9] 中轴大台基...")
    b.fill(49, Y0, 62, 67, Y0, 89, BASE)


# ══════════════════════════════════════════════════════════
# 2. 入口门厅 (51~65, 85~89) — 歇山顶
# ══════════════════════════════════════════════════════════

def _build_gate_hall(b: MinecraftBuilder):
    """入口门厅：歇山顶，南北各5格门洞，正式入园的第一道仪门"""
    print("  [2/9] 入口门厅...")

    x1, x2 = 51, 65
    z1, z2 = 85, 89   # z1=北, z2=南
    cx = 58            # 中心
    pillar_h = 5

    # -- 地面铺装 --
    b.fill(x1, Y0, z1, x2, Y0, z2, FLOOR)

    # -- 柱子: 东西各一排, 间距4格 --
    pillar_xs = [52, 56, 60, 64]
    pillar_zs = [z1, z2]  # 南北两排

    for px in pillar_xs:
        for pz in pillar_zs:
            b.setblock(px, Y0, pz, BASE_COL)  # 柱础
            b.fill(px, Y0 + 1, pz, px, Y0 + pillar_h, pz, PILLAR)

    # -- 额枋 (梁) --
    beam_y = Y0 + pillar_h
    # 北梁
    b.fill(pillar_xs[0], beam_y, z1, pillar_xs[-1], beam_y, z1, BEAM)
    # 南梁
    b.fill(pillar_xs[0], beam_y, z2, pillar_xs[-1], beam_y, z2, BEAM)
    # 东西向连梁
    for px in pillar_xs:
        b.fill(px, beam_y, z1, px, beam_y, z2, BEAM)

    # -- 南北各5格门洞: cx-2 ~ cx+2 留空, 其余做半墙 --
    door_x1, door_x2 = cx - 2, cx + 2
    for pz in [z1, z2]:
        for x in range(x1, x2 + 1):
            if door_x1 <= x <= door_x2:
                continue  # 门洞
            if x in pillar_xs:
                continue  # 柱位
            # 半墙 2 格高
            b.setblock(x, Y0 + 1, pz, WALL_BASE)
            b.setblock(x, Y0 + 2, pz, WALL)

    # -- 歇山顶 --
    _build_hip_gable_roof(b, x1 - 1, x2 + 1, z1 - 1, z2 + 1, beam_y + 1)

    # -- 灯笼 --
    b.setblock(cx, beam_y - 1, z1, f'{LANTERN}[hanging=true]')
    b.setblock(cx, beam_y - 1, z2, f'{LANTERN}[hanging=true]')


def _build_hip_gable_roof(b: MinecraftBuilder, x1, x2, z1, z2, roof_y):
    """歇山顶: 下部庑殿(四面坡), 上部悬山(两端山花)

    脊线沿 X 轴(东西向), 坡面向南北下降。
    x1~x2: 檐口X范围(含出檐), z1~z2: 檐口Z范围(含出檐)
    roof_y: 檐口层Y
    """
    cx = (x1 + x2) // 2
    cz = (z1 + z2) // 2
    half_z = (z2 - z1) // 2  # 南北半跨

    # 层0(roof_y): 檐口 — 四面楼梯
    for x in range(x1 + 1, x2):
        b.setblock(x, roof_y, z1, f"{ROOF}[facing=south,half=bottom]")
        b.setblock(x, roof_y, z2, f"{ROOF}[facing=north,half=bottom]")
    for z in range(z1 + 1, z2):
        b.setblock(x1, roof_y, z, f"{ROOF}[facing=east,half=bottom]")
        b.setblock(x2, roof_y, z, f"{ROOF}[facing=west,half=bottom]")
    # 四角
    b.setblock(x1, roof_y, z1, f"{EAVE}[facing=south,half=bottom,shape=outer_right]")
    b.setblock(x2, roof_y, z1, f"{EAVE}[facing=south,half=bottom,shape=outer_left]")
    b.setblock(x1, roof_y, z2, f"{EAVE}[facing=north,half=bottom,shape=outer_left]")
    b.setblock(x2, roof_y, z2, f"{EAVE}[facing=north,half=bottom,shape=outer_right]")

    # 层1(roof_y+1): 缩进1格四面坡
    for x in range(x1 + 2, x2 - 1):
        b.setblock(x, roof_y + 1, z1 + 1, f"{ROOF}[facing=south,half=bottom]")
        b.setblock(x, roof_y + 1, z2 - 1, f"{ROOF}[facing=north,half=bottom]")
    for z in range(z1 + 2, z2 - 1):
        b.setblock(x1 + 1, roof_y + 1, z, f"{ROOF}[facing=east,half=bottom]")
        b.setblock(x2 - 1, roof_y + 1, z, f"{ROOF}[facing=west,half=bottom]")
    # 角
    b.setblock(x1 + 1, roof_y + 1, z1 + 1,
               f"{ROOF}[facing=south,half=bottom,shape=outer_right]")
    b.setblock(x2 - 1, roof_y + 1, z1 + 1,
               f"{ROOF}[facing=south,half=bottom,shape=outer_left]")
    b.setblock(x1 + 1, roof_y + 1, z2 - 1,
               f"{ROOF}[facing=north,half=bottom,shape=outer_left]")
    b.setblock(x2 - 1, roof_y + 1, z2 - 1,
               f"{ROOF}[facing=north,half=bottom,shape=outer_right]")
    # 内部填充
    if x1 + 2 <= x2 - 2 and z1 + 2 <= z2 - 2:
        b.fill(x1 + 2, roof_y + 1, z1 + 2, x2 - 2, roof_y + 1, z2 - 2, ROOF_BLOCK)

    # 层2(roof_y+2): 歇山转悬山 — 南北继续收, 东西做山花(垂直三角)
    # 南北坡继续
    for x in range(x1 + 2, x2 - 1):
        b.setblock(x, roof_y + 2, z1 + 2, f"{ROOF}[facing=south,half=bottom]")
        b.setblock(x, roof_y + 2, z2 - 2, f"{ROOF}[facing=north,half=bottom]")
    # 东西山花: 实心墙封住
    for z in range(z1 + 2, z2 - 1):
        b.setblock(x1 + 1, roof_y + 2, z, ROOF_BLOCK)
        b.setblock(x2 - 1, roof_y + 2, z, ROOF_BLOCK)
    # 内部填充
    if x1 + 2 <= x2 - 2 and z1 + 3 <= z2 - 3:
        b.fill(x1 + 2, roof_y + 2, z1 + 3, x2 - 2, roof_y + 2, z2 - 3, ROOF_BLOCK)

    # 层3(roof_y+3): 屋脊 — 半砖收顶
    for x in range(x1 + 1, x2):
        b.setblock(x, roof_y + 3, cz, f"{ROOF_SLAB}[type=bottom]")
    # 山花顶端
    b.setblock(x1 + 1, roof_y + 3, cz, ROOF_BLOCK)
    b.setblock(x2 - 1, roof_y + 3, cz, ROOF_BLOCK)


# ══════════════════════════════════════════════════════════
# 3. 影壁 (54~62, 82~84)
# ══════════════════════════════════════════════════════════

def _build_screen_wall(b: MinecraftBuilder):
    """影壁: 门厅北侧3格处, 遮挡视线, 漏窗装饰"""
    print("  [3/9] 影壁...")

    sx1, sx2 = 54, 62
    sz = 83  # 影壁Z中心线

    # 影壁主体 4格高
    for x in range(sx1, sx2 + 1):
        b.setblock(x, Y0 + 1, sz, WALL_BASE)
        b.setblock(x, Y0 + 2, sz, WALL)
        b.setblock(x, Y0 + 3, sz, WALL)
        b.setblock(x, Y0 + 4, sz, WALL_CAP)

    # 漏窗: y+3层中间段铁栏杆
    for x in range(sx1 + 1, sx2):
        b.setblock(x, Y0 + 3, sz, WINDOW)
    # y+2层间隔漏窗
    for x in range(sx1 + 1, sx2):
        if (x - sx1) % 2 == 0:
            b.setblock(x, Y0 + 2, sz, WINDOW)

    # 底座加宽(前后各1格出挑)
    for x in range(sx1, sx2 + 1):
        b.setblock(x, Y0, sz - 1, WALL_BASE)
        b.setblock(x, Y0, sz + 1, WALL_BASE)
        b.setblock(x, Y0 + 1, sz - 1, f"{BASE_SLAB}[type=top]")
        b.setblock(x, Y0 + 1, sz + 1, f"{BASE_SLAB}[type=top]")


# ══════════════════════════════════════════════════════════
# 4. 小庭深院 (51~65, 78~82) — 露天天井
# ══════════════════════════════════════════════════════════

def _build_courtyard(b: MinecraftBuilder):
    """小庭深院: 露天天井, 东西矮墙围合, 南北通透"""
    print("  [4/9] 小庭深院...")

    cx1, cx2 = 51, 65
    cz1, cz2 = 78, 82  # z1=北, z2=南

    # 地面铺装(棋盘格)
    for x in range(cx1, cx2 + 1):
        for z in range(cz1, cz2 + 1):
            blk = FLOOR if (x + z) % 2 == 0 else FLOOR_ALT
            b.setblock(x, Y0, z, blk)

    # 东西矮墙: 3格高(墙基+墙身+压瓦)
    # 【已修改】西墙(X=51)在Z=77~79留3格宽门洞，对准西廊中心线Z=78
    door_z1, door_z2 = 77, 79  # 门洞Z范围
    door_h = 3  # 门洞高度3格

    for z in range(cz1, cz2 + 1):
        for wx in [cx1, cx2]:
            # 西墙门洞：X=51, Z=77~79, 高度3格(Y0+1 ~ Y0+3)留空
            if wx == cx1 and door_z1 <= z <= door_z2:
                continue  # 跳过门洞位置，不建墙
            b.setblock(wx, Y0 + 1, z, WALL_BASE)
            b.setblock(wx, Y0 + 2, z, WALL)
            b.setblock(wx, Y0 + 3, z, WALL_CAP)

    # 东墙花窗(居中) — 西墙门洞处不放花窗了
    wz = (cz1 + cz2) // 2
    b.setblock(cx2, Y0 + 2, wz, f"{TRAPDOOR}[facing=west,half=bottom,open=true]")


# ══════════════════════════════════════════════════════════
# 5. 抄手游廊 (51~65, 72~78) — 小庭↔远香堂
# ══════════════════════════════════════════════════════════

def _build_cloister(b: MinecraftBuilder):
    """抄手游廊: 东西两侧有柱有顶的通廊, 中间露天

    南柱=小庭北柱(z=78复用), 北柱=远香堂南柱(z=72复用)
    """
    print("  [5/9] 抄手游廊...")

    gx1, gx2 = 51, 65
    gz1, gz2 = 72, 78  # z1=北(远香堂侧), z2=南(小庭侧)
    pillar_h = 4

    # 地面铺装
    b.fill(gx1, Y0, gz1, gx2, Y0, gz2, FLOOR_ALT)

    # 东西两侧廊道: 各宽3格
    for side_x, other_x in [(gx1, gx1 + 2), (gx2 - 2, gx2)]:
        # 柱子: 沿z每3格
        for pz in range(gz1, gz2 + 1, 3):
            # 外侧柱
            b.setblock(side_x, Y0, pz, BASE_COL)
            b.fill(side_x, Y0 + 1, pz, side_x, Y0 + pillar_h, pz, PILLAR)
            # 内侧柱
            b.setblock(other_x, Y0, pz, BASE_COL)
            b.fill(other_x, Y0 + 1, pz, other_x, Y0 + pillar_h, pz, PILLAR)

        # 横梁
        beam_y = Y0 + pillar_h
        for pz in range(gz1, gz2 + 1, 3):
            b.fill(side_x, beam_y, pz, other_x, beam_y, pz, BEAM)

        # 纵梁
        b.fill(side_x, beam_y, gz1, side_x, beam_y, gz2, BEAM)
        b.fill(other_x, beam_y, gz1, other_x, beam_y, gz2, BEAM)

        # 屋顶半砖
        roof_y = beam_y + 1
        b.fill(side_x, roof_y, gz1, other_x, roof_y, gz2,
               f"{ROOF_SLAB}[type=bottom]")

        # 栏杆(外侧柱间)
        for pz in range(gz1, gz2 + 1):
            is_pillar = (pz - gz1) % 3 == 0
            if not is_pillar:
                b.setblock(side_x, Y0 + 1, pz, RAIL)

    # 中间露天(不加顶), 铺碎石意境
    mid_x1 = gx1 + 3
    mid_x2 = gx2 - 3
    for x in range(mid_x1, mid_x2 + 1):
        for z in range(gz1, gz2 + 1):
            if (x + z) % 3 == 0:
                b.setblock(x, Y0, z, GRAVEL)


# ══════════════════════════════════════════════════════════
# 6. 远香堂 (49~67, 62~72) — 最大建筑, 歇山顶
# ══════════════════════════════════════════════════════════

def _build_yuan_xiang_hall(b: MinecraftBuilder):
    """远香堂: 19格宽, 歇山顶, 北面朝湖全开敞, 南面接游廊"""
    print("  [6/9] 远香堂...")

    hx1, hx2 = 49, 67
    hz1, hz2 = 62, 72  # z1=北(朝湖), z2=南(接游廊)
    cx = 58
    cz = 67
    pillar_h = 6

    # -- 台基(比地面高1格) --
    b.fill(hx1, Y0, hz1, hx2, Y0, hz2, BASE)
    b.fill(hx1 + 1, Y0 + 1, hz1 + 1, hx2 - 1, Y0 + 1, hz2 - 1, FLOOR)
    floor_y = Y0 + 1

    # 台基楼梯围边
    for x in range(hx1, hx2 + 1):
        b.setblock(x, Y0 + 1, hz1, f"{BASE_STEP}[facing=north,half=top]")
        b.setblock(x, Y0 + 1, hz2, f"{BASE_STEP}[facing=south,half=top]")
    for z in range(hz1, hz2 + 1):
        b.setblock(hx1, Y0 + 1, z, f"{BASE_STEP}[facing=west,half=top]")
        b.setblock(hx2, Y0 + 1, z, f"{BASE_STEP}[facing=east,half=top]")

    # 北面踏步(朝湖,5格宽)
    for x in range(cx - 2, cx + 3):
        b.setblock(x, Y0, hz1 - 1, f"{BASE_STEP}[facing=south,half=bottom]")
        b.setblock(x, Y0 + 1, hz1, f"{BASE_STEP}[facing=south,half=bottom]")

    # -- 柱子: 前后各一排, 间距4格 --
    pillar_xs = [51, 55, 58, 61, 65]
    front_z = hz1 + 1  # 北排(朝湖)
    back_z = hz2 - 1   # 南排
    beam_y = floor_y + pillar_h

    for px in pillar_xs:
        for pz in [front_z, back_z]:
            b.setblock(px, floor_y, pz, BASE_COL)
            b.fill(px, floor_y + 1, pz, px, floor_y + pillar_h, pz, PILLAR)

    # -- 额枋 --
    b.fill(pillar_xs[0], beam_y, front_z, pillar_xs[-1], beam_y, front_z, BEAM)
    b.fill(pillar_xs[0], beam_y, back_z, pillar_xs[-1], beam_y, back_z, BEAM)
    for px in pillar_xs:
        b.fill(px, beam_y, front_z, px, beam_y, back_z, BEAM)

    # -- 墙体: 东西南三面封墙, 北面全开敞 --
    wall_y_top = floor_y + pillar_h - 1

    # 西墙(x=hx1+1)
    for y in range(floor_y + 1, wall_y_top + 1):
        for z in range(front_z + 1, back_z):
            b.setblock(hx1 + 1, y, z, WALL)
    # 东墙(x=hx2-1)
    for y in range(floor_y + 1, wall_y_top + 1):
        for z in range(front_z + 1, back_z):
            b.setblock(hx2 - 1, y, z, WALL)
    # 南墙(z=back_z) — 中间留5格门洞
    for y in range(floor_y + 1, wall_y_top + 1):
        for x in range(pillar_xs[0] + 1, pillar_xs[-1]):
            if cx - 2 <= x <= cx + 2:
                continue  # 门洞
            if x in pillar_xs:
                continue
            if y <= floor_y + 2:
                b.setblock(x, y, back_z, WALL)
            else:
                b.setblock(x, y, back_z,
                           f'{TRAPDOOR}[facing=north,half=top,open=true]')

    # 北面完全开敞, 仅放美人靠栏杆
    for x in range(pillar_xs[0] + 1, pillar_xs[-1]):
        if x in pillar_xs:
            continue
        b.setblock(x, floor_y + 1, front_z, RAIL)

    # -- 歇山顶 --
    _build_hip_gable_roof(b, hx1 - 1, hx2 + 1, hz1 - 1, hz2 + 1, beam_y + 1)

    # -- 灯笼 --
    for px in [pillar_xs[1], pillar_xs[3]]:
        b.setblock(px, beam_y - 1, front_z, f'{LANTERN}[hanging=true]')
        b.setblock(px, beam_y - 1, back_z, f'{LANTERN}[hanging=true]')

    # 木地板
    b.fill(hx1 + 2, floor_y, front_z + 1, hx2 - 2, floor_y, back_z - 1, FLOOR_WOOD)


# ══════════════════════════════════════════════════════════
# 7. 中轴两侧花墙 x=49 和 x=67
# ══════════════════════════════════════════════════════════

def _build_side_flower_walls(b: MinecraftBuilder):
    """花墙: 沿中轴两侧x=49和x=67, 从远香堂到门厅通高围合"""
    print("  [7/9] 中轴花墙...")

    wall_z1, wall_z2 = 72, 85  # 远香堂南端到门厅北端
    wall_h = 4  # 墙高

    # 【修改】西墙(x=49)在Z=77~79留门洞给西廊道通行
    west_door_zs = {77, 78, 79}  # 西廊门洞位置

    for wx in [49, 67]:
        for z in range(wall_z1, wall_z2 + 1):
            # 西墙在门洞位置跳过
            if wx == 49 and z in west_door_zs:
                continue
            b.setblock(wx, Y0 + 1, z, WALL_BASE)
            b.setblock(wx, Y0 + 2, z, WALL)
            b.setblock(wx, Y0 + 3, z, WALL)
            b.setblock(wx, Y0 + 4, z, WALL_CAP)

        # 花窗: 每隔4格开一个（跳过门洞位置）
        for z in range(wall_z1 + 2, wall_z2, 4):
            if wx == 49 and z in west_door_zs:
                continue
            b.setblock(wx, Y0 + 3, z, WINDOW)
            b.setblock(wx, Y0 + 2, z, WINDOW)


# ══════════════════════════════════════════════════════════
# 8. 闺塾 (18~26, 75~81) — 独立小院
# ══════════════════════════════════════════════════════════

def _build_gui_shu(b: MinecraftBuilder):
    """闺塾: 小型书房院落, 东墙有门洞通西廊, 围墙小院"""
    print("  [8/9] 闺塾...")

    gx1, gx2 = 18, 26
    gz1, gz2 = 75, 81  # z1=北, z2=南
    cx = 22
    cz = 78
    pillar_h = 5

    # -- 台基 --
    b.fill(gx1, Y0, gz1, gx2, Y0, gz2, BASE)
    floor_y = Y0

    # -- 书房主体(20~26, 76~80): 东面开敞 --
    rx1, rx2 = 20, 26
    rz1, rz2 = 76, 80

    # 柱子
    pillar_pos = [(rx1, rz1), (rx2, rz1), (rx1, rz2), (rx2, rz2),
                  (rx1, cz), (rx2, cz)]
    beam_y = floor_y + pillar_h

    for px, pz in pillar_pos:
        b.setblock(px, floor_y, pz, BASE_COL)
        b.fill(px, floor_y + 1, pz, px, floor_y + pillar_h, pz, PILLAR)

    # 额枋
    b.fill(rx1, beam_y, rz1, rx2, beam_y, rz1, BEAM)
    b.fill(rx1, beam_y, rz2, rx2, beam_y, rz2, BEAM)
    b.fill(rx1, beam_y, rz1, rx1, beam_y, rz2, BEAM)
    b.fill(rx2, beam_y, rz1, rx2, beam_y, rz2, BEAM)

    # 【已修改】西墙+北墙+南墙+东墙(白墙)，东墙(X=26)在Z=77~79留3格宽×3格高门洞
    east_door_z1, east_door_z2 = 77, 79  # 东墙门洞Z范围，对准西廊中心线Z=78
    east_door_h = 3  # 门洞高度3格
    for y in range(floor_y + 1, beam_y):
        # 西墙
        for z in range(rz1 + 1, rz2):
            b.setblock(rx1, y, z, WALL)
        # 北墙
        for x in range(rx1 + 1, rx2):
            b.setblock(x, y, rz1, WALL)
        # 南墙（全封闭，不留门——闺塾只从东面西廊进入）
        for x in range(rx1 + 1, rx2):
            b.setblock(x, y, rz2, WALL)
        # 东墙(X=rx2=26)：Z=77~79处留3格宽×3格高门洞
        for z in range(rz1 + 1, rz2):
            if east_door_z1 <= z <= east_door_z2 and y <= floor_y + east_door_h:
                continue  # 门洞
            b.setblock(rx2, y, z, WALL)

    # 北墙花窗
    for x in range(rx1 + 2, rx2 - 1):
        b.setblock(x, floor_y + 3, rz1,
                   f'{TRAPDOOR}[facing=south,half=top,open=true]')
        b.setblock(x, floor_y + 4, rz1,
                   f'{TRAPDOOR}[facing=south,half=top,open=true]')

    # 悬山顶【已修改】改为脊线沿Z轴(南北向)，坡面向东西倾斜，加飞檐
    _build_gable_roof(b, rx1 - 1, rx2 + 1, rz1 - 1, rz2 + 1, beam_y + 1,
                      axis='z')

    # 院子围墙(gx1~rx1, gz1~gz2)
    for z in range(gz1, gz2 + 1):
        b.setblock(gx1, floor_y + 1, z, WALL_BASE)
        b.setblock(gx1, floor_y + 2, z, WALL)
        b.setblock(gx1, floor_y + 3, z, WALL_CAP)

    # 灯笼
    b.setblock(cx, beam_y - 1, cz, f'{LANTERN}[hanging=true]')

    # 木地板
    b.fill(rx1 + 1, floor_y, rz1 + 1, rx2 - 1, floor_y, rz2 - 1, FLOOR_WOOD)

    # 【新增】闺塾内饰 — 书房氛围
    fy1 = floor_y + 1  # 家具放置层
    # 床（西墙边，红色）
    b.setblock(rx1 + 1, fy1, cz, "minecraft:red_bed[facing=east,part=foot]")
    b.setblock(rx1 + 1, fy1, cz - 1, "minecraft:red_bed[facing=east,part=head]")
    # 书架（北墙边）
    b.setblock(cx, fy1, rz1 + 1, "minecraft:bookshelf")
    b.setblock(cx + 1, fy1, rz1 + 1, "minecraft:bookshelf")
    b.setblock(cx, fy1 + 1, rz1 + 1, "minecraft:bookshelf")
    b.setblock(cx + 1, fy1 + 1, rz1 + 1, "minecraft:bookshelf")
    # 讲台（书架前）
    b.setblock(cx, fy1, rz1 + 2, "minecraft:lectern[facing=south]")
    # 花盆（窗边）
    b.setblock(rx1 + 1, fy1, rz1 + 1, "minecraft:flower_pot")
    # 红地毯（中央）
    b.setblock(cx, floor_y, cz, "minecraft:red_carpet")
    b.setblock(cx + 1, floor_y, cz, "minecraft:red_carpet")
    b.setblock(cx - 1, floor_y, cz, "minecraft:red_carpet")


def _build_gable_roof(b: MinecraftBuilder, x1, x2, z1, z2, roof_y,
                      axis='x'):
    """悬山顶: 两面坡屋顶

    axis='x': 脊线沿X轴(东西向), 坡面向南北 (原逻辑)
    axis='z': 脊线沿Z轴(南北向), 坡面向东西 (闺塾用)

    【已修改】支持两个方向，加飞檐(dark_oak_stairs外层包裹)，脊线用stone_brick_slab
    """
    cx = (x1 + x2) // 2
    cz = (z1 + z2) // 2

    if axis == 'x':
        # ---- 原逻辑：脊线沿X轴，坡面南北 ----
        half_z = (z2 - z1) // 2

        layers = []
        cur_z_off = 0
        y_off = 0
        while cur_z_off < half_z:
            layers.append((y_off, cz - half_z + cur_z_off, cz + half_z - cur_z_off))
            cur_z_off += 1
            y_off += 1

        for dy, south_z, north_z in layers:
            y = roof_y + dy
            for x in range(x1, x2 + 1):
                b.setblock(x, y, north_z, f"{ROOF}[facing=south,half=bottom]")
            for x in range(x1, x2 + 1):
                b.setblock(x, y, south_z, f"{ROOF}[facing=north,half=bottom]")
            if south_z - 1 >= north_z + 1:
                b.fill(x1, y, north_z + 1, x2, y, south_z - 1, ROOF_BLOCK)

        ridge_y = roof_y + y_off
        for x in range(x1, x2 + 1):
            b.setblock(x, ridge_y, cz, f"{ROOF_SLAB}[type=bottom]")

    else:
        # ---- 新逻辑：脊线沿Z轴(南北向)，坡面向东西倾斜 ----
        half_x = (x2 - x1) // 2

        # 飞檐层(roof_y - 1)：dark_oak_stairs 在最外层包裹
        eave_y = roof_y
        # 东西飞檐
        for z in range(z1, z2 + 1):
            b.setblock(x1, eave_y, z, f"{EAVE}[facing=east,half=bottom]")
            b.setblock(x2, eave_y, z, f"{EAVE}[facing=west,half=bottom]")
        # 南北飞檐
        for x in range(x1 + 1, x2):
            b.setblock(x, eave_y, z1, f"{EAVE}[facing=south,half=bottom]")
            b.setblock(x, eave_y, z2, f"{EAVE}[facing=north,half=bottom]")
        # 四角飞檐
        b.setblock(x1, eave_y, z1, f"{EAVE}[facing=south,half=bottom,shape=outer_right]")
        b.setblock(x2, eave_y, z1, f"{EAVE}[facing=south,half=bottom,shape=outer_left]")
        b.setblock(x1, eave_y, z2, f"{EAVE}[facing=north,half=bottom,shape=outer_left]")
        b.setblock(x2, eave_y, z2, f"{EAVE}[facing=north,half=bottom,shape=outer_right]")

        # 主屋顶：从飞檐内侧开始逐层收缩
        layers = []
        cur_x_off = 0
        y_off = 0
        inner_x1 = x1 + 1  # 飞檐内侧
        inner_x2 = x2 - 1
        inner_half_x = (inner_x2 - inner_x1) // 2
        inner_cx = (inner_x1 + inner_x2) // 2

        while cur_x_off < inner_half_x:
            west_x = inner_cx - inner_half_x + cur_x_off
            east_x = inner_cx + inner_half_x - cur_x_off
            layers.append((y_off, west_x, east_x))
            cur_x_off += 1
            y_off += 1

        for dy, west_x, east_x in layers:
            y = roof_y + 1 + dy  # 从飞檐上一层开始
            # 西坡
            for z in range(z1, z2 + 1):
                b.setblock(west_x, y, z, f"{ROOF}[facing=east,half=bottom]")
            # 东坡
            for z in range(z1, z2 + 1):
                b.setblock(east_x, y, z, f"{ROOF}[facing=west,half=bottom]")
            # 中间填充
            if east_x - 1 >= west_x + 1:
                b.fill(west_x + 1, y, z1, east_x - 1, y, z2, ROOF_BLOCK)

        # 屋脊(最高层)：脊线沿Z轴，用stone_brick_slab
        ridge_y = roof_y + 1 + y_off
        for z in range(z1, z2 + 1):
            b.setblock(inner_cx, ridge_y, z, f"{ROOF_SLAB}[type=bottom]")


# ══════════════════════════════════════════════════════════
# 9. 闺塾→小庭 西廊道 z=78, x=26→51
# ══════════════════════════════════════════════════════════

def _build_west_corridor(b: MinecraftBuilder):
    """西廊道: 从闺塾东端到小庭西墙, 沿z=78, 有柱有顶
    【已修改】廊道加宽为5格：柱Z=76和Z=80，走道Z=77~79（3格宽），屋顶Z=76~80
    """
    print("  [9/9] 闺塾→小庭 西廊道...")

    lz = 78  # 廊道中心Z
    lx1, lx2 = 26, 51  # 从闺塾东端到小庭西墙
    pillar_h = 4
    pillar_space = 3

    # 柱子Z坐标（走道外侧各1格）
    pz_north = 76  # 北侧柱
    pz_south = 80  # 南侧柱
    # 走道Z范围: 77~79（3格宽）

    # 地面：整个5格宽铺地
    b.fill(lx1, Y0, pz_north, lx2, Y0, pz_south, FLOOR_ALT)
    # 走道中心线用主地板
    b.fill(lx1, Y0, lz, lx2, Y0, lz, FLOOR)

    # 柱子+梁+顶
    beam_y = Y0 + pillar_h
    roof_y = beam_y + 1

    for x in range(lx1, lx2 + 1, pillar_space):
        # 南北两侧柱（在走道外侧 Z=76 和 Z=80）
        for pz in [pz_north, pz_south]:
            b.setblock(x, Y0, pz, BASE_COL)
            b.fill(x, Y0 + 1, pz, x, Y0 + pillar_h, pz, PILLAR)
        # 横梁（跨越整个5格宽）
        b.fill(x, beam_y, pz_north, x, beam_y, pz_south, BEAM)

    # 纵梁（沿柱线）
    b.fill(lx1, beam_y, pz_north, lx2, beam_y, pz_north, BEAM)
    b.fill(lx1, beam_y, pz_south, lx2, beam_y, pz_south, BEAM)

    # 屋顶半砖：覆盖 Z=76~80
    b.fill(lx1, roof_y, pz_north, lx2, roof_y, pz_south,
           f"{ROOF_SLAB}[type=bottom]")

    # 栏杆(柱间，放在柱线上)
    for x in range(lx1, lx2 + 1):
        is_pillar = (x - lx1) % pillar_space == 0
        if not is_pillar:
            b.setblock(x, Y0 + 1, pz_north, RAIL)
            b.setblock(x, Y0 + 1, pz_south, RAIL)

    # 灯笼(每6格一盏)
    for x in range(lx1 + 3, lx2, 6):
        b.setblock(x, beam_y - 1, lz, f'{LANTERN}[hanging=true]')


# ══════════════════════════════════════════════════════════
# 主入口
# ══════════════════════════════════════════════════════════

def build_cluster_d(b: MinecraftBuilder):
    """D群：南部中轴 — 入口仪式序列"""
    print("=== D群：南部中轴群 ===")

    _build_central_platform(b)
    _build_gate_hall(b)
    _build_screen_wall(b)
    _build_courtyard(b)
    _build_cloister(b)
    _build_yuan_xiang_hall(b)
    _build_side_flower_walls(b)
    _build_gui_shu(b)
    _build_west_corridor(b)

    # 注册边界框
    b.register_bbox("cluster_d_main", 49, GROUND_Y, 62, 67, Y0 + 16, 89)
    b.register_bbox("cluster_d_guishu", 18, GROUND_Y, 75, 26, Y0 + 10, 81)
    b.register_bbox("cluster_d_corridor", 26, GROUND_Y, 76, 51, Y0 + 6, 80)

    print(f"  D群建造完成!")


if __name__ == "__main__":
    with MinecraftBuilder() as b:
        build_cluster_d(b)
        print(f"Done! {b.cmd_count} commands")
