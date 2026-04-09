"""南面水乡灵魂细节 — 马头墙 + 河埠头 + 乌篷船

修复内容:
  1. 马头墙(封火墙) — 5栋民居东西山墙面加 2-3 级阶梯状高出屋脊
  2. 河埠头(石阶下河) — 运河北岸 3 处石砖楼梯通向水面
  3. 乌篷船 — 运河水面 1 条深色小船

用法:
    from fixes.fix_south_details import fix_south_details
    fix_south_details(b)
"""

import sys; sys.path.insert(0, '/Users/lambertlin/minecraft-server/scripts')
from blocks import BUILD_Y, GROUND_Y

# ── 方块 ──
WHITE_CONCRETE = "minecraft:white_concrete"
STONE_BRICK_SLAB = "minecraft:stone_brick_slab"
STONE_BRICK_STAIRS = "minecraft:stone_brick_stairs"
STONE_BRICK_WALL = "minecraft:stone_brick_wall"
STONE_BRICKS = "minecraft:stone_bricks"
DARK_OAK_PLANKS = "minecraft:dark_oak_planks"
DARK_OAK_SLAB = "minecraft:dark_oak_slab"
BLACK_WOOL = "minecraft:black_wool"
SPRUCE_FENCE = "minecraft:spruce_fence"
AIR = "minecraft:air"

# ══════════════════════════════════════════════════════════════
#  民居精确参数 (random.seed(300) 下的确定性结果)
# ══════════════════════════════════════════════════════════════

# (x1, x2, z1, z2, z_mid, half_span, gable_top_y)
HOUSES = [
    # House 0: width=8, depth=11
    (35, 42, 108, 118, 113, 5, -47),
    # House 1: width=9, depth=9
    (47, 55, 108, 116, 112, 4, -48),
    # House 2: width=8, depth=11
    (58, 65, 108, 118, 113, 5, -47),
    # House 3: width=9, depth=11
    (68, 76, 108, 118, 113, 5, -47),
    # House 4: width=9, depth=10
    (78, 86, 108, 117, 112, 4, -48),
]


# ══════════════════════════════════════════════════════════════
#  1. 马头墙 (封火墙)
# ══════════════════════════════════════════════════════════════

def fix_horse_head_walls(b):
    """每栋民居东西山墙面加马头墙: 阶梯状高出屋脊, 石砖半砖收顶"""
    print("  [1/3] 马头墙...")

    for i, (x1, x2, z1, z2, z_mid, half_span, gable_top_y) in enumerate(HOUSES):
        _add_horse_head_wall(b, x1, x2, z1, z2, z_mid, half_span, gable_top_y)
        print(f"    民居 {i} 马头墙完成")


def _add_horse_head_wall(b, x1, x2, z1, z2, z_mid, half_span, gable_top_y):
    """
    在山墙 (x=x1 和 x=x2) 顶部加马头墙。

    马头墙设计:
      - 从现有山墙三角形的顶部向上延伸
      - 分 2-3 级, 每级宽度递减, 形成阶梯轮廓
      - 每级顶部用 stone_brick_slab 做小坡水收顶

    现有山墙三角形: 从 y_ceil2=-52 到 gable_top_y, 每层宽度递减
    马头墙在三角形的中上部"突破"屋顶线, 高出 2-3 格

    策略: 取山墙三角形中间几层, 在原有位置上方加高 2-3 格
    形成视觉上的阶梯状突出
    """
    depth = z2 - z1 + 1

    # 马头墙分级: 从山墙三角的底层到顶层, 选 2-3 级做突出
    # 级数和层高根据房子大小调整
    if half_span >= 5:
        # 大房子 (depth=11): 3 级马头墙
        # 第1级 (最宽): 覆盖 gable layer 0-1 对应的 z 范围, 高出 3 格
        # 第2级 (中等): 覆盖 gable layer 2-3, 高出 2 格
        # 第3级 (最窄): 覆盖 gable layer 4, 高出 1 格
        levels = [
            # (z_start, z_end, extra_height) — 马头墙每级的 z 范围和额外高度
            (z1, z1 + 3, 3),       # 第1级: 最外4格, 高出3
            (z1 + 4, z_mid, 2),    # 第2级: 到中线, 高出2
        ]
        # 对称设计: 南侧
        levels_south = [
            (z2 - 3, z2, 3),
            (z2 - 6, z2 - 4, 2),
        ]
    else:
        # 小房子 (depth=9/10): 2 级马头墙
        levels = [
            (z1, z1 + 2, 3),       # 第1级: 外3格, 高出3
            (z1 + 3, z1 + 4, 2),   # 第2级: 中2格, 高出2
        ]
        levels_south = [
            (z2 - 2, z2, 3),
            (z2 - 4, z2 - 3, 2),
        ]

    for x_wall in [x1, x2]:
        # 北半侧马头墙
        for (zs, ze, extra_h) in levels:
            zs = max(zs, z1)
            ze = min(ze, z_mid)
            if zs > ze:
                continue
            # 找这个 z 范围内原有山墙最高 y
            # 山墙三角: 在 layer L, y = -52 + L, z 范围 = [z_mid - (half_span-L), z_mid + (half_span-L)]
            # 对于 z = zs, 它出现在 layer 满足 z_mid - (half_span - L) <= zs, 即 L >= half_span - (z_mid - zs)
            first_layer = max(0, half_span - (z_mid - zs))
            base_y = -52 + first_layer  # 这个z在山墙上首次出现的y

            # 马头墙: 每个z从该z的山墙实际高度开始向上延伸
            for z in range(zs, ze + 1):
                # 该z在山墙三角中的实际最高Y
                local_layer = max(0, half_span - abs(z_mid - z))
                local_top_y = -52 + local_layer
                for dy in range(extra_h):
                    y = local_top_y + 1 + dy
                    b.setblock(x_wall, y, z, WHITE_CONCRETE)

            # 顶部收顶: 用最高z的local_top_y + extra_h
            cap_y = base_y + extra_h + 1  # base_y是该段最低z的山墙高度
            for z in range(zs, ze + 1):
                b.setblock(x_wall, cap_y, z,
                           f"{STONE_BRICK_SLAB}[type=bottom]")
            # 阶梯过渡斜面: 最外侧z用楼梯衔接
            if zs > z1:
                b.setblock(x_wall, gable_top_y + extra_h, zs - 1,
                           f"{STONE_BRICK_STAIRS}[facing=south,half=bottom]")

        # 南半侧马头墙 (对称)
        for (zs, ze, extra_h) in levels_south:
            zs = max(zs, z_mid)
            ze = min(ze, z2)
            if zs > ze:
                continue

            for z in range(zs, ze + 1):
                local_layer = max(0, half_span - abs(z_mid - z))
                local_top_y = -52 + local_layer
                for dy in range(extra_h):
                    y = local_top_y + 1 + dy
                    b.setblock(x_wall, y, z, WHITE_CONCRETE)

            first_layer_s = max(0, half_span - abs(z_mid - ze))
            cap_y = (-52 + first_layer_s) + extra_h + 1
            for z in range(zs, ze + 1):
                b.setblock(x_wall, cap_y, z,
                           f"{STONE_BRICK_SLAB}[type=bottom]")
            if ze < z2:
                b.setblock(x_wall, gable_top_y + extra_h, ze + 1,
                           f"{STONE_BRICK_STAIRS}[facing=north,half=bottom]")


