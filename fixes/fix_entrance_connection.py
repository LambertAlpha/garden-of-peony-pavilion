"""修复入口门厅 ←→ 小庭深院 ←→ 影壁 的衔接问题

问题诊断:
  GATE (入口门厅): cx=58, cz=86, 15x9  => X:51~65, Z:82~90
  COURTYARD (小庭深院): cx=58, cz=80, 15x7 => X:51~65, Z:77~83
  影壁: cx=58, cz=78, w=9             => X:54~62, Z=78

  1. 门厅北界 Z=82 与小庭南界 Z=83 重叠 (Z=82~83 双方都写了墙/地面)
  2. 门厅门洞仅 3格宽 (cx-1 ~ cx+1), 作为主入口太窄
  3. 影壁 Z=78 位于小庭内部, 两侧通道不够宽

修复方案:
  1. 清除重叠区 Z=82~83 的所有建筑 (从地面到屋顶)
  2. Z=82~83 铺露天石板过渡路 (2格宽过渡带)
  3. 在门厅北墙 Z=84 开 5格宽门洞 (替换原来 Z=82 处的窄门)
  4. 在小庭南墙 Z=81 开 5格宽入口 (替换原来 Z=83 处的窄入口)
  5. 影壁从 Z=78 移到 Z=79 (小庭中心偏南), 确保两侧≥3格通道
  6. 从影壁绕行路到荼蘼花架方向铺接地石板

坐标参照 (修复后):
  门厅有效空间: Z=84~90, 北墙在 Z=84, 门洞 cx-2 ~ cx+2
  过渡石板路:    Z=82~83, X=51~65 (露天, 两侧矮墙引导)
  小庭有效空间: Z=77~81, 南墙在 Z=81, 入口 cx-2 ~ cx+2
  影壁新位置:    Z=79, X=54~62 (小庭中心)
  影壁两侧通道: 西侧 X=51~53 (3格), 东侧 X=63~65 (3格)

用法:
    from fixes.fix_entrance_connection import fix_entrance_connection
    fix_entrance_connection(b)
"""

import sys
sys.path.insert(0, '/Users/lambertlin/minecraft-server/scripts')

from blocks import PALETTE, BUILD_Y
import config_v3 as cfg


# ══════════════════════════════════════════════════════════════
#  材质常量
# ══════════════════════════════════════════════════════════════

AIR         = PALETTE["air"]
WALL_BLOCK  = PALETTE["wall"]           # white_concrete
WALL_BASE   = PALETTE["wall_base"]      # stone_bricks
WALL_CAP    = PALETTE["wall_cap"]       # stone_brick_slab
STONE_BRICK = PALETTE["base"]           # stone_bricks
FLOOR       = PALETTE["floor"]          # smooth_stone
FLOOR_ALT   = PALETTE["floor_alt"]      # stone_bricks
BASE_COL    = PALETTE["base_col"]       # polished_andesite
BEAM        = PALETTE["beam"]           # dark_oak_planks
BEAM_LOG    = PALETTE["beam_log"]       # dark_oak_log
LANTERN     = PALETTE["lantern"]        # lantern
PILLAR      = PALETTE["pillar"]         # stripped_crimson_stem


def _slab(block_base, stype="bottom"):
    return f"{block_base}[type={stype}]"


def _stair(block_base, facing, half="bottom"):
    return f"{block_base}[facing={facing},half={half}]"


# ══════════════════════════════════════════════════════════════
#  关键坐标 (从 config_v3 推导)
# ══════════════════════════════════════════════════════════════

# 门厅原始范围
GATE_X1, GATE_Z1, GATE_X2, GATE_Z2 = 51, 82, 65, 90
GATE_CX = cfg.GATE["cx"]   # 58
GY = BUILD_Y               # -60

# 小庭原始范围
COURT_X1, COURT_Z1, COURT_X2, COURT_Z2 = 51, 77, 65, 83

# 影壁原始参数
SW = cfg.ENTRANCE["screen_wall"]
SW_CX = SW["cx"]            # 58
SW_OLD_CZ = SW["cz"]        # 78
SW_NEW_CZ = 79              # 新位置: 小庭中心
SW_HALF_W = SW["width"] // 2  # 4
SW_HEIGHT = SW["height"]    # 4

# 修复后的关键 Z 坐标
GATE_NEW_NORTH_WALL_Z = 84  # 门厅北墙新位置
TRANSITION_Z1 = 82          # 过渡带南端
TRANSITION_Z2 = 83          # 过渡带北端
COURT_NEW_SOUTH_WALL_Z = 81 # 小庭南墙新位置

# 门洞半宽 (5格总宽 = cx-2 ~ cx+2)
DOOR_HALF = 2

