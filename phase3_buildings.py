"""phase3_buildings.py — 全部 19 栋建筑

牡丹亭·游园惊梦 — v3 Phase 3
包含: 牡丹亭(攒尖)、远香堂(歇山)、翠轩(悬山)、池馆、濯缨水阁、
      入口门厅、小庭深院、半亭、曲廊亭、听雨轩、荼蘼花架、秋千、
      太湖石组、大梅树、画船、石舫、梅花庵观、闺塾、芍药阑

命令预算 < 5000
"""

import sys
sys.path.insert(0, '/Users/lambertlin/minecraft-server/scripts')

from builder import MinecraftBuilder
import config_v3 as cfg
from blocks import PALETTE


# ═══════════════════════════════════════════
# 材质快捷引用
# ═══════════════════════════════════════════

P = PALETTE
PILLAR      = P["pillar"]          # stripped_crimson_stem
BEAM        = P["beam"]            # dark_oak_planks
BEAM_LOG    = P["beam_log"]        # dark_oak_log
BASE        = P["base"]            # stone_bricks
BASE_COL    = P["base_col"]        # polished_andesite
BASE_STEP   = P["base_step"]       # stone_brick_stairs
FLOOR       = P["floor"]           # smooth_stone
FLOOR_ALT   = P["floor_alt"]       # stone_bricks (棋盘格)
WALL_BLOCK  = P["wall"]            # white_concrete
WALL_BASE   = P["wall_base"]       # stone_bricks
WALL_CAP    = P["wall_cap"]        # stone_brick_slab
RAIL        = P["rail"]            # crimson_fence
RAIL_GATE   = P["rail_gate"]       # crimson_fence_gate
ROOF_STAIR  = P["roof"]            # stone_brick_stairs
ROOF_SLAB   = P["roof_slab"]       # stone_brick_slab
ROOF_BLOCK  = P["roof_block"]      # stone_bricks
EAVE_OUTER  = P["eave_outer"]      # dark_oak_stairs
EAVE_SLAB   = P["eave_slab"]       # dark_oak_slab
LANTERN     = P["lantern"]         # lantern
WINDOW      = P["window"]          # iron_bars
DOOR        = P["door"]            # crimson_door
AIR         = P["air"]
TRAPDOOR    = P["trapdoor"]        # jungle_trapdoor
CHERRY_LOG  = P["cherry_log"]
CHERRY_LVS  = P["cherry_leaves"]   # persistent=true
OAK_LVS     = P["oak_leaves"]      # persistent=true
SPRUCE_LVS  = P["spruce_leaves"]   # persistent=true
OAK_LOG     = P["oak_log"]
TAIHU_MAIN  = P["taihu_main"]      # dripstone_block
TAIHU_WHITE = P["taihu_white"]     # calcite
PEONY_FLOWER = P["peony"]
RED_CARPET  = P["red_carpet"]
FLOOR_WOOD  = P["floor_wood"]      # spruce_planks
BAMBOO      = P["bamboo"]


# ═══════════════════════════════════════════
# 方向常量 — stairs facing
# ═══════════════════════════════════════════
# Minecraft stair facing: "north" means ascending toward north (the LOW side faces north)
# For roof eaves: outer ring stairs face outward (low side = exterior)

def _stair(block_base, facing, half="bottom"):
    """生成 stairs blockstate 字符串"""
    return f"{block_base}[facing={facing},half={half}]"


def _slab(block_base, stype="bottom"):
    return f"{block_base}[type={stype}]"


# ═══════════════════════════════════════════
# 通用建筑组件
# ═══════════════════════════════════════════

def _build_platform(b, x1, z1, x2, z2, gy, height=1):
    """台基 + 散水带
    台基: stone_bricks, height 格高
    散水: polished_andesite 外围 1 格
    """
    # 散水带 (外围1格, 单层在 gy 层)
    b.fill(x1 - 1, gy, z1 - 1, x2 + 1, gy, z2 + 1, BASE_COL)
    # 台基实体
    for dy in range(height):
        b.fill(x1, gy + dy, z1, x2, gy + dy, z2, BASE)
    # 台基顶面 = gy + height - 1 (已经填好了)
    return gy + height  # 返回台基顶面的 下一层 Y (柱子起始)


def _build_floor_checkerboard(b, x1, z1, x2, z2, y):
    """棋盘格地面铺装: smooth_stone + polished_andesite"""
    # 先全部铺 smooth_stone
    b.fill(x1, y, z1, x2, y, z2, FLOOR)
    # 再隔格替换为 polished_andesite
    for x in range(x1, x2 + 1):
        for z in range(z1, z2 + 1):
            if (x + z) % 2 == 1:
                b.setblock(x, y, z, BASE_COL)


def _build_floor_checkerboard_fast(b, x1, z1, x2, z2, y):
    """条纹铺装 — 先铺满 smooth_stone，再按隔行 fill polished_andesite
    用 fill 逐行替换，命令数 = 1 + (z_span/2)，远少于逐格 setblock
    """
    b.fill(x1, y, z1, x2, y, z2, FLOOR)
    for z in range(z1, z2 + 1):
        if (z - z1) % 2 == 1:
            b.fill(x1, y, z, x2, y, z, BASE_COL)


