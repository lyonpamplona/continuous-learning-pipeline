"""Testes unitarios para modulo Dashboard."""

import os
import tempfile
from pathlib import Path
from clp.dashboard import Dashboard


class TestDashboard:
    """Testes para a classe Dashboard."""

    def setup_method(self):
        """Setup antes de cada teste."""
        self.temp_dir = tempfile.mkdtemp()
        self.pending_dir = os.path.join(self.temp_dir, "pending")
        self.approved_dir = os.path.join(self.temp_dir, "approved")
        self.rejected_dir = os.path.join(self.temp_dir, "rejected")
        self.reports_dir = os.path.join(self.temp_dir, "reports")

        os.makedirs(self.pending_dir, exist_ok=True)
        os.makedirs(self.approved_dir, exist_ok=True)
        os.makedirs(self.rejected_dir, exist_ok=True)
        os.makedirs(self.reports_dir, exist_ok=True)

        self.config = {
            "workspace_dir": self.temp_dir,
            "reports_dir": self.reports_dir,
        }
        self.dashboard = Dashboard(self.config)

    def test_generate(self):
        """Testar geracao do dashboard."""
        result = self.dashboard.generate(generate_html=True)
        assert "pending" in result
        assert "approved" in result
        assert "rejected" in result
        assert "html_path" in result
        assert "md_path" in result

    def test_generate_with_skills(self):
        """Testar geracao com skills pendentes."""
        # Criar skill pendente
        skill_dir = os.path.join(self.pending_dir, "test-skill")
        os.makedirs(skill_dir, exist_ok=True)

        content = """---
name: test-skill
trigger: test
description: "Test skill."
version: 1.0.0
---

# Test Skill

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
        with open(os.path.join(skill_dir, "SKILL.md"), "w") as f:
            f.write(content)

        result = self.dashboard.generate(generate_html=True)
        assert result["pending"] == 1
        assert result["approved"] == 0
        assert result["rejected"] == 0

    def test_generate_html_exists(self):
        """Testar existencia do arquivo HTML."""
        result = self.dashboard.generate(generate_html=True)
        assert os.path.exists(result["html_path"])

    def test_generate_md_exists(self):
        """Testar existencia do arquivo Markdown."""
        result = self.dashboard.generate(generate_html=False)
        assert os.path.exists(result["md_path"])

    def test_generate_empty_dirs(self):
        """Testar geracao com diretorios vazios."""
        result = self.dashboard.generate(generate_html=True)
        assert result["pending"] == 0
        assert result["approved"] == 0
        assert result["rejected"] == 0
