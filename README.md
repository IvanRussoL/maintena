# Maintena

Gestionale di manutenzione industriale: macchinari, guasti, ordini di lavoro e tecnici, esposti da un'API JSON.

Maintena è un progetto personale di studio, costruito un passo alla volta. L'obiettivo finale è aggiungere la ricerca nei manuali tecnici (RAG, con citazione delle fonti) e un agente che propone interventi e chiede la conferma di una persona prima di modificare i dati. Queste due parti non sono ancora presenti.

## Stato del progetto

| Fase | Obiettivo | Stato |
|---|---|---|
| 0 | Verifica di LLM ed embeddings via API | Chiusa |
| 1 | Gestionale: schema dati e API (FastAPI, PostgreSQL) | Chiusa, con i limiti noti elencati sotto |
| 2 | Qualità e sicurezza: validazione, errori, autenticazione, test automatici, strati servizi e repository | Da fare |
| 3 | RAG sui manuali (embeddings, pgvector) | Da fare |
| 4 | Agente con conferma umana (LangGraph) | Da fare |
| 5 | Produzione: Docker, CI, monitoraggio | Da fare |

## Tecnologie

- Python 3.13
- FastAPI e Uvicorn per l'API, Pydantic per gli schemi di ingresso e uscita
- PostgreSQL 18
- SQLAlchemy 2 come ORM, con il driver psycopg 3

## Requisiti

- Python 3.13
- PostgreSQL in esecuzione in locale, con un database vuoto per Maintena
- Git

## Installazione

Comandi per PowerShell su Windows; su Linux e macOS cambia solo l'attivazione dell'ambiente virtuale (`source venv/bin/activate`).

```powershell
git clone https://github.com/IvanRussoL/maintena.git
cd maintena
python -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Crea il file `.env` partendo da `.env.example` e scrivi l'indirizzo del tuo database:

```
DATABASE_URL=postgresql+psycopg://utente:password@localhost:5432/maintena
```

Il file `.env` contiene credenziali ed è escluso da Git: non va mai committato.

Crea le tabelle e avvia l'applicazione:

```powershell
python crea_tabelle.py
uvicorn app.main:app --reload
```

L'API risponde su `http://127.0.0.1:8000`. La documentazione interattiva (Swagger UI) è su `http://127.0.0.1:8000/docs`.

Nota: l'engine di SQLAlchemy ha `echo=True`, quindi ogni istruzione SQL viene stampata nel terminale. È voluto, per vedere cosa genera l'ORM.

## Rotte

| Metodo e percorso | Descrizione |
|---|---|
| `GET /` | Controlla che l'applicazione sia attiva |
| `GET /reparti` | Elenco dei reparti |
| `GET /reparti/{id}` | Un reparto (404 se non esiste) |
| `POST /reparti` | Crea un reparto (409 se il nome esiste già) |
| `GET /macchinari` | Elenco dei macchinari, filtro facoltativo `?reparto_id=` |
| `GET /macchinari/{id}` | Un macchinario (404 se non esiste) |
| `POST /macchinari` | Crea un macchinario (404 se il reparto non esiste, 409 se la matricola esiste già) |
| `GET /guasti` | Elenco dei guasti, filtro facoltativo `?macchinario_id=` |
| `POST /guasti` | Segnala un guasto (404 se il macchinario non esiste) |
| `PATCH /guasti/{id}` | Cambia lo stato di un guasto (409 se si chiude con ordini ancora aperti) |
| `GET /tecnici` | Elenco dei tecnici, filtro facoltativo `?attivo=` |
| `POST /tecnici` | Crea un tecnico (409 se il codice dipendente esiste già) |
| `GET /ordini-lavoro` | Elenco degli ordini di lavoro, filtro facoltativo `?stato=` |
| `POST /ordini-lavoro` | Crea un ordine (404 se macchinario, guasto o tecnico non esistono; 409 se il guasto è di un altro macchinario) |
| `PATCH /ordini-lavoro/{id}` | Cambia lo stato di un ordine |

## Struttura

```
maintena/
├── app/
│   ├── main.py          crea l'applicazione e aggancia i router
│   ├── database.py      engine, sessione e get_db
│   ├── models.py        le cinque tabelle (SQLAlchemy)
│   ├── schemas.py       schemi Pydantic di ingresso e uscita
│   └── routers/         una rotta per argomento: reparti, macchinari, guasti, tecnici, ordini_lavoro
├── docs/
│   └── PIANO_TEST.md    60 casi di test manuali sulle rotte
├── crea_tabelle.py      crea le tabelle nel database
├── DEVLOG.md            diario delle decisioni, passo per passo
├── requirements.txt
└── .env.example
```

Oggi le rotte parlano direttamente con il database. La divisione in strati servizi e repository è prevista nella fase 2.

## Limiti noti

Il comportamento attuale non è quello definitivo. I principali, tutti da sistemare nella fase 2:

- una priorità di guasto o una specializzazione di tecnico non valide danno 500 invece di 422;
- `GET /ordini-lavoro?stato=...` con uno stato inesistente risponde 200 con elenco vuoto;
- nessun controllo sulle transizioni di stato di guasti e ordini (per esempio un ordine `completato` può tornare `da_assegnare` e mantiene la data di completamento);
- nessuna autenticazione: tutte le rotte sono aperte;
- il nome di un reparto e la descrizione di un macchinario accettano la stringa vuota;
- gli elenchi non hanno un ordinamento esplicito né la paginazione.

L'elenco completo è nella sezione 4 del piano di test.

## Documentazione

- [DEVLOG.md](DEVLOG.md): decisioni, motivi e alternative scartate di ogni passo.
- [docs/PIANO_TEST.md](docs/PIANO_TEST.md): casi di test, ambiente e note per il tester.
- [docs/PROGETTAZIONE.md](docs/PROGETTAZIONE.md): scelte di progetto e alternative scartate.
