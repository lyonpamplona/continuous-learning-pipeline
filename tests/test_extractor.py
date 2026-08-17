"""Testes unitarios para modulo Extractor."""

from unittest.mock import Mock, patch
from clp.extractor import Extractor


class TestExtractor:
    """Testes para a classe Extractor."""

    def setup_method(self):
        """Setup antes de cada teste."""
        self.config = {"github_token": "test_token"}
        self.extractor = Extractor(self.config)

    def test_init(self):
        """Testar inicializacao do Extractor."""
        assert self.extractor.github_token == "test_token"

    @patch("clp.extractor.requests.get")
    def test_fetch_readme_success(self, mock_get):
        """Testar busca de README com sucesso."""
        import base64
        readme_content = "# Test Repo\n\nThis is a test repository."
        encoded = base64.b64encode(readme_content.encode()).decode()

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"content": encoded}
        mock_get.return_value = mock_response

        result = self.extractor.fetch_readme("test/repo")
        assert result == readme_content

    @patch("clp.extractor.requests.get")
    def test_fetch_readme_error(self, mock_get):
        """Testar busca de README com erro."""
        mock_get.side_effect = Exception("API Error")
        result = self.extractor.fetch_readme("test/repo")
        assert result == ""

    def test_analyze_readme(self):
        """Testar analise de README."""
        readme = """# Test Repo

This is a test repository for testing purposes.

## Installation

Install with pip:

```bash
pip install test-repo
```

## Features

- Feature one
- Feature two
- Feature three

## Usage

Use the repo like this.
"""
        info = self.extractor.analyze_readme(readme)
        assert "purpose" in info
        assert len(info["sections"]) > 0
        assert len(info["commands"]) > 0
        assert len(info["features"]) > 0

    def test_identify_workflows(self):
        """Testar identificacao de workflows."""
        readme_info = {
            "purpose": "Test purpose",
            "commands": ["cmd1", "cmd2"],
            "sections": [
                {"title": "Installation", "content": "Install steps"},
                {"title": "Usage", "content": "Usage steps"},
            ],
        }
        metadata = {"name": "test"}
        workflows = self.extractor.identify_workflows(readme_info, metadata)
        assert len(workflows) > 0

    def test_generate_skill_md(self):
        """Testar geracao de SKILL.md."""
        repo_name = "test/repo"
        metadata = {"name": "repo", "stars": 100, "language": "Python"}
        readme_info = {"purpose": "Test purpose", "usage": "Use it"}
        workflows = [{"name": "test", "description": "Test workflow", "commands": ["cmd1"]}]

        skill = self.extractor.generate_skill_md(repo_name, metadata, readme_info, workflows)
        assert "---" in skill
        assert "name:" in skill
        assert "trigger:" in skill
        assert "description:" in skill

    @patch("clp.extractor.requests.get")
    def test_extract_full(self, mock_get):
        """Testar pipeline completo de extracao."""
        import base64
        readme = "# Test\n\nTest content."
        encoded = base64.b64encode(readme.encode()).decode()

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "name": "test",
            "full_name": "test/repo",
            "stargazers_count": 100,
            "language": "Python",
            "content": encoded,
        }
        mock_get.return_value = mock_response

        result = self.extractor.extract("test/repo")
        assert result is not None
        assert "---" in result
