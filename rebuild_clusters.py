"""rebuild_clusters.py — 总调度脚本

基于 config_v4 的群组化重建流程:
  Phase 1: 水面系统 (复用 phase1_water.py)
  Phase 2: 围墙 (外围墙 + 内部花墙)
  Phase 3: 主环廊骨架
  Phase 4: 5个群组建筑
  Phase 5: 细节 (植被/灯笼/做旧)

用法:
    python rebuild_clusters.py          # 完整重建
    python rebuild_clusters.py verify   # 仅验证碰撞
    python rebuild_clusters.py clear    # 仅清空世界
    python rebuild_clusters.py phase N  # 执行单个 phase (1~5)

注意: 群组 A~D 的 build_cluster_X 函数需要后续补充对应文件。
      当前只有 E群(cluster_e) 和 主环廊(corridors) 是完整实现。
"""

import sys
import time

sys.path.insert(0, '/Users/lambertlin/minecraft-server/scripts')

from builder import MinecraftBuilder
import config_v4 as cfg


# ═══════════════════════════════════════════
# 碰撞检测 (复用 rebuild_v4 逻辑)
# ═══════════════════════════════════════════

COLLISION_MARGIN = 3

def _get_buffered_bbox(building):
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
    if a is None or b is None:
        return False
    return (a[0] < b[2] and a[2] > b[0] and
            a[1] < b[3] and a[3] > b[1])


def verify_collisions():
    """验证所有建筑碰撞"""
    buildings = cfg.ALL_BUILDINGS
    allowed = set()
    for a_name, b_name in cfg.ALLOWED_COLLISION_PAIRS:
        allowed.add((a_name, b_name))
        allowed.add((b_name, a_name))

    collision_count = 0
    lines = ["=" * 60, "=== 碰撞检测 (margin=3) ===", "=" * 60]

    for i in range(len(buildings)):
        for j in range(i + 1, len(buildings)):
            a, b = buildings[i], buildings[j]
            a_name = a.get("name", f"building_{i}")
            b_name = b.get("name", f"building_{j}")
            if (a_name, b_name) in allowed:
                continue
            ba = _get_buffered_bbox(a)
            bb = _get_buffered_bbox(b)
            if _aabb_overlap(ba, bb):
                collision_count += 1
                lines.append(f"  COLLISION #{collision_count}: {a_name} vs {b_name}")

    if collision_count == 0:
        lines.append("  ALL CLEAR!")
    else:
        lines.append(f"\n  {collision_count} collisions found!")

    report = "\n".join(lines)
    return collision_count, report


# ═══════════════════════════════════════════
# Phase 0: 清空世界
# ═══════════════════════════════════════════

def phase0_clear(b):
    """清空整个园林区域"""
    print("=" * 60)
    print("Phase 0: 清空世界")
    print("=" * 60)

    garden = cfg.GARDEN
    y_min = cfg.DEEP_POOL_BOTTOM_Y - 1   # -66
    y_max = cfg.BUILD_Y + 20              # -40

    b.fill(garden["x_min"], y_min, garden["z_min"],
           garden["x_max"], y_max, garden["z_max"],
           "minecraft:air")

    # 恢复基底草方块层
    b.fill(garden["x_min"], cfg.GROUND_Y, garden["z_min"],
           garden["x_max"], cfg.GROUND_Y, garden["z_max"],
           "minecraft:grass_block")

    print(f"  Phase 0 done ({b.cmd_count} commands)")


# ═══════════════════════════════════════════
# Phase 1: 水面系统
# ═══════════════════════════════════════════

