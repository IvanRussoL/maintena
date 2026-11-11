from fastapi import APIRouter, Depends, HTTPException
from app.models import OrdineLavoro, Macchinario, Guasto, Tecnico
from app.schemas import OrdineLavoroCreazione, OrdineLavoroLettura, OrdineLavoroAggiornamentoStato
from app.database import get_db

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

router = APIRouter(prefix="/ordini-lavoro", tags=["ordini-lavoro"])

@router.post("", response_model=OrdineLavoroLettura, status_code=201)
def crea_ordine_lavoro(dati: OrdineLavoroCreazione, db: Session = Depends(get_db)):
    """
    Crea un nuovo ordine di lavoro.
    Se è indicato un tecnico, l'ordine nasce 'assegnato'; altrimenti 'da_assegnare'.
    """
    ordine = OrdineLavoro(**dati.model_dump())
    if ordine.tecnico_id is not None:
        ordine.stato = "assegnato"
    # Il macchinario è obbligatorio, va sempre cercato
    macchinario = db.get(Macchinario, ordine.macchinario_id)
    if macchinario is None:
        raise HTTPException(status_code=404, detail="Macchinario non trovato")
    # Il guasto è facoltativo, lo cerchiamo solo se è stato inviato
    if ordine.guasto_id is not None:
        guasto = db.get(Guasto, ordine.guasto_id)
        if guasto is None:
            raise HTTPException(status_code=404, detail="Guasto non trovato")
        if ordine.macchinario_id != guasto.macchinario_id:
            raise HTTPException(status_code=409, detail="Il guasto non corrisponde al macchinario")
    # Il tecnico è facoltativo, va cercato solo se inviato
    if ordine.tecnico_id is not None:
        tecnico = db.get(Tecnico, ordine.tecnico_id)
        if tecnico is None:
            raise HTTPException(status_code=404, detail="Tecnico non trovato")
    db.add(ordine)
    try:
        db.commit()
    except IntegrityError as e:
        db.rollback()
        # I controlli sopra coprono il caso normale. Questo blocco resta
        # come ultima difesa: se tra il db.get e il commit un'altra richiesta
        # elimina il macchinario, il guasto o il tecnico (race condition),
        # la FK fa fallire l'INSERT con SQLSTATE 23503 e rispondiamo 404
        # invece di un 500.
        if e.orig.sqlstate == "23503":
            raise HTTPException(status_code=404, detail="Macchinario, guasto o tecnico non trovato")
        # Ogni altro errore di integrità viene rilanciato: non dovrebbe
        # succedere, perché lo stato lo impostiamo noi.
        raise
    db.refresh(ordine)
    return ordine

@router.get("", response_model=list[OrdineLavoroLettura])
def elenca_ordini_lavoro(stato: str | None = None, db: Session = Depends(get_db)):
    """
    Restituisce gli ordini-lavoro; se stato è indicato, solo quelli con quello stato.
    """
    q = select(OrdineLavoro)
    if stato is not None:
        q = q.where(OrdineLavoro.stato == stato)
    return db.scalars(q).all()

@router.patch("/{ordine_id}", response_model=OrdineLavoroLettura)
def aggiorna_stato_ordine(ordine_id: int, dati: OrdineLavoroAggiornamentoStato, db: Session = Depends(get_db)):
    """
    Aggiorna lo stato di un ordine di lavoro.
    """
    ordine = db.get(OrdineLavoro, ordine_id)
    if ordine is None:
        raise HTTPException(status_code=404, detail="L'ordine non esiste")
    ordine.stato = dati.stato
    if ordine.stato == "completato":
        ordine.data_completamento = datetime.now(timezone.utc)
    try:
        db.commit()
    except IntegrityError as e:
        db.rollback()
        if e.orig.sqlstate == "23514":
            raise HTTPException(status_code=422, detail="Stato non valido")
        raise
    db.refresh(ordine)
    return ordine