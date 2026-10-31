from pydantic import BaseModel, ConfigDict

class RepartoLettura(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str

    