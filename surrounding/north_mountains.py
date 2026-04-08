"""北面青山 — 江南远景连绵山脉

在园林北侧围墙外 (Z:-5 ~ Z:-70) 建造 3~4 座大山 + 若干小丘,
模拟苏州园林借景远山的效果。

建造方法: 逐层椭圆填充, 每层用 fill 而非 setblock。
材质分层: 山脚草地 → 山腰岩石草混 → 山顶裸岩。
"""

import sys
sys.path.insert(0, '/Users/lambertlin/minecraft-server/scripts')
from builder import MinecraftBuilder
from blocks import PALETTE, GROUND_Y
import random
import math


# ── 材质配置 ──

def _pick_block(progress: float) -> str:
    """根据高度比例 (0=山脚, 1=山顶) 随机选材质"""
    r = random.random()
    if progress < 0.3:
        # 山脚: 60% grass + 25% dirt + 15% coarse_dirt
        if r < 0.60:
            return "minecraft:grass_block"
        elif r < 0.85:
            return "minecraft:dirt"
        else:
            return "minecraft:coarse_dirt"
    elif progress < 0.6:
        # 山腰: 40% stone + 30% andesite + 20% grass + 10% mossy_cobblestone
        if r < 0.40:
            return "minecraft:stone"
        elif r < 0.70:
            return "minecraft:andesite"
        elif r < 0.90:
            return "minecraft:grass_block"
        else:
            return "minecraft:mossy_cobblestone"
    elif progress < 0.85:
        # 中上: 50% stone + 30% andesite + 20% cobblestone
        if r < 0.50:
            return "minecraft:stone"
        elif r < 0.80:
            return "minecraft:andesite"
        else:
            return "minecraft:cobblestone"
    else:
        # 山顶: 70% stone + 30% andesite
        if r < 0.70:
            return "minecraft:stone"
        else:
            return "minecraft:andesite"


def _primary_block(progress: float) -> str:
    """每层的主材质 (用于 fill 整层)"""
    if progress < 0.3:
        return "minecraft:grass_block"
    elif progress < 0.6:
        return "minecraft:stone"
    elif progress < 0.85:
        return "minecraft:stone"
    else:
        return "minecraft:stone"


# ── 噪声函数 ──

def _noise_2d(x: float, z: float, seed: int = 0) -> float:
    """简易伪随机噪声, 返回 -1 ~ 1"""
    n = int(x * 73 + z * 179 + seed * 31) & 0xFFFFFF
    n = (n << 13) ^ n
    return (1.0 - ((n * (n * n * 15731 + 789221) + 1376312589) & 0x7FFFFFFF) / 1073741824.0)


# ── 山体建造 ──

