"""修复两个问题: 大梅树加高 + 东侧补树

任务 1: 大梅树从 12 格加高到 ~20 格
  - 不重建整棵树，只在现有树顶上增高
  - 延伸树干 8 格 (dy 12..19)
  - 在新高度增加大型顶层树冠，半径 5-6

任务 2: 东侧 (X:70-90) 补 5 棵树
  - (90, 20): 中型橡树 h=8, 2x2 trunk
  - (70, 55): 垂杨 h=8, vine 垂 4-5 格
  - (78, 22): 芍药阑旁小花树 h=5, cherry_leaves
  - (43, 33): 廊桥北端桥头柳 h=7
  - (47, 57): 廊桥南端桥头柳 h=6

效率: fill 做树冠主层 + setblock 做缺口/细节，总计 < 1500 命令
"""

import sys
sys.path.insert(0, '/Users/lambertlin/minecraft-server/scripts')

from builder import MinecraftBuilder
from blocks import PALETTE, GROUND_Y, BUILD_Y
from config import PLUM_TREE, PEONY_RAIL, BRIDGE
import random


# ══════════════════════════════════════════════════════════════
#  工具函数
# ══════════════════════════════════════════════════════════════

def _vine_facing(vx, vz, trunk_cx, trunk_cz):
    """根据叶块位置相对树干中心，返回 vine 方块字符串"""
    dx = vx - trunk_cx
    dz = vz - trunk_cz
    faces = []
    if dx > 0:
        faces.append("east=true")
    elif dx < 0:
        faces.append("west=true")
    if dz > 0:
        faces.append("south=true")
    elif dz < 0:
        faces.append("north=true")
    if not faces:
        faces.append("south=true")
    return f"minecraft:vine[{','.join(faces)}]"


def _crown_layer_fill_then_carve(b, cx, y, cz, rx, rz, block, seed_offset=0):
    """高效树冠层: fill 一个矩形，再 setblock 去除圆外和随机缺口。

    比逐格 setblock 更省命令:
      - 1 条 fill 覆盖矩形
      - ~20% 的格子用 setblock air 去除 (圆外 + 缺口)
    """
    random.seed(seed_offset + y * 1000 + cx * 100 + cz)

    # fill 矩形
    b.fill(cx - rx, y, cz - rz, cx + rx, y, cz + rz, block)

    # 移除圆外的方块 + 随机缺口
    for dx in range(-rx, rx + 1):
        for dz in range(-rz, rz + 1):
            if rx == 0 or rz == 0:
                continue
            dist_sq = (dx / rx) ** 2 + (dz / rz) ** 2
            remove = False

            # 椭圆外部: 必须移除
            if dist_sq > 1.0:
                remove = True
            # 边缘 20% 缺口: 自然不规则
            elif dist_sq > 0.6 and random.random() < 0.22:
                remove = True
            # 内部偶尔透光
            elif dist_sq > 0.3 and random.random() < 0.05:
                remove = True

            if remove:
                b.setblock(cx + dx, y, cz + dz, "minecraft:air")


def _build_2x2_trunk(b, cx, cz, base_y, height, log_block, thicken_bottom=3):
    """2x2 底座树干，底部加粗。返回实际放置的最高 y。"""
    random.seed(cx * 100 + cz * 10 + height)
    for dy in range(height):
        y = base_y + dy
        # 核心 2x2
        for dx in range(2):
            for dz in range(2):
                b.setblock(cx + dx, y, cz + dz, log_block)

        # 底部加粗
        if dy < thicken_bottom:
            extras = [(-1, 0), (2, 0), (0, -1), (1, 2), (-1, 1), (2, 1)]
            for edx, edz in extras:
                if random.random() < 0.35 - dy * 0.08:
                    b.setblock(cx + edx, y, cz + edz, log_block)

        # 中段偶尔凸起
        if thicken_bottom <= dy <= height - 3:
            bumps = [(-1, 0), (2, 1), (1, 2), (0, -1)]
            for bdx, bdz in bumps:
                if random.random() < 0.15:
                    b.setblock(cx + bdx, y, cz + bdz, log_block)

    return base_y + height - 1


def _exposed_roots(b, cx, cz, ground_y, log_block):
    """树干基部外露根系"""
    random.seed(cx * 31 + cz * 17)
    root_dirs = [(-2, -1), (2, -1), (-1, 2), (3, 0), (0, -2), (2, 2)]
    for rdx, rdz in root_dirs:
        if random.random() < 0.6:
            rx, rz = cx + rdx, cz + rdz
            axis = "x" if abs(rdx) >= abs(rdz) else "z"
            b.setblock(rx, ground_y, rz, f"{log_block}[axis={axis}]")
            # 根旁粗泥
            if random.random() < 0.4:
                dirt = random.choice(["minecraft:coarse_dirt", "minecraft:podzol"])
                b.setblock(rx + random.choice([-1, 0, 1]), ground_y,
                           rz + random.choice([-1, 0, 1]), dirt)


