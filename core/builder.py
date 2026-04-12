"""Minecraft 园林建造核心库 — RCON 封装 + 几何工具"""

import time
import math
from mcrcon import MCRcon

RCON_HOST = "localhost"
RCON_PASS = "garden2026"
RCON_PORT = 25575
CMD_DELAY = 0.03  # 30ms between commands
FILL_LIMIT = 32768  # /fill 单次最大方块数


class MinecraftBuilder:
    def __init__(self, host=RCON_HOST, password=RCON_PASS, port=RCON_PORT):
        self.host = host
        self.password = password
        self.port = port
        self.mcr = None
        self.cmd_count = 0
        self.bounding_boxes = []  # 记录每个模块的边界，用于撤销

    def __enter__(self):
        self.mcr = MCRcon(self.host, self.password, self.port)
        self.mcr.connect()
        return self

    def __exit__(self, *args):
        if self.mcr:
            self.mcr.disconnect()

    # ── 基础命令 ──

    def cmd(self, command: str) -> str:
        """发送单条命令，带延迟和计数"""
        resp = self.mcr.command(command)
        self.cmd_count += 1
        if self.cmd_count % 200 == 0:
            print(f"  [{self.cmd_count} commands sent]")
        time.sleep(CMD_DELAY)
        return resp

    def setblock(self, x: int, y: int, z: int, block: str) -> str:
        return self.cmd(f"setblock {x} {y} {z} {block}")

    # ── Fill（自动分片）──

    def fill(self, x1: int, y1: int, z1: int,
             x2: int, y2: int, z2: int,
             block: str, mode: str = "") -> list[str]:
        """安全 fill，超过 FILL_LIMIT 自动分片"""
        dx = abs(x2 - x1) + 1
        dy = abs(y2 - y1) + 1
        dz = abs(z2 - z1) + 1
        volume = dx * dy * dz

        if volume <= FILL_LIMIT:
            suffix = f" {mode}" if mode else ""
            return [self.cmd(f"fill {x1} {y1} {z1} {x2} {y2} {z2} {block}{suffix}")]

        # 沿最长轴分片
        results = []
        if dx >= dy and dx >= dz:
            mid = (x1 + x2) // 2
            results += self.fill(x1, y1, z1, mid, y2, z2, block, mode)
            results += self.fill(mid + 1, y1, z1, x2, y2, z2, block, mode)
        elif dy >= dz:
            mid = (y1 + y2) // 2
            results += self.fill(x1, y1, z1, x2, mid, z2, block, mode)
            results += self.fill(x1, mid + 1, z1, x2, y2, z2, block, mode)
        else:
            mid = (z1 + z2) // 2
            results += self.fill(x1, y1, z1, x2, y2, mid, block, mode)
            results += self.fill(x1, y1, mid + 1, x2, y2, z2, block, mode)
        return results

    def replace(self, x1: int, y1: int, z1: int,
                x2: int, y2: int, z2: int,
                new_block: str, old_block: str) -> list[str]:
        """替换指定区域内的特定方块"""
        return self.fill(x1, y1, z1, x2, y2, z2, new_block, f"replace {old_block}")

    # ── Clone ──

    def clone(self, sx1, sy1, sz1, sx2, sy2, sz2, dx, dy, dz, mode="masked"):
        """克隆区域，默认 masked 模式（只复制非空气）"""
        return self.cmd(f"clone {sx1} {sy1} {sz1} {sx2} {sy2} {sz2} {dx} {dy} {dz} {mode}")

    # ── 清除/撤销 ──

    def clear(self, x1: int, y1: int, z1: int, x2: int, y2: int, z2: int):
        """用空气填充 — 撤销"""
        return self.fill(x1, y1, z1, x2, y2, z2, "minecraft:air")

    def register_bbox(self, name: str, x1, y1, z1, x2, y2, z2):
        """注册模块边界框"""
        self.bounding_boxes.append({
            "name": name, "x1": x1, "y1": y1, "z1": z1,
            "x2": x2, "y2": y2, "z2": z2
        })

    def undo(self, name: str):
        """撤销指定模块"""
        for bb in self.bounding_boxes:
            if bb["name"] == name:
                print(f"Undoing {name}...")
                self.clear(bb["x1"], bb["y1"], bb["z1"],
                           bb["x2"], bb["y2"], bb["z2"])
                return
        print(f"Module '{name}' not found")

    # ── 几何工具 ──

    def line(self, x1: int, y1: int, z1: int,
             x2: int, y2: int, z2: int, block: str):
        """3D Bresenham 画线"""
        points = bresenham_3d(x1, y1, z1, x2, y2, z2)
        for x, y, z in points:
            self.setblock(x, y, z, block)

    def circle_xz(self, cx: int, y: int, cz: int,
                   radius: int, block: str):
        """在 XZ 平面画圆（水平圆，如柱子排列）"""
        for x, z in circle_points(cx, cz, radius):
            self.setblock(x, y, z, block)

    def circle_xy(self, cx: int, cy: int, z: int,
                   radius: int, block: str):
        """在 XY 平面画圆（垂直圆，如月洞门，朝南北）"""
        for x, y in circle_points(cx, cy, radius):
            self.setblock(x, y, z, block)

    def circle_yz(self, x: int, cy: int, cz: int,
                   radius: int, block: str):
        """在 YZ 平面画圆（垂直圆，如月洞门，朝东西）"""
        for y, z in circle_points(cy, cz, radius):
            self.setblock(x, y, z, block)

    def filled_circle_xz(self, cx: int, y: int, cz: int,
                          radius: int, block: str):
        """在 XZ 平面画填充圆"""
        for x, z in filled_circle_points(cx, cz, radius):
            self.setblock(x, y, z, block)

    def tp_player(self, player: str, x: int, y: int, z: int):
        """传送玩家到指定位置"""
        return self.cmd(f"tp {player} {x} {y} {z}")


