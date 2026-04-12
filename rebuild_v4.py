"""rebuild_v4.py — 基于 config_v4 的全世界重建脚本

流程:
  1. 清空整个园林区域 (120x90, Y=-65 ~ -45)
  2. 按 config_v4 执行 phase1→2→3→4
  3. 应用入口一体化重建 (rebuild_entrance, 坐标适配 v4)
  4. 运行碰撞验证

用法:
    python rebuild_v4.py          # 完整重建
    python rebuild_v4.py verify   # 仅验证碰撞
    python rebuild_v4.py clear    # 仅清空世界

注意: 此脚本只写不执行——确认坐标无误后再运行！
"""

import sys
import time

sys.path.insert(0, '/Users/lambertlin/minecraft-server/scripts')

from builder import MinecraftBuilder
import config_v4 as cfg


# ═══════════════════════════════════════════
# 碰撞检测（纯计算，不需要 RCON）
# ═══════════════════════════════════════════

COLLISION_MARGIN = 3  # 每栋建筑外延 3 格

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


def _overlap_area(a, b):
    """重叠面积"""
    ox = max(0, min(a[2], b[2]) - max(a[0], b[0]))
    oz = max(0, min(a[3], b[3]) - max(a[1], b[1]))
    return ox * oz


def verify_collisions():
    """验证所有建筑碰撞，返回 (collision_count, report_str)"""
    buildings = cfg.ALL_BUILDINGS
    allowed = set()
    for a_name, b_name in cfg.ALLOWED_COLLISION_PAIRS:
        allowed.add((a_name, b_name))
        allowed.add((b_name, a_name))

    lines = []
    lines.append("=" * 60)
    lines.append("=== v4 碰撞检测 (margin=3) ===")
    lines.append("=" * 60)

    collision_count = 0

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
                area = _overlap_area(ba, bb)
                collision_count += 1
                lines.append(f"  COLLISION #{collision_count}: {a_name} vs {b_name}")
                lines.append(f"    {a_name}: buf=[{ba[0]},{ba[1]}]-[{ba[2]},{ba[3]}]")
                lines.append(f"    {b_name}: buf=[{bb[0]},{bb[1]}]-[{bb[2]},{bb[3]}]")
                lines.append(f"    overlap area: {area}")

    if collision_count == 0:
        lines.append("  ALL CLEAR — 无碰撞!")
    else:
        lines.append(f"\n  发现 {collision_count} 处碰撞，需要修正!")

    # 入口序列 Z 间距检查
    lines.append("")
    lines.append("=== 入口序列 Z 间距 ===")
    gate = cfg.GATE
    court = cfg.COURTYARD
    hall = cfg.YUAN_XIANG

    gate_z_n = gate["cz"] - gate["size_z"] // 2
    court_z_s = court["cz"] + court["size_z"] // 2
    court_z_n = court["cz"] - court["size_z"] // 2
    hall_z_s = hall["cz"] + hall["size_z"] // 2

    gap1 = gate_z_n - court_z_s
    gap2 = court_z_n - hall_z_s

    lines.append(f"  门厅 Z=[{gate['cz'] - gate['size_z']//2}, {gate['cz'] + gate['size_z']//2}]")
    lines.append(f"  小庭 Z=[{court['cz'] - court['size_z']//2}, {court['cz'] + court['size_z']//2}]")
    lines.append(f"  远香堂 Z=[{hall['cz'] - hall['size_z']//2}, {hall['cz'] + hall['size_z']//2}]")
    lines.append(f"  门厅-小庭 gap: {gap1}")
    lines.append(f"  小庭-远香堂 gap: {gap2}")

    if gap2 >= 5:
        lines.append("  入口序列间距 OK (>=5)")
    else:
        lines.append(f"  WARNING: 小庭-远香堂 gap={gap2} < 5")

    # 边界检查
    lines.append("")
    lines.append("=== 边界检查 (120x90) ===")
    out_of_bounds = 0
    for b in buildings:
        name = b.get("name", "unknown")
        if "cx" in b and "size_x" in b:
            hx = b["size_x"] // 2
            hz = b["size_z"] // 2
            x1, z1 = b["cx"] - hx, b["cz"] - hz
            x2, z2 = b["cx"] + hx, b["cz"] + hz
        elif "x" in b:
            x1, z1, x2, z2 = b["x"], b["z"], b["x"], b["z"]
        else:
            continue
        if x1 < 0 or z1 < 0 or x2 > 120 or z2 > 90:
            lines.append(f"  OUT OF BOUNDS: {name} [{x1},{z1}]-[{x2},{z2}]")
            out_of_bounds += 1

    if out_of_bounds == 0:
        lines.append("  All buildings within bounds!")

    report = "\n".join(lines)
    return collision_count, report


# ═══════════════════════════════════════════
# Step 1: 清空世界
# ═══════════════════════════════════════════