def _build_pillars(b, x1, z1, x2, z2, floor_y, pillar_h, corner_only=False):
    """柱子 + 柱础
    在矩形四角 + 每面中间等距放柱。
    corner_only=True 时只放四角。
    返回柱顶 Y。
    """
    pillar_top_y = floor_y + pillar_h

    # 收集柱位
    positions = []

    # 四角必放
    corners = [(x1, z1), (x1, z2), (x2, z1), (x2, z2)]
    positions.extend(corners)

    if not corner_only:
        # 每面墙中间等距加柱 (间距 ~3-4 格)
        # 北墙 (z=z1) 和 南墙 (z=z2)
        for z in [z1, z2]:
            span = x2 - x1
            if span > 4:
                n_mid = max(1, span // 4)
                step = span / (n_mid + 1)
                for i in range(1, n_mid + 1):
                    mx = x1 + round(step * i)
                    if (mx, z) not in positions:
                        positions.append((mx, z))

        # 西墙 (x=x1) 和 东墙 (x=x2)
        for x in [x1, x2]:
            span = z2 - z1
            if span > 4:
                n_mid = max(1, span // 4)
                step = span / (n_mid + 1)
                for i in range(1, n_mid + 1):
                    mz = z1 + round(step * i)
                    if (x, mz) not in positions:
                        positions.append((x, mz))

    for (px, pz) in positions:
        # 柱础 (polished_andesite, 在 floor_y 层)
        b.setblock(px, floor_y, pz, BASE_COL)
        # 柱身 (vertical fill)
        b.fill(px, floor_y + 1, pz, px, pillar_top_y, pz, PILLAR)

    return pillar_top_y, positions


def _build_beams(b, x1, z1, x2, z2, beam_y):
    """梁枋 — 在柱顶连接四面横梁"""
    # 北梁 (z=z1)
    b.fill(x1, beam_y, z1, x2, beam_y, z1, BEAM)
    # 南梁 (z=z2)
    b.fill(x1, beam_y, z2, x2, beam_y, z2, BEAM)
    # 西梁 (x=x1)
    b.fill(x1, beam_y, z1, x1, beam_y, z2, BEAM)
    # 东梁 (x=x2)
    b.fill(x2, beam_y, z1, x2, beam_y, z2, BEAM)


def _build_railings(b, x1, z1, x2, z2, rail_y, facing, entrance_width=3):
    """栏杆 — crimson_fence，每面留 entrance_width 格入口
    facing: 入口朝向 "north"/"south"/"east"/"west"/"all"/None
    如果 facing="all" 则四面都留入口
    """
    # 确定哪些面需要留入口
    if facing is None:
        entrance_faces = set()
    elif facing == "all":
        entrance_faces = {"north", "south", "east", "west"}
    elif facing in ("north", "south", "east", "west"):
        entrance_faces = {facing}
    elif facing == "northwest":
        entrance_faces = {"north", "west"}
    elif facing == "east_west":
        entrance_faces = {"east", "west"}
    elif facing == "north_south":
        entrance_faces = {"north", "south"}
    else:
        entrance_faces = {facing}

    half_ew = entrance_width // 2
    cx = (x1 + x2) // 2
    cz = (z1 + z2) // 2

    # 北面 (z=z1, x varies)
    for x in range(x1, x2 + 1):
        if "north" in entrance_faces and abs(x - cx) <= half_ew:
            continue  # 入口留空
        b.setblock(x, rail_y, z1, RAIL)

    # 南面 (z=z2, x varies)
    for x in range(x1, x2 + 1):
        if "south" in entrance_faces and abs(x - cx) <= half_ew:
            continue
        b.setblock(x, rail_y, z2, RAIL)

    # 西面 (x=x1, z varies)
    for z in range(z1, z2 + 1):
        if "west" in entrance_faces and abs(z - cz) <= half_ew:
            continue
        b.setblock(x1, rail_y, z, RAIL)

    # 东面 (x=x2, z varies)
    for z in range(z1, z2 + 1):
        if "east" in entrance_faces and abs(z - cz) <= half_ew:
            continue
        b.setblock(x2, rail_y, z, RAIL)


def _build_railings_fill(b, x1, z1, x2, z2, rail_y, facing, entrance_width=3):
    """栏杆 — 用 fill 高效版本
    先 fill 四面，再在入口处 fill air 打断
    """
    half_ew = entrance_width // 2
    cx = (x1 + x2) // 2
    cz = (z1 + z2) // 2

    if facing is None:
        entrance_faces = set()
    elif facing == "all":
        entrance_faces = {"north", "south", "east", "west"}
    elif facing in ("north", "south", "east", "west"):
        entrance_faces = {facing}
    elif facing == "northwest":
        entrance_faces = {"north", "west"}
    elif facing == "east_west":
        entrance_faces = {"east", "west"}
    elif facing == "north_south":
        entrance_faces = {"north", "south"}
    else:
        entrance_faces = {facing}

    # 四面 fill
    b.fill(x1, rail_y, z1, x2, rail_y, z1, RAIL)  # 北
    b.fill(x1, rail_y, z2, x2, rail_y, z2, RAIL)  # 南
    b.fill(x1, rail_y, z1, x1, rail_y, z2, RAIL)  # 西
    b.fill(x2, rail_y, z1, x2, rail_y, z2, RAIL)  # 东

    # 在入口处开口 (fill air)
    if "north" in entrance_faces:
        b.fill(cx - half_ew, rail_y, z1, cx + half_ew, rail_y, z1, AIR)
    if "south" in entrance_faces:
        b.fill(cx - half_ew, rail_y, z2, cx + half_ew, rail_y, z2, AIR)
    if "west" in entrance_faces:
        b.fill(x1, rail_y, cz - half_ew, x1, rail_y, cz + half_ew, AIR)
    if "east" in entrance_faces:
        b.fill(x2, rail_y, cz - half_ew, x2, rail_y, cz + half_ew, AIR)


def _build_lanterns(b, x1, z1, x2, z2, y, pillar_positions):
    """灯笼 — 挂在四角柱头内侧"""
    corners = [(x1, z1), (x1, z2), (x2, z1), (x2, z2)]
    cx = (x1 + x2) // 2
    cz = (z1 + z2) // 2
    for (px, pz) in corners:
        # 灯笼挂在柱子内侧1格, y-1 位置 (悬挂)
        dx = 1 if px < cx else -1
        dz = 1 if pz < cz else -1
        b.setblock(px + dx, y, pz + dz, f"{LANTERN}[hanging=true]")


# ═══════════════════════════════════════════
# 屋顶系统
# ═══════════════════════════════════════════

def _build_roof_hip(b, x1, z1, x2, z2, base_y):
    """歇山顶 (hip roof) — 四面坡
    从外圈 stairs 逐层收缩到顶部 slab
    stairs facing 朝外 (低端朝外)
    """
    layer = 0
    cx1, cz1, cx2, cz2 = x1 - 1, z1 - 1, x2 + 1, z2 + 1  # 出檐1格
    y = base_y

    while cx1 < cx2 and cz1 < cz2:
        # 四面 stairs
        # 北面 (facing=south, 低端朝北=facing north... 不对)
        # MC stairs facing=north 意味着楼梯底部朝北，上升朝南
        # 屋顶北面坡: 从北往南升高，所以 stairs facing=south
        # 实际: 屋顶外圈 stairs 低端朝外

        # 北边一行 stairs: facing=north (底端朝北=朝外)
        if cx2 - cx1 >= 2:
            b.fill(cx1 + 1, y, cz1, cx2 - 1, y, cz1,
                   _stair(ROOF_STAIR, "south"))
        # 南边
        if cx2 - cx1 >= 2:
            b.fill(cx1 + 1, y, cz2, cx2 - 1, y, cz2,
                   _stair(ROOF_STAIR, "north"))
        # 西边
        if cz2 - cz1 >= 2:
            b.fill(cx1, y, cz1 + 1, cx1, y, cz2 - 1,
                   _stair(ROOF_STAIR, "east"))
        # 东边
        if cz2 - cz1 >= 2:
            b.fill(cx2, y, cz1 + 1, cx2, y, cz2 - 1,
                   _stair(ROOF_STAIR, "west"))

        # 四角用实心方块填充
        for corner_x, corner_z in [(cx1, cz1), (cx1, cz2), (cx2, cz1), (cx2, cz2)]:
            b.setblock(corner_x, y, corner_z, ROOF_BLOCK)

        # 收缩
        cx1 += 1
        cz1 += 1
        cx2 -= 1
        cz2 -= 1
        y += 1
        layer += 1

        if layer > 10:
            break

    # 顶部封口 slab
    if cx1 <= cx2 and cz1 <= cz2:
        b.fill(cx1, y, cz1, cx2, y, cz2, _slab(ROOF_SLAB, "bottom"))
    elif cx1 - 1 <= cx2 + 1:
        b.setblock((cx1 + cx2) // 2, y, (cz1 + cz2) // 2,
                   _slab(ROOF_SLAB, "bottom"))

    # 飞檐 — 最外圈下方 dark_oak_stairs 朝外翘起
    eave_y = base_y - 1
    ox1, oz1, ox2, oz2 = x1 - 2, z1 - 2, x2 + 2, z2 + 2
    # 北飞檐
    b.fill(ox1 + 1, eave_y, oz1, ox2 - 1, eave_y, oz1,
           _stair(EAVE_OUTER, "south", "top"))
    # 南飞檐
    b.fill(ox1 + 1, eave_y, oz2, ox2 - 1, eave_y, oz2,
           _stair(EAVE_OUTER, "north", "top"))
    # 西飞檐
    b.fill(ox1, eave_y, oz1 + 1, ox1, eave_y, oz2 - 1,
           _stair(EAVE_OUTER, "east", "top"))
    # 东飞檐
    b.fill(ox2, eave_y, oz1 + 1, ox2, eave_y, oz2 - 1,
           _stair(EAVE_OUTER, "west", "top"))
    # 四角翘角
    for cx, cz in [(ox1, oz1), (ox1, oz2), (ox2, oz1), (ox2, oz2)]:
        b.setblock(cx, eave_y, cz, EAVE_SLAB)


def _build_roof_gable(b, x1, z1, x2, z2, base_y, ridge_axis="x"):
    """悬山顶 (gable roof) — 两面坡 + 两侧山墙
    ridge_axis: "x" 表示屋脊沿 X 方向 (南北两面坡)
                "z" 表示屋脊沿 Z 方向 (东西两面坡)
    """
    if ridge_axis == "x":
        # 屋脊沿 X，南北两面坡
        cz = (z1 + z2) // 2
        half_span = cz - z1 + 1  # 从边缘到中心的距离
        y = base_y

        # 出檐
        ox1, ox2 = x1 - 1, x2 + 1

        for layer in range(half_span + 1):
            nz = z1 - 1 + layer   # 北坡当前 Z
            sz = z2 + 1 - layer   # 南坡当前 Z

            if nz > cz:
                break

            if nz == sz:
                # 顶部屋脊 — slab
                b.fill(ox1, y, nz, ox2, y, nz, _slab(ROOF_SLAB, "bottom"))
            else:
                if nz == cz or sz == cz:
                    # 接近屋脊，用实心方块
                    if nz <= cz:
                        b.fill(ox1, y, nz, ox2, y, nz, ROOF_BLOCK)
                    if sz >= cz:
                        b.fill(ox1, y, sz, ox2, y, sz, ROOF_BLOCK)
                else:
                    # 北坡 stairs (facing=south, 底端朝北)
                    b.fill(ox1, y, nz, ox2, y, nz,
                           _stair(ROOF_STAIR, "south"))
                    # 南坡 stairs (facing=north, 底端朝南)
                    b.fill(ox1, y, sz, ox2, y, sz,
                           _stair(ROOF_STAIR, "north"))
            y += 1

        # 两侧山墙三角 (x=x1 和 x=x2 面)
        # 用 stone_bricks 填充三角形
        for wall_x in [x1, x2]:
            for dy in range(half_span):
                inner_z1 = z1 + dy
                inner_z2 = z2 - dy
                if inner_z1 < inner_z2:
                    b.fill(wall_x, base_y + dy, inner_z1, wall_x, base_y + dy, inner_z2,
                           WALL_BLOCK)

        # 飞檐
        eave_y = base_y - 1
        b.fill(ox1, eave_y, z1 - 2, ox2, eave_y, z1 - 2,
               _stair(EAVE_OUTER, "south", "top"))
        b.fill(ox1, eave_y, z2 + 2, ox2, eave_y, z2 + 2,
               _stair(EAVE_OUTER, "north", "top"))

    else:  # ridge_axis == "z"
        # 屋脊沿 Z，东西两面坡
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
                b.fill(wx, y, oz1, wx, y, oz2, _slab(ROOF_SLAB, "bottom"))
            else:
                if wx == cx_mid or ex == cx_mid:
                    if wx <= cx_mid:
                        b.fill(wx, y, oz1, wx, y, oz2, ROOF_BLOCK)
                    if ex >= cx_mid:
                        b.fill(ex, y, oz1, ex, y, oz2, ROOF_BLOCK)
                else:
                    b.fill(wx, y, oz1, wx, y, oz2,
                           _stair(ROOF_STAIR, "east"))
                    b.fill(ex, y, oz1, ex, y, oz2,
                           _stair(ROOF_STAIR, "west"))
            y += 1

        # 山墙
        for wall_z in [z1, z2]:
            for dy in range(half_span):
                inner_x1 = x1 + dy
                inner_x2 = x2 - dy
                if inner_x1 < inner_x2:
                    b.fill(inner_x1, base_y + dy, wall_z,
                           inner_x2, base_y + dy, wall_z, WALL_BLOCK)

        # 飞檐
        eave_y = base_y - 1
        b.fill(x1 - 2, eave_y, oz1, x1 - 2, eave_y, oz2,
               _stair(EAVE_OUTER, "east", "top"))
        b.fill(x2 + 2, eave_y, oz1, x2 + 2, eave_y, oz2,
               _stair(EAVE_OUTER, "west", "top"))


def _build_roof_hip_pointed(b, x1, z1, x2, z2, base_y):
    """攒尖顶 (hip-pointed / pyramidal) — 四面等坡收尖
    牡丹亭专用，顶部加宝顶 (lightning_rod)
    """
    cx = (x1 + x2) // 2
    cz = (z1 + z2) // 2
    layer = 0
    cx1, cz1, cx2, cz2 = x1 - 1, z1 - 1, x2 + 1, z2 + 1  # 出檐
    y = base_y

    while cx1 <= cx2 and cz1 <= cz2:
        if cx1 == cx2 and cz1 == cz2:
            # 尖顶
            b.setblock(cx1, y, cz1, ROOF_BLOCK)
            b.setblock(cx1, y + 1, cz1, P["lightning_rod"])  # 宝顶
            break
        elif cx1 == cx2:
            # 只剩一列
            b.fill(cx1, y, cz1, cx1, y, cz2, ROOF_BLOCK)
            y += 1
            cz1 += 1
            cz2 -= 1
            continue
        elif cz1 == cz2:
            # 只剩一行
            b.fill(cx1, y, cz1, cx2, y, cz1, ROOF_BLOCK)
            y += 1
            cx1 += 1
            cx2 -= 1
            continue

        # 四面 stairs
        # 北
        b.fill(cx1 + 1, y, cz1, cx2 - 1, y, cz1,
               _stair(ROOF_STAIR, "south"))
        # 南
        b.fill(cx1 + 1, y, cz2, cx2 - 1, y, cz2,
               _stair(ROOF_STAIR, "north"))
        # 西
        b.fill(cx1, y, cz1 + 1, cx1, y, cz2 - 1,
               _stair(ROOF_STAIR, "east"))
        # 东
        b.fill(cx2, y, cz1 + 1, cx2, y, cz2 - 1,
               _stair(ROOF_STAIR, "west"))
        # 四角
        for corner_x, corner_z in [(cx1, cz1), (cx1, cz2), (cx2, cz1), (cx2, cz2)]:
            b.setblock(corner_x, y, corner_z, ROOF_BLOCK)

        cx1 += 1
        cz1 += 1
        cx2 -= 1
        cz2 -= 1
        y += 1
        layer += 1
        if layer > 12:
            break

    # 飞檐 — 最外圈翘角
    eave_y = base_y - 1
    ox1, oz1, ox2, oz2 = x1 - 2, z1 - 2, x2 + 2, z2 + 2
    b.fill(ox1 + 1, eave_y, oz1, ox2 - 1, eave_y, oz1,
           _stair(EAVE_OUTER, "south", "top"))
    b.fill(ox1 + 1, eave_y, oz2, ox2 - 1, eave_y, oz2,
           _stair(EAVE_OUTER, "north", "top"))
    b.fill(ox1, eave_y, oz1 + 1, ox1, eave_y, oz2 - 1,
           _stair(EAVE_OUTER, "east", "top"))
    b.fill(ox2, eave_y, oz1 + 1, ox2, eave_y, oz2 - 1,
           _stair(EAVE_OUTER, "west", "top"))
    for ccx, ccz in [(ox1, oz1), (ox1, oz2), (ox2, oz1), (ox2, oz2)]:
        b.setblock(ccx, eave_y, ccz, EAVE_SLAB)


# ═══════════════════════════════════════════
# 墙体系统
# ═══════════════════════════════════════════

def _build_walls_enclosed(b, x1, z1, x2, z2, floor_y, wall_h, facing):
    """全封闭墙体: 白墙 + 窗 + 门
    facing 方向的中间开门(3格宽), 其余面有 iron_bars 窗
    """
    top_y = floor_y + wall_h

    entrance_faces = set()
    if facing in ("north", "south", "east", "west"):
        entrance_faces = {facing}
    elif facing == "all":
        entrance_faces = {"north", "south", "east", "west"}

    cx = (x1 + x2) // 2
    cz = (z1 + z2) // 2

    # 四面墙 fill
    # 北墙
    b.fill(x1, floor_y + 1, z1, x2, top_y, z1, WALL_BLOCK)
    # 南墙
    b.fill(x1, floor_y + 1, z2, x2, top_y, z2, WALL_BLOCK)
    # 西墙
    b.fill(x1, floor_y + 1, z1, x1, top_y, z2, WALL_BLOCK)
    # 东墙
    b.fill(x2, floor_y + 1, z1, x2, top_y, z2, WALL_BLOCK)

    # 开门 (3格宽, 2格高)
    door_h = min(2, wall_h)
    for face in entrance_faces:
        if face == "north":
            b.fill(cx - 1, floor_y + 1, z1, cx + 1, floor_y + door_h, z1, AIR)
        elif face == "south":
            b.fill(cx - 1, floor_y + 1, z2, cx + 1, floor_y + door_h, z2, AIR)
        elif face == "west":
            b.fill(x1, floor_y + 1, cz - 1, x1, floor_y + door_h, cz + 1, AIR)
        elif face == "east":
            b.fill(x2, floor_y + 1, cz - 1, x2, floor_y + door_h, cz + 1, AIR)

    # 窗户 (iron_bars, 在非门面的墙中段)
    window_y1 = floor_y + 2
    window_y2 = min(floor_y + 3, top_y)
    if window_y1 <= window_y2:
        if "north" not in entrance_faces:
            b.fill(cx - 1, window_y1, z1, cx + 1, window_y2, z1, WINDOW)
        if "south" not in entrance_faces:
            b.fill(cx - 1, window_y1, z2, cx + 1, window_y2, z2, WINDOW)
        if "west" not in entrance_faces:
            b.fill(x1, window_y1, cz - 1, x1, window_y2, cz + 1, WINDOW)
        if "east" not in entrance_faces:
            b.fill(x2, window_y1, cz - 1, x2, window_y2, cz + 1, WINDOW)


def _build_walls_half_open(b, x1, z1, x2, z2, floor_y, wall_h, facing):
    """半封闭墙体 (轩/阁): facing 方向全敞开, 其余面白墙+窗"""
    top_y = floor_y + wall_h

    open_faces = set()
    if facing in ("north", "south", "east", "west"):
        open_faces = {facing}
    elif facing == "all":
        return  # 全敞开不建墙
    elif facing == "northwest":
        open_faces = {"north", "west"}
    elif facing == "east_west":
        open_faces = {"east", "west"}

    cx = (x1 + x2) // 2
    cz = (z1 + z2) // 2

    # 建非敞开面的墙
    if "north" not in open_faces:
        b.fill(x1, floor_y + 1, z1, x2, top_y, z1, WALL_BLOCK)
        # 窗
        b.fill(cx - 1, floor_y + 2, z1, cx + 1, min(floor_y + 3, top_y), z1, WINDOW)
    if "south" not in open_faces:
        b.fill(x1, floor_y + 1, z2, x2, top_y, z2, WALL_BLOCK)
        b.fill(cx - 1, floor_y + 2, z2, cx + 1, min(floor_y + 3, top_y), z2, WINDOW)
    if "west" not in open_faces:
        b.fill(x1, floor_y + 1, z1, x1, top_y, z2, WALL_BLOCK)
        b.fill(x1, floor_y + 2, cz - 1, x1, min(floor_y + 3, top_y), cz + 1, WINDOW)
    if "east" not in open_faces:
        b.fill(x2, floor_y + 1, z1, x2, top_y, z2, WALL_BLOCK)
        b.fill(x2, floor_y + 2, cz - 1, x2, min(floor_y + 3, top_y), cz + 1, WINDOW)


# ═══════════════════════════════════════════
# 通用建筑建造器
# ═══════════════════════════════════════════

def _get_building_bounds(bldg):
    """从建筑 config 计算矩形范围"""
    cx = bldg["cx"]
    cz = bldg["cz"]
    sx = bldg["size_x"]
    sz = bldg["size_z"]
    x1 = cx - sx // 2
    z1 = cz - sz // 2
    x2 = cx + sx // 2
    z2 = cz + sz // 2
    return x1, z1, x2, z2


def _building_type(bldg):
    """判断建筑墙体类型: open / half_open / enclosed"""
    facing = bldg.get("facing")
    name = bldg.get("name", "")

    if facing == "all":
        return "open"  # 四面敞开 (亭)
    if facing is None:
        return "enclosed"  # 围合
    # 临水建筑通常半敞开
    if bldg.get("over_water"):
        return "half_open"
    # 轩/阁/水阁 → 半敞开
    if any(k in name for k in ["轩", "阁", "半亭"]):
        return "half_open"
    # 厅/堂/门厅/庵/塾 → 全封闭
    return "enclosed"


def build_standard_building(b, bldg):
    """建造一栋标准建筑: 台基→柱子→梁→墙→屋顶→栏杆→灯笼→地面"""
    name = bldg["name"]
    gy = bldg["ground_y"]
    pillar_h = bldg.get("pillar_h", 5)
    roof_type = bldg.get("roof_type", "hip")
    facing = bldg.get("facing", "south")

    x1, z1, x2, z2 = _get_building_bounds(bldg)
    btype = _building_type(bldg)

    print(f"  Building {name} ({btype}, {roof_type}) at ({x1},{z1})-({x2},{z2}) gy={gy}")

    # 1. 台基 + 散水
    platform_h = 2 if gy <= -59 else 1
    floor_y = _build_platform(b, x1, z1, x2, z2, gy, platform_h)
    # floor_y 现在是台基顶面+1 = gy + platform_h
    # 实际地面层 = floor_y - 1
    actual_floor_y = floor_y - 1

    # 2. 地面铺装 (条纹)
    _build_floor_checkerboard_fast(b, x1, z1, x2, z2, actual_floor_y)

    # 3. 柱子 + 柱础
    is_small = (x2 - x1 <= 5 and z2 - z1 <= 5)
    pillar_top_y, pillar_pos = _build_pillars(
        b, x1, z1, x2, z2, actual_floor_y, pillar_h,
        corner_only=is_small
    )

    # 4. 梁枋
    beam_y = pillar_top_y
    _build_beams(b, x1, z1, x2, z2, beam_y)

    # 5. 墙体
    wall_h = pillar_h - 1  # 墙比柱矮1格
    if btype == "open":
        pass  # 四面敞开，不建墙
    elif btype == "half_open":
        _build_walls_half_open(b, x1, z1, x2, z2, actual_floor_y, wall_h, facing)
    else:  # enclosed
        _build_walls_enclosed(b, x1, z1, x2, z2, actual_floor_y, wall_h, facing)

    # 6. 屋顶
    roof_base_y = beam_y + 1
    if roof_type == "hip_pointed":
        _build_roof_hip_pointed(b, x1, z1, x2, z2, roof_base_y)
    elif roof_type == "hip":
        _build_roof_hip(b, x1, z1, x2, z2, roof_base_y)
    elif roof_type == "gable":
        # 判断屋脊方向: 入口面垂直的方向为坡面
        if facing in ("north", "south"):
            ridge_axis = "x"  # 屋脊沿X，南北两面坡
        elif facing in ("east", "west"):
            ridge_axis = "z"  # 屋脊沿Z，东西两面坡
        else:
            # 默认按长边方向
            ridge_axis = "x" if (x2 - x1) >= (z2 - z1) else "z"
        _build_roof_gable(b, x1, z1, x2, z2, roof_base_y, ridge_axis)

    # 7. 栏杆 (仅敞开/半敞开建筑)
    if btype in ("open", "half_open"):
        _build_railings_fill(b, x1, z1, x2, z2, actual_floor_y + 1, facing)

    # 8. 灯笼
    lantern_y = beam_y - 1
    _build_lanterns(b, x1, z1, x2, z2, lantern_y, pillar_pos)

    # 注册 bbox 用于撤销
    roof_top_y = roof_base_y + max(x2 - x1, z2 - z1) // 2 + 3
    b.register_bbox(name, x1 - 2, gy, z1 - 2, x2 + 2, roof_top_y, z2 + 2)


# ═══════════════════════════════════════════
# 特殊建筑
# ═══════════════════════════════════════════

def build_peony_pavilion(b):
    """1. 牡丹亭 — 15x15 攒尖顶，全园最高建筑
    特殊处理: 更高的柱子(6格)、双层台基、宝顶
    """
    bldg = cfg.PEONY_PAVILION
    print(f"=== Building {bldg['name']} (P0 核心) ===")
    build_standard_building(b, bldg)

    # 额外: 中央放红毯 + 灯笼
    x1, z1, x2, z2 = _get_building_bounds(bldg)
    gy = bldg["ground_y"]
    floor_y = gy + 1  # 台基1格高
    cx = (x1 + x2) // 2
    cz = (z1 + z2) // 2
    # 中央红毯 3x3
    b.fill(cx - 1, floor_y + 1, cz - 1, cx + 1, floor_y + 1, cz + 1, RED_CARPET)
    # 中央灯笼柱
    b.fill(cx, floor_y + 1, cz, cx, floor_y + 3, cz, P["pillar"])
    b.setblock(cx, floor_y + 4, cz, f"{LANTERN}[hanging=false]")

    print(f"  牡丹亭 done. Commands: {b.cmd_count}")


def build_peony_rail(b):
    """2. 芍药阑 — 花圃围栏，不是建筑，只是围栏+花
    11x9 区域，crimson_fence 围合，内部种花
    """
    bldg = cfg.PEONY_RAIL
    print(f"=== Building {bldg['name']} ===")

    x1, z1, x2, z2 = _get_building_bounds(bldg)
    gy = bldg["ground_y"]

    # 地面铺草
    b.fill(x1, gy, z1, x2, gy, z2, "minecraft:grass_block")

    # 四周围栏 (留南面入口3格)
    cx = (x1 + x2) // 2
    # 北
    b.fill(x1, gy + 1, z1, x2, gy + 1, z1, RAIL)
    # 南 (留3格入口)
    b.fill(x1, gy + 1, z2, cx - 2, gy + 1, z2, RAIL)
    b.fill(cx + 2, gy + 1, z2, x2, gy + 1, z2, RAIL)
    # 西
    b.fill(x1, gy + 1, z1, x1, gy + 1, z2, RAIL)
    # 东
    b.fill(x2, gy + 1, z1, x2, gy + 1, z2, RAIL)

    # 内部种牡丹 (peony) — 交错种植
    for x in range(x1 + 1, x2, 2):
        for z in range(z1 + 1, z2, 2):
            b.setblock(x, gy + 1, z, PEONY_FLOWER)

    # 四角灯笼
    for lx, lz in [(x1, z1), (x1, z2), (x2, z1), (x2, z2)]:
        b.setblock(lx, gy + 2, lz, f"{LANTERN}[hanging=false]")

    print(f"  芍药阑 done. Commands: {b.cmd_count}")


def build_taihu_rocks(b):
    """14. 太湖石组 — 假山石景
    用 dripstone_block + calcite 堆叠不规则石头
    """
    bldg = cfg.TAIHU_ROCKS
    print(f"=== Building {bldg['name']} ===")

    x1, z1, x2, z2 = _get_building_bounds(bldg)
    gy = bldg["ground_y"]
    cx = bldg["cx"]
    cz = bldg["cz"]

    # 主峰 (中央偏东, 高6格)
    peak_x, peak_z = cx + 2, cz
    for dy in range(7):
        # 逐层收缩
        r = max(1, 3 - dy // 2)
        for dx in range(-r, r + 1):
            for dz in range(-r, r + 1):
                if abs(dx) + abs(dz) <= r + 1:
                    block = TAIHU_MAIN if (dx + dz + dy) % 3 != 0 else TAIHU_WHITE
                    b.setblock(peak_x + dx, gy + dy + 1, peak_z + dz, block)

    # 次峰 (西侧, 高4格)
    for dy in range(5):
        r = max(1, 2 - dy // 2)
        for dx in range(-r, r + 1):
            for dz in range(-r, r + 1):
                if abs(dx) + abs(dz) <= r:
                    block = TAIHU_WHITE if dy % 2 == 0 else TAIHU_MAIN
                    b.setblock(cx - 3 + dx, gy + dy + 1, cz - 1 + dz, block)

    # 散石 (几块独立小石头)
    for sx, sz, sh in [(cx - 5, cz + 2, 2), (cx + 5, cz - 3, 3), (cx, cz + 4, 2)]:
        for dy in range(sh):
            b.setblock(sx, gy + dy + 1, sz, TAIHU_MAIN)
            if dy == 0:
                b.setblock(sx + 1, gy + 1, sz, TAIHU_WHITE)

    print(f"  太湖石组 done. Commands: {b.cmd_count}")


def build_swing(b):
    """13. 秋千 — 3x3 区域，两根柱子+横梁+链子"""
    bldg = cfg.SWING
    print(f"=== Building {bldg['name']} ===")

    cx = bldg["cx"]
    cz = bldg["cz"]
    gy = bldg["ground_y"]

    # 两根柱子 (x 方向两端)
    for px in [cx - 1, cx + 1]:
        b.fill(px, gy + 1, cz, px, gy + 5, cz, PILLAR)

    # 横梁
    b.fill(cx - 1, gy + 5, cz, cx + 1, gy + 5, cz, BEAM)

    # 链子 (chain) — 中间悬挂
    for dy in range(1, 4):
        b.setblock(cx, gy + 5 - dy, cz, "minecraft:chain")

    # 座板 (spruce_slab)
    b.setblock(cx, gy + 1, cz, _slab("minecraft:spruce_slab", "bottom"))

    print(f"  秋千 done. Commands: {b.cmd_count}")


def build_plum_tree(b):
    """15. 大梅树 — 一棵大树 (cherry_log + cherry_leaves)"""
    bldg = cfg.PLUM_TREE
    print(f"=== Building {bldg['name']} ===")

    x = bldg["x"]
    z = bldg["z"]
    gy = bldg["ground_y"]

    # 树干 (cherry_log, 高5格)
    b.fill(x, gy + 1, z, x, gy + 5, z, CHERRY_LOG)

    # 树冠 (cherry_leaves, persistent=true)
    # 球形树冠, 半径3, 中心在 gy+6
    crown_y = gy + 6
    for dy in range(-2, 3):
        r = 3 - abs(dy)
        if r < 1:
            r = 1
        for dx in range(-r, r + 1):
            for dz in range(-r, r + 1):
                if dx * dx + dz * dz <= r * r + 1:
                    b.setblock(x + dx, crown_y + dy, z + dz, CHERRY_LVS)

    # 在 gy+5 层也加一圈叶子
    for dx in range(-2, 3):
        for dz in range(-2, 3):
            if abs(dx) + abs(dz) <= 3 and not (dx == 0 and dz == 0):
                b.setblock(x + dx, gy + 5, z + dz, CHERRY_LVS)

    print(f"  大梅树 done. Commands: {b.cmd_count}")


def build_tumi_trellis(b):
    """12. 荼蘼花架 — 12x4 花架，柱+横梁+叶顶"""
    bldg = cfg.TUMI_TRELLIS
    print(f"=== Building {bldg['name']} ===")

    x1, z1, x2, z2 = _get_building_bounds(bldg)
    gy = bldg["ground_y"]

    # 地面铺石
    b.fill(x1, gy, z1, x2, gy, z2, FLOOR)

    # 柱子 (每3格一根, 两侧)
    pillar_h = 4
    for x in range(x1, x2 + 1, 3):
        for z in [z1, z2]:
            b.setblock(x, gy, z, BASE_COL)  # 柱础
            b.fill(x, gy + 1, z, x, gy + pillar_h, z, PILLAR)

    # 横梁
    b.fill(x1, gy + pillar_h, z1, x2, gy + pillar_h, z1, BEAM)
    b.fill(x1, gy + pillar_h, z2, x2, gy + pillar_h, z2, BEAM)
    # 纵梁 (连接两侧)
    for x in range(x1, x2 + 1, 3):
        b.fill(x, gy + pillar_h, z1, x, gy + pillar_h, z2, BEAM)

    # 顶部叶子覆盖 (oak_leaves persistent=true)
    b.fill(x1, gy + pillar_h + 1, z1, x2, gy + pillar_h + 1, z2, OAK_LVS)

    # 两端灯笼
    b.setblock(x1, gy + pillar_h - 1, (z1 + z2) // 2, f"{LANTERN}[hanging=true]")
    b.setblock(x2, gy + pillar_h - 1, (z1 + z2) // 2, f"{LANTERN}[hanging=true]")

    print(f"  荼蘼花架 done. Commands: {b.cmd_count}")


def build_painted_boat(b):
    """16. 画船 — 水面上的装饰小船"""
    bldg = cfg.PAINTED_BOAT
    print(f"=== Building {bldg['name']} ===")

    x1, z1, x2, z2 = _get_building_bounds(bldg)
    gy = bldg["ground_y"]  # water surface = -61
    cx = bldg["cx"]
    cz = bldg["cz"]

    # 船底 (spruce_planks, 在水面层)
    b.fill(x1, gy, z1 + 1, x2, gy, z2 - 1, FLOOR_WOOD)

    # 船头/船尾 (收窄)
    b.fill(cx, gy, z1, cx, gy, z1, FLOOR_WOOD)      # 船头尖
    b.fill(cx, gy, z2, cx, gy, z2, FLOOR_WOOD)      # 船尾尖

    # 船舷 (两侧栏杆, 高1格)
    b.fill(x1, gy + 1, z1 + 1, x1, gy + 1, z2 - 1, "minecraft:spruce_fence")
    b.fill(x2, gy + 1, z1 + 1, x2, gy + 1, z2 - 1, "minecraft:spruce_fence")

    # 船篷 (中间段, spruce_slab)
    pz1 = cz - 2
    pz2 = cz + 2
    # 篷柱
    for px in [x1, x2]:
        for pz in [pz1, pz2]:
            b.fill(px, gy + 1, pz, px, gy + 3, pz, PILLAR)
    # 篷顶
    b.fill(x1 - 1, gy + 3, pz1, x2 + 1, gy + 3, pz2,
           _slab("minecraft:spruce_slab", "bottom"))

    # 灯笼
    b.setblock(cx, gy + 2, pz1, f"{LANTERN}[hanging=true]")

    print(f"  画船 done. Commands: {b.cmd_count}")


def build_stone_boat(b):
    """17. 石舫 — 石质仿船建筑, 半临水"""
    bldg = cfg.STONE_BOAT
    print(f"=== Building {bldg['name']} ===")

    x1, z1, x2, z2 = _get_building_bounds(bldg)
    gy = bldg["ground_y"]
    cx = bldg["cx"]
    cz = bldg["cz"]

    # 船体基座 (stone_bricks, 从水面到地面+1)
    water_y = cfg.WATER_SURFACE_Y
    b.fill(x1, water_y, z1, x2, gy, z2, BASE)

    # 甲板地面
    b.fill(x1, gy + 1, z1, x2, gy + 1, z2, FLOOR)

    # 船头尖 (南端收窄)
    b.fill(cx, gy, z2 + 1, cx, gy + 1, z2 + 2, BASE)
    b.setblock(cx, gy + 1, z2 + 2, _stair(BASE_STEP, "north"))

    # 船尾 (北端方正, 有小楼)
    # 船楼 (北段 4 格)
    cabin_z1 = z1
    cabin_z2 = z1 + 3
    # 墙
    b.fill(x1, gy + 2, cabin_z1, x2, gy + 4, cabin_z2, WALL_BLOCK)
    # 内部挖空
    b.fill(x1 + 1, gy + 2, cabin_z1 + 1, x2 - 1, gy + 4, cabin_z2 - 1, AIR)
    # 南面开门
    b.fill(cx, gy + 2, cabin_z2, cx, gy + 3, cabin_z2, AIR)
    # 窗
    b.fill(x1, gy + 3, cabin_z1 + 1, x1, gy + 3, cabin_z2 - 1, WINDOW)
    b.fill(x2, gy + 3, cabin_z1 + 1, x2, gy + 3, cabin_z2 - 1, WINDOW)

    # 船楼屋顶
    b.fill(x1 - 1, gy + 5, cabin_z1 - 1, x2 + 1, gy + 5, cabin_z2 + 1,
           _slab(ROOF_SLAB, "bottom"))

    # 甲板栏杆 (敞开区)
    b.fill(x1, gy + 2, cabin_z2 + 1, x1, gy + 2, z2, RAIL)
    b.fill(x2, gy + 2, cabin_z2 + 1, x2, gy + 2, z2, RAIL)

    # 灯笼
    b.setblock(cx, gy + 4, cabin_z1 + 1, f"{LANTERN}[hanging=true]")

    print(f"  石舫 done. Commands: {b.cmd_count}")


def build_courtyard(b):
    """8. 小庭深院 — 围合庭院，不是建筑而是围墙+地面"""
    bldg = cfg.COURTYARD
    print(f"=== Building {bldg['name']} ===")

    x1, z1, x2, z2 = _get_building_bounds(bldg)
    gy = bldg["ground_y"]

    # 地面
    b.fill(x1, gy, z1, x2, gy, z2, FLOOR)
    # 条纹铺装
    for z in range(z1, z2 + 1):
        if (z - z1) % 2 == 1:
            b.fill(x1, gy, z, x2, gy, z, BASE_COL)

    # 四周白墙 (高3格, 南北留3格入口)
    cx = (x1 + x2) // 2
    wall_h = 3
    # 东墙
    b.fill(x2, gy + 1, z1, x2, gy + wall_h, z2, WALL_BLOCK)
    # 西墙
    b.fill(x1, gy + 1, z1, x1, gy + wall_h, z2, WALL_BLOCK)
    # 北墙 (留入口)
    b.fill(x1, gy + 1, z1, cx - 2, gy + wall_h, z1, WALL_BLOCK)
    b.fill(cx + 2, gy + 1, z1, x2, gy + wall_h, z1, WALL_BLOCK)
    # 南墙 (留入口)
    b.fill(x1, gy + 1, z2, cx - 2, gy + wall_h, z2, WALL_BLOCK)
    b.fill(cx + 2, gy + 1, z2, x2, gy + wall_h, z2, WALL_BLOCK)

    # 墙顶压瓦
    b.fill(x1, gy + wall_h + 1, z1, x2, gy + wall_h + 1, z1,
           _slab(WALL_CAP, "bottom"))
    b.fill(x1, gy + wall_h + 1, z2, x2, gy + wall_h + 1, z2,
           _slab(WALL_CAP, "bottom"))
    b.fill(x1, gy + wall_h + 1, z1, x1, gy + wall_h + 1, z2,
           _slab(WALL_CAP, "bottom"))
    b.fill(x2, gy + wall_h + 1, z1, x2, gy + wall_h + 1, z2,
           _slab(WALL_CAP, "bottom"))

    # 庭院中央一棵小树
    tree_x, tree_z = cx, (z1 + z2) // 2
    b.fill(tree_x, gy + 1, tree_z, tree_x, gy + 3, tree_z, OAK_LOG)
    for dx in range(-2, 3):
        for dz in range(-2, 3):
            if abs(dx) + abs(dz) <= 3:
                b.setblock(tree_x + dx, gy + 4, tree_z + dz, OAK_LVS)
                if abs(dx) + abs(dz) <= 2:
                    b.setblock(tree_x + dx, gy + 5, tree_z + dz, OAK_LVS)

    # 灯笼 (入口两侧)
    b.setblock(cx - 2, gy + 2, z1, f"{LANTERN}[hanging=false]")
    b.setblock(cx + 2, gy + 2, z1, f"{LANTERN}[hanging=false]")
    b.setblock(cx - 2, gy + 2, z2, f"{LANTERN}[hanging=false]")
    b.setblock(cx + 2, gy + 2, z2, f"{LANTERN}[hanging=false]")

    print(f"  小庭深院 done. Commands: {b.cmd_count}")


def build_gate(b):
    """7. 入口门厅 — 15x9 带屋顶的门厅建筑"""
    bldg = cfg.GATE
    print(f"=== Building {bldg['name']} ===")

    # 标准建筑流程，但加门厅特有元素
    build_standard_building(b, bldg)

    x1, z1, x2, z2 = _get_building_bounds(bldg)
    gy = bldg["ground_y"]
    cx = (x1 + x2) // 2
    floor_y = gy + 1  # 台基后的地面

    # 门厅额外: 大门（南面中央5格宽，用 dark_oak_planks 做门框）
    b.fill(cx - 2, floor_y + 1, z2, cx + 2, floor_y + 3, z2, BEAM)
    b.fill(cx - 1, floor_y + 1, z2, cx + 1, floor_y + 2, z2, AIR)  # 门洞

    # 北面也开大门
    b.fill(cx - 2, floor_y + 1, z1, cx + 2, floor_y + 3, z1, BEAM)
    b.fill(cx - 1, floor_y + 1, z1, cx + 1, floor_y + 2, z1, AIR)

    # 匾额位置 (南门上方)
    b.setblock(cx, floor_y + 3, z2, BEAM_LOG)

    print(f"  入口门厅 done. Commands: {b.cmd_count}")


def build_screen_wall(b):
    """影壁 — 入口门厅后的遮挡墙"""
    sw = cfg.ENTRANCE["screen_wall"]
    print(f"=== Building 影壁 ===")

    cx = sw["cx"]
    cz = sw["cz"]
    half_w = sw["width"] // 2
    h = sw["height"]
    gy = cfg.BUILD_Y

    x1 = cx - half_w
    x2 = cx + half_w

    # 墙基 (石砖)
    b.fill(x1, gy, cz, x2, gy, cz, BASE)
    # 墙身 (白色混凝土)
    b.fill(x1, gy + 1, cz, x2, gy + h - 1, cz, WALL_BLOCK)
    # 墙顶 (石砖半砖)
    b.fill(x1, gy + h, cz, x2, gy + h, cz, _slab(WALL_CAP, "bottom"))

    # 中央装饰 (一个 dark_oak 匾)
    b.setblock(cx, gy + 2, cz, BEAM_LOG)

    print(f"  影壁 done. Commands: {b.cmd_count}")


# ═══════════════════════════════════════════
# 主建造函数
# ═══════════════════════════════════════════

def build_all_buildings(b):
    """按优先级顺序建造所有建筑"""

    # ── P0: 核心梦境建筑 ──
    build_peony_pavilion(b)
    build_peony_rail(b)

    # ── P1: 主要建筑 ──
    # 远香堂 (最大体量, 歇山顶)
    print(f"=== Building 远香堂 (P1 主厅) ===")
    build_standard_building(b, cfg.YUAN_XIANG)
    print(f"  远香堂 done. Commands: {b.cmd_count}")

    # 翠轩 (悬山顶)
    print(f"=== Building 翠轩 (P1) ===")
    build_standard_building(b, cfg.CUI_XUAN)
    print(f"  翠轩 done. Commands: {b.cmd_count}")

    # 池馆 (水榭)
    print(f"=== Building 池馆 (P1) ===")
    build_standard_building(b, cfg.CHI_GUAN)
    print(f"  池馆 done. Commands: {b.cmd_count}")

    # 濯缨水阁
    print(f"=== Building 濯缨水阁 (P1) ===")
    build_standard_building(b, cfg.ZHUO_YING)
    print(f"  濯缨水阁 done. Commands: {b.cmd_count}")

    # 入口门厅 (特殊处理)
    build_gate(b)

    # 小庭深院 (围合庭院)
    build_courtyard(b)

    # 太湖石组
    build_taihu_rocks(b)

    # ── P2: 中小型建筑 ──

    # 半亭 (东南角)
    print(f"=== Building 半亭 (P2) ===")
    build_standard_building(b, cfg.HALF_PAVILION_SE)
    print(f"  半亭 done. Commands: {b.cmd_count}")

    # 曲廊亭 (东岸)
    print(f"=== Building 曲廊亭 (P2) ===")
    build_standard_building(b, cfg.CORRIDOR_PAVILION_E)
    print(f"  曲廊亭 done. Commands: {b.cmd_count}")

    # 听雨轩
    print(f"=== Building 听雨轩 (P2) ===")
    build_standard_building(b, cfg.TING_YU_XUAN)
    print(f"  听雨轩 done. Commands: {b.cmd_count}")

    # 荼蘼花架
    build_tumi_trellis(b)

    # 秋千
    build_swing(b)

    # 大梅树
    build_plum_tree(b)

    # 画船
    build_painted_boat(b)

    # 石舫
    build_stone_boat(b)

    # 梅花庵观
    print(f"=== Building 梅花庵观 (P2) ===")
    build_standard_building(b, cfg.PLUM_HERMITAGE)
    print(f"  梅花庵观 done. Commands: {b.cmd_count}")

    # 闺塾
    print(f"=== Building 闺塾 (P2) ===")
    build_standard_building(b, cfg.GUI_SHU)
    print(f"  闺塾 done. Commands: {b.cmd_count}")

    # 影壁
    build_screen_wall(b)

    print(f"\n=== All {19} buildings complete! Total commands: {b.cmd_count} ===")


# ═══════════════════════════════════════════
# 入口
# ═══════════════════════════════════════════

if __name__ == "__main__":
    with MinecraftBuilder() as b:
        build_all_buildings(b)
        print(f"Done! {b.cmd_count} commands")
