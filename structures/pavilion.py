"""牡丹亭 — 四角攒尖亭

《牡丹亭·游园惊梦》中杜丽娘梦遇柳梦梅之地，全园视觉焦点。
形制：须弥座台基 + 四柱 + 斗拱 + 攒尖顶（飞檐翘角）+ 避雷针宝顶。
"""

import sys; sys.path.insert(0, '/Users/lambertlin/minecraft-server/scripts')
from builder import MinecraftBuilder
from blocks import PALETTE, GROUND_Y


def build_pavilion(b: MinecraftBuilder, cx: int, ground_y: int, cz: int):
    """
    建造牡丹亭（四角攒尖亭）

    Parameters:
        cx, cz  : 亭中心 XZ 坐标
        ground_y: 当地地面 Y 坐标（台基底面）
    """
    print(f"=== 牡丹亭 at ({cx}, {ground_y}, {cz}) ===")

    # ── 常用方块 ──
    BASE       = PALETTE["base"]           # stone_bricks
    BASE_STEP  = PALETTE["base_step"]      # stone_brick_stairs
    BASE_SLAB  = PALETTE["base_slab"]      # stone_brick_slab
    BASE_COL   = PALETTE["base_col"]       # stone_slab (柱础)
    PILLAR     = PALETTE["pillar"]         # stripped_acacia_log
    BEAM       = PALETTE["beam"]           # dark_oak_planks
    ROOF       = PALETTE["roof"]           # deepslate_tile_stairs
    ROOF_BLOCK = PALETTE["roof_block"]     # deepslate_tiles
    FLOOR      = PALETTE["floor"]          # smooth_stone
    RAIL       = PALETTE["rail"]           # acacia_fence
    ROD        = PALETTE["lightning_rod"]  # lightning_rod (宝顶)

    # ── 高度基准 ──
    # ground_y     : 高地地面（台基底面）
    # ground_y + 1 : 台基第一层（stone_bricks）
    # ground_y + 2 : 台基第二层（楼梯围边 + 中间半砖）= 台面
    # ground_y + 3 : 亭内地面铺装 + 栏杆层
    # ground_y + 3 ~ +7 : 柱子（5格高，从 +3 到 +7）
    # ground_y + 8 : 额枋/梁
    # ground_y + 8 : 斗拱（柱顶层）
    # ground_y + 9 : 屋顶第1层 (9x9)
    # ground_y +10 : 屋顶第2层 (7x7)
    # ground_y +11 : 屋顶第3层 (5x5)
    # ground_y +12 : 屋顶第4层 (3x3 实心)
    # ground_y +13 : 宝顶

    base_y   = ground_y       # 台基底面
    floor_y  = ground_y + 2   # 台面/亭内地面
    pillar_b = ground_y + 3   # 柱子底部
    pillar_t = ground_y + 7   # 柱子顶部
    beam_y   = ground_y + 8   # 额枋层
    roof_y   = ground_y + 9   # 屋顶起始层

    # 台基范围：中心 ±5 → 11×11
    R_BASE = 5
    # 柱位：距台基边缘2格内缩 → 中心 ±3，形成 7×7 柱间距
    R_COL = 3

    # ================================================================
    # 1. 台基（须弥座）—— 2格高，底实上饰
    # ================================================================
    print("  [1/8] 台基（须弥座）...")

    # --- 底层 (base_y + 1)：stone_bricks 全铺 11×11 ---
    b.fill(cx - R_BASE, base_y + 1, cz - R_BASE,
           cx + R_BASE, base_y + 1, cz + R_BASE, BASE)

    # --- 上层 (base_y + 2)：楼梯围边 + 中间半砖 ---
    # 先铺满中间用半砖（top half，与楼梯齐平）
    b.fill(cx - R_BASE + 1, base_y + 2, cz - R_BASE + 1,
           cx + R_BASE - 1, base_y + 2, cz + R_BASE - 1,
           f"{BASE_SLAB}[type=top]")

    # 四面楼梯围边（朝外）
    # 北面 (z = cz - R_BASE): facing=south → 低端朝南（朝外=朝北，但facing是低端朝向）
    #   须弥座楼梯朝外 = 楼梯高端朝内、低端朝外
    #   北面低端朝北 → facing=north
    for x in range(cx - R_BASE, cx + R_BASE + 1):
        b.setblock(x, base_y + 2, cz - R_BASE,
                   f"{BASE_STEP}[facing=north,half=top]")  # 北面，朝外
        b.setblock(x, base_y + 2, cz + R_BASE,
                   f"{BASE_STEP}[facing=south,half=top]")  # 南面，朝外
    for z in range(cz - R_BASE, cz + R_BASE + 1):
        b.setblock(cx - R_BASE, base_y + 2, z,
                   f"{BASE_STEP}[facing=west,half=top]")   # 西面，朝外
        b.setblock(cx + R_BASE, base_y + 2, z,
                   f"{BASE_STEP}[facing=east,half=top]")   # 东面，朝外

    # --- 四面踏步（每面中间3格）---
    # 踏步从地面 (base_y) 到台面 (base_y + 2)，共2级
    # 北面踏步 (z = cz - R_BASE - 1 和 cz - R_BASE)
    for x in range(cx - 1, cx + 2):  # 中间3格
        b.setblock(x, base_y + 1, cz - R_BASE - 1,
                   f"{BASE_STEP}[facing=south,half=bottom]")  # 第一级，从北走上来
        b.setblock(x, base_y + 2, cz - R_BASE,
                   f"{BASE_STEP}[facing=south,half=bottom]")  # 第二级（覆盖围边楼梯）

    # 南面踏步
    for x in range(cx - 1, cx + 2):
        b.setblock(x, base_y + 1, cz + R_BASE + 1,
                   f"{BASE_STEP}[facing=north,half=bottom]")
        b.setblock(x, base_y + 2, cz + R_BASE,
                   f"{BASE_STEP}[facing=north,half=bottom]")

    # 西面踏步
    for z in range(cz - 1, cz + 2):
        b.setblock(cx - R_BASE - 1, base_y + 1, z,
                   f"{BASE_STEP}[facing=east,half=bottom]")
        b.setblock(cx - R_BASE, base_y + 2, z,
                   f"{BASE_STEP}[facing=east,half=bottom]")

    # 东面踏步
    for z in range(cz - 1, cz + 2):
        b.setblock(cx + R_BASE + 1, base_y + 1, z,
                   f"{BASE_STEP}[facing=west,half=bottom]")
        b.setblock(cx + R_BASE, base_y + 2, z,
                   f"{BASE_STEP}[facing=west,half=bottom]")

    # ================================================================
    # 2. 地面铺装 —— 台面顶部铺 smooth_stone
    # ================================================================
    print("  [2/8] 地面铺装...")

    # 台面内部（柱间区域及周围）铺 smooth_stone
    b.fill(cx - R_BASE + 1, floor_y + 1, cz - R_BASE + 1,
           cx + R_BASE - 1, floor_y + 1, cz + R_BASE - 1, FLOOR)

    # ================================================================
    # 3. 柱子 + 柱础 —— 四角各一根
    # ================================================================
    print("  [3/8] 柱子 + 柱础...")

    col_positions = [
        (cx - R_COL, cz - R_COL),  # 西北角
        (cx + R_COL, cz - R_COL),  # 东北角
        (cx - R_COL, cz + R_COL),  # 西南角
        (cx + R_COL, cz + R_COL),  # 东南角
    ]

    for px, pz in col_positions:
        # 柱础（石半砖，在柱底下方 = 台面层）
        b.setblock(px, floor_y + 1, pz, BASE_COL)
        # 柱身（5格高）
        b.fill(px, pillar_b, pz, px, pillar_t, pz, PILLAR)

    # ================================================================
    # 4. 额枋/梁 —— 柱顶连接
    # ================================================================
    print("  [4/8] 额枋/梁...")

    # 四条梁连接四根柱子顶部上方1格
    # 北梁（西北 → 东北）
    b.fill(cx - R_COL, beam_y, cz - R_COL,
           cx + R_COL, beam_y, cz - R_COL, BEAM)
    # 南梁（西南 → 东南）
    b.fill(cx - R_COL, beam_y, cz + R_COL,
           cx + R_COL, beam_y, cz + R_COL, BEAM)
    # 西梁（西北 → 西南）
    b.fill(cx - R_COL, beam_y, cz - R_COL,
           cx - R_COL, beam_y, cz + R_COL, BEAM)
    # 东梁（东北 → 东南）
    b.fill(cx + R_COL, beam_y, cz - R_COL,
           cx + R_COL, beam_y, cz + R_COL, BEAM)

    # ================================================================
    # 5. 斗拱 —— 每根柱子顶部四方向出挑
    # ================================================================
    print("  [5/8] 斗拱...")

    # 深色橡木楼梯，在 beam_y 层，从每根柱子向外各放一个
    dougong_stair = "minecraft:dark_oak_stairs"
    for px, pz in col_positions:
        # 四个方向出挑（倒置楼梯，half=top，面朝外）
        # 北
        b.setblock(px, beam_y, pz - 1,
                   f"{dougong_stair}[facing=south,half=top]")
        # 南
        b.setblock(px, beam_y, pz + 1,
                   f"{dougong_stair}[facing=north,half=top]")
        # 西
        b.setblock(px - 1, beam_y, pz,
                   f"{dougong_stair}[facing=east,half=top]")
        # 东
        b.setblock(px + 1, beam_y, pz,
                   f"{dougong_stair}[facing=west,half=top]")

    # ================================================================
    # 6. 攒尖屋顶 —— 逐层缩小的楼梯金字塔
    # ================================================================
    print("  [6/8] 攒尖屋顶...")

    _build_pyramidal_roof(b, cx, cz, roof_y, ROOF, ROOF_BLOCK, ROD)

    # ================================================================
    # 7. 栏杆 —— 柱间金合欢栅栏
    # ================================================================
    print("  [7/8] 栏杆...")

    rail_y = pillar_b  # 栏杆在柱子底部同层（台面上方1格）

    # 北面栏杆（西北柱 → 东北柱，排除柱位本身）
    for x in range(cx - R_COL + 1, cx + R_COL):
        b.setblock(x, rail_y, cz - R_COL, RAIL)
    # 南面栏杆
    for x in range(cx - R_COL + 1, cx + R_COL):
        b.setblock(x, rail_y, cz + R_COL, RAIL)
    # 西面栏杆
    for z in range(cz - R_COL + 1, cz + R_COL):
        b.setblock(cx - R_COL, rail_y, z, RAIL)
    # 东面栏杆
    for z in range(cz - R_COL + 1, cz + R_COL):
        b.setblock(cx + R_COL, rail_y, z, RAIL)

    # ================================================================
    # 8. 注册边界框（用于撤销）
    # ================================================================
    print("  [8/8] 注册边界框...")

    b.register_bbox("pavilion",
                    cx - R_BASE - 1, base_y, cz - R_BASE - 1,
                    cx + R_BASE + 1, roof_y + 5, cz + R_BASE + 1)

    print("  牡丹亭建造完成！")


