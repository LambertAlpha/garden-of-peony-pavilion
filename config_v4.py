"""v4 总平面图配置 — 碰撞修正版

基于 config_v3 修正所有建筑碰撞。

修正原则:
  1. 每栋建筑含 3 格外延后不与任何其他建筑重叠
  2. 水面轮廓不变 (MAIN_LAKE / CREEK / DEEP_POOL 等)
  3. 廊道 waypoints 跟随建筑坐标调整
  4. 入口序列 Z 轴间距至少留 5 格（门厅-小庭 raw gap=3, 小庭-远香堂 raw gap=6）
  5. 入口门厅+小庭深院作为一体化建筑群，允许 buffered 重叠
  6. 秋千嵌入太湖石组区域，允许 buffered 重叠

坐标修改汇总 (v3 → v4):
  牡丹亭:   cz 10→8
  芍药阑:   cx 58→50, cz 22→26
  池馆:     cx 55→34, cz 18→20
  太湖石组: cx 70→80
  秋千:     cx 65→76, cz 14→8
  濯缨水阁: cx 74→82, cz 22→26
  远香堂:   cz 72→67
  入口门厅: cz 86→87, size_z 9→5
  小庭深院: cz 80不变, size_z 7→5
  听雨轩:   cx 40→34, cz 58→54
  荼蘼花架: cx 48→50, cz 68→53
  半亭:     cx 82→88, cz 58→62
  石舫:     cx 84→85, cz 48→46
  曲廊亭:   cx 92→96
  梅花庵观: cz 12→13
  大梅树:   x 10→6, z 10→4
  翠轩/画船/闺塾: 不变

坐标系:
  原点 (0,0) = 西北角
  X 正方向 = 东，Z 正方向 = 南
  地块: 120 x 90 (10,800格)
"""

VERSION = "v4-collision-fix"

# ═══════════════════════════════════════════
# 园林范围
# ═══════════════════════════════════════════
GARDEN = {"x_min": 0, "x_max": 120, "z_min": 0, "z_max": 90}

# ═══════════════════════════════════════════
# Y 坐标体系
# ═══════════════════════════════════════════
GROUND_Y = -61          # 草方块层（超平坦默认）
BUILD_Y = -60           # 标准地面建筑起始层
HIGHLAND_Y = -57        # 北侧假山高地（牡丹亭区域）
WATER_SURFACE_Y = -61   # 水面层
LAKE_BOTTOM_Y = -64     # 主湖底（深3格）
DEEP_POOL_BOTTOM_Y = -65  # 假山深潭底（深4格）

# ═══════════════════════════════════════════
# 一、水面系统 — 与 v3 完全相同，不修改
# ═══════════════════════════════════════════

MAIN_LAKE = {
    "shoreline": [
        (30, 20), (38, 17), (45, 21),
        (50, 15), (56, 13), (62, 16),
        (68, 19), (75, 16), (80, 22),
        (86, 28),
        (90, 34), (92, 42), (90, 50),
        (86, 56), (82, 60),
        (74, 64), (66, 67), (58, 68),
        (50, 67), (42, 64), (36, 60),
        (32, 54), (28, 46), (26, 38),
        (28, 32), (30, 26), (30, 20),
    ],
    "depth": 3,
    "bottom_y": -64,
    "center": (58, 40),
}

CREEK = {
    "centerline": [
        (30, 20), (26, 16), (25, 15), (20, 13),
        (16, 16), (14, 20), (12, 25), (14, 30),
    ],
    "widths": [5, 5, 4, 3, 3, 4, 3, 8],
    "depth": 2,
    "bottom_y": -63,
}

CREEK_POOL = {
    "cx": 14, "cz": 30,
    "rx": 5, "rz": 5,
    "depth": 2,
    "bottom_y": -63,
}

DEEP_POOL = {
    "shoreline": [
        (88, 10), (94, 8), (100, 10), (102, 16),
        (98, 20), (92, 18), (88, 14), (88, 10),
    ],
    "depth": 4,
    "bottom_y": -65,
}

POOL_CREEK = {
    "centerline": [
        (82, 28), (84, 24), (86, 20), (88, 16), (88, 14),
    ],
    "width": 2,
    "depth": 2,
}

# ═══════════════════════════════════════════
# 二、建筑 (19栋) — 碰撞修正后坐标
# ═══════════════════════════════════════════

