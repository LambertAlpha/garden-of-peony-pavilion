"""曲廊起终点衔接重设计 — 修复动线"始"与"终"的仪式感

问题诊断:
  1. 起点: 影壁(Z=70) → 曲廊A(55,68) 之间仅2格裸地，花架(Z=66~69)
     和曲廊在Z方向重叠，玩家从影壁绕出来就直接撞进曲廊，
     没有"入廊"的仪式感。
  2. 终点: 曲廊H(70,15) 到牡丹亭台基(实际西边X=73)之间只有3格，
     connections.py 用了 config 中过时的 r_base=8 (算出X=70)，
     但 pavilion.py 实际 R_BASE=5 (西边X=73)。
     无论如何，没有"远眺-趋近-仰望"的空间序列。

设计方案(基于苏州园林廊道设计原则):

  ── 起点: "起始门廊"(入廊亭) ──
  苏州园林的廊从不凭空开始。拙政园的廊起于建筑(厅堂、门廊)，
  沧浪亭复廊起于门洞。我们的曲廊起点需要一个"门廊"作为起始标志。

  方案: 在曲廊A点(55,68)前方(东侧)设一座"月洞门式门廊"：
  - 位置: (57, 67)~(59, 69)，即A点东侧2~4格
  - 形制: 简化月洞门框(3格宽拱门) + 上方小屋顶
  - 从影壁绕出 → 穿过花架区 → 看到月洞门 → 穿门入廊
  - 花架和门廊之间铺碎石小径(~3格)作为过渡

  ── 终点: "观亭前庭" ──
  苏州园林的廊到达重要建筑前，必有一段"收"→"放"的空间节奏。
  人从廊的狭长空间走出，进入开阔前庭，视野突然放大，
  牡丹亭出现在视野中——这就是"先抑后扬"。

  方案: 将曲廊H终点从(70,15)后退到(67,15)，
  腾出 X=68~72 共5格 + 牡丹亭台基前3格(X=70~72) = 8格前庭空间。
  - 前庭铺装: 7x7 石砖方台 (X=67~73, Z=12~18)
  - 中置太湖石或灯笼台 (X=70, Z=15) 作为对景点
  - 两侧放置条凳(台阶方块模拟)供"驻足仰望"
  - 前庭边缘至牡丹亭踏步之间铺碎石过渡

注意: 本脚本只修复两个端点的衔接空间，不修改曲廊主体路线。
     曲廊 waypoint G(70,20)->H(70,15) 应在 config.py 中改为
     G(67,20)->H(67,15)，但这需要修改曲廊主体重建，超出本脚本范围。
     本脚本假设 H 终点仍在 (70,15)，在其前方(东侧)建造前庭。

坐标总表:
  影壁:        Z=70, X=48~62
  花架:        Z=66~69, X=48~62
  入廊门洞:    (58, 66), 朝南开口
  曲廊A:       (55, 68), Y=-60
  曲廊H:       (70, 15), Y=-57 (爬山廊终点)
  牡丹亭:      cx=78, cz=15, R_BASE=5, ground_y=-57
  牡丹亭西踏步: X=72, Z=14~16
  前庭:        X=71~76, Z=12~18, Y=-57
"""

import sys
sys.path.insert(0, '/Users/lambertlin/minecraft-server/scripts')

from builder import MinecraftBuilder
from blocks import PALETTE, GROUND_Y, BUILD_Y
from config import CORRIDOR, GATE_AREA, PAVILION
import random

