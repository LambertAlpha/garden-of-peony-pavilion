"""廊桥 + 画船 — 拙政园"小飞虹"式廊桥 & 烟波画船

廊桥：南北跨池塘，有顶有栏杆，中段微拱。
画船：池塘西侧水面漂浮小舟，红顶、灯笼。
"""

import sys; sys.path.insert(0, '/Users/lambertlin/minecraft-server/scripts')
from builder import MinecraftBuilder
from blocks import PALETTE


# ================================================================
#  廊桥（小飞虹）
# ================================================================

def _build_bridge(b: MinecraftBuilder):
    """
    廊桥：X=35~37（3格宽），Z=22~36（15格长，南北跨池塘）
    中心线 X=36，桥面 y=-60，中段抬高 y=-59
    """
    print("  [廊桥] 开始建造...")

    # ── 材质 ──
    PILLAR    = PALETTE["pillar"]       # stripped_acacia_log  (金合欢去皮原木)
    FLOOR     = "minecraft:oak_planks"  # 橡木木板桥面
    RAIL      = PALETTE["rail"]         # acacia_fence (金合欢栅栏)
    RED_CAR   = PALETTE["red_carpet"]   # 红色地毯
    ROOF_SLAB = PALETTE["roof_slab"]    # deepslate_tile_slab
    BEAM      = PALETTE["beam"]         # dark_oak_planks
    STAIR_N   = "minecraft:stone_brick_stairs[facing=north,half=bottom]"
    STAIR_S   = "minecraft:stone_brick_stairs[facing=south,half=bottom]"

    # 桥 X 范围
    BX1, BX2 = 35, 37   # 3格宽: 35(西栏杆) 36(中走道) 37(东栏杆)
    # 桥 Z 范围
    BZ_S, BZ_N = 36, 22  # 南端 Z=36, 北端 Z=22

    # ── 辅助：判断某 Z 处桥面高度 ──
    def deck_y(z: int) -> int:
        """桥面Y坐标：两端平直 y=-60，中段抬高 y=-59"""
        if z <= 24 or z >= 34:
            return -60  # 两端 3 格平直
        elif z == 25 or z == 33:
            return -60  # 过渡处（楼梯放此处）
        else:
            return -59  # 中段抬高

    # ── 1. 桥面铺设 ──
    print("    桥面...")
    for z in range(BZ_N, BZ_S + 1):  # Z: 22 → 36
        dy = deck_y(z)
        for x in range(BX1, BX2 + 1):
            b.setblock(x, dy, z, FLOOR)

    # ── 2. 过渡楼梯 ──
    # Z=25: 从南来（Z大→Z小方向走），从 -60 上到 -59 → 楼梯 facing=north
    # Z=33: 从北来（Z小→Z大方向走），从 -60 上到 -59 → 楼梯 facing=south
    print("    拱桥过渡楼梯...")
    for x in range(BX1, BX2 + 1):
        # Z=33: 南侧过渡，人从 Z=34(y=-60) 走向 Z=32(y=-59)
        # facing=south → 低端朝南，人从南踏上
        b.setblock(x, -60, 33, STAIR_S)
        # Z=25: 北侧过渡，人从 Z=24(y=-60) 走向 Z=26(y=-59)
        # facing=north → 低端朝北，人从北踏上
        b.setblock(x, -60, 25, STAIR_N)

    # ── 3. 桥柱 ──
    # 每隔 4 格一排柱子，从水底 y=-63 到桥面以下
    print("    桥柱...")
    pillar_zs = [22, 26, 30, 34]  # 4 个柱位
    for z in pillar_zs:
        dy = deck_y(z)
        for x in [BX1, BX2]:  # 两侧各一根柱子
            for y in range(-63, dy):  # 从水底到桥面下方
                b.setblock(x, y, z, PILLAR)

    # ── 4. 栏杆 ──
    print("    栏杆 + 红地毯...")
    for z in range(BZ_N, BZ_S + 1):
        dy = deck_y(z)
        for x in [BX1, BX2]:  # 两侧
            b.setblock(x, dy + 1, z, RAIL)       # 栏杆
            b.setblock(x, dy + 2, z, RED_CAR)    # 红色地毯铺栏杆顶

    # ── 5. 廊顶结构 ──
    # 柱子从桥面起 3 格高 → 顶棚在 deck_y + 4
    # 廊顶宽 5 格（BX1-1 ~ BX2+1），比桥面各多出 1 格出檐
    print("    廊顶...")
    for z in range(BZ_N, BZ_S + 1):
        dy = deck_y(z)
        roof_y = dy + 4  # 顶棚高度

        # 顶柱 + 横梁（只在柱位处）
        if z in pillar_zs:
            for x in [BX1, BX2]:
                b.setblock(x, dy + 3, z, PILLAR)  # 两侧柱延伸
            # 中间横梁连接两柱
            b.setblock(BX1 + 1, dy + 3, z, BEAM)

        # 顶棚：深板岩瓦片半砖，宽 5 格（含出檐）
        for x in range(BX1 - 1, BX2 + 2):  # 34 ~ 38，共 5 格
            b.setblock(x, roof_y, z, f"{ROOF_SLAB}[type=top]")

    # ── 6. 南北端地面衔接 ──
    # 确保桥两端与地面连接自然（补地面方块）
    print("    端部衔接...")
    for x in range(BX1, BX2 + 1):
        # 南端 Z=36：桥面 y=-60，与南岸地面齐平
        b.setblock(x, -60, 37, FLOOR)  # 多铺一格衔接
        # 北端 Z=22：桥面 y=-60，与北岸地面齐平
        b.setblock(x, -60, 21, FLOOR)  # 多铺一格衔接

    print("  [廊桥] 完成!")


