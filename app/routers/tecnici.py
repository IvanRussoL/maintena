from fastapi import APIRouter, Depends, HTTPException

from app.models import Tecnico
from app.schemas import TecnicoCreazione, TecnicoLettura
from app.database import get_db

from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

router = APIRouter(prefix="/tecnici", tags=["tecnici"])

@router.post("", response_model=TecnicoLettura, status_code=201)
def crea_tecnico(dati: TecnicoCreazione, db: Session = Depends(get_db)):
    """
    Crea un nuovo tecnico.
    
    Risponde 409 se esiste già un tecnico con lo stesso codice.
    """
    tecnico = Tecnico(**dati.model_dump())
    db.add(tecnico)
    try:
        db.commit()
    except IntegrityError as e:
        # annulliamo la transazione fallita prima di rispondere.
        db.rollback()
        # L'unicità del codice la controlla il database (vincolo UNIQUE):
        if e.orig.sqlstate == "23505":
            raise HTTPException(status_code=409, detail="Esiste già un tecnico con questo codice")
        # Ogni altro errore (es. 23514, specializzazione non valida) viene rilanciato.
        raise 
    db.refresh(tecnico)
    return tecnico

@router.get("", response_model=list[TecnicoLettura])
def lista_tecnici(attivo: bool | None = None, db: Session = Depends(get_db)):
    """
    Restituisce i tecnici; se 'attivo' è indicato, solo quelli con quello stato.
    """
    q = select(Tecnico)
    if attivo is not None:
        q = q.where(Tecnico.attivo == attivo)
    return db.scalars(q).all()