# --- 核心梦境建筑 (P0) ---

PEONY_PAVILION = {  # 1. 牡丹亭 — 四角攒尖亭
    "name": "牡丹亭",
    "cx": 58, "cz": 8,         # v3: cz=10 → v4: cz=8, 上移2格
    "size_x": 15, "size_z": 15,
    "facing": "all",
    "ground_y": -57,
    "pillar_h": 6,
    "roof_type": "hip_pointed",
    "priority": "P0",
}

PEONY_RAIL = {  # 2. 芍药阑 — 花圃围栏
    "name": "芍药阑",
    "cx": 50, "cz": 26,        # v3: cx=58,cz=22 → v4: cx=50,cz=26
    "size_x": 11, "size_z": 9,
    "facing": None,
    "ground_y": -58,
    "priority": "P0",
}

# --- 主要建筑 (P1) ---

CUI_XUAN = {  # 3. 翠轩 — 不变
    "name": "翠轩",
    "cx": 16, "cz": 28,
    "size_x": 17, "size_z": 11,
    "facing": "east",
    "ground_y": -60,
    "pillar_h": 6,
    "roof_type": "gable",
    "priority": "P1",
}

CHI_GUAN = {  # 4. 池馆 — 大幅西移，远离牡丹亭
    "name": "池馆",
    "cx": 34, "cz": 20,        # v3: cx=55,cz=18 → v4: cx=34,cz=20
    "size_x": 9, "size_z": 7,
    "facing": "south",
    "ground_y": -59,
    "pillar_h": 5,
    "roof_type": "gable",
    "over_water": True,
    "priority": "P1",
}

ZHUO_YING = {  # 5. 濯缨水阁 — 东移，远离牡丹亭和芍药阑
    "name": "濯缨水阁",
    "cx": 82, "cz": 26,        # v3: cx=74,cz=22 → v4: cx=82,cz=26
    "size_x": 11, "size_z": 7,
    "facing": "south",
    "ground_y": -59,
    "pillar_h": 5,
    "roof_type": "gable",
    "over_water": True,
    "priority": "P1",
}

YUAN_XIANG = {  # 6. 远香堂 — 北移，拉开与入口序列间距
    "name": "远香堂",
    "cx": 58, "cz": 67,        # v3: cz=72 → v4: cz=67
    "size_x": 19, "size_z": 11,
    "facing": "north",
    "ground_y": -60,
    "pillar_h": 6,
    "roof_type": "hip",
    "priority": "P1",
}

GATE = {  # 7. 入口门厅 — 南移+缩小，与小庭形成一体化序列
    "name": "入口门厅",
    "cx": 58, "cz": 87,        # v3: cz=86 → v4: cz=87, size_z 9→5
    "size_x": 15, "size_z": 5,
    "facing": "south",
    "ground_y": -60,
    "pillar_h": 5,
    "priority": "P1",
}

COURTYARD = {  # 8. 小庭深院 — 缩小，与门厅配合
    "name": "小庭深院",
    "cx": 58, "cz": 80,        # cz 不变, size_z 7→5
    "size_x": 15, "size_z": 5,
    "facing": None,
    "ground_y": -60,
    "priority": "P1",
}

# --- 中小型建筑 (P2) ---

HALF_PAVILION_SE = {  # 9. 半亭（东南角）— 东移南移
    "name": "半亭",
    "cx": 88, "cz": 62,        # v3: cx=82,cz=58 → v4: cx=88,cz=62
    "size_x": 7, "size_z": 7,
    "facing": "northwest",
    "ground_y": -60,
    "pillar_h": 5,
    "priority": "P2",
}

CORRIDOR_PAVILION_E = {  # 10. 曲廊亭（东岸转折）— 东移
    "name": "曲廊亭",
    "cx": 96, "cz": 42,        # v3: cx=92 → v4: cx=96
    "size_x": 5, "size_z": 5,
    "facing": "all",
    "ground_y": -60,
    "pillar_h": 4,
    "priority": "P2",
}

TING_YU_XUAN = {  # 11. 听雨轩 — 西移北移
    "name": "听雨轩",
    "cx": 34, "cz": 54,        # v3: cx=40,cz=58 → v4: cx=34,cz=54
    "size_x": 9, "size_z": 7,
    "facing": "north",
    "ground_y": -60,
    "pillar_h": 5,
    "priority": "P2",
}

