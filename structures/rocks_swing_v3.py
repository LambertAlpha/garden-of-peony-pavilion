"""太湖石置石组 + 秋千 — v3 重写

v2→v3 变更:
- 主石增高到10格，强化"瘦皱漏透"四字诀
- 穿行洞穴扩大为 3x2 格通道（东西贯穿），真正可以走人
- 使用 config.py v3 坐标 (TAIHU_ROCKS cx=45,cz=12 / SWING cx=62,cz=25)
- 秋千柱间距改为4格，高度6格，链条改用铁栏杆
- 修复 PALETTE["taihu_moss"] → PALETTE["moss"] 的 key 错误
"""

import sys; sys.path.insert(0, '/Users/lambertlin/minecraft-server/scripts')
from builder import MinecraftBuilder
from blocks import PALETTE, GROUND_Y
from config import TAIHU_ROCKS, SWING
import random


# ══════════════════════════════════════════════════════════════
#  太湖石 — 主石（10层）+ 副石 ×2
# ══════════════════════════════════════════════════════════════

def _build_taihu_main(b: MinecraftBuilder, cx: int, ground_y: int, cz: int):
    """
    主石：高10格，手工逐层 pattern。

    Pattern 尺寸 10×10，原点 (cx-4, cz-4)。
    1 = 石块, 0 = 空气。

    设计意图——
      Layer 0-1 : 窄底座（"瘦"的根基，上大下小）
      Layer 2-4 : 洞穴三层（东西贯穿 3×2 通道，z行4-5, x列2-7全通）
      Layer 5-6 : 上部大幅外扩（"瘦"的反差：头重脚轻）
      Layer 7   : 最宽层，含两处透孔（"透"）
      Layer 8   : 凹凸不规则收窄（"皱"）
      Layer 9   : 尖顶3块
    """
    print(f"  主石 at ({cx}, {ground_y}, {cz})")

    MAIN  = PALETTE["taihu_main"]     # dripstone_block
    WHITE = PALETTE["taihu_white"]    # calcite
    MOSS  = PALETTE["moss"]           # moss_block
    MCARPET = PALETTE["moss_carpet"]

    random.seed(42)

    # 10×10 pattern, 10 layers
    layers = [
        # Layer 0 — 窄底座：不对称
        [
            [0,0,0,0,0,0,0,0,0,0],
            [0,0,0,0,0,0,0,0,0,0],
            [0,0,0,0,1,1,0,0,0,0],
            [0,0,0,1,1,1,1,0,0,0],
            [0,0,0,1,1,1,1,0,0,0],
            [0,0,0,1,1,1,0,0,0,0],
            [0,0,0,0,1,0,0,0,0,0],
            [0,0,0,0,0,0,0,0,0,0],
            [0,0,0,0,0,0,0,0,0,0],
            [0,0,0,0,0,0,0,0,0,0],
        ],
        # Layer 1 — 底座上层：略扩，仍然较窄
        [
            [0,0,0,0,0,0,0,0,0,0],
            [0,0,0,0,1,0,0,0,0,0],
            [0,0,0,1,1,1,1,0,0,0],
            [0,0,1,1,1,1,1,0,0,0],
            [0,0,1,1,1,1,1,1,0,0],
            [0,0,0,1,1,1,1,0,0,0],
            [0,0,0,0,1,1,0,0,0,0],
            [0,0,0,0,0,0,0,0,0,0],
            [0,0,0,0,0,0,0,0,0,0],
            [0,0,0,0,0,0,0,0,0,0],
        ],
        # Layer 2 — 洞穴底层：3格宽东西贯穿通道
        # 通道在 z行4-5 (cz+0 ~ cz+1), x列2-7 全通
        [
            [0,0,0,0,0,0,0,0,0,0],
            [0,0,0,1,1,1,1,0,0,0],
            [0,0,1,1,1,1,1,1,0,0],
            [0,1,1,1,1,1,1,1,1,0],
            [0,1,0,0,0,0,0,0,1,0],  # ← 洞穴通道
            [0,1,0,0,0,0,0,0,1,0],  # ← 洞穴通道
            [0,0,1,1,1,1,1,1,0,0],
            [0,0,0,1,1,1,0,0,0,0],
            [0,0,0,0,0,0,0,0,0,0],
            [0,0,0,0,0,0,0,0,0,0],
        ],
        # Layer 3 — 洞穴中层：通道继续，壁更厚
        [
            [0,0,0,0,1,0,0,0,0,0],
            [0,0,1,1,1,1,1,0,0,0],
            [0,1,1,1,1,1,1,1,0,0],
            [0,1,1,1,1,1,1,1,1,0],
            [0,1,0,0,0,0,0,0,1,0],  # ← 洞穴通道
            [0,1,0,0,0,0,0,0,1,0],  # ← 洞穴通道
            [0,1,1,1,1,1,1,1,0,0],
            [0,0,1,1,1,1,1,0,0,0],
            [0,0,0,0,1,0,0,0,0,0],
            [0,0,0,0,0,0,0,0,0,0],
        ],
        # Layer 4 — 洞穴顶层：通道开始合拢（仅3格宽残留透缝）
        [
            [0,0,0,0,1,1,0,0,0,0],
            [0,0,1,1,1,1,1,1,0,0],
            [0,1,1,1,1,1,1,1,1,0],
            [0,1,1,1,1,1,1,1,1,0],
            [0,1,1,0,0,0,1,1,1,0],  # ← 通道缩窄到3格（"漏"的感觉）
            [0,1,1,0,0,0,1,1,1,0],  # ← 通道缩窄
            [0,1,1,1,1,1,1,1,0,0],
            [0,0,1,1,1,1,1,0,0,0],
            [0,0,0,0,1,0,0,0,0,0],
            [0,0,0,0,0,0,0,0,0,0],
        ],
        # Layer 5 — 上部扩宽（"瘦"= 上大下小的核心层）
        [
            [0,0,0,1,1,1,0,0,0,0],
            [0,0,1,1,1,1,1,1,0,0],
            [0,1,1,1,1,1,1,1,1,0],
            [1,1,1,1,1,1,1,1,1,1],
            [0,1,1,1,1,1,1,1,1,0],
            [1,1,1,1,1,1,1,1,1,0],
            [0,1,1,1,1,1,1,1,1,0],
            [0,0,1,1,1,1,1,1,0,0],
            [0,0,0,1,1,1,0,0,0,0],
            [0,0,0,0,0,0,0,0,0,0],
        ],
        # Layer 6 — 继续宽大，有小透孔
        [
            [0,0,1,1,1,1,1,0,0,0],
            [0,1,1,1,1,1,1,1,0,0],
            [1,1,1,1,1,1,1,1,1,0],
            [1,1,1,1,0,1,1,1,1,1],  # ← 透孔
            [1,1,1,1,1,1,1,1,1,1],
            [1,1,1,0,1,1,0,1,1,1],  # ← 两处透孔（"透"）
            [0,1,1,1,1,1,1,1,1,0],
            [0,1,1,1,1,1,1,1,0,0],
            [0,0,0,1,1,1,1,0,0,0],
            [0,0,0,0,0,0,0,0,0,0],
        ],
        # Layer 7 — 最宽层：飘逸外扩，多处透孔
        [
            [0,0,1,1,1,1,1,0,0,0],
            [0,1,1,1,1,1,1,1,1,0],
            [1,1,1,0,1,1,0,1,1,1],  # ← 皱纹凹陷
            [1,1,1,1,1,1,1,1,1,1],
            [1,1,0,1,1,1,1,0,1,1],  # ← 透孔
            [1,1,1,1,1,1,1,1,1,1],
            [1,1,1,1,0,1,1,1,1,0],  # ← 皱纹
            [0,1,1,1,1,1,1,1,0,0],
            [0,0,1,1,1,1,0,0,0,0],
            [0,0,0,0,0,0,0,0,0,0],
        ],
        # Layer 8 — 收窄但仍比底座宽，凹凸不平（"皱"）
        [
            [0,0,0,1,1,1,0,0,0,0],
            [0,0,1,1,1,1,1,0,0,0],
            [0,1,1,0,1,1,1,1,0,0],  # ← 皱纹凹陷
            [0,1,1,1,1,1,1,0,0,0],
            [0,1,1,1,1,0,1,1,0,0],  # ← 凹陷
            [0,0,1,1,1,1,1,1,0,0],
            [0,0,1,1,1,1,1,0,0,0],
            [0,0,0,1,1,0,0,0,0,0],
            [0,0,0,0,0,0,0,0,0,0],
            [0,0,0,0,0,0,0,0,0,0],
        ],
        # Layer 9 — 尖顶：最终3~4块
        [
            [0,0,0,0,0,0,0,0,0,0],
            [0,0,0,0,1,0,0,0,0,0],
            [0,0,0,1,1,1,0,0,0,0],
            [0,0,0,0,1,0,0,0,0,0],
            [0,0,0,0,0,0,0,0,0,0],
            [0,0,0,0,0,0,0,0,0,0],
            [0,0,0,0,0,0,0,0,0,0],
            [0,0,0,0,0,0,0,0,0,0],
            [0,0,0,0,0,0,0,0,0,0],
            [0,0,0,0,0,0,0,0,0,0],
        ],
    ]

    # 放置主石
    ox = cx - 4  # pattern 原点 x
    oz = cz - 4  # pattern 原点 z

    for dy, layer in enumerate(layers):
        y = ground_y + dy
        for dz_idx, row in enumerate(layer):
            for dx_idx, val in enumerate(row):
                if val == 1:
                    bx = ox + dx_idx
                    bz = oz + dz_idx
                    # 70% dripstone_block + 30% calcite
                    block = WHITE if random.random() < 0.30 else MAIN
                    b.setblock(bx, y, bz, block)

    # ── 底部苔藓覆盖 ──
    _add_moss_base(b, cx, ground_y, cz, ox, oz, layers, MOSS, MCARPET)

    # ── 洞穴内部地面铺苔藓 ──
    # 洞穴 layer 2-4，通道位置: z行4-5, x列2-7
    for dz_off in [0, 1]:
        for dx_off in range(-2, 4):
            bx = cx + dx_off
            bz = cz + dz_off
            b.setblock(bx, ground_y + 2, bz, MOSS)


