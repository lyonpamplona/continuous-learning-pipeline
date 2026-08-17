"""Testes unitarios para modulo Publisher."""

import tempfile
import os
from pathlib import Path
from clp.publisher import Publisher
from clp.plugins import FilePlugin


class TestPublisher:
    """Testes para a classe Publisher."""

    def setup_method(self):
        """Setup antes de cada teste."""
        self.temp_dir = tempfile.mkdtemp()
        self.skills_dir = os.path.join(self.temp_dir, "skills")
        os.makedirs(self.skills_dir, exist_ok=True)
        self.plugin = FilePlugin(skills_dir=self.skills_dir)
        self.publisher = Publisher(self.plugin, {})

    def test_publish_valid(self):
        """Testar publicacao de skill valida."""
        content = """---
name: test-skill
trigger: test
description: "Test skill."
version: 1.0.0
---

# Test

## When to Use

- When testing

## Procedure

1. Step one
2. Step two
3. Step three

## Pitfalls

- Pitfall one
- Pitfall two
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(content)
            temp_path = f.name

        try:
            result = self.publisher.publish(temp_path, "test-skill", "test")
            assert result is True
            # FilePlugin salva em skills_dir/category/name/SKILL.md
            skill_path = os.path.join(self.skills_dir, "test", "test-skill", "SKILL.md")
            assert os.path.exists(skill_path)
        finally:
            os.unlink(temp_path)

    def test_publish_invalid_path(self):
        """Testar publicacao com caminho invalido."""
        result = self.publisher.publish("/nonexistent/path.md")
        assert result is False

    def test_publish_from_workspace(self):
        """Testar publicacao a partir do workspace."""
        workspace = os.path.join(self.temp_dir, "workspace")
        approved = os.path.join(workspace, "approved", "my-skill")
        os.makedirs(approved, exist_ok=True)

        content = """---
name: my-skill
trigger: test
description: "My skill."
version: 1.0.0
---

# My Skill

## When to Use

- When testing

## Procedure

1. Step one
2. Step two
3. Step three

## Pitfalls

- Pitfall one
- Pitfall two
"""
        with open(os.path.join(approved, "SKILL.md"), "w") as f:
            f.write(content)

        self.publisher.config = {"workspace_dir": workspace}
        published = self.publisher.publish_from_workspace()
        assert "my-skill" in published

    def test_list_published(self):
        """Testar listagem de skills publicadas."""
        # Criar uma skill publicada
        skill_path = os.path.join(self.skills_dir, "test", "existing", "SKILL.md")
        os.makedirs(os.path.dirname(skill_path), exist_ok=True)
        with open(skill_path, "w") as f:
            f.write("# Existing")

        skills = self.publisher.list_published()
        assert len(skills) > 0
        assert any("existing" in s.get("name", "").lower() for s in skills)