# ══════════════════════════════════════════════════════════════
#  任务 1: 大梅树加高 — 从 12 格增至 ~20 格
# ══════════════════════════════════════════════════════════════

def extend_plum_tree(b):
    """在现有大梅树顶部增高 8 格树干 + 新顶层树冠。

    现有状态 (fix_trees.py):
      - 树干: BUILD_Y+0 .. BUILD_Y+11 (12 格), 2x2 核心
      - 树冠: BUILD_Y+8 .. BUILD_Y+15 (8 层)
      - 分枝: BUILD_Y+7..10 区域

    增加:
      - 树干延伸: BUILD_Y+12 .. BUILD_Y+19 (8 格), 逐渐变细
      - 顶部分枝: BUILD_Y+16..18 向外延伸
      - 新顶层树冠: BUILD_Y+16 .. BUILD_Y+22, 半径 5-6
      - 总高 ~22 格 (BUILD_Y+0 到 BUILD_Y+21)
    """
    print("  [1] 大梅树加高...")
    px, pz = PLUM_TREE["x"], PLUM_TREE["z"]
    random.seed(142)

    # ── 树干延伸: BUILD_Y+12 到 BUILD_Y+19 ──
    # 从 2x2 逐渐缩到 1x2 再到 1x1
    for dy in range(12, 20):
        y = BUILD_Y + dy

        if dy < 16:
            # 仍然 2x2，但偶尔缺角
            for dx in range(2):
                for dz in range(2):
                    if dy >= 14 and dx == 1 and dz == 1 and random.random() < 0.4:
                        continue  # 高处开始不规则
                    b.setblock(px + dx, y, pz + dz, PALETTE["cherry_log"])
        elif dy < 18:
            # 缩到 1x2 或 2x1
            b.setblock(px, y, pz, PALETTE["cherry_log"])
            b.setblock(px + 1, y, pz, PALETTE["cherry_log"])
            if random.random() < 0.5:
                b.setblock(px, y, pz + 1, PALETTE["cherry_log"])
        else:
            # 顶端 1x1
            b.setblock(px, y, pz, PALETTE["cherry_log"])

    # ── 顶部分枝: BUILD_Y+16..18 ──
    top_branches = [
        (16, -1, -1, 3),   # 西北
        (17,  2,  0, 3),   # 东
        (16,  0,  2, 3),   # 南
        (18, -1,  1, 2),   # 西南
    ]
    for br_y_off, br_dx, br_dz, br_len in top_branches:
        for step in range(1, br_len + 1):
            bx = px + br_dx * step
            bz = pz + br_dz * step
            by = BUILD_Y + br_y_off + step // 2
            axis = "x" if abs(br_dx) >= abs(br_dz) else "z"
            b.setblock(bx, by, bz, f"minecraft:cherry_log[axis={axis}]")

    # ── 新顶层树冠: BUILD_Y+16 到 BUILD_Y+22 ──
    # 与现有树冠 (BUILD_Y+8..15) 的顶部有 1 格重叠，视觉连续
    crown_layers = [
        # (y_offset, x_radius, z_radius)
        (15, 4, 3),    # 过渡层，与旧冠顶部融合
        (16, 5, 5),    # 新冠底部
        (17, 6, 6),    # 最宽
        (18, 6, 5),    # 仍然宽
        (19, 5, 5),    # 开始收
        (20, 4, 4),    # 收窄
        (21, 3, 3),    # 更窄
        (22, 1, 1),    # 顶点
    ]

    crown_cx = px  # 整数中心，偏树干西北角
    crown_cz = pz

    for dy_off, rx, rz in crown_layers:
        y = BUILD_Y + dy_off
        _crown_layer_fill_then_carve(b, crown_cx, y, crown_cz, rx, rz,
                                     PALETTE["cherry_leaves"],
                                     seed_offset=142)

    # ── 新冠下缘垂花: 底部边缘挂几条 vine ──
    vine_y = BUILD_Y + 15
    vine_candidates = []
    r = 5
    for dx in range(-r, r + 1):
        for dz in range(-r, r + 1):
            dist_sq = dx * dx + dz * dz
            if (r - 2) ** 2 < dist_sq <= r * r:
                vine_candidates.append((crown_cx + dx, vine_y, crown_cz + dz))

    random.shuffle(vine_candidates)
    for vx, vy, vz in vine_candidates[:8]:
        facing = _vine_facing(vx, vz, px + 0.5, pz + 0.5)
        vine_len = random.randint(2, 4)
        for vdy in range(vine_len):
            target_y = vy - 1 - vdy
            if target_y <= BUILD_Y + 8:  # 不侵入现有低层冠
                break
            b.setblock(vx, target_y, vz, facing)

    print(f"    大梅树加高完成: 总高 ~22 格 (BUILD_Y+0..+22)")
    print(f"    新树干: dy 12..19, 新冠: dy 15..22, 冠幅 ~12 格")


