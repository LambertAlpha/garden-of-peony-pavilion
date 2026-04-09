"""入口建筑群一体化重建 — 门楼+门厅+天井+影壁 整体设计

设计参照留园入口序列，从南到北：
  1. 门楼 (Z=89~90): 2格深，门框+匾额，悬山小顶
  2. 门厅 (Z=84~88): 5格深，歇山屋顶，两侧实墙，南北各留5格宽门洞
  3. 过渡天井 (Z=81~83): 3格深，露天！地面铺装，东西矮墙(1格高)
  4. 影壁 (Z=80): 白墙9格宽4格高，正对门厅北门
  5. 影壁后天井 (Z=78~79): 2格深，影壁两侧各3格通道可绕行
  6. 北出口 (Z=77): 通向远香堂方向，5格宽

核心原则：
  - 一个函数完成全部建造，没有"衔接修复"
  - 地面 Z=77~90 连续铺装
  - 墙体共享——门厅东西墙延续到天井矮墙
  - 屋顶只覆盖门厅(Z=84~88)，天井露天
  - 门洞宽度统一5格 (cx-2 ~ cx+2)
  - 所有通行高度 >= 3格

用法:
    from fixes.rebuild_entrance import build_entrance_complex
    build_entrance_complex(b)
"""

import sys
sys.path.insert(0, '/Users/lambertlin/minecraft-server/scripts')

from blocks import PALETTE, BUILD_Y


# ══════════════════════════════════════════════════════════════
#  材质常量
# ══════════════════════════════════════════════════════════════

AIR        = PALETTE["air"]
PILLAR     = PALETTE["pillar"]         # stripped_crimson_stem
BEAM       = PALETTE["beam"]           # dark_oak_planks
BEAM_LOG   = PALETTE["beam_log"]       # dark_oak_log
ROOF_STAIR = PALETTE["roof"]           # stone_brick_stairs
ROOF_SLAB  = PALETTE["roof_slab"]      # stone_brick_slab
ROOF_BLOCK = PALETTE["roof_block"]     # stone_bricks
WALL_BLOCK = PALETTE["wall"]           # white_concrete
WALL_BASE  = PALETTE["wall_base"]      # stone_bricks
WALL_CAP   = PALETTE["wall_cap"]       # stone_brick_slab
FLOOR      = PALETTE["floor"]          # smooth_stone
FLOOR_ALT  = PALETTE["base_col"]       # polished_andesite
LANTERN    = PALETTE["lantern"]
WINDOW     = PALETTE["window"]         # iron_bars
DOOR       = PALETTE["door"]           # crimson_door
EAVE_STAIR = PALETTE["eave_outer"]     # dark_oak_stairs
EAVE_SLAB  = PALETTE["eave_slab"]      # dark_oak_slab


# ══════════════════════════════════════════════════════════════
#  方块状态辅助
# ══════════════════════════════════════════════════════════════

def _stair(block, facing, half="bottom", shape="straight"):
    return f"{block}[facing={facing},half={half},shape={shape}]"

def _slab(block, stype="bottom"):
    return f"{block}[type={stype}]"

def _door(block, facing, half="lower", hinge="left", open_="false"):
    return f"{block}[facing={facing},half={half},hinge={hinge},open={open_}]"


# ══════════════════════════════════════════════════════════════
#  主函数
# ══════════════════════════════════════════════════════════════

