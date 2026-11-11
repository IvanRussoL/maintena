from fastapi import APIRouter, Depends, HTTPException

from app.models import Reparto
from app.schemas import RepartoCreazione, RepartoLettura
from app.database import get_db

from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

router = APIRouter(prefix="/reparti", tags=["reparti"])

@router.get("", response_model=list[RepartoLettura])
def lista_reparti(db: Session = Depends(get_db)):
    """
    Restituisce tutti i reparti.
    """
    return db.scalars(select(Reparto)).all()


@router.get("/{reparto_id}", response_model=RepartoLettura)
def leggi_reparto(reparto_id: int, db: Session = Depends(get_db)):
    """
    Restituisce un reparto dato il suo id.

    Risponde 404 se il reparto non esiste.
    """
    reparto = db.get(Reparto, reparto_id)
    if reparto is None:
        raise HTTPException(status_code=404, detail="Reparto non trovato")
    return reparto


@router.post("", response_model=RepartoLettura, status_code=201)
def crea_reparto(dati: RepartoCreazione, db: Session = Depends(get_db)):
    """
    Crea un nuovo reparto.

    Risponde 409 se esiste già un reparto con lo stesso nome.
    """
    reparto = Reparto(nome=dati.nome, descrizione=dati.descrizione)
    db.add(reparto)
    try:
        db.commit()
    except IntegrityError:
        # L'unicità del nome la controlla il database (vincolo UNIQUE):
        # annulliamo la transazione fallita prima di rispondere.
        db.rollback()
        raise HTTPException(status_code=409, detail="Esiste già un reparto con questo nome")
    db.refresh(reparto)  # ricarica id e valori predefiniti assegnati dal database
    return reparto