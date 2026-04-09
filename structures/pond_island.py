"""池中岛 · 荷风亭 · 九曲桥 · 北岸小石桥

拙政园荷风四面亭意境：池心岛屿，六角攒尖亭居中，
九曲桥从南蜿蜒而入，北石桥直线通烟波榭。
"""

import sys; sys.path.insert(0, '/Users/lambertlin/minecraft-server/scripts')
import math
import random
from builder import MinecraftBuilder
from blocks import PALETTE
from config import POND

# ── 坐标常量 ──
CX = POND["cx"]          # 52 — 池塘/岛中心 X
CZ = POND["cz"]          # 45 — 池塘/岛中心 Z
GROUND_Y = -60            # 岛面 Y（高出水面 1 格）
WATER_Y = -61             # 水面 Y

# ── 材质 ──
DIRT        = PALETTE["dirt"]
GRASS       = PALETTE["grass"]
COBBLE      = PALETTE["cobblestone"]
MOSSY_COBBLE = PALETTE["mossy_cobblestone"]
WATER       = PALETTE["water"]
STONE_BRICK = PALETTE["base"]              # stone_bricks
BASE_STEP   = PALETTE["base_step"]         # stone_brick_stairs
PILLAR      = PALETTE["pillar"]            # stripped_crimson_stem
RAIL        = PALETTE["rail"]              # crimson_fence
ROOF        = PALETTE["roof"]              # stone_brick_stairs
ROOF_BLOCK  = PALETTE["roof_block"]        # stone_bricks
ROOF_SLAB   = PALETTE["roof_slab"]         # stone_brick_slab
ROD         = PALETTE["lightning_rod"]
FLOOR       = PALETTE["floor"]             # smooth_stone
SLAB        = PALETTE["base_slab"]         # stone_brick_slab
COBBLE_WALL = "minecraft:cobblestone_wall"
STRIPPED_CRIMSON = "minecraft:stripped_crimson_stem"
AIR         = PALETTE["air"]
LILY        = PALETTE["lily"]
BEAM        = PALETTE["beam"]              # dark_oak_planks


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  1. 池中岛 — 11×11 椭圆 + 噪声不规则边缘
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def _island_mask(cx, cz, seed=42):
    """生成不规则岛屿 mask，返回 set of (x, z) 坐标。
    基于椭圆 + 伪随机噪声扰动边缘。"""
    random.seed(seed)
    rx, rz = 5.5, 5.0  # 基础椭圆半轴 → ~11×10
    mask = set()
    for dx in range(-7, 8):
        for dz in range(-7, 8):
            # 椭圆判定 + 噪声
            dist = (dx / rx) ** 2 + (dz / rz) ** 2
            # 边缘噪声：角度相关的伪随机偏移
            angle = math.atan2(dz, dx)
            noise = random.uniform(-0.15, 0.15)
            if dist <= 1.0 + noise:
                mask.add((cx + dx, cz + dz))
    return mask


def _edge_blocks(mask):
    """找出 mask 中的边缘方块（至少有一个四邻域不在 mask 中）"""
    edges = set()
    for (x, z) in mask:
        for nx, nz in [(x+1,z),(x-1,z),(x,z+1),(x,z-1)]:
            if (nx, nz) not in mask:
                edges.add((x, z))
                break
    return edges