# ══════════════════════════════════════════════════════════════
#  任务 2: 东侧补树
# ══════════════════════════════════════════════════════════════

# ── 2a: 中型橡树 (90, 20), 高 8 格 ──

def build_east_oak(b):
    """中型橡树: 2x2 树干，高 8，oak_leaves 冠幅半径 4"""
    print("  [2a] 中型橡树 @ (92, 20)...")
    tx, tz = 92, 20  # 从90改为92，避免树冠X=86侵入牡丹亭台基
    base_y = BUILD_Y
    trunk_h = 8
    random.seed(201)

    # 根部
    _exposed_roots(b, tx, tz, GROUND_Y, "minecraft:oak_log")

    # 树干 2x2
    _build_2x2_trunk(b, tx, tz, base_y, trunk_h, PALETTE["oak_log"],
                     thicken_bottom=3)

    # 树冠: 用 fill + carve，5 层
    crown_layers = [
        (6,  3, 3),    # 底层
        (7,  4, 4),    # 次宽
        (8,  4, 4),    # 最宽
        (9,  3, 3),    # 收
        (10, 2, 2),    # 顶
    ]
    for dy_off, rx, rz in crown_layers:
        y = base_y + dy_off
        _crown_layer_fill_then_carve(b, tx, y, tz, rx, rz,
                                     PALETTE["oak_leaves"],
                                     seed_offset=201)

    print(f"    橡树完成: 高{trunk_h}格, 冠径~8格")


# ── 2b: 池塘东南岸垂杨 (70, 55), 高 8 格 ──

def build_east_willow(b):
    """垂杨: 2x2 树干高 8, oak_leaves 扁冠, vine 垂 4-5 格"""
    print("  [2b] 垂杨 @ (70, 55)...")
    tx, tz = 70, 55
    base_y = BUILD_Y
    trunk_h = 8
    random.seed(202)

    # 根部
    _exposed_roots(b, tx, tz, GROUND_Y, "minecraft:oak_log")

    # 树干 2x2
    _build_2x2_trunk(b, tx, tz, base_y, trunk_h, PALETTE["oak_log"],
                     thicken_bottom=2)

    # 树冠: 垂柳特征——扁平宽大
    crown_top = base_y + trunk_h
    crown_layers = [
        (-1, 4, 4),    # 下延
        (0,  5, 5),    # 最宽
        (1,  5, 4),    # 仍宽
        (2,  3, 3),    # 顶部收
    ]

    vine_candidates = []
    for dy_off, rx, rz in crown_layers:
        y = crown_top + dy_off
        _crown_layer_fill_then_carve(b, tx, y, tz, rx, rz,
                                     PALETTE["oak_leaves"],
                                     seed_offset=202)
        # 底层和主层边缘收集挂藤点
        if dy_off <= 0:
            for dx in range(-rx, rx + 1):
                for dz in range(-rz, rz + 1):
                    dist_sq = (dx / max(rx, 1)) ** 2 + (dz / max(rz, 1)) ** 2
                    if 0.5 < dist_sq <= 1.0:
                        vine_candidates.append((tx + dx, y, tz + dz))

    # vine 垂 4-5 格
    vine_candidates = list(set(vine_candidates))
    random.shuffle(vine_candidates)
    vine_count = min(len(vine_candidates), 20)

    for vx, vy, vz in vine_candidates[:vine_count]:
        facing = _vine_facing(vx, vz, tx + 0.5, tz + 0.5)
        vine_len = random.randint(4, 5)
        for vdy in range(vine_len):
            target_y = vy - 1 - vdy
            if target_y <= GROUND_Y:
                break
            b.setblock(vx, target_y, vz, facing)

    print(f"    垂杨完成: 高{trunk_h}格, 冠径~10格, 藤{vine_count}条")


# ── 2c: 芍药阑旁小花树 (78, 22), 高 5 格 ──

