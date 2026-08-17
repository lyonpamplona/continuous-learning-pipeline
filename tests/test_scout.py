"""Testes unitarios para modulo Scout."""

import json
from unittest.mock import Mock, patch
from clp.scout import Scout


class TestScout:
    """Testes para a classe Scout."""

    def setup_method(self):
        """Setup antes de cada teste."""
        self.config = {
            "github_token": "test_token",
            "scout_keywords": "agents,ai",
            "data_dir": "/tmp/clp-test/data",
        }
        self.scout = Scout(self.config)

    def test_init(self):
        """Testar inicializacao do Scout."""
        assert self.scout.github_token == "test_token"
        assert "Authorization" in self.scout.headers

    def test_init_without_token(self):
        """Testar inicializacao sem token."""
        scout = Scout({})
        assert scout.github_token == ""
        assert len(scout.headers) == 0

    @patch("clp.scout.requests.get")
    def test_search_trending_success(self, mock_get):
        """Testar busca de repositórios com sucesso."""
        # Mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "items": [
                {
                    "full_name": "test/repo1",
                    "name": "repo1",
                    "owner": {"login": "test"},
                    "description": "Test repo",
                    "stargazers_count": 100,
                    "forks_count": 10,
                    "language": "Python",
                    "updated_at": "2026-01-01T00:00:00Z",
                    "created_at": "2025-01-01T00:00:00Z",
                    "topics": ["test"],
                    "html_url": "https://github.com/test/repo1",
                    "url": "https://api.github.com/repos/test/repo1",
                }
            ]
        }
        mock_get.return_value = mock_response

        results = self.scout.search_trending(["test"], max_results=5)
        assert len(results) == 1
        assert results[0]["full_name"] == "test/repo1"
        assert results[0]["stars"] == 100

    @patch("clp.scout.requests.get")
    def test_search_trending_empty(self, mock_get):
        """Testar busca sem resultados."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"items": []}
        mock_get.return_value = mock_response

        results = self.scout.search_trending(["nonexistent"], max_results=5)
        assert len(results) == 0

    @patch("clp.scout.requests.get")
    def test_search_trending_error(self, mock_get):
        """Testar busca com erro de API."""
        mock_get.side_effect = Exception("API Error")
        results = self.scout.search_trending(["test"], max_results=5)
        assert len(results) == 0

    def test_save_results(self):
        """Testar salvamento de resultados."""
        results = [{"full_name": "test/repo", "stars": 100}]
        output_path = self.scout.save_results(results, "/tmp/clp-test/output.json")
        assert output_path == "/tmp/clp-test/output.json"

        with open(output_path) as f:
            saved = json.load(f)
        assert len(saved) == 1
        assert saved[0]["full_name"] == "test/repo"

    @patch("clp.scout.requests.get")
    def test_get_repo_details(self, mock_get):
        """Testar obtencao de detalhes do repositório."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"name": "test", "full_name": "test/repo"}
        mock_get.return_value = mock_response

        details = self.scout.get_repo_details("test/repo")
        assert details["name"] == "test"
        assert details["full_name"] == "test/repo"

    @patch("clp.scout.requests.get")
    def test_get_repo_details_error(self, mock_get):
        """Testar obtencao de detalhes com erro."""
        mock_get.side_effect = Exception("API Error")
        details = self.scout.get_repo_details("test/repo")
        assert details == {}
