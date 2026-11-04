from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError


from app.database import get_db
from app.models import Reparto, Macchinario
from app.schemas import RepartoLettura, RepartoCreazione, MacchinarioCreazione, MacchinarioLettura

app = FastAPI(title="Maintena")

@app.get("/")
def stato():
    return {"applicazione": "Maintena", "stato": "attiva"}

###################################################################
# API reparti

@app.get("/reparti", response_model=list[RepartoLettura])
def lista_reparti(db: Session = Depends(get_db)):
    return db.scalars(select(Reparto)).all()

@app.get("/reparti/{reparto_id}", response_model=RepartoLettura)
def leggi_reparto(reparto_id: int, db: Session = Depends(get_db)):
    reparto = db.get(Reparto, reparto_id)
    if reparto is None:
        raise HTTPException(status_code=404, detail="Reparto non trovato")
    return reparto

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


##################################################################

#################################################################
# API macchinari

@app.post("/macchinari", response_model=MacchinarioLettura, status_code=201)
def crea_macchinario(dati: MacchinarioCreazione, db: Session = Depends(get_db)):
    if db.get(Reparto, dati.reparto_id) is None:
        raise HTTPException(status_code=404, detail="Reparto non trovato")
    macchinario = Macchinario(**dati.model_dump())
    db.add(macchinario)
    try:
        db.commit()
    except IntegrityError as e:
        db.rollback()
        codice = e.orig.sqlstate
        if codice == "23503":
            raise HTTPException(status_code=404, detail="Reparto non trovato")
        raise HTTPException(status_code=409, detail="Esiste già un macchinario con questa matricola")
    db.refresh(macchinario)
    return macchinario

@app.get("/macchinari", response_model=list[MacchinarioLettura])
def elenca_macchinari(reparto_id: int | None =  None, db: Session = Depends(get_db)):
    query = select(Macchinario)
    if reparto_id is not None:
        query = query.where(Macchinario.reparto_id == reparto_id)
    return db.scalars(query).all()