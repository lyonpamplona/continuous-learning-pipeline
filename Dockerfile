FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias do sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copiar arquivos do projeto
COPY pyproject.toml ./
COPY README.md ./
COPY LICENSE ./

# Instalar dependencias Python
RUN pip install --no-cache-dir -e .

# Copiar codigo fonte
COPY clp/ ./clp/

# Criar diretorios de trabalho
RUN mkdir -p /clp/skills /clp/workspace /clp/reports /clp/data

# Variaveis de ambiente
ENV CLP_SKILLS_DIR=/clp/skills \
    CLP_WORKSPACE_DIR=/clp/workspace \
    CLP_REPORTS_DIR=/clp/reports \
    CLP_DATA_DIR=/clp/data \
    CLP_PLUGIN_TYPE=file

# Expor porta do dashboard
EXPOSE 8080

# Comando padrao
ENTRYPOINT ["clp"]
CMD ["--help"]
