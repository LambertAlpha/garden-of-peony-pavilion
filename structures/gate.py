"""入口区建造 — 小庭深院 (牡丹亭·游园惊梦)

"园门洞开""画廊金粉半零星""粉画垣"
设计核心："藏" — 进门后被影壁遮挡视线，转弯后水面豁然开朗。

组件：园门 → 小庭院 → 粉画垣(影壁) → 荼蘼花架 → 石径
"""

import sys
sys.path.insert(0, '/Users/lambertlin/minecraft-server/scripts')

from builder import MinecraftBuilder
from blocks import PALETTE, GROUND_Y, BUILD_Y
import random


# ── 常量 ──

# 园门位置（南墙缺口中央）
GATE_CX = 43          # 门中心 X
GATE_Z = 60           # 南墙线
GATE_PILLAR_W = 41    # 西柱 X
GATE_PILLAR_E = 45    # 东柱 X（净宽3格：42,43,44）

# 小庭院范围
COURT_X1, COURT_X2 = 38, 48
COURT_Z1, COURT_Z2 = 53, 59   # Z1=北端(影壁), Z2=南端(靠园门)

# 影壁
SCREEN_Z = 53
SCREEN_X1, SCREEN_X2 = 40, 46  # 缩短，两端各留2格通道

# 荼蘼花架
BOWER_X1, BOWER_X2 = 40, 46
BOWER_Z1, BOWER_Z2 = 49, 52

# 石径终点（池塘南岸）
PATH_END_Z = 38


# ══════════════════════════════════════════════════════════
# 1. 园门
# ══════════════════════════════════════════════════════════

def _build_gate(b: MinecraftBuilder):
    """简单门楼：两柱 + 横梁 + 硬山顶小屋顶 + 门槛"""
    print("  [1/5] 园门...")

    PILLAR = PALETTE["pillar"]          # 去皮金合欢
    BEAM = PALETTE["beam"]              # 深色橡木板
    ROOF = PALETTE["roof"]              # 深板岩瓦片楼梯
    ROOF_SLAB = PALETTE["roof_slab"]    # 深板岩瓦片半砖
    ROOF_BLOCK = PALETTE["roof_block"]  # 深板岩瓦片
    BASE_SLAB = PALETTE["base_slab"]    # 石砖半砖（门槛）

    y0 = BUILD_Y  # -60, 地面第一格

    # --- 门槛（石砖半砖，门洞底部） ---
    for x in range(GATE_PILLAR_W + 1, GATE_PILLAR_E):
        b.setblock(x, y0, GATE_Z, f"{BASE_SLAB}[type=bottom]")

    # --- 两根柱子（4格高，y0 到 y0+3） ---
    for pillar_x in (GATE_PILLAR_W, GATE_PILLAR_E):
        b.fill(pillar_x, y0, GATE_Z, pillar_x, y0 + 3, GATE_Z, PILLAR)

    # --- 横梁（柱顶，y0+4，连接两柱） ---
    b.fill(GATE_PILLAR_W, y0 + 4, GATE_Z,
           GATE_PILLAR_E, y0 + 4, GATE_Z, BEAM)

    # --- 硬山顶小屋顶（3格宽两面坡） ---
    # 屋顶在 y0+5 层，以 GATE_CX 为脊线
    # 门楼沿Z轴只1格厚，所以屋顶向南北各出挑1格
    roof_y = y0 + 5

    # 南坡（facing=north，低端朝南=朝外）
    for x in range(GATE_PILLAR_W, GATE_PILLAR_E + 1):
        b.setblock(x, roof_y, GATE_Z + 1,
                   f"{ROOF}[facing=north,half=bottom]")
    # 北坡（facing=south，低端朝北=朝外）
    for x in range(GATE_PILLAR_W, GATE_PILLAR_E + 1):
        b.setblock(x, roof_y, GATE_Z - 1,
                   f"{ROOF}[facing=south,half=bottom]")
    # 屋脊（中间一排实心瓦片）
    for x in range(GATE_PILLAR_W, GATE_PILLAR_E + 1):
        b.setblock(x, roof_y, GATE_Z, ROOF_BLOCK)

    # 屋脊上方半砖收顶
    for x in range(GATE_PILLAR_W, GATE_PILLAR_E + 1):
        b.setblock(x, roof_y + 1, GATE_Z, f"{ROOF_SLAB}[type=bottom]")

    # 两端山墙封板（东西两头用瓦片封住三角形）
    for gable_x in (GATE_PILLAR_W - 1, GATE_PILLAR_E + 1):
        b.setblock(gable_x, roof_y, GATE_Z, ROOF_BLOCK)
        # 南北出挑的楼梯端头也补一个
        b.setblock(gable_x, roof_y, GATE_Z + 1,
                   f"{ROOF}[facing=north,half=bottom]")
        b.setblock(gable_x, roof_y, GATE_Z - 1,
                   f"{ROOF}[facing=south,half=bottom]")


