"""修复园林树木比例 — 主景树 10-15 格，中景 8-10 格

问题: 牡丹亭 16 格高，大梅树才 6 格 —— 比例严重失调。
修复: 大梅树升至 12 格，垂杨 8-10 格，新增松树和行道树。

每棵树一个函数，可单独调用。
"""

import sys; sys.path.insert(0, '/Users/lambertlin/minecraft-server/scripts')
from builder import MinecraftBuilder, filled_circle_points
from blocks import PALETTE, GROUND_Y, BUILD_Y
from config import GARDEN, PLUM_TREE, WILLOWS as CFG_WILLOWS, HALL, TAIHU_ROCKS, GATE_AREA
import random
import math


# ══════════════════════════════════════════════════════════════
#  工具函数
# ══════════════════════════════════════════════════════════════

def _get_vine_facing(vx, vz, trunk_cx, trunk_cz):
    """根据位置相对树干中心方向生成 vine 方块状态"""
    dx = vx - trunk_cx
    dz = vz - trunk_cz
    faces = []
    if dx > 0:
        faces.append("east=true")
    elif dx < 0:
        faces.append("west=true")
    if dz > 0:
        faces.append("south=true")
    elif dz < 0:
        faces.append("north=true")
    if not faces:
        faces.append("south=true")
    return f"minecraft:vine[{','.join(faces)}]"


def _clear_tree_area(b, cx, cz, radius, height):
    """清除旧树区域的所有非地面方块"""
    for dx in range(-radius, radius + 1):
        for dz in range(-radius, radius + 1):
            for dy in range(height + 5):
                b.setblock(cx + dx, BUILD_Y + dy, cz + dz, "minecraft:air")


# ══════════════════════════════════════════════════════════════
#  1. 大梅树 — 杜丽娘葬身处，"大梅树一株"
#     高 12 格，2x2 不规则树干，树冠半径 6-7，根部外露，树下落花
# ══════════════════════════════════════════════════════════════

