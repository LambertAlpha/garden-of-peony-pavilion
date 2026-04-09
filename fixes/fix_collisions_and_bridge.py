"""一次性修复所有碰撞和衔接问题

1. 云片松/垂杨侵入翠轩 -> 移位重建
2. 廊桥中段底部空洞 -> 补铺 Y=-60 桥面
3. 廊桥->翠轩连接路 -> 石砖石板路 + 台阶
4. 曲廊起点月洞门 -> 白墙 + 月洞门
5. 曲廊终点前庭 -> 石砖前庭 + 灯笼

坐标参照:
  翠轩: cx=16, cz=35, X:8~24, Z:30~40, ground_y=-60
  廊桥 v3: cx=45, z_start=35, z_end=55, width=5, X:43~47
    微拱: mid=Z45, arch Z:42~48 deck_y=-59, 其余 deck_y=-60
    过渡楼梯: stair_z_n=41, stair_z_s=49
  曲廊 A: (55, 68), 曲廊 H: (70, 15)
  云片松原位: (8, 32), 新位: (3, 32)
  垂杨原位: (18, 28), 新位: (18, 22)
"""

import sys
sys.path.insert(0, '/Users/lambertlin/minecraft-server/scripts')

from builder import MinecraftBuilder, filled_circle_points
from blocks import PALETTE, GROUND_Y, BUILD_Y
from config import HALL, BRIDGE, CORRIDOR
import random
import math


# ══════════════════════════════════════════════════════════════
#  材质常量
# ══════════════════════════════════════════════════════════════

AIR            = PALETTE["air"]
WALL_BLOCK     = PALETTE["wall"]           # white_concrete
WALL_BASE      = PALETTE["wall_base"]      # stone_bricks
WALL_CAP       = PALETTE["wall_cap"]       # stone_brick_slab
STONE_BRICK    = PALETTE["base"]           # stone_bricks
STONE_BRICK_ST = PALETTE["base_step"]      # stone_brick_stairs
FLOOR          = PALETTE["floor"]          # smooth_stone
FLOOR_ALT      = PALETTE["floor_alt"]      # stone_bricks
LANTERN        = PALETTE["lantern"]
OAK_PLANKS     = "minecraft:oak_planks"
SPRUCE_LOG     = "minecraft:spruce_log"
SPRUCE_LEAVES  = PALETTE["spruce_leaves"]  # spruce_leaves[persistent=true]
OAK_LOG        = PALETTE["oak_log"]
OAK_LEAVES     = PALETTE["oak_leaves"]     # oak_leaves[persistent=true]


# ══════════════════════════════════════════════════════════════
#  工具函数 (从 fix_trees.py 复用)
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


def _build_cloud_layer(b, cx, y, cz, rx, rz, block=None):
    """构建一个云片层: 扁平椭圆，厚度 2 格，有不规则边缘"""
    if block is None:
        block = SPRUCE_LEAVES
    for dy in range(2):
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
                    continue
                b.setblock(cx + dx, y + dy, cz + dz, block)


# ══════════════════════════════════════════════════════════════
#  1. 云片松和垂杨移位 (解决侵入翠轩问题)
# ══════════════════════════════════════════════════════════════

