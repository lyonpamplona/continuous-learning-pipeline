"""Scout module — discovers relevant repositories from GitHub."""

import json
import time
from pathlib import Path
from typing import Optional

import requests


class Scout:
    """Discovers relevant GitHub repositories for skill extraction."""

    def __init__(self, config=None):
        self.config = config or {}
        self.github_token = self.config.get("github_token", "")
        self.headers = {}
        if self.github_token:
            self.headers["Authorization"] = f"token {self.github_token}"

    def search_trending(self, keywords: list = None, max_results: int = 10) -> list:
        """Search GitHub for trending repositories matching keywords."""
        if keywords is None:
            keywords = self.config.get("scout_keywords", "agents,ai,automation").split(",")

        results = []
        seen = set()

        for keyword in keywords:
            keyword = keyword.strip()
            if not keyword:
                continue

            try:
                url = f"https://api.github.com/search/repositories"
                params = {
                    "q": f"{keyword} stars:>100 created:>2024-01-01",
                    "sort": "stars",
                    "order": "desc",
                    "per_page": min(max_results, 30),
                }
                resp = requests.get(url, params=params, headers=self.headers, timeout=15)

                if resp.status_code != 200:
                    continue

                data = resp.json()
                for repo in data.get("items", []):
                    full_name = repo.get("full_name", "")
                    if full_name in seen:
                        continue
                    seen.add(full_name)

                    results.append({
                        "full_name": full_name,
                        "name": repo.get("name", ""),
                        "owner": repo.get("owner", {}).get("login", ""),
                        "description": repo.get("description", ""),
                        "stars": repo.get("stargazers_count", 0),
                        "forks": repo.get("forks_count", 0),
                        "language": repo.get("language", ""),
                        "updated_at": repo.get("updated_at", ""),
                        "created_at": repo.get("created_at", ""),
                        "topics": repo.get("topics", []),
                        "url": repo.get("html_url", ""),
                        "api_url": repo.get("url", ""),
                    })

                    if len(results) >= max_results:
                        break
            except Exception as e:
                print(f"[SCOUT] Error searching '{keyword}': {e}")
                time.sleep(2)

        # Sort by stars descending
        results.sort(key=lambda r: r.get("stars", 0), reverse=True)
        return results[:max_results]

    def get_repo_details(self, full_name: str) -> dict:
        """Get detailed information about a repository."""
        try:
            url = f"https://api.github.com/repos/{full_name}"
            resp = requests.get(url, headers=self.headers, timeout=15)
            if resp.status_code == 200:
                return resp.json()
        except Exception:
            pass
        return {}

    def save_results(self, results: list, output_path: str = None) -> str:
        """Save scout results to a JSON file."""
        if output_path is None:
            data_dir = Path(self.config.get("data_dir", "~/.clp/data")).expanduser()
            data_dir.mkdir(parents=True, exist_ok=True)
            output_path = str(data_dir / "scout-results.json")
        else:
            output_path = str(Path(output_path).expanduser())
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w") as f:
            json.dump(results, f, indent=2)

        return output_path
