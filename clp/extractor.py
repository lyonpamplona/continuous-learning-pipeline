"""Modulo Extrator — analisa repositórios e gera arquivos SKILL.md."""

import base64
import logging
import re
import time
from typing import Optional

import requests
import yaml

logger = logging.getLogger(__name__)


class Extractor:
    """Analisa repositórios e gera arquivos SKILL.md."""

    def __init__(self, config=None):
        self.config = config or {}
        self.github_token = self.config.get("github_token", "")
        self.headers = {}
        if self.github_token:
            self.headers["Authorization"] = f"token {self.github_token}"
        self.timeout = self.config.get("extract_timeout", 15)

    def fetch_readme(self, full_name: str) -> str:
        """Buscar conteudo do README de um repositório."""
        try:
            url = f"https://api.github.com/repos/{full_name}/readme"
            params = {"ref": "main"}
            resp = requests.get(url, headers=self.headers, params=params, timeout=self.timeout)
            if resp.status_code == 200:
                data = resp.json()
                return base64.b64decode(data.get("content", "")).decode("utf-8", errors="replace")
            logger.warning(f"Erro buscando README de '{full_name}': status {resp.status_code}")
        except Exception as e:
            logger.error(f"Erro buscando README de '{full_name}': {e}")
        return ""

    def fetch_files(self, full_name: str, path: str = "") -> list:
        """Busca arvores de arquivos de um repositório."""
        try:
            url = f"https://api.github.com/repos/{full_name}/contents/{path}"
            resp = requests.get(url, headers=self.headers, timeout=self.timeout)
            if resp.status_code == 200:
                return resp.json()
        except Exception as e:
            logger.error(f"Erro buscando arquivos de '{full_name}/{path}': {e}")
        return []

    def analyze_readme(self, readme: str) -> dict:
        """Analyze README content for workflow information."""
        info = {
            "purpose": "",
            "features": [],
            "installation": "",
            "usage": "",
            "commands": [],
            "sections": [],
        }

        # Extract purpose from first paragraph
        lines = readme.split("\n")
        purpose_lines = []
        for line in lines:
            line = line.strip()
            if not line or line.startswith("#") or line.startswith("-"):
                if purpose_lines:
                    break
                continue
            purpose_lines.append(line)
        info["purpose"] = " ".join(purpose_lines[:3])

        # Extract sections
        current_section = ""
        current_content = []
        for line in lines:
            if line.startswith("## ") and not line.startswith("###"):
                if current_section and current_content:
                    info["sections"].append({
                        "title": current_section,
                        "content": "\n".join(current_content),
                    })
                current_section = line[3:].strip()
                current_content = []
            else:
                current_content.append(line)
        if current_section and current_content:
            info["sections"].append({
                "title": current_section,
                "content": "\n".join(current_content),
            })

        # Extract code blocks (commands)
        code_blocks = re.findall(r"```(?:bash|sh|shell)?\s*\n(.*?)```", readme, re.DOTALL)
        for block in code_blocks:
            commands = [c.strip() for c in block.strip().split("\n") if c.strip() and not c.strip().startswith("#")]
            info["commands"].extend(commands)

        # Extract features from bullet lists
        for section in info["sections"]:
            if "feature" in section["title"].lower():
                for line in section["content"].split("\n"):
                    line = line.strip()
                    if line.startswith("-") or line.startswith("*"):
                        info["features"].append(line[1:].strip())

        return info

    def identify_workflows(self, readme_info: dict, metadata: dict) -> list:
        """Identify reusable workflows from repository data."""
        workflows = []

        # Analyze commands for CLI workflows
        if readme_info.get("commands"):
            workflows.append({
                "name": "cli-usage",
                "type": "command-line",
                "description": "CLI commands and usage patterns",
                "commands": readme_info["commands"][:10],
            })

        # Analyze sections for procedural workflows
        for section in readme_info.get("sections", []):
            title = section["title"].lower()
            if any(kw in title for kw in ["install", "setup", "configure", "deploy", "usage", "example"]):
                workflows.append({
                    "name": f"{title}-workflow",
                    "type": "procedure",
                    "description": f"{section['title']} procedure",
                    "content": section["content"][:500],
                })

        # Add general workflow from purpose
        if readme_info.get("purpose"):
            workflows.append({
                "name": "general-usage",
                "type": "overview",
                "description": readme_info["purpose"][:200],
            })

        return workflows

    def generate_skill_md(self, repo_name: str, metadata: dict, readme_info: dict,
                         workflows: list, skill_name: str = None) -> str:
        """Generate SKILL.md content from extracted data."""
        if not skill_name:
            skill_name = metadata.get("name", repo_name.split("/")[-1]).lower().replace(" ", "-")

        description = readme_info.get("purpose", "")[:60]
        if description and not description.endswith("."):
            description = description + "."

        # Build procedure from workflows
        procedure = ""
        for i, wf in enumerate(workflows[:5], 1):
            procedure += f"{i}. **{wf['name']}**: {wf.get('description', '')}\n"
            if wf.get("commands"):
                procedure += "   ```bash\n"
                for cmd in wf["commands"][:3]:
                    procedure += f"   {cmd}\n"
                procedure += "   ```\n"

        if not procedure:
            procedure = "1. Clone the repository\n2. Follow installation instructions\n3. Use according to documentation\n"

        # Build pitfalls
        pitfalls = []
        if metadata.get("stars", 0) < 100:
            pitfalls.append("Low star count may indicate limited community support")
        if not metadata.get("updated_at"):
            pitfalls.append("Repository may not be actively maintained")
        pitfalls.append("Always verify commands work in your environment")

        skill_content = f"""---
name: {skill_name}
trigger: {metadata.get('name', '')}, {repo_name}, {readme_info.get('purpose', '')[:50]}
description: "{description}"
version: 1.0.0
author: CLP Pipeline, extracted from {repo_name}
license: MIT
metadata:
  source:
    repo: {repo_name}
    url: https://github.com/{repo_name}
    stars: {metadata.get('stars', 0)}
    language: {metadata.get('language', '')}
    extracted_at: {time.strftime('%Y-%m-%d')}
---

# {metadata.get('name', skill_name)}

{readme_info.get('purpose', '')}

## When to Use

- Working with {metadata.get('name', 'the project')}
- Need {readme_info.get('purpose', 'functionality')[:100].lower()}

## Procedure

{procedure}

## Usage

{readme_info.get('usage', 'Follow the project documentation for detailed usage.')}

## Pitfalls

""" + "\n".join(f"- {p}" for p in pitfalls) + f"""

## Source

- Repository: https://github.com/{repo_name}
- Stars: {metadata.get('stars', 0)}
- Language: {metadata.get('language', 'N/A')}
- Extracted: {time.strftime('%Y-%m-%d')}
"""
        return skill_content

    def extract(self, full_name: str, skill_name: str = None) -> Optional[str]:
        """Full extraction pipeline for a repository."""
        # Fetch metadata
        metadata = {}
        try:
            url = f"https://api.github.com/repos/{full_name}"
            resp = requests.get(url, headers=self.headers, timeout=15)
            if resp.status_code == 200:
                metadata = resp.json()
        except Exception:
            pass

        # Fetch and analyze README
        readme = self.fetch_readme(full_name)
        if not readme:
            return None

        readme_info = self.analyze_readme(readme)
        workflows = self.identify_workflows(readme_info, metadata)

        # Generate SKILL.md
        return self.generate_skill_md(full_name, metadata, readme_info, workflows, skill_name)
