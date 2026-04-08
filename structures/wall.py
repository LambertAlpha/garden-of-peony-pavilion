"""围墙建造 — 明代知府后花园 (牡丹亭·游园惊梦)

粉墙黛瓦，漏窗月洞，苔藓斑驳。
园林范围 X:0~80, Z:0~60，单方块厚围墙沿四边建造。
"""

import sys
sys.path.insert(0, '/Users/lambertlin/minecraft-server/scripts')

from builder import MinecraftBuilder, filled_circle_points
from blocks import PALETTE, GROUND_Y, BUILD_Y
import random


# ── 常量 ──

WALL_HEIGHT = 4          # 墙基1 + 墙身2 + 压瓦1
X_MIN, X_MAX = 0, 80
Z_MIN, Z_MAX = 0, 60

# 南墙入口缺口
SOUTH_GAP_X1 = 35
SOUTH_GAP_X2 = 50

# 漏窗参数
WINDOW_WIDTH = 3          # 漏窗宽 3 格
WINDOW_Y_OFFSET = 2       # 墙基上方第 2 格（墙身第2层）

# 月洞门参数（东墙）
MOON_GATE_RADIUS = 2
MOON_GATE_Z = 30          # 东墙中段

# 做旧参数
MOSSY_RATIO = 0.10        # 10% 苔石
CRACKED_RATIO = 0.05      # 5% 裂石 (合计 15%)
VINE_CHANCE = 0.08        # 墙基附近藤蔓概率


def _north_terrain_y(x: int) -> int:
    """北墙(Z=0)地形高度函数。

    地形在中段隆起：两端约 BUILD_Y(-60)，中段最高约 -55。
    用简单的二次曲线模拟丘陵。
    """
    # x 范围 0~80, 中心 x=40
    # 最高点 y=-55, 两端 y=-60
    cx = 40
    peak_y = -55
    base_y = BUILD_Y  # -60
    rise = peak_y - base_y  # 5
    # 二次: y = base_y + rise * (1 - ((x-cx)/cx)^2)
    t = (x - cx) / cx  # -1 ~ 1
    y = base_y + rise * (1 - t * t)
    return int(round(y))


def _build_wall_column(b: MinecraftBuilder, x: int, z: int,
                       base_y: int, direction: str = ""):
    """在 (x, z) 建造一根完整的墙柱（4格高）。

    base_y: 墙基 Y 坐标（地面层）
    direction: 用于藤蔓朝向记录，此处不直接使用
    """
    # 1. 墙基
    b.setblock(x, base_y, z, PALETTE["wall_base"])
    # 2. 墙身 (2格)
    b.setblock(x, base_y + 1, z, PALETTE["wall"])
    b.setblock(x, base_y + 2, z, PALETTE["wall"])
    # 3. 压瓦
    b.setblock(x, base_y + 3, z, PALETTE["wall_cap"])


def _build_straight_wall(b: MinecraftBuilder, positions: list[tuple[int, int]],
                         base_y: int):
    """沿一组 (x, z) 坐标建造直墙，统一 base_y。"""
    for x, z in positions:
        _build_wall_column(b, x, z, base_y)


def build_east_wall(b: MinecraftBuilder):
    """东墙 X=80, Z: 0~60"""
    print("  东墙 (X=80)...")
    positions = [(X_MAX, z) for z in range(Z_MIN, Z_MAX + 1)]
    _build_straight_wall(b, positions, BUILD_Y)


def build_west_wall(b: MinecraftBuilder):
    """西墙 X=0, Z: 0~60"""
    print("  西墙 (X=0)...")
    positions = [(X_MIN, z) for z in range(Z_MIN, Z_MAX + 1)]
    _build_straight_wall(b, positions, BUILD_Y)


def build_north_wall(b: MinecraftBuilder):
    """北墙 Z=0, X: 0~80 — 跟随地形高度"""
    print("  北墙 (Z=0) — 跟随地形...")
    for x in range(X_MIN, X_MAX + 1):
        base_y = _north_terrain_y(x)
        _build_wall_column(b, x, Z_MIN, base_y)


