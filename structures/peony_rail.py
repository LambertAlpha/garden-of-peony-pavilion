"""芍药阑 — 雕花围栏芍药圃

"牡丹亭畔，芍药阑边" — 与牡丹亭不可分割的一对，梦境发生地的另一半。
原文："雕阑芍药芽儿浅""嵌雕阑芍药"。

形制：金合欢栅栏围成矩形花圃，内植芍药，中有石径穿越，
      南北各留入口，四角灯笼点缀，藤蔓攀附做旧。
"""

import sys; sys.path.insert(0, '/Users/lambertlin/minecraft-server/scripts')
from builder import MinecraftBuilder
from blocks import PALETTE
import random


def build_peony_rail(b: MinecraftBuilder, cx: int, ground_y: int, cz: int):
    """
    建造芍药阑（芍药花圃围栏）

    Parameters:
        cx, cz  : 芍药阑中心 XZ 坐标
        ground_y: 地面 Y 坐标
    """
    print(f"=== 芍药阑 at ({cx}, {ground_y}, {cz}) ===")
    random.seed(42)

    # ── 常用方块 ──
    RAIL    = PALETTE["rail"]       # acacia_fence
    DIRT    = PALETTE["dirt"]       # dirt
    PATH    = PALETTE["path"]       # dirt_path
    PEONY   = PALETTE["peony"]      # peony（2格高花）
    LANTERN = PALETTE["lantern"]    # lantern
    VINE    = PALETTE["vine"]       # vine

    # ── 尺寸参数 ──
    # 围栏矩形：X方向9格（cx-4 ~ cx+4），Z方向7格（cz-3 ~ cz+3）
    HX = 4   # X方向半宽
    HZ = 3   # Z方向半宽
    rail_y = ground_y + 1  # 栏杆放在地面上方1格

    # 石径宽度：中间2格（cx, cx+1 → 不对称；改为 cx-1, cx 对称偏左不好）
    # 用 cx 为中心，左右各0.5 → 取 cx 和 cx-1 两格（偶数宽度）
    # 实际取 cx 单格两侧：path_x = [cx, cx+1] 不够对称
    # 最佳方案：cx 为奇数中心，2格宽取 cx-0 和 cx+1 → 偏右
    # 改为取 cx 和 cx-1 → [cx-1, cx] 从北到南
    PATH_XS = [cx, cx + 1]  # 2格宽石径

    # ================================================================
    # 1. 地面基底 — 围栏内铺泥土
    # ================================================================
    print("  [1/7] 地面基底...")

    # 围栏范围内（含栏杆下方）全铺泥土，作为花圃土壤
    b.fill(cx - HX, ground_y, cz - HZ,
           cx + HX, ground_y, cz + HZ, DIRT)

    # ================================================================
    # 2. 石径 — 从北到南穿越花圃
    # ================================================================
    print("  [2/7] 石径...")

    # 石径贯穿整个Z方向（含入口外延1格）
    for px in PATH_XS:
        for pz in range(cz - HZ - 1, cz + HZ + 2):
            b.setblock(px, ground_y, pz, PATH)

    # ================================================================
    # 3. 围合栏杆 — 金合欢栅栏矩形
    # ================================================================
    print("  [3/7] 围合栏杆...")

    # 北面栏杆（z = cz - HZ），中间3格留入口
    # 入口范围：cx-1, cx, cx+1（3格宽）
    for x in range(cx - HX, cx + HX + 1):
        if cx - 1 <= x <= cx + 1:
            continue  # 北入口
        b.setblock(x, rail_y, cz - HZ, RAIL)

    # 南面栏杆（z = cz + HZ），中间3格留入口
    for x in range(cx - HX, cx + HX + 1):
        if cx - 1 <= x <= cx + 1:
            continue  # 南入口
        b.setblock(x, rail_y, cz + HZ, RAIL)

    # 西面栏杆（x = cx - HX）
    for z in range(cz - HZ, cz + HZ + 1):
        b.setblock(cx - HX, rail_y, z, RAIL)

    # 东面栏杆（x = cx + HX）
    for z in range(cz - HZ, cz + HZ + 1):
        b.setblock(cx + HX, rail_y, z, RAIL)

    # ================================================================
    # 4. 角落灯笼 — 四角栅栏柱上
    # ================================================================
    print("  [4/7] 角落灯笼...")

    corners = [
        (cx - HX, cz - HZ),  # 西北
        (cx + HX, cz - HZ),  # 东北
        (cx - HX, cz + HZ),  # 西南
        (cx + HX, cz + HZ),  # 东南
    ]
    for lx, lz in corners:
        # 灯笼放在栅栏顶部上方1格
        b.setblock(lx, rail_y + 1, lz, LANTERN)

    # ================================================================
    # 5. 芍药花圃 — 密植芍药
    # ================================================================
    print("  [5/7] 芍药花圃...")

    # 在围栏内部种花（避开石径和栏杆位置）
    # 内部范围：x in [cx-HX+1, cx+HX-1], z in [cz-HZ+1, cz+HZ-1]
    # 但栏杆边也可以种（栏杆在 rail_y，花在 ground_y+1 同层但不冲突）
    # 种花范围：围栏内全部，减去石径
    for x in range(cx - HX + 1, cx + HX):
        for z in range(cz - HZ + 1, cz + HZ):
            if x in PATH_XS:
                continue  # 跳过石径
            # peony 是2格高花，放底部即可（Minecraft 自动生成上半部分）
            b.setblock(x, ground_y + 1, z, PEONY)

    # ================================================================
    # 6. 做旧效果 — 藤蔓 + 溢出花卉
    # ================================================================
    print("  [6/7] 做旧效果...")

    # --- 藤蔓：部分栏杆外侧攀附 ---
    # 藤蔓需要 blockstate 指定朝向（附着面）
    # vine[north=true] 表示藤蔓贴在方块的北面（即藤蔓在方块南侧，面朝北）
    # 栏杆外侧放藤蔓：
    #   西面栏杆外侧 → vine 在 x=cx-HX-1, 面朝东(east=true)
    #   东面栏杆外侧 → vine 在 x=cx+HX+1, 面朝西(west=true)
    #   北面栏杆外侧 → vine 在 z=cz-HZ-1, 面朝南(south=true)
    #   南面栏杆外侧 → vine 在 z=cz+HZ+1, 面朝北(north=true)
    vine_chance = 0.4

    # 西面藤蔓
    for z in range(cz - HZ, cz + HZ + 1):
        if random.random() < vine_chance:
            b.setblock(cx - HX - 1, rail_y, z, f"{VINE}[east=true]")
    # 东面藤蔓
    for z in range(cz - HZ, cz + HZ + 1):
        if random.random() < vine_chance:
            b.setblock(cx + HX + 1, rail_y, z, f"{VINE}[west=true]")
    # 北面藤蔓（避开入口）
    for x in range(cx - HX, cx + HX + 1):
        if cx - 1 <= x <= cx + 1:
            continue
        if random.random() < vine_chance:
            b.setblock(x, rail_y, cz - HZ - 1, f"{VINE}[south=true]")
    # 南面藤蔓（避开入口）
    for x in range(cx - HX, cx + HX + 1):
        if cx - 1 <= x <= cx + 1:
            continue
        if random.random() < vine_chance:
            b.setblock(x, rail_y, cz + HZ + 1, f"{VINE}[north=true]")

    # --- 溢出花卉：栏杆外1-2格散落芍药/玫瑰 ---
    overflow_flowers = [PEONY, PALETTE["rose"], PALETTE["tulip_pink"]]
    overflow_chance = 0.3

    # 四面外围1-2格散花
    for dist in [1, 2]:
        # 西侧外围
        for z in range(cz - HZ - 1, cz + HZ + 2):
            if random.random() < overflow_chance / dist:
                flower = random.choice(overflow_flowers)
                b.setblock(cx - HX - dist, ground_y, z, DIRT)
                b.setblock(cx - HX - dist, ground_y + 1, z, flower)
        # 东侧外围
        for z in range(cz - HZ - 1, cz + HZ + 2):
            if random.random() < overflow_chance / dist:
                flower = random.choice(overflow_flowers)
                b.setblock(cx + HX + dist, ground_y, z, DIRT)
                b.setblock(cx + HX + dist, ground_y + 1, z, flower)
        # 北侧外围（避开石径入口）
        for x in range(cx - HX - 1, cx + HX + 2):
            if cx - 2 <= x <= cx + 2:
                continue  # 入口附近不放
            if random.random() < overflow_chance / dist:
                flower = random.choice(overflow_flowers)
                b.setblock(x, ground_y, cz - HZ - dist, DIRT)
                b.setblock(x, ground_y + 1, cz - HZ - dist, flower)
        # 南侧外围（避开石径入口）
        for x in range(cx - HX - 1, cx + HX + 2):
            if cx - 2 <= x <= cx + 2:
                continue
            if random.random() < overflow_chance / dist:
                flower = random.choice(overflow_flowers)
                b.setblock(x, ground_y, cz + HZ + dist, DIRT)
                b.setblock(x, ground_y + 1, cz + HZ + dist, flower)

    # ================================================================
    # 7. 注册边界框
    # ================================================================
    print("  [7/7] 注册边界框...")

    # 边界包含外围溢出花（+2）和灯笼高度（+2）
    b.register_bbox("peony_rail",
                    cx - HX - 2, ground_y, cz - HZ - 2,
                    cx + HX + 2, ground_y + 3, cz + HZ + 2)

    print("  芍药阑建造完成！")


# ── 入口 ──

if __name__ == "__main__":
    with MinecraftBuilder() as b:
        build_peony_rail(b, cx=52, ground_y=-58, cz=20)
        print(f"Done! {b.cmd_count} commands")
