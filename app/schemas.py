from pydantic import BaseModel, ConfigDict
from typing import Literal

class RepartoCreazione(BaseModel):
    nome: str
    descrizione: str | None = None


class RepartoLettura(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    descrizione: str | None

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