TUMI_TRELLIS = {  # 12. 荼蘼花架 — 移位避开远香堂和听雨轩
    "name": "荼蘼花架",
    "cx": 50, "cz": 53,        # v3: cx=48,cz=68 → v4: cx=50,cz=53
    "size_x": 12, "size_z": 4,
    "facing": "east_west",
    "ground_y": -60,
    "priority": "P2",
}

SWING = {  # 13. 秋千 — 移入太湖石区域附近
    "name": "秋千",
    "cx": 76, "cz": 8,         # v3: cx=65,cz=14 → v4: cx=76,cz=8
    "size_x": 3, "size_z": 3,
    "facing": None,
    "ground_y": -58,
    "priority": "P2",
}

TAIHU_ROCKS = {  # 14. 太湖石组 — 东移
    "name": "太湖石组",
    "cx": 80, "cz": 10,        # v3: cx=70 → v4: cx=80
    "size_x": 15, "size_z": 10,
    "facing": None,
    "ground_y": -57,
    "priority": "P1",
}

PLUM_TREE = {  # 15. 大梅树 — 上移西移，远离梅花庵观
    "name": "大梅树",
    "x": 6, "z": 4,            # v3: x=10,z=10 → v4: x=6,z=4
    "ground_y": -60,
    "priority": "P2",
}

PAINTED_BOAT = {  # 16. 画船 — 不变
    "name": "画船",
    "cx": 36, "cz": 38,
    "size_x": 4, "size_z": 10,
    "facing": "north_south",
    "ground_y": WATER_SURFACE_Y,
    "priority": "P2",
}

STONE_BOAT = {  # 17. 石舫 — 微调避开半亭和曲廊亭
    "name": "石舫",
    "cx": 85, "cz": 46,        # v3: cx=84,cz=48 → v4: cx=85,cz=46
    "size_x": 5, "size_z": 12,
    "facing": "north_south",
    "ground_y": -60,
    "over_water": True,
    "priority": "P2",
}

PLUM_HERMITAGE = {  # 18. 梅花庵观 — 微调
    "name": "梅花庵观",
    "cx": 10, "cz": 13,        # v3: cz=12 → v4: cz=13
    "size_x": 7, "size_z": 7,
    "facing": "south",
    "ground_y": -60,
    "pillar_h": 4,
    "priority": "P2",
}

GUI_SHU = {  # 19. 闺塾/书房 — 不变
    "name": "闺塾",
    "cx": 22, "cz": 78,
    "size_x": 9, "size_z": 7,
    "facing": "east",
    "ground_y": -60,
    "pillar_h": 5,
    "priority": "P2",
}

# 建筑总列表（按优先级排序）
ALL_BUILDINGS = [
    PEONY_PAVILION, PEONY_RAIL,                          # P0
    CUI_XUAN, CHI_GUAN, ZHUO_YING, YUAN_XIANG,          # P1
    GATE, COURTYARD, TAIHU_ROCKS,                        # P1
    HALF_PAVILION_SE, CORRIDOR_PAVILION_E, TING_YU_XUAN, # P2
    TUMI_TRELLIS, SWING, PLUM_TREE, PAINTED_BOAT,        # P2
    STONE_BOAT, PLUM_HERMITAGE, GUI_SHU,                 # P2
]

# 允许碰撞的建筑对（同一建筑群或有意邻近）
ALLOWED_COLLISION_PAIRS = [
    ("入口门厅", "小庭深院"),    # 入口序列一体化
    ("太湖石组", "秋千"),        # 秋千嵌入太湖石区域
]

# ═══════════════════════════════════════════
# 三、廊道网络 — 跟随建筑坐标调整
# ═══════════════════════════════════════════

# 主环路（有顶曲廊，宽5格）— C形环绕主湖
MAIN_CORRIDOR = {
    "width": 5,
    "pillar_h": 4,
    "pillar_space": 4,
    "roofed": True,
    "waypoints": [
        # 南段（入口→远香堂→东岸）
        (58, 80),   # L1: 小庭深院北端 (v3同)
        (58, 67),   # L2: 远香堂 (v3: 72 → v4: 67)
        (74, 63),   # L3: 东南转角 (v3: 65 → v4: 63)
        (88, 62),   # L4: 半亭(东南) (v3: 82,58 → v4: 88,62)
        (88, 48),   # L5: 石舫旁 (v3: 88,48 同)
        (96, 42),   # L6: 曲廊亭(东) (v3: 92,42 → v4: 96,42)
        (90, 34),   # L7: 东岸转角 (不变)
        (86, 28),   # L8: 东北角 (不变)
    ],
}

