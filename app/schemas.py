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

# ----------------------------------------------------------
# Ordine-Lavoro
# ----------------------------------------------------------

class OrdineLavoroCreazione(BaseModel):
    macchinario_id: int
    guasto_id: int | None = None
    tecnico_id: int | None = None
    descrizione: str
    data_pianificata: datetime | None = None

class OrdineLavoroLettura(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    macchinario_id: int
    guasto_id: int | None
    tecnico_id: int | None
    descrizione: str
    stato: str
    data_creazione: datetime
    data_pianificata: datetime | None
    data_completamento: datetime | None
    esito: str | None

class OrdineLavoroAggiornamentoStato(BaseModel):
    stato: str