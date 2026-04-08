# Garden of Peony Pavilion | 游园惊梦

> "原来姹紫嫣红开遍，似这般都付与断井颓垣。"
> — Tang Xianzu, *The Peony Pavilion* (1598)

Recreating the dream garden from *The Peony Pavilion* (牡丹亭·游园惊梦) in Minecraft, using AI agents and Python RCON automation. Every structure is grounded in the original Ming Dynasty opera text and classical Chinese garden design principles.

## Screenshots

*(TODO: Add in-game screenshots)*

## What's Built

A complete Ming Dynasty private garden (~80×60 blocks) featuring:

| Structure | Chinese | Roof Style | Origin |
|-----------|---------|------------|--------|
| Peony Pavilion | 牡丹亭 | 攒尖顶 (pyramidal) | Act 10 *Startling Dream* |
| Peony Railing | 芍药阑 | — | "牡丹亭畔，芍药阑边" |
| Jade-Green Hall | 翠轩 | 悬山顶 (overhanging gable) | "云霞翠轩" |
| Garden Gate | 园门 | 硬山顶 (flush gable) | "园门洞开" |
| Screen Wall | 粉画垣 | — | "低就高来粉画垣" |
| Covered Bridge | 廊桥 | — | ref. Humble Administrator's Garden |
| Taihu Rocks | 太湖石 | — | "倚太湖石" |
| Painted Boat | 画船 | — | "烟波画船" |
| Plum Tree | 大梅树 | — | "大梅树一株，得葬于此" |

Plus: winding corridors (曲廊), swing (秋千), tea-rose bower (荼蘼花架), ruined wells (断井), weeping willows (垂杨), 91 scattered flowers, and full garden weathering.

## How It Works

All structures are built programmatically via **Minecraft RCON** — no manual block placement.

```
Python scripts  →  RCON commands  →  Minecraft Server  →  Blocks placed
```

### Tech Stack
- **Minecraft** 1.21.4 Java Edition (local server, creative mode, superflat)
- **Python** + `mcrcon` library for RCON communication
- **Claude Code** with Agent Teams for parallel script generation and review

### Build Stats
- **~6,100 RCON commands** total
- **14 AI agents** collaborated on design and code
- **4 research agents** for textual analysis, architectural review, and engineering audit

## Project Structure

```
garden-of-peony-pavilion/
├── builder.py              # Core build library (fill, line, circle, clone)
├── blocks.py               # Material palette mapping
├── landscape.py            # Final landscaping pass
├── structures/
│   ├── terrain.py          # Terrain shaping (north hills + pond)
│   ├── wall.py             # Perimeter walls + lattice windows + moon gate
│   ├── pavilion.py         # Peony Pavilion (pyramidal roof)
│   ├── peony_rail.py       # Peony railing enclosure
│   ├── hall.py             # Jade-Green Hall (waterside)
│   ├── gate.py             # Entrance area + screen wall + bower
│   ├── corridor.py         # Winding corridor system (6 segments)
│   ├── bridge_boat.py      # Covered bridge + painted boat
│   └── rocks_swing.py      # Taihu rocks + swing
├── docs/
│   ├── 总平面布局.md        # Master plan with coordinates
│   ├── 建筑模块清单.md      # Module specs with textual citations
│   ├── 材料方案.md          # Block palette
│   ├── 原文考证.md          # Primary source analysis
│   ├── 工程架构.md          # Technical architecture
│   └── 建造日志.md          # Build log
└── README.md
```

## Quick Start

### Prerequisites
- Minecraft Java Edition 1.21.4
- Python 3.10+
- `uv` package manager (or `pip install mcrcon`)

### Setup

```bash
# 1. Start a local Minecraft server (creative, superflat, offline mode)
cd ~/minecraft-server && java -Xmx2G -jar server.jar nogui

# 2. Enable RCON in server.properties:
#    enable-rcon=true
#    rcon.password=garden2026
#    rcon.port=25575

# 3. Join the server in Minecraft client (localhost)

# 4. Build everything:
cd garden-of-peony-pavilion

# Phase 1: Terrain + Walls
uvx --from mcrcon python3 structures/terrain.py
uvx --from mcrcon python3 structures/wall.py

# Phase 2: Core buildings
uvx --from mcrcon python3 structures/pavilion.py
uvx --from mcrcon python3 structures/peony_rail.py
uvx --from mcrcon python3 structures/hall.py

# Phase 3: Circulation
uvx --from mcrcon python3 structures/gate.py
uvx --from mcrcon python3 structures/corridor.py
uvx --from mcrcon python3 structures/bridge_boat.py

# Phase 4: Landscape
uvx --from mcrcon python3 structures/rocks_swing.py
uvx --from mcrcon python3 landscape.py
```

## Design Philosophy

This is **not** a replica of any real garden. It's a spatial interpretation of Tang Xianzu's text, following two principles:

1. **Textual fidelity** — Every structure traces back to specific lines in the opera
2. **Half-ruined beauty** — "姹紫嫣红开遍，似这般都付与断井颓垣" (Flowers bloom in riotous splendor, yet all given over to broken wells and crumbling walls)

The garden is designed to be walked through as Du Liniang's journey:

```
Gate → Courtyard → Screen wall (view blocked) → Turn →
Rose bower → Winding path → Pond (view opens!) →
Corridor → Hall (overlooking painted boat) →
Taihu rocks (cave passage) → Swing →
Peony railing → Peony Pavilion (dream encounter) →
Secluded corner → Lone plum tree (burial site)
```

## References

- Tang Xianzu, *The Peony Pavilion* (牡丹亭), 1598 — Acts 7, 9, 10, 12
- Ji Cheng, *The Craft of Gardens* (园冶), 1631
- Suzhou classical gardens (Humble Administrator's Garden, Lingering Garden)

## License

MIT
