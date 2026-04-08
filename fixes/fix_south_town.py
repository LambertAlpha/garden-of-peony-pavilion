"""南面江南水乡修复脚本

修复内容:
  1. fix_house_doors   — 民居门窗: 补装实际门方块、窗格铁栏杆、确认屋檐外挑
  2. fix_canal_connections — 运河-步道衔接: 园门到北岸路面连贯、灯笼间距、桥栏杆落地
  3. fix_market_details — 商业街生活感: 旗帜幌子、营火炊烟、花盆、货物暗示
  4. fix_south_all      — 汇总调用

用法:
    from fixes.fix_south_town import fix_south_all
    fix_south_all(b)
"""

import sys; sys.path.insert(0, '/Users/lambertlin/minecraft-server/scripts')
from blocks import PALETTE, GROUND_Y, BUILD_Y
import random


# ══════════════════════════════════════════════════════════════
#  常量 (与 south_town.py 保持一致)
# ══════════════════════════════════════════════════════════════

CANAL_X1, CANAL_X2 = 20, 100
CANAL_Z1, CANAL_Z2 = 97, 101

BRIDGE_POSITIONS = [45, 75]

HOUSE_X_STARTS = [35, 47, 58, 68, 78]
HOUSE_Z_FRONT = 108
HOUSE_DEPTH = 10
HOUSE_WIDTH = 9
HOUSE_TOTAL_H = 11

MARKET_X1, MARKET_X2 = 35, 85
MARKET_Z1, MARKET_Z2 = 104, 107

# 方块别名
STONE_BRICK = "minecraft:stone_bricks"
STONE_BRICK_SLAB = "minecraft:stone_brick_slab"
STONE_BRICK_STAIRS = "minecraft:stone_brick_stairs"
WHITE_CONCRETE = "minecraft:white_concrete"
SPRUCE_LOG = "minecraft:spruce_log"
SPRUCE_PLANKS = "minecraft:spruce_planks"
SPRUCE_SLAB = "minecraft:spruce_slab"
SPRUCE_STAIRS = "minecraft:spruce_stairs"
SPRUCE_TRAPDOOR = "minecraft:spruce_trapdoor"
SPRUCE_FENCE = "minecraft:spruce_fence"
SPRUCE_DOOR = "minecraft:spruce_door"
DARK_OAK_PLANKS = "minecraft:dark_oak_planks"
COBBLE_WALL = "minecraft:cobblestone_wall"
IRON_BARS = "minecraft:iron_bars"
LANTERN = "minecraft:lantern[hanging=false]"
HANGING_LANTERN = "minecraft:lantern[hanging=true]"
AIR = "minecraft:air"

# 生活细节方块
CAMPFIRE = "minecraft:campfire[lit=true]"
FLOWER_POT = "minecraft:potted_red_tulip"
FLOWER_POT_FERN = "minecraft:potted_fern"
FLOWER_POT_BAMBOO = "minecraft:potted_bamboo"
BARREL = "minecraft:barrel[facing=up]"
LOOM = "minecraft:loom[facing=north]"
CRAFTING_TABLE = "minecraft:crafting_table"
CAULDRON = "minecraft:water_cauldron[level=3]"
HAY_BLOCK = "minecraft:hay_block"
MELON = "minecraft:melon"
PUMPKIN = "minecraft:pumpkin"
RED_BANNER = "minecraft:red_wall_banner"
WHITE_BANNER = "minecraft:white_wall_banner"
SOUL_LANTERN = "minecraft:soul_lantern[hanging=false]"
SMOKER = "minecraft:smoker[facing=north,lit=true]"
COMPOSTER = "minecraft:composter[level=5]"


# ══════════════════════════════════════════════════════════════
#  1. 修复民居门窗
# ══════════════════════════════════════════════════════════════