# 通用尺寸
CX = GATE_CX  # 58 — 中轴线


# ══════════════════════════════════════════════════════════════
#  1. 清除重叠区域
# ══════════════════════════════════════════════════════════════

def _clear_overlap_zone(b):
    """清除 Z=81~84 区域从地面到 Y=-50 的所有方块

    范围解释:
      Z=81: 将成为小庭新南墙 (需要重建)
      Z=82~83: 重叠区 (门厅/小庭都写过, 全部清除)
      Z=84: 将成为门厅新北墙 (需要重建)
    """
    print("  [1/6] 清除重叠区 Z=81~84...")
    # 清除范围: X=50~66 (比建筑宽1格, 清除散水/台基边缘)
    # Y: 从地面 GY 到屋顶以上 GY+15
    b.fill(50, GY, 81, 66, GY + 15, 84, AIR)
    print(f"    清除完成. Commands: {b.cmd_count}")


# ══════════════════════════════════════════════════════════════
#  2. 铺设过渡石板路 (Z=82~83)
# ══════════════════════════════════════════════════════════════

def _build_transition_path(b):
    """在 Z=82~83 铺设露天石板过渡路

    这段是从门厅通往小庭的开放空间, 两侧有矮墙引导视线。
    地面用石砖+磨光安山岩条纹, 与两侧建筑地面一致。
    """
    print("  [2/6] 铺设过渡石板路 Z=82~83...")

    x1, x2 = COURT_X1, COURT_X2  # 51~65, 与两侧建筑等宽

    # 台基层 (与建筑台基齐平)
    b.fill(x1, GY, TRANSITION_Z1, x2, GY, TRANSITION_Z2, STONE_BRICK)

    # 地面层 — 条纹铺装 (与小庭一致)
    # Z=82: 主地面
    b.fill(x1, GY + 1, 82, x2, GY + 1, 82, FLOOR)
    # Z=83: 条纹行
    b.fill(x1, GY + 1, 83, x2, GY + 1, 83, BASE_COL)

    # 两侧矮墙引导 (高2格, 仅在门洞外侧)
    # 西侧矮墙: X=51
    b.fill(x1, GY + 1, TRANSITION_Z1, x1, GY + 2, TRANSITION_Z2, WALL_BLOCK)
    # 东侧矮墙: X=65
    b.fill(x2, GY + 1, TRANSITION_Z1, x2, GY + 2, TRANSITION_Z2, WALL_BLOCK)
    # 矮墙顶压瓦
    b.setblock(x1, GY + 3, 82, _slab(WALL_CAP, "bottom"))
    b.setblock(x1, GY + 3, 83, _slab(WALL_CAP, "bottom"))
    b.setblock(x2, GY + 3, 82, _slab(WALL_CAP, "bottom"))
    b.setblock(x2, GY + 3, 83, _slab(WALL_CAP, "bottom"))

    # 灯笼 (过渡路两端, 紧贴矮墙内侧)
    b.setblock(x1 + 1, GY + 2, 82, f"{LANTERN}[hanging=false]")
    b.setblock(x2 - 1, GY + 2, 82, f"{LANTERN}[hanging=false]")

    print(f"    过渡路完成. Commands: {b.cmd_count}")


# ══════════════════════════════════════════════════════════════
#  3. 重建门厅北墙 (Z=84) — 5格宽门洞
# ══════════════════════════════════════════════════════════════

def _rebuild_gate_north_wall(b):
    """重建门厅北墙

    原始 build_gate 在 Z=82 (北界) 处造了墙+3格门洞。
    现在北界退到 Z=84, 门洞加宽到 5格 (cx-2 ~ cx+2)。

    同时补回台基和地面在 Z=84 行的缺失。
    """
    print("  [3/6] 重建门厅北墙 Z=84, 门洞5格宽...")

    x1, x2 = GATE_X1, GATE_X2  # 51~65
    z = GATE_NEW_NORTH_WALL_Z   # 84
    floor_y = GY + 1            # -59 (台基顶面, 门厅 platform_h=1)

    # 台基补回
    b.fill(x1, GY, z, x2, GY, z, STONE_BRICK)
    # 地面补回
    b.fill(x1, floor_y, z, x2, floor_y, z, FLOOR)

    # 北墙 — 门框 (dark_oak_planks) 包裹 5格宽门洞
    wall_top = floor_y + 4  # pillar_h=5, 墙高4
    b.fill(x1, floor_y + 1, z, x2, wall_top, z, WALL_BLOCK)

    # 门框 (7格宽, cx-3 ~ cx+3, 含门框柱)
    b.fill(CX - 3, floor_y + 1, z, CX + 3, floor_y + 4, z, BEAM)
    # 门洞 (5格宽 x 3格高)
    b.fill(CX - 2, floor_y + 1, z, CX + 2, floor_y + 3, z, AIR)

    # 门框两侧立柱装饰
    b.setblock(CX - 3, floor_y + 1, z, PILLAR)
    b.setblock(CX - 3, floor_y + 2, z, PILLAR)
    b.setblock(CX - 3, floor_y + 3, z, PILLAR)
    b.setblock(CX + 3, floor_y + 1, z, PILLAR)
    b.setblock(CX + 3, floor_y + 2, z, PILLAR)
    b.setblock(CX + 3, floor_y + 3, z, PILLAR)

    print(f"    门厅北墙完成. Commands: {b.cmd_count}")


