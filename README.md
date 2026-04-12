# Garden of Peony Pavilion | 游园惊梦

> "原来姹紫嫣红开遍，似这般都付与断井颓垣。"
> -- 汤显祖《牡丹亭》(1598)

在 Minecraft 中重建《牡丹亭·游园惊梦》的梦中花园。所有建筑通过 Python RCON 自动化生成，每一处结构均有原著文本依据，遵循明代私家园林设计原则。

## Screenshots

<p align="center">
  <em>截图待补充 -- 请将游戏内截图放入 screenshots/ 目录</em>
</p>

## What's Built

一座完整的明代私家园林 (~120x90 blocks)，包含 5 个建筑群组、19 栋建筑：

| 群组 | 建筑 | 出处 |
|------|------|------|
| A群-北岸梦境 | 牡丹亭(攒尖顶)、太湖石组、秋千、芍药阑、濯缨水阁 | "牡丹亭畔，芍药阑边" |
| B群-西园梅林 | 大梅树、梅花庵观、翠轩(悬山顶)、池馆、画船 | "大梅树一株"、"云霞翠轩" |
| C群-花听长廊 | 听雨轩、荼蘼花架 | "荼蘼外烟丝醉软" |
| D群-南部中轴 | 入口门厅、小庭深院、远香堂(歇山顶)、闺塾 | "园门洞开" |
| E群-东岸舫舟 | 石舫、曲廊亭、半亭 | "烟波画船" |

加上：主环廊(曲廊)、围墙月洞门、桥梁、垂杨、断井、散花 91 朵、全园做旧。

## Project Structure

```
garden-of-peony-pavilion/
├── README.md
├── rebuild.py                   # 一键重建入口
├── config/
│   └── config_v4.py             # v4 总平面图配置 (碰撞修正版)
├── core/
│   ├── builder.py               # RCON 封装 + 几何工具 (fill/line/circle)
│   ├── blocks.py                # 材质映射表 (PALETTE)
│   ├── verifier.py              # 建造后自动验证系统
│   ├── blueprint.py             # 声明式建筑蓝图系统
│   └── skill_library.py         # Voyager-style 建筑技能库
├── clusters/                    # 5 个建筑群组
│   ├── cluster_a.py             # A群: 北岸梦境 (牡丹亭/太湖石/秋千)
│   ├── cluster_b.py             # B群: 西园梅林 (大梅树/翠轩/画船)
│   ├── cluster_c.py             # C群: 花听长廊 (听雨轩/荼蘼花架)
│   ├── cluster_d.py             # D群: 南部中轴 (入口/远香堂/闺塾)
│   ├── cluster_e.py             # E群: 东岸舫舟 (石舫/曲廊亭/半亭)
│   └── corridors.py             # 主环廊 + 群组间连接路径
├── phases/                      # 分阶段建造脚本 (v3 遗留，仍可独立运行)
│   ├── phase1_water.py          # 水面系统
│   ├── phase2_corridors.py      # 廊道骨架 + 围墙
│   ├── phase3_buildings.py      # 19 栋建筑
│   ├── phase4_details.py        # 植被/灯笼/做旧
│   └── phase5_landscape.py      # 景观填充
├── register_skills.py           # 预置技能注册
├── skills/                      # 建筑技能文档
├── docs/                        # 设计文档 (原文考证/平面图/建造日志)
└── screenshots/                 # 游戏内截图
```

## Quick Start

### Prerequisites
- Minecraft Java Edition 1.21.4
- Python 3.10+
- `mcrcon` (`pip install mcrcon` or `uv pip install mcrcon`)

### Setup

```bash
# 1. 启动 Minecraft 服务器 (创造模式, 超平坦, 启用 RCON)
cd ~/minecraft-server && java -Xmx2G -jar server.jar nogui

# server.properties 中设置:
#   enable-rcon=true
#   rcon.password=garden2026
#   rcon.port=25575

# 2. 客户端连接 localhost

# 3. 一键重建整个园林
python rebuild.py

# 或分步执行
python rebuild.py verify       # 仅碰撞检测
python rebuild.py clear        # 仅清空世界
python rebuild.py phase 1      # 执行单个 phase (0~5)
```

## How It Works

```
Python scripts  -->  RCON commands  -->  Minecraft Server  -->  Blocks placed
```

- **rebuild.py** 按顺序调度: 清空 -> 水面 -> 围墙 -> 5群组 -> 廊道 -> 景观
- **config_v4.py** 定义所有建筑坐标，内置碰撞检测确保 3 格外延无重叠
- **core/builder.py** 封装 RCON，提供 fill/line/circle/clone 等几何原语

### Build Stats
- **~6,100 RCON commands** total
- **14 AI agents** collaborated on design and code
- **4 research agents** for textual analysis, architectural review, and engineering audit

## Design Philosophy

这不是任何真实园林的复刻，而是对汤显祖文本的空间诠释，遵循两个原则：

1. **文本忠实** -- 每一处结构都可追溯到原著具体唱词
2. **半颓之美** -- "姹紫嫣红开遍，似这般都付与断井颓垣"

园林按杜丽娘游园路线设计：

```
园门 -> 小庭 -> 影壁(遮视线) -> 转弯 ->
荼蘼花架 -> 曲径 -> 池面(豁然开朗!) ->
廊道 -> 翠轩(远眺画船) ->
太湖石(穿洞) -> 秋千 ->
芍药阑 -> 牡丹亭(梦中相遇) ->
幽僻角落 -> 大梅树(葬花之地)
```

## References

- 汤显祖《牡丹亭》1598 -- 第七、九、十、十二出
- 计成《园冶》1631
- 苏州古典园林 (拙政园、留园)

## License

MIT
