from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError


from app.database import get_db
from app.models import Reparto
from app.schemas import RepartoLettura, RepartoCreazione

app = FastAPI(title="Maintena")

@app.get("/")
def stato():
    return {"applicazione": "Maintena", "stato": "attiva"}

@app.get("/reparti", response_model=list[RepartoLettura])
def lista_reparti(db: Session = Depends(get_db)):
    return db.scalars(select(Reparto)).all()

@app.post("/reparti", response_model=RepartoLettura, status_code=201)
def crea_reparto(dati: RepartoCreazione, db: Session = Depends(get_db)):
    reparto = Reparto(nome=dati.nome, descrizione=dati.descrizione)
    db.add(reparto)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Esiste già un reparto con questo nome")
    db.refresh(reparto)
    return reparto