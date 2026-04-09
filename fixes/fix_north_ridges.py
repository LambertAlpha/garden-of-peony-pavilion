"""修复北面远山：山脊连接三峰 + 围墙到山脚过渡带

问题诊断:
1. 三峰孤立 — 副峰1(20,-30)、主峰(50,-40)、副峰2(90,-35) 之间无连接，
   远看像三个土堆而非连绵山脉
2. 围墙(Z=0)到最近山脚(Z≈-20)之间 20 格裸地，没有任何过渡

修复:
- 任务1: 两条低矮山脊(高8-12)连接三峰，中间高两头低
- 任务2: 四层过渡带从围墙延伸到山脚

效率目标: <500 命令
"""

import sys
import math
import random

sys.path.insert(0, '/Users/lambertlin/minecraft-server/scripts')
from builder import MinecraftBuilder
from blocks import GROUND_Y


# ── 三峰坐标 ──

PEAK_MAIN = (50, -40)   # 主峰, 高35, 半径 18x13
PEAK_W    = (20, -30)   # 副峰1(西), 高20, 半径 12x10
PEAK_E    = (90, -35)   # 副峰2(东), 高25, 半径 15x11

BASE_Y = GROUND_Y  # -61

# X 全宽范围
X_MIN, X_MAX = -10, 130


# ═══════════════════════════════════════════════
#  任务 1: 山脊连接三峰
# ═══════════════════════════════════════════════

def _build_ridge(b: MinecraftBuilder,
                 x1: int, z1: int, x2: int, z2: int,
                 base_y: int, max_height: int, width: int,
                 name: str):
    """沿两点连线建山脊，截面垂直于连线方向扩展

    高度轮廓: 抛物线形，中间高两头低 h = max_height * (1 - (2t-1)^2)
    每步一个截面用 fill 填充（石头内核 + 草顶盖）
    """
    print(f"  山脊 {name}: ({x1},{z1}) → ({x2},{z2}), 最高{max_height}")
    cmd_before = b.cmd_count

    dx = x2 - x1
    dz = z2 - z1
    dist = math.sqrt(dx * dx + dz * dz)
    steps = int(dist)

    if steps == 0:
        return

    # 连线方向的法向量（用于截面宽度方向）
    nx = -dz / dist  # 法向 X 分量
    nz = dx / dist   # 法向 Z 分量

    for i in range(steps + 1):
        t = i / steps
        # 当前截面中心
        cx = int(x1 + dx * t)
        cz = int(z1 + dz * t)

        # 抛物线高度：中间高两头低
        h = int(max_height * (1.0 - (2 * t - 1) ** 2))
        h = max(2, h)

        # 宽度也中间宽两头窄（更自然）
        w = int(width * (0.5 + 0.5 * (1.0 - (2 * t - 1) ** 2)))
        w = max(2, w)
        hw = w // 2

        # 沿法向量展开截面，计算包围盒
        # 截面端点
        px1 = int(cx - nx * hw)
        pz1 = int(cz - nz * hw)
        px2 = int(cx + nx * hw)
        pz2 = int(cz + nz * hw)

        # fill 需要对齐到轴，取包围盒
        fill_x1 = min(px1, px2)
        fill_x2 = max(px1, px2)
        fill_z1 = min(pz1, pz2)
        fill_z2 = max(pz1, pz2)

        # 确保至少 1 格宽
        if fill_x1 == fill_x2:
            fill_x2 += 1
        if fill_z1 == fill_z2:
            fill_z2 += 1

        # 石头内核（从地面到 h-1）
        b.fill(fill_x1, base_y, fill_z1,
               fill_x2, base_y + h - 1, fill_z2,
               "minecraft:stone")

        # 安山岩点缀（中间几层）
        if h > 4 and i % 3 == 0:
            mid_y = base_y + h // 2
            b.fill(fill_x1, mid_y, fill_z1,
                   fill_x2, mid_y, fill_z2,
                   "minecraft:andesite")

        # 草顶盖
        b.fill(fill_x1, base_y + h, fill_z1,
               fill_x2, base_y + h, fill_z2,
               "minecraft:grass_block")

    cmd_used = b.cmd_count - cmd_before
    print(f"    完成: {cmd_used} 命令")


def build_ridges(b: MinecraftBuilder):
    """建造两条山脊连接三峰"""
    print("\n[任务1] 山脊连接三峰")

    # 山脊A: 副峰1 → 主峰
    _build_ridge(b,
                 x1=PEAK_W[0], z1=PEAK_W[1],
                 x2=PEAK_MAIN[0], z2=PEAK_MAIN[1],
                 base_y=BASE_Y, max_height=10, width=6,
                 name="A(西→主)")

    # 山脊B: 主峰 → 副峰2
    _build_ridge(b,
                 x1=PEAK_MAIN[0], z1=PEAK_MAIN[1],
                 x2=PEAK_E[0], z2=PEAK_E[1],
                 base_y=BASE_Y, max_height=12, width=7,
                 name="B(主→东)")


# ═══════════════════════════════════════════════
#  任务 2: 围墙到山脚过渡带
# ═══════════════════════════════════════════════

