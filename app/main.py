"""Applicazione FastAPI di Maintena: crea l'app e aggancia i router."""
from fastapi import FastAPI


from app.routers import (
    reparti, macchinari, guasti, tecnici, ordini_lavoro
)

app = FastAPI(title="Maintena")


@app.get("/")
def stato():
    """
    Controlla che l'applicazione sia attiva.
    """
    return {"applicazione": "Maintena", "stato": "attiva"}


# ------------------------------------------------------------------
# Reparti
# ------------------------------------------------------------------

app.include_router(reparti.router)

# ------------------------------------------------------------------
# Macchinari
# ------------------------------------------------------------------

app.include_router(macchinari.router)

# ------------------------------------------------------------------
# Guasto
# ------------------------------------------------------------------

app.include_router(guasti.router)

# ------------------------------------------------------------------
# Tecnico
# ------------------------------------------------------------------

app.include_router(tecnici.router)

# ------------------------------------------------------------------
# Ordine-Lavoro
# ------------------------------------------------------------------

app.include_router(ordini_lavoro.router)