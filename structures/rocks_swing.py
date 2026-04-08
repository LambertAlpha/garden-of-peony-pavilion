"""太湖石置石组 + 秋千 — 北侧高地景观

《牡丹亭》中太湖石是梦境核心地标——杜丽娘"倚太湖石"入梦；
秋千则是游园路线的节点——"秋千一两架""转过秋千"。

太湖石美学四字诀：瘦（上大下小）、皱（凹凸不平）、漏（穿行洞穴）、透（光线穿透）。
主石用手工逐层 pattern 建造，保证不规则的天然感。
"""

import sys; sys.path.insert(0, '/Users/lambertlin/minecraft-server/scripts')
from builder import MinecraftBuilder
from blocks import PALETTE, GROUND_Y
import random


# ══════════════════════════════════════════════════════════════
#  太湖石 — 主石 + 副石
# ══════════════════════════════════════════════════════════════

def _build_taihu_rocks(b: MinecraftBuilder, cx: int, ground_y: int, cz: int):
    """
    建造太湖石置石组（主石 + 2 块副石）

    Parameters:
        cx, cz  : 主石中心 XZ 坐标
        ground_y: 当地地面 Y 坐标
    """
    print(f"  太湖石 at ({cx}, {ground_y}, {cz})")

    MAIN  = PALETTE["taihu_main"]    # dripstone_block
    WHITE = PALETTE["taihu_white"]   # calcite
    MOSS  = PALETTE["taihu_moss"]    # moss_block
    MCARPET = PALETTE["moss_carpet"] # moss_carpet

    random.seed(42)

    # ── 主石：逐层手工 pattern ──
    # 每层是一个二维 pattern（相对于 cx-偏移, cz-偏移）
    # 1 = 石块, 0 = 空气
    # 原点 (0,0) 对应 (cx-3, cz-3) —— 即 pattern 左上角
    # pattern 尺寸统一 8×8，覆盖 cx-3 到 cx+4, cz-3 到 cz+4

    # 设计思路：
    # Layer 0-1: 底座，不规则但较窄（"瘦"的底部）
    # Layer 2:   稍微扩宽，洞穴通道开始（东西方向贯通）
    # Layer 3:   洞穴层（2×3 通道，Z 方向 3 格高在 layer 2-4）
    # Layer 4:   洞穴顶部，开始收束
    # Layer 5-6: 上部大幅扩宽（"瘦"= 上大下小）
    # Layer 7:   顶冠，不规则
    # Layer 8:   尖顶点缀

    layers = [
        # Layer 0 — 底座：窄而不规则
        [
            [0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 1, 1, 0, 0, 0],
            [0, 0, 1, 1, 1, 1, 0, 0],
            [0, 0, 1, 1, 1, 1, 0, 0],
            [0, 0, 1, 1, 1, 0, 0, 0],
            [0, 0, 0, 1, 1, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0],
        ],
        # Layer 1 — 底座上层：略扩，开始不对称
        [
            [0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 1, 1, 1, 0, 0, 0],
            [0, 0, 1, 1, 1, 1, 0, 0],
            [0, 1, 1, 1, 1, 1, 0, 0],
            [0, 0, 1, 1, 1, 1, 0, 0],
            [0, 0, 0, 1, 1, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0],
        ],
        # Layer 2 — 洞穴底层：中间挖空形成东西贯通通道
        # 通道在 z 相对行 3-4（即 cz+0 ~ cz+1），x 列 2-5 全通
        [
            [0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 1, 1, 1, 1, 0, 0],
            [0, 1, 1, 1, 1, 1, 1, 0],
            [0, 1, 0, 0, 0, 0, 1, 0],  # ← 洞穴通道
            [0, 1, 0, 0, 0, 0, 1, 0],  # ← 洞穴通道
            [0, 0, 1, 1, 1, 1, 0, 0],
            [0, 0, 0, 1, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0],
        ],
        # Layer 3 — 洞穴中层：通道继续，两侧石壁更厚
        [
            [0, 0, 0, 1, 0, 0, 0, 0],
            [0, 0, 1, 1, 1, 1, 0, 0],
            [0, 1, 1, 1, 1, 1, 1, 0],
            [0, 1, 0, 0, 0, 0, 1, 1],  # ← 洞穴通道，东侧凸出
            [0, 1, 0, 0, 0, 0, 1, 0],  # ← 洞穴通道
            [0, 1, 1, 1, 1, 1, 0, 0],
            [0, 0, 1, 1, 1, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0],
        ],
        # Layer 4 — 洞穴顶层：通道最后一层，开始合拢
        [
            [0, 0, 0, 1, 1, 0, 0, 0],
            [0, 1, 1, 1, 1, 1, 0, 0],
            [0, 1, 1, 1, 1, 1, 1, 0],
            [0, 1, 0, 0, 0, 1, 1, 1],  # ← 通道仅剩 3 格宽（更透的感觉）
            [0, 1, 1, 0, 0, 1, 1, 0],  # ← 部分合拢
            [0, 1, 1, 1, 1, 1, 0, 0],
            [0, 0, 1, 1, 1, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0],
        ],
        # Layer 5 — 上部扩宽开始（"瘦"= 上大下小的关键层）
        [
            [0, 0, 1, 1, 1, 0, 0, 0],
            [0, 1, 1, 1, 1, 1, 1, 0],
            [1, 1, 1, 1, 1, 1, 1, 0],
            [0, 1, 1, 1, 1, 1, 1, 1],
            [1, 1, 1, 1, 1, 1, 1, 0],
            [0, 1, 1, 1, 1, 1, 1, 0],
            [0, 0, 1, 1, 1, 1, 0, 0],
            [0, 0, 0, 1, 0, 0, 0, 0],
        ],
        # Layer 6 — 最宽层：大幅外扩，飘逸感
        [
            [0, 0, 1, 1, 1, 1, 0, 0],
            [0, 1, 1, 1, 1, 1, 1, 0],
            [1, 1, 1, 0, 1, 1, 1, 1],  # ← 中间挖一个小透孔（"透"）
            [1, 1, 1, 1, 0, 1, 1, 1],  # ← 另一个透孔
            [1, 1, 1, 1, 1, 1, 1, 1],
            [0, 1, 1, 1, 1, 1, 1, 0],
            [0, 1, 1, 1, 1, 1, 0, 0],
            [0, 0, 0, 1, 1, 0, 0, 0],
        ],
        # Layer 7 — 收窄但仍比底座宽，不规则边缘
        [
            [0, 0, 0, 1, 1, 0, 0, 0],
            [0, 0, 1, 1, 1, 1, 0, 0],
            [0, 1, 1, 0, 1, 1, 1, 0],  # ← 皱纹：小凹陷
            [0, 1, 1, 1, 1, 1, 1, 0],
            [0, 1, 1, 1, 1, 0, 1, 0],  # ← 皱纹：另一个凹陷
            [0, 0, 1, 1, 1, 1, 0, 0],
            [0, 0, 1, 1, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0],
        ],
        # Layer 8 — 顶冠：窄而尖，不对称
        [
            [0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 1, 1, 0, 0, 0],
            [0, 0, 1, 1, 1, 0, 0, 0],
            [0, 0, 1, 1, 1, 1, 0, 0],
            [0, 0, 0, 1, 1, 0, 0, 0],
            [0, 0, 0, 1, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0],
        ],
        # Layer 9 — 尖顶：最终两三个方块
        [
            [0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 1, 0, 0, 0, 0],
            [0, 0, 0, 1, 1, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0],
        ],
    ]

    # 放置主石
    ox = cx - 3   # pattern 原点 x
    oz = cz - 3   # pattern 原点 z

    for dy, layer in enumerate(layers):
        y = ground_y + dy
        for dz_idx, row in enumerate(layer):
            for dx_idx, val in enumerate(row):
                if val == 1:
                    bx = ox + dx_idx
                    bz = oz + dz_idx
                    # 决定材质：约 30% calcite，其余 dripstone
                    if random.random() < 0.30:
                        block = WHITE
                    else:
                        block = MAIN
                    b.setblock(bx, y, bz, block)

    # ── 苔藓覆盖：底座周围和底部两层外表面 ──
    _add_moss_base(b, cx, ground_y, cz, ox, oz, layers, MOSS, MCARPET)

    # ── 洞穴内部地面：铺苔藓 ──
    # 洞穴在 layer 2-4，通道位置是 z 行 3-4，x 列 2-5
    for dz_offset in [0, 1]:  # cz+0, cz+1
        for dx_offset in range(-1, 3):  # cx-1 到 cx+2
            bx = cx + dx_offset
            bz = cz + dz_offset
            b.setblock(bx, ground_y + 2, bz, MOSS)  # 洞穴地面铺苔藓

    # ── 副石 A：主石西南方，较小 ──
    _build_sub_rock_a(b, cx - 5, ground_y, cz + 3, MAIN, WHITE, MOSS, MCARPET)

    # ── 副石 B：主石东北方，最小 ──
    _build_sub_rock_b(b, cx + 4, ground_y, cz - 3, MAIN, WHITE, MOSS, MCARPET)


