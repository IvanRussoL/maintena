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

**Decisione:** PostgreSQL 18 con l'installer ufficiale, database `maintena`.
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

## 2026-10-30 – Driver psycopg 3 e configurazione della connessione

**Decisione:** SQLAlchemy 2.x con il driver `psycopg` (versione 3, pacchetto `psycopg[binary]`); la stringa di connessione sta in `DATABASE_URL`, letta da un file `.env` con `python-dotenv`. Il repository contiene solo `.env.example` con valori finti; `.env` è escluso da Git.
**Motivo:** psycopg 3 è la versione attuale del driver; la variante `[binary]` è precompilata e non richiede un compilatore su Windows. Tenere la stringa in `.env` evita password nel codice. Formato dell'URL: `postgresql+psycopg://utente:password@host:porta/database`.
**Alternative scartate:** psycopg2 (versione precedente del driver).
**Verifica:** una query `SELECT version()` dal venv restituisce PostgreSQL 18.6. Con `echo=True` si vede l'SQL eseguito, compresi `BEGIN`, `SELECT version()` e `ROLLBACK` (la transazione si chiude senza `commit()` perché non scriviamo nulla). Le dipendenze sono fissate in `requirements.txt`.
**Errore e correzione:** le prime installazioni erano finite fuori dall'ambiente virtuale; dopo aver verificato il prefisso di Python con `sys.prefix` i pacchetti sono stati reinstallati nel venv.

**Prossimo passo:** prima tabella (`reparto`) come classe SQLAlchemy 2.0 e creazione nel database.

## 2026-10-30 – Primo modello `Reparto` e creazione della tabella

**Decisione:** i modelli stanno in `app/models.py` come classi SQLAlchemy 2.0 (`Mapped` + `mapped_column`); `engine` e `Base` stanno in `app/database.py`; le tabelle si creano con lo script `crea_tabelle.py` (`Base.metadata.create_all(engine)`).
**Motivo:** una classe per tabella, con tipo e obbligatorietà dichiarati insieme (`Mapped[str]` obbligatorio, `Mapped[str | None]` facoltativo). `engine` e `Base` in un file separato evitano import circolari tra modelli e script. `create_all` basta finché le tabelle sono nuove.
**Dettagli:**
- `reparto`: `id` chiave primaria, `nome` `VARCHAR(100)` obbligatorio e unico, `descrizione` `TEXT` facoltativa. SQL generato: `CREATE TABLE reparto (id SERIAL NOT NULL, nome VARCHAR(100) NOT NULL, descrizione TEXT, PRIMARY KEY (id), UNIQUE (nome))`.
- In `crea_tabelle.py` l'import `from app import models` è necessario: senza, le classi non si registrano e `create_all` non crea nulla, senza errori.
- `echo=True` resta attivo in sviluppo per leggere l'SQL.
**Limite noto:** `create_all` crea solo le tabelle mancanti e non modifica quelle esistenti; per cambiare una tabella già creata serviranno le migrazioni.
**Alternative scartate:** per ora nessuna strumentazione di migrazioni (non serve finché le tabelle sono nuove).

**Prossimo passo:** tabella `macchinario`, con la prima chiave esterna (`reparto_id`).

## 2026-10-30 – Modello Macchinario e prima chiave esterna

**Decisione:** la classe `Macchinario` in `app/models.py` collega ogni macchinario a un reparto con `reparto_id` (`ForeignKey("reparto.id", ondelete="RESTRICT")`); `stato` è una `String(20)` con valore predefinito `attivo` impostato dal database (`server_default`) e un `CheckConstraint` (`ck_macchinario_stato`) che ammette solo `attivo`, `fermo`, `dismesso`.
**Motivo:**
- `RESTRICT`: un reparto che ha macchinari non può essere cancellato per errore.
- `String` + `CHECK`: elenco di valori fisso, ma più facile da cambiare di un tipo `Enum` del database (basta modificare la condizione).
- `server_default`: il valore predefinito vale per chiunque scriva nella tabella, non solo per questo codice.
- `modello` facoltativo (`Mapped[str | None]`): servirà per collegare i manuali tecnici, ma non tutti i macchinari lo avranno.
**Alternative scartate:** `ondelete="CASCADE"` (cancellerebbe anche macchinari e, in futuro, guasti e ordini); `SET NULL` (non applicabile: `reparto_id` è obbligatorio); `Enum` per `stato`.
**Nota:** `create_all` ha creato solo la tabella nuova e ha lasciato intatta `reparto`: non modifica le tabelle esistenti, per cambiarle serviranno le migrazioni.