def fix_house_doors(b):
    """修复所有民居的门窗问题:
    - 补装实际 spruce_door 方块 (朝北, 面向运河)
    - 窗户内侧加铁栏杆做窗格 (活板门+铁栏杆 = 完整窗)
    - 屋檐外挑检查 (Z方向已挑2格, X方向补到2格)
    """
    print("  [修复] 民居门窗...")
    random.seed(300)  # 与原始构建相同种子, 复现随机偏移

    for i, hx in enumerate(HOUSE_X_STARTS):
        # 复现原始随机变化
        depth = HOUSE_DEPTH + random.choice([-1, 0, 0, 1])
        width = HOUSE_WIDTH + random.choice([-1, 0, 0])
        _fix_one_house(b, hx, HOUSE_Z_FRONT, width, depth, i)
        print(f"    民居 {i+1} @ X={hx} ({width}x{depth}) — 门窗已修复")


def _fix_one_house(b, x_start, z_start, width, depth, index):
    """修复单栋民居的门、窗、屋檐"""
    x1 = x_start
    x2 = x_start + width - 1
    z1 = z_start           # 北面正面
    z2 = z_start + depth - 1
    mid_x = (x1 + x2) // 2

    y_base = BUILD_Y
    y_floor1 = y_base + 1
    y_ceil1 = y_base + 4
    y_ceil2 = y_base + 8

    # ── 修复1: 补装实际门 (一层正面中间, 朝北) ──
    # 原代码只清了空气, 没放门方块
    # Minecraft door: lower half + upper half
    b.setblock(mid_x, y_floor1, z1,
               f"{SPRUCE_DOOR}[facing=north,half=lower,hinge=left,open=false]")
    b.setblock(mid_x, y_floor1 + 1, z1,
               f"{SPRUCE_DOOR}[facing=north,half=upper,hinge=left,open=false]")
    # 门上方保留横梁
    b.setblock(mid_x, y_floor1 + 2, z1, DARK_OAK_PLANKS)

    # ── 修复2: 正面窗户加铁栏杆窗格 ──
    # 两层都修: 一层和二层
    for (y_bottom, y_top) in [(y_floor1, y_ceil1), (y_ceil1, y_ceil2)]:
        win_y1 = y_bottom + 1
        win_y2 = y_bottom + 2

        # 计算中间柱位置 (复现原始逻辑)
        step = 3 if (x2 - x1) <= 8 else 4
        mid_pillars_x = []
        px = x1 + step
        while px < x2:
            mid_pillars_x.append(px)
            px += step

        # 正面窗: 在活板门内侧加铁栏杆
        for x in range(x1 + 1, x2):
            if x in mid_pillars_x:
                continue
            if x == mid_x and y_bottom == y_floor1:
                continue  # 跳过门的位置

            rel = x - x1
            if rel % 2 == 0:
                # 活板门已经在 z1 面上, 在同位置再加铁栏杆
                # 铁栏杆放在窗洞中间 (替换原来的白色混凝土)
                b.setblock(x, win_y1, z1, IRON_BARS)
                b.setblock(x, win_y2, z1, IRON_BARS)
                # 活板门放在外侧: z1-1 (挑出面)
                # 实际上活板门开启后就是窗扇效果，放在z1面上
                # 保持活板门在z1, 铁栏杆需放在内侧z1+1
                # 但这样会占室内空间——更好的做法:
                # z1面放铁栏杆(窗格), 活板门放z1面外侧(open=true贴墙)
                # 重新设置: 铁栏杆在z1, 活板门在z1但open贴外墙
                b.setblock(x, win_y1, z1, IRON_BARS)
                b.setblock(x, win_y2, z1, IRON_BARS)
                # 外侧活板门 (窗扇装饰, 贴在z1面的北侧)
                # facing=south + open=true → 活板门翻起贴在z1北面
                # 注意: 上层窗扇用 half=top, 下层用 half=bottom
                # 但活板门 open=true 时是竖直的, 视觉上就是窗扇
                # 为了不遮挡铁栏杆, 把活板门放在 z1-1
                # 这样从外面看: 活板门(窗扇) | 铁栏杆(窗格) | 室内
                b.setblock(x, win_y1, z1 - 1,
                           f"{SPRUCE_TRAPDOOR}[facing=north,half=bottom,open=true]")
                b.setblock(x, win_y2, z1 - 1,
                           f"{SPRUCE_TRAPDOOR}[facing=north,half=top,open=true]")

        # 侧面窗 (东西墙) 也补铁栏杆
        mid_z = (z1 + z2) // 2
        for z in range(z1 + 2, z2 - 1, 3):
            # 西墙 x1
            b.setblock(x1, win_y1, z, IRON_BARS)
            b.setblock(x1, win_y2, z, IRON_BARS)
            b.setblock(x1 - 1, win_y1, z,
                       f"{SPRUCE_TRAPDOOR}[facing=east,half=bottom,open=true]")
            b.setblock(x1 - 1, win_y2, z,
                       f"{SPRUCE_TRAPDOOR}[facing=east,half=top,open=true]")
            # 东墙 x2
            b.setblock(x2, win_y1, z, IRON_BARS)
            b.setblock(x2, win_y2, z, IRON_BARS)
            b.setblock(x2 + 1, win_y1, z,
                       f"{SPRUCE_TRAPDOOR}[facing=west,half=bottom,open=true]")
            b.setblock(x2 + 1, win_y2, z,
                       f"{SPRUCE_TRAPDOOR}[facing=west,half=top,open=true]")

    # ── 修复3: 屋檐X方向补到2格外挑 ──
    # 原代码 overhang_x=1, 需要在 x1-2 和 x2+2 各补一排屋顶
    z_mid = (z1 + z2) // 2
    half_span = z_mid - z1
    overhang_z = 2

    for extra_x in [x1 - 2, x2 + 2]:
        for layer in range(half_span + 2):
            y = y_ceil2 + layer
            z_north = z_mid - (half_span + overhang_z - layer)
            z_south = z_mid + (half_span + overhang_z - layer)

            if z_north >= z_south:
                b.setblock(extra_x, y, z_mid, STONE_BRICK_SLAB)
                break

            b.setblock(extra_x, y, z_north,
                       f"{STONE_BRICK_STAIRS}[facing=south,half=bottom]")
            b.setblock(extra_x, y, z_south,
                       f"{STONE_BRICK_STAIRS}[facing=north,half=bottom]")

            # 中间填充防漏光
            for z in range(z_north + 1, z_south):
                b.setblock(extra_x, y, z, STONE_BRICK)