# ── 材质常量 ──
PILLAR     = PALETTE["pillar"]        # stripped_crimson_stem
BEAM       = PALETTE["beam"]          # dark_oak_planks
BEAM_LOG   = PALETTE["beam_log"]      # dark_oak_log
RAIL       = PALETTE["rail"]          # crimson_fence
RAIL_GATE  = PALETTE["rail_gate"]     # crimson_fence_gate
ROOF_SLAB  = PALETTE["roof_slab"]     # stone_brick_slab
ROOF_STAIR = PALETTE["roof"]         # stone_brick_stairs
ROOF_BLOCK = PALETTE["roof_block"]    # stone_bricks
FLOOR      = PALETTE["floor"]        # smooth_stone
FLOOR_ALT  = PALETTE["floor_alt"]    # stone_bricks
LANTERN    = PALETTE["lantern"]
BASE_COL   = PALETTE["base_col"]     # polished_andesite
WALL       = PALETTE["wall"]         # white_concrete
WALL_BASE  = PALETTE["wall_base"]    # stone_bricks
WALL_CAP   = PALETTE["wall_cap"]     # stone_brick_slab
WINDOW     = PALETTE["window"]       # iron_bars
TRAPDOOR   = PALETTE["trapdoor"]     # jungle_trapdoor
PATH_BLOCK = PALETTE["path"]         # dirt_path
GRAVEL     = PALETTE["gravel"]
AIR        = PALETTE["air"]
STONE_BRICK       = PALETTE["base"]
STONE_BRICK_STAIR = PALETTE["base_step"]
STONE_BRICK_SLAB  = PALETTE["base_slab"]
COBBLE     = PALETTE["cobblestone"]
MOSSY_COBBLE = PALETTE["mossy_cobblestone"]
TAIHU_MAIN = PALETTE["taihu_main"]   # dripstone_block
TAIHU_WHITE = PALETTE["taihu_white"] # calcite
RED_CARPET = PALETTE["red_carpet"]
MOSS_CARPET = PALETTE["moss_carpet"]
BAMBOO     = PALETTE["bamboo"]


# ══════════════════════════════════════════════════════════════
#  PART 1: 起点衔接 — 入廊门洞 + 碎石径
# ══════════════════════════════════════════════════════════════