def phase1_water(b):
    """复用 phase1_water.py"""
    print("=" * 60)
    print("Phase 1: 水面系统")
    print("=" * 60)

    cmd_start = b.cmd_count

    # 动态 patch: 让 phase1_water 用 config_v4
    import config_v4
    sys.modules['config_v3'] = config_v4

    if 'phase1_water' in sys.modules:
        del sys.modules['phase1_water']
    import phase1_water as p1

    # 逐步调用
    if hasattr(p1, 'build_highland'):
        p1.build_highland(b)
    if hasattr(p1, 'build_main_lake'):
        p1.build_main_lake(b)
    if hasattr(p1, 'build_creek'):
        p1.build_creek(b)
    if hasattr(p1, 'build_creek_pool'):
        p1.build_creek_pool(b)
    if hasattr(p1, 'build_deep_pool'):
        p1.build_deep_pool(b)
    if hasattr(p1, 'build_pool_creek'):
        p1.build_pool_creek(b)

    print(f"  Phase 1 done ({b.cmd_count - cmd_start} commands)")


# ═══════════════════════════════════════════
# Phase 2: 围墙
# ═══════════════════════════════════════════

def phase2_walls(b):
    """外围墙 + 内部花墙"""
    print("=" * 60)
    print("Phase 2: 围墙")
    print("=" * 60)

    cmd_start = b.cmd_count

    import config_v4
    sys.modules['config_v3'] = config_v4

    if 'phase2_corridors' in sys.modules:
        del sys.modules['phase2_corridors']
    import phase2_corridors as p2

    if hasattr(p2, 'build_outer_wall'):
        p2.build_outer_wall(b)
    if hasattr(p2, 'build_inner_walls'):
        p2.build_inner_walls(b)
    if hasattr(p2, 'build_bridges'):
        p2.build_bridges(b)

    print(f"  Phase 2 done ({b.cmd_count - cmd_start} commands)")


# ═══════════════════════════════════════════
# Phase 3: 主环廊骨架
# ═══════════════════════════════════════════

def phase3_corridors(b):
    """主环廊 + 群组间路径"""
    print("=" * 60)
    print("Phase 3: 主环廊骨架")
    print("=" * 60)

    cmd_start = b.cmd_count

    from clusters.corridors import build_main_corridors
    build_main_corridors(b)

    print(f"  Phase 3 done ({b.cmd_count - cmd_start} commands)")


# ═══════════════════════════════════════════
# Phase 4: 5个群组
# ═══════════════════════════════════════════

def _try_import_cluster(name, module_path, func_name):
    """安全导入群组建造函数，未实现则返回 None"""
    try:
        mod = __import__(module_path, fromlist=[func_name])
        return getattr(mod, func_name)
    except (ImportError, AttributeError) as e:
        print(f"    [SKIP] {name}: {e}")
        return None


def phase4_clusters(b):
    """5个群组建筑 — 按从小到大顺序"""
    print("=" * 60)
    print("Phase 4: 5个群组")
    print("=" * 60)

    cmd_start = b.cmd_count

    # C群: 最小，先试点 (听雨轩+荼蘼花架)
    build_c = _try_import_cluster("C群", "clusters.cluster_c", "build_cluster_c")
    if build_c:
        build_c(b)

    # D群: 入口序列 (入口门厅+小庭+远香堂+闺塾)
    build_d = _try_import_cluster("D群", "clusters.cluster_d", "build_cluster_d")
    if build_d:
        build_d(b)

    # A群: 北岸梦境 (牡丹亭+芍药阑+太湖石+秋千+濯缨水阁)
    build_a = _try_import_cluster("A群", "clusters.cluster_a", "build_cluster_a")
    if build_a:
        build_a(b)

    # B群: 西园幽趣 (翠轩+梅花庵观+大梅树+池馆+画船)
    build_b = _try_import_cluster("B群", "clusters.cluster_b", "build_cluster_b")
    if build_b:
        build_b(b)

    # E群: 东岸舫舟 (石舫+曲廊亭+半亭) — 已实现
    from clusters.cluster_e import build_cluster_e
    build_cluster_e(b)

    print(f"  Phase 4 done ({b.cmd_count - cmd_start} commands)")


# ═══════════════════════════════════════════
# Phase 5: 细节
# ═══════════════════════════════════════════