# ══════════════════════════════════════════════════════════════
#  2. 修复运河与步道衔接
# ══════════════════════════════════════════════════════════════

def fix_canal_connections(b):
    """修复运河到园门的路面连贯、灯笼间距、桥栏杆落地
    - 园门南端约Z=90, 北岸步道Z=94~95 → 补 Z=90~93 的路面
    - 灯笼间距改为6格 (更密, 更有氛围)
    - 石拱桥栏杆两端补落地段
    """
    print("  [修复] 运河-步道衔接...")

    # ── 修复1: Z=90~93 路面连接 (园门到北岸步道) ──
    # 从园墙外(Z=90)到北岸步道起点(Z=94)铺石砖路面
    # 路面宽度: 与南墙缺口对齐 (X=48~62), 再向两侧扩展到整条步道
    print("    补铺 Z=90~93 连接路面...")

    # 主路面: 全宽 (与步道等宽)
    for x in range(CANAL_X1, CANAL_X2 + 1):
        for z in range(90, 94):
            b.setblock(x, GROUND_Y, z, STONE_BRICK)
            b.setblock(x, BUILD_Y, z, STONE_BRICK_SLAB)

    # 园门正对的主通道 (X=48~62, 南墙缺口) 用更好的铺地
    for x in range(48, 63):
        for z in range(90, 94):
            b.setblock(x, GROUND_Y, z, STONE_BRICK)
            # 交替铺石砖半砖, 形成棋盘纹
            if (x + z) % 2 == 0:
                b.setblock(x, BUILD_Y, z, STONE_BRICK_SLAB)
            else:
                b.setblock(x, BUILD_Y, z,
                           f"{STONE_BRICK_STAIRS}[facing=south,half=bottom]")

    # ── 修复2: 补充灯笼使间距更均匀 ──
    # 原始: 北岸从X=22每8格, 南岸从X=26每8格
    # 修复: 在间距过大处(桥附近可能被遮挡)补灯笼
    # 同时在 Z=90~93 连接段也加灯笼
    print("    补充连接段灯笼...")

    lantern_ct = 0
    for x in range(CANAL_X1 + 4, CANAL_X2, 6):
        # Z=91 路灯 (连接段)
        b.setblock(x, BUILD_Y, 91, SPRUCE_FENCE)
        b.setblock(x, BUILD_Y + 1, 91, SPRUCE_FENCE)
        b.setblock(x, BUILD_Y + 2, 91, LANTERN)
        lantern_ct += 1

    print(f"    连接段灯笼 {lantern_ct} 盏")

    # ── 修复3: 石拱桥栏杆两端落地 ──
    # 原始栏杆: Z=96~102 范围 cobblestone_wall, 桥头柱在 Z=95,103
    # 问题: 北引桥Z=95面在 BUILD_Y (比桥面低1格), 栏杆悬空
    # 修复: 从桥头柱向下延伸到步道面
    print("    修复桥栏杆落地...")

    for bx in BRIDGE_POSITIONS:
        x1 = bx - 1
        x2 = bx + 1
        bridge_top_y = BUILD_Y + 1

        for x_side in [x1 - 1, x2 + 1]:
            # 北端 Z=95: 引桥面在 BUILD_Y, 桥头柱需要连到地面
            # 补一格 cobble_wall 在 BUILD_Y+1 at Z=95 (引桥面上方)
            # 桥头柱已有 bridge_top_y+1 和 +2, 补中间连接
            b.setblock(x_side, BUILD_Y, 95, STONE_BRICK)  # 基座
            b.setblock(x_side, BUILD_Y + 1, 95, COBBLE_WALL)

            # 同样补 Z=94 的一格过渡 (栏杆渐降到步道)
            b.setblock(x_side, BUILD_Y, 94, STONE_BRICK)
            b.setblock(x_side, BUILD_Y + 1, 94, COBBLE_WALL)

            # 南端 Z=103: 同理
            b.setblock(x_side, BUILD_Y, 103, STONE_BRICK)
            b.setblock(x_side, BUILD_Y + 1, 103, COBBLE_WALL)

            b.setblock(x_side, BUILD_Y, 104, STONE_BRICK)
            b.setblock(x_side, BUILD_Y + 1, 104, COBBLE_WALL)

        # 桥面与引桥之间补半砖过渡, 避免跳上跳下
        for x in range(x1, x2 + 1):
            # Z=95 从楼梯改为 slab (与桥面齐平)
            b.setblock(x, bridge_top_y, 95, STONE_BRICK_SLAB)
            # Z=94 加半砖台阶
            b.setblock(x, BUILD_Y, 94,
                       f"{STONE_BRICK_STAIRS}[facing=south,half=bottom]")
            # 南端
            b.setblock(x, bridge_top_y, 103, STONE_BRICK_SLAB)
            b.setblock(x, BUILD_Y, 104,
                       f"{STONE_BRICK_STAIRS}[facing=north,half=bottom]")

    print("    桥栏杆落地完成")