# ══════════════════════════════════════════════════════════════
#  4. 重建小庭南墙 (Z=81) — 5格宽入口
# ══════════════════════════════════════════════════════════════

def _rebuild_courtyard_south_wall(b):
    """重建小庭深院南墙

    原始 build_courtyard 在 Z=83 (南界) 处造了墙, 入口 cx-2~cx+2 = 5格。
    但那行被门厅覆盖了。现在南墙退到 Z=81, 保留5格宽入口。
    """
    print("  [4/6] 重建小庭南墙 Z=81, 入口5格宽...")

    x1, x2 = COURT_X1, COURT_X2  # 51~65
    z = COURT_NEW_SOUTH_WALL_Z    # 81
    wall_h = 3                    # 小庭围墙高度

    # 台基
    b.fill(x1, GY, z, x2, GY, z, STONE_BRICK)
    # 地面
    b.fill(x1, GY + 1, z, x2, GY + 1, z, FLOOR)

    # 南墙 (留5格入口: cx-2 ~ cx+2)
    b.fill(x1, GY + 1, z, CX - 3, GY + wall_h, z, WALL_BLOCK)
    b.fill(CX + 3, GY + 1, z, x2, GY + wall_h, z, WALL_BLOCK)

    # 墙顶压瓦
    b.fill(x1, GY + wall_h + 1, z, CX - 3, GY + wall_h + 1, z,
           _slab(WALL_CAP, "bottom"))
    b.fill(CX + 3, GY + wall_h + 1, z, x2, GY + wall_h + 1, z,
           _slab(WALL_CAP, "bottom"))

    # 入口两侧灯笼
    b.setblock(CX - 3, GY + 2, z, f"{LANTERN}[hanging=false]")
    b.setblock(CX + 3, GY + 2, z, f"{LANTERN}[hanging=false]")

    print(f"    小庭南墙完成. Commands: {b.cmd_count}")


# ══════════════════════════════════════════════════════════════
#  5. 重建影壁 (移到 Z=79, 确保两侧≥3格通道)
# ══════════════════════════════════════════════════════════════

def _rebuild_screen_wall(b):
    """重建影壁

    原位置 Z=78, 在小庭 Z=77~83 内部, 离北墙仅1格。
    新位置 Z=79 (小庭 Z=77~81 的中心):
      - 影壁到北墙(Z=77): 2格通道
      - 影壁到南墙(Z=81): 2格通道
      - 但影壁宽度9格(X=54~62), 两侧到庭墙(X=51/65):
        西侧: 54-51=3格通道 (X=51,52,53 可通行)
        东侧: 65-62=3格通道 (X=63,64,65 可通行)

    先清除旧影壁, 再在新位置重建。
    """
    print("  [5/6] 重建影壁 (Z=78 → Z=79)...")

    # 清除旧影壁 (Z=78)
    old_x1 = SW_CX - SW_HALF_W  # 54
    old_x2 = SW_CX + SW_HALF_W  # 62
    b.fill(old_x1, GY, SW_OLD_CZ, old_x2, GY + SW_HEIGHT + 1, SW_OLD_CZ, AIR)

    # 在新位置 Z=79 重建
    new_z = SW_NEW_CZ  # 79
    x1 = SW_CX - SW_HALF_W  # 54
    x2 = SW_CX + SW_HALF_W  # 62
    h = SW_HEIGHT            # 4

    # 墙基 (石砖)
    b.fill(x1, GY, new_z, x2, GY, new_z, STONE_BRICK)
    # 墙身 (白色混凝土)
    b.fill(x1, GY + 1, new_z, x2, GY + h - 1, new_z, WALL_BLOCK)
    # 墙顶 (石砖半砖)
    b.fill(x1, GY + h, new_z, x2, GY + h, new_z, _slab(WALL_CAP, "bottom"))

    # 中央装饰匾 (dark_oak)
    b.setblock(SW_CX, GY + 2, new_z, BEAM_LOG)
    # 两端装饰柱
    b.fill(x1, GY + 1, new_z, x1, GY + h - 1, new_z, PILLAR)
    b.fill(x2, GY + 1, new_z, x2, GY + h - 1, new_z, PILLAR)

    print(f"    影壁重建完成 (新位置 Z={new_z}). Commands: {b.cmd_count}")


