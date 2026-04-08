"""材质映射表 — 语义名 → Minecraft 方块ID"""

PALETTE = {
    # 结构
    "pillar":       "minecraft:stripped_acacia_log",       # 去皮金合欢（漆柱）
    "beam":         "minecraft:dark_oak_planks",           # 深色橡木（梁）
    "beam_log":     "minecraft:dark_oak_log",              # 深色橡木原木（粗梁）

    # 屋顶（深板岩瓦片 ≈ 青灰小青瓦）
    "roof":         "minecraft:deepslate_tile_stairs",
    "roof_slab":    "minecraft:deepslate_tile_slab",
    "roof_block":   "minecraft:deepslate_tiles",

    # 墙体
    "wall":         "minecraft:white_concrete",            # 粉墙
    "wall_base":    "minecraft:stone_bricks",              # 墙基
    "wall_cap":     "minecraft:deepslate_tile_slab",       # 墙顶压瓦
    "wall_mossy":   "minecraft:mossy_stone_bricks",        # 做旧墙
    "wall_cracked": "minecraft:cracked_stone_bricks",      # 裂墙

    # 台基
    "base":         "minecraft:stone_bricks",
    "base_step":    "minecraft:stone_brick_stairs",
    "base_slab":    "minecraft:stone_brick_slab",
    "base_col":     "minecraft:stone_slab",                # 柱础

    # 地面
    "floor":        "minecraft:smooth_stone",
    "floor_alt":    "minecraft:stone_bricks",              # 交替铺设
    "path":         "minecraft:dirt_path",                 # 小径
    "gravel":       "minecraft:gravel",

    # 栏杆/门窗
    "rail":         "minecraft:acacia_fence",              # 金合欢栏杆
    "rail_gate":    "minecraft:acacia_fence_gate",
    "window":       "minecraft:iron_bars",                 # 漏窗
    "trapdoor":     "minecraft:jungle_trapdoor",           # 花窗
    "door":         "minecraft:acacia_door",

    # 水
    "water":        "minecraft:water",
    "clay":         "minecraft:clay",                      # 池底
    "lily":         "minecraft:lily_pad",

    # 植物
    "peony":        "minecraft:peony",                     # 芍药/牡丹
    "azalea":       "minecraft:flowering_azalea",          # 杜鹃
    "rose":         "minecraft:rose_bush",                 # 玫瑰丛
    "tulip_red":    "minecraft:red_tulip",
    "tulip_pink":   "minecraft:pink_tulip",
    "vine":         "minecraft:vine",
    "moss":         "minecraft:moss_block",
    "moss_carpet":  "minecraft:moss_carpet",
    "tall_grass":   "minecraft:tall_grass",
    "fern":         "minecraft:fern",
    "bamboo":       "minecraft:bamboo",
    "cherry_log":   "minecraft:cherry_log",
    "cherry_leaves":"minecraft:cherry_leaves",
    "oak_leaves":   "minecraft:oak_leaves",

    # 石景
    "taihu_main":   "minecraft:dripstone_block",           # 太湖石主体
    "taihu_white":  "minecraft:calcite",                   # 太湖石白部
    "taihu_moss":   "minecraft:moss_block",                # 太湖石苔藓

    # 装饰
    "lantern":      "minecraft:lantern",
    "lightning_rod": "minecraft:lightning_rod",             # 宝顶
    "red_wool":     "minecraft:red_wool",                  # 画船顶棚
    "red_carpet":   "minecraft:red_carpet",

    # 基础
    "air":          "minecraft:air",
    "grass":        "minecraft:grass_block",
    "dirt":         "minecraft:dirt",
    "stone":        "minecraft:stone",
}

# 地面常量
GROUND_Y = -61     # 草方块层
BUILD_Y = -60      # 建筑起始层（地面上第一格）
BEDROCK_Y = -64
