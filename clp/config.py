"""Gerenciamento de configuracao para CLP."""

import os
from pathlib import Path
from typing import Optional

import yaml


class Config:
    """Configuration for the Continuous Learning Pipeline."""

    DEFAULTS = {
        "github_token": "",
        "github_per_page": 30,
        "scout_keywords": "agents,ai,automation,skills,workflows",
        "scout_max_results": 10,
        "scout_min_stars": 100,
        "extract_timeout": 30,
        "extract_max_files": 50,
        "score_min_pass": 70,
        "score_max_size": 100000,
        "dashboard_port": 8080,
        "dashboard_host": "0.0.0.0",
        "dashboard_refresh": 60,
        "skills_dir": "~/.clp/skills",
        "workspace_dir": "~/.clp/workspace",
        "reports_dir": "~/.clp/reports",
        "data_dir": "~/.clp/data",
        "plugin_type": "file",
    }

    def __init__(self, config_path: Optional[str] = None):
        self._config = dict(self.DEFAULTS)
        self._load_env()
        if config_path and Path(config_path).exists():
            self._load_file(config_path)

    def _load_env(self):
        env_mappings = {
            "GITHUB_TOKEN": "github_token",
            "CLP_SKILLS_DIR": "skills_dir",
            "CLP_WORKSPACE_DIR": "workspace_dir",
            "CLP_PLUGIN_TYPE": "plugin_type",
            "DASHBOARD_PORT": "dashboard_port",
        }
        for env_key, config_key in env_mappings.items():
            value = os.environ.get(env_key)
            if value:
                self._config[config_key] = value

    def _load_file(self, path: str):
        import yaml
        with open(path) as f:
            data = yaml.safe_load(f) or {}
        self._config.update(data)

    def get(self, key: str, default=None):
        return self._config.get(key, default)

    def set(self, key: str, value):
        self._config[key] = value

    def __getitem__(self, key):
        return self._config[key]

    def __setitem__(self, key, value):
        self._config[key] = value