# ══════════════════════════════════════════════════════════════
#  2. 河埠头 (石阶下河)
# ══════════════════════════════════════════════════════════════

# 河埠头位置: 民居之间, 运河北岸 Z=96 (步道边沿)
# House gaps: 42-47, 55-58 (太近码头), 65-68, 76-78
# 选 3 处有意义的位置
RIVER_STEP_POSITIONS = [
    38,  # house0 西侧（从43改为38，避开桥X=45）
    66,  # house2 和 house3 之间（无近桥，安全）
    82,  # house4 东侧（从77改为82，避开桥X=75）
]

# 步道面 Y=BUILD_Y=-60, 水面 Y=GROUND_Y=-61
# 北岸步道 Z=94-95, 运河从 Z=97 开始
# 岸边楼梯: Z=96 (原有 stone_brick_stairs facing=south)
# 河埠头: 从 Z=95 (步道) 下阶梯到 Z=97~98 (水中)

def fix_river_steps(b):
    """3 处河埠头: 石砖楼梯从步道下到水面"""
    print("  [2/3] 河埠头...")

    for x_center in RIVER_STEP_POSITIONS:
        _build_river_steps(b, x_center, z_bank=96)
        print(f"    河埠头 @ X={x_center}")


def _build_river_steps(b, x_center, z_bank):
    """
    河埠头: 3格宽石砖楼梯, 从步道面下到水面, 两侧石砖墙柱

    结构 (侧视图, 从西向东看):
        步道 Y=-60 Z=95  ___
                             |___  Y=-61 Z=96 (第1级)
                                  |___  Y=-62 Z=97 (第2级, 水面)
                                       |___  Y=-63 Z=98 (第3级, 水下)

    从北向南走, z 增大, 向下进水
    """
    # 清空河埠头上方空间 (用 fill 节省命令)
    b.fill(x_center - 2, BUILD_Y, z_bank,
           x_center + 2, BUILD_Y + 3, z_bank + 3, AIR)

    # 第1级台阶: Y=-60, Z=96 — facing=north(低端朝北=朝水面方向下行)
    for dx in range(-1, 2):
        b.setblock(x_center + dx, BUILD_Y, z_bank,
                   f"{STONE_BRICK_STAIRS}[facing=north,half=bottom]")

    # 第2级台阶: Y=-61, Z=97
    for dx in range(-1, 2):
        b.setblock(x_center + dx, GROUND_Y, z_bank + 1,
                   f"{STONE_BRICK_STAIRS}[facing=north,half=bottom]")

    # 第3级台阶: Y=-62, Z=98 (水下, 洗衣台)
    for dx in range(-1, 2):
        b.setblock(x_center + dx, GROUND_Y - 1, z_bank + 2,
                   f"{STONE_BRICK_STAIRS}[facing=north,half=bottom]")

    # 两侧石墙柱 (从步道面到水面以下, 3 级高度)
    for dx_side in [-2, 2]:
        x = x_center + dx_side
        # 柱子从 Y=-60 到 Y=-63 (4格高, 嵌入水中)
        for y in range(BUILD_Y, GROUND_Y - 2, -1):
            b.setblock(x, y, z_bank, STONE_BRICK_WALL)
        b.setblock(x, y, z_bank + 1, STONE_BRICK_WALL)
        # 柱顶装饰
        b.setblock(x, BUILD_Y + 1, z_bank, STONE_BRICK_WALL)

    # 台阶两侧护墙 (石砖, 防滑入水)
    for dx_side in [-2, 2]:
        x = x_center + dx_side
        b.setblock(x, GROUND_Y, z_bank + 1, STONE_BRICKS)
        b.setblock(x, GROUND_Y - 1, z_bank + 2, STONE_BRICKS)

    # 步道面平台恢复 (确保两侧步道连贯)
    for dx_side in [-2, 2]:
        b.setblock(x_center + dx_side, BUILD_Y, z_bank - 1,
                   f"{STONE_BRICK_SLAB}[type=bottom]")


