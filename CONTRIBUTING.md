# Contribuindo para o CLP

Obrigado por contribuir! Siga estas diretrizes.

## Como Contribuir

### 1. Fork o repositório
```bash
git clone https://github.com/seu-usuario/continuous-learning-pipeline.git
cd continuous-learning-pipeline
```

### 2. Criar branch
```bash
git checkout -b feature/sua-feature
```

### 3. Fazer alterações
- Siga o estilo de código existente
- Adicione testes para novas funcionalidades
- Atualize a documentação

### 4. Testar
```bash
pip install -e ".[dev]"
pytest
```

### 5. Commit
```bash
git commit -m "feat: descricao da feature"
```

### 6. Pull Request
- Descreva as mudanças
- Adicione screenshots se relevante
- Aguarde review

## Estilo de Código

- Python 3.10+
- Black para formatação
- Ruff para linting
- Docstrings em português

## Estrutura de Commits

- `feat:` nova funcionalidade
- `fix:` correção de bug
- `docs:` documentação
- `refactor:` refatoração
- `test:` testes
- `chore:` manutenção