def _add_moss_base(b, cx, ground_y, cz, ox, oz, layers, MOSS, MCARPET):
    """在主石底座周围铺苔藓，营造自然感"""
    random.seed(43)

    # 收集底层有方块的位置
    bottom = set()
    for dz_idx, row in enumerate(layers[0]):
        for dx_idx, val in enumerate(row):
            if val == 1:
                bottom.add((ox + dx_idx, oz + dz_idx))

    # 底层周围一圈铺苔藓
    for (bx, bz) in list(bottom):
        for ddx in [-1, 0, 1]:
            for ddz in [-1, 0, 1]:
                nx, nz = bx + ddx, bz + ddz
                if (nx, nz) not in bottom and random.random() < 0.6:
                    b.setblock(nx, ground_y, nz, MOSS)
                    if random.random() < 0.4:
                        b.setblock(nx, ground_y + 1, nz, MCARPET)

    # 底座本身部分替换为苔藓
    for (bx, bz) in bottom:
        if random.random() < 0.35:
            b.setblock(bx, ground_y, bz, MOSS)


def _build_sub_rock_a(b: MinecraftBuilder, sx: int, ground_y: int, sz: int):
    """副石 A：主石西南方，高5格，有透孔"""
    print(f"  副石A at ({sx}, {ground_y}, {sz})")

    MAIN  = PALETTE["taihu_main"]
    WHITE = PALETTE["taihu_white"]
    MOSS  = PALETTE["moss"]
    MCARPET = PALETTE["moss_carpet"]
    random.seed(44)

    sub_layers = [
        # Layer 0 — 窄底
        [
            [0,0,0,0,0],
            [0,0,1,1,0],
            [0,1,1,1,0],
            [0,0,1,0,0],
            [0,0,0,0,0],
        ],
        # Layer 1
        [
            [0,0,1,0,0],
            [0,1,1,1,0],
            [0,1,1,1,0],
            [0,0,1,1,0],
            [0,0,0,0,0],
        ],
        # Layer 2 — 扩宽，有透孔
        [
            [0,1,1,0,0],
            [1,1,0,1,0],  # ← 透孔
            [1,1,1,1,1],
            [0,1,1,1,0],
            [0,0,0,0,0],
        ],
        # Layer 3 — 最宽（上大下小）
        [
            [0,1,1,1,0],
            [1,1,1,1,1],
            [0,1,1,1,0],
            [0,0,1,0,0],
            [0,0,0,0,0],
        ],
        # Layer 4 — 尖顶
        [
            [0,0,0,0,0],
            [0,0,1,0,0],
            [0,1,1,0,0],
            [0,0,0,0,0],
            [0,0,0,0,0],
        ],
    ]

    for dy, layer in enumerate(sub_layers):
        y = ground_y + dy
        for dz_idx, row in enumerate(layer):
            for dx_idx, val in enumerate(row):
                if val == 1:
                    block = WHITE if random.random() < 0.30 else MAIN
                    b.setblock(sx + dx_idx, y, sz + dz_idx, block)

    # 底座苔藓
    for dx in range(-1, 6):
        for dz in range(-1, 6):
            if random.random() < 0.3:
                b.setblock(sx + dx, ground_y, sz + dz, MOSS)
                if random.random() < 0.3:
                    b.setblock(sx + dx, ground_y + 1, sz + dz, MCARPET)