# ══════════════════════════════════════════════════════════
# 2. 小庭院
# ══════════════════════════════════════════════════════════

def _build_courtyard(b: MinecraftBuilder):
    """小庭院：石砖铺地 + 矮墙围合 + 花窗"""
    print("  [2/5] 小庭院...")

    WALL = PALETTE["wall"]              # 白色混凝土（粉墙）
    WALL_BASE = PALETTE["wall_base"]    # 石砖（墙基）
    WALL_CAP = PALETTE["wall_cap"]      # 深板岩瓦片半砖（墙顶）
    FLOOR = PALETTE["floor_alt"]        # 石砖铺地
    TRAPDOOR = PALETTE["trapdoor"]      # 丛林活板门（花窗）

    y0 = BUILD_Y

    # --- 地面铺装（石砖） ---
    b.fill(COURT_X1, y0, COURT_Z1,
           COURT_X2, y0, COURT_Z2, FLOOR)

    # --- 矮墙围合（3格高 = 墙基1 + 墙身1 + 压瓦1） ---
    # 庭院矮墙比外围墙低1格，体现"深院"的围合而非封闭

    def _court_wall_column(x, z):
        """庭院矮墙单柱：墙基 + 白墙 + 压瓦"""
        b.setblock(x, y0 + 1, z, WALL_BASE)
        b.setblock(x, y0 + 2, z, WALL)
        b.setblock(x, y0 + 3, z, WALL_CAP)

    # 东墙 (X=COURT_X2)
    for z in range(COURT_Z1, COURT_Z2 + 1):
        _court_wall_column(COURT_X2, z)

    # 西墙 (X=COURT_X1)
    for z in range(COURT_Z1, COURT_Z2 + 1):
        _court_wall_column(COURT_X1, z)

    # 北墙 (Z=COURT_Z1) — 影壁两端的短墙段
    # 左段 X:38~39（影壁通道西侧闭合）
    for x in range(COURT_X1, SCREEN_X1):
        _court_wall_column(x, COURT_Z1)
    # 右段 X:47~48（影壁通道东侧闭合）
    for x in range(SCREEN_X2 + 1, COURT_X2 + 1):
        _court_wall_column(x, COURT_Z1)

    # 南墙 (Z=COURT_Z2) — 中段留门洞（对接园门）
    for x in range(COURT_X1, COURT_X2 + 1):
        if GATE_PILLAR_W <= x <= GATE_PILLAR_E:
            continue  # 门洞位置不建墙
        _court_wall_column(x, COURT_Z2)

    # --- 花窗（东西两面各一个） ---
    # 花窗位置：墙身中段，y0+2 层（白墙层），用打开的丛林活板门
    window_y = y0 + 2

    # 东墙花窗 — 居中，约 Z=56
    east_wz = 56
    b.setblock(COURT_X2, window_y, east_wz,
               f"{TRAPDOOR}[facing=west,half=bottom,open=true]")

    # 西墙花窗 — 居中，约 Z=56
    b.setblock(COURT_X1, window_y, east_wz,
               f"{TRAPDOOR}[facing=east,half=bottom,open=true]")


