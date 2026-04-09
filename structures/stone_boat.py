"""烟波舫 — 石舫（仿拙政园"香洲"）

"雨丝风片，烟波画船" — 石舫是园林中最浪漫的建筑类型：
以石为船，不能移动，永泊水面，寓"舟行不动"之意。

结构三段式（北→南）：
  前舱（方亭）→ 中舱（平榭）→ 后舱（二层小阁）
船头朝北，位于池塘东南水面。
"""

import sys; sys.path.insert(0, '/Users/lambertlin/minecraft-server/scripts')
from builder import MinecraftBuilder
from blocks import PALETTE


def build_stone_boat(b: MinecraftBuilder):
    """建造烟波舫（石舫）

    位置: 船体中心线 X=65, Z=39~54 (长16), 宽 X=63~67 (5格)
    船头(北) Z=39, 船尾(南) Z=54  # P1修复: 北移3格避免船尾搁浅
    甲板 Y=-60, 水面 Y=-61, 船底 Y=-62
    """
    print("=== 烟波舫（石舫）===")

    # ── 材质 ──
    STONE_BR   = "minecraft:stone_bricks"
    STONE_STAIR = "minecraft:stone_brick_stairs"
    STONE_SLAB = "minecraft:stone_brick_slab"
    SMOOTH     = PALETTE["floor"]           # smooth_stone
    PILLAR     = PALETTE["pillar"]          # stripped_crimson_stem
    RAIL       = PALETTE["rail"]            # crimson_fence
    WALL       = PALETTE["wall"]            # white_concrete
    TRAPDOOR   = PALETTE["trapdoor"]        # jungle_trapdoor
    BEAM       = PALETTE["beam"]            # dark_oak_planks
    LANTERN    = PALETTE["lantern"]         # lantern
    AIR        = "minecraft:air"

    # ── 坐标常量 ──
    CX = 65                   # 船中心线 X
    X1, X2 = 63, 67           # 船宽 5 格: 63,64,65,66,67
    Z_BOW = 39                # 船头(北端) P1修复: 北移3格
    Z_STERN = 54              # 船尾(南端)
    HULL_Y = -62              # 船底 (水下1格)
    WATER_Y = -61             # 水面层(船舷)
    DECK_Y = -60              # 甲板层

    # 三段分区
    # 前舱(方亭): Z=42~45 (4格)
    FORE_Z1, FORE_Z2 = 39, 42  # 北移3格配合Z_BOW
    # 中舱(平榭): Z=46~51 (6格)
    MID_Z1, MID_Z2 = 46, 51
    # 后舱(小阁): Z=52~57 (6格)
    AFT_Z1, AFT_Z2 = 52, 57

    # ================================================================
    # 1. 船体 — 石砖基座
    # ================================================================
    print("  [1/8] 船体...")

    # 船底: 5×16 石砖 (Y=-62)
    b.fill(X1, HULL_Y, Z_BOW, X2, HULL_Y, Z_STERN, STONE_BR)

    # 船舷: 两侧各1列石砖围挡 (Y=-61, 水面层)
    b.fill(X1, WATER_Y, Z_BOW, X1, WATER_Y, Z_STERN, STONE_BR)  # 西舷
    b.fill(X2, WATER_Y, Z_BOW, X2, WATER_Y, Z_STERN, STONE_BR)  # 东舷
    # 船尾横封
    b.fill(X1, WATER_Y, Z_STERN, X2, WATER_Y, Z_STERN, STONE_BR)

    # ================================================================
    # 2. 船头收窄 — 楼梯尖角
    # ================================================================
    print("  [2/8] 船头...")

    # Z=42(船头最北): 两侧用楼梯收窄，中间3格保留
    # 底层(HULL_Y): 西端和东端用楼梯
    b.setblock(X1, HULL_Y, Z_BOW,
               f"{STONE_STAIR}[facing=north,half=bottom]")
    b.setblock(X2, HULL_Y, Z_BOW,
               f"{STONE_STAIR}[facing=north,half=bottom]")
    # 船舷层(WATER_Y): 船头只保留中间1格
    b.setblock(X1, WATER_Y, Z_BOW, AIR)  # 移除西舷头部
    b.setblock(X2, WATER_Y, Z_BOW, AIR)  # 移除东舷头部
    b.setblock(CX, WATER_Y, Z_BOW, STONE_BR)  # 中间船舷保留

    # Z=42 船头前多加一格尖角 (Z=41)
    b.setblock(CX, HULL_Y, Z_BOW - 1,
               f"{STONE_STAIR}[facing=north,half=bottom]")
    b.setblock(CX, WATER_Y, Z_BOW - 1,
               f"{STONE_STAIR}[facing=north,half=top]")

    # Z=42 甲板层也收窄: 两侧楼梯过渡
    b.setblock(X1, WATER_Y, Z_BOW + 1,
               f"{STONE_STAIR}[facing=north,half=bottom]")
    b.setblock(X2, WATER_Y, Z_BOW + 1,
               f"{STONE_STAIR}[facing=north,half=bottom]")

    # ================================================================
    # 3. 甲板铺面
    # ================================================================
    print("  [3/8] 甲板...")

    # 全船甲板: smooth_stone (Y=-60)
    b.fill(X1, DECK_Y, Z_BOW, X2, DECK_Y, Z_STERN, SMOOTH)

    # 船头(Z=42): 收窄，只保留中间3格甲板
    b.setblock(X1, DECK_Y, Z_BOW, AIR)
    b.setblock(X2, DECK_Y, Z_BOW, AIR)

    # 船头尖角甲板(Z=41)
    b.setblock(CX, DECK_Y, Z_BOW - 1,
               f"{STONE_SLAB}[type=top]")

    # ================================================================
    # 4. 前舱 — 方亭 (Z=42~45)
    # ================================================================
    print("  [4/8] 前舱（方亭）...")

    # 4根柱子: 船宽内侧角 (X1+1, X2-1) × (FORE_Z1+1, FORE_Z2)
    fore_pillars = [
        (X1 + 1, FORE_Z1 + 1),  # 西北
        (X2 - 1, FORE_Z1 + 1),  # 东北
        (X1 + 1, FORE_Z2),      # 西南
        (X2 - 1, FORE_Z2),      # 东南
    ]
    for px, pz in fore_pillars:
        for y in range(DECK_Y + 1, DECK_Y + 4):  # 3格高柱
            b.setblock(px, y, pz, PILLAR)

    # 柱顶横梁 (Y = DECK_Y+4)
    beam_y_fore = DECK_Y + 4
    # 北梁
    b.fill(X1 + 1, beam_y_fore, FORE_Z1 + 1,
           X2 - 1, beam_y_fore, FORE_Z1 + 1, BEAM)
    # 南梁
    b.fill(X1 + 1, beam_y_fore, FORE_Z2,
           X2 - 1, beam_y_fore, FORE_Z2, BEAM)
    # 西梁
    b.fill(X1 + 1, beam_y_fore, FORE_Z1 + 1,
           X1 + 1, beam_y_fore, FORE_Z2, BEAM)
    # 东梁
    b.fill(X2 - 1, beam_y_fore, FORE_Z1 + 1,
           X2 - 1, beam_y_fore, FORE_Z2, BEAM)

    # 攒尖小顶 (两层楼梯 + slab)
    # 第1层 (beam_y_fore+1 = DECK_Y+5): 5×4 楼梯圈
    ry1 = beam_y_fore + 1
    # 北面楼梯
    for x in range(X1, X2 + 1):
        b.setblock(x, ry1, FORE_Z1,
                   f"{STONE_STAIR}[facing=south,half=bottom]")
    # 南面楼梯
    for x in range(X1, X2 + 1):
        b.setblock(x, ry1, FORE_Z2 + 1,
                   f"{STONE_STAIR}[facing=north,half=bottom]")
    # 西面楼梯
    for z in range(FORE_Z1, FORE_Z2 + 2):
        b.setblock(X1 - 1, ry1, z,
                   f"{STONE_STAIR}[facing=east,half=bottom]")
    # 东面楼梯
    for z in range(FORE_Z1, FORE_Z2 + 2):
        b.setblock(X2 + 1, ry1, z,
                   f"{STONE_STAIR}[facing=west,half=bottom]")
    # 中间填充
    b.fill(X1, ry1, FORE_Z1 + 1, X2, ry1, FORE_Z2, STONE_BR)

    # 第2层 (ry1+1 = DECK_Y+6): 3×2 楼梯圈
    ry2 = ry1 + 1
    # 北
    for x in range(X1 + 1, X2):
        b.setblock(x, ry2, FORE_Z1 + 1,
                   f"{STONE_STAIR}[facing=south,half=bottom]")
    # 南
    for x in range(X1 + 1, X2):
        b.setblock(x, ry2, FORE_Z2,
                   f"{STONE_STAIR}[facing=north,half=bottom]")
    # 西
    b.setblock(X1, ry2, FORE_Z1 + 2,
               f"{STONE_STAIR}[facing=east,half=bottom]")
    # 东
    b.setblock(X2, ry2, FORE_Z1 + 2,
               f"{STONE_STAIR}[facing=west,half=bottom]")
    # 中间
    b.fill(X1 + 1, ry2, FORE_Z1 + 2, X2 - 1, ry2, FORE_Z2 - 1, STONE_BR)

    # 顶部 slab
    b.setblock(CX, ry2 + 1, FORE_Z1 + 2,
               f"{STONE_SLAB}[type=bottom]")

    # 船头灯笼（挂在前舱北端中间）
    b.setblock(CX, DECK_Y + 1, Z_BOW - 1, RAIL)
    b.setblock(CX, DECK_Y + 2, Z_BOW - 1, LANTERN)

    # ================================================================
    # 5. 中舱 — 低平榭 (Z=46~51)
    # ================================================================
    print("  [5/8] 中舱（平榭）...")

    # 两侧栏杆 (Y = DECK_Y+1)
    for z in range(MID_Z1, MID_Z2 + 1):
        b.setblock(X1, DECK_Y + 1, z, RAIL)   # 西栏杆
        b.setblock(X2, DECK_Y + 1, z, RAIL)   # 东栏杆

    # 中舱南北端也加栏杆横档
    for x in range(X1, X2 + 1):
        b.setblock(x, DECK_Y + 1, MID_Z1, RAIL)  # 北端栏杆
    # 南端不加(与后舱相连)

    # 中舱两端加灯笼柱
    for z_lamp in [MID_Z1, MID_Z2]:
        for x_lamp in [X1, X2]:
            b.setblock(x_lamp, DECK_Y + 2, z_lamp, LANTERN)

    # ================================================================
    # 6. 后舱 — 二层小阁 (Z=52~57)
    # ================================================================
    print("  [6/8] 后舱（二层小阁）...")

    # -- 一层: 墙体 (DECK_Y+1 ~ DECK_Y+3, 3格高) --
    # 西墙
    b.fill(X1, DECK_Y + 1, AFT_Z1, X1, DECK_Y + 3, AFT_Z2, WALL)
    # 东墙
    b.fill(X2, DECK_Y + 1, AFT_Z1, X2, DECK_Y + 3, AFT_Z2, WALL)
    # 南墙(船尾)
    b.fill(X1, DECK_Y + 1, AFT_Z2, X2, DECK_Y + 3, AFT_Z2, WALL)
    # 北墙(与中舱相接，留门洞)
    b.fill(X1, DECK_Y + 1, AFT_Z1, X2, DECK_Y + 3, AFT_Z1, WALL)
    # 门洞: 北墙中间2格高 (CX, DECK_Y+1~+2)
    b.setblock(CX, DECK_Y + 1, AFT_Z1, AIR)
    b.setblock(CX, DECK_Y + 2, AFT_Z1, AIR)

    # 花窗: 两侧墙各开2个窗 (用trapdoor模拟)
    # 西墙花窗
    for z_win in [AFT_Z1 + 2, AFT_Z1 + 4]:
        b.setblock(X1, DECK_Y + 2, z_win, AIR)  # 先挖洞
        b.setblock(X1 - 1, DECK_Y + 2, z_win,
                   f"minecraft:jungle_trapdoor[facing=east,half=bottom,open=true]")
    # 东墙花窗
    for z_win in [AFT_Z1 + 2, AFT_Z1 + 4]:
        b.setblock(X2, DECK_Y + 2, z_win, AIR)
        b.setblock(X2 + 1, DECK_Y + 2, z_win,
                   f"minecraft:jungle_trapdoor[facing=west,half=bottom,open=true]")
    # 南墙(船尾)花窗: 中间1个
    b.setblock(CX, DECK_Y + 2, AFT_Z2, AIR)
    b.setblock(CX, DECK_Y + 2, AFT_Z2 + 1,
               f"minecraft:jungle_trapdoor[facing=north,half=bottom,open=true]")

    # 一层内柱 (4根角柱撑住二层)
    aft_pillars = [
        (X1 + 1, AFT_Z1 + 1),
        (X2 - 1, AFT_Z1 + 1),
        (X1 + 1, AFT_Z2 - 1),
        (X2 - 1, AFT_Z2 - 1),
    ]
    for px, pz in aft_pillars:
        for y in range(DECK_Y + 1, DECK_Y + 4):
            b.setblock(px, y, pz, PILLAR)

    # -- 一层天花板 / 二层地板 (DECK_Y+4) --
    floor2_y = DECK_Y + 4
    b.fill(X1, floor2_y, AFT_Z1, X2, floor2_y, AFT_Z2, BEAM)

    # -- 二层: 栏杆围合 (floor2_y+1 = DECK_Y+5) --
    rail2_y = floor2_y + 1
    # 四面栏杆
    for x in range(X1, X2 + 1):
        b.setblock(x, rail2_y, AFT_Z1, RAIL)  # 北
        b.setblock(x, rail2_y, AFT_Z2, RAIL)  # 南
    for z in range(AFT_Z1, AFT_Z2 + 1):
        b.setblock(X1, rail2_y, z, RAIL)       # 西
        b.setblock(X2, rail2_y, z, RAIL)       # 东

    # 二层四角立柱 (2格高)
    for px, pz in [(X1, AFT_Z1), (X2, AFT_Z1), (X1, AFT_Z2), (X2, AFT_Z2)]:
        b.setblock(px, rail2_y, pz, PILLAR)
        b.setblock(px, rail2_y + 1, pz, PILLAR)

    # -- 后舱歇山顶 --
    # 高度: rail2_y+2 = DECK_Y+7 起始
    roof_base_y = rail2_y + 2

    # 第1层: 7×8 楼梯圈 (X: X1-1 ~ X2+1 = 7格, Z: AFT_Z1-1 ~ AFT_Z2+1 = 8格)
    # 含出檐: 比墙体各多1格
    rx1, rx2 = X1 - 1, X2 + 1
    rz1, rz2 = AFT_Z1 - 1, AFT_Z2 + 1

    # 北面楼梯
    for x in range(rx1, rx2 + 1):
        b.setblock(x, roof_base_y, rz1,
                   f"{STONE_STAIR}[facing=south,half=bottom]")
    # 南面楼梯
    for x in range(rx1, rx2 + 1):
        b.setblock(x, roof_base_y, rz2,
                   f"{STONE_STAIR}[facing=north,half=bottom]")
    # 西面楼梯
    for z in range(rz1 + 1, rz2):
        b.setblock(rx1, roof_base_y, z,
                   f"{STONE_STAIR}[facing=east,half=bottom]")
    # 东面楼梯
    for z in range(rz1 + 1, rz2):
        b.setblock(rx2, roof_base_y, z,
                   f"{STONE_STAIR}[facing=west,half=bottom]")
    # 中间填充
    b.fill(X1, roof_base_y, AFT_Z1, X2, roof_base_y, AFT_Z2, STONE_BR)

    # 第2层: 缩小一圈 (5×6)
    ry = roof_base_y + 1
    # 北
    for x in range(X1, X2 + 1):
        b.setblock(x, ry, AFT_Z1,
                   f"{STONE_STAIR}[facing=south,half=bottom]")
    # 南
    for x in range(X1, X2 + 1):
        b.setblock(x, ry, AFT_Z2,
                   f"{STONE_STAIR}[facing=north,half=bottom]")
    # 西
    for z in range(AFT_Z1 + 1, AFT_Z2):
        b.setblock(X1, ry, z,
                   f"{STONE_STAIR}[facing=east,half=bottom]")
    # 东
    for z in range(AFT_Z1 + 1, AFT_Z2):
        b.setblock(X2, ry, z,
                   f"{STONE_STAIR}[facing=west,half=bottom]")
    # 中间
    b.fill(X1 + 1, ry, AFT_Z1 + 1, X2 - 1, ry, AFT_Z2 - 1, STONE_BR)

    # 第3层: 歇山脊 — 东西方向 slab 脊线
    ry3 = ry + 1
    for z in range(AFT_Z1 + 1, AFT_Z2):
        b.setblock(CX, ry3, z, f"{STONE_SLAB}[type=bottom]")
    # 脊线两端用楼梯收尾（歇山的山面）
    b.setblock(CX, ry3, AFT_Z1,
               f"{STONE_STAIR}[facing=south,half=bottom]")
    b.setblock(CX, ry3, AFT_Z2,
               f"{STONE_STAIR}[facing=north,half=bottom]")

    # 后舱灯笼（挂在二层内侧四角，避开屋顶覆盖）
    for px, pz in aft_pillars:
        b.setblock(px, floor2_y + 1, pz, LANTERN)

    # ================================================================
    # 7. 登船栈桥 — 从岸边到船尾
    # ================================================================
    print("  [7/8] 登船栈桥...")

    # 栈桥: 从岸(约X=70,Z=55) 到船尾东侧(X=68,Z=55)
    # 3格宽(Z=54~56), X从68到72
    BRIDGE_Z1, BRIDGE_Z2 = 54, 56
    BRIDGE_X1 = 68   # 紧接船尾(X2=67+1)
    BRIDGE_X2 = 72   # 到岸边

    STEM = "minecraft:stripped_crimson_stem"

    # 栈桥桥面: stone_brick_slab (Y=-60)
    for x in range(BRIDGE_X1, BRIDGE_X2 + 1):
        for z in range(BRIDGE_Z1, BRIDGE_Z2 + 1):
            b.setblock(x, DECK_Y, z, f"{STONE_SLAB}[type=top]")

    # 桥墩: 每隔2格一对 stripped_crimson_stem 插入水中
    for x in [BRIDGE_X1, BRIDGE_X1 + 2, BRIDGE_X2]:
        for z in [BRIDGE_Z1, BRIDGE_Z2]:
            for y in range(-63, DECK_Y):  # 从水底到桥面下方
                b.setblock(x, y, z, STEM)

    # 栈桥栏杆 (两侧)
    for x in range(BRIDGE_X1, BRIDGE_X2 + 1):
        b.setblock(x, DECK_Y + 1, BRIDGE_Z1, RAIL)
        b.setblock(x, DECK_Y + 1, BRIDGE_Z2, RAIL)

    # ================================================================
    # 8. 注册边界框 + 收尾
    # ================================================================
    print("  [8/8] 收尾...")

    # 整体边界: 含栈桥和屋顶
    b.register_bbox("stone_boat",
                    X1 - 1, HULL_Y, Z_BOW - 1,
                    BRIDGE_X2, roof_base_y + 3, AFT_Z2 + 1)

    print("  烟波舫建造完成！")


# ── 入口 ──

if __name__ == "__main__":
    with MinecraftBuilder() as b:
        build_stone_boat(b)
        print(f"Done! Total commands: {b.cmd_count}")
