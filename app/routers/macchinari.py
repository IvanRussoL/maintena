from fastapi import APIRouter, Depends, HTTPException

from app.models import Macchinario, Reparto
from app.schemas import MacchinarioCreazione, MacchinarioLettura
from app.database import get_db

from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

router = APIRouter(prefix="/macchinari", tags=["macchinari"])

@router.post("", response_model=MacchinarioLettura, status_code=201)
def crea_macchinario(dati: MacchinarioCreazione, db: Session = Depends(get_db)):
    """
    Crea un nuovo macchinario in un reparto esistente.

    Risponde 404 se il reparto non esiste e 409 se la matricola è già usata.
    """
    # Controllo esplicito: dà un messaggio chiaro senza tentare l'INSERT.
    if db.get(Reparto, dati.reparto_id) is None:
        raise HTTPException(status_code=404, detail="Reparto non trovato")
    macchinario = Macchinario(**dati.model_dump())
    db.add(macchinario)
    try:
        db.commit()
    except IntegrityError as e:
        db.rollback()
        # SQLSTATE 23503 = chiave esterna violata: il reparto è sparito
        # tra il controllo sopra e il commit. Altrimenti è la matricola doppia.
        if e.orig.sqlstate == "23503":
            raise HTTPException(status_code=404, detail="Reparto non trovato")
        raise HTTPException(status_code=409, detail="Esiste già un macchinario con questa matricola")
    db.refresh(macchinario)
    return macchinario


@router.get("", response_model=list[MacchinarioLettura])
def elenca_macchinari(reparto_id: int | None = None, db: Session = Depends(get_db)):
    """
    Restituisce i macchinari, filtrati per reparto se è indicato `reparto_id`.

    Un reparto senza macchinari (o inesistente) restituisce una lista vuota, non 404.
    """
    query = select(Macchinario)
    if reparto_id is not None:
        query = query.where(Macchinario.reparto_id == reparto_id)
    return db.scalars(query).all()


@router.get("/{macchinario_id}", response_model=MacchinarioLettura)
def leggi_macchinario(macchinario_id: int, db: Session = Depends(get_db)):
    """
    Restituisce un macchinario dato il suo id.

    Risponde 404 se il macchinario non esiste.
    """
    macchinario = db.get(Macchinario, macchinario_id)
    if macchinario is None:
        raise HTTPException(status_code=404, detail="Macchinario non trovato")
    return macchinario