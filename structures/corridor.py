"""曲廊（画廊）系统 — 中式园林动线骨架

"画廊金粉半零星" "回廊那厢"
曲径通幽，步移景异。L形+折返路线，从入口沿池塘西岸绕至翠轩，
再北折通向牡丹亭区域，共6段直线+5个转角。

路线：
  A(38,38) → B(20,38) → C(20,28) → D(20,15) → E(35,15) → F(35,10) → G(45,10)
  转角：B, C, D, E, F（至少3次转弯，实际5次）

截面：外宽3格（中间走道 + 两侧柱/栏杆）
  柱子：每隔3格，金合欢去皮原木，高3格
  柱间：金合欢栅栏，高1格
  屋顶：深板岩瓦片半砖，宽3格
  地面：走道smooth_stone，柱位stone_bricks
  横梁：柱顶深色橡木木板
"""

import sys; sys.path.insert(0, '/Users/lambertlin/minecraft-server/scripts')
from builder import MinecraftBuilder
from blocks import PALETTE, GROUND_Y, BUILD_Y


# ── 方块常量 ──
PILLAR     = PALETTE["pillar"]       # stripped_acacia_log
BEAM       = PALETTE["beam"]         # dark_oak_planks
RAIL       = PALETTE["rail"]         # acacia_fence
ROOF_SLAB  = PALETTE["roof_slab"]    # deepslate_tile_slab
ROOF_STAIR = PALETTE["roof"]         # deepslate_tile_stairs
FLOOR      = PALETTE["floor"]        # smooth_stone
FLOOR_ALT  = PALETTE["floor_alt"]    # stone_bricks
LANTERN    = PALETTE["lantern"]      # lantern
BASE_COL   = PALETTE["base_col"]     # stone_slab (柱础)

# ── 结构参数 ──
PILLAR_H     = 3     # 柱高（地面以上）
PILLAR_SPACE = 3     # 柱间距
CORRIDOR_W   = 3     # 廊道总宽（1走道 + 2柱位）


def _build_corridor_segment(b: MinecraftBuilder, x1: int, z1: int,
                            x2: int, z2: int, axis: str, y: int):
    """建造一段直线廊道。

    Args:
        x1, z1: 起点 XZ
        x2, z2: 终点 XZ
        axis: 'x' = 东西走向（柱在南北两侧），'z' = 南北走向（柱在东西两侧）
        y: 地面Y坐标（BUILD_Y）
    """
    if axis == 'x':
        _build_segment_x(b, x1, z1, x2, z2, y)
    else:
        _build_segment_z(b, x1, z1, x2, z2, y)


