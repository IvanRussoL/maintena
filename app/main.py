from fastapi import FastAPI, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Reparto
from app.schemas import RepartoLettura

app = FastAPI(title="Maintena")

@app.get("/")
def stato():
    return {"applicazione": "Maintena", "stato": "attiva"}

@app.get("/reparti", response_model=list[RepartoLettura])
def lista_reparti(db: Session = Depends(get_db)):
    return db.scalars(select(Reparto)).all()