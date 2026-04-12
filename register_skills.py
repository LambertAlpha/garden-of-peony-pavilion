"""预置技能注册 -- 从现有建筑代码中提取可复用的建筑函数

从 phase3_buildings.py, landscape.py, structures/ 等文件提取
10 个核心建筑模式，注册到 SkillLibrary。

用法:
    python register_skills.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from core.skill_library import SkillLibrary


# ═══════════════════════════════════════════════════════════
#  屋顶技能
# ═══════════════════════════════════════════════════════════

def register_roof_skills(lib: SkillLibrary):
    """注册屋顶相关技能"""

    # ── 1. 攒尖顶 ──
    lib.add_skill(
        name="roof_hip_pointed",
        code='''
def build_roof_hip_pointed(b, x1, z1, x2, z2, base_y,
                           roof_stair="minecraft:stone_brick_stairs",
                           roof_block="minecraft:stone_bricks",
                           eave_stair="minecraft:dark_oak_stairs",
                           eave_slab="minecraft:dark_oak_slab",
                           rod="minecraft:lightning_rod"):
    """攒尖顶 — 四面等坡收尖，顶部加宝顶。
    适用于亭子、角楼等正方形/近正方形建筑。

    Parameters:
        b        : MinecraftBuilder 实例
        x1,z1    : 柱间范围左上角
        x2,z2    : 柱间范围右下角
        base_y   : 屋顶起始Y（梁顶上方一层）
        roof_stair : 屋顶楼梯方块
        roof_block : 屋顶实心方块
        eave_stair : 飞檐楼梯方块
        eave_slab  : 飞檐半砖方块
        rod        : 宝顶方块
    """
    cx = (x1 + x2) // 2
    cz = (z1 + z2) // 2
    layer = 0
    cx1, cz1, cx2, cz2 = x1 - 1, z1 - 1, x2 + 1, z2 + 1  # 出檐1格
    y = base_y

    while cx1 <= cx2 and cz1 <= cz2:
        if cx1 == cx2 and cz1 == cz2:
            b.setblock(cx1, y, cz1, roof_block)
            b.setblock(cx1, y + 1, cz1, rod)  # 宝顶
            break
        elif cx1 == cx2:
            b.fill(cx1, y, cz1, cx1, y, cz2, roof_block)
            y += 1; cz1 += 1; cz2 -= 1; continue
        elif cz1 == cz2:
            b.fill(cx1, y, cz1, cx2, y, cz1, roof_block)
            y += 1; cx1 += 1; cx2 -= 1; continue

        # 四面楼梯
        b.fill(cx1 + 1, y, cz1, cx2 - 1, y, cz1,
               f"{roof_stair}[facing=south,half=bottom]")
        b.fill(cx1 + 1, y, cz2, cx2 - 1, y, cz2,
               f"{roof_stair}[facing=north,half=bottom]")
        b.fill(cx1, y, cz1 + 1, cx1, y, cz2 - 1,
               f"{roof_stair}[facing=east,half=bottom]")
        b.fill(cx2, y, cz1 + 1, cx2, y, cz2 - 1,
               f"{roof_stair}[facing=west,half=bottom]")
        # 四角实心
        for corner_x, corner_z in [(cx1, cz1), (cx1, cz2),
                                    (cx2, cz1), (cx2, cz2)]:
            b.setblock(corner_x, y, corner_z, roof_block)

        cx1 += 1; cz1 += 1; cx2 -= 1; cz2 -= 1
        y += 1; layer += 1
        if layer > 12:
            break

    # 飞檐翘角
    eave_y = base_y - 1
    ox1, oz1 = x1 - 2, z1 - 2
    ox2, oz2 = x2 + 2, z2 + 2
    b.fill(ox1 + 1, eave_y, oz1, ox2 - 1, eave_y, oz1,
           f"{eave_stair}[facing=south,half=top]")
    b.fill(ox1 + 1, eave_y, oz2, ox2 - 1, eave_y, oz2,
           f"{eave_stair}[facing=north,half=top]")
    b.fill(ox1, eave_y, oz1 + 1, ox1, eave_y, oz2 - 1,
           f"{eave_stair}[facing=east,half=top]")
    b.fill(ox2, eave_y, oz1 + 1, ox2, eave_y, oz2 - 1,
           f"{eave_stair}[facing=west,half=top]")
    for ccx, ccz in [(ox1, oz1), (ox1, oz2), (ox2, oz1), (ox2, oz2)]:
        b.setblock(ccx, eave_y, ccz, eave_slab)
''',
        description="攒尖顶屋顶，四面楼梯逐层等坡收尖至宝顶，含飞檐翘角。"
                    "适用于亭子、角楼等正方形建筑。"
                    "来源: phase3_buildings._build_roof_hip_pointed",
        tags=["屋顶", "攒尖", "亭子", "角楼", "roof", "pavilion", "pyramidal"],
    )

    # ── 2. 歇山顶 ──
    lib.add_skill(
        name="roof_hip",
        code='''
def build_roof_hip(b, x1, z1, x2, z2, base_y,
                   roof_stair="minecraft:stone_brick_stairs",
                   roof_slab="minecraft:stone_brick_slab",
                   roof_block="minecraft:stone_bricks",
                   eave_stair="minecraft:dark_oak_stairs",
                   eave_slab="minecraft:dark_oak_slab"):
    """歇山顶 — 四面坡逐层收缩，顶部半砖封顶，含飞檐翘角。
    适用于厅堂、殿宇等矩形建筑。

    Parameters:
        b        : MinecraftBuilder 实例
        x1,z1    : 柱间范围左上角
        x2,z2    : 柱间范围右下角
        base_y   : 屋顶起始Y
    """
    layer = 0
    cx1, cz1, cx2, cz2 = x1 - 1, z1 - 1, x2 + 1, z2 + 1  # 出檐1格
    y = base_y

    while cx1 < cx2 and cz1 < cz2:
        # 四面楼梯
        if cx2 - cx1 >= 2:
            b.fill(cx1 + 1, y, cz1, cx2 - 1, y, cz1,
                   f"{roof_stair}[facing=south,half=bottom]")
            b.fill(cx1 + 1, y, cz2, cx2 - 1, y, cz2,
                   f"{roof_stair}[facing=north,half=bottom]")
        if cz2 - cz1 >= 2:
            b.fill(cx1, y, cz1 + 1, cx1, y, cz2 - 1,
                   f"{roof_stair}[facing=east,half=bottom]")
            b.fill(cx2, y, cz1 + 1, cx2, y, cz2 - 1,
                   f"{roof_stair}[facing=west,half=bottom]")
        # 四角实心
        for corner_x, corner_z in [(cx1, cz1), (cx1, cz2),
                                    (cx2, cz1), (cx2, cz2)]:
            b.setblock(corner_x, y, corner_z, roof_block)

        cx1 += 1; cz1 += 1; cx2 -= 1; cz2 -= 1
        y += 1; layer += 1
        if layer > 10:
            break

    # 顶部封口
    if cx1 <= cx2 and cz1 <= cz2:
        b.fill(cx1, y, cz1, cx2, y, cz2,
               f"{roof_slab}[type=bottom]")
    elif cx1 - 1 <= cx2 + 1:
        b.setblock((cx1 + cx2) // 2, y, (cz1 + cz2) // 2,
                   f"{roof_slab}[type=bottom]")

    # 飞檐翘角
    eave_y = base_y - 1
    ox1, oz1 = x1 - 2, z1 - 2
    ox2, oz2 = x2 + 2, z2 + 2
    b.fill(ox1 + 1, eave_y, oz1, ox2 - 1, eave_y, oz1,
           f"{eave_stair}[facing=south,half=top]")
    b.fill(ox1 + 1, eave_y, oz2, ox2 - 1, eave_y, oz2,
           f"{eave_stair}[facing=north,half=top]")
    b.fill(ox1, eave_y, oz1 + 1, ox1, eave_y, oz2 - 1,
           f"{eave_stair}[facing=east,half=top]")
    b.fill(ox2, eave_y, oz1 + 1, ox2, eave_y, oz2 - 1,
           f"{eave_stair}[facing=west,half=top]")
    for ccx, ccz in [(ox1, oz1), (ox1, oz2), (ox2, oz1), (ox2, oz2)]:
        b.setblock(ccx, eave_y, ccz, eave_slab)
''',
        description="歇山顶（庑殿顶），四面坡逐层收缩至半砖封顶，含飞檐翘角。"
                    "适用于厅堂、殿宇等矩形建筑。"
                    "来源: phase3_buildings._build_roof_hip",
        tags=["屋顶", "歇山", "庑殿", "厅堂", "roof", "hip", "hall"],
    )

    # ── 3. 悬山顶 ──
    lib.add_skill(
        name="roof_gable",
        code='''
def build_roof_gable(b, x1, z1, x2, z2, base_y, ridge_axis="x",
                     roof_stair="minecraft:stone_brick_stairs",
                     roof_slab="minecraft:stone_brick_slab",
                     roof_block="minecraft:stone_bricks",
                     wall_block="minecraft:white_concrete",
                     eave_stair="minecraft:dark_oak_stairs"):
    """悬山顶 — 两面坡+两侧山墙三角，含飞檐。
    适用于轩、斋、廊亭等长条建筑。

    Parameters:
        b          : MinecraftBuilder 实例
        x1,z1      : 柱间范围左上角
        x2,z2      : 柱间范围右下角
        base_y     : 屋顶起始Y
        ridge_axis : "x" 屋脊沿X方向(南北两坡), "z" 屋脊沿Z方向(东西两坡)
    """
    if ridge_axis == "x":
        cz = (z1 + z2) // 2
        half_span = cz - z1 + 1
        y = base_y
        ox1, ox2 = x1 - 1, x2 + 1

        for layer in range(half_span + 1):
            nz = z1 - 1 + layer
            sz = z2 + 1 - layer
            if nz > cz:
                break
            if nz == sz:
                b.fill(ox1, y, nz, ox2, y, nz,
                       f"{roof_slab}[type=bottom]")
            else:
                if nz == cz or sz == cz:
                    if nz <= cz:
                        b.fill(ox1, y, nz, ox2, y, nz, roof_block)
                    if sz >= cz:
                        b.fill(ox1, y, sz, ox2, y, sz, roof_block)
                else:
                    b.fill(ox1, y, nz, ox2, y, nz,
                           f"{roof_stair}[facing=south,half=bottom]")
                    b.fill(ox1, y, sz, ox2, y, sz,
                           f"{roof_stair}[facing=north,half=bottom]")
            y += 1

        # 两侧山墙三角
        for wall_x in [x1, x2]:
            for dy in range(half_span):
                inner_z1 = z1 + dy
                inner_z2 = z2 - dy
                if inner_z1 < inner_z2:
                    b.fill(wall_x, base_y + dy, inner_z1,
                           wall_x, base_y + dy, inner_z2, wall_block)

        # 飞檐
        eave_y = base_y - 1
        b.fill(ox1, eave_y, z1 - 2, ox2, eave_y, z1 - 2,
               f"{eave_stair}[facing=south,half=top]")
        b.fill(ox1, eave_y, z2 + 2, ox2, eave_y, z2 + 2,
               f"{eave_stair}[facing=north,half=top]")

    else:  # ridge_axis == "z"
        cx_mid = (x1 + x2) // 2
        half_span = cx_mid - x1 + 1
        y = base_y
        oz1, oz2 = z1 - 1, z2 + 1

        for layer in range(half_span + 1):
            wx = x1 - 1 + layer
            ex = x2 + 1 - layer
            if wx > cx_mid:
                break
            if wx == ex:
                b.fill(wx, y, oz1, wx, y, oz2,
                       f"{roof_slab}[type=bottom]")
            else:
                if wx == cx_mid or ex == cx_mid:
                    if wx <= cx_mid:
                        b.fill(wx, y, oz1, wx, y, oz2, roof_block)
                    if ex >= cx_mid:
                        b.fill(ex, y, oz1, ex, y, oz2, roof_block)
                else:
                    b.fill(wx, y, oz1, wx, y, oz2,
                           f"{roof_stair}[facing=east,half=bottom]")
                    b.fill(ex, y, oz1, ex, y, oz2,
                           f"{roof_stair}[facing=west,half=bottom]")
            y += 1

        # 山墙三角
        for wall_z in [z1, z2]:
            for dy in range(half_span):
                inner_x1 = x1 + dy
                inner_x2 = x2 - dy
                if inner_x1 < inner_x2:
                    b.fill(inner_x1, base_y + dy, wall_z,
                           inner_x2, base_y + dy, wall_z, wall_block)

        # 飞檐
        eave_y = base_y - 1
        b.fill(x1 - 2, eave_y, oz1, x1 - 2, eave_y, oz2,
               f"{eave_stair}[facing=east,half=top]")
        b.fill(x2 + 2, eave_y, oz1, x2 + 2, eave_y, oz2,
               f"{eave_stair}[facing=west,half=top]")
''',
        description="悬山顶，两面坡+山墙三角填充，含飞檐。支持X/Z两个屋脊方向。"
                    "适用于轩、斋、廊亭等长条形建筑。"
                    "来源: phase3_buildings._build_roof_gable",
        tags=["屋顶", "悬山", "两坡", "轩", "斋", "roof", "gable"],
    )


# ═══════════════════════════════════════════════════════════
#  结构技能
# ═══════════════════════════════════════════════════════════

def register_structure_skills(lib: SkillLibrary):
    """注册结构相关技能"""

    # ── 4. 须弥座台基 ──
    lib.add_skill(
        name="platform_sumeru",
        code='''
def build_platform_sumeru(b, cx, cz, base_y, r_base=5,
                          base_block="minecraft:stone_bricks",
                          base_step="minecraft:stone_brick_stairs",
                          base_slab="minecraft:stone_brick_slab",
                          base_col="minecraft:polished_andesite"):
    """须弥座台基 — 底层石砖实铺 + 上层楼梯围边半砖台面 + 四面踏步 + 散水带。
    适用于亭台、殿宇等重要建筑的基座。

    Parameters:
        b        : MinecraftBuilder 实例
        cx, cz   : 台基中心坐标
        base_y   : 台基底面Y坐标（地面标高）
        r_base   : 台基半径（中心到边缘距离），总宽 2*r_base+1
    """
    # 散水带 (外围1格)
    b.fill(cx - r_base - 1, base_y, cz - r_base - 1,
           cx + r_base + 1, base_y, cz + r_base + 1, base_col)

    # 底层: stone_bricks 全铺
    b.fill(cx - r_base, base_y + 1, cz - r_base,
           cx + r_base, base_y + 1, cz + r_base, base_block)

    # 上层: 楼梯围边 + 中间半砖
    b.fill(cx - r_base + 1, base_y + 2, cz - r_base + 1,
           cx + r_base - 1, base_y + 2, cz + r_base - 1,
           f"{base_slab}[type=top]")

    # 四面楼梯围边（朝外）
    for x in range(cx - r_base, cx + r_base + 1):
        b.setblock(x, base_y + 2, cz - r_base,
                   f"{base_step}[facing=north,half=top]")
        b.setblock(x, base_y + 2, cz + r_base,
                   f"{base_step}[facing=south,half=top]")
    for z in range(cz - r_base, cz + r_base + 1):
        b.setblock(cx - r_base, base_y + 2, z,
                   f"{base_step}[facing=west,half=top]")
        b.setblock(cx + r_base, base_y + 2, z,
                   f"{base_step}[facing=east,half=top]")

    # 四面踏步（每面中间3格, 2级）
    for x in range(cx - 1, cx + 2):
        b.setblock(x, base_y + 1, cz - r_base - 1,
                   f"{base_step}[facing=south,half=bottom]")
        b.setblock(x, base_y + 2, cz - r_base,
                   f"{base_step}[facing=south,half=bottom]")
        b.setblock(x, base_y + 1, cz + r_base + 1,
                   f"{base_step}[facing=north,half=bottom]")
        b.setblock(x, base_y + 2, cz + r_base,
                   f"{base_step}[facing=north,half=bottom]")
    for z in range(cz - 1, cz + 2):
        b.setblock(cx - r_base - 1, base_y + 1, z,
                   f"{base_step}[facing=east,half=bottom]")
        b.setblock(cx - r_base, base_y + 2, z,
                   f"{base_step}[facing=east,half=bottom]")
        b.setblock(cx + r_base + 1, base_y + 1, z,
                   f"{base_step}[facing=west,half=bottom]")
        b.setblock(cx + r_base, base_y + 2, z,
                   f"{base_step}[facing=west,half=bottom]")

    return base_y + 2  # 返回台面Y坐标
''',
        description="须弥座台基，底层石砖+上层楼梯围边半砖+四面踏步+散水带。"
                    "适用于亭台殿宇的基座。返回台面Y坐标。"
                    "来源: structures/pavilion.py 台基段",
        tags=["台基", "须弥座", "基座", "platform", "sumeru", "base"],
    )

    # ── 5. 飞檐翘角 ──
    lib.add_skill(
        name="eaves_upturned",
        code='''
def build_eaves_upturned(b, x1, z1, x2, z2, eave_y,
                         eave_stair="minecraft:dark_oak_stairs",
                         eave_slab="minecraft:dark_oak_slab"):
    """飞檐翘角 — 四面倒置楼梯飞檐 + 四角半砖翘角。
    可独立使用，也可叠加在任何屋顶下方。

    Parameters:
        b        : MinecraftBuilder 实例
        x1,z1    : 飞檐内圈左上角（通常=柱间范围）
        x2,z2    : 飞檐内圈右下角
        eave_y   : 飞檐Y坐标（通常=屋顶base_y - 1）
    """
    # 飞檐在柱间范围外扩2格
    ox1, oz1 = x1 - 2, z1 - 2
    ox2, oz2 = x2 + 2, z2 + 2

    # 四面倒置楼梯
    b.fill(ox1 + 1, eave_y, oz1, ox2 - 1, eave_y, oz1,
           f"{eave_stair}[facing=south,half=top]")
    b.fill(ox1 + 1, eave_y, oz2, ox2 - 1, eave_y, oz2,
           f"{eave_stair}[facing=north,half=top]")
    b.fill(ox1, eave_y, oz1 + 1, ox1, eave_y, oz2 - 1,
           f"{eave_stair}[facing=east,half=top]")
    b.fill(ox2, eave_y, oz1 + 1, ox2, eave_y, oz2 - 1,
           f"{eave_stair}[facing=west,half=top]")

    # 四角翘角半砖
    for ccx, ccz in [(ox1, oz1), (ox1, oz2), (ox2, oz1), (ox2, oz2)]:
        b.setblock(ccx, eave_y, ccz, eave_slab)
''',
        description="飞檐翘角，四面倒置楼梯+四角半砖翘角。"
                    "可独立叠加在任何屋顶下方，外扩2格。"
                    "来源: phase3_buildings 屋顶函数中的飞檐段",
        tags=["飞檐", "翘角", "檐口", "eave", "upturned", "角"],
    )

    # ── 6. 围合院落 ──
    lib.add_skill(
        name="courtyard_enclosed",
        code='''
def build_courtyard_enclosed(b, x1, z1, x2, z2, y0, gate_cx=None,
                             gate_width=3, gate_face="south",
                             wall_block="minecraft:white_concrete",
                             wall_base="minecraft:stone_bricks",
                             wall_cap="minecraft:stone_brick_slab",
                             floor_block="minecraft:stone_bricks",
                             trapdoor="minecraft:jungle_trapdoor"):
    """围合院落/天井 — 矮墙围合(3格高) + 地面铺装 + 花窗 + 门洞。
    适用于入口庭院、天井、小院等。

    Parameters:
        b             : MinecraftBuilder 实例
        x1,z1,x2,z2  : 院落矩形范围
        y0            : 地面Y坐标
        gate_cx       : 门洞中心X (默认取中点)
        gate_width    : 门洞宽度 (默认3)
        gate_face     : 门洞朝向 "north"/"south"/"east"/"west"
    """
    if gate_cx is None:
        gate_cx = (x1 + x2) // 2

    # 地面铺装
    b.fill(x1, y0, z1, x2, y0, z2, floor_block)

    # 四面矮墙: 墙基(1) + 白墙(1) + 压瓦(1)
    for x in range(x1, x2 + 1):
        for z in [z1, z2]:
            # 门洞跳过
            if ((gate_face == "north" and z == z1) or
                (gate_face == "south" and z == z2)):
                half_w = gate_width // 2
                if abs(x - gate_cx) <= half_w:
                    continue
            b.setblock(x, y0 + 1, z, wall_base)
            b.setblock(x, y0 + 2, z, wall_block)
            b.setblock(x, y0 + 3, z, f"{wall_cap}[type=bottom]")

    for z in range(z1, z2 + 1):
        for x in [x1, x2]:
            if ((gate_face == "west" and x == x1) or
                (gate_face == "east" and x == x2)):
                half_w = gate_width // 2
                gate_cz = (z1 + z2) // 2
                if abs(z - gate_cz) <= half_w:
                    continue
            b.setblock(x, y0 + 1, z, wall_base)
            b.setblock(x, y0 + 2, z, wall_block)
            b.setblock(x, y0 + 3, z, f"{wall_cap}[type=bottom]")

    # 花窗 — 东西墙各一个 (打开的活板门)
    window_y = y0 + 2
    mid_z = (z1 + z2) // 2
    b.setblock(x1, window_y, mid_z,
               f"{trapdoor}[facing=east,half=bottom,open=true]")
    b.setblock(x2, window_y, mid_z,
               f"{trapdoor}[facing=west,half=bottom,open=true]")
''',
        description="围合院落/天井，矮墙围合+地面铺装+花窗+门洞。"
                    "适用于入口庭院、天井、小院。可指定门洞朝向和宽度。"
                    "来源: structures/gate.py _build_courtyard + rebuild_entrance.py 天井段",
        tags=["院落", "天井", "庭院", "围合", "courtyard", "enclosure", "院墙"],
    )

    # ── 7. 月洞门 ──
    lib.add_skill(
        name="moon_gate",
        code='''
def build_moon_gate(b, wall_x, center_z, radius, plane="yz",
                    air="minecraft:air",
                    frame_block="minecraft:stone_bricks"):
    """月洞门 — 在墙面上凿圆形洞口 + 石砖描边。
    适用于园墙、花墙的通道开洞。

    Parameters:
        b          : MinecraftBuilder 实例
        wall_x     : 墙面的固定坐标 (YZ平面时为X, XY平面时为Z)
        center_z   : 圆心的可变轴坐标 (YZ平面时为Z, XY平面时为X)
        radius     : 洞口半径
        plane      : "yz" (东西向通行) 或 "xy" (南北向通行)
        frame_block: 圆框描边方块
    """
    from core.builder import filled_circle_points

    build_y = -60  # 默认地面Y

    if plane == "yz":
        # YZ平面圆: 圆心Y=build_y+radius, 圆心Z=center_z
        cy = build_y + radius
        cz = center_z
        # 清空圆内
        for dy, dz in filled_circle_points(cy, cz, radius):
            b.setblock(wall_x, dy, dz, air)
        # 圆框描边
        b.circle_yz(wall_x, cy, cz, radius, frame_block)
        # 再清空内圈确保通道干净
        for dy, dz in filled_circle_points(cy, cz, radius - 1):
            b.setblock(wall_x, dy, dz, air)
        # 确保地面可走
        for dz_off in range(-radius, radius + 1):
            b.setblock(wall_x, build_y, cz + dz_off, air)
    else:
        # XY平面圆: 圆心Y=build_y+radius, 圆心X=center_z
        cy = build_y + radius
        cx = center_z
        for dx, dy in filled_circle_points(cx, cy, radius):
            b.setblock(dx, dy, wall_x, air)
        b.circle_xy(cx, cy, wall_x, radius, frame_block)
        for dx, dy in filled_circle_points(cx, cy, radius - 1):
            b.setblock(dx, dy, wall_x, air)
        for dx_off in range(-radius, radius + 1):
            b.setblock(cx + dx_off, build_y, wall_x, air)
''',
        description="月洞门，在墙面上凿圆形洞口+石砖圆框描边。"
                    "支持YZ平面(东西通行)和XY平面(南北通行)两种朝向。"
                    "来源: structures/terrain_wall_pond._build_moon_gate + phase2_corridors",
        tags=["月洞门", "圆门", "洞门", "开洞", "moon", "gate", "circle", "wall"],
    )


# ═══════════════════════════════════════════════════════════
#  景观技能
# ═══════════════════════════════════════════════════════════

def register_landscape_skills(lib: SkillLibrary):
    """注册景观相关技能"""

    # ── 8. 九曲桥 ──
    lib.add_skill(
        name="bridge_zigzag",
        code='''
def build_bridge_zigzag(b, segments, bridge_y=-60,
                        slab_block="minecraft:stone_brick_slab",
                        wall_block="minecraft:cobblestone_wall",
                        pier_block="minecraft:stripped_crimson_stem",
                        pier_interval=3, water_y=-62):
    """九曲桥 — 沿折线段铺设平桥，含栏杆和桥墩。
    适用于池塘上的蜿蜒通道。

    Parameters:
        b          : MinecraftBuilder 实例
        segments   : 折线段列表 [(x1,z1,x2,z2,width_axis), ...]
                     width_axis: 'x'=南北行进时桥面沿x展开, 'z'=东西行进时沿z展开
        bridge_y   : 桥面Y坐标
        slab_block : 桥面半砖
        wall_block : 栏杆方块
        pier_block : 桥墩方块
        pier_interval : 桥墩间距
        water_y    : 水面Y坐标
    """
    placed_slab = set()
    placed_wall = set()

    for (x1, z1, x2, z2, waxis) in segments:
        # 桥面
        b.fill(x1, bridge_y, z1, x2, bridge_y, z2,
               f"{slab_block}[type=top]")
        for x in range(x1, x2 + 1):
            for z in range(z1, z2 + 1):
                placed_slab.add((x, z))

        # 栏杆
        if waxis == 'x':
            for z in range(z1, z2 + 1):
                for wall_x in [x1 - 1, x2 + 1]:
                    key = (wall_x, z)
                    if key not in placed_wall and key not in placed_slab:
                        placed_wall.add(key)
                        b.setblock(wall_x, bridge_y, z, wall_block)
                        b.setblock(wall_x, bridge_y + 1, z, wall_block)
        else:
            for x in range(x1, x2 + 1):
                for wall_z in [z1 - 1, z2 + 1]:
                    key = (x, wall_z)
                    if key not in placed_wall and key not in placed_slab:
                        placed_wall.add(key)
                        b.setblock(x, bridge_y, wall_z, wall_block)
                        b.setblock(x, bridge_y + 1, wall_z, wall_block)

    # 桥墩
    pier_positions = set()
    for (x1, z1, x2, z2, waxis) in segments:
        if waxis == 'x':
            px = (x1 + x2) // 2
            for z in range(z1, z2 + 1, pier_interval):
                if (px, z) not in pier_positions:
                    pier_positions.add((px, z))
                    for y in range(water_y - 2, bridge_y):
                        b.setblock(px, y, z, pier_block)
        else:
            pz = (z1 + z2) // 2
            for x in range(x1, x2 + 1, pier_interval):
                if (x, pz) not in pier_positions:
                    pier_positions.add((x, pz))
                    for y in range(water_y - 2, bridge_y):
                        b.setblock(x, y, pz, pier_block)
''',
        description="九曲桥，沿折线段铺设平桥含栏杆和桥墩。"
                    "传入折线段列表，每段指定矩形范围和展开轴。"
                    "来源: structures/pond_island.build_zigzag_bridge",
        tags=["桥", "九曲", "折线", "栏杆", "桥墩", "bridge", "zigzag", "pond"],
    )

    # ── 9. 太湖石假山 ──
    lib.add_skill(
        name="taihu_rock",
        code='''
import random

def build_taihu_rock(b, cx, cz, ground_y, seed=42,
                     main_block="minecraft:dripstone_block",
                     white_block="minecraft:calcite",
                     moss_block="minecraft:moss_block",
                     moss_carpet="minecraft:moss_carpet"):
    """太湖石假山 — 逐层 pattern 堆叠，体现瘦皱漏透。
    主石9层(8x8)，含东西贯通洞穴+顶部透孔+上大下小体态。
    底座自动铺苔藓。

    Parameters:
        b            : MinecraftBuilder 实例
        cx, cz       : 主石中心XZ坐标
        ground_y     : 地面Y坐标
        seed         : 随机种子（控制材质分布）
    """
    random.seed(seed)

    # 逐层 pattern (8x8)，1=石块, 0=空气
    # 原点 (0,0) = (cx-3, cz-3)
    layers = [
        # L0: 窄底座
        [[0,0,0,0,0,0,0,0],[0,0,0,1,1,0,0,0],[0,0,1,1,1,1,0,0],
         [0,0,1,1,1,1,0,0],[0,0,1,1,1,0,0,0],[0,0,0,1,1,0,0,0],
         [0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0]],
        # L1: 略扩
        [[0,0,0,0,0,0,0,0],[0,0,1,1,1,0,0,0],[0,0,1,1,1,1,0,0],
         [0,1,1,1,1,1,0,0],[0,0,1,1,1,1,0,0],[0,0,0,1,1,0,0,0],
         [0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0]],
        # L2: 洞穴底层（东西贯通）
        [[0,0,0,0,0,0,0,0],[0,0,1,1,1,1,0,0],[0,1,1,1,1,1,1,0],
         [0,1,0,0,0,0,1,0],[0,1,0,0,0,0,1,0],[0,0,1,1,1,1,0,0],
         [0,0,0,1,0,0,0,0],[0,0,0,0,0,0,0,0]],
        # L3: 洞穴中层
        [[0,0,0,1,0,0,0,0],[0,0,1,1,1,1,0,0],[0,1,1,1,1,1,1,0],
         [0,1,0,0,0,0,1,1],[0,1,0,0,0,0,1,0],[0,1,1,1,1,1,0,0],
         [0,0,1,1,1,0,0,0],[0,0,0,0,0,0,0,0]],
        # L4: 洞穴顶层
        [[0,0,0,1,1,0,0,0],[0,1,1,1,1,1,0,0],[0,1,1,1,1,1,1,0],
         [0,1,0,0,0,1,1,1],[0,1,1,0,0,1,1,0],[0,1,1,1,1,1,0,0],
         [0,0,1,1,1,0,0,0],[0,0,0,0,0,0,0,0]],
        # L5: 上部扩宽（上大下小关键层）
        [[0,0,1,1,1,0,0,0],[0,1,1,1,1,1,1,0],[1,1,1,1,1,1,1,0],
         [0,1,1,1,1,1,1,1],[1,1,1,1,1,1,1,0],[0,1,1,1,1,1,1,0],
         [0,0,1,1,1,1,0,0],[0,0,0,1,0,0,0,0]],
        # L6: 最宽层+透孔
        [[0,0,1,1,1,1,0,0],[0,1,1,1,1,1,1,0],[1,1,1,0,1,1,1,1],
         [1,1,1,1,0,1,1,1],[1,1,1,1,1,1,1,1],[0,1,1,1,1,1,1,0],
         [0,1,1,1,1,1,0,0],[0,0,0,1,1,0,0,0]],
        # L7: 收窄，皱纹凹陷
        [[0,0,0,1,1,0,0,0],[0,0,1,1,1,1,0,0],[0,1,1,0,1,1,1,0],
         [0,1,1,1,1,1,1,0],[0,1,1,1,1,0,1,0],[0,0,1,1,1,1,0,0],
         [0,0,1,1,0,0,0,0],[0,0,0,0,0,0,0,0]],
        # L8: 顶冠
        [[0,0,0,0,0,0,0,0],[0,0,0,1,1,0,0,0],[0,0,1,1,1,0,0,0],
         [0,0,1,1,1,1,0,0],[0,0,0,1,1,0,0,0],[0,0,0,1,0,0,0,0],
         [0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0]],
        # L9: 尖顶
        [[0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0],[0,0,0,1,0,0,0,0],
         [0,0,0,1,1,0,0,0],[0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0],
         [0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0]],
    ]

    ox, oz = cx - 3, cz - 3
    for dy, layer in enumerate(layers):
        y = ground_y + dy
        for dz_idx, row in enumerate(layer):
            for dx_idx, val in enumerate(row):
                if val == 1:
                    block = white_block if random.random() < 0.30 else main_block
                    b.setblock(ox + dx_idx, y, oz + dz_idx, block)

    # 底座苔藓
    bottom = set()
    for dz_idx, row in enumerate(layers[0]):
        for dx_idx, val in enumerate(row):
            if val == 1:
                bottom.add((ox + dx_idx, oz + dz_idx))
    for (bx, bz) in list(bottom):
        for ddx in [-1, 0, 1]:
            for ddz in [-1, 0, 1]:
                nx, nz = bx + ddx, bz + ddz
                if (nx, nz) not in bottom and random.random() < 0.6:
                    b.setblock(nx, ground_y, nz, moss_block)
                    if random.random() < 0.4:
                        b.setblock(nx, ground_y + 1, nz, moss_carpet)
''',
        description="太湖石假山，10层逐层pattern堆叠，体现瘦皱漏透。"
                    "含东西贯通洞穴、顶部透孔、上大下小体态、底座苔藓。"
                    "来源: structures/rocks_swing._build_taihu_rocks",
        tags=["假山", "太湖石", "置石", "瘦皱漏透", "rock", "taihu", "garden"],
    )

    # ── 10. 垂柳 ──
    lib.add_skill(
        name="willow_tree",
        code='''
import random

def build_willow_tree(b, wx, wz, y_base=-60, seed=None):
    """垂柳 — oak_log树干 + oak_leaves扁平宽冠 + vine垂枝。
    适用于池塘岸边、水景点缀。

    Parameters:
        b        : MinecraftBuilder 实例
        wx, wz   : 树干底部XZ坐标
        y_base   : 树干底部Y坐标
        seed     : 随机种子 (None=不固定)
    """
    if seed is not None:
        random.seed(seed)

    trunk_h = random.randint(4, 6)

    # 树干
    for dy in range(trunk_h):
        b.setblock(wx, y_base + dy, wz, "minecraft:oak_log")

    # 扁平宽冠
    crown_top = y_base + trunk_h
    h_radius = random.randint(3, 4)
    v_layers = [
        (0, h_radius),
        (1, h_radius - 1),
        (-1, h_radius - 1),
    ]

    vine_candidates = []
    for dy_off, r in v_layers:
        y = crown_top + dy_off
        for dx in range(-r, r + 1):
            for dz in range(-r, r + 1):
                dist_sq = dx * dx + dz * dz
                if dist_sq <= r * r:
                    if dist_sq > r * r * 0.5 and random.random() < 0.25:
                        continue
                    b.setblock(wx + dx, y, wz + dz,
                               "minecraft:oak_leaves[persistent=true]")
                    if dy_off == -1 and dist_sq > (r - 1) ** 2:
                        vine_candidates.append((wx + dx, y, wz + dz))

    # 最宽层边缘下方也挂藤
    for dy_off, r in v_layers:
        if dy_off != 0:
            continue
        y = crown_top
        for dx in range(-r, r + 1):
            for dz in range(-r, r + 1):
                dist_sq = dx * dx + dz * dz
                if r * r * 0.7 < dist_sq <= r * r:
                    vine_candidates.append((wx + dx, y, wz + dz))

    # 垂枝 vine
    vine_candidates = list(set(vine_candidates))
    random.shuffle(vine_candidates)
    vine_count = min(len(vine_candidates), random.randint(8, 14))

    for vx, vy, vz in vine_candidates[:vine_count]:
        dx = vx - wx
        dz = vz - wz
        faces = []
        if dx > 0: faces.append("east=true")
        elif dx < 0: faces.append("west=true")
        if dz > 0: faces.append("south=true")
        elif dz < 0: faces.append("north=true")
        if not faces: faces.append("south=true")
        state = ",".join(faces)
        vine_len = random.randint(2, 3)
        for vdy in range(vine_len):
            b.setblock(vx, vy - 1 - vdy, vz,
                       f"minecraft:vine[{state}]")
''',
        description="垂柳，oak_log树干+oak_leaves扁平宽冠+vine垂枝。"
                    "随机树高4-6格，冠幅3-4格，8-14条藤蔓垂挂。"
                    "来源: landscape._build_willows",
        tags=["树", "垂柳", "垂杨", "藤蔓", "水景", "willow", "tree", "vine", "pond"],
    )


# ═══════════════════════════════════════════════════════════
#  主入口
# ═══════════════════════════════════════════════════════════

if __name__ == "__main__":
    lib = SkillLibrary()

    # 注册所有预置技能
    register_roof_skills(lib)
    register_structure_skills(lib)
    register_landscape_skills(lib)

    print(f"已注册 {len(lib.skills)} 个技能:")
    for name in lib.list_skills():
        skill = lib.skills[name]
        print(f"  - {name}: {skill['description'][:50]}... "
              f"[{', '.join(skill['tags'][:3])}]")
