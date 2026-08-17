"""Interface de linha de comando para o Continuous Learning Pipeline."""

import argparse
import json
import logging
import sys
from pathlib import Path

from clp.config import Config
from clp.plugins import get_plugin
from clp.scout import Scout
from clp.extractor import Extractor
from clp.scorer import Scorer
from clp.publisher import Publisher
from clp.tracker import Tracker
from clp.dashboard import Dashboard

logger = logging.getLogger(__name__)


def main():
    """Ponto de entrada principal da CLI."""
    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    parser = argparse.ArgumentParser(
        prog="clp",
        description="Continuous Learning Pipeline - Descoberta automatizada de skills para agentes de IA"
    )
    parser.add_argument("--config", help="Caminho para arquivo de configuracao")
    parser.add_argument("--plugin", default="file", help="Tipo de plugin (file, hermes, custom)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Modo verboso")

    subparsers = parser.add_subparsers(dest="command", help="Comandos disponiveis")

    # Comando Scout
    scout_parser = subparsers.add_parser("scout", help="Descobrir repositorios no GitHub")
    scout_parser.add_argument("--keywords", help="Palavras-chave separadas por virgula")
    scout_parser.add_argument("--max-results", type=int, default=10, help="Maximo de resultados")
    scout_parser.add_argument("--output", help="Caminho do arquivo de saida")

    # Comando Extract
    extract_parser = subparsers.add_parser("extract", help="Extrair skill de um repositorio")
    extract_parser.add_argument("--repo", required=True, help="Repositorio (owner/name)")
    extract_parser.add_argument("--name", help="Nome da skill")
    extract_parser.add_argument("--output", help="Caminho do arquivo de saida")

    # Comando Score
    score_parser = subparsers.add_parser("score", help="Pontuar um arquivo SKILL.md")
    score_parser.add_argument("--skill", required=True, help="Caminho para SKILL.md")

    # Comando Publish
    publish_parser = subparsers.add_parser("publish", help="Publicar uma skill")
    publish_parser.add_argument("--skill", required=True, help="Caminho para SKILL.md")
    publish_parser.add_argument("--name", help="Nome da skill")
    publish_parser.add_argument("--category", default="geral", help="Categoria da skill")

    # Comando Dashboard
    dashboard_parser = subparsers.add_parser("dashboard", help="Gerar dashboard de revisao")
    dashboard_parser.add_argument("--html", action="store_true", help="Gerar dashboard HTML")
    dashboard_parser.add_argument("--serve", action="store_true", help="Servir dashboard no localhost")

    # Comando Track
    track_parser = subparsers.add_parser("track", help="Rastrear atualizacoes de skills")
    track_parser.add_argument("--register", help="Registrar skill para rastreamento (name:repo)")
    track_parser.add_argument("--check", action="store_true", help="Verificar todas as skills rastreadas")

    # Comando Pipeline
    pipeline_parser = subparsers.add_parser("pipeline", help="Executar pipeline completo")
    pipeline_parser.add_argument("--keywords", help="Palavras-chave para scout")
    pipeline_parser.add_argument("--max-results", type=int, default=5, help="Maximo de repositorios para processar")

    args = parser.parse_args()

    # Ajustar nivel de logging se verbose
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    config = Config(args.config)
    plugin = get_plugin(args.plugin, skills_dir=config.get("skills_dir"))

    if args.command == "scout":
        _cmd_scout(args, config)
    elif args.command == "extract":
        _cmd_extract(args, config)
    elif args.command == "score":
        _cmd_score(args, config)
    elif args.command == "publish":
        _cmd_publish(args, config, plugin)
    elif args.command == "dashboard":
        _cmd_dashboard(args, config)
    elif args.command == "track":
        _cmd_track(args, config)
    elif args.command == "pipeline":
        _cmd_pipeline(args, config, plugin)
    else:
        parser.print_help()


def _cmd_scout(args, config):
    """Executar comando scout."""
    scout = Scout(config)
    keywords = args.keywords or config.get("scout_keywords", "agents,ai,automation")
    keywords = [k.strip() for k in keywords.split(",")]
    results = scout.search_trending(keywords, args.max_results)

    if results:
        logger.info(f"Encontrados {len(results)} repositorios:")
        for repo in results:
            logger.info(f"  - {repo['full_name']} ({repo['stars']} stars)")
            logger.info(f"    {repo.get('description', '')[:80]}")

        output = args.output or config.get("data_dir", "~/.clp/data")
        output_path = scout.save_results(results, output)
        logger.info(f"Resultados salvos em {output_path}")
    else:
        logger.warning("Nenhum repositorio encontrado.")


