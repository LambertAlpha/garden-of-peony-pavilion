# 建筑原语技能库

## L1: 原子操作（已实现 in builder.py）

| 原语 | 函数 | 用途 |
|------|------|------|
| fill | `b.fill(x1,y1,z1, x2,y2,z2, block, mode)` | 批量填充，自动分片≤32768 |
| setblock | `b.setblock(x,y,z, block)` | 单方块放置 |
| replace | `b.replace(x1,y1,z1, x2,y2,z2, new, old)` | 替换指定方块 |
| clone | `b.clone(sx1,sy1,sz1, sx2,sy2,sz2, dx,dy,dz)` | 克隆区域 |
| clear | `b.clear(x1,y1,z1, x2,y2,z2)` | fill air 撤销 |
| line | `b.line(x1,y1,z1, x2,y2,z2, block)` | 3D Bresenham 画线 |
| circle_xz | `b.circle_xz(cx,y,cz, r, block)` | 水平圆 |
| circle_yz | `b.circle_yz(x,cy,cz, r, block)` | 垂直圆（月洞门） |

## L2: 几何原语（待封装）

```python
def build_wall(b, x1,z1, x2,z2, base_y, height, wall_block, base_block, cap_block):
    """沿两点建直墙，含墙基+墙身+压瓦"""

def build_floor(b, x1,z1, x2,z2, y, block1, block2=None, pattern="checkerboard"):
    """铺地面，支持棋盘格/条纹/纯色"""

def build_stairs(b, x1,z1, x2,z2, y_start, y_end, block, axis):
    """自动计算台阶数量和facing方向"""

def build_arch(b, cx, cy, cz, radius, block, plane="yz"):
    """拱门/月洞门，在指定平面画半圆并清空内部"""
```

## L3: 建筑语义（待封装）

```python
def build_roof_hip_pointed(b, cx,cz, base_y, base_size, layers, stair_block, slab_block):
    """攒尖顶：逐层缩小的楼梯金字塔 + 宝顶"""

def build_roof_hip(b, x1,z1, x2,z2, base_y, stair_block, slab_block):
    """歇山顶：四面坡+山花"""

def build_roof_gable(b, x1,z1, x2,z2, base_y, ridge_axis, stair_block, slab_block):
    """悬山顶：两面坡+脊线"""

def build_flying_eaves(b, cx,cz, roof_y, base_size, eave_block):
    """飞檐翘角：四角倒置楼梯"""

def build_platform(b, cx,cz, size_x,size_z, base_y, height, block, step_block):
    """须弥座台基：含散水带+台阶"""
```

## 中式建筑材质速查

| 部位 | 方块ID | PALETTE key |
|------|--------|------------|
| 红漆柱 | stripped_crimson_stem | "pillar" |
| 深色梁 | dark_oak_planks | "beam" |
| 灰瓦屋顶 | stone_brick_stairs | "roof" |
| 白粉墙 | white_concrete | "wall" |
| 石砖台基 | stone_bricks | "base" |
| 磨制安山岩柱础 | polished_andesite | "base_col" |
| 铁栏杆漏窗 | iron_bars | "window" |
| 绯红木栏杆 | crimson_fence | "rail" |
| 灯笼 | lantern | "lantern" |
| 避雷针宝顶 | lightning_rod | "lightning_rod" |
