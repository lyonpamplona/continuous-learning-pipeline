"""Modulo Tracker — monitora atualizacoes de repositórios fonte."""

import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

import requests

logger = logging.getLogger(__name__)


class Tracker:
    """Monitora atualizacoes de repositórios fonte."""

    def __init__(self, config=None):
        self.config = config or {}
        self.github_token = self.config.get("github_token", "")
        self.headers = {}
        if self.github_token:
            self.headers["Authorization"] = f"token {self.github_token}"
        self.timeout = self.config.get("extract_timeout", 15)
        self.rate_limit_delay = self.config.get("rate_limit_delay", 1)
        self.tracker_file = Path(self.config.get("data_dir", "~/.clp/data")).expanduser() / "skill-updates.json"
        self.tracker_file.parent.mkdir(parents=True, exist_ok=True)
        self._load_tracker()

    def _load_tracker(self):
        if self.tracker_file.exists():
            self.tracker_data = json.loads(self.tracker_file.read_text())
        else:
            self.tracker_data = {"skills": {}, "last_check": None}

    def _save_tracker(self):
        self.tracker_data["last_check"] = datetime.now().isoformat()
        self.tracker_file.write_text(json.dumps(self.tracker_data, indent=2))

    def register_skill(self, name: str, repo: str):
        """Register a skill for tracking."""
        self.tracker_data["skills"][name] = {
            "repo": repo,
            "last_checked": None,
            "last_updated": None,
            "commits_since_check": 0,
        }
        self._save_tracker()

    def check_updates(self, name: str) -> Optional[dict]:
        """Verifica se o repositório fonte de uma skill tem atualizacoes."""
        skill = self.tracker_data["skills"].get(name)
        if not skill:
            return None

        repo = skill["repo"]
        try:
            url = f"https://api.github.com/repos/{repo}/commits"
            params = {"per_page": 1}
            if skill.get("last_checked"):
                params["since"] = skill["last_checked"]

            resp = requests.get(url, headers=self.headers, params=params, timeout=self.timeout)
            if resp.status_code == 200:
                commits = resp.json()
                if commits:
                    skill["commits_since_check"] = len(commits)
                    skill["last_updated"] = commits[0]["commit"]["committer"]["date"]
                    logger.info(f"{name}: {len(commits)} novo(s) commit(s)")
                else:
                    logger.info(f"{name}: sem novos commits")
            else:
                logger.warning(f"{name}: erro API {resp.status_code}")
        except Exception as e:
            logger.error(f"{name}: erro - {e}")

        skill["last_checked"] = datetime.now().isoformat()
        self._save_tracker()
        return skill

    def check_all(self) -> list:
        """Verifica todas as skills registradas por atualizacoes."""
        results = []
        for name in self.tracker_data["skills"]:
            result = self.check_updates(name)
            if result:
                results.append(result)
            time.sleep(self.rate_limit_delay)
        return results

    def get_pending(self) -> list:
        """Obtem skills com atualizacoes pendentes."""
        pending = []
        for name, skill in self.tracker_data["skills"].items():
            if skill.get("commits_since_check", 0) > 0:
                pending.append({
                    "name": name,
                    "repo": skill["repo"],
                    "commits": skill["commits_since_check"],
                    "last_updated": skill.get("last_updated"),
                })
        return pending