def step1_clear_world(b):
    """清空整个园林区域"""
    print("=" * 60)
    print("=== Step 1: 清空世界 ===")
    print("=" * 60)

    garden = cfg.GARDEN
    x_min = garden["x_min"]
    x_max = garden["x_max"]
    z_min = garden["z_min"]
    z_max = garden["z_max"]

    # 清空从湖底到建筑顶部的所有方块
    y_min = cfg.DEEP_POOL_BOTTOM_Y - 1   # -66
    y_max = cfg.BUILD_Y + 20              # -40

    print(f"  清空范围: X=[{x_min},{x_max}] Y=[{y_min},{y_max}] Z=[{z_min},{z_max}]")
    print(f"  体积: {(x_max-x_min) * (y_max-y_min) * (z_max-z_min)} 方块")

    # 分片清空（fill 单次上限 32768 方块）
    cmd_start = b.cmd_count
    b.fill(x_min, y_min, z_min, x_max, y_max, z_max, "minecraft:air")

    # 恢复基底草方块层
    print("  恢复基底草方块...")
    b.fill(x_min, cfg.GROUND_Y, z_min, x_max, cfg.GROUND_Y, z_max,
           "minecraft:grass_block")

    print(f"  Step 1 完成 ({b.cmd_count - cmd_start} commands)")


# ═══════════════════════════════════════════
# Step 2: Phase 1 — 水面系统
# ═══════════════════════════════════════════

def step2_phase1_water(b):
    """Phase 1: 地形 + 水面"""
    print("=" * 60)
    print("=== Step 2: Phase 1 — 水面系统 ===")
    print("=" * 60)

    cmd_start = b.cmd_count

    # 动态 patch config — 让 phase1_water 使用 config_v4
    import config_v4
    sys.modules['config_v3'] = config_v4

    # 重新加载 phase1_water（它 import config_v3）
    if 'phase1_water' in sys.modules:
        del sys.modules['phase1_water']
    import phase1_water

    # 调用 phase1 的 main 逻辑
    if hasattr(phase1_water, 'build_all'):
        phase1_water.build_all(b)
    elif hasattr(phase1_water, 'main'):
        phase1_water.main(b)
    else:
        # 手动调用各部分
        print("  [!] phase1_water 没有统一入口，尝试逐步调用...")
        if hasattr(phase1_water, 'build_terrain'):
            phase1_water.build_terrain(b)
        if hasattr(phase1_water, 'build_main_lake'):
            phase1_water.build_main_lake(b)
        if hasattr(phase1_water, 'build_creek'):
            phase1_water.build_creek(b)
        if hasattr(phase1_water, 'build_deep_pool'):
            phase1_water.build_deep_pool(b)

    print(f"  Step 2 完成 ({b.cmd_count - cmd_start} commands)")


# ═══════════════════════════════════════════
# Step 3: Phase 2 — 廊道+围墙
# ═══════════════════════════════════════════

def step3_phase2_corridors(b):
    """Phase 2: 廊道 + 围墙 + 桥梁"""
    print("=" * 60)
    print("=== Step 3: Phase 2 — 廊道+围墙 ===")
    print("=" * 60)

    cmd_start = b.cmd_count

    import config_v4
    sys.modules['config_v3'] = config_v4

    if 'phase2_corridors' in sys.modules:
        del sys.modules['phase2_corridors']
    import phase2_corridors

    if hasattr(phase2_corridors, 'build_all'):
        phase2_corridors.build_all(b)
    elif hasattr(phase2_corridors, 'main'):
        phase2_corridors.main(b)
    else:
        print("  [!] phase2_corridors 没有统一入口，尝试逐步调用...")
        if hasattr(phase2_corridors, 'build_wall'):
            phase2_corridors.build_wall(b)
        if hasattr(phase2_corridors, 'build_corridors'):
            phase2_corridors.build_corridors(b)
        if hasattr(phase2_corridors, 'build_bridges'):
            phase2_corridors.build_bridges(b)

    print(f"  Step 3 完成 ({b.cmd_count - cmd_start} commands)")


# ═══════════════════════════════════════════
# Step 4: Phase 3 — 建筑
# ═══════════════════════════════════════════

def step4_phase3_buildings(b):
    """Phase 3: 全部 19 栋建筑"""
    print("=" * 60)
    print("=== Step 4: Phase 3 — 建筑 ===")
    print("=" * 60)

    cmd_start = b.cmd_count

    import config_v4
    sys.modules['config_v3'] = config_v4

    if 'phase3_buildings' in sys.modules:
        del sys.modules['phase3_buildings']
    import phase3_buildings

    if hasattr(phase3_buildings, 'build_all'):
        phase3_buildings.build_all(b)
    elif hasattr(phase3_buildings, 'main'):
        phase3_buildings.main(b)
    else:
        print("  [!] phase3_buildings 没有统一入口")
        print("  需要检查 phase3_buildings.py 的入口函数名")

    print(f"  Step 4 完成 ({b.cmd_count - cmd_start} commands)")


