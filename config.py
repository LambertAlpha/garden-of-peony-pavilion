"""v3 全局配置 — 坐标、尺寸、版本参数的单一真相源"""

VERSION = "v3"

# ── 园林范围 ──
GARDEN = {"x_min": 0, "x_max": 120, "z_min": 0, "z_max": 90}

# ── Y 坐标 ──
GROUND_Y = -61      # 草方块层
BUILD_Y = -60       # 建筑起始层（地面上第一格空气）

# ── 牡丹亭 (四角攒尖) ──
PAVILION = {
    "cx": 78, "cz": 15,
    "r_base": 8,        # 底座半径 → 17×17
    "r_col": 5,         # 柱间半径 → 11×11, 内部净空 9×9
    "pillar_h": 6,
    "ground_y": -57,    # 北侧高地地面
}

# ── 芍药阑 ──
PEONY_RAIL = {
    "cx": 78, "cz": 29,
    "hx": 5, "hz": 4,   # 11×9 围栏
    "ground_y": -58,
}

# ── 翠轩/池馆 (悬山顶) ──
HALL = {
    "cx": 16, "cz": 35,
    "width_x": 17, "width_z": 11,
    "pillar_h": 6,
    "ground_y": BUILD_Y,
}

# ── 太湖石 ──
TAIHU_ROCKS = {
    "cx": 45, "cz": 12,
    "ground_y": -57,
}

# ── 秋千 ──
SWING = {
    "cx": 62, "cz": 25,
    "ground_y": -59,
}

# ── 入口区 ──
GATE_AREA = {
    "cx": 55, "cz": 80,
    "gate_width": 5,
    "court_width": 16, "court_depth": 10,
    "ground_y": BUILD_Y,
}

# ── 池塘 ──
POND = {
    "cx": 52, "cz": 45,
    "rx": 23, "rz": 12,    # 椭圆半轴
    "depth": 3,
}

# ── 围墙 ──
WALL = {
    "height": 5,            # 墙基1+墙身3+压瓦1
    "moon_gate_radius": 3,
    "moon_gate_wall": "east",
    "moon_gate_pos": 45,
    "south_gap": (48, 62),  # 南墙入口缺口 X 范围
}

# ── 曲廊 ──
CORRIDOR = {
    "width": 5,
    "pillar_h": 4,
    "pillar_space": 4,
    "waypoints": [
        (55, 68),   # A: 入口北端
        (28, 68),   # B: 向西到池塘西南
        (28, 50),   # C: 向北（翠轩东侧）
        (28, 35),   # D: 继续北走（翠轩侧门从此处向西进入）
        (28, 20),   # E: 向东北
        (55, 20),   # F: 继续东
        (70, 20),   # G: 接近牡丹亭
        (70, 15),   # H: 转向牡丹亭
    ],
}

# ── 廊桥 ──
BRIDGE = {
    "cx": 45, "z_start": 35, "z_end": 55,
    "width": 5,
}

# ── 画船 ──
BOAT = {
    "cx": 25, "cz": 42,  # 翠轩东侧水面
}

# ── 大梅树 ──
PLUM_TREE = {"x": 10, "z": 10}

# ── 景观花丛中心点 ──
FLOWER_CLUSTERS = [
    (35, 60), (80, 35), (10, 55), (90, 50), (8, 20),
]

# ── 垂杨位置 ──
WILLOWS = [
    (20, 50), (75, 55), (65, 30), (18, 28),
]

# ── 断井位置 ──
WELLS = [
    (90, 60), (95, 15), (10, 55),
]