def _cmd_extract(args, config):
    """Executar comando extract."""
    extractor = Extractor(config)
    skill_content = extractor.extract(args.repo, args.name)

    if skill_content:
        output = args.output or f"~/.clp/workspace/pending/{args.name or args.repo.split('/')[-1]}/SKILL.md"
        output_path = Path(output).expanduser()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(skill_content)
        logger.info(f"Skill salva em {output_path}")
    else:
        logger.error("Falha ao extrair skill.")


def _cmd_score(args, config):
    """Executar comando score."""
    scorer = Scorer(config.get("score_min_pass", 70))
    skill_data = scorer.load_skill(args.skill)

    if skill_data:
        result = scorer.score(skill_data)
        logger.info(f"Score: {result['score']}/100 ({result['decision']})")
        for check in result['checks']:
            logger.info(f"  {check}")
    else:
        logger.error("Falha ao carregar skill.")


def _cmd_publish(args, config, plugin):
    """Executar comando publish."""
    publisher = Publisher(plugin, config)
    success = publisher.publish(args.skill, args.name, args.category)
    if success:
        logger.info("Skill publicada com sucesso.")
    else:
        logger.error("Falha ao publicar skill.")


def _cmd_dashboard(args, config):
    """Executar comando dashboard."""
    dashboard = Dashboard(config)
    result = dashboard.generate(generate_html=args.html or True)

    logger.info(f"Dashboard - Pendentes: {result['pending']}, Aprovadas: {result['approved']}, Rejeitadas: {result['rejected']}")
    logger.info(f"HTML: {result.get('html_path', 'N/A')}")
    logger.info(f"MD: {result.get('md_path', 'N/A')}")

    if args.serve:
        import http.server
        port = config.get("dashboard_port", 8080)
        reports_dir = Path(config.get("reports_dir", "~/.clp/reports")).expanduser()

        handler = http.server.SimpleHTTPRequestHandler
        server = http.server.HTTPServer(("0.0.0.0", port), handler)
        server.directory = str(reports_dir)

        logger.info(f"Servindo em http://0.0.0.0:{port}")
        logger.info(f"Abra http://localhost:{port}/review-dashboard.html")
        server.serve_forever()


def _cmd_track(args, config):
    """Executar comando track."""
    tracker = Tracker(config)

    if args.register:
        name, repo = args.register.split(":", 1)
        tracker.register_skill(name, repo)
        logger.info(f"Registrado {name} -> {repo}")
    elif args.check:
        results = tracker.check_all()
        pending = tracker.get_pending()
        if pending:
            logger.info(f"{len(pending)} skill(s) com atualizacoes:")
            for p in pending:
                logger.info(f"  - {p['name']}: {p['commits']} novo(s) commit(s)")
        else:
            logger.info("Nenhuma atualizacao encontrada.")


def _cmd_pipeline(args, config, plugin):
    """Executar pipeline completo."""
    logger.info("Iniciando pipeline completo...")

    # Passo 1: Scout
    logger.info("Passo 1: Scouting...")
    scout = Scout(config)
    keywords = args.keywords or config.get("scout_keywords", "agents,ai,automation")
    keywords = [k.strip() for k in keywords.split(",")]
    results = scout.search_trending(keywords, args.max_results)
    logger.info(f"Encontrados {len(results)} repositorios")

    # Passo 2: Extract & Score
    logger.info("Passo 2: Extraindo e pontuando...")
    extractor = Extractor(config)
    scorer = Scorer(config.get("score_min_pass", 70))
    workspace = Path(config.get("workspace_dir", "~/.clp/workspace")).expanduser()
    pending_dir = workspace / "pending"

    for repo in results:
        full_name = repo["full_name"]
        logger.info(f"Processando {full_name}...")

        skill_content = extractor.extract(full_name)
        if not skill_content:
            logger.warning(f"  Pulando {full_name} (sem conteudo)")
            continue

        # Salvar em pending
        skill_name = repo["name"].lower().replace(" ", "-")
        skill_path = pending_dir / skill_name / "SKILL.md"
        skill_path.parent.mkdir(parents=True, exist_ok=True)
        skill_path.write_text(skill_content)

        # Pontuar
        skill_data = scorer.load_skill(str(skill_path))
        if skill_data:
            result = scorer.score(skill_data)
            logger.info(f"  {skill_name}: {result['score']}/100 ({result['decision']})")

    # Passo 3: Dashboard
    logger.info("Passo 3: Gerando dashboard...")
    dashboard = Dashboard(config)
    dashboard.generate()

    logger.info("Pipeline concluido.")


if __name__ == "__main__":
    main()