def build_south_wall(b: MinecraftBuilder):
    """南墙 Z=60, X: 0~80 — 中段留入口缺口"""
    print("  南墙 (Z=60) — 留入口缺口 X:%d~%d..." % (SOUTH_GAP_X1, SOUTH_GAP_X2))
    for x in range(X_MIN, X_MAX + 1):
        if SOUTH_GAP_X1 <= x <= SOUTH_GAP_X2:
            continue  # 入口区不建墙
        _build_wall_column(b, x, Z_MAX, BUILD_Y)


# ── 漏窗 ──

def _place_window(b: MinecraftBuilder, x: int, y: int, z: int,
                  axis: str, width: int = WINDOW_WIDTH):
    """在墙身上开漏窗。

    axis: 'x' 表示沿 X 轴展开（南北墙），'z' 表示沿 Z 轴展开（东西墙）
    y: 漏窗所在 Y 坐标（墙身第2层）
    """
    for i in range(width):
        if axis == 'x':
            b.setblock(x + i, y, z, PALETTE["window"])
        else:
            b.setblock(x, y, z + i, PALETTE["window"])


def build_windows(b: MinecraftBuilder):
    """在四面墙上开漏窗。"""
    print("  漏窗...")
    window_y = BUILD_Y + WINDOW_Y_OFFSET  # 墙身第2层

    # 东墙 (X=80, 沿Z轴): 3个漏窗, 间距约 15-20
    # Z: 0~60, 避开月洞门区域(Z=28~32)和角落
    east_window_starts = [8, 28, 48]  # 注意: z=28 可能与月洞门冲突，调整
    # 月洞门在 Z=30 附近，避开 Z:27~33
    east_window_starts = [8, 45, 55]  # 重新分配：避开月洞门
    for z_start in east_window_starts:
        _place_window(b, X_MAX, window_y, z_start, axis='z')

    # 西墙 (X=0, 沿Z轴): 3个漏窗
    west_window_starts = [10, 28, 48]
    for z_start in west_window_starts:
        _place_window(b, X_MIN, window_y, z_start, axis='z')

    # 北墙 (Z=0, 沿X轴): 2个漏窗 (北墙地形起伏，选平坦区段)
    # 两端 base_y 约 -60, 漏窗 y 在 base_y+2
    # 选靠近两端的平坦区域
    north_window_starts = [10, 60]
    for x_start in north_window_starts:
        local_y = _north_terrain_y(x_start + 1) + WINDOW_Y_OFFSET
        _place_window(b, x_start, local_y, Z_MIN, axis='x')

    # 南墙 (Z=60, 沿X轴): 2个漏窗 (避开入口缺口 X:35~50)
    south_window_starts = [8, 60]
    for x_start in south_window_starts:
        _place_window(b, x_start, BUILD_Y + WINDOW_Y_OFFSET, Z_MAX, axis='x')


# ── 月洞门 ──

def build_moon_gate(b: MinecraftBuilder):
    """在东墙(X=80)中段开月洞门。

    使用 circle_yz 在 YZ 平面画圆，然后清空圆内方块。
    """
    print("  月洞门 (东墙 Z=%d)..." % MOON_GATE_Z)
    # 圆心: X=80, Y=墙基+1.5 (取整 BUILD_Y+2), Z=MOON_GATE_Z
    cx = X_MAX
    cy = BUILD_Y + 2  # 圆心在墙身中间偏上
    cz = MOON_GATE_Z
    r = MOON_GATE_RADIUS

    # 先用 filled_circle_points 获取圆内所有点, 清空为 air
    for dy, dz in filled_circle_points(cy, cz, r):
        b.setblock(cx, dy, dz, PALETTE["air"])

    # 在圆的边框上放置墙顶压瓦材质作为门框装饰（可选）
    # 用 circle_yz 画圆框
    b.circle_yz(cx, cy, cz, r, PALETTE["wall_base"])

    # 再次清空圆内部，确保门框不遮挡通行
    for dy, dz in filled_circle_points(cy, cz, r - 1):
        b.setblock(cx, dy, dz, PALETTE["air"])

    # 清空地面层，确保可以走过
    for dz_off in range(-r + 1, r):
        b.setblock(cx, BUILD_Y, cz + dz_off, PALETTE["air"])


# ── 做旧效果 ──

def _get_vine_state(wall_side: str) -> str:
    """根据墙面朝向返回藤蔓 block state。

    藤蔓需要附着在方块的某个面上。
    wall_side 指的是藤蔓面对的方向（即墙的内侧方向）。
    """
    return f'{PALETTE["vine"]}[{wall_side}=true]'


