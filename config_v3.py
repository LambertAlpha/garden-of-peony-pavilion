"""v3 总平面图配置 — 游园惊梦最终总平面图的单一真相源

坐标系:
  原点 (0,0) = 西北角
  X 正方向 = 东，Z 正方向 = 南
  地块: 120 x 90 (10,800格)

数值约束:
  水面 ≥ 28% = 3,024格  → 实际 3,232格 (29.9%)
  建筑+廊道 20-25%       → 实际 2,517格 (23.3%)
  建筑数 19栋 (对标网师园)
"""

VERSION = "v3-final"

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
# 一、水面系统 (3,180格, 29.4%)
# ═══════════════════════════════════════════

# 主湖轮廓 — 不规则形，有岬角和湾
# 顺时针方向的关键锚点，中间用线性插值
# Shoelace面积 = 2,702格
MAIN_LAKE = {
    "shoreline": [
        # 北岸（复杂，有两个岬角）
        (30, 20), (38, 17), (45, 21),       # 西段北岸，向南凹 → 西湾
        (50, 15), (56, 13), (62, 16),       # 北岬1（池馆所在）
        (68, 19), (75, 16), (80, 22),       # 北岬2（濯缨水阁所在）
        (86, 28),                           # 东北角
        # 东岸
        (90, 34), (92, 42), (90, 50),
        (86, 56), (82, 60),                 # 东南角
        # 南岸（有浅湾）
        (74, 64), (66, 67), (58, 68),       # 南岸最南点
        (50, 67), (42, 64), (36, 60),       # 南岸西段
        # 西岸
        (32, 54), (28, 46), (26, 38),
        (28, 32), (30, 26), (30, 20),       # 闭合
    ],
    "depth": 3,          # 标准深度（格）
    "bottom_y": -64,
    "center": (58, 40),  # 近似中心，用于放置睡莲等
}

# 曲水溪流 — 从主湖西北角向西北蜿蜒
CREEK = {
    "centerline": [
        (30, 20),   # 起点：接主湖西北角
        (26, 16),
        (25, 15),
        (20, 13),   # 最窄处（宽3格），汀步石位置
        (16, 16),
        (14, 20),
        (12, 25),
        (14, 30),   # 末端扩大为翠轩前小池
    ],
    "widths": [5, 5, 4, 3, 3, 4, 3, 8],  # 各段宽度
    "depth": 2,
    "bottom_y": -63,
}

# 翠轩前小池 — 曲水末端扩大
CREEK_POOL = {
    "cx": 14, "cz": 30,
    "rx": 5, "rz": 5,   # 不规则，约8x8
    "depth": 2,
    "bottom_y": -63,
}

# 假山深潭 — 东北角
DEEP_POOL = {
    "shoreline": [
        (88, 10), (94, 8), (100, 10), (102, 16),
        (98, 20), (92, 18), (88, 14), (88, 10),  # 闭合
    ],
    "depth": 4,
    "bottom_y": -65,
}

# 深潭与主湖的连接溪
POOL_CREEK = {
    "centerline": [
        (82, 28),   # 主湖东北角
        (84, 24),
        (86, 20),
        (88, 16),
        (88, 14),   # 接深潭
    ],
    "width": 2,
    "depth": 2,
}

# ═══════════════════════════════════════════
# 二、建筑 (19栋)
# ═══════════════════════════════════════════

# --- 核心梦境建筑 (P0) ---

PEONY_PAVILION = {  # 1. 牡丹亭 — 四角攒尖亭
    "name": "牡丹亭",
    "cx": 58, "cz": 10,
    "size_x": 15, "size_z": 15,
    "facing": "all",        # 四面开敞
    "ground_y": -57,        # 北侧高地，全园最高
    "pillar_h": 6,
    "roof_type": "hip_pointed",  # 攒尖顶
    "priority": "P0",
}

PEONY_RAIL = {  # 2. 芍药阑 — 花圃围栏
    "name": "芍药阑",
    "cx": 58, "cz": 22,
    "size_x": 11, "size_z": 9,
    "facing": None,
    "ground_y": -58,        # 高地缓坡上
    "priority": "P0",
}