def build_island(b: MinecraftBuilder):
    """建造池中岛：按行 fill dirt 岛体 + 草皮 + 驳岸。
    用按行扫描 fill 连续段代替逐格操作，大幅减少命令数。"""
    print(f"=== 池中岛 at ({CX}, {GROUND_Y}, {CZ}) ===")

    mask = _island_mask(CX, CZ)
    # P0修复: 排除X<=47的点，避免覆盖廊桥桥墩(X=43~47)
    mask = {(x, z) for (x, z) in mask if x > 47}
    edges = _edge_blocks(mask)

    x_coords = [p[0] for p in mask]
    z_coords = [p[1] for p in mask]
    x_min, x_max = min(x_coords), max(x_coords)
    z_min, z_max = min(z_coords), max(z_coords)

    # 按行 fill：对每行 z 找出 mask 内的连续 x 段，用 fill 填 dirt 柱体
    for z in range(z_min, z_max + 1):
        row_xs = sorted([x for (x, zz) in mask if zz == z])
        if not row_xs:
            continue
        # 找连续段
        seg_start = row_xs[0]
        for i in range(1, len(row_xs)):
            if row_xs[i] != row_xs[i - 1] + 1:
                # 结束一段
                b.fill(seg_start, WATER_Y - 2, z, row_xs[i - 1], GROUND_Y, z, DIRT)
                seg_start = row_xs[i]
        # 最后一段
        b.fill(seg_start, WATER_Y - 2, z, row_xs[-1], GROUND_Y, z, DIRT)

    # 岛面覆草（非边缘）— 按行 fill 连续段
    interior = sorted([(x, z) for (x, z) in mask if (x, z) not in edges])
    for z in range(z_min, z_max + 1):
        row_xs = sorted([x for (x, zz) in interior if zz == z])
        if not row_xs:
            continue
        seg_start = row_xs[0]
        for i in range(1, len(row_xs)):
            if row_xs[i] != row_xs[i - 1] + 1:
                b.fill(seg_start, GROUND_Y, z, row_xs[i - 1], GROUND_Y, z, GRASS)
                seg_start = row_xs[i]
        b.fill(seg_start, GROUND_Y, z, row_xs[-1], GROUND_Y, z, GRASS)

    # 边缘驳岸：cobblestone / mossy_cobblestone 随机
    random.seed(123)
    for (x, z) in sorted(edges):
        stone = MOSSY_COBBLE if random.random() < 0.4 else COBBLE
        b.setblock(x, GROUND_Y, z, stone)
        b.setblock(x, WATER_Y, z, stone)

    # 岛周围水面点缀荷叶
    random.seed(456)
    for dx in range(-8, 9):
        for dz in range(-8, 8):
            x, z = CX + dx, CZ + dz
            if (x, z) not in mask:
                dist = (dx / 7.0) ** 2 + (dz / 6.5) ** 2
                if 0.6 < dist < 1.5 and random.random() < 0.15:
                    b.setblock(x, WATER_Y + 1, z, LILY)

    b.register_bbox("pond_island", x_min, WATER_Y - 2, z_min,
                     x_max, GROUND_Y + 20, z_max)
    print(f"  Island done. {b.cmd_count} cmds so far")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  2. 荷风亭 — 六角攒尖亭，底座 9×9 切角
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def _hex_footprint(cx, cz):
    """六角形（切角矩形）：9×9 正方形切去四角 2×2。
    返回 set of (x, z)。
    布局（相对于中心）:
       XXXXX      <- dz=-4: dx in [-2..2]
      XXXXXXX     <- dz=-3: dx in [-3..3]
     XXXXXXXXX    <- dz=-2..-1,0,1,2: dx in [-4..4]
      XXXXXXX     <- dz=3: dx in [-3..3]
       XXXXX      <- dz=4: dx in [-2..2]
    """
    footprint = set()
    for dz in range(-4, 5):
        if abs(dz) == 4:
            r = 2
        elif abs(dz) == 3:
            r = 3
        else:
            r = 4
        for dx in range(-r, r + 1):
            footprint.add((cx + dx, cz + dz))
    return footprint


def _hex_outline(cx, cz):
    """六角形轮廓（边缘一圈）"""
    full = _hex_footprint(cx, cz)
    inner = set()
    for (x, z) in full:
        is_edge = False
        for nx, nz in [(x+1,z),(x-1,z),(x,z+1),(x,z-1)]:
            if (nx, nz) not in full:
                is_edge = True
                break
        if not is_edge:
            inner.add((x, z))
    return full - inner


def _hex_vertices(cx, cz):
    """六角形的 6 个顶点（柱子位置）。
    切角矩形的 6 个拐角点。"""
    return [
        (cx - 2, cz - 4),  # 北偏西
        (cx + 2, cz - 4),  # 北偏东
        (cx + 4, cz - 2),  # 东偏北
        (cx + 4, cz + 2),  # 东偏南
        (cx + 2, cz + 4),  # 南偏东
        (cx - 2, cz + 4),  # 南偏西
        (cx - 4, cz + 2),  # 西偏南
        (cx - 4, cz - 2),  # 西偏北
    ]