def _build_mountain(b: MinecraftBuilder, cx: int, cz: int,
                    base_y: int, height: int, rx: int, rz: int,
                    name: str):
    """用逐层缩小的椭圆堆叠一座山

    cx, cz: 山顶中心 XZ
    base_y: 山脚 Y
    height: 总高度（格数）
    rx, rz: 底部半径 X/Z
    """
    print(f"  建造 {name}: 中心({cx},{cz}), 高{height}, 半径({rx},{rz})")

    for dy in range(height):
        y = base_y + dy
        progress = dy / height  # 0=底部, 1=顶部

        # 半径随高度缩小 (底宽顶窄, 略带曲线)
        taper = 1.0 - progress ** 0.7 * 0.85
        curr_rx = max(1, int(rx * taper))
        curr_rz = max(1, int(rz * taper))

        # 收集本层椭圆内的所有坐标
        # 策略: 先 fill 一个矩形主材质, 再 replace 添加次要材质
        # 但椭圆不是矩形, 所以我们按行 fill

        primary = _primary_block(progress)

        for dz in range(-curr_rz, curr_rz + 1):
            # 计算这一行在椭圆内的 x 范围
            if curr_rz == 0:
                frac_z = 0
            else:
                frac_z = (dz / curr_rz) ** 2
            if frac_z > 1.0:
                continue
            half_x = int(curr_rx * math.sqrt(1.0 - frac_z))
            if half_x < 0:
                continue

            # 加噪声让边缘不规则
            noise_val = _noise_2d(cx + half_x, cz + dz, dy)
            noise_offset = int(noise_val * 2)  # -2 ~ +2 格抖动
            half_x = max(0, half_x + noise_offset)

            x1 = cx - half_x
            x2 = cx + half_x
            z = cz + dz

            if x1 > x2:
                continue

            # fill 这一行
            b.fill(x1, y, z, x2, y, z, primary)

        # 随机替换部分方块为次要材质 (用 replace 命令批量处理)
        # 对每层的包围盒做 replace
        bbox_x1 = cx - curr_rx - 2
        bbox_x2 = cx + curr_rx + 2
        bbox_z1 = cz - curr_rz - 2
        bbox_z2 = cz + curr_rz + 2

        if progress < 0.3:
            # 山脚: 替换部分 grass 为 dirt 和 coarse_dirt
            b.fill(bbox_x1, y, bbox_z1, bbox_x2, y, bbox_z2,
                   "minecraft:dirt", f"replace {primary}")
            # 这样全替换了, 再把大部分换回来
            # 换个思路: 直接用 setblock 对少量位置做替换
            _scatter_replace(b, cx, cz, curr_rx, curr_rz, y,
                             primary, progress)
        else:
            _scatter_replace(b, cx, cz, curr_rx, curr_rz, y,
                             primary, progress)


