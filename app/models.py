from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base

class Reparto(Base):
    __tablename__ = "reparto"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(100), unique=True)
    descrizione: Mapped[str | None] = mapped_column(Text)

    