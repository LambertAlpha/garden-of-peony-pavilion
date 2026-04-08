"""翠轩/池馆 — 临水赏景敞厅
"朝飞暮卷，云霞翠轩" "池馆苍苔一片青"
悬山顶，东面(面水)全开敞，西面白墙，南北花窗
"""

import sys; sys.path.insert(0, '/Users/lambertlin/minecraft-server/scripts')
from builder import MinecraftBuilder
from blocks import PALETTE
import random


def build_hall(b: MinecraftBuilder, cx: int, ground_y: int, cz: int):
    """建造翠轩/池馆

    Args:
        cx, cz: 建筑中心 XZ 坐标
        ground_y: 地面 Y 坐标（台基底部）
    """
    print(f"=== 翠轩 at ({cx}, {ground_y}, {cz}) ===")
    random.seed(43)

    # ── 坐标常量 ──
    # 台基: 13(X进深) × 8(Z面阔), 1格高
    base_x1, base_x2 = cx - 6, cx + 6   # 13格 X方向
    base_z1, base_z2 = cz - 3, cz + 4   # 8格 Z方向
    base_y = ground_y                     # 台基底面
    floor_y = ground_y + 1                # 台基顶面 / 地面层

    # 柱子参数
    pillar_height = 5
    pillar_top_y = floor_y + pillar_height  # 柱顶 Y
    front_x = cx + 5   # 前排柱 X（面水/东）
    back_x = cx - 5    # 后排柱 X（靠山/西）
    pillar_zs = [cz - 3, cz, cz + 3]      # 柱子 Z 位置

    # ────────────────────────────────────
    # 1. 台基（石砖 + 苔藓石砖混铺）
    # ────────────────────────────────────
    print("  [1/7] 台基...")
    b.fill(base_x1, base_y, base_z1, base_x2, base_y, base_z2, PALETTE["base"])

    # 苍苔效果：约 20% 替换为苔藓石砖 — "池馆苍苔一片青"
    for x in range(base_x1, base_x2 + 1):
        for z in range(base_z1, base_z2 + 1):
            if random.random() < 0.20:
                b.setblock(x, base_y, z, PALETTE["wall_mossy"])

    # 台基顶面铺 smooth_stone 地面
    b.fill(base_x1, floor_y, base_z1, base_x2, floor_y, base_z2, PALETTE["floor"])

    # ────────────────────────────────────
    # 2. 柱子（6根金合欢柱）
    # ────────────────────────────────────
    print("  [2/7] 柱子...")
    for pz in pillar_zs:
        # 前排（东面/面水）
        for y in range(floor_y + 1, pillar_top_y + 1):
            b.setblock(front_x, y, pz, PALETTE["pillar"])
        # 柱础
        b.setblock(front_x, floor_y, pz, PALETTE["base_col"])

        # 后排（西面/靠山）
        for y in range(floor_y + 1, pillar_top_y + 1):
            b.setblock(back_x, y, pz, PALETTE["pillar"])
        b.setblock(back_x, floor_y, pz, PALETTE["base_col"])

    # ────────────────────────────────────
    # 3. 梁枋（柱顶横梁）
    # ────────────────────────────────────
    print("  [3/7] 梁枋...")
    # 南北向横梁（前排、后排各一道）
    b.fill(front_x, pillar_top_y, pillar_zs[0],
           front_x, pillar_top_y, pillar_zs[-1], PALETTE["beam"])
    b.fill(back_x, pillar_top_y, pillar_zs[0],
           back_x, pillar_top_y, pillar_zs[-1], PALETTE["beam"])

    # 东西向横梁（连接前后排柱顶，3道）
    for pz in pillar_zs:
        b.fill(back_x, pillar_top_y, pz,
               front_x, pillar_top_y, pz, PALETTE["beam"])

    # ────────────────────────────────────
    # 4. 墙体与花窗
    # ────────────────────────────────────
    print("  [4/7] 墙体与花窗...")

    # 西墙（背水面）：白墙，从台基顶到柱顶
    # 从 back_x 面、Z范围在两端柱之间
    wall_z1, wall_z2 = pillar_zs[0], pillar_zs[-1]
    for y in range(floor_y + 1, pillar_top_y):
        for z in range(wall_z1 + 1, wall_z2):
            b.setblock(back_x, y, z, PALETTE["wall"])

    # 南墙（Z=pillar_zs[0] 面）：下2格白墙 + 上2格花窗
    for y_offset in range(1, 5):
        y = floor_y + y_offset
        for x in range(back_x + 1, front_x):
            if y_offset <= 2:
                # 下半：白墙
                b.setblock(x, y, wall_z1, PALETTE["wall"])
            else:
                # 上半：花窗（jungle_trapdoor，打开状态朝南）
                b.setblock(x, y, wall_z1,
                           f'{PALETTE["trapdoor"]}[facing=south,half=top,open=true]')

    # 北墙（Z=pillar_zs[-1] 面）：下2格白墙 + 上2格花窗
    for y_offset in range(1, 5):
        y = floor_y + y_offset
        for x in range(back_x + 1, front_x):
            if y_offset <= 2:
                b.setblock(x, y, wall_z2, PALETTE["wall"])
            else:
                b.setblock(x, y, wall_z2,
                           f'{PALETTE["trapdoor"]}[facing=north,half=top,open=true]')

    # 东面完全开敞（不建墙）

    # ────────────────────────────────────
    # 5. 悬山顶（两面坡屋顶）
    # ────────────────────────────────────
    print("  [5/7] 悬山顶...")

    # 屋顶范围：
    #   Z方向(脊线/南北)：悬山各超出墙体1格
    #   X方向(东西坡)：出檐各超出柱位1格
    roof_z1 = pillar_zs[0] - 1   # 悬山南出檐
    roof_z2 = pillar_zs[-1] + 1  # 悬山北出檐

    roof_stair = PALETTE["roof"]
    roof_block = PALETTE["roof_block"]
    roof_slab = PALETTE["roof_slab"]

    # 屋顶坡面设计（从下到上）：
    #   建筑宽度: back_x(cx-5) 到 front_x(cx+5)，出檐到 cx-6 和 cx+6
    #   出檐层(柱顶+1): 最宽，东坡cx+6，西坡cx-6  (半坡宽6格)
    #   第2层(柱顶+2): 内缩2格 → 东cx+4, 西cx-4
    #   第3层(柱顶+3): 内缩2格 → 东cx+2, 西cx-2
    #   第4层(柱顶+4): 脊线 → cx 处放半砖
    # 每层内缩2格，3层楼梯+1层脊线，坡度约 1:2（舒缓坡度，符合南方建筑）

    roof_layers = [
        # (y_offset, east_x, west_x, is_ridge)
        (1, cx + 6, cx - 6, False),   # 出檐层（最宽）
        (2, cx + 4, cx - 4, False),   # 第2层
        (3, cx + 2, cx - 2, False),   # 第3层
        (4, cx,     cx,     True),    # 脊线
    ]

    for y_off, east_x, west_x, is_ridge in roof_layers:
        y = pillar_top_y + y_off

        if is_ridge:
            # 脊线：半砖
            for z in range(roof_z1, roof_z2 + 1):
                b.setblock(east_x, y, z, f'{roof_slab}[type=bottom]')
        else:
            # 东坡楼梯 (facing=west — 楼梯台面朝东、下降朝西 = 东坡)
            for z in range(roof_z1, roof_z2 + 1):
                b.setblock(east_x, y, z, f'{roof_stair}[facing=west,half=bottom]')

            # 西坡楼梯 (facing=east — 台面朝西、下降朝东 = 西坡)
            for z in range(roof_z1, roof_z2 + 1):
                b.setblock(west_x, y, z, f'{roof_stair}[facing=east,half=bottom]')

            # 两坡之间填充实心方块
            if west_x + 1 < east_x:
                b.fill(west_x + 1, y, roof_z1,
                       east_x - 1, y, roof_z2, roof_block)

    # ────────────────────────────────────
    # 6. 美人靠（面水侧倒置楼梯栏杆）
    # ────────────────────────────────────
    print("  [6/7] 美人靠...")

    # 前排柱间，用倒置金合欢楼梯模拟栏杆
    meiren_y = floor_y + 1  # 栏杆高度（坐凳高度）
    meiren_block = "minecraft:acacia_stairs[facing=west,half=top]"

    # 柱1 到 柱2 之间
    for z in range(pillar_zs[0] + 1, pillar_zs[1]):
        b.setblock(front_x, meiren_y, z, meiren_block)
    # 柱2 到 柱3 之间
    for z in range(pillar_zs[1] + 1, pillar_zs[2]):
        b.setblock(front_x, meiren_y, z, meiren_block)

    # ────────────────────────────────────
    # 7. 装饰细节
    # ────────────────────────────────────
    print("  [7/7] 装饰细节...")

    # 灯笼：挂在梁下（前后排各一盏，居中）
    b.setblock(front_x, pillar_top_y - 1, cz,
               f'{PALETTE["lantern"]}[hanging=true]')
    b.setblock(back_x, pillar_top_y - 1, cz,
               f'{PALETTE["lantern"]}[hanging=true]')

    # 柱间额外灯笼
    b.setblock(cx, pillar_top_y - 1, pillar_zs[0],
               f'{PALETTE["lantern"]}[hanging=true]')
    b.setblock(cx, pillar_top_y - 1, pillar_zs[-1],
               f'{PALETTE["lantern"]}[hanging=true]')

    # 注册边界框（用于撤销）
    b.register_bbox("hall",
                    base_x1 - 1, ground_y, roof_z1,
                    base_x2 + 1, pillar_top_y + 5, roof_z2)

    print(f"  翠轩建造完成！")


if __name__ == "__main__":
    with MinecraftBuilder() as b:
        build_hall(b, cx=12, ground_y=-60, cz=28)
        print(f"Done! {b.cmd_count} commands")