def _build_segment_x(b: MinecraftBuilder, x1: int, z1: int,
                     x2: int, z2: int, y: int):
    """东西走向廊段：沿X轴走，柱子在南北两侧。

    走道中心在 z=z1，柱子在 z1-1 和 z1+1。
    """
    # 确保 x1 < x2
    sx, ex = min(x1, x2), max(x1, x2)
    z_center = z1  # 走道中心
    z_south = z_center + 1   # 南侧柱位
    z_north = z_center - 1   # 北侧柱位

    # ── 地面 ──
    # 走道中心：smooth_stone
    b.fill(sx, y, z_center, ex, y, z_center, FLOOR)
    # 两侧柱位：stone_bricks
    b.fill(sx, y, z_south, ex, y, z_south, FLOOR_ALT)
    b.fill(sx, y, z_north, ex, y, z_north, FLOOR_ALT)

    # ── 柱子、栏杆、横梁、屋顶 ──
    # 每隔 PILLAR_SPACE 格放柱子
    length = ex - sx
    for i in range(0, length + 1, PILLAR_SPACE):
        px = sx + i
        if px > ex:
            break
        _place_pillar_pair_x(b, px, z_center, y)

    # 末端柱（如果最后一根不在终点，补一根）
    last_pillar_x = sx + (length // PILLAR_SPACE) * PILLAR_SPACE
    if last_pillar_x < ex:
        _place_pillar_pair_x(b, ex, z_center, y)

    # ── 柱间栏杆 ──
    _fill_rails_between_pillars_x(b, sx, ex, z_south, z_north, y)

    # ── 屋顶（半砖铺顶，宽3格）──
    roof_y = y + PILLAR_H + 1  # 柱顶上方1格
    b.fill(sx, roof_y, z_north, ex, roof_y, z_south,
           f'{ROOF_SLAB}[type=bottom]')


def _build_segment_z(b: MinecraftBuilder, x1: int, z1: int,
                     x2: int, z2: int, y: int):
    """南北走向廊段：沿Z轴走，柱子在东西两侧。

    走道中心在 x=x1，柱子在 x1-1 和 x1+1。
    """
    # 确保 z 顺序正确
    sz, ez = min(z1, z2), max(z1, z2)
    x_center = x1  # 走道中心
    x_east = x_center + 1   # 东侧柱位
    x_west = x_center - 1   # 西侧柱位

    # ── 地面 ──
    b.fill(x_center, y, sz, x_center, y, ez, FLOOR)
    b.fill(x_east, y, sz, x_east, y, ez, FLOOR_ALT)
    b.fill(x_west, y, sz, x_west, y, ez, FLOOR_ALT)

    # ── 柱子 ──
    length = ez - sz
    for i in range(0, length + 1, PILLAR_SPACE):
        pz = sz + i
        if pz > ez:
            break
        _place_pillar_pair_z(b, x_center, pz, y)

    # 末端柱
    last_pillar_z = sz + (length // PILLAR_SPACE) * PILLAR_SPACE
    if last_pillar_z < ez:
        _place_pillar_pair_z(b, x_center, ez, y)

    # ── 柱间栏杆 ──
    _fill_rails_between_pillars_z(b, sz, ez, x_east, x_west, y)

    # ── 屋顶 ──
    roof_y = y + PILLAR_H + 1
    b.fill(x_west, roof_y, sz, x_east, roof_y, ez,
           f'{ROOF_SLAB}[type=bottom]')


# ── 柱子放置辅助 ──

def _place_pillar_pair_x(b: MinecraftBuilder, px: int, z_center: int, y: int):
    """东西走向段：在px处放南北两根柱子 + 柱础 + 横梁。"""
    z_south = z_center + 1
    z_north = z_center - 1
    beam_y = y + PILLAR_H  # 柱顶层（第3格）= 横梁层

    for pz in (z_south, z_north):
        # 柱础
        b.setblock(px, y, pz, BASE_COL)
        # 柱身 3格（y+1 到 y+3）
        for dy in range(1, PILLAR_H + 1):
            b.setblock(px, y + dy, pz, PILLAR)

    # 横梁连接南北柱（在柱顶层，跨走道）
    b.fill(px, beam_y, z_north, px, beam_y, z_south, BEAM)


def _place_pillar_pair_z(b: MinecraftBuilder, x_center: int, pz: int, y: int):
    """南北走向段：在pz处放东西两根柱子 + 柱础 + 横梁。"""
    x_east = x_center + 1
    x_west = x_center - 1
    beam_y = y + PILLAR_H

    for px in (x_east, x_west):
        b.setblock(px, y, pz, BASE_COL)
        for dy in range(1, PILLAR_H + 1):
            b.setblock(px, y + dy, pz, PILLAR)

    # 横梁连接东西柱
    b.fill(x_west, beam_y, pz, x_east, beam_y, pz, BEAM)


# ── 柱间栏杆填充 ──

def _fill_rails_between_pillars_x(b: MinecraftBuilder,
                                   sx: int, ex: int,
                                   z_south: int, z_north: int, y: int):
    """东西走向段：在柱间填充栏杆（跳过柱位）。"""
    rail_y = y + 1  # 栏杆在地面上方1格
    pillar_xs = set()
    length = ex - sx
    for i in range(0, length + 1, PILLAR_SPACE):
        pillar_xs.add(sx + i)
    # 如果末端不是柱位也加上
    last_p = sx + (length // PILLAR_SPACE) * PILLAR_SPACE
    if last_p < ex:
        pillar_xs.add(ex)

    for x in range(sx, ex + 1):
        if x not in pillar_xs:
            b.setblock(x, rail_y, z_south, RAIL)
            b.setblock(x, rail_y, z_north, RAIL)


def _fill_rails_between_pillars_z(b: MinecraftBuilder,
                                   sz: int, ez: int,
                                   x_east: int, x_west: int, y: int):
    """南北走向段：在柱间填充栏杆（跳过柱位）。"""
    rail_y = y + 1
    pillar_zs = set()
    length = ez - sz
    for i in range(0, length + 1, PILLAR_SPACE):
        pillar_zs.add(sz + i)
    last_p = sz + (length // PILLAR_SPACE) * PILLAR_SPACE
    if last_p < ez:
        pillar_zs.add(ez)

    for z in range(sz, ez + 1):
        if z not in pillar_zs:
            b.setblock(x_east, rail_y, z, RAIL)
            b.setblock(x_west, rail_y, z, RAIL)


# ── 转角处理 ──

def _build_corner(b: MinecraftBuilder, cx: int, cz: int, y: int,
                  from_axis: str, to_axis: str,
                  from_dir: int, to_dir: int):
    """建造转角。

    在转角点放置：
      1. 3x3 地面（走道+柱位全覆盖）
      2. 角柱（4根，覆盖转角区域的4角）
      3. 角上屋顶（3x3半砖 + 4角楼梯转角）
      4. 横梁
      5. 内角灯笼

    Args:
        cx, cz: 转角中心（走道中心线交点）
        from_axis: 来向轴 'x' 或 'z'
        to_axis: 去向轴
        from_dir: 来向方向（+1或-1，表示沿轴正/负方向来的）
        to_dir: 去向方向（+1或-1，表示沿轴正/负方向去的）
    """
    beam_y = y + PILLAR_H
    roof_y = y + PILLAR_H + 1

    # ── 3x3 地面 ──
    b.fill(cx - 1, y, cz - 1, cx + 1, y, cz + 1, FLOOR_ALT)
    b.setblock(cx, y, cz, FLOOR)  # 中心走道

    # ── 四角柱 ──
    corners = [
        (cx - 1, cz - 1),  # 西北
        (cx + 1, cz - 1),  # 东北
        (cx - 1, cz + 1),  # 西南
        (cx + 1, cz + 1),  # 东南
    ]
    for pcx, pcz in corners:
        b.setblock(pcx, y, pcz, BASE_COL)
        for dy in range(1, PILLAR_H + 1):
            b.setblock(pcx, y + dy, pcz, PILLAR)

    # ── 横梁（十字形，连接四根角柱）──
    # 东西向横梁
    b.fill(cx - 1, beam_y, cz - 1, cx + 1, beam_y, cz - 1, BEAM)
    b.fill(cx - 1, beam_y, cz + 1, cx + 1, beam_y, cz + 1, BEAM)
    # 南北向横梁
    b.fill(cx - 1, beam_y, cz - 1, cx - 1, beam_y, cz + 1, BEAM)
    b.fill(cx + 1, beam_y, cz - 1, cx + 1, beam_y, cz + 1, BEAM)
    # 中心横梁
    b.setblock(cx, beam_y, cz, BEAM)

    # ── 屋顶（3x3半砖 + 转角楼梯）──
    b.fill(cx - 1, roof_y, cz - 1, cx + 1, roof_y, cz + 1,
           f'{ROOF_SLAB}[type=bottom]')

    # 转角楼梯：根据来去方向，判断外角位置，放置 outer 楼梯
    # 确定廊道"内侧"（转弯内角）方向以放灯笼
    _place_corner_roof_stairs(b, cx, cz, roof_y, from_axis, to_axis,
                              from_dir, to_dir)

    # ── 内角灯笼 ──
    _place_corner_lantern(b, cx, cz, beam_y, from_axis, to_axis,
                          from_dir, to_dir)


def _place_corner_roof_stairs(b: MinecraftBuilder, cx: int, cz: int,
                               roof_y: int, from_axis: str, to_axis: str,
                               from_dir: int, to_dir: int):
    """在转角屋顶的外侧角放置楼梯方块的转角形态。

    外侧角 = 转弯外侧的那个角，用 outer_left/outer_right 楼梯。
    """
    # 确定外角坐标：外角在两条廊道的外侧交点
    # from_axis='x', from_dir=+1 表示从东向西走来（X减小方向来的）
    #   → 来向的外侧垂直偏移
    # to_axis='z', to_dir=-1 表示向北走去（Z减小方向）
    #   → 去向的外侧垂直偏移

    # 简化：直接在四角都放楼梯，让 Minecraft 自动连接
    # 北面边
    b.setblock(cx - 1, roof_y, cz - 1,
               f'{ROOF_STAIR}[facing=south,half=bottom,shape=outer_right]')
    b.setblock(cx + 1, roof_y, cz - 1,
               f'{ROOF_STAIR}[facing=south,half=bottom,shape=outer_left]')
    # 南面边
    b.setblock(cx - 1, roof_y, cz + 1,
               f'{ROOF_STAIR}[facing=north,half=bottom,shape=outer_left]')
    b.setblock(cx + 1, roof_y, cz + 1,
               f'{ROOF_STAIR}[facing=north,half=bottom,shape=outer_right]')


def _place_corner_lantern(b: MinecraftBuilder, cx: int, cz: int,
                           beam_y: int, from_axis: str, to_axis: str,
                           from_dir: int, to_dir: int):
    """在转角内侧挂灯笼。

    内侧 = 转弯半径小的那一侧。
    灯笼挂在横梁下方（beam_y - 1），位于转角中心。
    """
    # 内角方向计算
    # from_axis='x', from_dir=-1 (向西走来) → 来向垂直=Z方向
    # to_axis='z', to_dir=-1 (向北走去) → 去向垂直=X方向
    # 内角 = 来向的"右手边" or "左手边" 取决于转弯方向
    #
    # 简化处理：灯笼放在转角中心正下方
    b.setblock(cx, beam_y - 1, cz, f'{LANTERN}[hanging=true]')


# ── C点翠轩侧门 ──

def _build_side_entrance(b: MinecraftBuilder, cx: int, cz: int, y: int):
    """在C点附近开一个通向翠轩的侧门/岔道标记。

    翠轩在 X=12，C点在 X=20, Z=28。
    在廊道西侧（x=19）开口，放置门框和路径指引。
    """
    # 西侧栏杆开口：移除C点附近的西侧栏杆，改为栅栏门
    gate_x = cx - 1  # 西侧柱位
    gate_z = cz       # C点Z坐标

    # 栅栏门（面向东西方向）
    b.setblock(gate_x, y + 1, gate_z,
               f'{PALETTE["rail_gate"]}[facing=west,open=false]')

    # 门两侧加柱标记
    b.setblock(gate_x, y + 1, gate_z - 1, PILLAR)
    b.setblock(gate_x, y + 1, gate_z + 1, PILLAR)
    b.setblock(gate_x, y + 2, gate_z - 1, PILLAR)
    b.setblock(gate_x, y + 2, gate_z + 1, PILLAR)

    # 门头横梁
    b.fill(gate_x, y + 3, gate_z - 1, gate_x, y + 3, gate_z + 1, BEAM)

    # 从门口向翠轩铺一小段石径（3格，x=18~16）
    for px in range(gate_x - 3, gate_x):
        b.setblock(px, y, gate_z, PALETTE["path"])


# ── 主函数 ──

def build_corridors(b: MinecraftBuilder):
    """建造完整曲廊系统。"""
    print("=== 曲廊系统 ===")
    y = BUILD_Y  # -60，地面层

    # 路段定义：((x1,z1), (x2,z2), axis)
    segments = [
        ((38, 38), (20, 38), 'x'),   # A→B 向西
        ((20, 38), (20, 28), 'z'),   # B→C 向北（经过翠轩）
        ((20, 28), (20, 15), 'z'),   # C→D 继续北走
        ((20, 15), (35, 15), 'x'),   # D→E 向东转
        ((35, 15), (35, 10), 'z'),   # E→F 向北
        ((35, 10), (45, 10), 'x'),   # F→G 向东接近牡丹亭
    ]

    # 转角定义：(转角中心坐标, 来向轴, 去向轴, 来向方向, 去向方向)
    # 方向：+1=沿轴正方向运动，-1=沿轴负方向运动
    corners = [
        # B(20,38): A→B向西(x负方向)，B→C向北(z负方向)
        (20, 38, 'x', 'z', -1, -1),
        # C(20,28): B→C向北(z负)，C→D向北(z负) — 直行，但这里是翠轩侧门点
        # C点不是转角（同方向），跳过转角处理，改为侧门
        # D(20,15): C→D向北(z负)，D→E向东(x正)
        (20, 15, 'z', 'x', -1, +1),
        # E(35,15): D→E向东(x正)，E→F向北(z负)
        (35, 15, 'x', 'z', +1, -1),
        # F(35,10): E→F向北(z负)，F→G向东(x正)
        (35, 10, 'z', 'x', -1, +1),
    ]

    # ── 1. 建造各直线段 ──
    print("  [1/4] 廊道直线段...")
    for i, ((x1, z1), (x2, z2), axis) in enumerate(segments):
        seg_label = chr(65 + i) + "→" + chr(65 + i + 1)  # A→B, B→C, ...
        print(f"    段 {seg_label}: ({x1},{z1})→({x2},{z2}) [{axis}轴]")
        _build_corridor_segment(b, x1, z1, x2, z2, axis, y)

    # ── 2. 建造转角 ──
    print("  [2/4] 转角...")
    for cx, cz, fa, ta, fd, td in corners:
        print(f"    转角 ({cx},{cz})")
        _build_corner(b, cx, cz, y, fa, ta, fd, td)

    # ── 3. C点翠轩侧门 ──
    print("  [3/4] 翠轩侧门...")
    _build_side_entrance(b, cx=20, cz=28, y=y)

    # ── 4. 起终点装饰 ──
    print("  [4/4] 起终点装饰...")
    _build_endpoints(b, y)

    # 注册边界框
    b.register_bbox("corridors", 16, GROUND_Y, 8, 46, BUILD_Y + 5, 40)

    print("  曲廊建造完成！")


def _build_endpoints(b: MinecraftBuilder, y: int):
    """起点(A)和终点(G)的装饰处理。"""
    beam_y = y + PILLAR_H
    roof_y = y + PILLAR_H + 1

    # ── A点(38,38)：入口端 ──
    # 放两根入口柱 + 挂灯笼
    ax, az = 38, 38
    # 入口柱（南北两侧）
    for pz in (az - 1, az + 1):
        b.setblock(ax + 1, y, pz, BASE_COL)
        for dy in range(1, PILLAR_H + 1):
            b.setblock(ax + 1, y + dy, pz, PILLAR)
    # 入口横梁
    b.fill(ax + 1, beam_y, az - 1, ax + 1, beam_y, az + 1, BEAM)
    # 入口灯笼
    b.setblock(ax + 1, beam_y - 1, az, f'{LANTERN}[hanging=true]')

    # ── G点(45,10)：终点端（朝牡丹亭方向）──
    gx, gz = 45, 10
    # 终点柱（南北两侧）
    for pz in (gz - 1, gz + 1):
        b.setblock(gx + 1, y, pz, BASE_COL)
        for dy in range(1, PILLAR_H + 1):
            b.setblock(gx + 1, y + dy, pz, PILLAR)
    # 终点横梁
    b.fill(gx + 1, beam_y, gz - 1, gx + 1, beam_y, gz + 1, BEAM)
    # 终点灯笼
    b.setblock(gx + 1, beam_y - 1, gz, f'{LANTERN}[hanging=true]')


if __name__ == "__main__":
    with MinecraftBuilder() as b:
        build_corridors(b)
        print(f"Done! {b.cmd_count} commands")