def fix_corridor_start(b: MinecraftBuilder):
    """重新设计从影壁到曲廊A的过渡空间。

    现状空间分析 (自南向北):
      Z=70: 影壁线 (庭院北端)
      Z=69: 花架南端 (bower_z2)
      Z=66: 花架北端 (bower_z1)
      Z=68: 曲廊A点 (55, 68)

    花架 X=48~62 覆盖了影壁等宽区域。
    曲廊A(55,68) 在花架内部(Z=66~69)。

    新设计:
    1. 在 A 点东侧偏北 (58, 65) 建一座入廊月洞门
       - 门洞朝东西向 (与曲廊第一段 A->B 平行)
       - 玩家从花架区域(Z=66~69)向北走出花架，
         在 Z=65 看到月洞门，穿门后向西即进入曲廊
    2. 从花架北端(Z=66) 到门洞(Z=65) 铺一段碎石径 (1格过渡)
    3. 门洞内部与曲廊 A 点地面连接

    但实际问题更本质:
    - 曲廊 A 在 (55, 68)，在花架范围内 (Z=66~69)
    - 花架 X=48~62, 曲廊中心 X=55, 曲廊宽5格 X=53~57
    - 花架和曲廊在空间上有交叉!

    更好的方案: 把入廊门洞直接建在花架的东侧出口处，
    作为"花架→曲廊"的转换节点。

    最终方案:
    a) 在曲廊 A(55,68) 东侧 X=58 处建月洞门框 (朝东西向)
       门框中心 (58, 68)，Z跨 66~70，朝东开口
       玩家从影壁东侧通道(~X=64)走过来 → 看到月洞门 → 穿门 → 进入曲廊
    b) 门洞是一个"YZ平面的拱形开口"，嵌在一段短白墙中
    c) 门洞西侧与曲廊A点地面无缝衔接
    d) 门洞东侧铺一小段碎石地面与影壁通道连接
    """
    print("  === 起点衔接: 入廊门洞 ===")

    y0 = BUILD_Y  # -60
    ax, az = CORRIDOR["waypoints"][0]   # (55, 68)
    corr_half = CORRIDOR["width"] // 2  # 2

    # ── 入口区参数 ──
    cfg = GATE_AREA
    cx = cfg["cx"]               # 55
    cz = cfg["cz"]               # 80
    cw = cfg["court_width"]      # 16
    cd = cfg["court_depth"]      # 10
    gw = cfg["gate_width"]       # 5
    screen_hw = gw + 2           # 7
    scr_x2 = cx + screen_hw     # 62

    # 影壁在 Z = cz - cd = 70
    screen_z = cz - cd           # 70

    # 东侧通道中心 X = scr_x2 + 2 = 64
    east_pass_x = scr_x2 + 2    # 64

    # ────────────────────────────────────────────
    # A. 月洞门 — 在曲廊A东侧, 作为"入廊仪式"
    # ────────────────────────────────────────────
    # 月洞门位置: X=58, Z=68(与A点同Z), YZ平面
    # 门洞朝东西方向通行
    # 门框嵌在一段南北向短白墙中 (Z=66~70, X=58)
    # 月洞门半径=2格 (在YZ平面画圆, 圆心 Y=y0+2, Z=68)

    gate_x = 58         # 门框所在X坐标
    gate_z = az          # 68, 与A点对齐
    gate_r = 2           # 月洞门半径

    print(f"    月洞门: X={gate_x}, Z={gate_z}, R={gate_r}")

    # ── A1. 短白墙 (门框载体) ──
    # Z=65~71, X=58, 高4格 (y0+1 ~ y0+4)
    wall_z1 = gate_z - 3  # 65
    wall_z2 = gate_z + 3  # 71
    wall_h = 4             # 墙高4格

    for z in range(wall_z1, wall_z2 + 1):
        b.setblock(gate_x, y0 + 1, z, WALL_BASE)       # 墙基
        b.setblock(gate_x, y0 + 2, z, WALL)             # 墙身
        b.setblock(gate_x, y0 + 3, z, WALL)             # 墙身
        b.setblock(gate_x, y0 + 4, z, WALL)             # 墙身
        b.setblock(gate_x, y0 + 5, z, f"{WALL_CAP}[type=top]")  # 压瓦

    # ── A2. 在白墙上凿月洞门 ──
    # YZ平面圆: 圆心 (Y=y0+2, Z=gate_z), 半径=2
    # 圆心在 y0+2 (地面上方2格) 使得圆底部刚好在 y0 层(地面)
    # 玩家身高2格, 门洞最高点 y0+4, 净空充足
    center_y = y0 + 2
    center_z = gate_z
    for dy in range(-gate_r, gate_r + 1):
        for dz in range(-gate_r, gate_r + 1):
            if dy * dy + dz * dz <= gate_r * gate_r:
                py = center_y + dy
                pz = center_z + dz
                if py >= y0:  # 包括地面层也清空(门洞通行)
                    b.setblock(gate_x, py, pz, AIR)

    # ── A3. 月洞门框装饰 (圆环边缘用石砖描边) ──
    # 在圆的外缘(半径r到r+1.5之间)，将白墙换成石砖强调门框轮廓
    for dy in range(-gate_r - 2, gate_r + 3):
        for dz in range(-gate_r - 2, gate_r + 3):
            dist_sq = dy * dy + dz * dz
            # 在半径r和r+1.5之间的环形区域
            if gate_r * gate_r < dist_sq <= (gate_r + 1.5) * (gate_r + 1.5):
                py = center_y + dy
                pz = center_z + dz
                if y0 + 1 <= py <= y0 + 4 and wall_z1 <= pz <= wall_z2:
                    b.setblock(gate_x, py, pz, STONE_BRICK)

    # ── A4. 月洞门底部地面 (确保门洞下方有地面可走) ──
    # 门洞内地面: X=58, Z=67~69, Y=y0
    for z in range(gate_z - 1, gate_z + 2):
        b.setblock(gate_x, y0, z, FLOOR)

    # ────────────────────────────────────────────
    # B. 月洞门两侧地面衔接
    # ────────────────────────────────────────────

    # ── B1. 西侧: 月洞门→曲廊A入口柱 (X=56~57, Z=66~70) ──
    # circulation.py _build_endpoints 在 A 东侧 X=ax+1=56 放了入口柱
    # 需要铺 X=57(入口柱外1格) 到 gate_x-1=57 的地面
    # 实际上 X=57 这一格需要铺地，保证从月洞门到入口柱之间可走
    print("    西侧衔接: 月洞门→曲廊A")
    for x in range(ax + corr_half, gate_x):  # X=57 (ax+2=57 到 gate_x-1=57)
        for z in range(az - corr_half, az + corr_half + 1):  # Z=66~70
            b.setblock(x, y0, z, FLOOR)

    # ── B2. 东侧: 月洞门→影壁通道 (X=59~63, Z=67~69) ──
    # 碎石小径连接东侧通道
    print("    东侧衔接: 月洞门→影壁通道")
    random.seed(88)
    for x in range(gate_x + 1, east_pass_x - 1):  # X=59~62
        for z in range(gate_z - 1, gate_z + 2):    # Z=67~69, 3格宽
            # 混合材质: 碎石为主, 偶尔石砖
            if random.random() < 0.3:
                b.setblock(x, y0, z, STONE_BRICK)
            else:
                b.setblock(x, y0, z, GRAVEL)
        # 小径两侧随机苔藓地毯 (地面上方, 需要下方有实心方块)
        for dz in [-2, 2]:
            if random.random() < 0.4:
                b.setblock(x, y0 + 1, gate_z + dz, MOSS_CARPET)

    # ────────────────────────────────────────────
    # C. 门洞上方小装饰
    # ────────────────────────────────────────────

    # ── C1. 门额匾位 (门洞正上方, 用深色橡木板模拟匾额) ──
    # 位于月洞门正上方 Y=y0+5, Z=gate_z-1 ~ gate_z+1
    # 已被压瓦覆盖，改为在 y0+4 门洞上沿加一条横梁
    b.fill(gate_x, y0 + 4, gate_z - 1, gate_x, y0 + 4, gate_z + 1, BEAM)

    # ── C2. 门洞两侧挂灯笼 ──
    # 在门洞南北两侧的墙面上(门洞边缘外1格)各挂一盏灯笼
    b.setblock(gate_x - 1, y0 + 3, gate_z - gate_r - 1,
               f'{LANTERN}[hanging=false]')  # 北侧
    b.setblock(gate_x - 1, y0 + 3, gate_z + gate_r + 1,
               f'{LANTERN}[hanging=false]')  # 南侧

    print("    入廊门洞建造完成")