def fix_plum_tree(b):
    """重建大梅树: 12 格高主景树，孤独、巨大、荫蔽"""
    print("  [1] 重建大梅树...")
    px, pz = PLUM_TREE["x"], PLUM_TREE["z"]
    random.seed(42)  # 可复现

    # 清除旧树
    _clear_tree_area(b, px, pz, 9, 18)

    # ── 根部外露 ──
    # 横向原木从树干基部向外延伸，砂土/粗泥铺底
    root_dirs = [
        (-1, -1), (2, -1), (-1, 2), (2, 1),  # 四个方向的根
        (-2, 0), (1, 3), (3, 0), (0, -2),
    ]
    for rdx, rdz in root_dirs:
        rx, rz = px + rdx, pz + rdz
        # 横向原木（axis 朝向根的延伸方向）
        if abs(rdx) >= abs(rdz):
            axis = "x"
        else:
            axis = "z"
        b.setblock(rx, GROUND_Y, rz, f"minecraft:cherry_log[axis={axis}]")
        # 根旁边铺粗泥/砂土
        for ddx in range(-1, 2):
            for ddz in range(-1, 2):
                if random.random() < 0.35:
                    rrx, rrz = rx + ddx, rz + ddz
                    # 不覆盖树干核心
                    if 0 <= rrx - px <= 1 and 0 <= rrz - pz <= 1:
                        continue
                    dirt_type = random.choice([
                        "minecraft:coarse_dirt", "minecraft:rooted_dirt",
                        "minecraft:dirt", "minecraft:podzol",
                    ])
                    b.setblock(rrx, GROUND_Y, rrz, dirt_type)

    # ── 树干: 2x2 基座，高 12 格，不规则弯曲 ──
    trunk_h = 12
    # 树干核心 2x2
    for dy in range(trunk_h):
        y = BUILD_Y + dy
        for dx in range(2):
            for dz in range(2):
                b.setblock(px + dx, y, pz + dz, PALETTE["cherry_log"])

        # 低处(0-3格): 树干略粗，加额外方块模拟粗壮
        if dy < 4:
            extras = [(-1, 0), (2, 0), (0, -1), (1, 2), (-1, 1), (2, 1)]
            for edx, edz in extras:
                if random.random() < 0.4 - dy * 0.08:
                    b.setblock(px + edx, y, pz + edz, PALETTE["cherry_log"])

        # 中段(4-7格): 偶尔突出一格
        if 4 <= dy <= 7:
            bumps = [(-1, 0), (2, 1), (1, 2), (0, -1)]
            for bdx, bdz in bumps:
                if random.random() < 0.2:
                    b.setblock(px + bdx, y, pz + bdz, PALETTE["cherry_log"])

    # ── 主枝分叉: 高8-10格处向外延伸 ──
    branches = [
        # (起始高度, dx方向, dz方向, 长度)
        (8,  -1, -1, 4),  # 西北
        (9,   1,  1, 3),  # 东南
        (10, -1,  1, 3),  # 西南
        (8,   1, -1, 4),  # 东北
        (7,   2,  0, 3),  # 正东
    ]
    for br_y, br_dx, br_dz, br_len in branches:
        for step in range(br_len):
            bx = px + br_dx * (step + 1)
            bz = pz + br_dz * (step + 1)
            by = BUILD_Y + br_y + step // 2  # 缓慢上升
            # 选择 axis
            if abs(br_dx) >= abs(br_dz):
                axis = "x"
            else:
                axis = "z"
            b.setblock(bx, by, bz, f"minecraft:cherry_log[axis={axis}]")

    # ── 树冠: 分层椭球，不规则空隙 ──
    crown_base_y = BUILD_Y + 8   # 树冠从第 8 格开始
    crown_peak_y = BUILD_Y + 15  # 到第 15 格
    crown_cx = px + 0.5
    crown_cz = pz + 0.5

    # 每层定义: (y_offset_from_base, x_radius, z_radius)
    crown_layers = [
        (0, 5, 4),   # 底层，向外铺开
        (1, 6, 6),   # 次宽
        (2, 7, 7),   # 最宽层
        (3, 7, 6),   # 继续宽
        (4, 6, 6),   # 开始收
        (5, 5, 5),   # 收窄
        (6, 4, 4),   # 更窄
        (7, 2, 2),   # 顶部
    ]

    for dy_off, rx, rz in crown_layers:
        y = crown_base_y + dy_off
        for dx in range(-rx, rx + 1):
            for dz in range(-rz, rz + 1):
                dist_sq = (dx / rx) ** 2 + (dz / rz) ** 2
                if dist_sq > 1.0:
                    continue
                # 制造自然空隙: 边缘更多缺口，内部偶尔透光
                if dist_sq > 0.6 and random.random() < 0.30:
                    continue
                if dist_sq > 0.3 and random.random() < 0.08:
                    continue  # 内部透光孔
                lx = int(crown_cx + dx)
                lz = int(crown_cz + dz)
                b.setblock(lx, y, lz, PALETTE["cherry_leaves"])

    # ── 树下意境: 大量落花、苔藓、粗泥 ──
    for dx in range(-7, 8):
        for dz in range(-7, 8):
            tx, tz = px + dx, pz + dz
            dist = math.sqrt(dx * dx + dz * dz)
            if dist > 7.5:
                continue
            # 跳过树干
            if 0 <= dx <= 1 and 0 <= dz <= 1:
                continue

            r = random.random()
            # 中心区落花更密
            density_factor = 1.0 - dist / 8.0
            if r < 0.30 * density_factor:
                b.setblock(tx, BUILD_Y, tz, "minecraft:pink_carpet")
            elif r < 0.45 * density_factor:
                b.setblock(tx, BUILD_Y, tz, PALETTE["moss_carpet"])
            elif r < 0.55 * density_factor:
                b.setblock(tx, GROUND_Y, tz, PALETTE["moss"])

    # 周围零星落花（更远处）
    for dx in range(-9, 10):
        for dz in range(-9, 10):
            dist = math.sqrt(dx * dx + dz * dz)
            if 6 < dist <= 9 and random.random() < 0.12:
                tx, tz = px + dx, pz + dz
                b.setblock(tx, BUILD_Y, tz, "minecraft:pink_carpet")

    print(f"    大梅树完成: ({px},{pz}), 高{trunk_h}格, 冠幅~14格")


# ══════════════════════════════════════════════════════════════
#  2. 垂杨 x4 — 高 8-10 格，2x2 树干，vine 垂 5-7 格
# ══════════════════════════════════════════════════════════════

