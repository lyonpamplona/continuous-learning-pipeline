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
        self.headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if self.github_token:
            self.headers["Authorization"] = f"token {self.github_token}"
        self.timeout = self.config.get("extract_timeout", 15)

    def fetch_readme(self, full_name: str) -> str:
        """Buscar conteudo do README de um repositório."""
        for branch in ["main", "master"]:
            try:
                url = f"https://api.github.com/repos/{full_name}/readme"
                params = {"ref": branch}
                resp = requests.get(url, headers=self.headers, params=params, timeout=self.timeout)
                if resp.status_code == 200:
                    data = resp.json()
                    return base64.b64decode(data.get("content", "")).decode("utf-8", errors="replace")
                logger.warning(f"Erro buscando README de '{full_name}' (branch={branch}): status {resp.status_code}")
            except Exception as e:
                logger.error(f"Erro buscando README de '{full_name}' (branch={branch}): {e}")
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

    @staticmethod
    def strip_html(text: str) -> str:
        """Remove tags HTML e entitidades de um texto."""
        # Remover tags HTML
        clean = re.sub(r"<[^>]+>", "", text)
        # Remover entitidades HTML comuns
        clean = clean.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
        clean = clean.replace("&quot;", '"').replace("&#39;", "'").replace("&nbsp;", " ")
        # Remover espacos extras
        clean = re.sub(r"\s+", " ", clean).strip()
        return clean

    def analyze_readme(self, readme: str) -> dict:
        """Analisa conteudo do README por informacoes de workflow."""
        info = {
            "purpose": "",
            "features": [],
            "installation": "",
            "usage": "",
            "commands": [],
            "sections": [],
        }

        # Extrair proposito do primeiro paragrafo
        lines = readme.split("\n")
        purpose_lines = []
        for line in lines:
            line = line.strip()
            if not line or line.startswith("#") or line.startswith("-"):
                if purpose_lines:
                    break
                continue
            purpose_lines.append(line)
        raw_purpose = " ".join(purpose_lines[:3])
        info["purpose"] = self.strip_html(raw_purpose)

        # Extrair secoes
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

        # Extrair blocos de codigo (comandos)
        code_blocks = re.findall(r"```(?:bash|sh|shell)?\s*\n(.*?)```", readme, re.DOTALL)
        for block in code_blocks:
            commands = [c.strip() for c in block.strip().split("\n") if c.strip() and not c.strip().startswith("#")]
            info["commands"].extend(commands)

        # Extrair features de listas com marcadores
        for section in info["sections"]:
            if "feature" in section["title"].lower():
                for line in section["content"].split("\n"):
                    line = line.strip()
                    if line.startswith("-") or line.startswith("*"):
                        info["features"].append(line[1:].strip())

        return info

    def identify_workflows(self, readme_info: dict, metadata: dict) -> list:
        """Identifica workflows reutilizaveis a partir dos dados do repositório."""
        workflows = []

        # Analisar comandos para workflows de CLI
        if readme_info.get("commands"):
            workflows.append({
                "name": "cli-usage",
                "type": "command-line",
                "description": "Comandos CLI e padroes de uso",
                "commands": readme_info["commands"][:10],
            })

        # Analisar secoes para workflows procedurais
        for section in readme_info.get("sections", []):
            title = section["title"].lower()
            if any(kw in title for kw in ["install", "setup", "configure", "deploy", "usage", "example"]):
                workflows.append({
                    "name": f"{title}-workflow",
                    "type": "procedure",
                    "description": f"Procedimento {section['title']}",
                    "content": section["content"][:500],
                })

        # Adicionar workflow geral a partir do proposito
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

        description = self.strip_html(readme_info.get("purpose", ""))[:60]
        if description and not description.endswith("."):
            description = description + "."
        # Escapar aspas para YAML
        description = description.replace('"', "'").replace("\\", "\\\\")

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

        # Sanitize trigger value for YAML safety
        trigger_parts = []
        name_val = metadata.get("name", "")
        if name_val:
            trigger_parts.append(name_val)
        trigger_parts.append(repo_name)
        purpose_val = readme_info.get("purpose", "")[:50]
        if purpose_val:
            trigger_parts.append(purpose_val)
        trigger_value = ", ".join(trigger_parts)
        # Escape special YAML characters in trigger
        trigger_value = trigger_value.replace('"', "'").replace("\n", " ").replace("|", "").replace(":", " ")

        skill_content = f"""---
name: {skill_name}
trigger: "{trigger_value}"
description: "{description}"
version: 1.0.0
author: "{repo_name}"
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
        """Pipeline completo de extracao para um repositório."""
        # Buscar metadata
        metadata = {}
        try:
            url = f"https://api.github.com/repos/{full_name}"
            resp = requests.get(url, headers=self.headers, timeout=self.timeout)
            if resp.status_code == 200:
                metadata = resp.json()
        except Exception as e:
            logger.error(f"Erro buscando metadata de '{full_name}': {e}")

        # Buscar e analisar README
        readme = self.fetch_readme(full_name)
        if not readme:
            return None

        readme_info = self.analyze_readme(readme)
        workflows = self.identify_workflows(readme_info, metadata)

        # Gerar SKILL.md
        return self.generate_skill_md(full_name, metadata, readme_info, workflows, skill_name)