def apply_weathering(b: MinecraftBuilder):
    """做旧效果：替换部分白墙 + 墙基藤蔓"""
    print("  做旧效果...")

    # 收集所有墙身白墙坐标
    wall_blocks = []

    # 东墙墙身
    for z in range(Z_MIN, Z_MAX + 1):
        wall_blocks.append((X_MAX, BUILD_Y + 1, z, "west"))
        wall_blocks.append((X_MAX, BUILD_Y + 2, z, "west"))

    # 西墙墙身
    for z in range(Z_MIN, Z_MAX + 1):
        wall_blocks.append((X_MIN, BUILD_Y + 1, z, "east"))
        wall_blocks.append((X_MIN, BUILD_Y + 2, z, "east"))

    # 北墙墙身 (地形跟随)
    for x in range(X_MIN, X_MAX + 1):
        base_y = _north_terrain_y(x)
        wall_blocks.append((x, base_y + 1, Z_MIN, "south"))
        wall_blocks.append((x, base_y + 2, Z_MIN, "south"))

    # 南墙墙身 (跳过入口区)
    for x in range(X_MIN, X_MAX + 1):
        if SOUTH_GAP_X1 <= x <= SOUTH_GAP_X2:
            continue
        wall_blocks.append((x, BUILD_Y + 1, Z_MAX, "north"))
        wall_blocks.append((x, BUILD_Y + 2, Z_MAX, "north"))

    # 替换白墙为苔石/裂石
    for x, y, z, side in wall_blocks:
        roll = random.random()
        if roll < MOSSY_RATIO:
            b.setblock(x, y, z, PALETTE["wall_mossy"])
        elif roll < MOSSY_RATIO + CRACKED_RATIO:
            b.setblock(x, y, z, PALETTE["wall_cracked"])

    # 墙基附近放藤蔓（贴在墙内侧面）
    # 东墙内侧 (X=80, 藤蔓在 X=79, 面朝 east 贴在墙上)
    for z in range(Z_MIN + 1, Z_MAX):
        if random.random() < VINE_CHANCE:
            b.setblock(X_MAX - 1, BUILD_Y, z, _get_vine_state("east"))

    # 西墙内侧 (X=0, 藤蔓在 X=1, 面朝 west)
    for z in range(Z_MIN + 1, Z_MAX):
        if random.random() < VINE_CHANCE:
            b.setblock(X_MIN + 1, BUILD_Y, z, _get_vine_state("west"))

    # 北墙内侧 (Z=0, 藤蔓在 Z=1, 面朝 north)
    for x in range(X_MIN + 1, X_MAX):
        if random.random() < VINE_CHANCE:
            base_y = _north_terrain_y(x)
            b.setblock(x, base_y, Z_MIN + 1, _get_vine_state("north"))

    # 南墙内侧 (Z=60, 藤蔓在 Z=59, 面朝 south) — 跳过入口区
    for x in range(X_MIN + 1, X_MAX):
        if SOUTH_GAP_X1 <= x <= SOUTH_GAP_X2:
            continue
        if random.random() < VINE_CHANCE:
            b.setblock(x, BUILD_Y, Z_MAX - 1, _get_vine_state("south"))


# ── 主入口 ──

def build_walls(b: MinecraftBuilder):
    """建造完整围墙。"""
    print("=== Phase 1c: 围墙 ===")
    random.seed(42)

    # 1. 四面墙体
    build_east_wall(b)
    build_west_wall(b)
    build_north_wall(b)
    build_south_wall(b)

    # 2. 漏窗
    build_windows(b)

    # 3. 月洞门
    build_moon_gate(b)

    # 4. 做旧效果
    apply_weathering(b)

    # 注册边界框 (用于 undo)
    # 北墙最高 y=-55, 墙顶 y=-55+3=-52
    b.register_bbox("walls",
                    X_MIN, GROUND_Y - 1, Z_MIN,
                    X_MAX, -52, Z_MAX)

    print("  围墙建造完成。")


if __name__ == "__main__":
    with MinecraftBuilder() as b:
        build_walls(b)
        print(f"Done! Total commands: {b.cmd_count}")
