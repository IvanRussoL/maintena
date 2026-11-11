from fastapi import APIRouter, Depends, HTTPException

from app.models import Guasto, Macchinario, OrdineLavoro
from app.schemas import GuastoCreazione, GuastoLettura, GuastoAggiornamentoStato
from app.database import get_db

from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from datetime import datetime, timezone

router = APIRouter(prefix="/guasti", tags=["guasti"])

@router.post("", response_model=GuastoLettura, status_code=201)
def crea_guasto(dati: GuastoCreazione, db: Session = Depends(get_db)):
    """
    Segnala un nuovo guasto su un macchinario esistente.

    Lo stato parte da "aperto" e la data di segnalazione la scrive il database.
    Risponde 404 se il macchinario non esiste.
    """
    # Controllo esplicito: dà un messaggio chiaro senza tentare l'INSERT.
    if db.get(Macchinario, dati.macchinario_id) is None:
        raise HTTPException(status_code=404, detail="Macchinario non trovato")
    guasto = Guasto(**dati.model_dump())
    db.add(guasto)
    try:
        db.commit()
    except IntegrityError as e:
        db.rollback()
        # SQLSTATE 23503 = chiave esterna violata: il macchinario è sparito
        # tra il controllo sopra e il commit.
        if e.orig.sqlstate == "23503":
            raise HTTPException(status_code=404, detail="Macchinario non trovato")
        # Ogni altro errore (es. 23514, priorità non valida) viene rilanciato
        # invece di restituire un guasto mai salvato. Validazione in fase 2.
        raise
    db.refresh(guasto)
    return guasto

@router.get("", response_model=list[GuastoLettura])
def elenca_guasti(macchinario_id: int | None = None, db: Session = Depends(get_db)):
    """
    Restituisce i guasti, filtrati per macchinario se è indicato `macchinario_id`.

    Un macchinario senza guasti (o inesistente) restituisce una lista vuota, non 404.
    """
    query = select(Guasto)
    if macchinario_id is not None:
        query = query.where(Guasto.macchinario_id == macchinario_id)
    return db.scalars(query).all()

@router.patch("/{guasto_id}", response_model=GuastoLettura)
def aggiorna_stato_guasto(guasto_id: int, dati: GuastoAggiornamentoStato, db: Session = Depends(get_db)):
    """
    Aggiorna lo stato di un guasto; non si può chiudere se ha ordini di lavoro aperti.
    """
    guasto = db.get(Guasto, guasto_id)
    if guasto is None:
        raise HTTPException(status_code=404, detail="Guasto non trovato")
    if dati.stato in ("risolto", "annullato"):
        q = select(OrdineLavoro).where(
            OrdineLavoro.guasto_id == guasto_id,
            OrdineLavoro.stato.not_in(("completato", "annullato")),
        )
        if db.scalars(q).first() is not None:
            raise HTTPException(status_code=409, detail="Il guasto ha ordini di lavoro aperti")
        guasto.data_chiusura = datetime.now(timezone.utc)

    guasto.stato = dati.stato
    try:
        db.commit()
    except IntegrityError as e:
        db.rollback()
        if e.orig.sqlstate == "23514":
            raise HTTPException(status_code=422, detail="Stato non valido")
        raise
    db.refresh(guasto)
    return guasto