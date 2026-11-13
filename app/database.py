import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

load_dotenv()
# echo=True stampa le query SQL: utile in sviluppo
engine = create_engine(os.getenv("DATABASE_URL"), echo=True)


class Base(DeclarativeBase):
    """Classe base dei modelli ORM."""
    pass


SessionLocal = sessionmaker(bind=engine)


def get_db():
    """Dipendenza FastAPI: una sessione per richiesta, chiusa sempre alla fine."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()