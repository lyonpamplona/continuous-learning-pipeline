"""Plugin custom para integracao com frameworks de agente personalizados."""

import logging
from pathlib import Path
from typing import Optional

from clp.plugins import AgentPlugin

logger = logging.getLogger(__name__)


class CustomPlugin(AgentPlugin):
    """Plugin custom para integracao com frameworks de agente personalizados.

    Este plugin permite que usuarios criem suas proprias integracoes
    com frameworks de agente que nao sao suportados nativamente.
    """

    def __init__(self, skills_dir: str = "~/.clp/skills", **kwargs):
        self.skills_dir = Path(skills_dir).expanduser()
        self.skills_dir.mkdir(parents=True, exist_ok=True)
        self.config = kwargs

    def create_skill(self, name: str, content: str, category: str = "geral") -> bool:
        """Criar uma skill no framework custom."""
        try:
            skill_dir = self.skills_dir / category / name
            skill_dir.mkdir(parents=True, exist_ok=True)
            (skill_dir / "SKILL.md").write_text(content)
            logger.info(f"Skill '{name}' criada em {skill_dir}")
            return True
        except Exception as e:
            logger.error(f"Erro ao criar skill '{name}': {e}")
            return False

    def update_skill(self, name: str, content: str) -> bool:
        """Atualizar uma skill existente."""
        try:
            for skill_file in self.skills_dir.rglob("SKILL.md"):
                if skill_file.parent.name == name:
                    skill_file.write_text(content)
                    logger.info(f"Skill '{name}' atualizada")
                    return True
            logger.warning(f"Skill '{name}' nao encontrada para atualizacao")
            return False
        except Exception as e:
            logger.error(f"Erro ao atualizar skill '{name}': {e}")
            return False

    def delete_skill(self, name: str) -> bool:
        """Deletar uma skill."""
        import shutil
        try:
            for skill_dir in self.skills_dir.rglob(name):
                if skill_dir.is_dir():
                    shutil.rmtree(skill_dir)
                    logger.info(f"Skill '{name}' deletada")
                    return True
            logger.warning(f"Skill '{name}' nao encontrada para delecao")
            return False
        except Exception as e:
            logger.error(f"Erro ao deletar skill '{name}': {e}")
            return False

    def list_skills(self) -> list:
        """Listar todas as skills."""
        skills = []
        try:
            for skill_file in self.skills_dir.rglob("SKILL.md"):
                skills.append({
                    "name": skill_file.parent.name,
                    "category": skill_file.parent.parent.name,
                    "path": str(skill_file),
                })
            logger.info(f"Listadas {len(skills)} skills")
        except Exception as e:
            logger.error(f"Erro ao listar skills: {e}")
        return skills

    def notify(self, message: str, level: str = "info") -> bool:
        """Enviar notificacao ao usuario."""
        try:
            log_msg = f"[{level.upper()}] {message}"
            if level == "error":
                logger.error(log_msg)
            elif level == "warning":
                logger.warning(log_msg)
            else:
                logger.info(log_msg)
            return True
        except Exception as e:
            logger.error(f"Erro ao enviar notificacao: {e}")
            return False

    def schedule_job(self, name: str, schedule: str, callback: str) -> bool:
        """Agendar um job periodico."""
        try:
            logger.info(f"Job '{name}' agendado: {schedule} -> {callback}")
            # Implementacao custom pode sobrescrever este metodo
            return True
        except Exception as e:
            logger.error(f"Erro ao agendar job '{name}': {e}")
            return False
