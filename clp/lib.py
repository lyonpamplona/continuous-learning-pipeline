"""
Interface de biblioteca para uso do CLP em outras CLIs com agentes.

Este modulo permite integrar o Continuous Learning Pipeline como uma biblioteca
em qualquer CLI ou framework de agente, sem depender da CLI do CLP.

Exemplo de uso:
    from clp.lib import CLP

    # Criar instancia com configuracao
    pipeline = CLP(config={
        "github_token": "seu_token",
        "skills_dir": "~/.meu-agente/skills",
        "plugin_type": "file",
    })

    # Descobrir repositorios
    repos = pipeline.scout(keywords=["agents", "ai"], max_results=10)

    # Extrair skill de um repositorio
    skill_content = pipeline.extract("langchain-ai/langchain")

    # Pontuar skill
    result = pipeline.score(skill_content)

    # Publicar skill
    pipeline.publish(skill_content, name="langchain", category="ai")
"""

import logging
from pathlib import Path
from typing import Optional

from clp.config import Config
from clp.plugins import get_plugin, AgentPlugin
from clp.scout import Scout
from clp.extractor import Extractor
from clp.scorer import Scorer
from clp.publisher import Publisher
from clp.tracker import Tracker
from clp.dashboard import Dashboard

logger = logging.getLogger(__name__)