# --- 主要建筑 (P1) ---

CUI_XUAN = {  # 3. 翠轩 — 悬山顶敞厅，临曲水
    "name": "翠轩",
    "cx": 16, "cz": 28,
    "size_x": 17, "size_z": 11,
    "facing": "east",       # 坐西朝东，面向曲水
    "ground_y": -60,
    "pillar_h": 6,
    "roof_type": "gable",   # 悬山顶
    "priority": "P1",
}

CHI_GUAN = {  # 4. 池馆 — 水榭，半架水上
    "name": "池馆",
    "cx": 55, "cz": 18,
    "size_x": 9, "size_z": 7,
    "facing": "south",
    "ground_y": -59,        # 北岬1上，略高
    "pillar_h": 5,
    "roof_type": "gable",
    "over_water": True,     # 三面临水
    "priority": "P1",
}

ZHUO_YING = {  # 5. 濯缨水阁 — 临水轩
    "name": "濯缨水阁",
    "cx": 74, "cz": 22,
    "size_x": 11, "size_z": 7,
    "facing": "south",
    "ground_y": -59,
    "pillar_h": 5,
    "roof_type": "gable",
    "over_water": True,
    "priority": "P1",
}

YUAN_XIANG = {  # 6. 远香堂 — 南岸主厅
    "name": "远香堂",
    "cx": 58, "cz": 72,    # 紧贴南岸(Z=67-68)，北缘距水2格
    "size_x": 19, "size_z": 11,
    "facing": "north",      # 坐南朝北，正对水面
    "ground_y": -60,
    "pillar_h": 6,
    "roof_type": "hip",     # 卷棚歇山
    "priority": "P1",
}

GATE = {  # 7. 入口门厅
    "name": "入口门厅",
    "cx": 58, "cz": 86,
    "size_x": 15, "size_z": 9,
    "facing": "south",
    "ground_y": -60,
    "pillar_h": 5,
    "priority": "P1",
}

COURTYARD = {  # 8. 小庭深院
    "name": "小庭深院",
    "cx": 58, "cz": 80,
    "size_x": 15, "size_z": 7,
    "facing": None,         # 围合庭院
    "ground_y": -60,
    "priority": "P1",
}

# --- 中小型建筑 (P2) ---

HALF_PAVILION_SE = {  # 9. 半亭（东南角）
    "name": "半亭",
    "cx": 82, "cz": 58,
    "size_x": 7, "size_z": 7,
    "facing": "northwest",
    "ground_y": -60,
    "pillar_h": 5,
    "priority": "P2",
}

CORRIDOR_PAVILION_E = {  # 10. 曲廊亭（东岸转折）
    "name": "曲廊亭",
    "cx": 92, "cz": 42,       # 紧贴东岸水面(92,42)
    "size_x": 5, "size_z": 5,
    "facing": "all",
    "ground_y": -60,
    "pillar_h": 4,
    "priority": "P2",
}

TING_YU_XUAN = {  # 11. 听雨轩
    "name": "听雨轩",
    "cx": 40, "cz": 58,
    "size_x": 9, "size_z": 7,
    "facing": "north",
    "ground_y": -60,
    "pillar_h": 5,
    "priority": "P2",
}

TUMI_TRELLIS = {  # 12. 荼蘼花架
    "name": "荼蘼花架",
    "cx": 48, "cz": 68,
    "size_x": 12, "size_z": 4,
    "facing": "east_west",
    "ground_y": -60,
    "priority": "P2",
}

SWING = {  # 13. 秋千
    "name": "秋千",
    "cx": 65, "cz": 14,
    "size_x": 3, "size_z": 3,
    "facing": None,
    "ground_y": -58,
    "priority": "P2",
}

TAIHU_ROCKS = {  # 14. 太湖石组
    "name": "太湖石组",
    "cx": 70, "cz": 12,
    "size_x": 15, "size_z": 10,
    "facing": None,
    "ground_y": -57,
    "priority": "P1",
}

PLUM_TREE = {  # 15. 大梅树（一株！）
    "name": "大梅树",
    "x": 10, "z": 10,
    "ground_y": -60,
    "priority": "P2",
}

