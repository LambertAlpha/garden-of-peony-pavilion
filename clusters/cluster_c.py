"""C群：花听长廊 — 听雨轩 + 连接花架 + 荼蘼花架

群组建造试点：一个函数建造整个群组，零间隙。
  - 台基一条 fill 铺满
  - 柱子复用（听雨轩东墙角柱 = 连接段起始柱）
  - 地面条纹从 x=30 到 x=56 连续不断

坐标来源 (config_v4):
  听雨轩:   cx=34, cz=54, 9x7  → X[30,38] Z[51,57]
  荼蘼花架: cx=50, cz=53, 12x4 → X[44,56] Z[51,55]
  连接段:   X[38,44] Z[51,55]  （听雨轩东墙→花架西端，3格宽走道 Z=52~54）
"""

import sys
sys.path.insert(0, '/Users/lambertlin/minecraft-server/scripts')

from builder import MinecraftBuilder
from blocks import PALETTE, BUILD_Y


def build_cluster_c(b: MinecraftBuilder):
    """C群：花听长廊 — 听雨轩+连接花架+荼蘼花架
    一条 fill 铺地，柱子复用，连续屋顶"""

    print("=" * 60)
    print("=== C群：花听长廊 ===")
    print("=" * 60)

    # ── 材质 ──
    BASE       = PALETTE["base"]           # stone_bricks
    BASE_STEP  = PALETTE["base_step"]      # stone_brick_stairs
    PILLAR     = PALETTE["pillar"]         # stripped_crimson_stem
    BEAM       = PALETTE["beam"]           # dark_oak_planks
    BEAM_LOG   = PALETTE["beam_log"]       # dark_oak_log
    WALL       = PALETTE["wall"]           # white_concrete
    WINDOW     = PALETTE["window"]         # iron_bars
    ROOF       = PALETTE["roof"]           # stone_brick_stairs
    ROOF_SLAB  = PALETTE["roof_slab"]      # stone_brick_slab
    ROOF_BLOCK = PALETTE["roof_block"]     # stone_bricks
    FLOOR      = PALETTE["floor"]          # smooth_stone
    FLOOR_ALT  = PALETTE["base_col"]       # polished_andesite
    RAIL       = PALETTE["rail"]           # crimson_fence
    VINE       = PALETTE["vine"]           # vine
    LANTERN    = PALETTE["lantern"]        # lantern
    SPRUCE_F   = "minecraft:spruce_fence"  # 云杉栅栏（花架立柱）
    TRAPDOOR   = PALETTE["trapdoor"]       # jungle_trapdoor

    # ── Y 坐标 ──
    ground_y = BUILD_Y                     # -60
    base_y   = ground_y                    # 台基层
    floor_y  = ground_y + 1                # 地面层
    pillar_b = ground_y + 1                # 柱底
    pillar_t = ground_y + 5                # 柱顶（5格高: +1,+2,+3,+4,+5）
    beam_y   = ground_y + 6                # 梁/额枋层
    roof_y   = ground_y + 7                # 屋顶起始层

    # ── 整体范围 ──
    # 听雨轩: X[30,38] Z[51,57]
    # 连接段: X[38,44] Z[51,55]（柱在 Z=51,55，走道 Z=52~54 三格宽）
    # 荼蘼花架: X[44,56] Z[51,55]
    X_MIN, X_MAX = 30, 56
    Z_MIN, Z_MAX = 51, 57

    cmd_start = b.cmd_count

    # ================================================================
    # 1. 整体台基 — 一条 fill 铺满
    # ================================================================
    print("  [1/6] 整体台基...")

    b.fill(X_MIN, base_y, Z_MIN,
           X_MAX, base_y, Z_MAX, BASE)

    # ================================================================
    # 2. 地面铺装 — smooth_stone + polished_andesite 条纹，连续不断
    # ================================================================
    print("  [2/6] 地面铺装...")

    # 东西向条纹：奇数 X 用 FLOOR_ALT，偶数 X 用 FLOOR
    for x in range(X_MIN, X_MAX + 1):
        block = FLOOR_ALT if (x % 2 == 1) else FLOOR
        b.fill(x, floor_y, Z_MIN, x, floor_y, Z_MAX, block)

    # ================================================================
    # 3. 听雨轩 (X[30,38] Z[51,57])
    # ================================================================
    print("  [3/6] 听雨轩...")

    TY_X1, TY_X2 = 30, 38   # 听雨轩 X 范围
    TY_Z1, TY_Z2 = 51, 57   # 听雨轩 Z 范围

    # ── 3a. 四根绯红柱（角柱），高5格 ──
    ty_pillars = [
        (TY_X1, TY_Z1),  # 西北
        (TY_X2, TY_Z1),  # 东北
        (TY_X1, TY_Z2),  # 西南
        (TY_X2, TY_Z2),  # 东南
    ]
    for px, pz in ty_pillars:
        b.fill(px, pillar_b, pz, px, pillar_t, pz, PILLAR)

    # ── 3b. 额枋/梁 — 柱顶连接 ──
    # 北梁 Z=51
    b.fill(TY_X1, beam_y, TY_Z1, TY_X2, beam_y, TY_Z1, BEAM)
    # 南梁 Z=57
    b.fill(TY_X1, beam_y, TY_Z2, TY_X2, beam_y, TY_Z2, BEAM)
    # 西梁 X=30
    b.fill(TY_X1, beam_y, TY_Z1, TY_X1, beam_y, TY_Z2, BEAM)
    # 东梁 X=38
    b.fill(TY_X2, beam_y, TY_Z1, TY_X2, beam_y, TY_Z2, BEAM)

    # ── 3c. 北面(Z=51) 开敞面湖 — 只有柱+梁+栏杆 ──
    for x in range(TY_X1 + 1, TY_X2):
        b.setblock(x, pillar_b, TY_Z1, RAIL)

    # ── 3d. 南面(Z=57) 白墙+花窗 ──
    # 墙体填充（柱间，Y: pillar_b 到 pillar_t）
    b.fill(TY_X1 + 1, pillar_b, TY_Z2,
           TY_X2 - 1, pillar_t, TY_Z2, WALL)
    # 花窗：南墙中间3格，Y: pillar_b+1 到 pillar_b+3 (3格高)
    mid_x = (TY_X1 + TY_X2) // 2  # x=34
    for x in range(mid_x - 1, mid_x + 2):  # x=33,34,35
        for y in range(pillar_b + 1, pillar_b + 4):
            b.setblock(x, y, TY_Z2, WINDOW)

    # ── 3e. 西墙(X=30) 实墙 ──
    b.fill(TY_X1, pillar_b, TY_Z1 + 1,
           TY_X1, pillar_t, TY_Z2 - 1, WALL)

    # ── 3f. 东墙(X=38) — Z=52~54 段开门洞对准3格宽走道 ──
    # 东墙封 Z=55~56（Z=51 和 Z=57 是柱位，不需要墙）
    b.fill(TY_X2, pillar_b, 55,
           TY_X2, pillar_t, TY_Z2 - 1, WALL)  # Z=55~56
    # 【修复】东墙门洞：Z=52~54, 3格宽×3格高
    # 门洞上方封墙（floor_y+4 到 pillar_t），下方3格(floor_y+1~+3)留空通行
    # 之前从 pillar_b(=floor_y) 开始清空，把地面也挖了，玩家会"陷进去"
    b.fill(TY_X2, floor_y + 4, 52,
           TY_X2, pillar_t, 54, WALL)  # 门洞上方封墙
    # 门洞通行空间：floor_y+1 ~ floor_y+3 确保为空气
    b.fill(TY_X2, floor_y + 1, 52,
           TY_X2, floor_y + 3, 54, "minecraft:air")  # 门洞3格宽×3格高
    # 确保门洞处地面连续（补回 floor_y 层地面方块，防止"陷进去"）
    door_floor_block = FLOOR_ALT if (TY_X2 % 2 == 1) else FLOOR
    b.fill(TY_X2, floor_y, 52,
           TY_X2, floor_y, 54, door_floor_block)  # 门洞地面平整

    # ── 3g. 悬山顶 ──
    # 悬山顶沿 X 轴（东西）为山墙面，Z 轴为正脊走向
    # 脊线在 Z 中间 = (51+57)/2 = 54

    # 第一层：屋檐出挑（超出墙面1格）
    # 北檐 Z=50（比北墙 Z=51 再出挑1格）
    for x in range(TY_X1 - 1, TY_X2 + 2):
        b.setblock(x, roof_y, TY_Z1 - 1,
                   f"{ROOF}[facing=south,half=bottom]")
    # 南檐 Z=58
    for x in range(TY_X1 - 1, TY_X2 + 2):
        b.setblock(x, roof_y, TY_Z2 + 1,
                   f"{ROOF}[facing=north,half=bottom]")

    # 第二层
    for x in range(TY_X1 - 1, TY_X2 + 2):
        b.setblock(x, roof_y + 1, TY_Z1,
                   f"{ROOF}[facing=south,half=bottom]")
        b.setblock(x, roof_y + 1, TY_Z2,
                   f"{ROOF}[facing=north,half=bottom]")

    # 第三层
    for x in range(TY_X1 - 1, TY_X2 + 2):
        b.setblock(x, roof_y + 2, TY_Z1 + 1,
                   f"{ROOF}[facing=south,half=bottom]")
        b.setblock(x, roof_y + 2, TY_Z2 - 1,
                   f"{ROOF}[facing=north,half=bottom]")

    # 第四层
    for x in range(TY_X1 - 1, TY_X2 + 2):
        b.setblock(x, roof_y + 3, TY_Z1 + 2,
                   f"{ROOF}[facing=south,half=bottom]")
        b.setblock(x, roof_y + 3, TY_Z2 - 2,
                   f"{ROOF}[facing=north,half=bottom]")

    # 正脊 Z=54
    b.fill(TY_X1 - 1, roof_y + 4, 54,
           TY_X2 + 1, roof_y + 4, 54, ROOF_BLOCK)

    # 填充屋顶内部空腔（防止漏光）
    for layer, z_n, z_s in [
        (roof_y,     TY_Z1,     TY_Z2),
        (roof_y + 1, TY_Z1 + 1, TY_Z2 - 1),
        (roof_y + 2, TY_Z1 + 2, TY_Z2 - 2),
        (roof_y + 3, TY_Z1 + 3, TY_Z2 - 3),
    ]:
        if z_n < z_s:
            b.fill(TY_X1, layer, z_n, TY_X2, layer, z_s, ROOF_BLOCK)

    # ================================================================
    # 4. 连接段 (X[38,44] Z[51,55]) — 走道3格宽 Z=52~54
    # ================================================================
    print("  [4/6] 连接花架段...")

    CONN_X1, CONN_X2 = 38, 44
    # 【修改1】柱子从 Z=52,54 移到 Z=51,55，走道加宽为 Z=52~54 三格宽
    CONN_Z1, CONN_Z2 = 51, 55

    # ── 4a. 柱子：x=40, 42, 44（x=38 复用听雨轩东墙角柱）──
    conn_pillar_xs = [40, 42, 44]
    for px in conn_pillar_xs:
        # 南北各一根柱（Z=51 和 Z=55），走道 Z=52~54 保持畅通
        b.fill(px, pillar_b, CONN_Z1, px, pillar_t, CONN_Z1, PILLAR)
        b.fill(px, pillar_b, CONN_Z2, px, pillar_t, CONN_Z2, PILLAR)

    # ── 4b. 横梁连接 ──
    # 北横梁 Z=51
    b.fill(CONN_X1, beam_y, CONN_Z1, CONN_X2, beam_y, CONN_Z1, BEAM)
    # 南横梁 Z=55
    b.fill(CONN_X1, beam_y, CONN_Z2, CONN_X2, beam_y, CONN_Z2, BEAM)

    # ── 4c. 顶部半砖花架顶（覆盖 Z=51~55 整个连接段宽度）──
    b.fill(CONN_X1, beam_y + 1, CONN_Z1,
           CONN_X2, beam_y + 1, CONN_Z2, ROOF_SLAB)

    # ── 4d. vine 垂挂（南北两侧外挂）──
    for x in range(CONN_X1 + 1, CONN_X2):
        # 北侧 vine（挂在 Z=50 面上，朝南的面）
        b.setblock(x, beam_y, CONN_Z1 - 1,
                   f"{VINE}[south=true]")
        b.setblock(x, beam_y - 1, CONN_Z1 - 1,
                   f"{VINE}[south=true]")
        # 南侧 vine（挂在 Z=56 面上）
        b.setblock(x, beam_y, CONN_Z2 + 1,
                   f"{VINE}[north=true]")
        b.setblock(x, beam_y - 1, CONN_Z2 + 1,
                   f"{VINE}[north=true]")

    # ================================================================
    # 5. 荼蘼花架 (X[44,56] Z[51,55])
    # ================================================================
    print("  [5/6] 荼蘼花架...")

    TM_X1, TM_X2 = 44, 56
    TM_Z1, TM_Z2 = 51, 55

    # ── 5a. 云杉栅栏立柱，每2格一根 ──
    # x=44 的柱已在连接段建过(PILLAR)，花架从 x=46 开始用云杉栅栏
    trellis_pillar_xs = list(range(46, TM_X2 + 1, 2))  # 46,48,50,52,54,56

    for px in trellis_pillar_xs:
        for pz in [TM_Z1, TM_Z2]:
            # 栅栏立柱，高5格
            b.fill(px, pillar_b, pz, px, pillar_t, pz, SPRUCE_F)

    # ── 5b. 顶部栅栏横梁 ──
    # 沿 X 方向的横梁（北侧 Z=51，南侧 Z=55）
    b.fill(TM_X1, beam_y, TM_Z1, TM_X2, beam_y, TM_Z1, SPRUCE_F)
    b.fill(TM_X1, beam_y, TM_Z2, TM_X2, beam_y, TM_Z2, SPRUCE_F)

    # 沿 Z 方向的横梁（每2格一根，与立柱对齐）
    for px in trellis_pillar_xs:
        b.fill(px, beam_y, TM_Z1, px, beam_y, TM_Z2, SPRUCE_F)

    # 顶部铺设栅栏网格
    for x in range(TM_X1, TM_X2 + 1):
        for z in range(TM_Z1 + 1, TM_Z2):
            if (x + z) % 2 == 0:
                b.setblock(x, beam_y, z, SPRUCE_F)

    # ── 5c. vine 垂挂 — 模拟荼蘼缠绕 ──
    for x in range(TM_X1 + 1, TM_X2, 2):
        # 从顶部向下挂 2~3 格
        for z in [TM_Z1, TM_Z2]:
            # 外侧挂
            if z == TM_Z1:
                face = "south=true"
                vz = z - 1
            else:
                face = "north=true"
                vz = z + 1
            for dy in range(0, 3):
                b.setblock(x, beam_y - dy, vz, f"{VINE}[{face}]")

        # 顶部内侧也挂一些
        for z in range(TM_Z1 + 1, TM_Z2):
            if (x + z) % 3 == 0:
                b.setblock(x, beam_y - 1, z, f"{VINE}[south=true]")

    # ── 5d. 活板门装饰（花架侧面）──
    for x in range(TM_X1 + 1, TM_X2, 3):
        b.setblock(x, pillar_b + 2, TM_Z1,
                   f"{TRAPDOOR}[facing=south,half=bottom,open=true]")
        b.setblock(x, pillar_b + 2, TM_Z2,
                   f"{TRAPDOOR}[facing=north,half=bottom,open=true]")

    # ================================================================
    # 6. 灯笼
    # ================================================================
    print("  [6/6] 灯笼...")

    # 听雨轩内 2 盏（挂在梁下）
    b.setblock(32, beam_y - 1, 54, f"{LANTERN}[hanging=true]")
    b.setblock(36, beam_y - 1, 54, f"{LANTERN}[hanging=true]")

    # 花架中间 2 盏
    b.setblock(48, beam_y - 1, 53, f"{LANTERN}[hanging=true]")
    b.setblock(52, beam_y - 1, 53, f"{LANTERN}[hanging=true]")

    # ================================================================
    # 7. 【修复】远香堂→C群 连接石径（露天 dirt_path）
    # ================================================================
    # 远香堂 X:49~67, Z:62~72，北面(Z=62)朝湖开敞
    # C群南端 Z=57。石径从 C群(X=42~43, Z=57) 向南到 Z=62，
    # 再沿 Z=62 向东延伸到远香堂西北角(X=49)
    # 远香堂北面是临湖开敞面，从西北角(X=49,Z=62)转入石径
    print("  [7/8] 远香堂连接石径...")
    PATH_BLOCK = "minecraft:dirt_path"

    # ── 7a. 南北段：X=42~43, Z=57~62（C群→远香堂纬度）──
    for z in range(57, 63):  # Z=57~62
        b.setblock(42, floor_y, z, PATH_BLOCK)
        b.setblock(43, floor_y, z, PATH_BLOCK)
    # dirt_path 需要 dirt 支撑
    for z in range(57, 63):
        b.setblock(42, ground_y, z, "minecraft:dirt")
        b.setblock(43, ground_y, z, "minecraft:dirt")

    # ── 7b. 东西段：沿 Z=62 从 X=44 向东延伸到 X=49（远香堂西北角）──
    # 宽度2格：Z=62~63，确保走路不会掉下去
    for x in range(44, 50):  # X=44~49
        for z in [62, 63]:
            b.setblock(x, floor_y, z, PATH_BLOCK)
            b.setblock(x, ground_y, z, "minecraft:dirt")

    # ── 7c. 在远香堂西北角(X=49, Z=62~63)放踏步，衔接台基高差 ──
    # 远香堂台基在 Y0(=-60)，台基楼梯在 Y0+1(=-59)
    # 石径在 floor_y(=-59)，与台基楼梯同高，无高差，直接走上去
    # 但需要确保 X=49 处的台基楼梯朝向正确（朝西，方便从石径走上来）
    # 这部分在 cluster_d.py 中修改

    # ================================================================
    # 注册边界框（南侧扩展到 Z=63 以覆盖石径 L 形路径）
    # ================================================================
    b.register_bbox("cluster_c",
                    X_MIN - 1, base_y, Z_MIN - 1,
                    X_MAX + 1, roof_y + 5, max(Z_MAX, 63) + 1)

    cmd_used = b.cmd_count - cmd_start
    print(f"  C群建造完成! ({cmd_used} commands)")


# ── 入口 ──

if __name__ == "__main__":
    with MinecraftBuilder() as b:
        build_cluster_c(b)
        print(f"Done! Total commands: {b.cmd_count}")