# ═══════════════════════════════════════════
# Step 5: Phase 4 — 景观细节
# ═══════════════════════════════════════════

def step5_phase4_details(b):
    """Phase 4: 植被 / 水面装饰 / 路面 / 灯笼"""
    print("=" * 60)
    print("=== Step 5: Phase 4 — 景观细节 ===")
    print("=" * 60)

    cmd_start = b.cmd_count

    import config_v4
    sys.modules['config_v3'] = config_v4

    if 'phase4_details' in sys.modules:
        del sys.modules['phase4_details']
    import phase4_details

    if hasattr(phase4_details, 'build_all'):
        phase4_details.build_all(b)
    elif hasattr(phase4_details, 'main'):
        phase4_details.main(b)
    else:
        print("  [!] phase4_details 没有统一入口")

    print(f"  Step 5 完成 ({b.cmd_count - cmd_start} commands)")


# ═══════════════════════════════════════════
# Step 6: 入口一体化重建
# ═══════════════════════════════════════════

def step6_rebuild_entrance(b):
    """入口建筑群一体化重建 — 适配 v4 坐标"""
    print("=" * 60)
    print("=== Step 6: 入口一体化重建 ===")
    print("=" * 60)

    cmd_start = b.cmd_count

    # rebuild_entrance 使用硬编码坐标，需要检查是否兼容 v4
    # v4 入口门厅: cx=58, cz=87, 小庭: cx=58, cz=80
    # rebuild_entrance.py 用的是: x1=51,x2=65, z_south=90, z_north=77
    # v4 中入口区域: Z=78~89, 需要适配

    from fixes.rebuild_entrance import build_entrance_complex

    # 注意: rebuild_entrance.py 中的坐标是硬编码的
    # 如果 z_north/z_south 需要调整，需要修改该文件或传参
    # 当前 v4 入口 Z 范围: 门厅 Z[85,89], 小庭 Z[78,82], 影壁 Z=78
    # 原 rebuild_entrance: z_south=90, z_north=77 — 基本兼容

    build_entrance_complex(b)

    print(f"  Step 6 完成 ({b.cmd_count - cmd_start} commands)")


# ═══════════════════════════════════════════
# Step 7: 验证
# ═══════════════════════════════════════════

def step7_verify(b):
    """运行碰撞验证 + 建筑采样验证"""
    print("=" * 60)
    print("=== Step 7: 验证 ===")
    print("=" * 60)

    # 7a. 离线碰撞检测（不需要 RCON）
    collision_count, report = verify_collisions()
    print(report)

    # 7b. 在线建筑验证（需要 RCON）
    if b is not None:
        import config_v4
        sys.modules['config_v3'] = config_v4

        if 'verifier' in sys.modules:
            del sys.modules['verifier']
        from verifier import verify_all_buildings

        print("\n=== 在线建筑方块验证 ===")
        result = verify_all_buildings(b, cfg.ALL_BUILDINGS)
        return collision_count == 0 and result["summary"]["failed"] == 0

    return collision_count == 0


# ═══════════════════════════════════════════
# 主入口
# ═══════════════════════════════════════════

def full_rebuild():
    """完整重建流程"""
    start_time = time.time()

    # 先运行离线碰撞检测
    collision_count, report = verify_collisions()
    print(report)
    if collision_count > 0:
        print("\n!!! 碰撞检测未通过，中止重建 !!!")
        return False

    print("\n碰撞检测通过，开始重建...\n")

    with MinecraftBuilder() as b:
        step1_clear_world(b)
        step2_phase1_water(b)
        step3_phase2_corridors(b)
        step4_phase3_buildings(b)
        step5_phase4_details(b)
        step6_rebuild_entrance(b)

        print(f"\n建造完成! 共 {b.cmd_count} 条命令")
        print(f"耗时: {time.time() - start_time:.1f} 秒")

        # 最终验证
        step7_verify(b)

        # 传送玩家到入口
        print("\n传送玩家到入口...")
        b.tp_player("@a", 58, -58, 90)

    return True


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "full"

    if mode == "verify":
        # 仅验证碰撞（离线）
        collision_count, report = verify_collisions()
        print(report)
        sys.exit(0 if collision_count == 0 else 1)

    elif mode == "clear":
        # 仅清空世界
        with MinecraftBuilder() as b:
            step1_clear_world(b)

    elif mode == "full":
        # 完整重建
        success = full_rebuild()
        sys.exit(0 if success else 1)

    else:
        print("用法: python rebuild_v4.py [full|verify|clear]")
        print("  full   — 完整重建 (默认)")
        print("  verify — 仅验证碰撞 (不需要 RCON)")
        print("  clear  — 仅清空世界")
        sys.exit(1)