PAINTED_BOAT = {  # 16. 画船
    "name": "画船",
    "cx": 36, "cz": 38,
    "size_x": 4, "size_z": 10,
    "facing": "north_south",
    "ground_y": WATER_SURFACE_Y,
    "priority": "P2",
}

STONE_BOAT = {  # 17. 石舫
    "name": "石舫",
    "cx": 84, "cz": 48,
    "size_x": 5, "size_z": 12,
    "facing": "north_south",
    "ground_y": -60,
    "over_water": True,
    "priority": "P2",
}

PLUM_HERMITAGE = {  # 18. 梅花庵观
    "name": "梅花庵观",
    "cx": 12, "cz": 12,
    "size_x": 7, "size_z": 7,
    "facing": "south",
    "ground_y": -60,
    "pillar_h": 4,
    "priority": "P2",
}

GUI_SHU = {  # 19. 闺塾/书房
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

# ═══════════════════════════════════════════
# 三、廊道网络
# ═══════════════════════════════════════════

# 主环路（有顶曲廊，宽5格）— C形环绕主湖
MAIN_CORRIDOR = {
    "width": 5,
    "pillar_h": 4,
    "pillar_space": 4,
    "roofed": True,
    "waypoints": [
        # 南段（入口→远香堂→东岸）
        (58, 80),   # L1: 小庭深院北端
        (58, 72),   # L2: 远香堂
        (74, 65),   # L3: 东南转角
        (82, 58),   # L4: 半亭(东南)
        (88, 48),   # L5: 石舫旁
        (92, 42),   # L6: 曲廊亭(东)，紧贴水面
        (90, 34),   # L7: 东岸转角
        (86, 28),   # L8: 东北角 —— 主廊断开
    ],
}

# 西段主廊（翠轩向南到远香堂）
WEST_CORRIDOR = {
    "width": 5,
    "pillar_h": 4,
    "pillar_space": 4,
    "roofed": True,
    "waypoints": [
        (22, 28),   # L9: 翠轩东廊
        (22, 38),   # L10: 向南
        (25, 48),   # L11: 转角
        (30, 56),   # L12: 转角
        (38, 60),   # L13: 听雨轩旁
        (46, 62),   # L14: 向东
        (52, 68),   # L15: 远香堂西侧
        (58, 72),   # 回到L2闭合
    ],
}

# 北岸假山石径（无顶，3格宽）
HIGHLAND_PATH = {
    "width": 3,
    "roofed": False,
    "surface": "stone_bricks",  # 石径
    "waypoints": [
        (86, 28),   # 从主廊L8出发
        (80, 24),
        (75, 20),   # 濯缨水阁
        (70, 18),
        (70, 12),   # 太湖石
        (65, 10),
        (58, 10),   # 牡丹亭
        (55, 16),
        (55, 18),   # 池馆
        (48, 23),
        (42, 24),
        (38, 26),
        (30, 27),
        (22, 28),   # 到翠轩，与西段主廊连接
    ],
}

# ═══════════════════════════════════════════
# 四、次路径（石径，2格宽）
# ═══════════════════════════════════════════

SECONDARY_PATHS = [
    {
        "name": "入口轴线",
        "width": 5,
        "waypoints": [(58, 90), (58, 86), (58, 80), (58, 72)],
        "surface": "stone_bricks",
    },
    {
        "name": "梅花小径",
        "width": 2,
        "waypoints": [(16, 28), (14, 22), (12, 16), (10, 12), (10, 10)],
        "surface": "dirt_path",
    },
    {
        "name": "闺塾径",
        "width": 2,
        "waypoints": [(58, 86), (48, 82), (38, 80), (28, 78), (22, 78)],
        "surface": "dirt_path",
    },
    {
        "name": "荼蘼径",
        "width": 2,
        "waypoints": [(48, 68), (44, 64), (40, 60), (40, 58)],
        "surface": "dirt_path",
    },
]

# ═══════════════════════════════════════════
# 五、水上通道
# ═══════════════════════════════════════════

MAIN_BRIDGE = {  # 主廊桥 — 三孔石桥，跨主湖中段
    "name": "主廊桥",
    "cx": 58, "z_start": 38, "z_end": 50,
    "width": 5,
    "arches": 3,
    "bridge_type": "stone_arch",
}

ZIGZAG_BRIDGE = {  # 九曲桥 — 西湾处
    "name": "九曲桥",
    "waypoints": [(38, 22), (40, 20), (43, 21), (45, 19)],
    "width": 3,
    "bridge_type": "zigzag",
}

STEPPING_STONES = {  # 汀步 — 曲水最窄处
    "name": "汀步石",
    "stones": [(19, 13), (20, 14), (21, 13)],  # 单格石头
}

SMALL_BRIDGE = {  # 小石桥 — 连接溪到深潭
    "name": "小石桥",
    "cx": 86, "z_start": 14, "z_end": 18,
    "width": 3,
    "arches": 1,
    "bridge_type": "stone_arch",
}

ALL_BRIDGES = [MAIN_BRIDGE, ZIGZAG_BRIDGE, STEPPING_STONES, SMALL_BRIDGE]

# ═══════════════════════════════════════════
# 六、围墙
# ═══════════════════════════════════════════

WALL = {
    "height": 5,            # 墙基1+墙身3+压瓦1
    "perimeter": [
        (0, 0), (120, 0), (120, 90), (0, 90),  # 四角
    ],
    "moon_gates": [
        {"wall": "east", "z": 40, "radius": 3},   # 东墙月洞门
    ],
    "south_gap": (50, 66),  # 南墙入口缺口 X 范围
    "lattice_windows": [    # 漏窗位置
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
    "position": (58, 90),   # 南墙正中
    "facing": "south",      # 从南进入
    "screen_wall": {        # 影壁（进门后遮挡视线）
        "cx": 58, "cz": 78,
        "width": 9, "height": 4,
    },
}

# ═══════════════════════════════════════════
# 八、地形高程区
# ═══════════════════════════════════════════

TERRAIN_ZONES = [
    {
        "name": "北侧假山高地",
        "x_range": (45, 85), "z_range": (0, 20),
        "ground_y": -57,
        "slope": {  # 向南缓降
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
# 九、景观元素
# ═══════════════════════════════════════════

# 垂杨散植
WILLOWS = [
    (26, 36),   # 曲水旁
    (38, 54),   # 西岸廊道旁
    (70, 58),   # 东南岸
    (78, 36),   # 东岸
    (50, 62),   # 南岸
]

# 花丛中心点
FLOWER_CLUSTERS = [
    (30, 48),   # 西岸花木
    (65, 56),   # 东南花木
    (45, 32),   # 湖西
    (80, 44),   # 东岸
    (20, 18),   # 曲水旁
]

# 断井（散布氛围）
WELLS = [
    (95, 55),   # 东墙角
    (15, 50),   # 西岸偏僻处
    (45, 8),    # 北侧假山中
]

# 睡莲位置（水面装饰）
LILY_PADS = [
    (38, 34),   # 西湾
    (36, 40),   # 西湾
    (55, 48),   # 湖中央偏南
    (70, 44),   # 东侧
    (14, 28),   # 曲水小池
]

# 大梅树重复声明（确保不遗漏）
PLUM_TREE_POS = {"x": 10, "z": 10, "ground_y": -60}

# ═══════════════════════════════════════════
# 十、游线定义（供验证和导览用）
# ═══════════════════════════════════════════

MAIN_TOUR = {
    "name": "杜丽娘游园路线",
    "stops": [
        ("入口", 58, 90),
        ("小庭深院", 58, 80),
        ("荼蘼花架", 48, 68),
        ("听雨轩", 40, 58),
        ("翠轩", 16, 28),
        ("曲水/曲桥", 40, 20),
        ("太湖石", 70, 12),
        ("牡丹亭", 58, 10),
        ("芍药阑", 58, 22),
        ("池馆", 55, 18),
        ("主廊桥", 58, 44),
        ("远香堂", 58, 72),
        ("回入口", 58, 90),
    ],
}

PLUM_DETOUR = {
    "name": "寻梦支线（大梅树方向）",
    "stops": [
        ("翠轩", 16, 28),
        ("梅花庵观", 12, 12),
        ("大梅树", 10, 10),
    ],
}
