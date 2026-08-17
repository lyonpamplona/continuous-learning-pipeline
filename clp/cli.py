"""CLI interface for the Continuous Learning Pipeline."""

import argparse
import json
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


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="clp",
        description="Continuous Learning Pipeline - Automated skill discovery for AI agents"
    )
    parser.add_argument("--config", help="Path to config file")
    parser.add_argument("--plugin", default="file", help="Plugin type (file, hermes)")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Scout command
    scout_parser = subparsers.add_parser("scout", help="Discover repositories from GitHub")
    scout_parser.add_argument("--keywords", help="Comma-separated keywords to search")
    scout_parser.add_argument("--max-results", type=int, default=10, help="Max results")
    scout_parser.add_argument("--output", help="Output file path")

    # Extract command
    extract_parser = subparsers.add_parser("extract", help="Extract skill from repository")
    extract_parser.add_argument("--repo", required=True, help="Repository (owner/name)")
    extract_parser.add_argument("--name", help="Skill name")
    extract_parser.add_argument("--output", help="Output file path")

    # Score command
    score_parser = subparsers.add_parser("score", help="Score a SKILL.md file")
    score_parser.add_argument("--skill", required=True, help="Path to SKILL.md")

    # Publish command
    publish_parser = subparsers.add_parser("publish", help="Publish a skill")
    publish_parser.add_argument("--skill", required=True, help="Path to SKILL.md")
    publish_parser.add_argument("--name", help="Skill name")
    publish_parser.add_argument("--category", default="general", help="Skill category")

    # Dashboard command
    dashboard_parser = subparsers.add_parser("dashboard", help="Generate review dashboard")
    dashboard_parser.add_argument("--html", action="store_true", help="Generate HTML dashboard")
    dashboard_parser.add_argument("--serve", action="store_true", help="Serve dashboard on localhost")

    # Track command
    track_parser = subparsers.add_parser("track", help="Track skill updates")
    track_parser.add_argument("--register", help="Register skill for tracking (name:repo)")
    track_parser.add_argument("--check", action="store_true", help="Check all tracked skills")

    # Pipeline command
    pipeline_parser = subparsers.add_parser("pipeline", help="Run full pipeline")
    pipeline_parser.add_argument("--keywords", help="Keywords for scout")
    pipeline_parser.add_argument("--max-results", type=int, default=5, help="Max repos to process")

    args = parser.parse_args()
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
    """Run scout command."""
    scout = Scout(config)
    keywords = args.keywords or config.get("scout_keywords", "agents,ai,automation")
    keywords = [k.strip() for k in keywords.split(",")]
    results = scout.search_trending(keywords, args.max_results)

    if results:
        print(f"[SCOUT] Found {len(results)} repositories:")
        for repo in results:
            print(f"  - {repo['full_name']} ({repo['stars']} stars)")
            print(f"    {repo.get('description', '')[:80]}")

        output = args.output or config.get("data_dir", "~/.clp/data")
        output_path = scout.save_results(results, output)
        print(f"[SCOUT] Results saved to {output_path}")
    else:
        print("[SCOUT] No repositories found.")


def _cmd_extract(args, config):
    """Run extract command."""
    extractor = Extractor(config)
    skill_content = extractor.extract(args.repo, args.name)

    if skill_content:
        output = args.output or f"~/.clp/workspace/pending/{args.name or args.repo.split('/')[-1]}/SKILL.md"
        output_path = Path(output).expanduser()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(skill_content)
        print(f"[EXTRACT] Skill saved to {output_path}")
    else:
        print("[EXTRACT] Failed to extract skill.")


def _cmd_score(args, config):
    """Run score command."""
    scorer = Scorer(config.get("score_min_pass", 70))
    skill_data = scorer.load_skill(args.skill)

    if skill_data:
        result = scorer.score(skill_data)
        print(f"[SCORE] {result['score']}/100 ({result['decision']})")
        for check in result['checks']:
            print(f"  {check}")
    else:
        print("[SCORE] Failed to load skill.")