# ================================================================
#  画船（烟波画船）
# ================================================================

def _build_boat(b: MinecraftBuilder):
    """
    画船：船头朝北(Z小端)，船尾朝南(Z大端)
    位置中心 X=20, Z=28，展开为 X:19~21, Z:24~31 (3×8)
    底部 y=-61（水面层），船舷 y=-60
    """
    print("  [画船] 开始建造...")

    OAK     = "minecraft:oak_planks"
    RAIL    = "minecraft:oak_fence"      # 橡木栅栏（船用）
    RED_W   = PALETTE["red_wool"]        # 红色羊毛顶棚
    LANTERN = PALETTE["lantern"]         # 灯笼
    STAIR_N = "minecraft:oak_stairs[facing=north,half=bottom]"
    STAIR_S = "minecraft:oak_stairs[facing=south,half=bottom]"

    # 船体范围
    SX1, SX2 = 19, 21   # 3 格宽
    SZ_BOW   = 24        # 船头（北）
    SZ_STERN = 31        # 船尾（南）
    HULL_Y   = -61       # 船底（水面层）
    DECK_Y   = -60       # 甲板/船舷层

    # ── 1. 船底 ──
    # 3×8 橡木木板 (y=-61)
    print("    船底...")
    b.fill(SX1, HULL_Y, SZ_BOW, SX2, HULL_Y, SZ_STERN, OAK)

    # ── 2. 船舷 (y=-60) ──
    # 两侧各 1 列橡木木板，中间空（走道）
    print("    船舷...")
    for z in range(SZ_BOW, SZ_STERN + 1):
        b.setblock(SX1, DECK_Y, z, OAK)  # 西舷
        b.setblock(SX2, DECK_Y, z, OAK)  # 东舷

    # 船尾横板（封死）
    b.setblock(SX1 + 1, DECK_Y, SZ_STERN, OAK)  # 中间也封

    # ── 3. 船头尖角 ──
    # Z=24(船头)：收窄为中间 1 格，两侧用楼梯模拟斜面
    print("    船头...")
    b.setblock(SX1 + 1, HULL_Y, SZ_BOW, OAK)            # 中间保留
    b.setblock(SX1, HULL_Y, SZ_BOW, STAIR_N)             # 西侧楼梯尖头
    b.setblock(SX2, HULL_Y, SZ_BOW, STAIR_N)             # 东侧楼梯尖头

    # 船头船舷也收窄：只有中间 1 格
    b.setblock(SX1, DECK_Y, SZ_BOW, "minecraft:air")     # 移除西舷头部
    b.setblock(SX2, DECK_Y, SZ_BOW, "minecraft:air")     # 移除东舷头部
    b.setblock(SX1 + 1, DECK_Y, SZ_BOW, OAK)             # 中间船舷

    # Z=25 也稍微收窄过渡
    b.setblock(SX1, DECK_Y, SZ_BOW + 1, STAIR_N)         # 西侧楼梯过渡
    b.setblock(SX2, DECK_Y, SZ_BOW + 1, STAIR_N)         # 东侧楼梯过渡

    # ── 4. 顶棚（中段 4 格: Z=27~30）──
    # 4 根橡木栅栏柱（高2格），红色羊毛顶
    print("    顶棚...")
    CANOPY_Z1, CANOPY_Z2 = 27, 30  # 顶棚覆盖 Z 范围
    CANOPY_Y_BASE = DECK_Y + 1     # 柱子底部 y=-59
    CANOPY_Y_TOP  = DECK_Y + 2     # 柱子顶部 y=-58
    ROOF_Y        = DECK_Y + 3     # 顶棚 y=-57

    # 4 根角柱
    for x in [SX1, SX2]:
        for z in [CANOPY_Z1, CANOPY_Z2]:
            b.setblock(x, CANOPY_Y_BASE, z, RAIL)  # 柱 下
            b.setblock(x, CANOPY_Y_TOP,  z, RAIL)  # 柱 上

    # 红色羊毛顶棚 (3×4)
    b.fill(SX1, ROOF_Y, CANOPY_Z1, SX2, ROOF_Y, CANOPY_Z2, RED_W)

    # ── 5. 装饰 ──
    # 船头灯笼
    print("    装饰...")
    # 灯笼挂在船头中间 (X=20, Z=24) 上方
    # 先放一根栅栏柱，再挂灯笼
    b.setblock(SX1 + 1, DECK_Y + 1, SZ_BOW, RAIL)    # 短柱
    b.setblock(SX1 + 1, DECK_Y + 2, SZ_BOW, LANTERN)  # 灯笼

    print("  [画船] 完成!")


# ================================================================
#  入口
# ================================================================

def build_bridge_and_boat(b: MinecraftBuilder):
    print("=== 廊桥 + 画船 ===")
    _build_bridge(b)
    _build_boat(b)
    # 注册边界框（用于 undo）
    b.register_bbox("bridge", 34, -63, 21, 38, -55, 37)
    b.register_bbox("boat", 19, -61, 24, 22, -57, 31)


if __name__ == "__main__":
    with MinecraftBuilder() as b:
        build_bridge_and_boat(b)
        print(f"Done! {b.cmd_count} commands")