# ══════════════════════════════════════════════════════════════
#  3. 修复商业街细节
# ══════════════════════════════════════════════════════════════

def fix_market_details(b):
    """给商业街增加生活感:
    - 旗帜(wall_banner)做幌子
    - 营火(campfire)做炊烟
    - 花盆做装饰
    - 摊位补货物暗示(木桶/南瓜/西瓜/干草)
    """
    print("  [修复] 商业街生活细节...")
    random.seed(301)  # 独立种子, 不影响其他随机

    # ── 旗帜幌子: 沿商业街北侧墙面/柱子挂 ──
    # 每隔5~7格挂一面旗帜
    banner_ct = 0
    x = MARKET_X1 + 3
    while x < MARKET_X2 - 3:
        # 北侧旗帜 (挂在柱子上, facing=south 朝向街道)
        b.setblock(x, BUILD_Y + 2, MARKET_Z1,
                   f"{RED_BANNER}[facing=south]")
        banner_ct += 1

        # 南侧偶尔也挂 (白色旗帜换换花样)
        if random.random() < 0.6:
            b.setblock(x + 2, BUILD_Y + 2, MARKET_Z2,
                       f"{WHITE_BANNER}[facing=north]")
            banner_ct += 1

        x += random.randint(5, 7)

    print(f"    旗帜 {banner_ct} 面")

    # ── 营火炊烟: 街角/摊位旁放营火 ──
    # 营火位置: 商业街两端 + 中段, 模拟小吃摊烟火气
    campfire_positions = [
        (MARKET_X1 + 1, MARKET_Z2 + 1),    # 西端街角
        (MARKET_X2 - 1, MARKET_Z2 + 1),    # 东端街角
        ((MARKET_X1 + MARKET_X2) // 2, MARKET_Z2 + 1),  # 中段
    ]

    for cx, cz in campfire_positions:
        b.setblock(cx, BUILD_Y, cz, CAMPFIRE)
        # 营火旁放个炉灶感的方块
        b.setblock(cx + 1, BUILD_Y, cz, SMOKER)

    print(f"    营火 {len(campfire_positions)} 处")

    # ── 花盆装饰: 沿街每隔几格放花盆 ──
    pot_types = [FLOWER_POT, FLOWER_POT_FERN, FLOWER_POT_BAMBOO]
    pot_ct = 0

    for x in range(MARKET_X1, MARKET_X2 + 1, 4):
        pot = random.choice(pot_types)
        # 北侧路边
        b.setblock(x, BUILD_Y, MARKET_Z1, pot)
        pot_ct += 1
        # 南侧偶尔放
        if random.random() < 0.4:
            b.setblock(x + 1, BUILD_Y, MARKET_Z2, random.choice(pot_types))
            pot_ct += 1

    print(f"    花盆 {pot_ct} 个")

    # ── 摊位货物暗示: 在已有摊位柜台上/旁边放货物 ──
    # 沿商业街南侧 (Z=107) 摊位位置, 补货物
    # 由于摊位是随机放的, 这里按固定间距在柜台后面放货
    goods_types = [BARREL, HAY_BLOCK, MELON, PUMPKIN, COMPOSTER, CRAFTING_TABLE]
    goods_ct = 0

    # 南侧摊位货物 (Z=108, 柜台后方)
    x = MARKET_X1 + 2
    while x < MARKET_X2 - 4:
        # 柜台上面放东西
        good = random.choice(goods_types)
        b.setblock(x, BUILD_Y + 1, MARKET_Z2 + 1, good)
        goods_ct += 1

        # 旁边再来一个不同的
        if random.random() < 0.5:
            good2 = random.choice(goods_types)
            b.setblock(x + 1, BUILD_Y, MARKET_Z2 + 1, good2)
            goods_ct += 1

        x += random.randint(6, 9)

    # 北侧摊位货物 (Z=103, 柜台后方)
    x = MARKET_X1 + 5
    while x < MARKET_X2 - 4:
        if random.random() < 0.5:
            good = random.choice(goods_types)
            b.setblock(x, BUILD_Y + 1, MARKET_Z1 - 1, good)
            goods_ct += 1
        x += random.randint(7, 10)

    print(f"    货物 {goods_ct} 件")

    # ── 街道装饰: 沿路面放小物件 ──
    # 水缸 (炼药锅装水)
    b.setblock(MARKET_X1 + 10, BUILD_Y, MARKET_Z1 + 1, CAULDRON)
    b.setblock(MARKET_X2 - 8, BUILD_Y, MARKET_Z2 - 1, CAULDRON)

    # 织布机 (暗示布匹摊)
    b.setblock(MARKET_X1 + 15, BUILD_Y, MARKET_Z2,
               f"{LOOM}[facing=north]")

    print("    街道装饰完成")


# ══════════════════════════════════════════════════════════════
#  4. 汇总
# ══════════════════════════════════════════════════════════════

def fix_south_all(b):
    """修复南面江南水乡所有已知问题"""
    print("=== 南面水乡修复 ===")

    fix_house_doors(b)
    fix_canal_connections(b)
    fix_market_details(b)

    print("=== 南面水乡修复完成 ===")


if __name__ == "__main__":
    from builder import MinecraftBuilder
    with MinecraftBuilder() as b:
        fix_south_all(b)
        print(f"Done! {b.cmd_count} commands")