def fix_trees_collision(b):
    """移动云片松 (8,32)->(3,32) 和垂杨 (18,28)->(18,22)。

    先清除旧树整个区域，再在新位置重建。
    """
    print("=== [1] 修复树木碰撞: 移位云片松和垂杨 ===")
    random.seed(55)

    # ────────────────────────────────────────────
    # 1A. 云片松: (8,32) -> (3,32)
    # ────────────────────────────────────────────
    print("  云片松: (8,32) -> (3,32)")

    old_px, old_pz = 8, 32
    new_px, new_pz = 3, 32
    hall_ground = HALL["ground_y"]  # BUILD_Y = -60

    # 清除旧树区域: 以旧位置为中心，半径6，高15格
    # 覆盖树干+树冠+根部
    for dx in range(-6, 7):
        for dz in range(-6, 7):
            for dy in range(-1, 15):
                b.setblock(old_px + dx, hall_ground + dy, old_pz + dz, AIR)
    # 恢复旧位置地面为草方块
    for dx in range(-6, 7):
        for dz in range(-6, 7):
            b.setblock(old_px + dx, GROUND_Y, old_pz + dz, PALETTE["grass"])

    # 在新位置 (3, 32) 重建云片松
    b_base_y = hall_ground  # -60

    # 树干: 高 8 格，笔直，2x2
    trunk_h = 8
    for dy in range(trunk_h):
        y = b_base_y + dy
        b.setblock(new_px, y, new_pz, SPRUCE_LOG)
        b.setblock(new_px + 1, y, new_pz, SPRUCE_LOG)
        if dy < 2:
            b.setblock(new_px, y, new_pz + 1, SPRUCE_LOG)
            b.setblock(new_px + 1, y, new_pz + 1, SPRUCE_LOG)
        if dy == 3:
            b.setblock(new_px - 1, y, new_pz, f"{SPRUCE_LOG}[axis=x]")
        if dy == 5:
            b.setblock(new_px + 2, y, new_pz, f"{SPRUCE_LOG}[axis=x]")

    # 云片树冠: 4 层层叠，间隔错开
    cloud_layers = [
        (b_base_y + 3, new_px - 1, new_pz,     3, 2),  # 最低层，偏西
        (b_base_y + 5, new_px + 1, new_pz,     3, 3),  # 中低层，偏东
        (b_base_y + 6, new_px,     new_pz - 1, 2, 3),  # 中高层，偏北
        (b_base_y + 8, new_px,     new_pz,     2, 2),  # 顶层
    ]
    for ly, lcx, lcz, lrx, lrz in cloud_layers:
        _build_cloud_layer(b, lcx, ly, lcz, lrx, lrz)

    # 根部
    for rdx, rdz in [(-1, -1), (2, 0), (0, 2), (-1, 1)]:
        if random.random() < 0.6:
            axis = "x" if abs(rdx) > abs(rdz) else "z"
            b.setblock(new_px + rdx, hall_ground - 1, new_pz + rdz,
                       f"{SPRUCE_LOG}[axis={axis}]")
            b.setblock(new_px + rdx, hall_ground - 1,
                       new_pz + rdz + random.choice([-1, 1]),
                       "minecraft:podzol")

    print(f"    云片松完成: ({new_px},{new_pz}), 高{trunk_h}格, 4层云片冠")

    # ────────────────────────────────────────────
    # 1B. 垂杨: (18,28) -> (18,22)
    # ────────────────────────────────────────────
    print("  垂杨: (18,28) -> (18,22)")

    old_wx, old_wz = 18, 28
    new_wx, new_wz = 18, 22

    # 清除旧树区域: 半径8，高16格
    for dx in range(-8, 9):
        for dz in range(-8, 9):
            for dy in range(-1, 16):
                b.setblock(old_wx + dx, BUILD_Y + dy, old_wz + dz, AIR)
    # 恢复旧位置地面
    for dx in range(-8, 9):
        for dz in range(-8, 9):
            b.setblock(old_wx + dx, GROUND_Y, old_wz + dz, PALETTE["grass"])

    # 重建垂杨
    random.seed(77)  # 与 fix_trees.py 同种子保持风格一致
    trunk_h = 9
    base_y = BUILD_Y

    # 树干 2x2
    for dy in range(trunk_h):
        y = base_y + dy
        for dx in range(2):
            for dz in range(2):
                b.setblock(new_wx + dx, y, new_wz + dz, OAK_LOG)
        if dy < 3:
            extras = [(-1, 0), (2, 0), (0, -1), (1, 2)]
            for edx, edz in extras:
                if random.random() < 0.35 - dy * 0.1:
                    b.setblock(new_wx + edx, y, new_wz + edz, OAK_LOG)
        if dy == trunk_h // 2 and random.random() < 0.5:
            bend_dx = random.choice([-1, 2])
            b.setblock(new_wx + bend_dx, y, new_wz, OAK_LOG)

    # 根部外露
    root_offsets = [(-1, -1), (2, 0), (0, 2), (2, 2), (-1, 1)]
    for rdx, rdz in root_offsets:
        if random.random() < 0.6:
            axis = "x" if abs(rdx) > abs(rdz) else "z"
            b.setblock(new_wx + rdx, GROUND_Y, new_wz + rdz,
                       f"minecraft:oak_log[axis={axis}]")
            if random.random() < 0.5:
                b.setblock(new_wx + rdx, GROUND_Y,
                           new_wz + rdz + random.choice([-1, 1]),
                           "minecraft:coarse_dirt")

    # 树冠: 扁平宽大
    crown_top_y = base_y + trunk_h
    h_radius = 5
    trunk_cx = new_wx + 0.5
    trunk_cz = new_wz + 0.5

    crown_layers = [
        (-1, h_radius - 1),
        (0,  h_radius),
        (1,  h_radius),
        (2,  h_radius - 2),
    ]

    vine_hang_points = []
    for dy_off, r in crown_layers:
        y = crown_top_y + dy_off
        for dx in range(-r, r + 1):
            for dz in range(-r, r + 1):
                dist_sq = dx * dx + dz * dz
                if dist_sq > r * r:
                    continue
                if dist_sq > r * r * 0.6 and random.random() < 0.22:
                    continue
                lx = int(trunk_cx + dx)
                lz = int(trunk_cz + dz)
                b.setblock(lx, y, lz, OAK_LEAVES)

                if dy_off <= 0 and dist_sq > (r - 2) ** 2:
                    vine_hang_points.append((lx, y, lz))

    # vine 垂 5-7 格
    vine_hang_points = list(set(vine_hang_points))
    random.shuffle(vine_hang_points)
    vine_count = min(len(vine_hang_points), random.randint(18, 28))

    for vx, vy, vz in vine_hang_points[:vine_count]:
        facing = _get_vine_facing(vx, vz, new_wx + 0.5, new_wz + 0.5)
        vine_len = random.randint(5, 7)
        for vdy in range(vine_len):
            target_y = vy - 1 - vdy
            if target_y <= GROUND_Y:
                break
            b.setblock(vx, target_y, vz, facing)

    print(f"    垂杨完成: ({new_wx},{new_wz}), 高{trunk_h}格, "
          f"冠径{h_radius*2}, 藤{vine_count}条")