def _build_sub_rock_b(b: MinecraftBuilder, sx: int, ground_y: int, sz: int):
    """副石 B：主石东北方，最小，高3格"""
    print(f"  副石B at ({sx}, {ground_y}, {sz})")

    MAIN  = PALETTE["taihu_main"]
    WHITE = PALETTE["taihu_white"]
    MOSS  = PALETTE["moss"]
    random.seed(45)

    sub_layers = [
        # Layer 0 — 窄底
        [
            [0,0,0],
            [0,1,0],
            [0,1,0],
        ],
        # Layer 1 — 扩宽
        [
            [0,1,0],
            [1,1,1],
            [0,1,0],
        ],
        # Layer 2 — 最宽（上大下小！）
        [
            [1,1,0],
            [1,1,1],
            [0,1,1],
        ],
        # Layer 3 — 顶
        [
            [0,0,0],
            [0,1,0],
            [0,0,0],
        ],
    ]

    for dy, layer in enumerate(sub_layers):
        y = ground_y + dy
        for dz_idx, row in enumerate(layer):
            for dx_idx, val in enumerate(row):
                if val == 1:
                    block = WHITE if random.random() < 0.25 else MAIN
                    b.setblock(sx + dx_idx, y, sz + dz_idx, block)

    # 小片苔藓
    for dx in range(-1, 4):
        for dz in range(-1, 4):
            if random.random() < 0.2:
                b.setblock(sx + dx, ground_y, sz + dz, MOSS)