def _add_moss_base(b, cx, ground_y, cz, ox, oz, layers, MOSS, MCARPET):
    """在主石底座周围铺苔藓块和苔藓毯，增加自然感"""
    random.seed(43)  # 不同的种子避免和主体混淆

    # 收集底层（layer 0）有方块的位置
    bottom_positions = set()
    for dz_idx, row in enumerate(layers[0]):
        for dx_idx, val in enumerate(row):
            if val == 1:
                bottom_positions.add((ox + dx_idx, oz + dz_idx))

    # 在底层方块周围一圈铺苔藓
    for (bx, bz) in list(bottom_positions):
        for ddx in [-1, 0, 1]:
            for ddz in [-1, 0, 1]:
                nx, nz = bx + ddx, bz + ddz
                if (nx, nz) not in bottom_positions:
                    if random.random() < 0.6:
                        b.setblock(nx, ground_y, nz, MOSS)
                        # 苔藓块上面有概率放苔藓毯
                        if random.random() < 0.4:
                            b.setblock(nx, ground_y + 1, nz, MCARPET)

    # 底座方块本身，最底层部分替换为苔藓（根部长苔的感觉）
    for (bx, bz) in bottom_positions:
        if random.random() < 0.35:
            b.setblock(bx, ground_y, bz, MOSS)


