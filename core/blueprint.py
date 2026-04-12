"""声明式建筑蓝图系统 — 定义与渲染分离

借鉴 T2BM Interlayer JSON 的"参数化声明 + 统一渲染"思路，
以及 Mindcraft Blueprint 的 phase 分阶段执行模型。

核心设计:
  1. 蓝图 = Python dict，描述"什么建筑、多大、分几步建"
  2. 渲染器 = BlueprintRenderer，读蓝图 dict → 调 builder API 出方块
  3. 参数表达式: "{col_radius}*2+1" 在渲染时解析，蓝图本身不含绝对坐标
  4. 材质通过 PALETTE key 间接引用，蓝图不硬编码 minecraft:xxx

用法:
  from core.blueprint import BlueprintRenderer, PAVILION_BLUEPRINT
  renderer = BlueprintRenderer(builder)
  result = renderer.render(PAVILION_BLUEPRINT, cx=58, cz=10, ground_y=-57)
"""

from __future__ import annotations

import copy
import math
import re
from typing import Any

# 项目内引用 — 仅在运行时需要，类型标注用 string
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from core.blocks import PALETTE


# ═══════════════════════════════════════════════════════════════════════════
# 第一部分：参数解析引擎
# ═══════════════════════════════════════════════════════════════════════════

# 表达式中允许的安全名称（禁止 __builtins__ 等）
_SAFE_NAMES = {"abs": abs, "min": min, "max": max, "round": round, "int": int}


def _resolve_expr(expr: str, params: dict[str, int | float]) -> int | float:
    """解析参数表达式，如 "{col_radius}*2+1" → 11

    安全策略：只允许算术运算和 params 中的变量，禁止任意代码执行。
    """
    # 先替换 {xxx} 占位符为参数值
    def _sub(m):
        key = m.group(1)
        if key not in params:
            raise KeyError(f"蓝图参数 '{key}' 未定义，可用参数: {list(params.keys())}")
        return str(params[key])

    resolved = re.sub(r"\{(\w+)\}", _sub, str(expr))

    # 如果是纯数字，直接返回
    try:
        return int(resolved)
    except (ValueError, TypeError):
        pass
    try:
        return float(resolved)
    except (ValueError, TypeError):
        pass

    # 如果展开后是纯字母/下划线字符串（非数值表达式），原样返回
    # 例如 "{open_side}" 展开为 "E"，这是方向字符串，不是表达式
    if re.fullmatch(r"[A-Za-z_][A-Za-z_0-9]*", resolved):
        return resolved

    # 表达式求值（受限命名空间）
    try:
        result = eval(resolved, {"__builtins__": {}}, {**_SAFE_NAMES, **params})
        return int(result) if isinstance(result, float) and result == int(result) else result
    except Exception as e:
        raise ValueError(f"无法解析表达式 '{expr}' (展开后: '{resolved}'): {e}")


def _resolve_value(val: Any, params: dict[str, int | float]) -> Any:
    """递归解析单个值：str 尝试表达式，list/dict 递归，其余原样返回"""
    if isinstance(val, str):
        if "{" in val:
            return _resolve_expr(val, params)
        # 纯字符串原样返回（如材质名 "base"、朝向 "N"）
        return val
    if isinstance(val, list):
        return [_resolve_value(v, params) for v in val]
    if isinstance(val, dict):
        return {k: _resolve_value(v, params) for k, v in val.items()}
    return val


def resolve_params(raw_params: dict) -> dict[str, int | float]:
    """解析蓝图顶层 params — 支持参数间相互引用（拓扑排序）

    例: {"base_radius": 7, "col_radius": 5, "roof_start": "{col_radius}*2+1"}
    """
    resolved = {}
    unresolved = dict(raw_params)
    max_iter = len(unresolved) * 2  # 防止循环引用死循环

    for _ in range(max_iter):
        if not unresolved:
            break
        progressed = False
        for key, val in list(unresolved.items()):
            try:
                resolved[key] = _resolve_value(val, resolved)
                del unresolved[key]
                progressed = True
            except (KeyError, ValueError):
                continue  # 依赖的参数还没解析，稍后重试
        if not progressed:
            raise ValueError(f"参数循环引用或无法解析: {list(unresolved.keys())}")

    return resolved


def resolve_phase_params(phase_params: dict, global_params: dict) -> dict:
    """解析单个 phase 的 params，引用全局参数"""
    result = {}
    for key, val in phase_params.items():
        result[key] = _resolve_value(val, global_params)
    return result


# ═══════════════════════════════════════════════════════════════════════════
# 第二部分：材质解析
# ═══════════════════════════════════════════════════════════════════════════

def _mat(name: str) -> str:
    """从 PALETTE 取材质，支持直接 minecraft:xxx 透传"""
    if name.startswith("minecraft:"):
        return name
    if name not in PALETTE:
        raise KeyError(f"材质 '{name}' 不在 PALETTE 中，可用: {sorted(PALETTE.keys())}")
    return PALETTE[name]


# ═══════════════════════════════════════════════════════════════════════════
# 第三部分：蓝图渲染器
# ═══════════════════════════════════════════════════════════════════════════