# ══════════════════════════════════════════════════════════════
#  PART 2: 终点衔接 — 观亭前庭
# ══════════════════════════════════════════════════════════════

def fix_corridor_end(b: MinecraftBuilder):
    """重新设计从曲廊H到牡丹亭的过渡空间。

    现状:
      曲廊H: (70, 15), Y=-57 (爬山廊终点)
      牡丹亭: cx=78, cz=15, 实际R_BASE=5
        台基: X=73~83, Z=10~20
        西面踏步: X=72, Z=14~16 (从 Y=-57+1=-56 到 Y=-55)
        台面: Y=-55

    H(X=70) 到 台基西边(X=73) = 3格空隙 (X=71, 72 = 踏步)
    加上踏步那一格也算，H到台基实体之间有 2 格平地 + 1 格踏步。

    这太窄了。玩家从爬山廊走出来，一抬头就是台基，
    没有"从廊的幽暗走入开阔前庭，远远仰望牡丹亭"的空间体验。

    新设计 — "观亭前庭":
    苏州园林到达重要建筑前必有"收→放"的节奏:
    廊道(窄) → 出廊(门框) → 前庭(宽阔) → 踏步 → 亭台

    由于不修改曲廊主体路线(H仍在70,15)，我们在H点前方建造:

    1. "出廊门框" — 在H点(70,15)建一个简单的出口门框
       标志着曲廊的正式结束
    2. "观亭前庭" — H点到牡丹亭之间的开阔石铺空间
       X=71~72, Z=12~18 (受限于只有2-3格纵深)
       前庭虽窄，但通过以下手法营造仪式感:
       a) 地面从廊道的 smooth_stone 换成 stone_bricks (材质变化暗示空间转换)
       b) 前庭中心(X=71, Z=15) 放一座小石灯笼台 (对景)
       c) 两侧(Z=12,18) 放矮竹丛 (框景,引导视线向牡丹亭)

    但说实话，2~3格的前庭太寒酸了。让我重新想:

    实际上牡丹亭台基外还有踏步占1格(X=72)，台基从X=73开始。
    如果我们把"前庭"的概念扩大——不只是廊道和台基之间的缝隙，
    而是把牡丹亭台基周围一圈都算作"前庭环境":

    方案: 在 X=71~72, Z=11~19 铺石砖广场(9x2格)，
    加上台基踏步前的1格平台 = 3格进深。
    在广场南北两端(Z=11, Z=19)各放一座小石灯台。
    广场中轴(Z=15)对准牡丹亭中心和曲廊出口。
    """
    print("  === 终点衔接: 观亭前庭 ===")

    # ── 牡丹亭参数 ──
    p_cx = PAVILION["cx"]        # 78
    p_cz = PAVILION["cz"]        # 15
    p_gy = PAVILION["ground_y"]  # -57
    # 实际台基: R_BASE=5 (pavilion.py 硬编码)
    pav_r_base = 5
    pav_west_edge = p_cx - pav_r_base   # 73 (台基西边)
    pav_west_step = pav_west_edge - 1    # 72 (西面踏步位置)

    # ── 曲廊 H 参数 ──
    hx, hz = CORRIDOR["waypoints"][7]    # (70, 15)
    corr_half = CORRIDOR["width"] // 2   # 2
    h_y = p_gy                           # -57

    # ────────────────────────────────────────────
    # A. 出廊门框 — 标志曲廊正式结束
    # ────────────────────────────────────────────
    # H(70,15) 是曲廊末端，G(70,20)->H(70,15) 沿 Z 轴向北
    # 曲廊到H后终止。玩家需要向东走去牡丹亭(78,15)。
    # 曲廊是南北走向(Z轴)，柱子在东西两侧(X=68, 72)
    # 出廊门框建在H点东侧: X=hx+corr_half+1=73，但这里已是台基!
    #
    # 重新思考: H 是曲廊末端(Z最小处)，玩家走到H后自然向北走出。
    # 但牡丹亭在东边。所以出廊后需要向东转。
    # 在H北端(Z=hz=15处)放出口门框(南北走向廊道的北端出口)。
    # 然后前庭向东展开到牡丹亭。
    print("    出廊门框: H点北端")

    ph = CORRIDOR["pillar_h"]  # 4
    beam_y = h_y + ph          # -57 + 4 = -53

    # G->H 沿 Z 轴，柱在东西两侧 X=hx-half 和 hx+half
    # H点本身已有柱(由build_corridors放置)
    # 在H点北侧1格(Z=hz-1=14)加一对出口标志柱
    exit_z = hz - 1            # 14, H点北1格
    for dx in [-corr_half, corr_half]:
        bx = hx + dx
        b.setblock(bx, h_y, exit_z, BASE_COL)          # 柱础
        for dy in range(1, ph + 1):
            b.setblock(bx, h_y + dy, exit_z, PILLAR)   # 柱身
    # 横梁
    b.fill(hx - corr_half, beam_y, exit_z,
           hx + corr_half, beam_y, exit_z, BEAM)
    # 出口灯笼
    b.setblock(hx, beam_y - 1, exit_z, f'{LANTERN}[hanging=true]')

    # ────────────────────────────────────────────
    # B. 观亭前庭 — 曲廊出口到牡丹亭踏步之间
    # ────────────────────────────────────────────
    # 区域: X=71~72, Z=11~19 (9格宽 x 2格深)
    # 加上曲廊出口处(X=70)也铺一圈 → X=70~72, Z=11~19
    # Y=h_y=-57 (与爬山廊终点齐平)

    plaza_x1 = hx + 1           # 71
    plaza_x2 = pav_west_step    # 72 (踏步那一格也算前庭)
    plaza_z1 = p_cz - 4         # 11
    plaza_z2 = p_cz + 4         # 19
    plaza_y = h_y                # -57

    print(f"    前庭: X={plaza_x1}~{plaza_x2}, Z={plaza_z1}~{plaza_z2}, Y={plaza_y}")

    # ── B1. 清理前庭区域上方障碍物 ──
    # 只清 X=71 这一列，X=72 保留(牡丹亭踏步在这里)
    b.fill(plaza_x1, plaza_y + 1, plaza_z1,
           plaza_x1, plaza_y + ph + 2, plaza_z2, AIR)

    # ── B2. 铺前庭地面 ──
    # 中轴(Z=14~16)用 smooth_stone，两侧用 stone_bricks
    # 形成"地面引导线"指向牡丹亭
    for x in range(plaza_x1, plaza_x2 + 1):
        for z in range(plaza_z1, plaza_z2 + 1):
            if p_cz - 1 <= z <= p_cz + 1:
                # 中轴3格: 光滑石头(与曲廊走道同材质,暗示动线延续)
                b.setblock(x, plaza_y, z, FLOOR)
            else:
                # 两翼: 石砖(广场感)
                b.setblock(x, plaza_y, z, STONE_BRICK)

    # 也把曲廊出口(X=70)北侧的一小段铺成前庭
    for z in range(plaza_z1, hz - corr_half):
        b.setblock(hx, plaza_y, z, STONE_BRICK)
    for z in range(hz + corr_half + 1, plaza_z2 + 1):
        b.setblock(hx, plaza_y, z, STONE_BRICK)

    # ── B3. 前庭边缘装饰 ──

    # 南北两端各放一座小石灯台 (太湖石底座 + 灯笼)
    for lz in [plaza_z1, plaza_z2]:
        # 底座: 2格高石块
        b.setblock(plaza_x1, plaza_y + 1, lz, TAIHU_MAIN)
        b.setblock(plaza_x1, plaza_y + 2, lz, TAIHU_WHITE)
        # 灯笼放在石块顶
        b.setblock(plaza_x1, plaza_y + 3, lz, f'{LANTERN}[hanging=false]')

    # 前庭中央(X=71或72, Z=15)放一块点景石(对景——视线焦点)
    # 玩家从曲廊走出，第一眼看到这块石头，然后视线越过石头看到牡丹亭
    focus_x = plaza_x1   # 71
    focus_z = p_cz        # 15
    # 用一块矮太湖石 (1格高, 不挡路, 玩家可以绕过)
    # 放在中轴线偏侧(Z=15+1=16)避免挡住正中路线
    b.setblock(focus_x, plaza_y + 1, focus_z + 1, TAIHU_MAIN)

    # ── B4. 前庭两侧矮竹丛 (框景效果) ──
    # 在前庭南北边缘种几根竹子，框住牡丹亭的视野
    random.seed(99)
    for lz in [plaza_z1 - 1, plaza_z1, plaza_z2, plaza_z2 + 1]:
        for x in range(plaza_x1, plaza_x2 + 1):
            if random.random() < 0.5:
                b.setblock(x, plaza_y + 1, lz, BAMBOO)

    # ── B5. 确保牡丹亭西面踏步正常 ──
    # 踏步在 X=72, Z=14~16, 从 Y=-56 到 Y=-55
    # pavilion.py 的踏步是3格宽(cx-1~cx+1=77~79 不对...)
    # 实际是 Z=cz-1~cz+1=14~16, X=pav_west_edge-1=72
    # 踏步第一级: X=72, Y=-57+1=-56, facing=east
    # 踏步第二级: X=73, Y=-57+2=-55, facing=east
    # 这些由 pavilion.py 处理，这里不重建
    # 但需要确保前庭地面(Y=-57)和踏步(Y=-56)正确衔接
    # 在 X=72 处，前庭地面上方就是踏步第一级
    # 如果踏步已存在，前庭铺地不会覆盖(因为踏步在Y=-56，前庭在Y=-57)

    print("    观亭前庭建造完成")