def _build_sub_rock_a(b, sx, ground_y, sz, MAIN, WHITE, MOSS, MCARPET):
    """副石 A：高约 4 格，有一个小透孔"""
    print(f"  副石A at ({sx}, {ground_y}, {sz})")
    random.seed(44)

    sub_layers = [
        # Layer 0 — 底座
        [
            [0, 0, 0, 0],
            [0, 1, 1, 0],
            [0, 1, 1, 0],
            [0, 0, 0, 0],
        ],
        # Layer 1
        [
            [0, 1, 0, 0],
            [1, 1, 1, 0],
            [0, 1, 1, 0],
            [0, 0, 0, 0],
        ],
        # Layer 2 — 有透孔
        [
            [0, 1, 1, 0],
            [1, 0, 1, 0],  # ← 透孔
            [1, 1, 1, 1],
            [0, 0, 1, 0],
        ],
        # Layer 3 — 顶部扩宽（上大下小）
        [
            [0, 1, 1, 0],
            [1, 1, 1, 1],
            [0, 1, 1, 0],
            [0, 0, 0, 0],
        ],
        # Layer 4 — 尖顶
        [
            [0, 0, 0, 0],
            [0, 1, 0, 0],
            [0, 1, 0, 0],
            [0, 0, 0, 0],
        ],
    ]

    for dy, layer in enumerate(sub_layers):
        y = ground_y + dy
        for dz_idx, row in enumerate(layer):
            for dx_idx, val in enumerate(row):
                if val == 1:
                    bx = sx + dx_idx
                    bz = sz + dz_idx
                    block = WHITE if random.random() < 0.30 else MAIN
                    b.setblock(bx, y, bz, block)

    # 底座苔藓
    for dx in range(-1, 5):
        for dz in range(-1, 5):
            if random.random() < 0.3:
                bx, bz = sx + dx, sz + dz
                b.setblock(bx, ground_y, bz, MOSS)
                if random.random() < 0.3:
                    b.setblock(bx, ground_y + 1, bz, MCARPET)


