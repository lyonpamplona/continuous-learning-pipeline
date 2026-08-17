"""Testes unitarios para modulo Config."""

import os
import tempfile
from clp.config import Config


class TestConfig:
    """Testes para a classe Config."""

    def test_init_defaults(self):
        """Testar inicializacao com padroes."""
        config = Config()
        assert config.get("github_token") == ""
        assert config.get("scout_keywords") == "agents,ai,automation,skills,workflows"
        assert config.get("score_min_pass") == 70

    def test_get_default(self):
        """Testar get com valor padrao."""
        config = Config()
        assert config.get("nonexistent", "default") == "default"

    def test_set_get(self):
        """Testar set e get."""
        config = Config()
        config.set("test_key", "test_value")
        assert config.get("test_key") == "test_value"

    def test_getitem_setitem(self):
        """Testar acesso via index."""
        config = Config()
        config["test_key"] = "test_value"
        assert config["test_key"] == "test_value"

    def test_load_env(self, monkeypatch):
        """Testar carregamento de variaveis de ambiente."""
        monkeypatch.setenv("GITHUB_TOKEN", "env_token")
        monkeypatch.setenv("CLP_SKILLS_DIR", "/custom/skills")
        config = Config()
        assert config.get("github_token") == "env_token"
        assert config.get("skills_dir") == "/custom/skills"

    def test_load_file(self):
        """Testar carregamento de arquivo YAML."""
        yaml_content = """
github_token: file_token
scout_keywords: custom,keywords
score_min_pass: 80
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            config = Config(temp_path)
            assert config.get("github_token") == "file_token"
            assert config.get("scout_keywords") == "custom,keywords"
            assert config.get("score_min_pass") == 80
        finally:
            os.unlink(temp_path)

    def test_file_overrides_env(self, monkeypatch):
        """Testar que arquivo sobrescreve variaveis de ambiente."""
        monkeypatch.setenv("GITHUB_TOKEN", "env_token")
        yaml_content = "github_token: file_token\n"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            config = Config(temp_path)
            assert config.get("github_token") == "file_token"
        finally:
            os.unlink(temp_path)
