from datetime import datetime
from sqlalchemy import String, Text, ForeignKey, CheckConstraint, DateTime, func
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


class Guasto(Base):
    __tablename__ = "guasto"
    __table_args__ = (
        CheckConstraint("priorita IN ('bassa', 'media', 'alta', 'critica')", name="ck_guasto_priorita"),
        CheckConstraint("stato IN ('aperto', 'in_lavorazione', 'risolto', 'annullato')", name="ck_guasto_stato"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    macchinario_id: Mapped[int] = mapped_column(ForeignKey("macchinario.id", ondelete="RESTRICT"))
    descrizione: Mapped[str] = mapped_column(Text)
    data_segnalazione: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    priorita: Mapped[str] = mapped_column(String(20))
    stato: Mapped[str] = mapped_column(String(20), server_default="aperto")
    data_chiusura: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    segnalato_da: Mapped[str] = mapped_column(String(100))

class OrdineLavoro(Base):
    __tablename__ = "ordine_lavoro"
    __table_args__ = (
        CheckConstraint("stato IN ('da_assegnare', 'assegnato', 'in_corso', 'completato', 'annullato')", name="ck_ordine_lavoro_stato"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    macchinario_id: Mapped[int] = mapped_column(ForeignKey("macchinario.id", ondelete="RESTRICT"))
    guasto_id: Mapped[int | None] = mapped_column(ForeignKey("guasto.id", ondelete="RESTRICT"))
    tecnico_id: Mapped[int | None] = mapped_column(ForeignKey("tecnico.id", ondelete="RESTRICT"))
    descrizione: Mapped[str] = mapped_column(Text)
    stato: Mapped[str] = mapped_column(String(20), server_default="da_assegnare")
    data_creazione: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    data_pianificata: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    data_completamento: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    esito: Mapped[str | None] = mapped_column(Text)