# ══════════════════════════════════════════════════════════════
#  PART 3: 辅助修复 — 地面填充与连接
# ══════════════════════════════════════════════════════════════

def fix_ground_connections(b: MinecraftBuilder):
    """填充起点和终点附近的地面，确保无悬空或断层。"""
    print("  === 地面连接修复 ===")

    y0 = BUILD_Y  # -60

    # ── 起点区: 花架区域地面确保连续 ──
    # 花架 X=48~62, Z=66~69 下方应有地面
    # connections.py fix_gate_to_corridor 已经铺了通道地面
    # 这里补充月洞门附近的地面
    gate_x = 58
    az = CORRIDOR["waypoints"][0][1]  # 68
    # X=55~58, Z=65~71 确保有地面 (月洞门区域)
    for x in range(55, 59):
        for z in range(65, 72):
            # 不覆盖已有的特殊地面，只填补 air/grass 下方
            b.setblock(x, GROUND_Y, z, PALETTE["dirt"])

    # ── 终点区: 前庭下方填实 ──
    # 前庭 Y=-57，下方 Y=-58~-61 可能是空气(爬山廊清除过)
    # 需要填充支撑
    hx, hz = CORRIDOR["waypoints"][7]  # (70, 15)
    h_y = PAVILION["ground_y"]         # -57
    plaza_x1 = hx + 1       # 71
    plaza_x2 = 72
    plaza_z1 = 11
    plaza_z2 = 19

    # 填充前庭下方 (从 ground_y-1 到 GROUND_Y)
    for fill_y in range(GROUND_Y, h_y):
        b.fill(plaza_x1, fill_y, plaza_z1,
               plaza_x2, fill_y, plaza_z2, PALETTE["stone"])

    # 也填充 H 点附近下方
    for fill_y in range(GROUND_Y, h_y):
        b.fill(hx - 2, fill_y, plaza_z1,
               hx + 2, fill_y, hz, PALETTE["stone"])

    print("    地面填充完成")


# ══════════════════════════════════════════════════════════════
#  主函数
# ══════════════════════════════════════════════════════════════

def fix_all(b: MinecraftBuilder):
    """执行所有端点衔接修复。"""
    print("=" * 60)
    print("  曲廊端点衔接修复")
    print("=" * 60)

    fix_corridor_start(b)
    fix_corridor_end(b)
    fix_ground_connections(b)

    # 注册边界框（便于撤销）
    b.register_bbox("corridor_start_fix",
                    55, GROUND_Y, 65,
                    64, BUILD_Y + 6, 72)
    b.register_bbox("corridor_end_fix",
                    68, GROUND_Y, 11,
                    73, PAVILION["ground_y"] + 6, 19)

    print("=" * 60)
    print("  全部端点衔接修复完成!")
    print("=" * 60)


if __name__ == "__main__":
    with MinecraftBuilder() as b:
        fix_all(b)
        print(f"Done! {b.cmd_count} commands")
