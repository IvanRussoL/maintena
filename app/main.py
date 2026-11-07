"""Applicazione FastAPI di Maintena: rotte per reparti e macchinari."""

from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.database import get_db
from app.models import Reparto, Macchinario, Guasto
from app.schemas import RepartoLettura, RepartoCreazione, MacchinarioCreazione, MacchinarioLettura, GuastoCreazione, GuastoLettura

app = FastAPI(title="Maintena")


@app.get("/")
def stato():
    """Controlla che l'applicazione sia attiva."""
    return {"applicazione": "Maintena", "stato": "attiva"}


# ------------------------------------------------------------------
# Reparti
# ------------------------------------------------------------------

@app.get("/reparti", response_model=list[RepartoLettura])
def lista_reparti(db: Session = Depends(get_db)):
    """Restituisce tutti i reparti."""
    return db.scalars(select(Reparto)).all()


@app.get("/reparti/{reparto_id}", response_model=RepartoLettura)
def leggi_reparto(reparto_id: int, db: Session = Depends(get_db)):
    """Restituisce un reparto dato il suo id.

    Risponde 404 se il reparto non esiste.
    """
    reparto = db.get(Reparto, reparto_id)
    if reparto is None:
        raise HTTPException(status_code=404, detail="Reparto non trovato")
    return reparto


@app.post("/reparti", response_model=RepartoLettura, status_code=201)
def crea_reparto(dati: RepartoCreazione, db: Session = Depends(get_db)):
    """Crea un nuovo reparto.

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


# ------------------------------------------------------------------
# Macchinari
# ------------------------------------------------------------------

@app.post("/macchinari", response_model=MacchinarioLettura, status_code=201)
def crea_macchinario(dati: MacchinarioCreazione, db: Session = Depends(get_db)):
    """Crea un nuovo macchinario in un reparto esistente.

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


@app.get("/macchinari", response_model=list[MacchinarioLettura])
def elenca_macchinari(reparto_id: int | None = None, db: Session = Depends(get_db)):
    """Restituisce i macchinari, filtrati per reparto se è indicato `reparto_id`.

    Un reparto senza macchinari (o inesistente) restituisce una lista vuota, non 404.
    """
    query = select(Macchinario)
    if reparto_id is not None:
        query = query.where(Macchinario.reparto_id == reparto_id)
    return db.scalars(query).all()


@app.get("/macchinari/{macchinario_id}", response_model=MacchinarioLettura)
def leggi_macchinario(macchinario_id: int, db: Session = Depends(get_db)):
    """Restituisce un macchinario dato il suo id.

    Risponde 404 se il macchinario non esiste.
    """
    macchinario = db.get(Macchinario, macchinario_id)
    if macchinario is None:
        raise HTTPException(status_code=404, detail="Macchinario non trovato")
    return macchinario

# ------------------------------------------------------------------
# Guasto
# ------------------------------------------------------------------

@app.post("/guasti", response_model=GuastoLettura, status_code=201)
def crea_guasto(dati: GuastoCreazione, db: Session = Depends(get_db)):
    """Segnala un nuovo guasto su un macchinario esistente.

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

@app.get("/guasti", response_model=list[GuastoLettura])
def elenca_guasti(macchinario_id: int | None = None, db: Session = Depends(get_db)):
    """Restituisce i guasti, filtrati per macchinario se è indicato `macchinario_id`.

    Un macchinario senza guasti (o inesistente) restituisce una lista vuota, non 404.
    """
    query = select(Guasto)
    if macchinario_id is not None:
        query = query.where(Guasto.macchinario_id == macchinario_id)
    return db.scalars(query).all()