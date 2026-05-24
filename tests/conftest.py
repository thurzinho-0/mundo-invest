# =============================================================================
# MUNDO INVEST — conftest.py
# =============================================================================
# Configura o ambiente de testes ANTES de qualquer import da aplicação.
# Define a DATABASE_URL de teste para que database.py use o banco correto
# desde o início — inclusive quando o lifespan chama init_db().
# =============================================================================

import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Define a URL do banco ANTES dos imports da app (executa no load do conftest)
TEST_DB_URL = "sqlite:////tmp/mundo_invest_test.db"
os.environ["DATABASE_URL"] = TEST_DB_URL

# Agora podemos importar a app — ela lerá DATABASE_URL do ambiente
from app.db.database import Base, get_db  # noqa: E402
from app.models import cliente, evento    # noqa: E402, F401
from app.main import app                  # noqa: E402
from fastapi.testclient import TestClient # noqa: E402

engine_test = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine_test)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def reset_db():
    """Recria o schema para cada teste (isolamento)."""
    Base.metadata.drop_all(bind=engine_test)
    Base.metadata.create_all(bind=engine_test)
    yield
    Base.metadata.drop_all(bind=engine_test)


@pytest.fixture
def client(reset_db):
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
