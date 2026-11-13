# tests/conftest.py
# Configurazione condivisa dei test: pytest legge questo file da solo
# e rende disponibili le fixture a tutti i file test_*.py della cartella.
import os
import pytest
from dotenv import load_dotenv
from fastapi.testclient import TestClient   # finto client HTTP: chiama le rotte senza avviare il server
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app                    # l'applicazione FastAPI da testare
from app.database import Base, get_db       # Base: elenco delle tabelle; get_db: la dipendenza da sostituire
from app import models  # ci serve solo a "registrare" le tabelle in Base.metadata

load_dotenv()                               # legge .env, dove c'è TEST_DATABASE_URL
# Secondo motore, separato da quello dell'app: punta al database maintena_test.
engine_test = create_engine(os.getenv("TEST_DATABASE_URL"))
# Fabbrica di sessioni legate al database di test.
SessionTest = sessionmaker(bind=engine_test)


@pytest.fixture
def db():
    """Database pulito per ogni test: crea le tabelle, presta una sessione, poi cancella tutto."""
    Base.metadata.create_all(bind=engine_test)   # prima del test: tabelle vuote
    sessione = SessionTest()
    try:
        yield sessione                           # qui gira il test
    finally:
        sessione.close()                         # dopo il test, anche se è fallito
        Base.metadata.drop_all(bind=engine_test) # tabelle eliminate: il test dopo riparte da zero


@pytest.fixture
def client(db):
    """Client HTTP che fa usare alle rotte il database di test al posto di quello vero."""
    def get_db_test():
        yield db                                 # le rotte ricevono la sessione di test
    # "Quando una rotta chiede get_db, dalle get_db_test."
    app.dependency_overrides[get_db] = get_db_test
    with TestClient(app) as c:
        yield c                                  # qui gira il test
    app.dependency_overrides.clear()             # ripristina l'app com'era