# ══════════════════════════════════════════════════════════
# 3. 粉画垣 / 影壁
# ══════════════════════════════════════════════════════════

def _build_screen_wall(b: MinecraftBuilder):
    """影壁：白墙4格高，铁栏杆漏窗装饰，两端留通道"""
    print("  [3/5] 粉画垣（影壁）...")

    WALL = PALETTE["wall"]
    WALL_BASE = PALETTE["wall_base"]
    WALL_CAP = PALETTE["wall_cap"]
    WINDOW = PALETTE["window"]       # 铁栏杆

    y0 = BUILD_Y

    # --- 影壁主体 X:40~46, Z=53, 4格高 ---
    for x in range(SCREEN_X1, SCREEN_X2 + 1):
        # 墙基
        b.setblock(x, y0 + 1, SCREEN_Z, WALL_BASE)
        # 墙身（2格白墙）
        b.setblock(x, y0 + 2, SCREEN_Z, WALL)
        b.setblock(x, y0 + 3, SCREEN_Z, WALL)
        # 压瓦
        b.setblock(x, y0 + 4, SCREEN_Z, WALL_CAP)

    # --- 漏窗装饰（铁栏杆图案，在墙身中段） ---
    # 在 y0+3 层（墙身第2层），中间5格做漏窗（X:41~45）
    # 保留两端各1格实墙(X:40和46)作为边框
    for x in range(SCREEN_X1 + 1, SCREEN_X2):
        b.setblock(x, y0 + 3, SCREEN_Z, WINDOW)

    # 在 y0+2 层做间隔漏窗（每隔一格），形成几何图案
    for x in range(SCREEN_X1 + 1, SCREEN_X2):
        if (x - SCREEN_X1) % 2 == 0:
            b.setblock(x, y0 + 2, SCREEN_Z, WINDOW)

    # --- 影壁底座加宽（前后各出挑1格石砖，增加厚重感） ---
    for x in range(SCREEN_X1, SCREEN_X2 + 1):
        b.setblock(x, y0, SCREEN_Z - 1, WALL_BASE)
        b.setblock(x, y0, SCREEN_Z + 1, WALL_BASE)
        b.setblock(x, y0 + 1, SCREEN_Z - 1,
                   f"{PALETTE['base_slab']}[type=top]")
        b.setblock(x, y0 + 1, SCREEN_Z + 1,
                   f"{PALETTE['base_slab']}[type=top]")


# ══════════════════════════════════════════════════════════
# 4. 荼蘼花架
# ══════════════════════════════════════════════════════════

def _build_flower_bower(b: MinecraftBuilder):
    """荼蘼花架：云杉栅栏搭架 + 藤蔓垂挂
    "荼蘼外烟丝醉软""睡荼蘼抓住裙衩线"
    """
    print("  [4/5] 荼蘼花架...")

    FENCE = "minecraft:spruce_fence"    # 云杉栅栏
    VINE = PALETTE["vine"]

    y0 = BUILD_Y

    # --- 花架立柱（四角，3格高） ---
    pillar_positions = [
        (BOWER_X1, BOWER_Z1),   # 西北
        (BOWER_X2, BOWER_Z1),   # 东北
        (BOWER_X1, BOWER_Z2),   # 西南
        (BOWER_X2, BOWER_Z2),   # 东南
    ]
    for px, pz in pillar_positions:
        for dy in range(1, 4):  # y0+1 到 y0+3
            b.setblock(px, y0 + dy, pz, FENCE)

    # --- 中间加两根立柱（增加密度） ---
    mid_pillars = [
        (GATE_CX, BOWER_Z1),    # 北中
        (GATE_CX, BOWER_Z2),    # 南中
    ]
    for px, pz in mid_pillars:
        for dy in range(1, 4):
            b.setblock(px, y0 + dy, pz, FENCE)

    # --- 顶部横梁（y0+3 层，沿X轴连接） ---
    # 北横梁
    for x in range(BOWER_X1, BOWER_X2 + 1):
        b.setblock(x, y0 + 3, BOWER_Z1, FENCE)
    # 南横梁
    for x in range(BOWER_X1, BOWER_X2 + 1):
        b.setblock(x, y0 + 3, BOWER_Z2, FENCE)
    # 纵梁（沿Z轴连接，形成网格顶）
    for x in range(BOWER_X1, BOWER_X2 + 1, 2):
        for z in range(BOWER_Z1, BOWER_Z2 + 1):
            b.setblock(x, y0 + 3, z, FENCE)

    # --- 藤蔓垂挂（从顶部向下，模拟荼蘼攀援） ---
    for x in range(BOWER_X1 + 1, BOWER_X2):
        for z in range(BOWER_Z1, BOWER_Z2 + 1):
            if random.random() < 0.45:
                # 藤蔓挂在横梁下方，1~2格长
                vine_len = random.choice([1, 2])
                for dy in range(vine_len):
                    vy = y0 + 2 - dy
                    # 藤蔓需要附着方向，随机选一面
                    face = random.choice(["north", "south", "east", "west"])
                    b.setblock(x, vy, z, f"{VINE}[{face}=true]")


