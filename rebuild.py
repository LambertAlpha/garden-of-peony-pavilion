"""rebuild.py -- 一键重建脚本

基于 config_v4 的群组化重建流程:
  Phase 1: 清空世界 + 水面系统
  Phase 2: 围墙 + 廊道骨架
  Phase 3: 5 个群组建筑 (A~E)
  Phase 4: 主环廊 + 群组间连接
  Phase 5: 景观填充 (铺地/植被/做旧)

用法:
    python rebuild.py              # 完整重建
    python rebuild.py verify       # 仅碰撞验证 (不需要 RCON)
    python rebuild.py clear        # 仅清空世界
    python rebuild.py phase N      # 执行单个 phase (1~5)
"""

import sys
import time
from pathlib import Path

# 确保项目根目录在 sys.path 中
sys.path.insert(0, str(Path(__file__).resolve().parent))

from core.builder import MinecraftBuilder
from config import config_v4 as cfg


# ═══════════════════════════════════════════
# 碰撞检测 (纯计算，不需要 RCON)
# ═══════════════════════════════════════════

COLLISION_MARGIN = 3

def _get_buffered_bbox(building):
    """获取建筑含外延的 AABB"""
    m = COLLISION_MARGIN
    if "cx" in building and "size_x" in building:
        cx, cz = building["cx"], building["cz"]
        hx = building["size_x"] // 2
        hz = building["size_z"] // 2
        return (cx - hx - m, cz - hz - m, cx + hx + m, cz + hz + m)
    elif "x" in building:
        x, z = building["x"], building["z"]
        return (x - m, z - m, x + m, z + m)
    return None


def _aabb_overlap(a, b):
    """两个 AABB (x1,z1,x2,z2) 是否重叠"""
    if a is None or b is None:
        return False
    return (a[0] < b[2] and a[2] > b[0] and
            a[1] < b[3] and a[3] > b[1])


# 允许碰撞的建筑对 (一体化设计)
ALLOWED_OVERLAPS = {
    frozenset({"入口门厅", "小庭深院"}),
    frozenset({"秋千", "太湖石组"}),
}


def verify_collisions():
    """检查所有建筑碰撞"""
    buildings = cfg.ALL_BUILDINGS  # 这是一个列表
    collisions = []
    for i in range(len(buildings)):
        for j in range(i + 1, len(buildings)):
            a_name = buildings[i]["name"]
            b_name = buildings[j]["name"]
            a_bbox = _get_buffered_bbox(buildings[i])
            b_bbox = _get_buffered_bbox(buildings[j])
            if _aabb_overlap(a_bbox, b_bbox):
                pair = frozenset({a_name, b_name})
                if pair not in ALLOWED_OVERLAPS:
                    collisions.append((a_name, b_name))

    if collisions:
        print(f"[WARN] {len(collisions)} 对碰撞:")
        for a, b in collisions:
            print(f"  - {a} <-> {b}")
        return False
    else:
        print("[OK] 碰撞检测通过，0 对碰撞")
        return True


# ═══════════════════════════════════════════
# Phase 执行器
# ═══════════════════════════════════════════

def phase_clear(b: MinecraftBuilder):
    """Phase 0: 彻底清空整个园林区域（含高处树冠/屋顶）"""
    print("=== Phase 0: 彻底清空世界 ===")
    g = cfg.GARDEN
    # 从 Y=-65 到 Y=-20 全部清空（覆盖地下到最高树冠/屋顶）
    # 分两段清除避免超出 fill 体积限制
    print("  清空下半部分 (Y=-65 ~ -40)...")
    b.fill(g["x_min"], -65, g["z_min"],
           g["x_max"], -40, g["z_max"],
           "minecraft:air")
    print("  清空上半部分 (Y=-39 ~ -20)...")
    b.fill(g["x_min"], -39, g["z_min"],
           g["x_max"], -20, g["z_max"],
           "minecraft:air")
    # 铺回草方块底层
    print("  铺回草地...")
    b.fill(g["x_min"], cfg.GROUND_Y, g["z_min"],
           g["x_max"], cfg.GROUND_Y, g["z_max"],
           "minecraft:grass_block")
    # 草方块下方铺 dirt 防止露底
    b.fill(g["x_min"], cfg.GROUND_Y - 1, g["z_min"],
           g["x_max"], cfg.GROUND_Y - 1, g["z_max"],
           "minecraft:dirt")
    b.fill(g["x_min"], cfg.GROUND_Y - 2, g["z_min"],
           g["x_max"], cfg.GROUND_Y - 2, g["z_max"],
           "minecraft:dirt")
    b.fill(g["x_min"], cfg.GROUND_Y - 3, g["z_min"],
           g["x_max"], cfg.GROUND_Y - 3, g["z_max"],
           "minecraft:dirt")
    print(f"  已彻底清空 {g['x_max']}x{g['z_max']} 区域 (Y=-65 ~ -20)")