# ══════════════════════════════════════════════════════════════
#  3. 乌篷船
# ══════════════════════════════════════════════════════════════

def fix_wupeng_boat(b):
    """运河中 1 条乌篷船: 深色橡木船体 + 黑色羊毛篷顶"""
    print("  [3/3] 乌篷船...")

    # 船位置: X=52~56, Z=99 (运河中央), 水面 Y=GROUND_Y=-61
    boat_x = 52
    boat_z = 99
    water_y = GROUND_Y  # -61

    # 船体: 深色橡木板, 2宽 x 5长, 在水面高度
    # 船底
    for dx in range(5):
        for dz in range(2):
            b.setblock(boat_x + dx, water_y, boat_z + dz, DARK_OAK_PLANKS)

    # 船舷 (两侧加高1格, 用楼梯模拟弧度)
    for dx in range(5):
        b.setblock(boat_x + dx, water_y + 1, boat_z - 1,
                   f"minecraft:dark_oak_stairs[facing=south,half=bottom]")
        b.setblock(boat_x + dx, water_y + 1, boat_z + 2,
                   f"minecraft:dark_oak_stairs[facing=north,half=bottom]")

    # 船头船尾 (楼梯收尖)
    b.setblock(boat_x - 1, water_y + 1, boat_z,
               f"minecraft:dark_oak_stairs[facing=east,half=bottom]")
    b.setblock(boat_x - 1, water_y + 1, boat_z + 1,
               f"minecraft:dark_oak_stairs[facing=east,half=bottom]")
    b.setblock(boat_x + 5, water_y + 1, boat_z,
               f"minecraft:dark_oak_stairs[facing=west,half=bottom]")
    b.setblock(boat_x + 5, water_y + 1, boat_z + 1,
               f"minecraft:dark_oak_stairs[facing=west,half=bottom]")

    # 篷顶骨架: 中间 3 格有顶棚 (X=53~55)
    # 用栅栏做支撑柱, 黑色羊毛做篷
    for dx in [1, 3]:  # 两根支撑柱 (相对 boat_x)
        b.setblock(boat_x + dx, water_y + 1, boat_z, SPRUCE_FENCE)
        b.setblock(boat_x + dx, water_y + 1, boat_z + 1, SPRUCE_FENCE)
        b.setblock(boat_x + dx, water_y + 2, boat_z, SPRUCE_FENCE)
        b.setblock(boat_x + dx, water_y + 2, boat_z + 1, SPRUCE_FENCE)

    # 篷顶: 黑色羊毛半砖效果 (用 dark_oak_slab 模拟竹篷)
    for dx in range(1, 4):  # 篷覆盖 3 格
        b.setblock(boat_x + dx, water_y + 3, boat_z - 1,
                   f"{DARK_OAK_SLAB}[type=bottom]")
        b.setblock(boat_x + dx, water_y + 3, boat_z, BLACK_WOOL)
        b.setblock(boat_x + dx, water_y + 3, boat_z + 1, BLACK_WOOL)
        b.setblock(boat_x + dx, water_y + 3, boat_z + 2,
                   f"{DARK_OAK_SLAB}[type=bottom]")

    print("    乌篷船完成")


# ══════════════════════════════════════════════════════════════
#  总控
# ══════════════════════════════════════════════════════════════

def fix_south_details(b):
    """南面水乡灵魂细节 — 马头墙 + 河埠头 + 乌篷船"""
    print("=== 南面水乡细节修复 ===")

    fix_horse_head_walls(b)
    fix_river_steps(b)
    fix_wupeng_boat(b)

    print("=== 南面水乡细节修复完成 ===")


if __name__ == "__main__":
    from builder import MinecraftBuilder
    with MinecraftBuilder() as b:
        fix_south_details(b)
        print(f"Done! {b.cmd_count} commands")
