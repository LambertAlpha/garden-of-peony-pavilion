"""v3 材质映射表 — 基于参考项目调研修订

v2→v3 变更:
- 柱子: stripped_acacia → stripped_crimson_stem (红漆柱，原版最佳)
- 屋顶: deepslate_tile → stone_brick (灰瓦) + smooth_red_sandstone (暖瓦)
- 飞檐外层: dark_oak (深色橡木包裹翘角，参考网易茶亭教程)
- 柱础: stone_slab → polished_andesite (磨制安山岩)
- 栏杆: acacia_fence → crimson_fence (配套绯红木)
"""

PALETTE = {
    # ── 柱梁 ──
    "pillar":       "minecraft:stripped_crimson_stem",
    "beam":         "minecraft:dark_oak_planks",
    "beam_log":     "minecraft:dark_oak_log",

    # ── 屋顶(灰瓦 — 江南"粉墙黛瓦") ──
    "roof":         "minecraft:stone_brick_stairs",
    "roof_slab":    "minecraft:stone_brick_slab",
    "roof_block":   "minecraft:stone_bricks",

    # ── 屋顶(暖瓦 — 重要建筑点缀) ──
    "roof_warm":    "minecraft:smooth_red_sandstone_stairs",
    "roof_warm_slab": "minecraft:smooth_red_sandstone_slab",
    "roof_warm_block": "minecraft:smooth_red_sandstone",

    # ── 飞檐外层(翘角包裹) ──
    "eave_outer":   "minecraft:dark_oak_stairs",
    "eave_slab":    "minecraft:dark_oak_slab",

    # ── 墙体 ──
    "wall":         "minecraft:white_concrete",
    "wall_base":    "minecraft:stone_bricks",
    "wall_cap":     "minecraft:stone_brick_slab",
    "wall_mossy":   "minecraft:mossy_stone_bricks",
    "wall_cracked": "minecraft:cracked_stone_bricks",

    # ── 台基 ──
    "base":         "minecraft:stone_bricks",
    "base_step":    "minecraft:stone_brick_stairs",
    "base_slab":    "minecraft:stone_brick_slab",
    "base_col":     "minecraft:polished_andesite",

    # ── 地面 ──
    "floor":        "minecraft:smooth_stone",
    "floor_alt":    "minecraft:stone_bricks",
    "floor_wood":   "minecraft:spruce_planks",
    "path":         "minecraft:dirt_path",
    "gravel":       "minecraft:gravel",

    # ── 栏杆/门窗 ──
    "rail":         "minecraft:crimson_fence",
    "rail_gate":    "minecraft:crimson_fence_gate",
    "window":       "minecraft:iron_bars",
    "trapdoor":     "minecraft:jungle_trapdoor",
    "door":         "minecraft:crimson_door",

    # ── 水 ──
    "water":        "minecraft:water",
    "clay":         "minecraft:clay",
    "lily":         "minecraft:lily_pad",

    # ── 植物 ──
    "peony":        "minecraft:peony",
    "azalea":       "minecraft:flowering_azalea",
    "rose":         "minecraft:rose_bush",
    "tulip_red":    "minecraft:red_tulip",
    "tulip_pink":   "minecraft:pink_tulip",
    "vine":         "minecraft:vine",
    "moss":         "minecraft:moss_block",
    "moss_carpet":  "minecraft:moss_carpet",
    "tall_grass":   "minecraft:tall_grass",
    "fern":         "minecraft:fern",
    "bamboo":       "minecraft:bamboo",
    "cherry_log":   "minecraft:cherry_log",
    "cherry_leaves": "minecraft:cherry_leaves",
    "oak_leaves":   "minecraft:oak_leaves",
    "oak_log":      "minecraft:oak_log",

    # ── 石景 ──
    "taihu_main":   "minecraft:dripstone_block",
    "taihu_white":  "minecraft:calcite",

    # ── 装饰 ──
    "lantern":      "minecraft:lantern",
    "lightning_rod": "minecraft:lightning_rod",
    "red_wool":     "minecraft:red_wool",
    "red_carpet":   "minecraft:red_carpet",

    # ── 基础 ──
    "air":          "minecraft:air",
    "grass":        "minecraft:grass_block",
    "dirt":         "minecraft:dirt",
    "stone":        "minecraft:stone",
    "cobblestone":  "minecraft:cobblestone",
    "mossy_cobblestone": "minecraft:mossy_cobblestone",
}

GROUND_Y = -61
BUILD_Y = -60
BEDROCK_Y = -64