# ══════════════════════════════════════════════════════════
# 5. 石径（曲径通幽）
# ══════════════════════════════════════════════════════════

def _build_winding_path(b: MinecraftBuilder):
    """蜿蜒小径：从花架通向池塘南岸
    "曲径通幽" — 宽2格，左右轻微偏移
    """
    print("  [5/5] 石径...")

    PATH = PALETTE["path"]          # 泥土小径
    GRAVEL = PALETTE["gravel"]      # 碎石点缀

    # 石径从 Z=49（花架北端）向北到 Z=38（池塘南岸）
    # 基准中心线 X=43，每隔2~3格偏移 +-1
    center_x = GATE_CX  # 43

    # 预计算蜿蜒路线：每个Z值对应的X偏移
    path_points = []
    offset = 0
    direction = 1  # 1=向东偏, -1=向西偏

    for z in range(BOWER_Z1 - 1, PATH_END_Z - 1, -1):  # Z=48 down to Z=38
        path_points.append((center_x + offset, z))

        # 每2~3格改变偏移
        if random.random() < 0.45:
            offset += direction
            # 限制偏移范围 [-2, 2]
            if abs(offset) >= 2:
                direction = -direction

    # 铺设小径（每个点铺2格宽）
    for px, pz in path_points:
        # 先把地面改回泥土（dirt_path 需要在 dirt 上方）
        # dirt_path 是特殊方块，直接放置即可
        b.setblock(px, GROUND_Y, pz, PATH)
        b.setblock(px + 1, GROUND_Y, pz, PATH)

    # 小径两侧随机碎石点缀
    for px, pz in path_points:
        if random.random() < 0.2:
            side = random.choice([-1, 2])  # 左侧或右侧
            b.setblock(px + side, GROUND_Y, pz, GRAVEL)


# ══════════════════════════════════════════════════════════
# 主入口
# ══════════════════════════════════════════════════════════

def build_gate_area(b: MinecraftBuilder):
    """建造入口区：园门 → 小庭院 → 影壁 → 荼蘼花架 → 石径"""
    print("=== 入口区 ===")
    random.seed(44)

    _build_gate(b)
    _build_courtyard(b)
    _build_screen_wall(b)
    _build_flower_bower(b)
    _build_winding_path(b)

    # 注册边界框（覆盖整个入口区，含屋顶最高点）
    b.register_bbox("gate_area", 36, GROUND_Y, PATH_END_Z - 1,
                    50, BUILD_Y + 8, GATE_Z + 2)

    print("  入口区建造完成。")


if __name__ == "__main__":
    with MinecraftBuilder() as b:
        build_gate_area(b)
        print(f"Done! {b.cmd_count} commands")
