# =============================================================================
# MUNDO INVEST — Configuração do banco de dados (SQLite)
# =============================================================================
# Usa SQLAlchemy como ORM. O banco é SQLite por padrão, facilitando
# execução local sem dependências externas.
# Para produção, bastaria trocar a DATABASE_URL por uma string do PostgreSQL/RDS.
# =============================================================================

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

# ---------------------------------------------------------------------------
# URL do banco: lê da variável de ambiente ou usa SQLite local como fallback
# ---------------------------------------------------------------------------
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./mundo_invest.db")

# ---------------------------------------------------------------------------
# Engine: connect_args é necessário apenas para SQLite (evita erros de thread)
# ---------------------------------------------------------------------------
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)

# ---------------------------------------------------------------------------
# SessionLocal: fábrica de sessões — cada request recebe a sua própria
# ---------------------------------------------------------------------------
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# ---------------------------------------------------------------------------
# Base declarativa: todas as models herdam desta classe
# ---------------------------------------------------------------------------
class Base(DeclarativeBase):
    pass


# ---------------------------------------------------------------------------
# init_db: cria todas as tabelas mapeadas (chamada no startup da aplicação)
# ---------------------------------------------------------------------------
def init_db():
    # Importamos as models aqui para garantir que estejam registradas na Base
    from app.models import cliente, evento  # noqa: F401
    Base.metadata.create_all(bind=engine)


# ---------------------------------------------------------------------------
# get_db: gerador de sessão para injeção de dependência via FastAPI (Depends)
# ---------------------------------------------------------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