def fix_willows(b):
    """重建 4 棵垂杨: 扁平宽冠，长垂藤"""
    print("  [2] 重建垂杨...")
    random.seed(77)

    for idx, (wx, wz) in enumerate(CFG_WILLOWS):
        # 清除旧树
        _clear_tree_area(b, wx, wz, 8, 16)

        trunk_h = random.randint(8, 10)

        # ── 树干: 2x2，不规则 ──
        for dy in range(trunk_h):
            y = BUILD_Y + dy
            # 核心 2x2
            for dx in range(2):
                for dz in range(2):
                    b.setblock(wx + dx, y, wz + dz, PALETTE["oak_log"])

            # 底部加粗 (0-2格)
            if dy < 3:
                extras = [(-1, 0), (2, 0), (0, -1), (1, 2)]
                for edx, edz in extras:
                    if random.random() < 0.35 - dy * 0.1:
                        b.setblock(wx + edx, y, wz + edz, PALETTE["oak_log"])

            # 中段轻微弯曲
            if dy == trunk_h // 2 and random.random() < 0.5:
                bend_dx = random.choice([-1, 2])
                b.setblock(wx + bend_dx, y, wz, PALETTE["oak_log"])

        # ── 根部外露 ──
        root_offsets = [(-1, -1), (2, 0), (0, 2), (2, 2), (-1, 1)]
        for rdx, rdz in root_offsets:
            if random.random() < 0.6:
                axis = "x" if abs(rdx) > abs(rdz) else "z"
                b.setblock(wx + rdx, GROUND_Y, wz + rdz,
                           f"minecraft:oak_log[axis={axis}]")
                if random.random() < 0.5:
                    b.setblock(wx + rdx, GROUND_Y, wz + rdz + random.choice([-1, 1]),
                               "minecraft:coarse_dirt")

        # ── 树冠: 扁平宽大，水平半径 5-6 ──
        crown_top_y = BUILD_Y + trunk_h
        h_radius = random.randint(5, 6)
        trunk_cx = wx + 0.5
        trunk_cz = wz + 0.5

        # 垂柳树冠矮胖: 只有 3 层但很宽
        crown_layers = [
            (-1, h_radius - 1),   # 下层
            (0,  h_radius),       # 最宽（主冠层）
            (1,  h_radius),       # 仍然宽
            (2,  h_radius - 2),   # 顶部收窄
        ]

        vine_hang_points = []  # 收集可挂藤的边缘点

        for dy_off, r in crown_layers:
            y = crown_top_y + dy_off
            for dx in range(-r, r + 1):
                for dz in range(-r, r + 1):
                    dist_sq = dx * dx + dz * dz
                    if dist_sq > r * r:
                        continue
                    # 边缘不规则
                    if dist_sq > r * r * 0.6 and random.random() < 0.22:
                        continue
                    lx = int(trunk_cx + dx)
                    lz = int(trunk_cz + dz)
                    b.setblock(lx, y, lz, PALETTE["oak_leaves"])

                    # 底层和主层边缘 -> 挂藤候选
                    if dy_off <= 0 and dist_sq > (r - 2) ** 2:
                        vine_hang_points.append((lx, y, lz))

        # ── vine 垂 5-7 格 ——"垂"是核心特征 ──
        vine_hang_points = list(set(vine_hang_points))
        random.shuffle(vine_hang_points)
        vine_count = min(len(vine_hang_points), random.randint(18, 28))

        for vx, vy, vz in vine_hang_points[:vine_count]:
            facing = _get_vine_facing(vx, vz, wx + 0.5, wz + 0.5)
            vine_len = random.randint(5, 7)  # 5-7 格长藤!
            for vdy in range(vine_len):
                target_y = vy - 1 - vdy
                if target_y <= GROUND_Y:
                    break
                b.setblock(vx, target_y, vz, facing)

        print(f"    垂柳 #{idx+1} @ ({wx},{wz}), "
              f"高{trunk_h}, 冠径{h_radius*2}, 藤{vine_count}条x5-7格")


# ══════════════════════════════════════════════════════════════
#  3. 新增主景松树 — 云片/迎客松造型（层叠，不是圆锥）
# ══════════════════════════════════════════════════════════════

def _build_cloud_layer(b, cx, y, cz, rx, rz, block="minecraft:spruce_leaves"):
    """构建一个云片层: 扁平椭圆，厚度 1-2 格，有不规则边缘"""
    for dy in range(2):  # 每个云片 2 格厚
        current_rx = rx if dy == 0 else rx - 1
        current_rz = rz if dy == 0 else rz - 1
        if current_rx < 1 or current_rz < 1:
            continue
        for dx in range(-current_rx, current_rx + 1):
            for dz in range(-current_rz, current_rz + 1):
                dist = (dx / current_rx) ** 2 + (dz / current_rz) ** 2
                if dist > 1.0:
                    continue
                if dist > 0.65 and random.random() < 0.30:
                    continue  # 边缘缺口
                b.setblock(cx + dx, y + dy, cz + dz, block)