def build_peony_rail_tree(b):
    """小观赏花树: 1x1 树干高 5, cherry_leaves 小冠"""
    print("  [2c] 芍药阑旁花树 @ (78, 22)...")
    tx, tz = 78, 22
    # 芍药阑地面 -58，树基于此
    base_y = PEONY_RAIL["ground_y"] + 1  # -57
    trunk_h = 5
    random.seed(203)

    # 1x1 树干 (小树不需要 2x2)
    for dy in range(trunk_h):
        b.setblock(tx, base_y + dy, tz, PALETTE["cherry_log"])
        # 底部 2 格偶尔加一块
        if dy < 2:
            if random.random() < 0.4:
                b.setblock(tx + random.choice([-1, 1]), base_y + dy, tz,
                           PALETTE["cherry_log"])

    # 小树冠: 半径 2-3，cherry_leaves
    crown_layers = [
        (3,  2, 2),    # 底
        (4,  3, 3),    # 最宽
        (5,  3, 2),    # 宽
        (6,  2, 2),    # 收
        (7,  1, 1),    # 顶
    ]
    for dy_off, rx, rz in crown_layers:
        y = base_y + dy_off
        _crown_layer_fill_then_carve(b, tx, y, tz, rx, rz,
                                     PALETTE["cherry_leaves"],
                                     seed_offset=203)

    # 树下落花
    for dx in range(-3, 4):
        for dz in range(-3, 4):
            if dx == 0 and dz == 0:
                continue
            if dx * dx + dz * dz > 9:
                continue
            if random.random() < 0.25:
                b.setblock(tx + dx, base_y, tz + dz, "minecraft:pink_carpet")

    print(f"    花树完成: 高{trunk_h}格, 冠径~6格")


# ── 2d: 廊桥两端桥头柳 (43, 33) 和 (47, 57) ──

def build_bridge_willows(b):
    """廊桥两端各 1 棵桥头柳，6-7 格高，vine 垂 4 格"""
    print("  [2d] 桥头柳...")
    random.seed(204)

    willows = [
        (43, 31, 7, "北端"),   # 从Z=33改为31，避免树冠侵入廊桥Z=35
        (47, 59, 6, "南端"),   # 从Z=57改为59，避免树冠侵入廊桥Z=55
    ]

    for wx, wz, trunk_h, label in willows:
        base_y = BUILD_Y

        # 根部
        _exposed_roots(b, wx, wz, GROUND_Y, "minecraft:oak_log")

        # 2x2 树干
        _build_2x2_trunk(b, wx, wz, base_y, trunk_h, PALETTE["oak_log"],
                         thicken_bottom=2)

        # 扁平树冠
        crown_top = base_y + trunk_h
        crown_layers = [
            (-1, 3, 3),
            (0,  4, 4),
            (1,  4, 3),
            (2,  2, 2),
        ]

        vine_candidates = []
        for dy_off, rx, rz in crown_layers:
            y = crown_top + dy_off
            _crown_layer_fill_then_carve(b, wx, y, wz, rx, rz,
                                         PALETTE["oak_leaves"],
                                         seed_offset=204 + wx)
            if dy_off <= 0:
                for dx in range(-rx, rx + 1):
                    for dz in range(-rz, rz + 1):
                        dist_sq = (dx / max(rx, 1)) ** 2 + (dz / max(rz, 1)) ** 2
                        if 0.5 < dist_sq <= 1.0:
                            vine_candidates.append((wx + dx, y, wz + dz))

        # vine 垂 4 格
        vine_candidates = list(set(vine_candidates))
        random.shuffle(vine_candidates)
        vine_count = min(len(vine_candidates), 14)

        for vx, vy, vz in vine_candidates[:vine_count]:
            facing = _vine_facing(vx, vz, wx + 0.5, wz + 0.5)
            vine_len = random.randint(3, 4)
            for vdy in range(vine_len):
                target_y = vy - 1 - vdy
                if target_y <= GROUND_Y:
                    break
                b.setblock(vx, target_y, vz, facing)

        print(f"    桥头柳({label}) @ ({wx},{wz}), "
              f"高{trunk_h}格, 藤{vine_count}条")


# ══════════════════════════════════════════════════════════════
#  主函数
# ══════════════════════════════════════════════════════════════

def fix_more_trees(b):
    """一键执行: 大梅树加高 + 东侧补树"""
    print("=== 修复: 大梅树加高 + 东侧补树 ===")
    extend_plum_tree(b)
    build_east_oak(b)
    build_east_willow(b)
    build_peony_rail_tree(b)
    build_bridge_willows(b)
    print("=== 修复完成 ===")


if __name__ == "__main__":
    with MinecraftBuilder() as b:
        fix_more_trees(b)
        print(f"Done! {b.cmd_count} commands")