def build_foothill_transition(b: MinecraftBuilder):
    """四层过渡带: Z=0(围墙) → Z=-20(山脚)

    Z=0  ~ Z=-3   碎石小径 (andesite)
    Z=-3 ~ Z=-8   野草地 (grass_block + tall_grass)
    Z=-8 ~ Z=-14  灌木丛 (azalea_leaves + oak_leaves 低堆)
    Z=-14~ Z=-20  山脚碎石坡 (cobblestone + mossy_cobblestone)
    """
    print("\n[任务2] 围墙到山脚过渡带")
    cmd_before = b.cmd_count

    # ── 层1: 碎石小径 Z=0 到 Z=-3 ──
    print("  层1: 碎石小径 (Z=0 ~ Z=-3)")
    # 主体 andesite 地面
    b.fill(X_MIN, BASE_Y, -3, X_MAX, BASE_Y, -1, "minecraft:andesite")
    # 注意: Z=0 是围墙位置，不能覆盖

    # ── 层2: 野草地 Z=-3 到 Z=-8 ──
    print("  层2: 野草地 (Z=-3 ~ Z=-8)")
    # 确保地面是 grass_block
    b.fill(X_MIN, BASE_Y, -8, X_MAX, BASE_Y, -4, "minecraft:grass_block")
    # tall_grass 稀疏散布 — 分几条带放置，每条一个 fill
    # tall_grass 的下半部分 (minecraft:tall_grass)
    # 条带1: 偏西
    b.fill(-5, BASE_Y + 1, -7, 40, BASE_Y + 1, -7, "minecraft:tall_grass")
    # 条带2: 中部
    b.fill(45, BASE_Y + 1, -5, 95, BASE_Y + 1, -5, "minecraft:tall_grass")
    # 条带3: 偏东
    b.fill(100, BASE_Y + 1, -6, 125, BASE_Y + 1, -6, "minecraft:tall_grass")
    # 短草填充其他行
    b.fill(X_MIN, BASE_Y + 1, -8, X_MAX, BASE_Y + 1, -4,
           "minecraft:short_grass", "replace minecraft:air")

    # ── 层3: 灌木丛 Z=-8 到 Z=-14 ──
    print("  层3: 灌木丛 (Z=-8 ~ Z=-14)")
    # 地面保持 grass
    b.fill(X_MIN, BASE_Y, -14, X_MAX, BASE_Y, -9, "minecraft:grass_block")

    # 灌木堆：低矮的叶子方块堆（高 1-2 格）
    # persistent=true 防止衰变
    azalea_l = "minecraft:azalea_leaves[persistent=true]"
    oak_l = "minecraft:oak_leaves[persistent=true]"

    # 西段灌木
    b.fill(0, BASE_Y + 1, -13, 12, BASE_Y + 2, -11, azalea_l)
    b.fill(15, BASE_Y + 1, -12, 25, BASE_Y + 1, -10, oak_l)

    # 中段灌木
    b.fill(35, BASE_Y + 1, -13, 48, BASE_Y + 2, -11, oak_l)
    b.fill(52, BASE_Y + 1, -12, 60, BASE_Y + 1, -10, azalea_l)

    # 东段灌木
    b.fill(70, BASE_Y + 1, -13, 82, BASE_Y + 2, -11, azalea_l)
    b.fill(85, BASE_Y + 1, -12, 100, BASE_Y + 1, -10, oak_l)
    b.fill(105, BASE_Y + 1, -13, 120, BASE_Y + 2, -11, azalea_l)

    # 灌木间隙种点花（flowering_azalea 整株）
    b.fill(28, BASE_Y + 1, -11, 33, BASE_Y + 1, -11, "minecraft:flowering_azalea")
    b.fill(62, BASE_Y + 1, -11, 68, BASE_Y + 1, -11, "minecraft:flowering_azalea")

    # ── 层4: 山脚碎石坡 Z=-14 到 Z=-20 ──
    print("  层4: 山脚碎石坡 (Z=-14 ~ Z=-20)")
    # cobblestone 主体
    b.fill(X_MIN, BASE_Y, -20, X_MAX, BASE_Y, -15, "minecraft:cobblestone")
    # 混入 mossy_cobblestone（分条带替换）
    b.fill(X_MIN, BASE_Y, -19, X_MAX, BASE_Y, -19,
           "minecraft:mossy_cobblestone", "replace minecraft:cobblestone")
    b.fill(X_MIN, BASE_Y, -17, X_MAX, BASE_Y, -17,
           "minecraft:mossy_cobblestone", "replace minecraft:cobblestone")
    b.fill(X_MIN, BASE_Y, -15, X_MAX, BASE_Y, -15,
           "minecraft:mossy_cobblestone", "replace minecraft:cobblestone")
    # 顶上散落碎石（高 1 格，稀疏）
    b.fill(5, BASE_Y + 1, -19, 30, BASE_Y + 1, -18, "minecraft:cobblestone")
    b.fill(55, BASE_Y + 1, -18, 80, BASE_Y + 1, -17, "minecraft:cobblestone")
    b.fill(95, BASE_Y + 1, -20, 120, BASE_Y + 1, -19, "minecraft:mossy_cobblestone")

    cmd_used = b.cmd_count - cmd_before
    print(f"  过渡带完成: {cmd_used} 命令")


# ═══════════════════════════════════════════════
#  主入口
# ═══════════════════════════════════════════════

if __name__ == "__main__":
    with MinecraftBuilder() as b:
        build_ridges(b)
        build_foothill_transition(b)
        print(f"\nDone! {b.cmd_count} commands")
