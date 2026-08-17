"""Modulo Scout — descobre repositórios relevantes no GitHub."""

import json
import logging
import time
from pathlib import Path
from typing import Optional

import requests

logger = logging.getLogger(__name__)


class Scout:
    """Descobre repositórios relevantes no GitHub para extração de skills."""

    def __init__(self, config=None):
        self.config = config or {}
        self.github_token = self.config.get("github_token", "")
        self.headers = {}
        if self.github_token:
            self.headers["Authorization"] = f"token {self.github_token}"
        self.timeout = self.config.get("extract_timeout", 15)
        self.rate_limit_delay = self.config.get("rate_limit_delay", 2)

    def search_trending(self, keywords: list = None, max_results: int = 10) -> list:
        """Busca repositórios trending no GitHub por palavras-chave."""
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
                resp = requests.get(url, params=params, headers=self.headers, timeout=self.timeout)

                if resp.status_code != 200:
                    logger.warning(f"Erro buscando '{keyword}': status {resp.status_code}")
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
                logger.error(f"Erro buscando '{keyword}': {e}")
                time.sleep(self.rate_limit_delay)

        # Ordenar por estrelas descendente
        results.sort(key=lambda r: r.get("stars", 0), reverse=True)
        return results[:max_results]

    def get_repo_details(self, full_name: str) -> dict:
        """Obtem informacoes detalhadas sobre um repositório."""
        try:
            url = f"https://api.github.com/repos/{full_name}"
            resp = requests.get(url, headers=self.headers, timeout=self.timeout)
            if resp.status_code == 200:
                return resp.json()
            logger.warning(f"Erro obtendo detalhes de '{full_name}': status {resp.status_code}")
        except Exception as e:
            logger.error(f"Erro obtendo detalhes de '{full_name}': {e}")
        return {}

    def save_results(self, results: list, output_path: str = None) -> str:
        """Salva resultados do scout em um arquivo JSON."""
        if output_path is None:
            data_dir = Path(self.config.get("data_dir", "~/.clp/data")).expanduser()
            data_dir.mkdir(parents=True, exist_ok=True)
            output_path = str(data_dir / "scout-results.json")
        else:
            output_path = str(Path(output_path).expanduser())
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w") as f:
            json.dump(results, f, indent=2)

        logger.info(f"Resultados salvos em {output_path}")
        return output_path