# ══════════════════════════════════════════════════════════════
#  2. 廊桥中段底部空洞
# ══════════════════════════════════════════════════════════════

def fix_bridge_deck(b):
    """补铺廊桥中段(微拱区) Y=-60 的桥面。

    廊桥 v3: cx=45, X:43~47, Z:35~55
    微拱区 deck_y=-59 的 Z 段，其 Y=-60 层是空气 -> 补铺 oak_planks。
    同时确保所有 Z 段在 Y=-60 和 Y=-59 都有实心方块。
    """
    print("=== [2] 修复廊桥中段底部空洞 ===")

    cx = BRIDGE["cx"]           # 45
    z_s = BRIDGE["z_start"]     # 35
    z_e = BRIDGE["z_end"]       # 55
    w = BRIDGE["width"]         # 5
    half = w // 2               # 2

    bx_w = cx - half            # 43
    bx_e = cx + half            # 47

    # 微拱参数 (与 circulation.py build_bridge 一致)
    mid = (z_s + z_e) // 2          # 45
    half_span = (z_e - z_s) // 2    # 10
    arch_boundary = half_span // 3  # 3

    def deck_y(z):
        dist_from_mid = abs(z - mid)
        if dist_from_mid <= arch_boundary:
            return -59
        return -60

    # 遍历整个桥面，确保 Y=-60 都有实心方块
    for z in range(z_s, z_e + 1):
        dy = deck_y(z)
        if dy == -59:
            # 微拱段: 桥面在 -59，补铺 -60
            b.fill(bx_w, -60, z, bx_e, -60, z, OAK_PLANKS)
        # 同时确保 deck_y 层本身也有方块 (理论上已有，保险补一下)
        b.fill(bx_w, dy, z, bx_e, dy, z, OAK_PLANKS)

    print(f"    廊桥底部空洞已补铺: X={bx_w}~{bx_e}, Z={z_s}~{z_e}")


# ══════════════════════════════════════════════════════════════
#  3. 廊桥 -> 翠轩连接路
# ══════════════════════════════════════════════════════════════