def _hex_pillar_positions(cx, cz):
    """6 根柱子位置 — 六角形长边中点附近"""
    return [
        (cx,     cz - 4),  # 北
        (cx + 4, cz - 2),  # 东北
        (cx + 4, cz + 2),  # 东南
        (cx,     cz + 4),  # 南
        (cx - 4, cz + 2),  # 西南
        (cx - 4, cz - 2),  # 西北
    ]


def build_lotus_pavilion(b: MinecraftBuilder):
    """建造荷风亭 — 六角攒尖亭"""
    print(f"=== 荷风亭 at ({CX}, {GROUND_Y}, {CZ}) ===")

    base_y = GROUND_Y   # -60，岛面
    pillar_h = 5         # 柱高 5 格

    # ── 1. 台基（1 格高 stone_bricks）──
    footprint = _hex_footprint(CX, CZ)
    outline = _hex_outline(CX, CZ)

    # 台基实体
    for (x, z) in footprint:
        b.setblock(x, base_y, z, STONE_BRICK)

    # 台面铺装（台基上面 = base_y + 1）
    floor_y = base_y + 1
    for (x, z) in footprint:
        if (x, z) not in outline:
            b.setblock(x, floor_y, z, FLOOR)
        else:
            b.setblock(x, floor_y, z, STONE_BRICK)

    # ── 2. 柱子（6 根，高 5 格）──
    pillars = _hex_pillar_positions(CX, CZ)
    pillar_base = floor_y + 1  # base_y + 2
    pillar_top = pillar_base + pillar_h - 1  # base_y + 6

    for (px, pz) in pillars:
        for y in range(pillar_base, pillar_top + 1):
            b.setblock(px, y, pz, PILLAR)

    # ── 3. 栏杆 — 轮廓线上（柱间），中间留入口 ──
    # 栏杆在 floor_y + 1 高度
    rail_y = floor_y + 1

    # 六条边的定义（每条边从一个柱子到下一个柱子）
    # 柱子顺序：北、东北、东南、南、西南、西北
    # 每条边中间 3 格留空作为入口
    pillar_set = set(pillars)

    # P0修复: 南北各留3格入口（九曲桥和北岸桥接入方向）
    entrance_positions = set()
    for dx in range(-1, 2):
        entrance_positions.add((CX + dx, CZ + 4))  # 南门
        entrance_positions.add((CX + dx, CZ - 4))  # 北门

    for (x, z) in outline:
        if (x, z) not in pillar_set and (x, z) not in entrance_positions:
            b.setblock(x, rail_y, z, RAIL)

    # ── 4. 额枋（梁）— 柱顶连线 ──
    beam_y = pillar_top + 1  # base_y + 7
    for (x, z) in outline:
        b.setblock(x, beam_y, z, BEAM)
    # 柱顶也补梁
    for (px, pz) in pillars:
        b.setblock(px, beam_y, pz, BEAM)

    # ── 5. 六角攒尖顶 — 逐层缩小 ──
    # 屋顶从 beam_y + 1 开始
    roof_y = beam_y + 1  # base_y + 8

    # 第 1 层：完整六角 9×9 切角 + 外圈飞檐（stairs 朝外）
    _build_hex_roof_layer(b, CX, roof_y, CZ, 4, overhang=1)

    # 第 2 层：缩小一圈 7×7 切角
    _build_hex_roof_layer(b, CX, roof_y + 1, CZ, 3, overhang=0)

    # 第 3 层：5×5 切角
    _build_hex_roof_layer(b, CX, roof_y + 2, CZ, 2, overhang=0)

    # 第 4 层：3×3 实心
    b.fill(CX - 1, roof_y + 3, CZ - 1, CX + 1, roof_y + 3, CZ + 1, ROOF_BLOCK)

    # 第 5 层：1×1 + 宝顶
    b.setblock(CX, roof_y + 4, CZ, ROOF_BLOCK)
    b.setblock(CX, roof_y + 5, CZ, ROD)

    b.register_bbox("lotus_pavilion", CX - 6, base_y, CZ - 6,
                     CX + 6, roof_y + 6, CZ + 6)
    print(f"  Pavilion done. {b.cmd_count} cmds so far")


