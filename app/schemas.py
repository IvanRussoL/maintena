from pydantic import BaseModel, ConfigDict
from typing import Literal
from datetime import datetime

# ----------------------------------------------------------
# Reparto
# ----------------------------------------------------------
class RepartoCreazione(BaseModel):
    nome: str
    descrizione: str | None = None


class RepartoLettura(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    descrizione: str | None

# ----------------------------------------------------------
# Macchinario
# ----------------------------------------------------------    

class MacchinarioLettura(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    matricola: str
    nome: str
    reparto_id: int
    modello: str | None
    stato: Literal["attivo","fermo","dismesso"]
    descrizione: str | None

class MacchinarioCreazione(BaseModel):
    matricola: str
    nome: str
    reparto_id: int
    modello: str | None = None
    stato: Literal["attivo","fermo","dismesso"] = "attivo"
    descrizione: str | None = None

# ----------------------------------------------------------
# Guasto
# ----------------------------------------------------------

class GuastoLettura(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    macchinario_id: int
    descrizione: str
    data_segnalazione: datetime
    priorita: str
    stato: str
    data_chiusura: datetime | None 
    segnalato_da: str


class GuastoCreazione(BaseModel):
    macchinario_id: int
    descrizione: str
    priorita: str
    segnalato_da: str

# ----------------------------------------------------------
# Guasto
# ----------------------------------------------------------

class TecnicoCreazione(BaseModel):
    codice_dipendente: str
    nome: str
    cognome: str
    specializzazione: str | None = None

class TecnicoLettura(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    codice_dipendente: str
    nome: str
    cognome: str
    specializzazione: str | None
    attivo: bool 