def fix_bridge_to_hall_path(b):
    """铺设翠轩东边到廊桥西边的石砖路。

    翠轩东边 X=24, 廊桥西边 X=43, 中间 19 格空隙。
    铺 3 格宽 stone_bricks 路: X=25~42, Z=34~36, Y=-60
    翠轩台基处(X=24) 放一级台阶 stone_brick_stairs[facing=east]
    """
    print("=== [3] 修复廊桥->翠轩连接路 ===")

    path_y = BUILD_Y        # -60
    path_z1 = 34
    path_z2 = 36
    path_x1 = 25            # 翠轩东边 +1
    path_x2 = 42            # 廊桥西边 -1

    # 铺石砖路面
    b.fill(path_x1, path_y, path_z1, path_x2, path_y, path_z2, STONE_BRICK)

    # 路面下方填实 (Y=-61 确保不悬空)
    b.fill(path_x1, GROUND_Y, path_z1, path_x2, GROUND_Y, path_z2,
           PALETTE["dirt"])

    # 翠轩台基处放一级台阶 (X=24, 从翠轩台基走下到路面)
    # facing=east 表示低端朝东，人从东侧(路面)踏上向西进翠轩
    for z in range(path_z1, path_z2 + 1):
        b.setblock(24, path_y, z,
                   "minecraft:stone_brick_stairs[facing=east,half=bottom]")

    print(f"    连接路完成: X={path_x1}~{path_x2}, Z={path_z1}~{path_z2}, "
          f"Y={path_y}")
    print(f"    翠轩台阶: X=24, Z={path_z1}~{path_z2}")


# ══════════════════════════════════════════════════════════════
#  4. 曲廊起点月洞门
# ══════════════════════════════════════════════════════════════

def fix_corridor_start_gate(b):
    """在曲廊A起点处建白墙+月洞门。

    位置: X=58, Z=65~71
    月洞门半径2, 中心 Z=68 对准曲廊A (55, 68)
    墙体: 白墙(white_concrete) 高5格
    月洞门: circle_yz 在 YZ 平面开洞, 朝东西向通行
    """
    print("=== [4] 修复曲廊起点月洞门 ===")

    gate_x = 58
    gate_z_center = 68       # 对准曲廊 A
    gate_r = 2               # 月洞门半径
    wall_z1 = 65
    wall_z2 = 71
    y0 = BUILD_Y             # -60
    wall_h = 5               # 墙高5格

    # ── 4A. 清除旧结构 (如果之前有 fix_corridor_endpoints 建的门) ──
    b.fill(gate_x - 1, y0, wall_z1 - 1,
           gate_x + 1, y0 + wall_h + 2, wall_z2 + 1, AIR)

    # ── 4B. 建白墙: X=58, Z=65~71, Y=y0+1 ~ y0+wall_h ──
    for z in range(wall_z1, wall_z2 + 1):
        # 墙基 (第1格): 石砖
        b.setblock(gate_x, y0 + 1, z, WALL_BASE)
        # 墙身 (第2~4格): 白色混凝土
        for dy in range(2, wall_h):
            b.setblock(gate_x, y0 + dy, z, WALL_BLOCK)
        # 压顶 (第5格): 石砖半砖
        b.setblock(gate_x, y0 + wall_h, z,
                   f"{WALL_CAP}[type=top]")

    # ── 4C. 凿月洞门 (YZ 平面, 半径=2) ──
    # 圆心: Y = y0 + 2, Z = gate_z_center
    # 使得圆底部在 y0 层 (地面可通行)
    center_y = y0 + 2
    center_z = gate_z_center

    # 使用 circle_yz 思路: 在圆内区域全部清空
    for dy in range(-gate_r, gate_r + 1):
        for dz in range(-gate_r, gate_r + 1):
            if dy * dy + dz * dz <= gate_r * gate_r:
                py = center_y + dy
                pz = center_z + dz
                if py >= y0:  # 包括地面层，确保可通行
                    b.setblock(gate_x, py, pz, AIR)

    # ── 4D. 月洞门框描边 (石砖环, 增加辨识度) ──
    for dy in range(-gate_r - 2, gate_r + 3):
        for dz in range(-gate_r - 2, gate_r + 3):
            dist_sq = dy * dy + dz * dz
            # 半径 r 到 r+1.5 之间的环形区域
            if gate_r * gate_r < dist_sq <= (gate_r + 1.5) ** 2:
                py = center_y + dy
                pz = center_z + dz
                if y0 + 1 <= py <= y0 + wall_h and wall_z1 <= pz <= wall_z2:
                    b.setblock(gate_x, py, pz, STONE_BRICK)

    # ── 4E. 月洞门底部地面 (确保门洞可走) ──
    for z in range(gate_z_center - 1, gate_z_center + 2):
        b.setblock(gate_x, y0, z, FLOOR)

    # ── 4F. 门额横梁 + 装饰 ──
    # 门洞上方一条横梁
    b.fill(gate_x, y0 + 4, gate_z_center - 1,
           gate_x, y0 + 4, gate_z_center + 1,
           PALETTE["beam"])

    # 门洞两侧灯笼
    b.setblock(gate_x - 1, y0 + 3, gate_z_center - gate_r - 1,
               f'{LANTERN}[hanging=false]')
    b.setblock(gate_x - 1, y0 + 3, gate_z_center + gate_r + 1,
               f'{LANTERN}[hanging=false]')

    print(f"    月洞门完成: X={gate_x}, Z={wall_z1}~{wall_z2}, "
          f"门心Z={gate_z_center}, R={gate_r}")