def _build_sub_rock_b(b, sx, ground_y, sz, MAIN, WHITE, MOSS, MCARPET):
    """副石 B：最小，高约 3 格，像一颗倒放的鹅卵石"""
    print(f"  副石B at ({sx}, {ground_y}, {sz})")
    random.seed(45)

    sub_layers = [
        # Layer 0 — 窄底
        [
            [0, 0, 0],
            [0, 1, 0],
            [0, 1, 0],
        ],
        # Layer 1 — 扩宽
        [
            [0, 1, 0],
            [1, 1, 1],
            [0, 1, 0],
        ],
        # Layer 2 — 最宽（上大下小！）
        [
            [1, 1, 0],
            [1, 1, 1],
            [0, 1, 1],
        ],
        # Layer 3 — 顶
        [
            [0, 0, 0],
            [0, 1, 0],
            [0, 0, 0],
        ],
    ]

    for dy, layer in enumerate(sub_layers):
        y = ground_y + dy
        for dz_idx, row in enumerate(layer):
            for dx_idx, val in enumerate(row):
                if val == 1:
                    bx = sx + dx_idx
                    bz = sz + dz_idx
                    block = WHITE if random.random() < 0.25 else MAIN
                    b.setblock(bx, y, bz, block)

    # 小片苔藓
    for dx in range(-1, 4):
        for dz in range(-1, 4):
            if random.random() < 0.2:
                b.setblock(sx + dx, ground_y, sz + dz, MOSS)


# ══════════════════════════════════════════════════════════════
#  秋千
# ══════════════════════════════════════════════════════════════

def _build_swing(b: MinecraftBuilder, cx: int, ground_y: int, cz: int):
    """
    建造秋千一架

    结构：两根金合欢原木柱（间距3格）+ 深色橡木横梁 + 铁栏杆链条 + 橡木半砖座板

    Parameters:
        cx, cz  : 秋千中心 XZ 坐标（两柱之间的中点偏左柱）
        ground_y: 当地地面 Y 坐标
    """
    print(f"  秋千 at ({cx}, {ground_y}, {cz})")

    PILLAR = PALETTE["pillar"]   # stripped_acacia_log
    BEAM   = PALETTE["beam"]     # dark_oak_planks
    BARS   = PALETTE["window"]   # iron_bars

    # 两根柱子的 X 坐标
    x_left  = cx
    x_right = cx + 3

    pillar_h = 5   # 柱高 5 格
    top_y = ground_y + pillar_h  # 横梁 Y

    # ── 左柱 ──
    for dy in range(1, pillar_h + 1):
        b.setblock(x_left, ground_y + dy, cz, PILLAR)

    # ── 右柱 ──
    for dy in range(1, pillar_h + 1):
        b.setblock(x_right, ground_y + dy, cz, PILLAR)

    # ── 顶部横梁：连接两柱 ──
    for x in range(x_left, x_right + 1):
        b.setblock(x, top_y, cz, BEAM)

    # ── 链条（铁栏杆）：从横梁下方垂下 ──
    # 两条链各在距中心 1 格处
    chain_x1 = cx + 1
    chain_x2 = cx + 2
    chain_len = 3  # 链条长 3 格

    for dy in range(1, chain_len + 1):
        b.setblock(chain_x1, top_y - dy, cz, BARS)
        b.setblock(chain_x2, top_y - dy, cz, BARS)

    # ── 座板：橡木半砖，在链条底端下方一格 ──
    seat_y = top_y - chain_len - 1
    b.setblock(chain_x1, seat_y, cz, "minecraft:oak_slab")
    b.setblock(chain_x2, seat_y, cz, "minecraft:oak_slab")

    # ── 地面装饰：柱脚周围铺碎石 ──
    for bx in [x_left, x_right]:
        for ddx in [-1, 0, 1]:
            for ddz in [-1, 0, 1]:
                if ddx == 0 and ddz == 0:
                    continue
                if random.random() < 0.4:
                    b.setblock(bx + ddx, ground_y, cz + ddz, PALETTE["gravel"])


# ══════════════════════════════════════════════════════════════
#  主入口
# ══════════════════════════════════════════════════════════════

def build_rocks_and_swing(b: MinecraftBuilder):
    print("=== 太湖石 + 秋千 ===")
    _build_taihu_rocks(b, cx=31, ground_y=-56, cz=9)
    _build_swing(b, cx=42, ground_y=-59, cz=15)
    b.register_bbox("taihu_rocks", 26, -56, 5, 36, -47, 14)
    b.register_bbox("swing", 40, -59, 14, 45, -53, 16)


if __name__ == "__main__":
    with MinecraftBuilder() as b:
        build_rocks_and_swing(b)
        print(f"Done! {b.cmd_count} commands")
