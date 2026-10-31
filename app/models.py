from sqlalchemy import String, Text, ForeignKey, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base

class Reparto(Base):
    __tablename__ = "reparto"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(100), unique=True)
    descrizione: Mapped[str | None] = mapped_column(Text)


class Macchinario(Base):
    __tablename__ = "macchinario"
    __table_args__ = (
        CheckConstraint("stato IN ('attivo', 'fermo', 'dismesso')", name="ck_macchinario_stato"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    matricola: Mapped[str] = mapped_column(String(50), unique=True)
    nome: Mapped[str] = mapped_column(String(100))
    reparto_id: Mapped[int] = mapped_column(ForeignKey("reparto.id", ondelete="RESTRICT"))
    modello: Mapped[str | None] = mapped_column(String(100))
    stato: Mapped[str] = mapped_column(String(20), server_default="attivo")
    descrizione: Mapped[str | None] = mapped_column(Text)


class Tecnico(Base):
    __tablename__ = "tecnico"
    __table_args__ = (
        CheckConstraint("specializzazione IN ('meccanica', 'elettrica', 'idraulica', 'elettronica')", name="ck_tecnico_specializzazione"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    codice_dipendente: Mapped[str] = mapped_column(String(50), unique=True)
    nome: Mapped[str] = mapped_column(String(100))
    cognome: Mapped[str] = mapped_column(String(100))
    specializzazione: Mapped[str | None] = mapped_column(String(20))
    attivo: Mapped[bool] = mapped_column(server_default="true")