# ══════════════════════════════════════════════════════════════
#  5. 曲廊终点前庭
# ══════════════════════════════════════════════════════════════

def fix_corridor_end_court(b):
    """在曲廊H(70,15)前建前庭。

    前庭范围: X=71~72, Z=11~19
    铺地: smooth_stone + stone_bricks 交替(棋盘格)
    南北端各放一个灯笼
    """
    print("=== [5] 修复曲廊终点前庭 ===")

    hx, hz = CORRIDOR["waypoints"][7]  # (70, 15)
    # 前庭在 H 点东侧 (X 增大方向)
    court_x1 = 71
    court_x2 = 72
    court_z1 = 11
    court_z2 = 19
    # 前庭高度与爬山廊终点齐平
    court_y = -57  # PAVILION ground_y

    # ── 5A. 清除前庭区域上方障碍 ──
    b.fill(court_x1, court_y + 1, court_z1,
           court_x2, court_y + 6, court_z2, AIR)

    # ── 5B. 前庭下方填实 (支撑) ──
    for fill_y in range(GROUND_Y, court_y):
        b.fill(court_x1, fill_y, court_z1,
               court_x2, fill_y, court_z2, PALETTE["stone"])

    # ── 5C. 铺地: smooth_stone + stone_bricks 交替 (棋盘格) ──
    for x in range(court_x1, court_x2 + 1):
        for z in range(court_z1, court_z2 + 1):
            if (x + z) % 2 == 0:
                b.setblock(x, court_y, z, FLOOR)      # smooth_stone
            else:
                b.setblock(x, court_y, z, STONE_BRICK) # stone_bricks

    # ── 5D. 南北端灯笼 ──
    # 南端 (Z=19): 灯笼台
    b.setblock(court_x1, court_y + 1, court_z2, STONE_BRICK)
    b.setblock(court_x1, court_y + 2, court_z2,
               f'{LANTERN}[hanging=false]')

    # 北端 (Z=11): 灯笼台
    b.setblock(court_x1, court_y + 1, court_z1, STONE_BRICK)
    b.setblock(court_x1, court_y + 2, court_z1,
               f'{LANTERN}[hanging=false]')

    print(f"    前庭完成: X={court_x1}~{court_x2}, Z={court_z1}~{court_z2}, "
          f"Y={court_y}")
    print(f"    灯笼: Z={court_z1}(北), Z={court_z2}(南)")


# ══════════════════════════════════════════════════════════════
#  主函数
# ══════════════════════════════════════════════════════════════

def fix_all(b):
    """一键修复所有碰撞和衔接问题。"""
    print("=" * 60)
    print("  碰撞和衔接问题一次性修复")
    print("=" * 60)

    fix_trees_collision(b)       # 1. 移树
    fix_bridge_deck(b)           # 2. 补桥面
    fix_bridge_to_hall_path(b)   # 3. 铺路
    fix_corridor_start_gate(b)   # 4. 月洞门
    fix_corridor_end_court(b)    # 5. 前庭

    # 注册边界框
    b.register_bbox("fix_trees_collision",
                    -5, GROUND_Y, 14,
                    30, BUILD_Y + 16, 40)
    b.register_bbox("fix_bridge_deck",
                    43, -60, 35,
                    47, -59, 55)
    b.register_bbox("fix_bridge_to_hall_path",
                    24, GROUND_Y, 34,
                    42, BUILD_Y, 36)
    b.register_bbox("fix_corridor_start_gate",
                    56, BUILD_Y, 64,
                    60, BUILD_Y + 7, 72)
    b.register_bbox("fix_corridor_end_court",
                    71, GROUND_Y, 11,
                    72, -55, 19)

    print("=" * 60)
    print("  全部修复完成!")
    print("=" * 60)


if __name__ == "__main__":
    with MinecraftBuilder() as b:
        fix_all(b)
        print(f"Done! {b.cmd_count} commands")