# ── 独立几何函数 ──

def bresenham_3d(x1, y1, z1, x2, y2, z2):
    """3D Bresenham 直线算法"""
    points = []
    dx, dy, dz = abs(x2 - x1), abs(y2 - y1), abs(z2 - z1)
    sx = 1 if x2 > x1 else -1
    sy = 1 if y2 > y1 else -1
    sz = 1 if z2 > z1 else -1

    if dx >= dy and dx >= dz:
        ey, ez = 2 * dy - dx, 2 * dz - dx
        x = x1
        for _ in range(dx + 1):
            points.append((x, y1, z1))
            if ey > 0:
                y1 += sy
                ey -= 2 * dx
            if ez > 0:
                z1 += sz
                ez -= 2 * dx
            ey += 2 * dy
            ez += 2 * dz
            x += sx
    elif dy >= dz:
        ex, ez = 2 * dx - dy, 2 * dz - dy
        y = y1
        for _ in range(dy + 1):
            points.append((x1, y, z1))
            if ex > 0:
                x1 += sx
                ex -= 2 * dy
            if ez > 0:
                z1 += sz
                ez -= 2 * dy
            ex += 2 * dx
            ez += 2 * dz
            y += sy
    else:
        ex, ey = 2 * dx - dz, 2 * dy - dz
        z = z1
        for _ in range(dz + 1):
            points.append((x1, y1, z))
            if ex > 0:
                x1 += sx
                ex -= 2 * dz
            if ey > 0:
                y1 += sy
                ey -= 2 * dz
            ex += 2 * dx
            ey += 2 * dy
            z += sz
    return points


def circle_points(ca, cb, radius):
    """中点圆算法 — 返回圆上的整数坐标对"""
    points = set()
    a, b = radius, 0
    d = 1 - radius
    while a >= b:
        for da, db in [(a, b), (b, a), (-a, b), (-b, a),
                       (a, -b), (b, -a), (-a, -b), (-b, -a)]:
            points.add((ca + da, cb + db))
        b += 1
        if d < 0:
            d += 2 * b + 1
        else:
            a -= 1
            d += 2 * (b - a) + 1
    return points


def filled_circle_points(ca, cb, radius):
    """填充圆 — 返回圆内所有整数坐标"""
    points = set()
    for a in range(-radius, radius + 1):
        for b in range(-radius, radius + 1):
            if a * a + b * b <= radius * radius:
                points.add((ca + a, cb + b))
    return points


def rectangle_outline(x1, z1, x2, z2):
    """矩形边框坐标（XZ 平面）"""
    points = set()
    for x in range(x1, x2 + 1):
        points.add((x, z1))
        points.add((x, z2))
    for z in range(z1, z2 + 1):
        points.add((x1, z))
        points.add((x2, z))
    return points
