"""建筑技能库 — Voyager-style Skill Library for Minecraft 建筑

存储、检索、复用中式园林建筑模式。
每个技能是一个可独立执行的建筑函数（代码字符串），带描述和标签。

用法:
    from skill_library import SkillLibrary
    lib = SkillLibrary()
    results = lib.search("屋顶 亭子")
    code = lib.get_code("roof_hip_pointed")
"""

import json
import os

SKILLS_DIR = "/Users/lambertlin/minecraft-server/scripts/skills_db"


class SkillLibrary:
    """建筑技能库 -- 存储、检索、复用建筑模式"""

    def __init__(self):
        self.skills = {}  # name -> {code, description, tags, usage_count}
        os.makedirs(SKILLS_DIR, exist_ok=True)
        self._load_all()

    def add_skill(self, name: str, code: str, description: str, tags: list[str]):
        """存储一个新技能"""
        self.skills[name] = {
            "code": code,
            "description": description,
            "tags": tags,
            "usage_count": 0,
        }
        self._save(name)

    def search(self, query: str, top_k: int = 5) -> list[dict]:
        """搜索最相关的技能（简单关键词匹配，后续可升级为向量检索）"""
        results = []
        query_words = set(query.lower().split())
        for name, skill in self.skills.items():
            # 计算匹配分数: 名称、描述、标签全部参与
            text = f"{name} {skill['description']} {' '.join(skill['tags'])}".lower()
            score = sum(1 for w in query_words if w in text)
            if score > 0:
                results.append({"name": name, "score": score, **skill})
        results.sort(key=lambda x: (-x["score"], -x["usage_count"]))
        return results[:top_k]

    def get_code(self, name: str) -> str | None:
        """获取技能代码，同时递增使用计数"""
        if name in self.skills:
            self.skills[name]["usage_count"] += 1
            self._save(name)
            return self.skills[name]["code"]
        return None

    def list_skills(self) -> list[str]:
        """列出所有技能名称"""
        return sorted(self.skills.keys())

    def remove_skill(self, name: str) -> bool:
        """删除一个技能"""
        if name in self.skills:
            del self.skills[name]
            path = os.path.join(SKILLS_DIR, f"{name}.json")
            if os.path.exists(path):
                os.remove(path)
            return True
        return False

    def _save(self, name: str):
        path = os.path.join(SKILLS_DIR, f"{name}.json")
        with open(path, "w") as f:
            json.dump(self.skills[name], f, indent=2, ensure_ascii=False)

    def _load_all(self):
        if not os.path.exists(SKILLS_DIR):
            return
        for fname in os.listdir(SKILLS_DIR):
            if fname.endswith(".json"):
                with open(os.path.join(SKILLS_DIR, fname)) as f:
                    self.skills[fname[:-5]] = json.load(f)