# ══════════════════════════════════════════════════════════════
#  6. 铺设影壁绕行路 → 荼蘼花架方向
# ══════════════════════════════════════════════════════════════

def _build_bypass_path(b):
    """从影壁两侧绕行到小庭北出口, 然后向荼蘼花架(48,68)方向铺路

    路线:
      影壁西侧通道: X=51~53, Z=78~80 (已有地面, 确保畅通)
      影壁东侧通道: X=63~65, Z=78~80 (已有地面, 确保畅通)
      小庭北出口:   Z=77, cx-2~cx+2

    从小庭北出口(58,77)到远香堂(58,72)的路已由主廊道覆盖。
    这里只铺影壁绕行通道的地面, 确保没有遮挡。
    """
    print("  [6/6] 铺设影壁绕行通道...")

    # 确保影壁两侧通道地面完整 (石砖地面)
    # 西侧通道: X=51~53, Z=77~81
    for z in range(77, 82):
        b.fill(51, GY + 1, z, 53, GY + 1, z, FLOOR_ALT if z % 2 == 0 else FLOOR)
    # 东侧通道: X=63~65, Z=77~81
    for z in range(77, 82):
        b.fill(63, GY + 1, z, 65, GY + 1, z, FLOOR_ALT if z % 2 == 0 else FLOOR)

    # 确保两侧通道上方无遮挡 (只清内侧，保留围墙X=51和X=65)
    b.fill(52, GY + 2, 78, 53, GY + 5, 80, AIR)  # BUG2修复: X从52起不破坏西墙
    b.fill(63, GY + 2, 78, 64, GY + 5, 80, AIR)  # BUG2修复: X到64不破坏东墙

    # BUG1修复: 删除穿远香堂(X:49~67,Z:67~77)的土径
    # 改为从小庭西外侧绕行，走X=49以西
    path_block = PALETTE["path"]
    path_points = [
        (50, 78), (49, 77), (48, 76),
        (47, 75), (47, 74), (47, 73), (47, 72),
        (47, 71), (47, 70), (48, 69), (48, 68),
    ]
    for px, pz in path_points:
        b.fill(px, GY, pz, px + 1, GY, pz, PALETTE["dirt"])
        b.fill(px, GY + 1, pz, px + 1, GY + 1, pz, path_block)

    print(f"    绕行通道完成. Commands: {b.cmd_count}")


# ══════════════════════════════════════════════════════════════
#  汇总入口
# ══════════════════════════════════════════════════════════════

def fix_entrance_connection(b):
    """修复入口门厅 ←→ 小庭深院 ←→ 影壁 的全部衔接问题

    调用顺序至关重要:
      1. 先清除重叠区, 避免后续重建被旧方块干扰
      2. 铺过渡路 (Z=82~83)
      3. 重建门厅北墙 (Z=84)
      4. 重建小庭南墙 (Z=81)
      5. 重建影壁 (Z=78 → Z=79)
      6. 铺绕行通道
    """
    print("=" * 50)
    print("修复入口门厅 ←→ 小庭深院 ←→ 影壁")
    print("=" * 50)

    cmd_start = b.cmd_count

    _clear_overlap_zone(b)
    _build_transition_path(b)
    _rebuild_gate_north_wall(b)
    _rebuild_courtyard_south_wall(b)
    _rebuild_screen_wall(b)
    _build_bypass_path(b)

    total = b.cmd_count - cmd_start
    print(f"\n修复完成! 总命令数: {total}")
    print(f"  门厅北墙: Z={GATE_NEW_NORTH_WALL_Z}, 门洞 X={CX-DOOR_HALF}~{CX+DOOR_HALF} (5格)")
    print(f"  过渡带: Z={TRANSITION_Z1}~{TRANSITION_Z2} (露天石板)")
    print(f"  小庭南墙: Z={COURT_NEW_SOUTH_WALL_Z}, 入口 X={CX-DOOR_HALF}~{CX+DOOR_HALF} (5格)")
    print(f"  影壁: Z={SW_NEW_CZ}, X={SW_CX-SW_HALF_W}~{SW_CX+SW_HALF_W}")
    print(f"  影壁通道: 西侧3格(X=51~53), 东侧3格(X=63~65)")


# ══════════════════════════════════════════════════════════════
#  直接运行
# ══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    from builder import MinecraftBuilder
    print("连接 Minecraft 服务器...")
    with MinecraftBuilder() as b:
        fix_entrance_connection(b)
        print(f"\n全部完成. 总 RCON 命令: {b.cmd_count}")
