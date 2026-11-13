# Maintena

API REST per la manutenzione industriale: reparti, macchinari, guasti, tecnici e ordini di lavoro. Scritta in Python con FastAPI, SQLAlchemy e PostgreSQL.

## Funzionalità

- Anagrafica di reparti, macchinari e tecnici
- Segnalazione dei guasti e cambio di stato
- Ordini di lavoro collegati a macchinario, guasto e tecnico
- Filtri sugli elenchi: per reparto, macchinario, stato, tecnico attivo
- Controlli di coerenza sui dati: un guasto non si chiude con ordini ancora aperti, un ordine deve riguardare lo stesso macchinario del suo guasto
- Documentazione interattiva generata da FastAPI (Swagger UI)

## Stack

Python 3.13, FastAPI, Pydantic, SQLAlchemy 2, psycopg 3, PostgreSQL 18.

## Installazione

Servono Python 3.13, Git e un database PostgreSQL vuoto per Maintena.

```powershell
git clone https://github.com/IvanRussoL/maintena.git
cd maintena
python -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Su Linux e macOS l'ambiente virtuale si attiva con `source venv/bin/activate`.

Per eseguire anche i test si installa `requirements-dev.txt`, che include `requirements.txt` e aggiunge pytest:

```powershell
pip install -r requirements-dev.txt
```

## Configurazione

Copia `.env.example` in `.env` e imposta l'indirizzo del database:

```
DATABASE_URL=postgresql+psycopg://utente:password@localhost:5432/maintena
```

`.env` è escluso da Git.

Crea le tabelle:

```powershell
python crea_tabelle.py
```

## Test

I test usano un database PostgreSQL separato, che le fixture riempiono e svuotano a ogni test: non va usato quello dell'applicazione. Crea un database vuoto (per esempio `maintena_test`) e aggiungi a `.env` il suo indirizzo:

```
TEST_DATABASE_URL=postgresql+psycopg://utente:password@localhost:5432/maintena_test
```

Poi, dalla radice del progetto:

```powershell
python -m pytest -v
```

Per ora c'è un solo test automatico (creazione di un reparto); gli altri casi sono descritti in [docs/PIANO_TEST.md](docs/PIANO_TEST.md) e vanno ancora trasformati in test.

## Avvio

```powershell
uvicorn app.main:app --reload
```

L'API risponde su `http://127.0.0.1:8000`. La documentazione interattiva è su `/docs`.

L'engine di SQLAlchemy ha `echo=True`: ogni istruzione SQL viene stampata nel terminale.

## Endpoint

| Metodo e percorso | Descrizione |
|---|---|
| `GET /` | Controlla che l'applicazione sia attiva |
| `GET /reparti` | Elenco dei reparti |
| `GET /reparti/{id}` | Un reparto (404 se non esiste) |
| `POST /reparti` | Crea un reparto (409 se il nome esiste già) |
| `GET /macchinari` | Elenco dei macchinari, filtro `?reparto_id=` |
| `GET /macchinari/{id}` | Un macchinario (404 se non esiste) |
| `POST /macchinari` | Crea un macchinario (404 se il reparto non esiste, 409 se la matricola esiste già) |
| `GET /guasti` | Elenco dei guasti, filtro `?macchinario_id=` |
| `POST /guasti` | Segnala un guasto (404 se il macchinario non esiste) |
| `PATCH /guasti/{id}` | Cambia lo stato (409 se si chiude con ordini aperti) |
| `GET /tecnici` | Elenco dei tecnici, filtro `?attivo=` |
| `POST /tecnici` | Crea un tecnico (409 se il codice dipendente esiste già) |
| `GET /ordini-lavoro` | Elenco degli ordini, filtro `?stato=` |
| `POST /ordini-lavoro` | Crea un ordine (404 se macchinario, guasto o tecnico non esistono; 409 se il guasto è di un altro macchinario) |
| `PATCH /ordini-lavoro/{id}` | Cambia lo stato di un ordine |

## Struttura

```
app/
├── main.py          applicazione e router
├── database.py      engine, sessione, get_db
├── models.py        tabelle (SQLAlchemy)
├── schemas.py       schemi Pydantic
└── routers/         reparti, macchinari, guasti, tecnici, ordini_lavoro
docs/
├── PIANO_TEST.md    casi di test
└── PROGETTAZIONE.md scelte di progetto
tests/               test automatici (pytest)
crea_tabelle.py      crea le tabelle
DEVLOG.md            diario delle decisioni
```

## Roadmap

- Fase 2 (in corso): test automatici con pytest (infrastruttura pronta), strati servizi e repository, validazione in ingresso (422), transizioni di stato, autenticazione
- Ricerca nei manuali tecnici (RAG con pgvector e citazione delle fonti)
- Agente (LangGraph) che propone interventi e chiede conferma prima di modificare i dati
- Docker e CI

## Limiti noti

- Una priorità di guasto o una specializzazione di tecnico non valide danno 500 invece di 422
- Nessun controllo sulle transizioni di stato di guasti e ordini
- Nessuna autenticazione: le rotte sono aperte
- Gli elenchi non hanno ordinamento né paginazione

L'elenco completo è nella sezione 4 di [docs/PIANO_TEST.md](docs/PIANO_TEST.md).

## Documentazione

- [docs/PROGETTAZIONE.md](docs/PROGETTAZIONE.md): requisiti, modello dei dati, scelte e alternative scartate
- [docs/PIANO_TEST.md](docs/PIANO_TEST.md): casi di test
- [DEVLOG.md](DEVLOG.md): decisioni passo per passo