def fix_pine_trees(b):
    """新增 2 棵主景松树: 太湖石旁迎客松 + 翠轩后云片松"""
    print("  [3] 新增松树...")
    random.seed(55)

    # ── 松树 A: 太湖石旁迎客松 (38, 15) ──
    # 迎客松: 主干略倾斜，一侧枝干横向大幅延伸
    ax, az = 38, 15
    ground_y = TAIHU_ROCKS["ground_y"]  # -57, 太湖石区高地
    base_y = ground_y + 1

    print("    松树A: 迎客松 @ (38,15)...")

    # 树干: 高 10 格，微倾（每 3 格偏移 1 格向东）
    trunk_h = 10
    trunk_positions = []
    cur_x = ax
    for dy in range(trunk_h):
        y = base_y + dy
        # 每 3 格向东偏 1 格，模拟倾斜
        if dy > 0 and dy % 3 == 0:
            cur_x += 1
        b.setblock(cur_x, y, az, "minecraft:spruce_log")
        b.setblock(cur_x + 1, y, az, "minecraft:spruce_log")  # 2格宽干
        trunk_positions.append((cur_x, y, az))

        # 底部加粗
        if dy < 3:
            b.setblock(cur_x - 1, y, az, "minecraft:spruce_log")
            if random.random() < 0.4:
                b.setblock(cur_x, y, az - 1, "minecraft:spruce_log")

    # 迎客枝: 从高 6 格处向东南大幅延伸 5 格
    welcome_branch_y = base_y + 6
    wb_x = cur_x  # 当前偏移后的 x
    for step in range(1, 6):
        bx = wb_x + step + 1
        bz = az + (step // 2)
        by = welcome_branch_y + (step // 3)
        b.setblock(bx, by, bz, "minecraft:spruce_log[axis=x]")

    # 云片层叠树冠（3 层）
    top_x = cur_x
    layers = [
        (base_y + 5,  top_x - 1,  az, 3, 2),    # 低层
        (base_y + 7,  top_x,      az, 3, 3),     # 中层
        (base_y + 9,  top_x + 1,  az, 2, 2),     # 顶层
    ]
    for ly, lcx, lcz, lrx, lrz in layers:
        _build_cloud_layer(b, lcx, ly, lcz, lrx, lrz)

    # 迎客枝上的云片
    _build_cloud_layer(b, wb_x + 4, welcome_branch_y + 1, az + 1, 3, 2)

    # 根部
    for rdx, rdz in [(-2, 0), (-1, -1), (1, 1), (2, 1), (0, -2)]:
        if random.random() < 0.7:
            axis = "x" if abs(rdx) > abs(rdz) else "z"
            b.setblock(ax + rdx, ground_y, az + rdz,
                       f"minecraft:spruce_log[axis={axis}]")
            if random.random() < 0.5:
                b.setblock(ax + rdx + random.choice([-1, 0, 1]),
                           ground_y, az + rdz + random.choice([-1, 0, 1]),
                           "minecraft:podzol")

    print(f"    迎客松完成: 高{trunk_h}格, 迎客枝向东延伸5格")

    # ── 松树 B: 翠轩后云片松 (8, 32) ──
    bx_pos, bz_pos = 8, 32
    hall_ground = HALL["ground_y"]  # BUILD_Y = -60
    b_base_y = hall_ground

    print("    松树B: 云片松 @ (8,32)...")

    # 树干: 高 8 格，笔直但有纹理变化
    trunk_h_b = 8
    for dy in range(trunk_h_b):
        y = b_base_y + dy
        # 2x2 主干
        b.setblock(bx_pos, y, bz_pos, "minecraft:spruce_log")
        b.setblock(bx_pos + 1, y, bz_pos, "minecraft:spruce_log")
        # 底部更粗
        if dy < 2:
            b.setblock(bx_pos, y, bz_pos + 1, "minecraft:spruce_log")
            b.setblock(bx_pos + 1, y, bz_pos + 1, "minecraft:spruce_log")
        # 中段偶尔突出小枝
        if dy == 3:
            b.setblock(bx_pos - 1, y, bz_pos, "minecraft:spruce_log[axis=x]")
        if dy == 5:
            b.setblock(bx_pos + 2, y, bz_pos, "minecraft:spruce_log[axis=x]")

    # 云片树冠: 4 层层叠，间隔错开
    cloud_layers = [
        (b_base_y + 3,  bx_pos - 1, bz_pos, 3, 2),   # 最低层，偏西
        (b_base_y + 5,  bx_pos + 1, bz_pos, 3, 3),    # 中低层，偏东
        (b_base_y + 6,  bx_pos,     bz_pos - 1, 2, 3), # 中高层，偏北
        (b_base_y + 8,  bx_pos,     bz_pos, 2, 2),     # 顶层
    ]
    for ly, lcx, lcz, lrx, lrz in cloud_layers:
        _build_cloud_layer(b, lcx, ly, lcz, lrx, lrz)

    # 根部
    for rdx, rdz in [(-1, -1), (2, 0), (0, 2), (-1, 1)]:
        if random.random() < 0.6:
            axis = "x" if abs(rdx) > abs(rdz) else "z"
            b.setblock(bx_pos + rdx, hall_ground - 1, bz_pos + rdz,
                       f"minecraft:spruce_log[axis={axis}]")
            b.setblock(bx_pos + rdx, hall_ground - 1, bz_pos + rdz + random.choice([-1, 1]),
                       "minecraft:podzol")

    print(f"    云片松完成: 高{trunk_h_b}格, 4层云片冠")


# ══════════════════════════════════════════════════════════════
#  4. 园门两侧行道树 — 中型衬托树
# ══════════════════════════════════════════════════════════════

def fix_gate_trees(b):
    """园门入口两侧各 1 棵中型树，高 8 格"""
    print("  [4] 园门行道树...")
    random.seed(66)

    gate_cx = GATE_AREA["cx"]   # 55
    gate_cz = GATE_AREA["cz"]   # 80
    gate_ground = GATE_AREA["ground_y"]  # BUILD_Y = -60

    # 两棵树分列入口两侧
    positions = [
        (gate_cx - 5, gate_cz + 3),   # 左侧(西)
        (gate_cx + 5, gate_cz + 3),   # 右侧(东)
    ]

    for idx, (tx, tz) in enumerate(positions):
        trunk_h = 8
        base_y = gate_ground

        # ── 树干: 2x2，规整但有细节 ──
        for dy in range(trunk_h):
            y = base_y + dy
            b.setblock(tx, y, tz, PALETTE["cherry_log"])
            b.setblock(tx + 1, y, tz, PALETTE["cherry_log"])
            # 底部 2x2
            if dy < 4:
                b.setblock(tx, y, tz + 1, PALETTE["cherry_log"])
                b.setblock(tx + 1, y, tz + 1, PALETTE["cherry_log"])
            # 底部偶尔加宽
            if dy < 2 and random.random() < 0.4:
                b.setblock(tx - 1, y, tz, PALETTE["cherry_log"])

        # ── 树冠: 圆球偏扁，半径 3-4 ──
        crown_y = base_y + trunk_h
        r = 4
        crown_layers = [
            (-1, r - 1),
            (0,  r),
            (1,  r),
            (2,  r - 1),
            (3,  r - 2),
        ]

        for dy_off, cr in crown_layers:
            y = crown_y + dy_off
            for dx in range(-cr, cr + 1):
                for dz in range(-cr, cr + 1):
                    dist_sq = dx * dx + dz * dz
                    if dist_sq > cr * cr:
                        continue
                    if dist_sq > cr * cr * 0.55 and random.random() < 0.25:
                        continue
                    b.setblock(tx + dx, y, tz + dz, PALETTE["cherry_leaves"])

        # 根部装饰
        for rdx, rdz in [(-1, -1), (2, 0), (0, 2)]:
            if random.random() < 0.5:
                b.setblock(tx + rdx, gate_ground - 1, tz + rdz, "minecraft:coarse_dirt")

        side = "左(西)" if idx == 0 else "右(东)"
        print(f"    行道树{side} @ ({tx},{tz}), 高{trunk_h}格")


# ══════════════════════════════════════════════════════════════
#  主函数
# ══════════════════════════════════════════════════════════════

def fix_all_trees(b):
    """一键修复所有树木比例问题"""
    print("=== 修复树木比例 ===")
    fix_plum_tree(b)
    fix_willows(b)
    fix_pine_trees(b)
    fix_gate_trees(b)
    print("=== 树木修复完成 ===")


if __name__ == "__main__":
    with MinecraftBuilder() as b:
        fix_all_trees(b)
        print(f"Done! {b.cmd_count} commands")