**Prossimo passo:** da definire (altre tabelle del gestionale, poi la prima API).

## 2026-10-31 – Modello Tecnico e cancellazione logica

**Decisione:** la classe `Tecnico` in `app/models.py` ha `codice_dipendente` (unico, `String(50)`), `nome` e `cognome` (`String(100)`), `specializzazione` (`String(20)`, con `CheckConstraint` `ck_tecnico_specializzazione` sui valori `meccanica`, `elettrica`, `idraulica`, `elettronica`) e `attivo` (`Mapped[bool]` con `server_default="true"`).
**Motivo:**
- `attivo` al posto della cancellazione: un tecnico ha ordini di lavoro nello storico, che non devono perdersi né impedire l'operazione. Si disattiva e non lo si propone più per nuovi interventi; gli elenchi dovranno filtrare `attivo = true`.
- `Mapped[bool]` basta a SQLAlchemy per creare una colonna `BOOLEAN`; il predefinito sta nella tabella (`server_default`), come per `stato` di `macchinario`.
- `String` + `CHECK` per `specializzazione`, come per gli altri elenchi fissi: più facile da modificare di un `Enum`.
**Errori e correzioni:** il `CHECK` era stato scritto su `attivo` (inutile su una colonna già booleana, e confrontava una stringa invece di un booleano): spostato su `specializzazione`. Un refuso nel nome del vincolo e le lunghezze di `cognome` e `specializzazione` sono stati corretti prima di lanciare `create_all`, che non modifica le tabelle già create.
**Alternative scartate:** cancellare i tecnici (perderebbe lo storico o sarebbe bloccato dalla chiave esterna); `Enum` per `specializzazione`.
**Correzione (stesso giorno):** `specializzazione` doveva essere facoltativa, come nello schema iniziale, ma nel codice era obbligatoria (svista). Modello cambiato in `Mapped[str | None]` e colonna resa facoltativa con `ALTER TABLE tecnico ALTER COLUMN specializzazione DROP NOT NULL`, verificata con un inserimento senza specializzazione. Il `CHECK` resta valido: un valore `NULL` lo supera.
**Limite noto:** modificare una tabella già creata richiede oggi un intervento manuale sul database, oltre alla modifica del modello; con dati veri serviranno le migrazioni.

**Prossimo passo:** tabella `guasto`, con chiave esterna verso `macchinario` e i campi data.

## 2026-10-31 – Modello Guasto, date con fuso orario

**Decisione:** la classe `Guasto` in `app/models.py` collega ogni guasto a un macchinario con `macchinario_id` (`ForeignKey("macchinario.id", ondelete="RESTRICT")`). `priorita` e `stato` sono `String(20)` con due `CheckConstraint` nominati (`ck_guasto_priorita`: `bassa`, `media`, `alta`, `critica`; `ck_guasto_stato`: `aperto`, `in_lavorazione`, `risolto`, `annullato`); `stato` ha predefinito `aperto` (`server_default`). Le date sono `DateTime(timezone=True)`: `data_segnalazione` ha `server_default=func.now()`, `data_chiusura` è facoltativa. `segnalato_da` è un testo provvisorio (`String(100)`), da rivedere quando arriveranno gli utenti.
**Motivo:**
- `RESTRICT`: un macchinario con guasti non si cancella, per non perdere lo storico (si usa lo stato `dismesso`).
- `timezone=True`: la colonna conserva un istante preciso, senza ambiguità di fuso o ora legale.
- `func.now()` come `server_default`: la data di segnalazione la mette il database, anche per chi inserisce con SQL a mano.
- Lo stato è salvato e non calcolato dagli ordini: "risolto" è una decisione di una persona. La coerenza con gli ordini aperti sarà una regola dello strato servizi.
- `data_chiusura` facoltativa: un guasto aperto non ha ancora una chiusura.
**Alternative scartate:** `Enum` per `priorita` e `stato` (più difficile da modificare); data senza fuso orario; `ondelete="CASCADE"` (cancellerebbe lo storico dei guasti).
**Errori e correzioni:** valori e virgola finale nei `CHECK`, `Mapped[DateTime]` al posto di `Mapped[datetime]` (con import mancante), `server_default=func` al posto di `func.now()`, `data_chiusura` e `descrizione` con obbligatorietà e tipo sbagliati: tutti corretti prima di lanciare `create_all`.
**Decisione `segnalato_da`:** resta obbligatorio, anche se lo schema iniziale non lo indicava come tale. Motivo: un guasto senza segnalante è un dato povero, e in seguito il campo diventerà il collegamento all'utente. Alternativa scartata: facoltativo (serve solo per segnalazioni anonime). Limite: `NOT NULL` non vieta il testo vuoto.

