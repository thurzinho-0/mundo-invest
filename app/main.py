# =============================================================================
# MUNDO INVEST — Ponto de entrada principal da aplicação
# =============================================================================
# Este arquivo inicializa o FastAPI, registra os roteadores e configura
# o banco de dados na primeira execução.
# =============================================================================

from fastapi import FastAPI
from contextlib import asynccontextmanager

from app.db.database import init_db
from app.api import clientes, webhooks


# ---------------------------------------------------------------------------
# Lifespan: roda antes de aceitar requisições e ao encerrar a aplicação
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Cria as tabelas no SQLite (se ainda não existirem)
    init_db()
    yield
    # Aqui entraria lógica de shutdown (fechar conexões, etc.)


# ---------------------------------------------------------------------------
# Instância principal do FastAPI
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Mundo Invest — Client Management API",
    description=(
        "API interna para gestão de clientes e integração simulada com o Pipefy. "
        "Gerencia patrimônios, prioridades e mapeamento de cards via GraphQL."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# Registro dos roteadores (cada um cuida de seu domínio)
# ---------------------------------------------------------------------------
app.include_router(clientes.router, prefix="/clientes", tags=["Clientes"])
app.include_router(webhooks.router, prefix="/webhooks", tags=["Webhooks"])


# ---------------------------------------------------------------------------
# Health check — útil para monitoramento e testes de infraestrutura
# ---------------------------------------------------------------------------
@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok", "service": "mundo-invest-api"}