# 西段主廊（翠轩向南到远香堂）
WEST_CORRIDOR = {
    "width": 5,
    "pillar_h": 4,
    "pillar_space": 4,
    "roofed": True,
    "waypoints": [
        (22, 28),   # L9: 翠轩东廊 (不变)
        (22, 38),   # L10: 向南 (不变)
        (25, 48),   # L11: 转角 (不变)
        (30, 54),   # L12: 转角 (v3: 56 → v4: 54, 跟听雨轩)
        (34, 56),   # L13: 听雨轩旁 (v3: 38,60 → v4: 34,56)
        (44, 60),   # L14: 向东 (v3: 46,62 → v4: 44,60)
        (50, 64),   # L15: 远香堂西侧 (v3: 52,68 → v4: 50,64)
        (58, 67),   # 回到L2闭合 (v3: 72 → v4: 67)
    ],
}

# 北岸假山石径（无顶，3格宽）
HIGHLAND_PATH = {
    "width": 3,
    "roofed": False,
    "surface": "stone_bricks",
    "waypoints": [
        (86, 28),   # 从主廊L8出发 (不变)
        (84, 26),   # 濯缨水阁附近 (v3: 80,24 → v4: 84,26)
        (82, 26),   # 濯缨水阁 (v3: 75,20 → v4: 82,26)
        (80, 18),   # (v3: 70,18 → v4: 80,18)
        (80, 12),   # 太湖石 (v3: 70,12 → v4: 80,12)
        (72, 10),   # (v3: 65,10 → v4: 72,10)
        (58, 8),    # 牡丹亭 (v3: 58,10 → v4: 58,8)
        (52, 18),   # (v3: 55,16 → v4: 52,18)
        (50, 22),   # 芍药阑旁 (v3: 55,18 → v4: 50,22)
        (42, 22),   # (v3: 48,23 → v4: 42,22)
        (38, 24),   # (v3: 42,24 → v4: 38,24)
        (34, 24),   # 池馆旁 (v3: 38,26 → v4: 34,24)
        (28, 26),   # (v3: 30,27 → v4: 28,26)
        (22, 28),   # 到翠轩 (不变)
    ],
}

# ═══════════════════════════════════════════
# 四、次路径（石径，2格宽）
# ═══════════════════════════════════════════

SECONDARY_PATHS = [
    {
        "name": "入口轴线",
        "width": 5,
        "waypoints": [(58, 90), (58, 87), (58, 80), (58, 67)],
        "surface": "stone_bricks",
    },
    {
        "name": "梅花小径",
        "width": 2,
        "waypoints": [(16, 28), (14, 22), (10, 16), (8, 10), (6, 4)],
        "surface": "dirt_path",
    },
    {
        "name": "闺塾径",
        "width": 2,
        "waypoints": [(58, 87), (48, 82), (38, 80), (28, 78), (22, 78)],
        "surface": "dirt_path",
    },
    {
        "name": "荼蘼径",
        "width": 2,
        "waypoints": [(50, 56), (46, 56), (38, 56), (34, 54)],
        "surface": "dirt_path",
    },
]

# ═══════════════════════════════════════════
# 五、水上通道 — 位置跟随建筑微调
# ═══════════════════════════════════════════

MAIN_BRIDGE = {
    "name": "主廊桥",
    "cx": 58, "z_start": 38, "z_end": 50,
    "width": 5,
    "arches": 3,
    "bridge_type": "stone_arch",
}

ZIGZAG_BRIDGE = {
    "name": "九曲桥",
    "waypoints": [(38, 22), (40, 20), (43, 21), (45, 19)],
    "width": 3,
    "bridge_type": "zigzag",
}

STEPPING_STONES = {
    "name": "汀步石",
    "stones": [(19, 13), (20, 14), (21, 13)],
}

SMALL_BRIDGE = {
    "name": "小石桥",
    "cx": 86, "z_start": 14, "z_end": 18,
    "width": 3,
    "arches": 1,
    "bridge_type": "stone_arch",
}