class CLP:
    """Interface de biblioteca para o Continuous Learning Pipeline.

    Permite usar o CLP como biblioteca em outras CLIs com agentes,
    sem depender da CLI do CLP.

    Args:
        config: Dicionario de configuracao ou caminho para arquivo YAML.
        plugin: Tipo de plugin ("file", "hermes", "custom") ou instancia de AgentPlugin.

    Exemplo:
        >>> from clp.lib import CLP
        >>> pipeline = CLP(config={"github_token": "token"})
        >>> repos = pipeline.scout(keywords=["agents"])
    """

    def __init__(
        self,
        config: dict | str | None = None,
        plugin: str | AgentPlugin | None = None,
    ):
        """Inicializar o CLP.

        Args:
            config: Dicionario de configuracao ou caminho para arquivo YAML.
            plugin: Tipo de plugin ou instancia de AgentPlugin.
        """
        # Configurar configuracao
        if isinstance(config, str):
            self._config = Config(config)
        elif isinstance(config, dict):
            self._config = Config()
            for key, value in config.items():
                self._config.set(key, value)
        else:
            self._config = Config()

        # Configurar plugin
        if isinstance(plugin, AgentPlugin):
            self._plugin = plugin
        elif isinstance(plugin, str):
            self._plugin = get_plugin(plugin, skills_dir=self._config.get("skills_dir"))
        else:
            plugin_type = self._config.get("plugin_type", "file") or "file"
            self._plugin = get_plugin(plugin_type, skills_dir=self._config.get("skills_dir"))

        # Instanciar modulos
        self._scout = Scout(self._config)
        self._extractor = Extractor(self._config)
        self._scorer = Scorer(
            min_pass=self._config.get("score_min_pass", 70) or 70,
            max_size=self._config.get("score_max_size", 100000) or 100000,
        )
        self._publisher = Publisher(self._plugin, self._config)
        self._tracker = Tracker(self._config)
        self._dashboard = Dashboard(self._config)

    @property
    def config(self) -> Config:
        """Retorna a configuracao atual."""
        return self._config

    @property
    def plugin(self) -> AgentPlugin:
        """Retorna o plugin atual."""
        return self._plugin

    def scout(self, keywords: list[str] | None = None, max_results: int = 10) -> list[dict]:
        """Descobrir repositorios relevantes no GitHub.

        Args:
            keywords: Palavras-chave para busca.
            max_results: Maximo de resultados.

        Returns:
            Lista de dicionarios com informacoes dos repositorios.
        """
        return self._scout.search_trending(keywords, max_results)

    def extract(self, repo: str, skill_name: str | None = None) -> str | None:
        """Extrair skill de um repositorio GitHub.

        Args:
            repo: Repositorio no formato "owner/name".
            skill_name: Nome opcional para a skill.

        Returns:
            Conteudo SKILL.md ou None se falhar.
        """
        return self._extractor.extract(repo, skill_name)

    def score(self, skill_content: str | str) -> dict:
        """Pontuar um arquivo SKILL.md.

        Args:
            skill_content: Conteudo SKILL.md ou caminho para arquivo.

        Returns:
            Dicionario com score, decisao e checks.
        """
        # Se for caminho, carregar o arquivo
        if isinstance(skill_content, str) and Path(skill_content).exists():
            skill_data = self._scorer.load_skill(skill_content)
        else:
            # Se for conteudo, salvar temporariamente
            import tempfile
            with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
                f.write(skill_content)
                temp_path = f.name
            skill_data = self._scorer.load_skill(temp_path)

        if not skill_data:
            return {"score": 0, "decision": "REJECT", "checks": ["FAIL: Nao foi possivel carregar a skill"]}

        return self._scorer.score(skill_data)

    def publish(self, skill_content: str | str, name: str | None = None, category: str = "geral") -> bool:
        """Publicar uma skill.

        Args:
            skill_content: Conteudo SKILL.md ou caminho para arquivo.
            name: Nome da skill.
            category: Categoria da skill.

        Returns:
            True se publicada com sucesso.
        """
        # Se for conteudo, salvar temporariamente
        if isinstance(skill_content, str) and not Path(skill_content).exists():
            import tempfile
            with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
                f.write(skill_content)
                temp_path = f.name
            return self._publisher.publish(temp_path, name, category)

        return self._publisher.publish(skill_content, name, category)

    def track_register(self, name: str, repo: str) -> None:
        """Registrar uma skill para rastreamento.

        Args:
            name: Nome da skill.
            repo: Repositorio no formato "owner/name".
        """
        self._tracker.register_skill(name, repo)

    def track_check(self) -> list[dict]:
        """Verificar atualizacoes de todas as skills registradas.

        Returns:
            Lista de skills com atualizacoes pendentes.
        """
        self._tracker.check_all()
        return self._tracker.get_pending()

    def dashboard(self, generate_html: bool = True) -> dict:
        """Gerar dashboard de revisao.

        Args:
            generate_html: Se deve gerar dashboard HTML.

        Returns:
            Dicionario com status do dashboard.
        """
        return self._dashboard.generate(generate_html=generate_html)

    def pipeline(self, keywords: list[str] | None = None, max_results: int = 5) -> dict:
        """Executar pipeline completo.

        Args:
            keywords: Palavras-chave para scout.
            max_results: Maximo de repositorios para processar.

        Returns:
            Dicionario com resultados do pipeline.
        """
        logger.info("Iniciando pipeline completo...")

        # Passo 1: Scout
        logger.info("Passo 1: Scouting...")
        results = self.scout(keywords, max_results)
        logger.info(f"Encontrados {len(results)} repositorios")

        # Passo 2: Extract & Score
        logger.info("Passo 2: Extraindo e pontuando...")
        extracted = []
        for repo in results:
            full_name = repo["full_name"]
            logger.info(f"Processando {full_name}...")

            skill_content = self.extract(full_name)
            if not skill_content:
                logger.warning(f"  Pulando {full_name} (sem conteudo)")
                continue

            score_result = self.score(skill_content)
            logger.info(f"  {repo['name']}: {score_result['score']}/100 ({score_result['decision']})")
            extracted.append({
                "repo": full_name,
                "skill": skill_content,
                "score": score_result,
            })

        # Passo 3: Dashboard
        logger.info("Passo 3: Gerando dashboard...")
        dashboard_result = self.dashboard()

        logger.info("Pipeline concluido.")

        return {
            "scout_results": results,
            "extracted": extracted,
            "dashboard": dashboard_result,
        }
