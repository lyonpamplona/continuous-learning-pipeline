"""Testes unitarios para modulo Scorer."""

import tempfile
import os
from clp.scorer import Scorer


class TestScorer:
    """Testes para a classe Scorer."""

    def setup_method(self):
        """Setup antes de cada teste."""
        self.scorer = Scorer(min_pass=70, max_size=100000)

    def test_init(self):
        """Testar inicializacao do Scorer."""
        assert self.scorer.min_pass == 70
        assert self.scorer.max_size == 100000

    def test_load_skill_valid(self):
        """Testar carregamento de skill valido."""
        content = """---
name: test-skill
trigger: test
description: "Test skill description."
version: 1.0.0
---

# Test Skill

This is a test skill.

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
            skill_data = self.scorer.load_skill(temp_path)
            assert skill_data is not None
            assert "frontmatter" in skill_data
            assert "body" in skill_data
            assert skill_data["frontmatter"]["name"] == "test-skill"
        finally:
            os.unlink(temp_path)

    def test_load_skill_invalid(self):
        """Testar carregamento de skill invalido."""
        content = "No frontmatter here"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(content)
            temp_path = f.name

        try:
            skill_data = self.scorer.load_skill(temp_path)
            assert skill_data is None
        finally:
            os.unlink(temp_path)

    def test_score_perfect(self):
        """Testar scoring com skill perfeita."""
        content = """---
name: perfect-skill
trigger: perfect
description: "Perfect skill description."
version: 1.0.0
author: Human Author
---

# Perfect Skill

This is a perfect skill.

## When to Use

- When you need perfection

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
            skill_data = self.scorer.load_skill(temp_path)
            result = self.scorer.score(skill_data)
            assert result["score"] >= 70
            assert result["decision"] == "PASS"
        finally:
            os.unlink(temp_path)

    def test_score_incomplete_frontmatter(self):
        """Testar scoring com frontmatter incompleto."""
        content = """---
name: incomplete
---

# Incomplete

No sections.
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(content)
            temp_path = f.name

        try:
            skill_data = self.scorer.load_skill(temp_path)
            result = self.scorer.score(skill_data)
            assert result["score"] < 70
            assert result["decision"] == "REJECT"
        finally:
            os.unlink(temp_path)

    def test_score_long_description(self):
        """Testar scoring com descricao longa."""
        content = """---
name: long-desc
trigger: test
description: "This is a very long description that exceeds the sixty character limit for descriptions."
version: 1.0.0
---

# Long Desc

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
            skill_data = self.scorer.load_skill(temp_path)
            result = self.scorer.score(skill_data)
            # Should fail description length check
            assert any("Description tem" in c and "FAIL" in c for c in result["checks"])
        finally:
            os.unlink(temp_path)

    def test_score_marketing_words(self):
        """Testar scoring com palavras de marketing."""
        content = """---
name: marketing
trigger: test
description: "Marketing skill."
version: 1.0.0
author: Human
---

# Marketing

This is revolutionary and game-changing.

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
            skill_data = self.scorer.load_skill(temp_path)
            result = self.scorer.score(skill_data)
            # Should fail marketing words check
            assert any("marketing" in c.lower() and "FAIL" in c for c in result["checks"])
        finally:
            os.unlink(temp_path)