def phase5_details(b):
    """植被 / 灯笼 / 做旧"""
    print("=" * 60)
    print("Phase 5: 细节")
    print("=" * 60)

    cmd_start = b.cmd_count

    import config_v4
    sys.modules['config_v3'] = config_v4

    if 'phase4_details' in sys.modules:
        del sys.modules['phase4_details']

    try:
        import phase4_details as p4
        if hasattr(p4, 'build_all'):
            p4.build_all(b)
        elif hasattr(p4, 'main'):
            p4.main(b)
        else:
            print("  [!] phase4_details 无统一入口，尝试逐步调用...")
            for func_name in ['build_willows', 'build_flowers', 'build_lily_pads',
                              'build_lanterns', 'add_weathering']:
                if hasattr(p4, func_name):
                    getattr(p4, func_name)(b)
    except ImportError:
        print("  [SKIP] phase4_details not available")

    print(f"  Phase 5 done ({b.cmd_count - cmd_start} commands)")


# ═══════════════════════════════════════════
# 总调度
# ═══════════════════════════════════════════

def rebuild_all(b):
    """完整重建流程"""
    print("Phase 1: 水面")
    phase1_water(b)

    print("\nPhase 2: 围墙")
    phase2_walls(b)

    print("\nPhase 3: 主环廊骨架")
    phase3_corridors(b)

    print("\nPhase 4: 5个群组")
    phase4_clusters(b)

    print("\nPhase 5: 细节")
    phase5_details(b)


def full_rebuild():
    """完整重建 (含清空+验证)"""
    start_time = time.time()

    # 先碰撞检测
    collision_count, report = verify_collisions()
    print(report)
    if collision_count > 0:
        print("\n!!! 碰撞检测未通过，中止重建 !!!")
        return False

    print("\n碰撞检测通过，开始重建...\n")

    with MinecraftBuilder() as b:
        phase0_clear(b)
        rebuild_all(b)

        elapsed = time.time() - start_time
        print(f"\n{'=' * 60}")
        print(f"建造完成! 共 {b.cmd_count} 条命令, 耗时 {elapsed:.1f}s")
        print(f"{'=' * 60}")

        # 传送到入口
        b.tp_player("@a", 58, -58, 90)

    return True


# ═══════════════════════════════════════════
# CLI 入口
# ═══════════════════════════════════════════

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "full"

    if mode == "verify":
        collision_count, report = verify_collisions()
        print(report)
        sys.exit(0 if collision_count == 0 else 1)

    elif mode == "clear":
        with MinecraftBuilder() as b:
            phase0_clear(b)

    elif mode == "full":
        success = full_rebuild()
        sys.exit(0 if success else 1)

    elif mode == "phase":
        phase_num = int(sys.argv[2]) if len(sys.argv) > 2 else 0
        phase_map = {
            0: phase0_clear,
            1: phase1_water,
            2: phase2_walls,
            3: phase3_corridors,
            4: phase4_clusters,
            5: phase5_details,
        }
        if phase_num not in phase_map:
            print(f"Unknown phase: {phase_num} (valid: 0~5)")
            sys.exit(1)

        with MinecraftBuilder() as b:
            phase_map[phase_num](b)
            print(f"\nPhase {phase_num} done! {b.cmd_count} commands")

    elif mode == "e":
        # 快捷: 只建 E群
        with MinecraftBuilder() as b:
            from clusters.cluster_e import build_cluster_e
            build_cluster_e(b)
            print(f"Done! {b.cmd_count} commands")

    elif mode == "corridors":
        # 快捷: 只建主环廊
        with MinecraftBuilder() as b:
            from clusters.corridors import build_main_corridors
            build_main_corridors(b)
            print(f"Done! {b.cmd_count} commands")

    else:
        print("用法: python rebuild_clusters.py [mode]")
        print("  full       — 完整重建 (默认)")
        print("  verify     — 仅碰撞验证")
        print("  clear      — 仅清空世界")
        print("  phase N    — 执行单个 phase (0~5)")
        print("  e          — 只建 E群")
        print("  corridors  — 只建主环廊")
        sys.exit(1)