ALL_BRIDGES = [MAIN_BRIDGE, ZIGZAG_BRIDGE, STEPPING_STONES, SMALL_BRIDGE]

# ═══════════════════════════════════════════
# 六、围墙 — 不变
# ═══════════════════════════════════════════

WALL = {
    "height": 5,
    "perimeter": [
        (0, 0), (120, 0), (120, 90), (0, 90),
    ],
    "moon_gates": [
        {"wall": "east", "z": 40, "radius": 3},
    ],
    "south_gap": (50, 66),
    "lattice_windows": [
        {"wall": "east", "z": 20},
        {"wall": "east", "z": 60},
        {"wall": "west", "z": 30},
        {"wall": "west", "z": 50},
        {"wall": "north", "x": 30},
        {"wall": "north", "x": 90},
    ],
}

# ═══════════════════════════════════════════
# 七、入口
# ═══════════════════════════════════════════

ENTRANCE = {
    "position": (58, 90),
    "facing": "south",
    "screen_wall": {
        "cx": 58, "cz": 78,    # 影壁位于小庭深院北侧
        "width": 9, "height": 4,
    },
}

# ═══════════════════════════════════════════
# 八、地形高程区
# ═══════════════════════════════════════════

TERRAIN_ZONES = [
    {
        "name": "北侧假山高地",
        "x_range": (45, 95),     # v3: (45,85) → v4: 扩大到95，覆盖太湖石新位
        "z_range": (0, 20),
        "ground_y": -57,
        "slope": {
            "z_start": 12, "z_end": 22,
            "y_start": -57, "y_end": -60,
        },
    },
    {
        "name": "东北假山",
        "x_range": (85, 105), "z_range": (0, 22),
        "ground_y": -57,
    },
    {
        "name": "标准地面",
        "x_range": (0, 120), "z_range": (20, 90),
        "ground_y": -60,
    },
]

# ═══════════════════════════════════════════
# 九、景观元素 — 微调避开新建筑位置
# ═══════════════════════════════════════════

WILLOWS = [
    (26, 36),   # 曲水旁 (不变)
    (34, 50),   # 西岸廊道旁 (v3: 38,54 → v4: 34,50 避开听雨轩)
    (70, 58),   # 东南岸 (不变)
    (78, 36),   # 东岸 (不变)
    (50, 60),   # 南岸 (v3: 50,62 → v4: 50,60)
]

FLOWER_CLUSTERS = [
    (30, 48),   # 西岸花木 (不变)
    (65, 56),   # 东南花木 (不变)
    (45, 32),   # 湖西 (不变)
    (80, 44),   # 东岸 (不变)
    (20, 18),   # 曲水旁 (不变)
]

WELLS = [
    (95, 55),
    (15, 50),
    (45, 4),    # v3: (45,8) → v4: z=4 避开假山建筑
]

LILY_PADS = [
    (38, 34),
    (36, 40),
    (55, 48),
    (70, 44),
    (14, 28),
]

PLUM_TREE_POS = {"x": 6, "z": 4, "ground_y": -60}

# ═══════════════════════════════════════════
# 十、游线定义 — 坐标跟随建筑更新
# ═══════════════════════════════════════════

MAIN_TOUR = {
    "name": "杜丽娘游园路线",
    "stops": [
        ("入口", 58, 90),
        ("小庭深院", 58, 80),
        ("荼蘼花架", 50, 53),       # v3: (48,68) → v4
        ("听雨轩", 34, 54),         # v3: (40,58) → v4
        ("翠轩", 16, 28),
        ("曲水/曲桥", 40, 20),
        ("太湖石", 80, 10),          # v3: (70,12) → v4
        ("牡丹亭", 58, 8),           # v3: (58,10) → v4
        ("芍药阑", 50, 26),          # v3: (58,22) → v4
        ("池馆", 34, 20),            # v3: (55,18) → v4
        ("主廊桥", 58, 44),
        ("远香堂", 58, 67),          # v3: (58,72) → v4
        ("回入口", 58, 90),
    ],
}

PLUM_DETOUR = {
    "name": "寻梦支线（大梅树方向）",
    "stops": [
        ("翠轩", 16, 28),
        ("梅花庵观", 10, 13),        # v3: (12,12) → v4
        ("大梅树", 6, 4),            # v3: (10,10) → v4
    ],
}
