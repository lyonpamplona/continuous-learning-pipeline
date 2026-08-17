"""Plugin system for agent framework integration."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional


class AgentPlugin(ABC):
    """Base plugin interface for agent framework integration."""

    @abstractmethod
    def create_skill(self, name: str, content: str, category: str = "general") -> bool:
        """Create a skill in the agent framework."""
        pass

    @abstractmethod
    def update_skill(self, name: str, content: str) -> bool:
        """Update an existing skill."""
        pass

    @abstractmethod
    def delete_skill(self, name: str) -> bool:
        """Delete a skill."""
        pass

    @abstractmethod
    def list_skills(self) -> list:
        """List all skills."""
        pass

    @abstractmethod
    def notify(self, message: str, level: str = "info") -> bool:
        """Send notification to the user."""
        pass

    @abstractmethod
    def schedule_job(self, name: str, schedule: str, callback: str) -> bool:
        """Schedule a periodic job."""
        pass


class FilePlugin(AgentPlugin):
    """Standalone plugin that saves skills to disk."""

    def __init__(self, skills_dir: str = "~/.clp/skills"):
        self.skills_dir = Path(skills_dir).expanduser()
        self.skills_dir.mkdir(parents=True, exist_ok=True)

    def create_skill(self, name: str, content: str, category: str = "general") -> bool:
        skill_dir = self.skills_dir / category / name
        skill_dir.mkdir(parents=True, exist_ok=True)
        (skill_dir / "SKILL.md").write_text(content)
        return True

    def update_skill(self, name: str, content: str) -> bool:
        for skill_file in self.skills_dir.rglob("SKILL.md"):
            if skill_file.parent.name == name:
                skill_file.write_text(content)
                return True
        return False

    def delete_skill(self, name: str) -> bool:
        import shutil
        for skill_dir in self.skills_dir.rglob(name):
            if skill_dir.is_dir():
                shutil.rmtree(skill_dir)
                return True
        return False

    def list_skills(self) -> list:
        skills = []
        for skill_file in self.skills_dir.rglob("SKILL.md"):
            skills.append({
                "name": skill_file.parent.name,
                "category": skill_file.parent.parent.name,
                "path": str(skill_file),
            })
        return skills

    def notify(self, message: str, level: str = "info") -> bool:
        print(f"[{level.upper()}] {message}")
        return True

    def schedule_job(self, name: str, schedule: str, callback: str) -> bool:
        print(f"[SCHEDULE] {name}: {schedule} -> {callback}")
        return True


def get_plugin(plugin_type: str = "file", **kwargs) -> AgentPlugin:
    """Factory function para obter o plugin apropriado."""
    if plugin_type == "file":
        return FilePlugin(**kwargs)
    elif plugin_type == "hermes":
        from clp.plugins.hermes import HermesPlugin
        return HermesPlugin(**kwargs)
    elif plugin_type == "custom":
        from clp.plugins.custom import CustomPlugin
        return CustomPlugin(**kwargs)
    else:
        raise ValueError(f"Tipo de plugin desconhecido: {plugin_type}")