def build_entrance_complex(b):
    """入口建筑群 — 门楼+门厅+天井+影壁 一体化建造"""
    print("=" * 55)
    print("=== 入口建筑群 一体化重建 ===")
    print("=" * 55)

    # ── 全局坐标 ──
    x1, x2 = 51, 65          # 东西边界 (15格宽)
    z_south, z_north = 90, 77 # 南北边界 (14格深)
    cx = 58                   # 中轴线
    gy = BUILD_Y              # -60, 地面标高
    cmd_start = b.cmd_count

    # ══════════════════════════════════════════════════════════
    #  0. 清除整个区域 — 干干净净从头来
    # ══════════════════════════════════════════════════════════
    print("  [0] 清除整个入口区域...")
    # 比实际范围多1格余量，确保清除旧屋顶飞檐等残留
    b.fill(x1 - 1, gy, z_north - 1, x2 + 1, gy + 16, z_south + 1, AIR)
    # 注册边界框以便日后撤销
    b.register_bbox("entrance_complex", x1 - 1, gy, z_north - 1,
                     x2 + 1, gy + 16, z_south + 1)

    # ══════════════════════════════════════════════════════════
    #  1. 统一地面铺装 Z=77~90 — 不留任何断裂
    # ══════════════════════════════════════════════════════════
    print("  [1] 统一地面铺装 Z=77~90...")

    # 台基层 (石砖，整个区域)
    b.fill(x1, gy, z_north, x2, gy, z_south, WALL_BASE)

    # 地面层 — smooth_stone 与 polished_andesite 逐行交替
    for z in range(z_north, z_south + 1):
        block = FLOOR if z % 2 == 0 else FLOOR_ALT
        b.fill(x1, gy + 1, z, x2, gy + 1, z, block)

    # 中轴线特别铺装 — 5格宽红砖标记主动线 (cx-2 ~ cx+2)
    # 用 stone_bricks 区分中轴，给人一种引导感
    for z in range(z_north, z_south + 1):
        b.fill(cx - 2, gy + 1, z, cx + 2, gy + 1, z, PALETTE["floor_alt"])

    # ══════════════════════════════════════════════════════════
    #  2. 门楼 (Z=89~90) — 入口第一道门面
    # ══════════════════════════════════════════════════════════
    print("  [2] 门楼 Z=89~90...")

    # --- 2a. 两侧门垛 (门楼的实体部分) ---
    # 西侧门垛: X=51~55
    b.fill(x1, gy + 2, 89, x1 + 4, gy + 5, 90, WALL_BLOCK)
    # 东侧门垛: X=61~65
    b.fill(x2 - 4, gy + 2, 89, x2, gy + 5, 90, WALL_BLOCK)

    # 门垛底部石砖勒脚
    b.fill(x1, gy + 2, 89, x1 + 4, gy + 2, 90, WALL_BASE)
    b.fill(x2 - 4, gy + 2, 89, x2, gy + 2, 90, WALL_BASE)

    # --- 2b. 门框 (5格宽门洞: cx-2=56 ~ cx+2=60) ---
    # 门框立柱
    for z in [89, 90]:
        b.fill(cx - 3, gy + 2, z, cx - 3, gy + 5, z, PILLAR)  # X=55 西柱
        b.fill(cx + 3, gy + 2, z, cx + 3, gy + 5, z, PILLAR)  # X=61 东柱

    # 门框横梁 (顶部)
    b.fill(cx - 3, gy + 5, 89, cx + 3, gy + 5, 90, BEAM)
    # 门洞内净空 (5格宽 x 3格高)
    b.fill(cx - 2, gy + 2, 89, cx + 2, gy + 4, 90, AIR)

    # --- 2c. 匾额 (门楼正中上方) ---
    # 用 dark_oak_log 做匾额框
    b.fill(cx - 1, gy + 5, 90, cx + 1, gy + 5, 90, BEAM_LOG)

    # --- 2d. 门楼悬山小顶 ---
    gate_roof_y = gy + 6  # 屋顶起始高度

    # 两坡屋面 — 东西方向延伸，南北2格深(Z=89~90)
    # 使用eave层(dark_oak) + 主体层(stone_brick)
    for z in [89, 90]:
        # 第一层檐口: 向外挑出1格
        b.setblock(x1 - 1, gate_roof_y, z,
                   _stair(EAVE_STAIR, "east"))
        b.setblock(x2 + 1, gate_roof_y, z,
                   _stair(EAVE_STAIR, "west"))
        # 东西两侧坡面
        b.setblock(x1, gate_roof_y, z,
                   _stair(ROOF_STAIR, "east"))
        b.setblock(x2, gate_roof_y, z,
                   _stair(ROOF_STAIR, "west"))
        # 第二层
        b.fill(x1 + 1, gate_roof_y + 1, z, x1 + 2, gate_roof_y + 1, z,
               _stair(ROOF_STAIR, "east"))
        b.fill(x2 - 2, gate_roof_y + 1, z, x2 - 1, gate_roof_y + 1, z,
               _stair(ROOF_STAIR, "west"))
        # 第三层
        b.fill(x1 + 3, gate_roof_y + 2, z, cx - 1, gate_roof_y + 2, z,
               _stair(ROOF_STAIR, "east"))
        b.fill(cx + 1, gate_roof_y + 2, z, x2 - 3, gate_roof_y + 2, z,
               _stair(ROOF_STAIR, "west"))
        # 脊 (中间1格)
        b.setblock(cx, gate_roof_y + 2, z, _slab(ROOF_SLAB, "bottom"))

    # 门楼屋脊装饰 — 前后两端悬山挑出
    for z_edge in [88, 91]:
        b.setblock(cx, gate_roof_y + 2, z_edge, _slab(EAVE_SLAB, "bottom"))
        b.setblock(x1, gate_roof_y, z_edge,
                   _stair(EAVE_STAIR, "east"))
        b.setblock(x2, gate_roof_y, z_edge,
                   _stair(EAVE_STAIR, "west"))

    # ══════════════════════════════════════════════════════════
    #  3. 门厅 (Z=84~88) — 主体建筑，有屋顶！
    # ══════════════════════════════════════════════════════════
    print("  [3] 门厅 Z=84~88 (含歇山屋顶)...")

    hall_z1 = 84  # 北界
    hall_z2 = 88  # 南界
    pillar_h = 5  # 柱高
    top_y = gy + 1 + pillar_h  # gy+6, 梁底/柱顶标高

    # --- 3a. 柱子 (6根：东西各3根) ---
    pillar_positions = [
        # 西侧柱列 X=52
        (x1 + 1, hall_z1), (x1 + 1, 86), (x1 + 1, hall_z2),
        # 东侧柱列 X=64
        (x2 - 1, hall_z1), (x2 - 1, 86), (x2 - 1, hall_z2),
    ]
    for px, pz in pillar_positions:
        b.fill(px, gy + 2, pz, px, gy + 1 + pillar_h, pz, PILLAR)
        # 柱础 (polished_andesite)
        b.setblock(px, gy + 1, pz, FLOOR_ALT)

    # --- 3b. 东西实墙 (门厅两侧封闭) ---
    # 西墙 X=51, Z=84~88
    b.fill(x1, gy + 2, hall_z1, x1, gy + 1 + pillar_h, hall_z2, WALL_BLOCK)
    # 东墙 X=65, Z=84~88
    b.fill(x2, gy + 2, hall_z1, x2, gy + 1 + pillar_h, hall_z2, WALL_BLOCK)

    # 墙基勒脚 (石砖，底部1格)
    b.fill(x1, gy + 2, hall_z1, x1, gy + 2, hall_z2, WALL_BASE)
    b.fill(x2, gy + 2, hall_z1, x2, gy + 2, hall_z2, WALL_BASE)

    # 西墙铁栏窗 (两扇，Z=85和Z=87)
    for wz in [85, 87]:
        b.fill(x1, gy + 3, wz, x1, gy + 4, wz, WINDOW)
    # 东墙铁栏窗
    for wz in [85, 87]:
        b.fill(x2, gy + 3, wz, x2, gy + 4, wz, WINDOW)

    # --- 3c. 南门洞 (Z=88, 面向门楼方向) ---
    # 南墙 Z=88 — 门洞两侧填墙
    b.fill(x1, gy + 2, hall_z2, cx - 3, gy + 1 + pillar_h, hall_z2, WALL_BLOCK)
    b.fill(cx + 3, gy + 2, hall_z2, x2, gy + 1 + pillar_h, hall_z2, WALL_BLOCK)
    # 门框柱
    b.fill(cx - 3, gy + 2, hall_z2, cx - 3, gy + 4, hall_z2, PILLAR)
    b.fill(cx + 3, gy + 2, hall_z2, cx + 3, gy + 4, hall_z2, PILLAR)
    # 门框横梁
    b.fill(cx - 3, gy + 5, hall_z2, cx + 3, gy + 5, hall_z2, BEAM)
    # 门洞净空 (5格宽 x 3格高: cx-2~cx+2, gy+2~gy+4)
    b.fill(cx - 2, gy + 2, hall_z2, cx + 2, gy + 4, hall_z2, AIR)

    # --- 3d. 北门洞 (Z=84, 面向天井方向) ---
    b.fill(x1, gy + 2, hall_z1, cx - 3, gy + 1 + pillar_h, hall_z1, WALL_BLOCK)
    b.fill(cx + 3, gy + 2, hall_z1, x2, gy + 1 + pillar_h, hall_z1, WALL_BLOCK)
    # 门框柱
    b.fill(cx - 3, gy + 2, hall_z1, cx - 3, gy + 4, hall_z1, PILLAR)
    b.fill(cx + 3, gy + 2, hall_z1, cx + 3, gy + 4, hall_z1, PILLAR)
    # 门框横梁
    b.fill(cx - 3, gy + 5, hall_z1, cx + 3, gy + 5, hall_z1, BEAM)
    # 门洞净空
    b.fill(cx - 2, gy + 2, hall_z1, cx + 2, gy + 4, hall_z1, AIR)

    # --- 3e. 梁架 (东西向，连接柱顶) ---
    # 横梁 — 沿Z方向每根柱子处一条东西向梁
    for bz in [hall_z1, 86, hall_z2]:
        b.fill(x1, top_y, bz, x2, top_y, bz, BEAM)
    # 纵梁 — 东西两侧柱顶连接
    b.fill(x1 + 1, top_y, hall_z1, x1 + 1, top_y, hall_z2, BEAM)
    b.fill(x2 - 1, top_y, hall_z1, x2 - 1, top_y, hall_z2, BEAM)
    # 脊檩 — 正中
    b.fill(cx, top_y, hall_z1, cx, top_y, hall_z2, BEAM_LOG)

    # --- 3f. 歇山屋顶 ---
    # 屋顶高度: top_y+1 起 (gy+7)
    # 歇山 = 四坡顶，山面上部做三角形小山花
    roof_y = top_y + 1  # gy+7

    # 第一层: 檐口 — 四面外挑1格
    # 南北两坡
    for z in range(hall_z1, hall_z2 + 1):
        # 西侧飞檐
        b.setblock(x1 - 1, roof_y, z, _stair(EAVE_STAIR, "east"))
        b.setblock(x1, roof_y, z, _stair(ROOF_STAIR, "east"))
        # 东侧飞檐
        b.setblock(x2 + 1, roof_y, z, _stair(EAVE_STAIR, "west"))
        b.setblock(x2, roof_y, z, _stair(ROOF_STAIR, "west"))
    # 南檐
    for x in range(x1 + 1, x2):
        b.setblock(x, roof_y, hall_z2 + 1, _stair(EAVE_STAIR, "north"))
    # 北檐
    for x in range(x1 + 1, x2):
        b.setblock(x, roof_y, hall_z1 - 1, _stair(EAVE_STAIR, "south"))
    # 四角翘角
    b.setblock(x1 - 1, roof_y, hall_z2 + 1, _stair(EAVE_STAIR, "east"))
    b.setblock(x2 + 1, roof_y, hall_z2 + 1, _stair(EAVE_STAIR, "west"))
    b.setblock(x1 - 1, roof_y, hall_z1 - 1, _stair(EAVE_STAIR, "east"))
    b.setblock(x2 + 1, roof_y, hall_z1 - 1, _stair(EAVE_STAIR, "west"))

    # 第二层 (roof_y+1 = gy+8)
    for z in range(hall_z1, hall_z2 + 1):
        b.setblock(x1 + 1, roof_y + 1, z, _stair(ROOF_STAIR, "east"))
        b.setblock(x1 + 2, roof_y + 1, z, _stair(ROOF_STAIR, "east"))
        b.setblock(x2 - 1, roof_y + 1, z, _stair(ROOF_STAIR, "west"))
        b.setblock(x2 - 2, roof_y + 1, z, _stair(ROOF_STAIR, "west"))
    # 南北坡第二层
    for x in range(x1 + 3, x2 - 2):
        b.setblock(x, roof_y + 1, hall_z2, _stair(ROOF_STAIR, "north"))
        b.setblock(x, roof_y + 1, hall_z1, _stair(ROOF_STAIR, "south"))

    # 第三层 (roof_y+2 = gy+9)
    for z in range(hall_z1 + 1, hall_z2):
        b.setblock(x1 + 3, roof_y + 2, z, _stair(ROOF_STAIR, "east"))
        b.setblock(x1 + 4, roof_y + 2, z, _stair(ROOF_STAIR, "east"))
        b.setblock(x2 - 3, roof_y + 2, z, _stair(ROOF_STAIR, "west"))
        b.setblock(x2 - 4, roof_y + 2, z, _stair(ROOF_STAIR, "west"))
    # 南北坡第三层 (两端收缩)
    for x in range(x1 + 5, x2 - 4):
        b.setblock(x, roof_y + 2, hall_z2 - 1,
                   _stair(ROOF_STAIR, "north"))
        b.setblock(x, roof_y + 2, hall_z1 + 1,
                   _stair(ROOF_STAIR, "south"))
    # 歇山山花面(南北端面) — 三角形白墙填充
    for z_face, stair_dir in [(hall_z1, "south"), (hall_z2, "north")]:
        b.fill(x1 + 3, roof_y + 2, z_face, x2 - 3, roof_y + 2, z_face,
               ROOF_BLOCK)

    # 第四层: 脊 (roof_y+3 = gy+10)
    for z in range(hall_z1 + 1, hall_z2):
        b.fill(x1 + 5, roof_y + 3, z, x2 - 5, roof_y + 3, z, ROOF_BLOCK)
    # 脊顶slab
    for z in range(hall_z1 + 1, hall_z2):
        b.fill(x1 + 5, roof_y + 4, z, x2 - 5, roof_y + 4, z,
               _slab(ROOF_SLAB, "bottom"))
    # 正脊两端鸱尾装饰 (用 lightning_rod)
    b.setblock(cx, roof_y + 5, hall_z1 + 1, PALETTE["lightning_rod"])
    b.setblock(cx, roof_y + 5, hall_z2 - 1, PALETTE["lightning_rod"])

    # --- 3g. 门厅内部装饰 ---
    # 悬挂灯笼 (梁下)
    for lz in [85, 87]:
        b.setblock(cx, top_y - 1, lz, f"{LANTERN}[hanging=true]")
    # 两侧壁灯
    for lz in [85, 87]:
        b.setblock(x1 + 1, gy + 4, lz, f"{LANTERN}[hanging=false]")
        b.setblock(x2 - 1, gy + 4, lz, f"{LANTERN}[hanging=false]")

    # ══════════════════════════════════════════════════════════
    #  4. 过渡天井 (Z=81~83) — 露天！无顶！
    # ══════════════════════════════════════════════════════════
    print("  [4] 过渡天井 Z=81~83 (露天)...")

    # 地面已经在步骤1统一铺设，这里只建墙

    # 东西矮墙 (1格高 = 膝盖高度，起引导视线的作用)
    # 西侧矮墙 X=51
    b.fill(x1, gy + 2, 81, x1, gy + 2, 83, WALL_BASE)
    b.fill(x1, gy + 3, 81, x1, gy + 3, 83, _slab(WALL_CAP, "bottom"))
    # 东侧矮墙 X=65
    b.fill(x2, gy + 2, 81, x2, gy + 2, 83, WALL_BASE)
    b.fill(x2, gy + 3, 81, x2, gy + 3, 83, _slab(WALL_CAP, "bottom"))

    # 天井角落装饰: 四个石砖方柱标记天井范围
    for corner_x in [x1 + 1, x2 - 1]:
        for corner_z in [81, 83]:
            b.fill(corner_x, gy + 2, corner_z,
                   corner_x, gy + 4, corner_z, PILLAR)

    # 天井内置灯笼 (地面灯, 矮墙内侧)
    b.setblock(x1 + 1, gy + 2, 82, f"{LANTERN}[hanging=false]")
    b.setblock(x2 - 1, gy + 2, 82, f"{LANTERN}[hanging=false]")

    # ══════════════════════════════════════════════════════════
    #  5. 影壁 (Z=80) — 进门正对，挡住视线
    # ══════════════════════════════════════════════════════════
    print("  [5] 影壁 Z=80...")

    sw_x1 = cx - 4  # 54
    sw_x2 = cx + 4  # 62
    sw_h = 4         # 4格高 (gy+2 ~ gy+5)

    # 影壁基座 (石砖)
    b.fill(sw_x1, gy + 1, 80, sw_x2, gy + 1, 80, WALL_BASE)
    b.fill(sw_x1, gy + 2, 80, sw_x2, gy + 2, 80, WALL_BASE)

    # 影壁墙身 (白色混凝土)
    b.fill(sw_x1, gy + 3, 80, sw_x2, gy + sw_h, 80, WALL_BLOCK)

    # 影壁压顶 (石砖slab)
    b.fill(sw_x1, gy + sw_h + 1, 80, sw_x2, gy + sw_h + 1, 80,
           _slab(WALL_CAP, "bottom"))

    # 影壁两端立柱装饰
    b.fill(sw_x1, gy + 2, 80, sw_x1, gy + sw_h, 80, PILLAR)
    b.fill(sw_x2, gy + 2, 80, sw_x2, gy + sw_h, 80, PILLAR)

    # 中央匾额装饰 (dark_oak_log)
    b.fill(cx - 1, gy + 3, 80, cx + 1, gy + 4, 80, BEAM_LOG)

    # ══════════════════════════════════════════════════════════
    #  6. 影壁后天井 (Z=78~79) — 绕行空间
    # ══════════════════════════════════════════════════════════
    print("  [6] 影壁后天井 Z=78~79...")

    # 地面已铺好。这里确保影壁两侧通道通畅:
    # 西通道: X=51~53 (sw_x1=54, 所以51~53三格可通行)
    # 东通道: X=63~65 (sw_x2=62, 所以63~65三格可通行)

    # 两侧通道的围墙(与天井矮墙风格一致)
    # 西侧围墙 X=51
    b.fill(x1, gy + 2, 78, x1, gy + 2, 79, WALL_BASE)
    b.fill(x1, gy + 3, 78, x1, gy + 3, 79, _slab(WALL_CAP, "bottom"))
    # 东侧围墙 X=65
    b.fill(x2, gy + 2, 78, x2, gy + 2, 79, WALL_BASE)
    b.fill(x2, gy + 3, 78, x2, gy + 3, 79, _slab(WALL_CAP, "bottom"))

    # 确保通道上方无遮挡 (3格净高)
    b.fill(x1 + 1, gy + 2, 78, sw_x1 - 1, gy + 5, 79, AIR)  # 西通道
    b.fill(sw_x2 + 1, gy + 2, 78, x2 - 1, gy + 5, 79, AIR)  # 东通道

    # ══════════════════════════════════════════════════════════
    #  7. 北出口 (Z=77) — 通向远香堂
    # ══════════════════════════════════════════════════════════
    print("  [7] 北出口 Z=77...")

    # 北端墙 (东西两段，中间留5格宽出口)
    b.fill(x1, gy + 2, 77, cx - 3, gy + 4, 77, WALL_BLOCK)
    b.fill(cx + 3, gy + 2, 77, x2, gy + 4, 77, WALL_BLOCK)

    # 北墙基座
    b.fill(x1, gy + 2, 77, cx - 3, gy + 2, 77, WALL_BASE)
    b.fill(cx + 3, gy + 2, 77, x2, gy + 2, 77, WALL_BASE)

    # 北墙压顶
    b.fill(x1, gy + 5, 77, cx - 3, gy + 5, 77,
           _slab(WALL_CAP, "bottom"))
    b.fill(cx + 3, gy + 5, 77, x2, gy + 5, 77,
           _slab(WALL_CAP, "bottom"))

    # 出口门框
    b.fill(cx - 3, gy + 2, 77, cx - 3, gy + 4, 77, PILLAR)
    b.fill(cx + 3, gy + 2, 77, cx + 3, gy + 4, 77, PILLAR)
    b.fill(cx - 3, gy + 5, 77, cx + 3, gy + 5, 77, BEAM)

    # 出口上方灯笼
    b.setblock(cx, gy + 4, 77, f"{LANTERN}[hanging=true]")

    # ══════════════════════════════════════════════════════════
    #  完成
    # ══════════════════════════════════════════════════════════
    total = b.cmd_count - cmd_start
    print()
    print("=" * 55)
    print(f"入口建筑群重建完成! 总命令数: {total}")
    print("=" * 55)
    print(f"  门楼:      Z=89~90, 门洞 X={cx-2}~{cx+2}")
    print(f"  门厅:      Z=84~88, 歇山顶, 两侧实墙")
    print(f"  过渡天井:  Z=81~83, 露天, 矮墙引导")
    print(f"  影壁:      Z=80, X={sw_x1}~{sw_x2}, 高{sw_h}格")
    print(f"  影壁后:    Z=78~79, 两侧3格通道")
    print(f"  北出口:    Z=77, X={cx-2}~{cx+2}")
    print(f"  地面连续:  Z=77~90, 无断裂")


# ══════════════════════════════════════════════════════════════
#  直接运行
# ══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    from builder import MinecraftBuilder
    print("连接 Minecraft 服务器...")
    with MinecraftBuilder() as b:
        build_entrance_complex(b)
        print(f"\n全部完成. 总 RCON 命令: {b.cmd_count}")