def phase1_water(b: MinecraftBuilder):
    """Phase 1: 水面系统"""
    print("=== Phase 1: 水面系统 ===")
    from phases.phase1_water import (
        build_highland, build_main_lake, build_creek,
        build_creek_pool, build_deep_pool, build_pool_creek,
    )
    build_highland(b)
    build_main_lake(b)
    build_creek(b)
    build_creek_pool(b)
    build_deep_pool(b)
    build_pool_creek(b)
    print("  水面系统完成")


def phase1_5_terrain(b: MinecraftBuilder):
    """Phase 1.5: 所有地形堆高（必须在围墙/廊道之前！）"""
    print("=== Phase 1.5: 地形系统 ===")
    from clusters.cluster_a import build_cluster_a_terrain
    build_cluster_a_terrain(b)
    print("  地形系统完成")


def phase2_walls_corridors(b: MinecraftBuilder):
    """Phase 2: 围墙 + 廊道骨架"""
    print("=== Phase 2: 围墙 + 廊道 ===")
    from phases.phase2_corridors import (
        build_outer_wall, build_inner_walls, build_corridors, build_bridges,
    )
    build_outer_wall(b)
    build_inner_walls(b)
    build_corridors(b)
    build_bridges(b)
    print("  围墙 + 廊道完成")


def phase3_clusters(b: MinecraftBuilder):
    """Phase 3: 5 个建筑群组"""
    print("=== Phase 3: 建筑群组 ===")
    from clusters.cluster_a import build_cluster_a
    from clusters.cluster_b import build_cluster_b
    from clusters.cluster_c import build_cluster_c
    from clusters.cluster_d import build_cluster_d
    from clusters.cluster_e import build_cluster_e

    for name, builder_fn in [
        ("A群-北岸梦境", build_cluster_a),
        ("B群-西园梅林", build_cluster_b),
        ("C群-花听长廊", build_cluster_c),
        ("D群-南部中轴", build_cluster_d),
        ("E群-东岸舫舟", build_cluster_e),
    ]:
        print(f"  建造 {name}...")
        builder_fn(b)

    print("  5 个群组全部完成")


def phase4_connections(b: MinecraftBuilder):
    """Phase 4: 主环廊 + 群组间连接"""
    print("=== Phase 4: 主环廊 + 连接 ===")
    from clusters.corridors import build_main_corridors
    build_main_corridors(b)
    print("  廊道连接完成")


def phase5_landscape(b: MinecraftBuilder):
    """Phase 5: 景观填充"""
    print("=== Phase 5: 景观填充 ===")
    from phases.phase5_landscape import build_all_landscape
    build_all_landscape(b)
    print("  景观填充完成")


# ═══════════════════════════════════════════
# 主入口
# ═══════════════════════════════════════════

PHASES = {
    0: ("清空世界", phase_clear),
    1: ("水面系统", phase1_water),
    2: ("围墙+廊道", phase2_walls_corridors),
    3: ("建筑群组", phase3_clusters),
    4: ("主环廊连接", phase4_connections),
    5: ("景观填充", phase5_landscape),
}


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "all"

    if mode == "verify":
        verify_collisions()
        return

    if mode == "phase":
        n = int(sys.argv[2])
        if n not in PHASES:
            print(f"无效 phase: {n}，可选 0~5")
            return
        with MinecraftBuilder() as b:
            PHASES[n][1](b)
            print(f"\n命令总数: {b.cmd_count}")
        return

    if mode == "clear":
        with MinecraftBuilder() as b:
            phase_clear(b)
            print(f"\n命令总数: {b.cmd_count}")
        return

    # 默认: 完整重建
    print("=" * 60)
    print("牡丹亭·游园惊梦 — 完整重建")
    print("=" * 60)

    # 先验证碰撞
    if not verify_collisions():
        print("\n碰撞检测失败，中止重建。请先修复 config_v4.py")
        return

    t0 = time.time()
    with MinecraftBuilder() as b:
        phase_clear(b)
        phase1_water(b)
        phase1_5_terrain(b)
        phase2_walls_corridors(b)
        phase3_clusters(b)
        phase4_connections(b)
        phase5_landscape(b)

        elapsed = time.time() - t0
        print(f"\n{'=' * 60}")
        print(f"重建完成! 命令总数: {b.cmd_count}, 耗时: {elapsed:.1f}s")
        print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
