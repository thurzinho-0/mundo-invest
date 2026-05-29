import os
import pytest
import tempfile
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

# --- Banco de teste em arquivo temporário ---
temp_db = tempfile.NamedTemporaryFile(suffix=".db").name
TEST_DB_URL = f"sqlite:///{temp_db}"
os.environ["DATABASE_URL"] = TEST_DB_URL

from app.db.database import Base, get_db
from app.models import cliente, evento
from app.main import app

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
    # Cria tabelas antes de cada teste
    Base.metadata.drop_all(bind=engine_test)
    Base.metadata.create_all(bind=engine_test)
    yield
    Base.metadata.drop_all(bind=engine_test)

@pytest.fixture
def client(reset_db):
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield 
    app.dependency_overrides.clear()