class BlueprintRenderer:
    """统一蓝图渲染器 — 读取蓝图 dict，通过 builder API 输出方块

    职责:
      1. 解析参数表达式
      2. 按 phases 顺序调用对应 handler
      3. 计算连接器绝对坐标
      4. 注册边界框用于撤销
    """

    def __init__(self, builder):
        """
        Args:
            builder: MinecraftBuilder 实例（需在 with 块内使用）
        """
        self.b = builder

        # phase type → handler 映射
        # handler 签名统一: (cx, cz, gy, **phase_params)
        self.phase_handlers: dict[str, callable] = {
            # 基础结构
            "platform":              self._render_platform,
            "floor":                 self._render_floor,
            "corner_pillars":        self._render_pillars,
            "grid_pillars":          self._render_grid_pillars,
            "beam_ring":             self._render_beam_ring,
            "beam_grid":             self._render_beam_grid,

            # 屋顶系统
            "roof_hip_pointed":      self._render_roof_pointed,
            "roof_hip":              self._render_roof_hip,
            "roof_gable":            self._render_roof_gable,

            # 飞檐
            "flying_eaves":          self._render_flying_eaves,

            # 墙体
            "wall_enclosed":         self._render_wall_enclosed,
            "wall_half_open":        self._render_wall_half_open,

            # 栏杆
            "railing_with_entrances": self._render_railing,

            # 单体元素
            "single_block":          self._render_single_block,

            # 装饰
            "lanterns":              self._render_lanterns,
            "dougong":               self._render_dougong,

            # 复合结构（门厅专用）
            "gate_pillars":          self._render_gate_pillars,
            "screen_wall":           self._render_screen_wall,
            "courtyard_walls":       self._render_courtyard_walls,

            # 水上结构
            "stilts":                self._render_stilts,
        }

    # ──────────────────────────────────────────────────────
    # 主入口
    # ──────────────────────────────────────────────────────

    def render(self, blueprint: dict, cx: int, cz: int, ground_y: int,
               clear_first: bool = True) -> dict:
        """渲染一个建筑蓝图到世界坐标

        Args:
            blueprint: 蓝图 dict
            cx, cz:    建筑中心 XZ 世界坐标
            ground_y:  地面 Y 坐标（台基底面）
            clear_first: 是否先清除区域（默认 True）

        Returns:
            {
                "name": str,
                "connectors": {name: {x, y, z, type}},
                "bbox": (x1, y1, z1, x2, y2, z2),
            }
        """
        name = blueprint.get("name", "unnamed")
        print(f"=== 蓝图渲染: {name} at ({cx}, {ground_y}, {cz}) ===")

        # 1. 解析全局参数
        params = resolve_params(blueprint["params"])
        print(f"  参数: {params}")

        # 2. 计算边界并清除
        r = int(params.get("base_radius", params.get("half_x", 8)))
        rz = int(params.get("base_radius", params.get("half_z", r)))
        roof_h = int(params.get("roof_layers", 5)) + int(params.get("pillar_h", 6)) + 5
        bbox = (cx - r - 2, ground_y, cz - rz - 2,
                cx + r + 2, ground_y + roof_h, cz + rz + 2)

        if clear_first:
            print(f"  清除区域: {bbox}")
            self.b.clear(*bbox)

        # 3. 逐阶段渲染
        for i, phase in enumerate(blueprint["phases"]):
            phase_type = phase["type"]
            phase_name = phase.get("name", phase_type)

            if phase_type not in self.phase_handlers:
                print(f"  [!] 跳过未知 phase type: {phase_type}")
                continue

            handler = self.phase_handlers[phase_type]
            phase_params = resolve_phase_params(phase["params"], params)
            print(f"  [{i+1}/{len(blueprint['phases'])}] {phase_name}...")

            handler(cx, cz, ground_y, **phase_params)

        # 4. 计算连接器绝对坐标
        connectors = {}
        for conn_name, conn in blueprint.get("connectors", {}).items():
            offsets = [_resolve_value(o, params) for o in conn["offset"]]
            ox, oy, oz = int(offsets[0]), int(offsets[1]), int(offsets[2])
            connectors[conn_name] = {
                "x": cx + ox, "y": ground_y + oy, "z": cz + oz,
                "type": conn["type"]
            }

        # 5. 注册边界框
        self.b.register_bbox(name, *bbox)
        print(f"  {name} 渲染完成!")

        return {"name": name, "connectors": connectors, "bbox": bbox}

    # ──────────────────────────────────────────────────────
    # Phase Handlers — 基础结构
    # ──────────────────────────────────────────────────────

    def _render_platform(self, cx, cz, gy, *,
                         radius, height, material, step_material,
                         slab_material="base_slab", step_width=3,
                         shape="square", sides=None):
        """须弥座台基

        - 底层实心填充
        - 顶层楼梯围边 + 半砖内部
        - 四面踏步（每面中间 step_width 格）

        Args:
            radius: 台基半径（边长 = 2*radius+1）
            height: 台基高度（通常 2）
            material: 主体材质 PALETTE key
            step_material: 楼梯材质 PALETTE key
            slab_material: 半砖材质 PALETTE key
            step_width: 踏步宽度（默认 3）
            shape: "square"（默认）
            sides: 有踏步的面列表，默认 ["N","S","E","W"]
        """
        r = int(radius)
        h = int(height)
        mat = _mat(material)
        step = _mat(step_material)
        slab = _mat(slab_material)
        sides = sides or ["N", "S", "E", "W"]
        sw = int(step_width) // 2  # 踏步半宽

        # 底层到倒数第二层：实心填充
        if h >= 2:
            self.b.fill(cx - r, gy + 1, cz - r, cx + r, gy + h - 1, cz + r, mat)

        # 顶层：内部半砖 + 楼梯围边
        top_y = gy + h

        # 内部半砖
        if r > 0:
            self.b.fill(cx - r + 1, top_y, cz - r + 1,
                        cx + r - 1, top_y, cz + r - 1,
                        f"{slab}[type=top]")

        # 四面楼梯围边（朝外）
        facing_map = {"N": "north", "S": "south", "E": "east", "W": "west"}
        # 北面
        for x in range(cx - r, cx + r + 1):
            self.b.setblock(x, top_y, cz - r, f"{step}[facing=north,half=top]")
        # 南面
        for x in range(cx - r, cx + r + 1):
            self.b.setblock(x, top_y, cz + r, f"{step}[facing=south,half=top]")
        # 西面
        for z in range(cz - r, cz + r + 1):
            self.b.setblock(cx - r, top_y, z, f"{step}[facing=west,half=top]")
        # 东面
        for z in range(cz - r, cz + r + 1):
            self.b.setblock(cx + r, top_y, z, f"{step}[facing=east,half=top]")

        # 踏步（h 级台阶）
        for side in sides:
            for level in range(1, h + 1):
                step_y = gy + level
                if side == "N":
                    for x in range(cx - sw, cx + sw + 1):
                        self.b.setblock(x, step_y, cz - r - (h - level),
                                        f"{step}[facing=south,half=bottom]")
                elif side == "S":
                    for x in range(cx - sw, cx + sw + 1):
                        self.b.setblock(x, step_y, cz + r + (h - level),
                                        f"{step}[facing=north,half=bottom]")
                elif side == "W":
                    for z in range(cz - sw, cz + sw + 1):
                        self.b.setblock(cx - r - (h - level), step_y, z,
                                        f"{step}[facing=east,half=bottom]")
                elif side == "E":
                    for z in range(cz - sw, cz + sw + 1):
                        self.b.setblock(cx + r + (h - level), step_y, z,
                                        f"{step}[facing=west,half=bottom]")

    def _render_floor(self, cx, cz, gy, *,
                      radius, material, height_offset=3,
                      alt_material=None, pattern="solid",
                      half_x=None, half_z=None):
        """地面铺装

        Args:
            radius: 铺装半径（正方形时）
            material: 主材质 PALETTE key
            height_offset: 铺装层相对 gy 的偏移（默认 3，即台面上一格）
            alt_material: 交替材质（pattern=checkerboard 时用）
            pattern: "solid" | "checkerboard"
            half_x, half_z: 非正方形时的 XZ 半径
        """
        r = int(radius)
        hx = int(half_x) if half_x is not None else r
        hz = int(half_z) if half_z is not None else r
        y = gy + int(height_offset)
        mat = _mat(material)

        if pattern == "solid" or alt_material is None:
            self.b.fill(cx - hx, y, cz - hz, cx + hx, y, cz + hz, mat)
        elif pattern == "checkerboard":
            alt = _mat(alt_material)
            for x in range(cx - hx, cx + hx + 1):
                for z in range(cz - hz, cz + hz + 1):
                    if (x + z) % 2 == 0:
                        self.b.setblock(x, y, z, mat)
                    else:
                        self.b.setblock(x, y, z, alt)

    def _render_pillars(self, cx, cz, gy, *,
                        radius, height, material,
                        base_material="base_col",
                        height_offset=3):
        """四角柱（攒尖亭标配）

        在 (cx +/- radius, cz +/- radius) 四个角放置柱子。

        Args:
            radius: 柱位离中心的距离
            height: 柱高（格数）
            material: 柱身材质
            base_material: 柱础材质
            height_offset: 柱底相对 gy 的偏移
        """
        r = int(radius)
        h = int(height)
        y_base = gy + int(height_offset)
        mat = _mat(material)
        base_mat = _mat(base_material)

        corners = [
            (cx - r, cz - r), (cx + r, cz - r),
            (cx - r, cz + r), (cx + r, cz + r),
        ]
        for px, pz in corners:
            # 柱础
            self.b.setblock(px, y_base, pz, base_mat)
            # 柱身
            self.b.fill(px, y_base + 1, pz, px, y_base + h, pz, mat)

    def _render_grid_pillars(self, cx, cz, gy, *,
                             half_x, half_z, spacing_z, height, material,
                             base_material="base_col",
                             height_offset=1):
        """网格柱（厅堂用：前后两排，沿 Z 轴等距分布）

        Args:
            half_x: 前后排柱 X 距中心的距离
            half_z: 端柱 Z 距中心的距离
            spacing_z: Z 方向柱间距
            height: 柱高
            material: 柱身材质
            base_material: 柱础材质
            height_offset: 柱底相对 gy 的偏移
        """
        hx = int(half_x)
        hz = int(half_z)
        sp = int(spacing_z)
        h = int(height)
        y_base = gy + int(height_offset)
        mat = _mat(material)
        base_mat = _mat(base_material)

        # 生成 Z 坐标列表
        z_positions = list(range(cz - hz, cz + hz + 1, sp))
        if cz + hz not in z_positions:
            z_positions.append(cz + hz)

        for pz in z_positions:
            for px in [cx - hx, cx + hx]:
                self.b.setblock(px, y_base, pz, base_mat)
                self.b.fill(px, y_base + 1, pz, px, y_base + h, pz, mat)

    # ──────────────────────────────────────────────────────
    # Phase Handlers — 梁枋
    # ──────────────────────────────────────────────────────

    def _render_beam_ring(self, cx, cz, gy, *,
                          radius, y_offset, material):
        """柱顶环形额枋（四边梁，连接四角柱顶）

        Args:
            radius: 柱位半径
            y_offset: 梁层相对 gy 的偏移
            material: 梁材质
        """
        r = int(radius)
        y = gy + int(y_offset)
        mat = _mat(material)

        # 北梁
        self.b.fill(cx - r, y, cz - r, cx + r, y, cz - r, mat)
        # 南梁
        self.b.fill(cx - r, y, cz + r, cx + r, y, cz + r, mat)
        # 西梁
        self.b.fill(cx - r, y, cz - r, cx - r, y, cz + r, mat)
        # 东梁
        self.b.fill(cx + r, y, cz - r, cx + r, y, cz + r, mat)

    def _render_beam_grid(self, cx, cz, gy, *,
                          half_x, half_z, spacing_z, y_offset, material):
        """网格梁（厅堂用：纵梁 + 横梁）

        Args:
            half_x: 前后排 X 距离
            half_z: 端柱 Z 距离
            spacing_z: Z 方向柱间距
            y_offset: 梁层相对 gy 的偏移
            material: 梁材质
        """
        hx = int(half_x)
        hz = int(half_z)
        sp = int(spacing_z)
        y = gy + int(y_offset)
        mat = _mat(material)

        # Z 坐标列表
        z_positions = list(range(cz - hz, cz + hz + 1, sp))
        if cz + hz not in z_positions:
            z_positions.append(cz + hz)

        # 两道纵梁（前后排各一，沿 Z 轴）
        self.b.fill(cx - hx, y, cz - hz, cx - hx, y, cz + hz, mat)
        self.b.fill(cx + hx, y, cz - hz, cx + hx, y, cz + hz, mat)

        # 横梁（每组柱位连接前后排）
        for pz in z_positions:
            self.b.fill(cx - hx, y, pz, cx + hx, y, pz, mat)

    # ──────────────────────────────────────────────────────
    # Phase Handlers — 屋顶系统
    # ──────────────────────────────────────────────────────

    def _render_roof_pointed(self, cx, cz, gy, *,
                             start_size, layers, y_offset,
                             stair, slab, block):
        """攒尖顶（四角亭） — 逐层缩小的楼梯金字塔

        每层为 (start_size - 2*i) 的楼梯围边，角部用 outer 形态。
        最顶层为实心方块 + 半砖收顶。

        Args:
            start_size: 底层边长（奇数）
            layers: 楼梯层数
            y_offset: 屋顶起始层相对 gy 的偏移
            stair: 楼梯材质
            slab: 半砖材质
            block: 实心方块材质
        """
        size = int(start_size)
        n_layers = int(layers)
        roof_y = gy + int(y_offset)
        stair_mat = _mat(stair)
        slab_mat = _mat(slab)
        block_mat = _mat(block)

        hs = size // 2  # 初始 half_size

        for i in range(n_layers):
            y = roof_y + i
            cur_hs = hs - i

            if cur_hs <= 0:
                # 到顶了，放实心方块
                self.b.setblock(cx, y, cz, block_mat)
                break

            if cur_hs == 1:
                # 3x3 实心方块
                self.b.fill(cx - 1, y, cz - 1, cx + 1, y, cz + 1, block_mat)
                continue

            # 楼梯围边
            n, s, w, e = cz - cur_hs, cz + cur_hs, cx - cur_hs, cx + cur_hs

            # 四面楼梯（不含角）
            for x in range(w + 1, e):
                self.b.setblock(x, y, n, f"{stair_mat}[facing=south,half=bottom]")
            for x in range(w + 1, e):
                self.b.setblock(x, y, s, f"{stair_mat}[facing=north,half=bottom]")
            for z in range(n + 1, s):
                self.b.setblock(w, y, z, f"{stair_mat}[facing=east,half=bottom]")
            for z in range(n + 1, s):
                self.b.setblock(e, y, z, f"{stair_mat}[facing=west,half=bottom]")

            # 四角 outer 楼梯
            self.b.setblock(w, y, n, f"{stair_mat}[facing=south,half=bottom,shape=outer_right]")
            self.b.setblock(e, y, n, f"{stair_mat}[facing=south,half=bottom,shape=outer_left]")
            self.b.setblock(w, y, s, f"{stair_mat}[facing=north,half=bottom,shape=outer_left]")
            self.b.setblock(e, y, s, f"{stair_mat}[facing=north,half=bottom,shape=outer_right]")

            # 内部填充实心方块
            if cur_hs > 2:
                self.b.fill(w + 1, y, n + 1, e - 1, y, s - 1, block_mat)

    def _render_roof_gable(self, cx, cz, gy, *,
                           half_x, half_z, y_offset, layers,
                           stair, slab, block,
                           overhang=1, facing="east_west"):
        """悬山顶 / 硬山顶（两面坡）

        脊线方向由 facing 决定:
          "east_west" → 脊线沿 Z 轴（南北向），东西两坡
          "north_south" → 脊线沿 X 轴（东西向），南北两坡

        Args:
            half_x: 建筑 X 半宽（柱位 X 距中心）
            half_z: 建筑 Z 半宽（柱位 Z 距中心）
            y_offset: 屋顶起始 Y 偏移
            layers: 坡面层数（不含脊线）
            stair: 楼梯材质
            slab: 半砖材质
            block: 实心方块材质
            overhang: 出檐（悬山超出山墙的格数）
            facing: 坡面朝向 "east_west" | "north_south"
        """
        hx = int(half_x)
        hz = int(half_z)
        n_layers = int(layers)
        roof_y = gy + int(y_offset)
        stair_mat = _mat(stair)
        slab_mat = _mat(slab)
        block_mat = _mat(block)
        oh = int(overhang)

        if facing == "east_west":
            # 脊线沿 Z（南北），东西两坡
            # 悬山出檐在 Z 方向
            roof_z1 = cz - hz - oh
            roof_z2 = cz + hz + oh

            for i in range(n_layers):
                y = roof_y + i
                east_x = cx + hx + 1 - i * 2 if n_layers > 1 else cx + 1
                west_x = cx - hx - 1 + i * 2 if n_layers > 1 else cx - 1

                # 如果两坡交汇或超过
                if west_x >= east_x:
                    break

                # 东坡楼梯 (facing=west)
                for z in range(roof_z1, roof_z2 + 1):
                    self.b.setblock(east_x, y, z, f"{stair_mat}[facing=west,half=bottom]")
                # 西坡楼梯 (facing=east)
                for z in range(roof_z1, roof_z2 + 1):
                    self.b.setblock(west_x, y, z, f"{stair_mat}[facing=east,half=bottom]")
                # 两坡之间填充实心
                if west_x + 1 < east_x:
                    self.b.fill(west_x + 1, y, roof_z1, east_x - 1, y, roof_z2, block_mat)

            # 脊线（半砖）
            ridge_y = roof_y + n_layers
            for z in range(roof_z1, roof_z2 + 1):
                self.b.setblock(cx, ridge_y, z, f"{slab_mat}[type=bottom]")

        else:  # "north_south"
            # 脊线沿 X（东西），南北两坡
            roof_x1 = cx - hx - oh
            roof_x2 = cx + hx + oh

            for i in range(n_layers):
                y = roof_y + i
                south_z = cz + hz + 1 - i * 2 if n_layers > 1 else cz + 1
                north_z = cz - hz - 1 + i * 2 if n_layers > 1 else cz - 1

                if north_z >= south_z:
                    break

                for x in range(roof_x1, roof_x2 + 1):
                    self.b.setblock(x, y, south_z, f"{stair_mat}[facing=north,half=bottom]")
                for x in range(roof_x1, roof_x2 + 1):
                    self.b.setblock(x, y, north_z, f"{stair_mat}[facing=south,half=bottom]")
                if north_z + 1 < south_z:
                    self.b.fill(roof_x1, y, north_z + 1, roof_x2, y, south_z - 1, block_mat)

            ridge_y = roof_y + n_layers
            for x in range(roof_x1, roof_x2 + 1):
                self.b.setblock(x, ridge_y, cz, f"{slab_mat}[type=bottom]")

    def _render_roof_hip(self, cx, cz, gy, *,
                         half_x, half_z, y_offset, layers,
                         stair, slab, block,
                         facing="east_west"):
        """歇山顶（卷棚歇山） — 下部四面坡 + 上部两面坡

        大型厅堂主要屋顶形式。下半为庑殿式四坡，上半为悬山式两坡。

        Args:
            half_x: X 方向半宽
            half_z: Z 方向半宽
            y_offset: 起始 Y 偏移
            layers: 总层数
            stair, slab, block: 材质
            facing: 脊线方向 "east_west" | "north_south"
        """
        hx = int(half_x)
        hz = int(half_z)
        n_layers = int(layers)
        roof_y = gy + int(y_offset)
        stair_mat = _mat(stair)
        slab_mat = _mat(slab)
        block_mat = _mat(block)

        # 歇山顶: 前几层四面缩 (庑殿), 后几层只两面缩 (悬山)
        # 转折点: 约 layers // 2
        hip_layers = max(1, n_layers // 2)

        for i in range(n_layers):
            y = roof_y + i

            if i < hip_layers:
                # 庑殿段：四面缩
                cur_hx = hx + 1 - i
                cur_hz = hz + 1 - i
            else:
                # 悬山段：只在 facing 方向缩
                if facing == "east_west":
                    cur_hx = hx + 1 - i
                    cur_hz = hz + 1 - hip_layers  # Z 固定
                else:
                    cur_hx = hx + 1 - hip_layers  # X 固定
                    cur_hz = hz + 1 - i

            if cur_hx <= 0 or cur_hz <= 0:
                break

            n_z, s_z = cz - cur_hz, cz + cur_hz
            w_x, e_x = cx - cur_hx, cx + cur_hx

            # 四面楼梯
            for x in range(w_x + 1, e_x):
                self.b.setblock(x, y, n_z, f"{stair_mat}[facing=south,half=bottom]")
                self.b.setblock(x, y, s_z, f"{stair_mat}[facing=north,half=bottom]")
            for z in range(n_z + 1, s_z):
                self.b.setblock(w_x, y, z, f"{stair_mat}[facing=east,half=bottom]")
                self.b.setblock(e_x, y, z, f"{stair_mat}[facing=west,half=bottom]")

            # 角楼梯
            self.b.setblock(w_x, y, n_z, f"{stair_mat}[facing=south,half=bottom,shape=outer_right]")
            self.b.setblock(e_x, y, n_z, f"{stair_mat}[facing=south,half=bottom,shape=outer_left]")
            self.b.setblock(w_x, y, s_z, f"{stair_mat}[facing=north,half=bottom,shape=outer_left]")
            self.b.setblock(e_x, y, s_z, f"{stair_mat}[facing=north,half=bottom,shape=outer_right]")

            # 内部填充
            if w_x + 1 < e_x and n_z + 1 < s_z:
                self.b.fill(w_x + 1, y, n_z + 1, e_x - 1, y, s_z - 1, block_mat)

        # 脊线
        ridge_y = roof_y + n_layers
        if facing == "east_west":
            final_hz = hz + 1 - hip_layers
            for z in range(cz - final_hz, cz + final_hz + 1):
                self.b.setblock(cx, ridge_y, z, f"{slab_mat}[type=bottom]")
        else:
            final_hx = hx + 1 - hip_layers
            for x in range(cx - final_hx, cx + final_hx + 1):
                self.b.setblock(x, ridge_y, cz, f"{slab_mat}[type=bottom]")

    # ──────────────────────────────────────────────────────
    # Phase Handlers — 飞檐
    # ──────────────────────────────────────────────────────

    def _render_flying_eaves(self, cx, cz, gy, *,
                             size, y_offset, material):
        """飞檐翘角 — 在屋顶第一层四角各放倒置楼梯模拟上翘

        Args:
            size: 飞檐层边长
            y_offset: 飞檐层 Y 偏移（与屋顶第一层同层）
            material: 飞檐楼梯材质
        """
        hs = int(size) // 2
        y = gy + int(y_offset)
        eave = _mat(material)

        # 四角翘角组合（每角 3 个方块: 对角 + X 延伸 + Z 延伸）
        corners = [
            # (dx_diag, dz_diag, dx_arm, dz_arm, dz_zarm, dx_zarm, corner_facing, arm_x_facing, arm_z_facing)
            (-hs - 1, -hs - 1, -hs - 1, -hs, -hs, -hs - 1,
             "south,shape=outer_right", "east", "south"),
            (+hs + 1, -hs - 1, +hs + 1, -hs, +hs, -hs - 1,
             "south,shape=outer_left", "west", "south"),
            (-hs - 1, +hs + 1, -hs - 1, +hs, -hs, +hs + 1,
             "north,shape=outer_left", "east", "north"),
            (+hs + 1, +hs + 1, +hs + 1, +hs, +hs, +hs + 1,
             "north,shape=outer_right", "west", "north"),
        ]

        for dx_d, dz_d, dx_a, dz_a, dx_z, dz_z, c_face, ax_face, az_face in corners:
            self.b.setblock(cx + dx_d, y, cz + dz_d,
                            f"{eave}[facing={c_face},half=top]")
            self.b.setblock(cx + dx_a, y, cz + dz_a,
                            f"{eave}[facing={ax_face},half=top]")
            self.b.setblock(cx + dx_z, y, cz + dz_z,
                            f"{eave}[facing={az_face},half=top]")

    # ──────────────────────────────────────────────────────
    # Phase Handlers — 墙体
    # ──────────────────────────────────────────────────────

    def _render_wall_enclosed(self, cx, cz, gy, *,
                              half_x, half_z, height, y_offset,
                              material, base_material="wall_base",
                              window_material="trapdoor",
                              window_height=2, open_sides=None):
        """封闭式墙体（厅堂用）

        四面墙，可指定 open_sides 留空（如朝水面那侧不建墙）。
        下半白墙 + 上半花窗。

        Args:
            half_x, half_z: 墙位 XZ 半距
            height: 墙高（不含屋顶）
            y_offset: 墙底 Y 偏移
            material: 墙身材质
            base_material: 墙基材质
            window_material: 花窗材质
            window_height: 花窗起始高度（从墙底算）
            open_sides: 不建墙的面列表 ["E"] 等
        """
        hx = int(half_x)
        hz = int(half_z)
        h = int(height)
        y0 = gy + int(y_offset)
        mat = _mat(material)
        base_mat = _mat(base_material)
        win_mat = _mat(window_material)
        open_sides = open_sides or []
        win_h = int(window_height)

        faces = {
            "N": {"axis": "x", "range": range(cx - hx + 1, cx + hx), "fix": cz - hz, "facing": "south"},
            "S": {"axis": "x", "range": range(cx - hx + 1, cx + hx), "fix": cz + hz, "facing": "north"},
            "W": {"axis": "z", "range": range(cz - hz + 1, cz + hz), "fix": cx - hx, "facing": "east"},
            "E": {"axis": "z", "range": range(cz - hz + 1, cz + hz), "fix": cx + hx, "facing": "west"},
        }

        for side, info in faces.items():
            if side in open_sides:
                continue
            for pos in info["range"]:
                for dy in range(1, h + 1):
                    y = y0 + dy
                    if dy <= win_h:
                        x = pos if info["axis"] == "x" else info["fix"]
                        z = info["fix"] if info["axis"] == "x" else pos
                        self.b.setblock(x, y, z, mat)
                    else:
                        x = pos if info["axis"] == "x" else info["fix"]
                        z = info["fix"] if info["axis"] == "x" else pos
                        self.b.setblock(x, y, z,
                                        f"{win_mat}[facing={info['facing']},half=top,open=true]")

    def _render_wall_half_open(self, cx, cz, gy, *,
                               half_x, half_z, height, y_offset,
                               material, open_side,
                               window_material="trapdoor",
                               window_height=2):
        """半开敞墙体（轩/斋用）

        一面完全开敞，其余面下实上虚。

        Args:
            open_side: 完全开敞的面 "E" | "W" | "N" | "S"
            其余同 wall_enclosed
        """
        open_sides = [open_side] if isinstance(open_side, str) else list(open_side)
        self._render_wall_enclosed(
            cx, cz, gy,
            half_x=half_x, half_z=half_z, height=height, y_offset=y_offset,
            material=material, window_material=window_material,
            window_height=window_height, open_sides=open_sides
        )

    # ──────────────────────────────────────────────────────
    # Phase Handlers — 栏杆
    # ──────────────────────────────────────────────────────

    def _render_railing(self, cx, cz, gy, *,
                        radius, material, y_offset=3,
                        entrance_width=3, sides=None):
        """带入口的栏杆围栏

        每面中间留 entrance_width 格入口，其余放栅栏。

        Args:
            radius: 栏杆位置半径
            material: 栏杆材质
            y_offset: 栏杆层 Y 偏移
            entrance_width: 入口宽度
            sides: 需要栏杆的面列表
        """
        r = int(radius)
        y = gy + int(y_offset)
        mat = _mat(material)
        ew = int(entrance_width) // 2
        sides = sides or ["N", "S", "E", "W"]

        for side in sides:
            if side == "N":
                for x in range(cx - r + 1, cx + r):
                    if abs(x - cx) > ew:
                        self.b.setblock(x, y, cz - r, mat)
            elif side == "S":
                for x in range(cx - r + 1, cx + r):
                    if abs(x - cx) > ew:
                        self.b.setblock(x, y, cz + r, mat)
            elif side == "W":
                for z in range(cz - r + 1, cz + r):
                    if abs(z - cz) > ew:
                        self.b.setblock(cx - r, y, z, mat)
            elif side == "E":
                for z in range(cz - r + 1, cz + r):
                    if abs(z - cz) > ew:
                        self.b.setblock(cx + r, y, z, mat)

    # ──────────────────────────────────────────────────────
    # Phase Handlers — 单体 / 装饰
    # ──────────────────────────────────────────────────────

    def _render_single_block(self, cx, cz, gy, *,
                             y_offset, material,
                             x_offset=0, z_offset=0):
        """放置单个方块（宝顶等）"""
        self.b.setblock(cx + int(x_offset), gy + int(y_offset),
                        cz + int(z_offset), _mat(material))

    def _render_lanterns(self, cx, cz, gy, *,
                         positions, y_offset, material="lantern"):
        """悬挂灯笼

        Args:
            positions: 相对坐标列表 [[dx, dz], ...]
            y_offset: Y 偏移
            material: 灯笼材质
        """
        y = gy + int(y_offset)
        mat = _mat(material)
        for pos in positions:
            dx, dz = int(pos[0]), int(pos[1])
            self.b.setblock(cx + dx, y, cz + dz, f"{mat}[hanging=true]")

    def _render_dougong(self, cx, cz, gy, *,
                        radius, y_offset, material="eave_outer"):
        """斗拱 — 柱顶四方向出挑的倒置楼梯

        Args:
            radius: 柱位半径
            y_offset: 斗拱层 Y 偏移
            material: 斗拱楼梯材质
        """
        r = int(radius)
        y = gy + int(y_offset)
        mat = _mat(material)

        corners = [
            (cx - r, cz - r), (cx + r, cz - r),
            (cx - r, cz + r), (cx + r, cz + r),
        ]
        for px, pz in corners:
            self.b.setblock(px, y, pz - 1, f"{mat}[facing=south,half=top]")
            self.b.setblock(px, y, pz + 1, f"{mat}[facing=north,half=top]")
            self.b.setblock(px - 1, y, pz, f"{mat}[facing=east,half=top]")
            self.b.setblock(px + 1, y, pz, f"{mat}[facing=west,half=top]")

    # ──────────────────────────────────────────────────────
    # Phase Handlers — 门厅 / 复合结构
    # ──────────────────────────────────────────────────────

    def _render_gate_pillars(self, cx, cz, gy, *,
                             gap_width, height, material, y_offset=0):
        """门楼双柱

        Args:
            gap_width: 门洞净宽
            height: 柱高
            material: 柱材质
            y_offset: Y 偏移
        """
        gw = int(gap_width) // 2
        h = int(height)
        y0 = gy + int(y_offset)
        mat = _mat(material)

        for px in [cx - gw - 1, cx + gw + 1]:
            self.b.fill(px, y0, cz, px, y0 + h, cz, mat)

    def _render_screen_wall(self, cx, cz, gy, *,
                            half_width, height, z_offset, y_offset=1,
                            material="wall", base_material="wall_base",
                            cap_material="wall_cap",
                            window_material="window"):
        """影壁 / 照壁

        Args:
            half_width: 半宽
            height: 总高（含墙基和压瓦）
            z_offset: Z 偏移（相对中心）
            material: 墙身材质
            base_material: 墙基材质
            cap_material: 压瓦材质
            window_material: 漏窗材质
        """
        hw = int(half_width)
        h = int(height)
        z = cz + int(z_offset)
        y0 = gy + int(y_offset)
        mat = _mat(material)
        base = _mat(base_material)
        cap = _mat(cap_material)
        win = _mat(window_material)

        for x in range(cx - hw, cx + hw + 1):
            self.b.setblock(x, y0, z, base)
            for dy in range(1, h - 1):
                self.b.setblock(x, y0 + dy, z, mat)
            self.b.setblock(x, y0 + h - 1, z, cap)

        # 漏窗（墙身第二层中间段）
        if hw > 1 and h > 2:
            for x in range(cx - hw + 1, cx + hw):
                self.b.setblock(x, y0 + h - 2, z, win)

    def _render_courtyard_walls(self, cx, cz, gy, *,
                                half_x, half_z, height, y_offset=1,
                                material="wall", base_material="wall_base",
                                cap_material="wall_cap",
                                gate_side="S", gate_width=3):
        """庭院围墙（矮墙围合，一面留门洞）

        Args:
            half_x, half_z: 庭院 XZ 半尺寸
            height: 矮墙高度
            gate_side: 留门洞的面
            gate_width: 门洞宽度
        """
        hx = int(half_x)
        hz = int(half_z)
        h = int(height)
        y0 = gy + int(y_offset)
        mat = _mat(material)
        base = _mat(base_material)
        cap = _mat(cap_material)
        gw = int(gate_width) // 2

        def _wall_col(x, z):
            self.b.setblock(x, y0, z, base)
            for dy in range(1, h - 1):
                self.b.setblock(x, y0 + dy, z, mat)
            self.b.setblock(x, y0 + h - 1, z, cap)

        # 四面墙
        for x in range(cx - hx, cx + hx + 1):
            # 北墙
            _wall_col(x, cz - hz)
            # 南墙（留门洞）
            if gate_side == "S" and abs(x - cx) <= gw:
                continue
            _wall_col(x, cz + hz)

        for z in range(cz - hz + 1, cz + hz):
            # 西墙
            _wall_col(cx - hx, z)
            # 东墙
            if gate_side == "E" and abs(z - cz) <= gw:
                continue
            _wall_col(cx + hx, z)

    # ──────────────────────────────────────────────────────
    # Phase Handlers — 水上结构
    # ──────────────────────────────────────────────────────

    def _render_stilts(self, cx, cz, gy, *,
                       half_x, half_z, depth, material,
                       water_side="S"):
        """水上柱基（榭/水阁的水下桩柱）

        Args:
            half_x, half_z: 建筑 XZ 半尺寸
            depth: 水深（桩柱长度）
            material: 桩柱材质
            water_side: 临水面方向
        """
        hx = int(half_x)
        hz = int(half_z)
        d = int(depth)
        mat = _mat(material)

        # 沿临水侧放置桩柱
        if water_side in ("S", "N"):
            z = cz + hz if water_side == "S" else cz - hz
            for x in range(cx - hx, cx + hx + 1, 2):
                self.b.fill(x, gy - d, z, x, gy, z, mat)
        else:
            x = cx + hx if water_side == "E" else cx - hx
            for z in range(cz - hz, cz + hz + 1, 2):
                self.b.fill(x, gy - d, z, x, gy, z, mat)


# ═══════════════════════════════════════════════════════════════════════════
# 第四部分：预置蓝图库
# ═══════════════════════════════════════════════════════════════════════════

# ─────────────────────────────────────────────
# 1. 四角攒尖亭（牡丹亭）
# ─────────────────────────────────────────────
PAVILION_BLUEPRINT = {
    "name": "四角攒尖亭",
    "type": "pavilion",
    "description": "四面开敞、攒尖顶方亭。牡丹亭标配形制。",

    "params": {
        "base_radius": 8,       # 台基半径 → 17x17
        "col_radius": 5,        # 柱间半径 → 11x11
        "pillar_h": 6,          # 柱高
        "roof_layers": 5,       # 屋顶楼梯层数
        "beam_y_off": 10,       # 额枋 Y 偏移 = 3(台面) + 1(柱础) + 6(柱高) = 10
        "roof_y_off": 11,       # 屋顶起始 = beam_y_off + 1
    },

    "phases": [
        {
            "name": "台基",
            "type": "platform",
            "params": {
                "radius": "{base_radius}",
                "height": 2,
                "material": "base",
                "step_material": "base_step",
                "step_width": 5,
                "sides": ["N", "S", "E", "W"],
            }
        },
        {
            "name": "地面",
            "type": "floor",
            "params": {
                "radius": "{base_radius}-1",
                "material": "floor",
                "alt_material": "base_col",
                "pattern": "checkerboard",
                "height_offset": 3,
            }
        },
        {
            "name": "柱子",
            "type": "corner_pillars",
            "params": {
                "radius": "{col_radius}",
                "height": "{pillar_h}",
                "material": "pillar",
                "base_material": "base_col",
                "height_offset": 3,
            }
        },
        {
            "name": "额枋",
            "type": "beam_ring",
            "params": {
                "radius": "{col_radius}",
                "y_offset": "{beam_y_off}",
                "material": "beam",
            }
        },
        {
            "name": "斗拱",
            "type": "dougong",
            "params": {
                "radius": "{col_radius}",
                "y_offset": "{beam_y_off}",
                "material": "eave_outer",
            }
        },
        {
            "name": "攒尖屋顶",
            "type": "roof_hip_pointed",
            "params": {
                "start_size": "{col_radius}*2+1",
                "layers": "{roof_layers}",
                "y_offset": "{roof_y_off}",
                "stair": "roof",
                "slab": "roof_slab",
                "block": "roof_block",
            }
        },
        {
            "name": "飞檐",
            "type": "flying_eaves",
            "params": {
                "size": "{col_radius}*2+1",
                "y_offset": "{roof_y_off}",
                "material": "eave_outer",
            }
        },
        {
            "name": "宝顶",
            "type": "single_block",
            "params": {
                "y_offset": "{roof_y_off}+{roof_layers}",
                "material": "lightning_rod",
            }
        },
        {
            "name": "栏杆",
            "type": "railing_with_entrances",
            "params": {
                "radius": "{col_radius}",
                "material": "rail",
                "y_offset": 3,
                "entrance_width": 5,
                "sides": ["N", "S", "E", "W"],
            }
        },
        {
            "name": "灯笼",
            "type": "lanterns",
            "params": {
                "positions": [[0, 0], ["{col_radius}", 0], ["-{col_radius}", 0],
                              [0, "{col_radius}"], [0, "-{col_radius}"]],
                "y_offset": "{beam_y_off}-1",
                "material": "lantern",
            }
        },
    ],

    "connectors": {
        "north": {"offset": [0, 0, "-{base_radius}-1"], "type": "path_end"},
        "south": {"offset": [0, 0, "{base_radius}+1"], "type": "path_end"},
        "east":  {"offset": ["{base_radius}+1", 0, 0], "type": "path_end"},
        "west":  {"offset": ["-{base_radius}-1", 0, 0], "type": "path_end"},
    }
}


# ─────────────────────────────────────────────
# 2. 厅堂（远香堂 — 歇山顶封闭式）
# ─────────────────────────────────────────────
HALL_BLUEPRINT = {
    "name": "歇山厅堂",
    "type": "hall",
    "description": "坐南朝北的正式厅堂，歇山顶，四面封闭但北面满窗。",

    "params": {
        "half_x": 9,            # X 半宽 → 19 格面阔
        "half_z": 5,            # Z 半宽 → 11 格进深
        "pillar_h": 6,          # 柱高
        "pillar_hx": 8,         # 柱位 X 半距
        "pillar_hz": 4,         # 柱位 Z 半距
        "pillar_spacing": 4,    # Z 方向柱间距
        "roof_layers": 5,       # 屋顶层数
        "beam_y_off": 8,        # 额枋 Y 偏移 = 1(台基) + 1(柱础) + 6(柱高)
        "roof_y_off": 9,        # 屋顶起始
    },

    "phases": [
        {
            "name": "台基",
            "type": "platform",
            "params": {
                "radius": "{half_x}",
                "height": 1,
                "material": "base",
                "step_material": "base_step",
                "step_width": 5,
                "sides": ["N", "S"],
            }
        },
        {
            "name": "地面",
            "type": "floor",
            "params": {
                "radius": "{half_x}-1",
                "material": "floor",
                "height_offset": 2,
                "half_x": "{half_x}-1",
                "half_z": "{half_z}-1",
            }
        },
        {
            "name": "柱子",
            "type": "grid_pillars",
            "params": {
                "half_x": "{pillar_hx}",
                "half_z": "{pillar_hz}",
                "spacing_z": "{pillar_spacing}",
                "height": "{pillar_h}",
                "material": "pillar",
                "base_material": "base_col",
                "height_offset": 2,
            }
        },
        {
            "name": "梁枋",
            "type": "beam_grid",
            "params": {
                "half_x": "{pillar_hx}",
                "half_z": "{pillar_hz}",
                "spacing_z": "{pillar_spacing}",
                "y_offset": "{beam_y_off}",
                "material": "beam",
            }
        },
        {
            "name": "墙体",
            "type": "wall_enclosed",
            "params": {
                "half_x": "{pillar_hx}",
                "half_z": "{pillar_hz}",
                "height": "{pillar_h}-1",
                "y_offset": 2,
                "material": "wall",
                "base_material": "wall_base",
                "window_material": "trapdoor",
                "window_height": 2,
                "open_sides": ["N"],
            }
        },
        {
            "name": "歇山屋顶",
            "type": "roof_hip",
            "params": {
                "half_x": "{pillar_hx}+1",
                "half_z": "{pillar_hz}+1",
                "y_offset": "{roof_y_off}",
                "layers": "{roof_layers}",
                "stair": "roof",
                "slab": "roof_slab",
                "block": "roof_block",
                "facing": "north_south",
            }
        },
        {
            "name": "灯笼",
            "type": "lanterns",
            "params": {
                "positions": [["{pillar_hx}", 0], ["-{pillar_hx}", 0],
                              [0, "{pillar_hz}"], [0, "-{pillar_hz}"]],
                "y_offset": "{beam_y_off}-1",
                "material": "lantern",
            }
        },
    ],

    "connectors": {
        "north": {"offset": [0, 0, "-{half_z}-2"], "type": "path_end"},
        "south": {"offset": [0, 0, "{half_z}+2"], "type": "path_end"},
        "east":  {"offset": ["{half_x}+2", 0, 0], "type": "corridor_joint"},
        "west":  {"offset": ["-{half_x}-2", 0, 0], "type": "corridor_joint"},
    }
}


# ─────────────────────────────────────────────
# 3. 轩/斋（翠轩 — 悬山顶半开敞）
# ─────────────────────────────────────────────
STUDIO_BLUEPRINT = {
    "name": "悬山半开敞轩",
    "type": "studio",
    "description": "一面全开敞的书斋或赏景轩，悬山顶，对侧白墙花窗。",

    "params": {
        "half_x": 6,            # X 半宽 → 13 格
        "half_z": 4,            # Z 半宽 → 9 格
        "pillar_h": 5,          # 柱高
        "pillar_hx": 5,         # 柱位 X 半距
        "pillar_hz": 3,         # 柱位 Z 半距
        "pillar_spacing": 3,    # Z 方向柱间距
        "roof_layers": 4,       # 屋顶层数
        "beam_y_off": 7,        # 额枋 Y 偏移 = 1 + 1 + 5
        "roof_y_off": 8,        # 屋顶起始
        "open_side": "E",       # 开敞面（面水方向）
    },

    "phases": [
        {
            "name": "台基",
            "type": "platform",
            "params": {
                "radius": "{half_x}",
                "height": 1,
                "material": "base",
                "step_material": "base_step",
                "step_width": 3,
                "sides": ["E", "W"],
            }
        },
        {
            "name": "地面",
            "type": "floor",
            "params": {
                "radius": "{half_x}-1",
                "material": "floor",
                "height_offset": 2,
                "half_x": "{half_x}-1",
                "half_z": "{half_z}-1",
            }
        },
        {
            "name": "柱子",
            "type": "grid_pillars",
            "params": {
                "half_x": "{pillar_hx}",
                "half_z": "{pillar_hz}",
                "spacing_z": "{pillar_spacing}",
                "height": "{pillar_h}",
                "material": "pillar",
                "base_material": "base_col",
                "height_offset": 2,
            }
        },
        {
            "name": "梁枋",
            "type": "beam_grid",
            "params": {
                "half_x": "{pillar_hx}",
                "half_z": "{pillar_hz}",
                "spacing_z": "{pillar_spacing}",
                "y_offset": "{beam_y_off}",
                "material": "beam",
            }
        },
        {
            "name": "墙体",
            "type": "wall_half_open",
            "params": {
                "half_x": "{pillar_hx}",
                "half_z": "{pillar_hz}",
                "height": "{pillar_h}-1",
                "y_offset": 2,
                "material": "wall",
                "open_side": "{open_side}",
                "window_material": "trapdoor",
                "window_height": 2,
            }
        },
        {
            "name": "悬山屋顶",
            "type": "roof_gable",
            "params": {
                "half_x": "{pillar_hx}",
                "half_z": "{pillar_hz}",
                "y_offset": "{roof_y_off}",
                "layers": "{roof_layers}",
                "stair": "roof",
                "slab": "roof_slab",
                "block": "roof_block",
                "overhang": 1,
                "facing": "east_west",
            }
        },
        {
            "name": "灯笼",
            "type": "lanterns",
            "params": {
                "positions": [["{pillar_hx}", 0], ["-{pillar_hx}", 0]],
                "y_offset": "{beam_y_off}-1",
                "material": "lantern",
            }
        },
    ],

    "connectors": {
        "north": {"offset": [0, 0, "-{half_z}-1"], "type": "path_end"},
        "south": {"offset": [0, 0, "{half_z}+1"], "type": "path_end"},
        "east":  {"offset": ["{half_x}+1", 0, 0], "type": "path_end"},
        "west":  {"offset": ["-{half_x}-1", 0, 0], "type": "path_end"},
    }
}


# ─────────────────────────────────────────────
# 4. 水榭（临水悬山）
# ─────────────────────────────────────────────
WATERSIDE_BLUEPRINT = {
    "name": "临水榭",
    "type": "waterside",
    "description": "三面临水的水上建筑，悬山顶，面水全开敞，背水白墙。",

    "params": {
        "half_x": 5,            # X 半宽 → 11 格
        "half_z": 3,            # Z 半宽 → 7 格
        "pillar_h": 5,          # 柱高
        "pillar_hx": 4,         # 柱位 X 半距
        "pillar_hz": 3,         # 柱位 Z 半距
        "pillar_spacing": 3,    # Z 方向柱间距
        "water_depth": 3,       # 水深
        "roof_layers": 3,       # 屋顶层数
        "beam_y_off": 7,        # 额枋 Y 偏移
        "roof_y_off": 8,        # 屋顶起始
        "water_side": "S",      # 临水面
    },

    "phases": [
        {
            "name": "水下桩柱",
            "type": "stilts",
            "params": {
                "half_x": "{pillar_hx}",
                "half_z": "{pillar_hz}",
                "depth": "{water_depth}",
                "material": "base",
                "water_side": "{water_side}",
            }
        },
        {
            "name": "台基",
            "type": "platform",
            "params": {
                "radius": "{half_x}",
                "height": 1,
                "material": "base",
                "step_material": "base_step",
                "step_width": 3,
                "sides": ["N"],
            }
        },
        {
            "name": "地面",
            "type": "floor",
            "params": {
                "radius": "{half_x}-1",
                "material": "floor_wood",
                "height_offset": 2,
                "half_x": "{half_x}-1",
                "half_z": "{half_z}-1",
            }
        },
        {
            "name": "柱子",
            "type": "grid_pillars",
            "params": {
                "half_x": "{pillar_hx}",
                "half_z": "{pillar_hz}",
                "spacing_z": "{pillar_spacing}",
                "height": "{pillar_h}",
                "material": "pillar",
                "base_material": "base_col",
                "height_offset": 2,
            }
        },
        {
            "name": "梁枋",
            "type": "beam_grid",
            "params": {
                "half_x": "{pillar_hx}",
                "half_z": "{pillar_hz}",
                "spacing_z": "{pillar_spacing}",
                "y_offset": "{beam_y_off}",
                "material": "beam",
            }
        },
        {
            "name": "背墙",
            "type": "wall_half_open",
            "params": {
                "half_x": "{pillar_hx}",
                "half_z": "{pillar_hz}",
                "height": "{pillar_h}-1",
                "y_offset": 2,
                "material": "wall",
                "open_side": "{water_side}",
                "window_material": "trapdoor",
                "window_height": 2,
            }
        },
        {
            "name": "悬山屋顶",
            "type": "roof_gable",
            "params": {
                "half_x": "{pillar_hx}",
                "half_z": "{pillar_hz}",
                "y_offset": "{roof_y_off}",
                "layers": "{roof_layers}",
                "stair": "roof",
                "slab": "roof_slab",
                "block": "roof_block",
                "overhang": 1,
                "facing": "east_west",
            }
        },
    ],

    "connectors": {
        "north": {"offset": [0, 0, "-{half_z}-1"], "type": "path_end"},
        "south": {"offset": [0, 0, "{half_z}+1"], "type": "water_edge"},
        "east":  {"offset": ["{half_x}+1", 0, 0], "type": "water_edge"},
        "west":  {"offset": ["-{half_x}-1", 0, 0], "type": "water_edge"},
    }
}


# ─────────────────────────────────────────────
# 5. 门厅+庭院+影壁（入口组团）
# ─────────────────────────────────────────────
GATE_COMPLEX_BLUEPRINT = {
    "name": "入口门厅",
    "type": "gate_complex",
    "description": "园门 + 小庭深院 + 粉画垣影壁，一体化入口序列。",

    "params": {
        "half_x": 7,            # 整体 X 半宽
        "half_z": 5,            # 门厅 Z 半宽
        "gate_width": 3,        # 门洞净宽
        "gate_height": 4,       # 门柱高
        "court_half_x": 5,      # 庭院 X 半宽
        "court_half_z": 4,      # 庭院 Z 半宽
        "court_z_off": -5,      # 庭院中心 Z 偏移（门厅北侧）
        "screen_hw": 4,         # 影壁半宽
        "screen_h": 4,          # 影壁高
        "screen_z_off": -9,     # 影壁 Z 偏移
        "roof_layers": 2,       # 门楼小屋顶层数
    },

    "phases": [
        {
            "name": "门楼双柱",
            "type": "gate_pillars",
            "params": {
                "gap_width": "{gate_width}",
                "height": "{gate_height}",
                "material": "pillar",
                "y_offset": 0,
            }
        },
        {
            "name": "门楼横梁",
            "type": "beam_ring",
            "params": {
                "radius": "{gate_width}//2+1",
                "y_offset": "{gate_height}+1",
                "material": "beam",
            }
        },
        {
            "name": "门楼小屋顶",
            "type": "roof_gable",
            "params": {
                "half_x": "{gate_width}//2+2",
                "half_z": 0,
                "y_offset": "{gate_height}+2",
                "layers": "{roof_layers}",
                "stair": "roof",
                "slab": "roof_slab",
                "block": "roof_block",
                "overhang": 0,
                "facing": "north_south",
            }
        },
        {
            "name": "庭院围墙",
            "type": "courtyard_walls",
            "params": {
                "half_x": "{court_half_x}",
                "half_z": "{court_half_z}",
                "height": 3,
                "y_offset": 1,
                "material": "wall",
                "base_material": "wall_base",
                "cap_material": "wall_cap",
                "gate_side": "S",
                "gate_width": "{gate_width}",
            }
        },
        {
            "name": "庭院铺地",
            "type": "floor",
            "params": {
                "radius": "{court_half_x}",
                "material": "floor_alt",
                "height_offset": 1,
                "half_x": "{court_half_x}-1",
                "half_z": "{court_half_z}-1",
            }
        },
        {
            "name": "粉画垣",
            "type": "screen_wall",
            "params": {
                "half_width": "{screen_hw}",
                "height": "{screen_h}",
                "z_offset": "{screen_z_off}",
                "material": "wall",
                "base_material": "wall_base",
                "cap_material": "wall_cap",
                "window_material": "window",
            }
        },
    ],

    "connectors": {
        "south_entrance": {"offset": [0, 0, "{half_z}+1"], "type": "entrance"},
        "north_exit":     {"offset": [0, 0, "{screen_z_off}-1"], "type": "path_end"},
        "east":           {"offset": ["{half_x}+1", 0, 0], "type": "corridor_joint"},
        "west":           {"offset": ["-{half_x}-1", 0, 0], "type": "corridor_joint"},
    }
}


# ═══════════════════════════════════════════════════════════════════════════
# 蓝图注册表
# ═══════════════════════════════════════════════════════════════════════════

BLUEPRINT_REGISTRY: dict[str, dict] = {
    "pavilion":     PAVILION_BLUEPRINT,
    "hall":         HALL_BLUEPRINT,
    "studio":       STUDIO_BLUEPRINT,
    "waterside":    WATERSIDE_BLUEPRINT,
    "gate_complex": GATE_COMPLEX_BLUEPRINT,
}


# ═══════════════════════════════════════════════════════════════════════════
# 工具函数
# ═══════════════════════════════════════════════════════════════════════════

def clone_blueprint(blueprint: dict, **overrides) -> dict:
    """复制蓝图并覆盖参数

    用法:
        small_pav = clone_blueprint(PAVILION_BLUEPRINT,
                                    base_radius=4, col_radius=2)
    """
    bp = copy.deepcopy(blueprint)
    bp["params"].update(overrides)
    return bp


def list_blueprints() -> list[str]:
    """列出所有注册的蓝图名"""
    return list(BLUEPRINT_REGISTRY.keys())


def get_blueprint(name: str) -> dict:
    """按名称获取蓝图"""
    if name not in BLUEPRINT_REGISTRY:
        raise KeyError(f"蓝图 '{name}' 不存在，可用: {list_blueprints()}")
    return copy.deepcopy(BLUEPRINT_REGISTRY[name])


# ═══════════════════════════════════════════════════════════════════════════
# 连接器工具（建筑间连接）
# ═══════════════════════════════════════════════════════════════════════════

def connector_distance(a: dict, b: dict) -> float:
    """计算两个连接器之间的距离"""
    return math.sqrt(
        (a["x"] - b["x"]) ** 2 +
        (a["y"] - b["y"]) ** 2 +
        (a["z"] - b["z"]) ** 2
    )


# ═══════════════════════════════════════════════════════════════════════════
# CLI 入口（仅测试用，不会实际连接服务器）
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    # 干跑测试：验证参数解析
    print("=== 蓝图系统自检 ===\n")

    for name, bp in BLUEPRINT_REGISTRY.items():
        print(f"[{name}] {bp['name']}")
        params = resolve_params(bp["params"])
        print(f"  解析后参数: {params}")

        for phase in bp["phases"]:
            try:
                pp = resolve_phase_params(phase["params"], params)
                print(f"  {phase['name']}: OK")
            except Exception as e:
                print(f"  {phase['name']}: FAIL — {e}")
        print()

    print("=== 用法示例 ===")
    print("""
from core.blueprint import BlueprintRenderer, PAVILION_BLUEPRINT, clone_blueprint
from core.builder import MinecraftBuilder

with MinecraftBuilder() as b:
    renderer = BlueprintRenderer(b)

    # 建造牡丹亭
    result = renderer.render(PAVILION_BLUEPRINT, cx=58, cz=10, ground_y=-57)

    # 建造缩小版亭子
    small = clone_blueprint(PAVILION_BLUEPRINT, base_radius=5, col_radius=3, pillar_h=4)
    result2 = renderer.render(small, cx=92, cz=42, ground_y=-60)

    # 查看连接器
    print(result["connectors"])
""")
