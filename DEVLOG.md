# DEVLOG – Maintena

Diario delle decisioni di sviluppo: data, decisione, motivo, alternative scartate.

## 2026-10-28 – Schema dati a cinque tabelle

**Decisione:** il gestionale parte con `reparto`, `macchinario`, `guasto`, `tecnico`, `ordine_lavoro`.
**Motivo:** coprono il dominio minimo (dove sono le macchine, cosa si rompe, chi interviene). Lo stato del guasto è salvato e non calcolato dagli ordini, perché "risolto" è una decisione umana. Il tecnico non viene cancellato ma disattivato (`attivo`), per non perdere lo storico degli ordini.
**Alternative scartate:** tabelle per componenti e ruoli (non serve ancora); `tipo` correttiva/preventiva nell'ordine (si ricava da `guasto_id`); `reparto_id` nell'ordine (si ricava dal macchinario).

## 2026-10-28 – SQLAlchemy 2.0 come ORM

**Decisione:** accesso al database con SQLAlchemy 2.0.
**Motivo:** è lo strumento più diffuso in Python e tiene separati i modelli del database da quelli dell'API (Pydantic), come richiede l'architettura a strati. Si controlla sempre l'SQL generato.
**Alternative scartate:** SQLModel (unisce i due tipi di modello e nasconde di più); Django ORM (legato a Django); SQL scritto a mano (più istruttivo, ma meno usato nei progetti reali).

## 2026-10-28 – PostgreSQL 18 installato in nativo su Windows

**Decisione:** PostgreSQL 18.1 con l'installer ufficiale, database `maintena`.
**Motivo:** è la via più semplice per iniziare, senza strati aggiuntivi.
**Alternative scartate:** WSL2 e Docker (Docker arriverà con la fase di produzione).

## 2026-10-30 – Creazione del repository

**Decisione:** repository Git in `maintena_code/`, ambiente virtuale Python (3.13) in `maintena_code/venv`, ramo `main`.
**Motivo:** il codice vive in un repository proprio, separato dalla documentazione di lavoro.
**Dettagli:**
- `.gitignore` esclude `venv/`, `.env`, `__pycache__/` e `*.pyc`, così ambiente, segreti e file generati non finiscono mai nel repository.
- Primo commit: "Inizializza il repository con .gitignore".
**Errore e correzione:** al primo tentativo `git init` e il venv erano stati creati nella cartella sopra, per un `cd` saltato. Dopo aver verificato che il venv fosse appena creato, sono stati eliminati e ricreati nel posto giusto.

**Prossimo passo:** definire le cinque tabelle con SQLAlchemy 2.0 (installando anche il driver PostgreSQL) e configurare la connessione con un file `.env` (escluso da Git) e un `.env.example` con valori finti.