def _cmd_publish(args, config, plugin):
    """Run publish command."""
    publisher = Publisher(plugin, config)
    success = publisher.publish(args.skill, args.name, args.category)
    if success:
        print("[PUBLISH] Skill published successfully.")
    else:
        print("[PUBLISH] Failed to publish skill.")


def _cmd_dashboard(args, config):
    """Run dashboard command."""
    dashboard = Dashboard(config)
    result = dashboard.generate(generate_html=args.html or True)

    print(f"[DASHBOARD] Pending: {result['pending']}, Approved: {result['approved']}, Rejected: {result['rejected']}")
    print(f"[DASHBOARD] HTML: {result.get('html_path', 'N/A')}")
    print(f"[DASHBOARD] MD: {result.get('md_path', 'N/A')}")

    if args.serve:
        import http.server
        import threading
        port = config.get("dashboard_port", 8080)
        reports_dir = Path(config.get("reports_dir", "~/.clp/reports")).expanduser()

        handler = http.server.SimpleHTTPRequestHandler
        server = http.server.HTTPServer(("0.0.0.0", port), handler)
        server.directory = str(reports_dir)

        print(f"[DASHBOARD] Serving on http://0.0.0.0:{port}")
        print(f"[DASHBOARD] Open http://localhost:{port}/review-dashboard.html")
        server.serve_forever()


def _cmd_track(args, config):
    """Run track command."""
    tracker = Tracker(config)

    if args.register:
        name, repo = args.register.split(":", 1)
        tracker.register_skill(name, repo)
        print(f"[TRACK] Registered {name} -> {repo}")
    elif args.check:
        results = tracker.check_all()
        pending = tracker.get_pending()
        if pending:
            print(f"[TRACK] {len(pending)} skill(s) with updates:")
            for p in pending:
                print(f"  - {p['name']}: {p['commits']} new commit(s)")
        else:
            print("[TRACK] No updates found.")


def _cmd_pipeline(args, config, plugin):
    """Run full pipeline."""
    print("[PIPELINE] Starting full pipeline...")

    # Step 1: Scout
    print("[PIPELINE] Step 1: Scouting...")
    scout = Scout(config)
    keywords = args.keywords or config.get("scout_keywords", "agents,ai,automation")
    keywords = [k.strip() for k in keywords.split(",")]
    results = scout.search_trending(keywords, args.max_results)
    print(f"[PIPELINE] Found {len(results)} repositories")

    # Step 2: Extract & Score
    print("[PIPELINE] Step 2: Extracting & Scoring...")
    extractor = Extractor(config)
    scorer = Scorer(config.get("score_min_pass", 70))
    workspace = Path(config.get("workspace_dir", "~/.clp/workspace")).expanduser()
    pending_dir = workspace / "pending"

    for repo in results:
        full_name = repo["full_name"]
        print(f"[PIPELINE] Processing {full_name}...")

        skill_content = extractor.extract(full_name)
        if not skill_content:
            print(f"[PIPELINE]  Skip {full_name} (no content)")
            continue

        # Save to pending
        skill_name = repo["name"].lower().replace(" ", "-")
        skill_path = pending_dir / skill_name / "SKILL.md"
        skill_path.parent.mkdir(parents=True, exist_ok=True)
        skill_path.write_text(skill_content)

        # Score
        skill_data = scorer.load_skill(str(skill_path))
        if skill_data:
            result = scorer.score(skill_data)
            print(f"[PIPELINE]  {skill_name}: {result['score']}/100 ({result['decision']})")

    # Step 3: Dashboard
    print("[PIPELINE] Step 3: Generating dashboard...")
    dashboard = Dashboard(config)
    dashboard.generate()

    print("[PIPELINE] Pipeline complete.")


if __name__ == "__main__":
    main()