**Prossimo passo:** tabella `ordine_lavoro`, con tre chiavi esterne (macchinario, guasto e tecnico facoltativi dove previsto) e le date.

## 2026-10-31 – Modello OrdineLavoro e schema della fase 1 completo

**Decisione:** la classe `OrdineLavoro` in `app/models.py` ha tre chiavi esterne con `ondelete="RESTRICT"`: `macchinario_id` (obbligatoria), `guasto_id` e `tecnico_id` (facoltative, `Mapped[int | None]`). `descrizione` è obbligatoria (`Text`); `stato` è una `String(20)` con predefinito `da_assegnare` e un `CheckConstraint` (`ck_ordine_lavoro_stato`: `da_assegnare`, `assegnato`, `in_corso`, `completato`, `annullato`); `data_creazione` ha `server_default=func.now()`; `data_pianificata`, `data_completamento` ed `esito` sono facoltativi. Con questa tabella lo schema della fase 1 è completo: cinque tabelle.
**Motivo:**
- `guasto_id` facoltativo: una manutenzione programmata non nasce da un guasto, quindi il vuoto significa "preventiva". Per questo non c'è una colonna `tipo`.
- `tecnico_id` facoltativo: l'assegnazione avviene dopo la creazione dell'ordine; il vuoto significa "non ancora assegnato".
- `RESTRICT` anche sulle chiavi facoltative: conserva lo storico. `SET NULL` cambierebbe in silenzio il significato di un ordine (da correttivo a preventivo) quando si cancella un guasto.
- `data_completamento` ed `esito` si compilano a lavoro finito, come `data_chiusura` del guasto; `data_pianificata` si può decidere dopo la creazione.
**Alternative scartate:** `SET NULL` su `guasto_id` e `tecnico_id`; una colonna `tipo` correttiva/preventiva (si ricava da `guasto_id`); `reparto_id` nell'ordine (si ricava dal macchinario).
**Errori e correzioni:** nel `CHECK` mancava `'annullato'` (senza, un ordine non si sarebbe potuto annullare) e una riga aveva `=` al posto dei due punti dopo il nome dell'attributo; entrambi corretti prima di lanciare `create_all`.
**Limite noto:** il database controlla le colonne una per una, non le combinazioni. Accetta, per esempio, un ordine `completato` senza `data_completamento`, un ordine `assegnato` senza tecnico o un macchinario diverso da quello del guasto. Sono regole dello strato servizi, da progettare.

**Prossimo passo:** da decidere tra le regole di coerenza dei servizi e la prima API FastAPI.

## 2026-10-31 – Prima app FastAPI

**Decisione:** `app/main.py` crea l'applicazione con `FastAPI(title="Maintena")` ed espone una sola rotta, `GET /`, che restituisce `{"applicazione": "Maintena", "stato": "attiva"}`. FastAPI è installato con `pip install "fastapi[standard]"` (include Uvicorn e Pydantic) e si avvia in sviluppo con `fastapi dev app/main.py`; la documentazione interattiva è su `/docs`.
**Motivo:**
- Partire da una rotta minima che non tocca il database permette di verificare l'installazione e di capire il ciclo richiesta, funzione, risposta JSON prima di aggiungere sessione e schemi.
- FastAPI restituisce JSON e genera da solo la documentazione `/docs`, utile per provare le rotte senza un client.
**Alternative scartate:** Flask (già noto, ma senza validazione e documentazione automatiche); aggiungere subito `GET /reparti` (richiede la sessione del database e uno schema, due concetti nuovi in un passo solo).

**Prossimo passo:** `GET /reparti`, che legge i reparti dal database.

## 2026-10-31 – Prima rotta sui dati: GET /reparti

**Decisione:** `GET /reparti` restituisce l'elenco dei reparti. La sessione del database si ottiene con `get_db` (in `app/database.py`, un generatore con `yield` che chiude la sessione nel `finally`), iniettata nella rotta con `Depends(get_db)`. La forma della risposta è uno schema Pydantic, `RepartoLettura` (in `app/schemas.py`, con `from_attributes=True`), indicato in `response_model=list[RepartoLettura]`.
**Motivo:**
- Una sessione per richiesta, chiusa sempre (anche in caso di errore), evita connessioni lasciate aperte e sessioni condivise tra richieste.
- `Depends` toglie dalla rotta il codice di apertura e chiusura, e rende la sessione sostituibile nei test.
- Modello SQLAlchemy e schema Pydantic restano separati: il primo descrive la tabella, il secondo i dati che escono dall'API, così la risposta non espone per forza tutte le colonne.
- Lo schema deve avere gli stessi campi facoltativi del modello (`descrizione` può essere vuota), altrimenti la validazione della risposta fallisce.
**Alternative scartate:** una sessione globale unica; aprire e chiudere la sessione a mano in ogni rotta (ripetizione e rischio di dimenticare `close`); restituire direttamente gli oggetti SQLAlchemy senza schema.
**Limite noto:** per ora la rotta esegue la query da sola; quando nasceranno repository e servizi la query si sposterà nello strato repository. Con la tabella vuota la risposta è `[]`.