def _scatter_replace(b: MinecraftBuilder, cx: int, cz: int,
                     curr_rx: int, curr_rz: int, y: int,
                     primary: str, progress: float):
    """在椭圆内随机散布次要材质方块

    用 setblock 替换约 30% 的方块为次要材质, 比全量 replace 更可控。
    为了效率, 每隔几格放一个。
    """
    # 计算要替换的数量 (椭圆面积的 ~25%)
    area = int(math.pi * curr_rx * curr_rz)
    num_replace = max(0, area // 4)

    # 限制单层 setblock 数量, 避免太慢
    num_replace = min(num_replace, 60)

    for _ in range(num_replace):
        # 随机选椭圆内一点
        angle = random.uniform(0, 2 * math.pi)
        r_frac = random.uniform(0, 1) ** 0.5  # sqrt 使分布更均匀
        dx = int(curr_rx * r_frac * math.cos(angle))
        dz = int(curr_rz * r_frac * math.sin(angle))
        bx = cx + dx
        bz = cz + dz
        block = _pick_block(progress)
        if block != primary:
            b.setblock(bx, y, bz, block)


# ── 植被 ──

def _place_trees(b: MinecraftBuilder, cx: int, cz: int,
                 base_y: int, height: int, rx: int, rz: int,
                 name: str):
    """在山体上种树"""
    print(f"  种植 {name} 的植被...")

    # 山脚橡树 (0~30% 高度)
    for _ in range(random.randint(5, 8)):
        angle = random.uniform(0, 2 * math.pi)
        r_frac = random.uniform(0.5, 0.95)
        dy = random.randint(0, int(height * 0.25))
        taper = 1.0 - (dy / height) ** 0.7 * 0.85
        eff_rx = rx * taper * r_frac
        eff_rz = rz * taper * r_frac
        tx = int(cx + eff_rx * math.cos(angle))
        tz = int(cz + eff_rz * math.sin(angle))
        ty = base_y + dy + 1
        _place_oak_tree(b, tx, ty, tz)

    # 山脚杜鹃花丛
    for _ in range(random.randint(3, 6)):
        angle = random.uniform(0, 2 * math.pi)
        r_frac = random.uniform(0.6, 0.95)
        dy = random.randint(0, int(height * 0.2))
        taper = 1.0 - (dy / height) ** 0.7 * 0.85
        eff_rx = rx * taper * r_frac
        eff_rz = rz * taper * r_frac
        ax = int(cx + eff_rx * math.cos(angle))
        az = int(cz + eff_rz * math.sin(angle))
        ay = base_y + dy + 1
        b.setblock(ax, ay, az, "minecraft:flowering_azalea")

    # 山腰稀疏云杉 (30~60%)
    for _ in range(random.randint(2, 4)):
        angle = random.uniform(0, 2 * math.pi)
        r_frac = random.uniform(0.3, 0.7)
        dy = random.randint(int(height * 0.3), int(height * 0.55))
        taper = 1.0 - (dy / height) ** 0.7 * 0.85
        eff_rx = rx * taper * r_frac
        eff_rz = rz * taper * r_frac
        sx = int(cx + eff_rx * math.cos(angle))
        sz = int(cz + eff_rz * math.sin(angle))
        sy = base_y + dy + 1
        _place_spruce_tree(b, sx, sy, sz)

    # 山顶苔藓点缀 (85~100%)
    for _ in range(random.randint(2, 5)):
        angle = random.uniform(0, 2 * math.pi)
        r_frac = random.uniform(0.1, 0.5)
        dy = random.randint(int(height * 0.85), height - 1)
        taper = 1.0 - (dy / height) ** 0.7 * 0.85
        eff_rx = max(1, rx * taper * r_frac)
        eff_rz = max(1, rz * taper * r_frac)
        mx = int(cx + eff_rx * math.cos(angle))
        mz = int(cz + eff_rz * math.sin(angle))
        my = base_y + dy + 1
        b.setblock(mx, my, mz, "minecraft:moss_block")
        # 上面加苔藓毯
        b.setblock(mx, my + 1, mz, "minecraft:moss_carpet")


def _place_oak_tree(b: MinecraftBuilder, x: int, y: int, z: int):
    """放一棵简易橡树 (trunk 4~5 格 + 树冠)"""
    trunk_h = random.randint(4, 5)
    # 树干
    b.fill(x, y, z, x, y + trunk_h - 1, z, "minecraft:oak_log")
    # 树冠 (顶部 3 层)
    top = y + trunk_h
    for dy in range(3):
        r = 2 if dy < 2 else 1
        b.fill(x - r, top + dy, z - r,
               x + r, top + dy, z + r,
               "minecraft:oak_leaves", "replace minecraft:air")


def _place_spruce_tree(b: MinecraftBuilder, x: int, y: int, z: int):
    """放一棵简易云杉 (瘦高, 锥形冠)"""
    trunk_h = random.randint(5, 7)
    b.fill(x, y, z, x, y + trunk_h - 1, z, "minecraft:spruce_log")
    # 锥形树冠
    for dy in range(trunk_h - 1):
        ly = y + dy + 1
        # 从底到顶半径 3→0
        r = max(0, 3 - dy)
        if r > 0:
            b.fill(x - r, ly, z - r,
                   x + r, ly, z + r,
                   "minecraft:spruce_leaves", "replace minecraft:air")
        elif dy < trunk_h - 1:
            # 顶部 1x1
            b.setblock(x, ly, z, "minecraft:spruce_leaves")


# ── 山间小溪 ──

def _build_stream(b: MinecraftBuilder, base_y: int):
    """在主峰与副峰1之间建一条小溪"""
    print("  建造山间溪流...")
    # 溪流从约 X=35, Z=-35 流向 X=30, Z=-10
    # 蜿蜒路径
    stream_points = []
    for i in range(30):
        t = i / 29
        x = int(35 - 5 * t + 2 * math.sin(t * 4))
        z = int(-35 + 25 * t)
        y = int(base_y + 15 * (1 - t))  # 从高处流下
        stream_points.append((x, y, z))

    for x, y, z in stream_points:
        # 2 格宽水流
        b.fill(x, y, z, x + 1, y, z, "minecraft:water")
        # 溪床用石头
        b.fill(x - 1, y - 1, z, x + 2, y - 1, z, "minecraft:mossy_cobblestone")


# ── 山脚苔藓铺地 ──

def _build_moss_ground(b: MinecraftBuilder, base_y: int):
    """在山脚散布苔藓地面"""
    print("  铺设山脚苔藓...")
    # 在 Z:-5 ~ Z:-15 范围内随机铺苔藓
    for _ in range(80):
        x = random.randint(5, 115)
        z = random.randint(-15, -5)
        b.setblock(x, base_y, z, "minecraft:moss_block")
        if random.random() < 0.5:
            b.setblock(x, base_y + 1, z, "minecraft:moss_carpet")


# ── 主函数 ──

def build_north_mountains(b: MinecraftBuilder):
    print("=== 北面青山 ===")
    random.seed(200)

    base_y = GROUND_Y  # -61

    # 注册边界框以便撤销
    b.register_bbox("north_mountains", -5, base_y, -70, 125, base_y + 45, 0)

    # ── 1) 主峰: X=50, Z=-40, 高度 40 ──
    print("\n[1/4] 主峰")
    _build_mountain(b, cx=50, cz=-40, base_y=base_y,
                    height=40, rx=20, rz=15, name="主峰")
    _place_trees(b, cx=50, cz=-40, base_y=base_y,
                 height=40, rx=20, rz=15, name="主峰")

    # ── 2) 副峰1: X=20, Z=-30, 高度 25 ──
    print("\n[2/4] 副峰1")
    _build_mountain(b, cx=20, cz=-30, base_y=base_y,
                    height=25, rx=15, rz=12, name="副峰1")
    _place_trees(b, cx=20, cz=-30, base_y=base_y,
                 height=25, rx=15, rz=12, name="副峰1")

    # ── 3) 副峰2: X=90, Z=-35, 高度 30 ──
    print("\n[3/4] 副峰2")
    _build_mountain(b, cx=90, cz=-35, base_y=base_y,
                    height=30, rx=18, rz=13, name="副峰2")
    _place_trees(b, cx=90, cz=-35, base_y=base_y,
                 height=30, rx=18, rz=13, name="副峰2")

    # ── 4) 小丘 (填充山间空隙) ──
    print("\n[4/4] 小丘")
    small_hills = [
        (35, -20, 12, 10, 8, "小丘A"),   # 主峰与副峰1之间
        (70, -25, 15, 12, 9, "小丘B"),   # 主峰与副峰2之间
        (10, -15, 10, 8, 7, "小丘C"),    # 最西侧
        (105, -20, 11, 9, 7, "小丘D"),   # 最东侧
    ]
    for hx, hz, hh, hrx, hrz, hname in small_hills:
        _build_mountain(b, cx=hx, cz=hz, base_y=base_y,
                        height=hh, rx=hrx, rz=hrz, name=hname)
        # 小丘只种少量低矮植被
        for _ in range(random.randint(2, 4)):
            angle = random.uniform(0, 2 * math.pi)
            r_frac = random.uniform(0.3, 0.8)
            dy = random.randint(0, int(hh * 0.3))
            taper = 1.0 - (dy / hh) ** 0.7 * 0.85
            px = int(hx + hrx * taper * r_frac * math.cos(angle))
            pz = int(hz + hrz * taper * r_frac * math.sin(angle))
            py = base_y + dy + 1
            b.setblock(px, py, pz, "minecraft:flowering_azalea")

    # ── 5) 山间溪流 ──
    print("\n[5] 溪流")
    _build_stream(b, base_y)

    # ── 6) 山脚苔藓 ──
    print("\n[6] 苔藓铺地")
    _build_moss_ground(b, base_y)

    print("\n=== 北面青山完成 ===")


if __name__ == "__main__":
    with MinecraftBuilder() as b:
        build_north_mountains(b)
        print(f"Done! {b.cmd_count} commands")
