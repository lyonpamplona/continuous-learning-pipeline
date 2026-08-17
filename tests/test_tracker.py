"""Testes unitarios para modulo Tracker."""

import json
import os
import tempfile
from unittest.mock import Mock, patch
from clp.tracker import Tracker


class TestTracker:
    """Testes para a classe Tracker."""

    def setup_method(self):
        """Setup antes de cada teste."""
        self.temp_dir = tempfile.mkdtemp()
        self.config = {
            "github_token": "test_token",
            "data_dir": self.temp_dir,
        }
        self.tracker = Tracker(self.config)

    def test_init(self):
        """Testar inicializacao do Tracker."""
        assert self.tracker.github_token == "test_token"

    def test_register_skill(self):
        """Testar registro de skill para tracking."""
        self.tracker.register_skill("test-skill", "test/repo")
        # O tracker salva em data_dir/skill-updates.json
        tracker_file = os.path.join(self.temp_dir, "skill-updates.json")
        assert os.path.exists(tracker_file)

        with open(tracker_file) as f:
            data = json.load(f)
        assert "test-skill" in data["skills"]
        assert data["skills"]["test-skill"]["repo"] == "test/repo"

    @patch("clp.tracker.requests.get")
    def test_check_updates(self, mock_get):
        """Testar verificacao de atualizacoes."""
        # Registrar skill primeiro
        self.tracker.register_skill("test-skill", "test/repo")

        # Mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {"sha": "abc123", "commit": {"committer": {"date": "2026-08-16"}}}
        ]
        mock_get.return_value = mock_response

        result = self.tracker.check_updates("test-skill")
        assert result is not None
        assert result["commits_since_check"] == 1

    @patch("clp.tracker.requests.get")
    def test_check_all(self, mock_get):
        """Testar verificacao de todas skills."""
        # Registrar skill
        self.tracker.register_skill("test-skill", "test/repo")

        # Mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "commits": [{"sha": "abc123"}],
            "total_count": 1,
        }
        mock_get.return_value = mock_response

        results = self.tracker.check_all()
        assert len(results) > 0

    def test_get_pending(self):
        """Testar obtencao de skills pendentes."""
        # Registrar skill
        self.tracker.register_skill("test-skill", "test/repo")

        # Simular commits pendentes diretamente no tracker_data
        self.tracker.tracker_data["skills"]["test-skill"]["commits_since_check"] = 5

        pending = self.tracker.get_pending()
        assert len(pending) == 1
        assert pending[0]["name"] == "test-skill"
        assert pending[0]["commits"] == 5