def _build_hex_roof_layer(b, cx, y, cz, half_size, overhang=0):
    """建造一层六角形屋顶。
    half_size: 正方形半边长（实际宽 = 2*half_size+1）
    overhang: 飞檐外挑格数
    """
    # 生成该层六角形
    layer = set()
    for dz in range(-half_size, half_size + 1):
        if half_size >= 3:
            if abs(dz) == half_size:
                r = half_size - 2
            elif abs(dz) == half_size - 1:
                r = half_size - 1
            else:
                r = half_size
        elif half_size == 2:
            if abs(dz) == 2:
                r = 1
            else:
                r = 2
        else:
            r = half_size
        for dx in range(-r, r + 1):
            layer.add((cx + dx, cz + dz))

    # 填实心屋顶方块
    for (x, z) in layer:
        b.setblock(x, y, z, ROOF_BLOCK)

    # 飞檐（仅第一层有外挑）
    if overhang > 0:
        # 在六角形外一圈放 stairs 朝外
        for (x, z) in layer:
            for nx, nz in [(x+1,z),(x-1,z),(x,z+1),(x,z-1)]:
                if (nx, nz) not in layer:
                    # 判断朝向
                    dx_dir = nx - x
                    dz_dir = nz - z
                    if dz_dir == -1:
                        facing = "facing=south"  # 北侧飞檐朝南
                    elif dz_dir == 1:
                        facing = "facing=north"
                    elif dx_dir == -1:
                        facing = "facing=east"
                    else:
                        facing = "facing=west"
                    b.setblock(nx, y, nz,
                               f"minecraft:stone_brick_stairs[{facing},half=top]")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  3. 九曲桥 — 南岸 → 岛南端
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def build_zigzag_bridge(b: MinecraftBuilder):
    """九曲桥：从南岸 (52, 57) 到岛南端 (52, 49)。
    折线路径：每 2-3 格转弯，东-北-西-北交替。
    桥面宽 2 格，stone_brick_slab。两侧 cobblestone_wall 栏杆。
    桥墩 stripped_crimson_stem 每 3 格一根插入水中。
    """
    print(f"=== 九曲桥 (南岸→岛) ===")

    bridge_y = GROUND_Y  # -60
    SLAB_TOP = f"minecraft:stone_brick_slab[type=top]"

    # 九曲路径 — 每段定义为 (x1,z1, x2,z2, width_axis)
    # width_axis: 'x' → 桥面沿 x 展开 2 格（南北行进时）
    #             'z' → 桥面沿 z 展开 2 格（东西行进时）
    # waypoints（桥面左下角基准点，宽 2 格）
    segments = [
        # (x1, z1, x2, z2, 展开轴)
        # 段 1: 南岸北行 — x=52,53 z=57→55
        (52, 55, 53, 57, 'x'),
        # 段 2: 东行 — z=54,55 x=53→56
        (53, 54, 56, 55, 'z'),
        # 段 3: 北行 — x=55,56 z=54→52
        (55, 52, 56, 54, 'x'),
        # 段 4: 西行 — z=51,52 x=52→56
        (52, 51, 56, 52, 'z'),
        # 段 5: 北行 — x=52,53 z=51→49
        (52, 49, 53, 51, 'x'),
        # 段 6: 东行 — z=48,49 x=53→55
        (53, 48, 55, 49, 'z'),
        # 段 7: 北行到岛 — x=54,55 z=48→46 (接入岛边)
        (54, 46, 55, 48, 'x'),
        # 段 8: 西行接岛心 — z=45,46 x=52→55
        (52, 45, 55, 46, 'z'),
    ]

    placed_slab = set()
    placed_wall = set()

    for (x1, z1, x2, z2, waxis) in segments:
        # fill 桥面
        b.fill(x1, bridge_y, z1, x2, bridge_y, z2, SLAB_TOP)
        for x in range(x1, x2 + 1):
            for z in range(z1, z2 + 1):
                placed_slab.add((x, z))

        # 栏杆 — 沿行进方向两侧
        if waxis == 'x':
            # 南北行进，桥面 x 方向宽 2 格 → 栏杆在 x1-1 和 x2+1
            for z in range(z1, z2 + 1):
                for wall_x in [x1 - 1, x2 + 1]:
                    key = (wall_x, z)
                    if key not in placed_wall and key not in placed_slab:
                        placed_wall.add(key)
                        b.setblock(wall_x, bridge_y, z, COBBLE_WALL)
                        b.setblock(wall_x, bridge_y + 1, z, COBBLE_WALL)
        else:
            # 东西行进，桥面 z 方向宽 2 格 → 栏杆在 z1-1 和 z2+1
            for x in range(x1, x2 + 1):
                for wall_z in [z1 - 1, z2 + 1]:
                    key = (x, wall_z)
                    if key not in placed_wall and key not in placed_slab:
                        placed_wall.add(key)
                        b.setblock(x, bridge_y, wall_z, COBBLE_WALL)
                        b.setblock(x, bridge_y + 1, wall_z, COBBLE_WALL)

    # 桥墩：每 3 格一根 (在桥面中线下方)
    pier_count = 0
    pier_positions = set()
    for (x1, z1, x2, z2, waxis) in segments:
        if waxis == 'x':
            px = (x1 + x2) // 2  # 桥中线
            for z in range(z1, z2 + 1, 3):
                if (px, z) not in pier_positions:
                    pier_positions.add((px, z))
                    for y in range(WATER_Y - 2, bridge_y):
                        b.setblock(px, y, z, STRIPPED_CRIMSON)
                    pier_count += 1
        else:
            pz = (z1 + z2) // 2
            for x in range(x1, x2 + 1, 3):
                if (x, pz) not in pier_positions:
                    pier_positions.add((x, pz))
                    for y in range(WATER_Y - 2, bridge_y):
                        b.setblock(x, y, pz, STRIPPED_CRIMSON)
                    pier_count += 1

    b.register_bbox("zigzag_bridge", 49, WATER_Y - 2, 44, 58, bridge_y + 2, 58)
    print(f"  Zigzag bridge done ({pier_count} piers). {b.cmd_count} cmds so far")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  4. 北岸小石桥 — 直线平桥
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def build_north_bridge(b: MinecraftBuilder):
    """北岸小石桥：从烟波榭方向 (52, 33) 到岛北端 (52, 40)。
    宽 3 格，直线石板平桥，Y=-60。
    """
    print(f"=== 北岸小石桥 ===")

    bridge_y = GROUND_Y  # -60
    x_center = CX        # 52
    z_start = 34          # 北岸（留 1 格余量）
    z_end = 40            # 岛北端

    # 桥面：3 格宽 (x_center-1 .. x_center+1)
    b.fill(x_center - 1, bridge_y, z_start,
           x_center + 1, bridge_y, z_end,
           f"minecraft:stone_brick_slab[type=top]")

    # 栏杆：两侧 cobblestone_wall（2 格高）
    for wall_x in [x_center - 2, x_center + 2]:
        for z in range(z_start, z_end + 1):
            b.setblock(wall_x, bridge_y, z, COBBLE_WALL)
            b.setblock(wall_x, bridge_y + 1, z, COBBLE_WALL)

    # 桥墩：每 3 格一根
    for z in range(z_start, z_end + 1, 3):
        for y in range(WATER_Y - 2, bridge_y):
            b.setblock(x_center, y, z, STONE_BRICK)

    b.register_bbox("north_bridge", x_center - 2, WATER_Y - 2, z_start,
                     x_center + 2, bridge_y + 2, z_end)
    print(f"  North bridge done. {b.cmd_count} cmds so far")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Main
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

if __name__ == "__main__":
    with MinecraftBuilder() as b:
        build_island(b)
        build_lotus_pavilion(b)
        build_zigzag_bridge(b)
        build_north_bridge(b)
        print(f"Done! {b.cmd_count} commands")