**Prossimo passo:** `POST /reparti`, per creare reparti e provare la lettura con dati veri.

## 2026-11-04 – Creazione di reparti: POST /reparti

**Decisione:** `POST /reparti` crea un reparto. I dati in ingresso sono descritti da uno schema Pydantic separato, `RepartoCreazione` (`nome: str`, `descrizione: str | None = None`), diverso da `RepartoLettura`, che descrive la risposta. La rotta ha `status_code=201` e `response_model=RepartoLettura`. Crea l'oggetto `Reparto`, poi `db.add`, `db.commit` e `db.refresh`, e lo restituisce.
**Motivo:**
- Schema di ingresso e di uscita separati: il client non deve mandare l'`id`, che assegna il database, mentre nella risposta l'`id` serve.
- `descrizione: str | None = None`: il tipo dichiara che il valore può essere assente o `null`, e il predefinito la rende facoltativa. `str = None` dichiarerebbe un tipo falso e rifiuterebbe un `null` esplicito con un errore 422.
- `201 Created` e non `200`: la richiesta ha creato una risorsa.
- `db.add` mette l'oggetto in sessione, `db.commit` scrive nel database, `db.refresh` rilegge la riga per avere i valori assegnati dal database (l'`id`).
- `response_model=RepartoLettura` filtra la risposta ai soli campi dello schema; senza di esso (o con lo schema sbagliato) la risposta non ha l'`id`.
**Alternative scartate:** riusare `RepartoLettura` anche in ingresso (obbligherebbe a mandare l'`id`); rispondere 200; restituire solo un messaggio di conferma senza il reparto creato.
**Errori e correzioni:** `descrizione: str = None` (tipo falso); `response_model` iniziale sbagliato (risposta senza `id`); `git add /app` fallito perché il percorso era assoluto (`git add app` funziona): tutti corretti.
**Limiti noti:** un nome già esistente fa fallire l'`INSERT` sul vincolo `UNIQUE` e la rotta risponde 500 (`IntegrityError` non gestito); l'`id` della riga fallita viene comunque consumato, perché le sequenze di PostgreSQL non tornano indietro. Un nome vuoto (`""`) è accettato: validazione in fase 2. La rotta scrive ancora direttamente nel database, senza servizi né repository.

**Prossimo passo:** rispondere 409 Conflict quando il nome del reparto esiste già.

## 2026-11-04 – Nome reparto duplicato: 409 Conflict

**Decisione:** in `POST /reparti` il `db.commit()` è dentro un `try`; se solleva `IntegrityError` (vincolo `UNIQUE` su `nome`) la rotta fa `db.rollback()` e solleva `HTTPException(status_code=409, detail="Esiste già un reparto con questo nome")`. `db.add` resta fuori dal `try`: non parla col database, l'errore nasce al `commit`.
**Motivo:**
- 409 Conflict dice che la richiesta è valida ma in conflitto con lo stato dei dati; 500 indicherebbe un guasto del server, mentre qui la causa è la richiesta.
- Dopo un errore la transazione è fallita: il `rollback` riporta la sessione in uno stato utilizzabile.
- `HTTPException` interrompe la funzione e FastAPI la trasforma nella risposta con il codice e il messaggio scelti.
**Alternative scartate:** controllare prima con una `SELECT` se il nome esiste (due richieste simultanee possono passare entrambe il controllo e una fallisce comunque sul `UNIQUE`: il vincolo del database serve comunque); lasciare il 500.
**Limiti noti:** `IntegrityError` copre qualunque vincolo violato, non solo il `UNIQUE`: va bene finché `reparto` ha solo quello; per tabelle con chiavi esterne servirà distinguere. L'`INSERT` fallito consuma comunque un id. Il 409 non è ancora documentato in Swagger (parametro `responses=`): rinviato alla fase 2. La rotta scrive ancora direttamente nel database, senza servizi né repository.

**Prossimo passo:** da decidere.
