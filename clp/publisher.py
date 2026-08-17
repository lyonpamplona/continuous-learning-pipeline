"""Modulo Publisher — publica skills aprovadas no framework de agente."""

import logging
import re
import shutil
from pathlib import Path
from typing import Optional

import yaml

from clp.plugins import AgentPlugin, get_plugin

logger = logging.getLogger(__name__)


class Publisher:
    """Publishes approved skills to the agent framework."""

    def __init__(self, plugin: Optional[AgentPlugin] = None, config=None):
        self.plugin = plugin or get_plugin("file")
        self.config = config or {}

    def publish(self, skill_path: str, name: str = None, category: str = "geral") -> bool:
        """Publicar uma skill a partir de um caminho de arquivo."""
        skill_file = Path(skill_path)
        if not skill_file.exists():
            print(f"[PUBLISH] Arquivo nao encontrado: {skill_path}")
            return False

        content = skill_file.read_text()
        if not name:
            # Extrair nome do frontmatter
            match = re.search(r"^---\n(.*?)\n---", content, re.DOTALL)
            if match:
                fm = yaml.safe_load(match.group(1))
                name = fm.get("name", skill_file.stem)

        success = self.plugin.create_skill(name, content, category)
        if success:
            print(f"[PUBLISH] Skill '{name}' published successfully.")
        else:
            print(f"[PUBLISH] Failed to publish '{name}'.")
        return success

    def publish_from_workspace(self, workspace_dir: str = None) -> list:
        """Publish all approved skills from workspace."""
        if workspace_dir is None:
            workspace_dir = self.config.get("workspace_dir", "~/.clp/workspace")

        approved_dir = Path(workspace_dir).expanduser() / "approved"
        if not approved_dir.exists():
            print(f"[PUBLISH] No approved directory found: {approved_dir}")
            return []

        published = []
        for skill_dir in approved_dir.iterdir():
            if skill_dir.is_dir():
                skill_file = skill_dir / "SKILL.md"
                if skill_file.exists():
                    name = skill_dir.name
                    success = self.publish(str(skill_file), name=name)
                    if success:
                        published.append(name)
                        # Move to published archive
                        published_dir = Path(workspace_dir).expanduser() / "published" / name
                        published_dir.mkdir(parents=True, exist_ok=True)
                        shutil.move(str(skill_file), str(published_dir / "SKILL.md"))

        return published

    def list_published(self) -> list:
        """List all published skills."""
        return self.plugin.list_skills()
