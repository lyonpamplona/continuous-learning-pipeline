# Documentação Técnica — Continuous Learning Pipeline

## Arquitetura do Sistema

```
┌─────────────────────────────────────────────────────────┐
│                    Continuous Learning Pipeline          │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐         │
│  │  SCOUT   │───▶│ EXTRACT  │───▶│  SCORE   │         │
│  │          │    │          │    │          │         │
│  └──────────┘    └──────────┘    └──────────┘         │
│       │               │               │                │
│       ▼               ▼               ▼                │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐         │
│  │ TRACKER  │◀───│PUBLISHER│◀───│DASHBOARD │         │
│  └──────────┘    └──────────┘    └──────────┘         │
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │              Plugin System                       │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐      │  │
│  │  │   FILE   │  │  HERMES  │  │  CUSTOM  │      │  │
│  │  └──────────┘  └──────────┘  └──────────┘      │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

## Módulos

### 1. Scout (`clp.scout`)
Descobre repositórios relevantes no GitHub usando a API de busca.

**Funções principais:**
- `search_trending()`: Busca repositórios por palavras-chave
- `get_repo_details()`: Obtém detalhes de um repositório
- `save_results()`: Salva resultados em JSON

### 2. Extractor (`clp.extractor`)
Analisa repositórios e gera arquivos SKILL.md.

**Funções principais:**
- `fetch_readme()`: Busca conteúdo do README
- `analyze_readme()`: Analisa README para informações de workflow
- `identify_workflows()`: Identifica workflows reutilizáveis
- `generate_skill_md()`: Gera conteúdo SKILL.md
- `extract()`: Pipeline completo de extração

### 3. Scorer (`clp.scorer`)
Avalia qualidade de SKILL.md com 10 critérios objetivos.

**Critérios:**
1. Frontmatter completo (15 pts)
2. Description ≤ 60 chars (10 pts)
3. Termina com ponto (5 pts)
4. Seções essenciais (20 pts)
5. Procedure ≥ 3 passos (15 pts)
6. Pitfalls ≥ 2 itens (10 pts)
7. Sem palavras de marketing (5 pts)
8. Size ≤ max_size (5 pts)
9. Author credita humano (5 pts)
10. Name válido (5 pts)

### 4. Publisher (`clp.publisher`)
Publica skills aprovadas no framework de agente.

**Funções principais:**
- `publish()`: Publica uma skill
- `publish_from_workspace()`: Publica todas aprovadas
- `list_published()`: Lista skills publicadas

### 5. Tracker (`clp.tracker`)
Monitora atualizações de repositórios fonte.

**Funções principais:**
- `register_skill()`: Registra skill para tracking
- `check_updates()`: Verifica atualizações
- `check_all()`: Verifica todas registradas
- `get_pending()`: Obtém skills com atualizações pendentes

### 6. Dashboard (`clp.dashboard`)
Gera dashboard web para revisão de skills.

**Funções principais:**
- `generate()`: Gera dashboard HTML/MD
- `_generate_html()`: Gera HTML com estilo CLI/IDE
- `_generate_markdown()`: Gera Markdown

### 7. CLI (`clp.cli`)
Interface de linha de comando.

**Comandos:**
- `clp scout`: Descobrir repositórios
- `clp extract`: Extrair skill de repositório
- `clp score`: Pontuar SKILL.md
- `clp publish`: Publicar skill
- `clp dashboard`: Gerar dashboard
- `clp track`: Rastrear atualizações
- `clp pipeline`: Executar pipeline completo

### 8. Config (`clp.config`)
Gerenciamento de configuração.

**Configurações disponíveis:**
- `github_token`: Token da API GitHub
- `scout_keywords`: Palavras-chave para busca
- `score_min_pass`: Pontuação mínima para aprovação
- `dashboard_port`: Porta do servidor dashboard
- `skills_dir`: Diretório de skills
- `workspace_dir`: Diretório de workspace
- `reports_dir`: Diretório de relatórios
- `data_dir`: Diretório de dados

### 9. Plugins (`clp.plugins`)
Sistema de plugins para integração com frameworks de agentes.

**Plugins disponíveis:**
- `FilePlugin`: Modo standalone, salva skills em disco
- `HermesPlugin`: Integração nativa com Hermes Agent
- `get_plugin()`: Factory para obter plugin apropriado

## Fluxos do Sistema

### Fluxo 1: Scout → Extract → Score → Publish
```
1. Scout descobre repositórios no GitHub
2. Extractor analisa README e gera SKILL.md
3. Scorer avalia qualidade com 10 critérios
4. Publisher publica skills aprovadas
```

### Fluxo 2: Tracker → Extract → Score → Publish
```
1. Tracker monitora repositórios fonte
2. Detecta atualizações (novos commits)
3. Extractor re-extrai SKILL.md atualizado
4. Scorer re-avalia qualidade
5. Publisher atualiza skill publicada
```

### Fluxo 3: Dashboard → Review → Approve/Reject
```
1. Dashboard gera visão geral de skills pendentes
2. Usuário revisa skills no dashboard
3. Usuário aprova ou rejeita skills
4. Skills aprovadas são publicadas
5. Skills rejeitadas são arquivadas
```

## Configuração

### Variáveis de Ambiente
```bash
export GITHUB_TOKEN=seu_token_aqui
export CLP_SKILLS_DIR=~/.clp/skills
export CLP_WORKSPACE_DIR=~/.clp/workspace
export CLP_PLUGIN_TYPE=file
export DASHBOARD_PORT=8080
```

### Arquivo de Configuração (YAML)
```yaml
github_token: seu_token_aqui
scout_keywords: agents,ai,automation,skills,workflows
scout_max_results: 10
score_min_pass: 70
dashboard_port: 8080
skills_dir: ~/.clp/skills
workspace_dir: ~/.clp/workspace
reports_dir: ~/.clp/reports
data_dir: ~/.clp/data
plugin_type: file
```

## Dependências

### Python
- `pyyaml>=6.0`: Parse de YAML
- `requests>=2.31.0`: Requisições HTTP
- `python-dateutil>=2.8.0`: Manipulação de datas

### Opcionais
- `pytest>=7.0`: Testes unitários
- `pytest-cov>=4.0`: Cobertura de testes
- `black>=23.0`: Formatação de código
- `ruff>=0.1.0`: Linting

## Instalação

### Standalone
```bash
pip install continuous-learning-pipeline
```

### Com Hermes Agent
```bash
pip install continuous-learning-pipeline[hermes]
```

### Docker
```bash
docker-compose up -d
```

## Uso

### Comando Scout
```bash
clp scout --keywords "agents,ai" --max-results 10
```

### Comando Extract
```bash
clp extract --repo langchain-ai/langchain --name langchain
```

### Comando Score
```bash
clp score --skill ~/.clp/workspace/pending/langchain/SKILL.md
```

### Comando Publish
```bash
clp publish --skill ~/.clp/workspace/approved/langchain/SKILL.md
```

### Comando Dashboard
```bash
clp dashboard --html --serve
```

### Comando Track
```bash
clp track --register "langchain:langchain-ai/langchain"
clp track --check
```

### Comando Pipeline
```bash
clp pipeline --keywords "agents,ai" --max-results 5
```

## Estrutura de Diretórios

```
~/.clp/
├── skills/           # Skills publicadas
├── workspace/        # Workspace do pipeline
│   ├── pending/      # Skills aguardando revisão
│   ├── approved/     # Skills aprovadas
│   ├── rejected/     # Skills rejeitadas
│   └── published/    # Skills publicadas
├── reports/          # Relatórios e dashboards
└── data/             # Dados do pipeline
```

## Licença

MIT License - veja [LICENSE](../LICENSE) para detalhes.

## Autor

lyon christopher - [Hermes Agent](https://hermes-agent.nousresearch.com)