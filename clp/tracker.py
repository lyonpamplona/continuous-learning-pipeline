"""Tracker module — monitors existing skills for updates."""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

import requests


class Tracker:
    """Monitors existing skills for repository updates."""

    def __init__(self, config=None):
        self.config = config or {}
        self.github_token = self.config.get("github_token", "")
        self.headers = {}
        if self.github_token:
            self.headers["Authorization"] = f"token {self.github_token}"
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
        """Check if a skill's source repository has updates."""
        skill = self.tracker_data["skills"].get(name)
        if not skill:
            return None

        repo = skill["repo"]
        try:
            url = f"https://api.github.com/repos/{repo}/commits"
            params = {"per_page": 1}
            if skill.get("last_checked"):
                params["since"] = skill["last_checked"]

            resp = requests.get(url, headers=self.headers, params=params, timeout=15)
            if resp.status_code == 200:
                commits = resp.json()
                if commits:
                    skill["commits_since_check"] = len(commits)
                    skill["last_updated"] = commits[0]["commit"]["committer"]["date"]
                    print(f"[TRACKER] {name}: {len(commits)} new commit(s)")
                else:
                    print(f"[TRACKER] {name}: no new commits")
            else:
                print(f"[TRACKER] {name}: API error {resp.status_code}")
        except Exception as e:
            print(f"[TRACKER] {name}: error - {e}")

        skill["last_checked"] = datetime.now().isoformat()
        self._save_tracker()
        return skill

    def check_all(self) -> list:
        """Check all registered skills for updates."""
        results = []
        for name in self.tracker_data["skills"]:
            result = self.check_updates(name)
            if result:
                results.append(result)
            time.sleep(1)  # Rate limiting
        return results

    def get_pending(self) -> list:
        """Get skills with pending updates."""
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