# ══════════════════════════════════════════════════════════════
#  秋千 — 柱间距4格、高6格
# ══════════════════════════════════════════════════════════════

def _build_swing(b: MinecraftBuilder, cx: int, ground_y: int, cz: int):
    """
    秋千：两根绯红木柱（间距4格）、高6格，
    深色橡木横梁 + 铁栏杆链条 + 橡木半砖座板。
    """
    print(f"  秋千 at ({cx}, {ground_y}, {cz})")

    PILLAR = PALETTE["pillar"]   # stripped_crimson_stem
    BEAM   = PALETTE["beam"]     # dark_oak_planks
    BARS   = PALETTE["window"]   # iron_bars

    x_left  = cx
    x_right = cx + 4   # 间距 4 格
    pillar_h = 6
    top_y = ground_y + pillar_h

    # ── 左柱 ──
    for dy in range(1, pillar_h + 1):
        b.setblock(x_left, ground_y + dy, cz, PILLAR)

    # ── 右柱 ──
    for dy in range(1, pillar_h + 1):
        b.setblock(x_right, ground_y + dy, cz, PILLAR)

    # ── 横梁：连接两柱顶 ──
    for x in range(x_left, x_right + 1):
        b.setblock(x, top_y, cz, BEAM)

    # ── 链条（铁栏杆）：从横梁内侧垂下 ──
    chain_x1 = cx + 1
    chain_x2 = cx + 3
    chain_len = 3

    for dy in range(1, chain_len + 1):
        b.setblock(chain_x1, top_y - dy, cz, BARS)
        b.setblock(chain_x2, top_y - dy, cz, BARS)

    # ── 座板：橡木半砖 ──
    seat_y = top_y - chain_len
    for x in range(chain_x1, chain_x2 + 1):
        b.setblock(x, seat_y, cz, "minecraft:oak_slab")

    # ── 柱脚碎石装饰 ──
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
    print("=== 太湖石 + 秋千 (v3) ===")

    # 太湖石
    cfg = TAIHU_ROCKS
    cx, cz, gy = cfg["cx"], cfg["cz"], cfg["ground_y"]
    _build_taihu_main(b, cx, gy, cz)
    _build_sub_rock_a(b, cx - 6, gy, cz + 4)
    _build_sub_rock_b(b, cx + 6, gy, cz - 4)
    b.register_bbox("taihu_rocks", cx - 10, gy, cz - 8, cx + 10, gy + 12, cz + 8)

    # 秋千
    cfg = SWING
    cx, cz, gy = cfg["cx"], cfg["cz"], cfg["ground_y"]
    _build_swing(b, cx, gy, cz)
    b.register_bbox("swing", cx - 1, gy, cz - 1, cx + 5, gy + 7, cz + 1)

    print("=== 太湖石 + 秋千 完成 ===")


if __name__ == "__main__":
    with MinecraftBuilder() as b:
        build_rocks_and_swing(b)
        print(f"Done! {b.cmd_count} commands")
