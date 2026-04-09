"""建造后自动验证系统 — 通过 RCON 检查方块是否正确放置

借鉴 Mindcraft checkBlueprintLevel 模式：
  1. 注册检查点（单点或区域采样）
  2. 用 execute if block 无损检测方块类型
  3. 汇总通过/失败，输出可操作的报告

用法:
    with MinecraftBuilder() as b:
        v = BuildingVerifier(b)
        for x, y, z, block, desc in get_pavilion_checks(**PEONY_PAVILION):
            v.add_check(x, y, z, block, desc)
        result = v.verify_all()
        v.print_report(result)
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from builder import MinecraftBuilder


# ═══════════════════════════════════════════
# 核心验证器
# ═══════════════════════════════════════════

@dataclass
class CheckPoint:
    x: int
    y: int
    z: int
    expected: str  # e.g. "minecraft:stone_bricks"
    desc: str = ""


class BuildingVerifier:
    """建造后验证器 — 通过 RCON 检查关键方块是否正确放置"""

    def __init__(self, builder: "MinecraftBuilder"):
        self.b = builder
        self.checks: list[CheckPoint] = []

    # ── 注册检查点 ──

    def add_check(self, x: int, y: int, z: int, expected_block: str, description: str = ""):
        """注册单个检查点"""
        block = _normalize_block(expected_block)
        self.checks.append(CheckPoint(x, y, z, block, description))

    def add_checks(self, checks: list[tuple]):
        """批量注册: [(x, y, z, block, desc), ...]"""
        for item in checks:
            self.add_check(*item)

    def add_area_check(
        self,
        x1: int, y1: int, z1: int,
        x2: int, y2: int, z2: int,
        expected_block: str,
        description: str = "",
        max_samples: int = 13,
    ):
        """注册区域检查 — 四角 + 边中点 + 中心 + 随机采样

        对于大区域，保证至少覆盖结构性位置（角、边、中心），
        再用随机点填充到 max_samples。
        """
        block = _normalize_block(expected_block)
        lx, hx = sorted([x1, x2])
        ly, hy = sorted([y1, y2])
        lz, hz = sorted([z1, z2])

        # 确定性采样点：8 角 + 中心
        deterministic = set()
        for x in (lx, hx):
            for y in (ly, hy):
                for z in (lz, hz):
                    deterministic.add((x, y, z))
        # 中心
        mx, my, mz = (lx + hx) // 2, (ly + hy) // 2, (lz + hz) // 2
        deterministic.add((mx, my, mz))
        # 各面中心（6 面）
        deterministic.add((mx, ly, mz))
        deterministic.add((mx, hy, mz))
        deterministic.add((lx, my, mz))
        deterministic.add((hx, my, mz))
        deterministic.add((mx, my, lz))
        deterministic.add((mx, my, hz))

        samples = list(deterministic)

        # 随机补充
        remaining = max_samples - len(samples)
        if remaining > 0:
            rng = random.Random(hash((lx, ly, lz, hx, hy, hz)))  # 可复现
            for _ in range(remaining * 3):  # 多尝试几次避免重复
                if len(samples) >= max_samples:
                    break
                pt = (
                    rng.randint(lx, hx),
                    rng.randint(ly, hy),
                    rng.randint(lz, hz),
                )
                if pt not in deterministic:
                    samples.append(pt)
                    deterministic.add(pt)

        for x, y, z in samples:
            self.checks.append(
                CheckPoint(x, y, z, block, f"{description} @({x},{y},{z})")
            )

    def clear_checks(self):
        """清空所有已注册的检查点"""
        self.checks.clear()

    # ── 执行验证 ──

    def check_block(self, x: int, y: int, z: int, expected_block: str) -> bool:
        """无损检测单个方块是否匹配

        使用 execute if block 命令 — 纯读取，不修改世界状态。
        比 fill replace + setblock 还原的方案安全得多。
        """
        block = _normalize_block(expected_block)
        # execute if block 在匹配时返回 "Test passed"
        # 不匹配时返回空或 "Test failed"
        resp = self.b.cmd(
            f"execute if block {x} {y} {z} {block} run say __VERIFY_OK__"
        )
        return "Test passed" in resp or "__VERIFY_OK__" in resp

    def verify_all(self) -> dict:
        """执行所有已注册的检查，返回汇总结果

        Returns:
            {
                "total": int,
                "passed": int,
                "failed": int,
                "pass_rate": float,       # 0.0 ~ 1.0
                "all_passed": bool,
                "failures": [
                    {"x": int, "y": int, "z": int, "expected": str, "desc": str},
                    ...
                ],
                "passes": [
                    {"x": int, "y": int, "z": int, "expected": str, "desc": str},
                    ...
                ],
            }
        """
        if not self.checks:
            return {
                "total": 0, "passed": 0, "failed": 0,
                "pass_rate": 1.0, "all_passed": True,
                "failures": [], "passes": [],
            }

        passes = []
        failures = []

        for cp in self.checks:
            ok = self.check_block(cp.x, cp.y, cp.z, cp.expected)
            entry = {
                "x": cp.x, "y": cp.y, "z": cp.z,
                "expected": cp.expected, "desc": cp.desc,
            }
            if ok:
                passes.append(entry)
            else:
                failures.append(entry)

        total = len(self.checks)
        passed = len(passes)
        return {
            "total": total,
            "passed": passed,
            "failed": total - passed,
            "pass_rate": passed / total if total else 1.0,
            "all_passed": len(failures) == 0,
            "failures": failures,
            "passes": passes,
        }

    def verify_building(self, building_config: dict) -> dict:
        """从建筑 config 自动生成检查点并验证

        根据建筑类型自动选择合适的检查模板。
        """
        self.clear_checks()
        checks = auto_checks_from_config(building_config)
        self.add_checks(checks)
        result = self.verify_all()
        result["building"] = building_config.get("name", "unknown")
        return result

    def verify_connectivity(
        self,
        ax: int, ay: int, az: int,
        bx: int, by: int, bz: int,
        step: int = 1,
    ) -> dict:
        """验证两点之间是否可通行

        沿直线采样，检查每个采样点：
          - 脚下 (y) 有实体方块（非 air）
          - 头部 (y+1) 和上方 (y+2) 是 air（2格高通行空间）

        Args:
            ax, ay, az: 起点（脚下位置）
            bx, by, bz: 终点（脚下位置）
            step: 采样间隔（格数）

        Returns:
            {"passable": bool, "total_points": int, "blocked": [...]}
        """
        # 简单 Bresenham 采样
        dx = bx - ax
        dz = bz - az
        dist = max(abs(dx), abs(dz), 1)
        num_samples = dist // step + 1

        blocked = []
        for i in range(num_samples):
            t = i / max(num_samples - 1, 1)
            x = round(ax + dx * t)
            z = round(az + dz * t)
            # Y 取起终点线性插值（适应坡道）
            y = round(ay + (by - ay) * t)

            # 脚下应有实体方块
            has_ground = not self.check_block(x, y, z, "minecraft:air")
            # 头部两格应该是 air
            head_clear = self.check_block(x, y + 1, z, "minecraft:air")
            above_clear = self.check_block(x, y + 2, z, "minecraft:air")

            if not (has_ground and head_clear and above_clear):
                reasons = []
                if not has_ground:
                    reasons.append("no_ground")
                if not head_clear:
                    reasons.append("head_blocked")
                if not above_clear:
                    reasons.append("above_blocked")
                blocked.append({
                    "x": x, "y": y, "z": z,
                    "reasons": reasons,
                })

        return {
            "passable": len(blocked) == 0,
            "total_points": num_samples,
            "blocked": blocked,
        }

    # ── 报告 ──

    @staticmethod
    def print_report(result: dict):
        """打印人类可读的验证报告"""
        name = result.get("building", "")
        header = f"=== 验证报告: {name} ===" if name else "=== 验证报告 ==="
        print(header)
        total = result["total"]
        passed = result["passed"]
        failed = result["failed"]
        rate = result["pass_rate"]

        status = "ALL PASS" if result["all_passed"] else "HAS FAILURES"
        print(f"  状态: {status}")
        print(f"  通过: {passed}/{total} ({rate:.0%})")

        if result["failures"]:
            print(f"  失败 ({failed}):")
            for f in result["failures"]:
                desc = f["desc"] or "unnamed"
                print(f"    FAIL {desc}: ({f['x']},{f['y']},{f['z']}) "
                      f"期望 {f['expected']}")
        print()


# ═══════════════════════════════════════════
# 工具函数
# ═══════════════════════════════════════════

def _normalize_block(block: str) -> str:
    """确保方块 ID 带 minecraft: 前缀"""
    if not block.startswith("minecraft:"):
        block = f"minecraft:{block}"
    return block


# ═══════════════════════════════════════════
# 预置检查模板
# ═══════════════════════════════════════════

def get_pavilion_checks(
    cx: int, cz: int, ground_y: int,
    pillar_h: int = 6,
    size_x: int = 15, size_z: int = 15,
    **_extra,
) -> list[tuple]:
    """亭子（攒尖顶）标准检查点

    检查: 台基四角、柱子、宝顶、入口通行性
    """
    checks = []
    r_base_x = size_x // 2
    r_base_z = size_z // 2

    # 台基四角 — 石砖
    for dx, dz in [
        (-r_base_x, -r_base_z), (r_base_x, -r_base_z),
        (-r_base_x, r_base_z), (r_base_x, r_base_z),
    ]:
        checks.append((
            cx + dx, ground_y + 1, cz + dz,
            "minecraft:stone_bricks", "台基角"
        ))

    # 柱位 — 绛红菌茎（缩进 2 格）
    r_col_x = r_base_x - 2
    r_col_z = r_base_z - 2
    for dx, dz in [
        (-r_col_x, -r_col_z), (r_col_x, -r_col_z),
        (-r_col_x, r_col_z), (r_col_x, r_col_z),
    ]:
        checks.append((
            cx + dx, ground_y + 3, cz + dz,
            "minecraft:stripped_crimson_stem", "柱子"
        ))

    # 宝顶 — 避雷针
    checks.append((
        cx, ground_y + pillar_h + 8, cz,
        "minecraft:lightning_rod", "宝顶"
    ))

    # 入口通行（四面皆空）
    for desc, dx, dz in [
        ("北入口", 0, -r_col_z),
        ("南入口", 0, r_col_z),
        ("西入口", -r_col_x, 0),
        ("东入口", r_col_x, 0),
    ]:
        checks.append((
            cx + dx, ground_y + 3, cz + dz,
            "minecraft:air", desc
        ))

    return checks


def get_hall_checks(
    cx: int, cz: int, ground_y: int,
    pillar_h: int = 6,
    size_x: int = 19, size_z: int = 11,
    facing: str = "north",
    **_extra,
) -> list[tuple]:
    """厅堂（歇山/悬山）标准检查点

    检查: 台基四角、柱列、屋脊中心、正面入口通行
    """
    checks = []
    hx = size_x // 2
    hz = size_z // 2

    # 台基四角
    for dx, dz in [(-hx, -hz), (hx, -hz), (-hx, hz), (hx, hz)]:
        checks.append((
            cx + dx, ground_y + 1, cz + dz,
            "minecraft:stone_bricks", "台基角"
        ))

    # 四角柱位
    r_col_x = hx - 1
    r_col_z = hz - 1
    for dx, dz in [
        (-r_col_x, -r_col_z), (r_col_x, -r_col_z),
        (-r_col_x, r_col_z), (r_col_x, r_col_z),
    ]:
        checks.append((
            cx + dx, ground_y + 3, cz + dz,
            "minecraft:stripped_crimson_stem", "柱子"
        ))

    # 屋脊中心 — 应有方块（非 air）
    checks.append((
        cx, ground_y + pillar_h + 4, cz,
        "minecraft:polished_andesite", "屋脊中心"
    ))

    # 地面中心 — 光滑石
    checks.append((
        cx, ground_y + 1, cz,
        "minecraft:smooth_stone", "室内地面"
    ))

    # 正面入口通行
    entry_offsets = {
        "north": (0, -hz),
        "south": (0, hz),
        "east": (hx, 0),
        "west": (-hx, 0),
    }
    if facing in entry_offsets:
        ex, ez = entry_offsets[facing]
        checks.append((
            cx + ex, ground_y + 3, cz + ez,
            "minecraft:air", f"{facing}入口通行"
        ))

    return checks


def get_water_pavilion_checks(
    cx: int, cz: int, ground_y: int,
    pillar_h: int = 5,
    size_x: int = 9, size_z: int = 7,
    facing: str = "south",
    **_extra,
) -> list[tuple]:
    """水榭/临水建筑检查点

    额外检查: 下方是否有水
    """
    checks = get_hall_checks(
        cx=cx, cz=cz, ground_y=ground_y,
        pillar_h=pillar_h, size_x=size_x, size_z=size_z,
        facing=facing,
    )
    # 水面检查 — 建筑下方应有水
    from config_v3 import WATER_SURFACE_Y
    checks.append((
        cx, WATER_SURFACE_Y, cz,
        "minecraft:water", "下方水面"
    ))
    return checks


def get_corridor_checks(
    waypoints: list[tuple],
    ground_y: int = -60,
    surface: str = "minecraft:stone_bricks",
    width: int = 5,
    roofed: bool = True,
    pillar_h: int = 4,
    **_extra,
) -> list[tuple]:
    """廊道检查点 — 检查路面和通行性

    在每个 waypoint 处检查：地面材质、头顶空间。
    """
    checks = []
    surface = _normalize_block(surface) if surface else "minecraft:stone_bricks"

    for i, (wx, wz) in enumerate(waypoints):
        # 地面方块
        checks.append((
            wx, ground_y, wz,
            surface, f"路点{i}地面"
        ))
        # 通行空间 — 人站的两格应为 air
        checks.append((
            wx, ground_y + 1, wz,
            "minecraft:air", f"路点{i}脚部空间"
        ))
        checks.append((
            wx, ground_y + 2, wz,
            "minecraft:air", f"路点{i}头部空间"
        ))

    return checks


def get_wall_checks(
    perimeter: list[tuple],
    ground_y: int = -60,
    height: int = 5,
    **_extra,
) -> list[tuple]:
    """围墙检查点 — 四角 + 墙体高度"""
    checks = []
    for i, (px, pz) in enumerate(perimeter):
        # 墙基
        checks.append((
            px, ground_y + 1, pz,
            "minecraft:stone_bricks", f"墙角{i}基"
        ))
        # 墙顶
        checks.append((
            px, ground_y + height, pz,
            "minecraft:stone_brick_slab", f"墙角{i}顶"
        ))
    return checks


# ═══════════════════════════════════════════
# 自动检查点生成
# ═══════════════════════════════════════════

def auto_checks_from_config(cfg: dict) -> list[tuple]:
    """根据建筑 config 自动选择检查模板

    识别逻辑:
      - over_water=True → get_water_pavilion_checks
      - roof_type='hip_pointed' 或 facing='all' → get_pavilion_checks
      - 有 pillar_h → get_hall_checks
      - 否则 → 最基础的台基检查
    """
    if cfg.get("over_water"):
        return get_water_pavilion_checks(**cfg)
    if cfg.get("roof_type") == "hip_pointed" or cfg.get("facing") == "all":
        if cfg.get("pillar_h"):
            return get_pavilion_checks(**cfg)
    if cfg.get("pillar_h"):
        return get_hall_checks(**cfg)

    # 最基础: 只检查中心点地面
    cx = cfg.get("cx", 0)
    cz = cfg.get("cz", 0)
    gy = cfg.get("ground_y", -60)
    return [(cx, gy + 1, cz, "minecraft:stone_bricks", "中心地面")]


# ═══════════════════════════════════════════
# 批量验证所有建筑
# ═══════════════════════════════════════════

def verify_all_buildings(builder: "MinecraftBuilder", buildings: list[dict]) -> dict:
    """验证 ALL_BUILDINGS 列表中的每栋建筑

    Returns:
        {
            "summary": {"total": N, "passed": N, "failed": N},
            "buildings": [
                {"name": "...", "passed": N, "total": N, "failures": [...]},
                ...
            ],
        }
    """
    v = BuildingVerifier(builder)
    all_results = []
    total_checks = 0
    total_passed = 0

    for cfg in buildings:
        result = v.verify_building(cfg)
        all_results.append(result)
        total_checks += result["total"]
        total_passed += result["passed"]
        v.print_report(result)

    summary = {
        "total": total_checks,
        "passed": total_passed,
        "failed": total_checks - total_passed,
    }

    print("=" * 50)
    print(f"总计: {summary['passed']}/{summary['total']} 检查通过 "
          f"({summary['passed']/max(summary['total'],1):.0%})")
    if summary["failed"]:
        print(f"  {summary['failed']} 项失败，需要修复")
    else:
        print("  全部通过!")

    return {"summary": summary, "buildings": all_results}


# ═══════════════════════════════════════════
# 游线验证
# ═══════════════════════════════════════════

def verify_tour_route(
    builder: "MinecraftBuilder",
    stops: list[tuple],
    ground_y: int = -60,
) -> dict:
    """验证游览路线的连通性

    对路线中相邻的每对站点调用 verify_connectivity。

    Args:
        stops: [(name, x, z), ...]
        ground_y: 默认地面 Y
    """
    v = BuildingVerifier(builder)
    segments = []

    for i in range(len(stops) - 1):
        name_a, ax, az = stops[i]
        name_b, bx, bz = stops[i + 1]
        result = v.verify_connectivity(
            ax, ground_y, az,
            bx, ground_y, bz,
            step=2,
        )
        segment = {
            "from": name_a, "to": name_b,
            "passable": result["passable"],
            "blocked_count": len(result["blocked"]),
            "blocked": result["blocked"],
        }
        segments.append(segment)

        status = "OK" if result["passable"] else f"BLOCKED x{len(result['blocked'])}"
        print(f"  {name_a} -> {name_b}: {status}")

    all_pass = all(s["passable"] for s in segments)
    print(f"\n游线连通性: {'全部畅通' if all_pass else '存在阻断'}")
    return {"all_passable": all_pass, "segments": segments}


# ═══════════════════════════════════════════
# CLI 入口
# ═══════════════════════════════════════════

if __name__ == "__main__":
    import sys
    from builder import MinecraftBuilder
    from config_v3 import ALL_BUILDINGS, MAIN_TOUR

    mode = sys.argv[1] if len(sys.argv) > 1 else "all"

    with MinecraftBuilder() as b:
        if mode == "all":
            print(">>> 验证所有建筑...")
            verify_all_buildings(b, ALL_BUILDINGS)
        elif mode == "tour":
            print(">>> 验证游览路线...")
            verify_tour_route(b, MAIN_TOUR["stops"])
        elif mode == "building":
            # python verifier.py building 牡丹亭
            target = sys.argv[2] if len(sys.argv) > 2 else ""
            for cfg in ALL_BUILDINGS:
                if cfg.get("name") == target:
                    v = BuildingVerifier(b)
                    result = v.verify_building(cfg)
                    v.print_report(result)
                    break
            else:
                print(f"未找到建筑: {target}")
                print(f"可用: {[c['name'] for c in ALL_BUILDINGS]}")
        else:
            print("用法: python verifier.py [all|tour|building <name>]")
