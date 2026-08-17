# Continuous Learning Pipeline

Automated skill discovery and generation for AI agents.

## Overview

The Continuous Learning Pipeline (CLP) is an automated system that discovers, extracts, scores, and publishes Agent Skills from GitHub repositories. It runs as a standalone tool or integrates with AI agent frameworks like Hermes Agent.

## Features

- **Scout**: Discovers relevant repositories from GitHub Trending
- **Extract**: Analyzes repositories and generates SKILL.md files
- **Score**: Automated quality scoring with 10 objective criteria
- **Publish**: Publishes approved skills to your agent framework
- **Track**: Monitors existing skills for updates
- **Dashboard**: CLI/IDE-style web dashboard for review

## Quick Start

```bash
# Clone the repository
git clone https://github.com/lyonchristopher/continuous-learning-pipeline.git
cd continuous-learning-pipeline

# Install dependencies
pip install -e .

# Run the pipeline
clp scout
clp extract --repo langchain-ai/langchain
clp score --skill path/to/SKILL.md
clp publish --skill path/to/SKILL.md
```

## Installation

### Standalone

```bash
pip install continuous-learning-pipeline
```

### With Hermes Agent

```bash
pip install continuous-learning-pipeline[hermes]
```

### Docker

```bash
docker-compose up -d
```

## Architecture

```
[SCOUT] -> [EXTRACT] -> [SCORE] -> [REVIEW] -> [PUBLISH]
   ^                                              |
   +------------------- FEEDBACK LOOP -------------+
```

## Plugins

CLP supports multiple agent frameworks through plugins:

- **File Plugin**: Standalone mode, saves skills to disk
- **Hermes Plugin**: Native integration with Hermes Agent
- **Custom Plugin**: Template for building your own integration

## Configuration

Create a `.env` file:

```env
# GitHub API (optional, for higher rate limits)
GITHUB_TOKEN=your_token_here

# Dashboard
DASHBOARD_PORT=8080
DASHBOARD_HOST=0.0.0.0

# Scout
SCOUT_KEYWORDS=agents,ai,automation,skills,workflows
SCOUT_MAX_RESULTS=10

# Scoring
SCORE_MIN_PASS=70
```

## License

MIT License - see [LICENSE](LICENSE) for details.

## Contributing

See [CONTRIBUTING.md](docs/contributing.md) for guidelines.

## Author

lyon christopher - [Hermes Agent](https://hermes-agent.nousresearch.com)