def _build_pyramidal_roof(b: MinecraftBuilder, cx: int, cz: int,
                          roof_y: int, ROOF: str, ROOF_BLOCK: str,
                          ROD: str):
    """
    攒尖顶：5层逐层缩小

    层级（从下到上）：
      第1层 roof_y+0 : 9×9 楼梯围边 + 飞檐翘角
      第2层 roof_y+1 : 7×7 楼梯围边
      第3层 roof_y+2 : 5×5 楼梯围边
      第4层 roof_y+3 : 3×3 实心深板岩瓦片
      第5层 roof_y+4 : 1×1 避雷针（宝顶）
    """

    # ── 通用辅助：放置一圈屋顶楼梯 ──
    def _roof_ring(y: int, half_size: int):
        """
        在 y 层放置 (2*half_size+1)×(2*half_size+1) 的楼梯围边。
        攒尖顶楼梯朝向：每面楼梯低端朝外（从檐口向屋脊升高）。
          北面 → facing=south （低端朝北=朝外）
          南面 → facing=north
          东面 → facing=west
          西面 → facing=east
        """
        n = cz - half_size  # 北边 z
        s = cz + half_size  # 南边 z
        w = cx - half_size  # 西边 x
        e = cx + half_size  # 东边 x

        # 北面一排（不含角）
        for x in range(w + 1, e):
            b.setblock(x, y, n, f"{ROOF}[facing=south,half=bottom]")
        # 南面一排（不含角）
        for x in range(w + 1, e):
            b.setblock(x, y, s, f"{ROOF}[facing=north,half=bottom]")
        # 西面一排（不含角）
        for z in range(n + 1, s):
            b.setblock(w, y, z, f"{ROOF}[facing=east,half=bottom]")
        # 东面一排（不含角）
        for z in range(n + 1, s):
            b.setblock(e, y, z, f"{ROOF}[facing=west,half=bottom]")

        # 四角转角楼梯（outer 形态）
        # 西北角：北面facing=south + 西面转角 → outer_right
        b.setblock(w, y, n,
                   f"{ROOF}[facing=south,half=bottom,shape=outer_right]")
        # 东北角：北面facing=south + 东面转角 → outer_left
        b.setblock(e, y, n,
                   f"{ROOF}[facing=south,half=bottom,shape=outer_left]")
        # 西南角：南面facing=north + 西面转角 → outer_left
        b.setblock(w, y, s,
                   f"{ROOF}[facing=north,half=bottom,shape=outer_left]")
        # 东南角：南面facing=north + 东面转角 → outer_right
        b.setblock(e, y, s,
                   f"{ROOF}[facing=north,half=bottom,shape=outer_right]")

    # ── 第1层：9×9 (half_size=4) ──
    _roof_ring(roof_y, 4)

    # ── 第1层飞檐翘角：四角各延伸1格，用倒置楼梯模拟上翘 ──
    hs = 4  # 第1层 half_size
    # 翘角位置：在四角再向外延伸1格对角线方向
    # 西北翘角
    b.setblock(cx - hs - 1, roof_y, cz - hs - 1,
               f"{ROOF}[facing=south,half=top,shape=outer_right]")
    # 西北角沿 x 轴延伸
    b.setblock(cx - hs - 1, roof_y, cz - hs,
               f"{ROOF}[facing=east,half=top]")
    # 西北角沿 z 轴延伸
    b.setblock(cx - hs, roof_y, cz - hs - 1,
               f"{ROOF}[facing=south,half=top]")

    # 东北翘角
    b.setblock(cx + hs + 1, roof_y, cz - hs - 1,
               f"{ROOF}[facing=south,half=top,shape=outer_left]")
    b.setblock(cx + hs + 1, roof_y, cz - hs,
               f"{ROOF}[facing=west,half=top]")
    b.setblock(cx + hs, roof_y, cz - hs - 1,
               f"{ROOF}[facing=south,half=top]")

    # 西南翘角
    b.setblock(cx - hs - 1, roof_y, cz + hs + 1,
               f"{ROOF}[facing=north,half=top,shape=outer_left]")
    b.setblock(cx - hs - 1, roof_y, cz + hs,
               f"{ROOF}[facing=east,half=top]")
    b.setblock(cx - hs, roof_y, cz + hs + 1,
               f"{ROOF}[facing=north,half=top]")

    # 东南翘角
    b.setblock(cx + hs + 1, roof_y, cz + hs + 1,
               f"{ROOF}[facing=north,half=top,shape=outer_right]")
    b.setblock(cx + hs + 1, roof_y, cz + hs,
               f"{ROOF}[facing=west,half=top]")
    b.setblock(cx + hs, roof_y, cz + hs + 1,
               f"{ROOF}[facing=north,half=top]")

    # ── 第2层：7×7 (half_size=3) ──
    _roof_ring(roof_y + 1, 3)

    # ── 第3层：5×5 (half_size=2) ──
    _roof_ring(roof_y + 2, 2)

    # ── 第4层：3×3 实心深板岩瓦片 ──
    b.fill(cx - 1, roof_y + 3, cz - 1,
           cx + 1, roof_y + 3, cz + 1, ROOF_BLOCK)

    # ── 第5层：宝顶（避雷针）──
    b.setblock(cx, roof_y + 4, cz, ROD)


# ── 入口 ──

if __name__ == "__main__":
    with MinecraftBuilder() as b:
        # 默认位置：北侧高地
        build_pavilion(b, cx=52, ground_y=-57, cz=10)
        print(f"Done! Total commands: {b.cmd_count}")
