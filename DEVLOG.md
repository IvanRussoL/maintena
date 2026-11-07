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

## 2026-11-04 – Lettura di un reparto: GET /reparti/{reparto_id}

**Decisione:** `GET /reparti/{reparto_id}` restituisce un solo reparto. L'id è un parametro di percorso tipizzato (`reparto_id: int`); la ricerca usa `db.get(Reparto, reparto_id)`; se il risultato è `None` la rotta solleva `HTTPException(status_code=404, detail="Reparto non trovato")`. La risposta usa `response_model=RepartoLettura`.
**Motivo:**
- `db.get` cerca per chiave primaria ed è il modo diretto per leggere una riga dall'id; restituisce `None` se non esiste.
- 404 Not Found dice che la risorsa richiesta non esiste; 200 con corpo vuoto nasconderebbe l'errore a chi usa l'API.
- Il tipo `int` fa validare l'id a FastAPI: con un valore non numerico (`/reparti/abc`) risponde da solo 422 e la funzione non parte.
- Lo schema di uscita è lo stesso della lista, così le due letture hanno la stessa forma.
**Alternative scartate:** `select(Reparto).where(Reparto.id == reparto_id)` con `scalar_one_or_none()` (più lungo per una ricerca per chiave); restituire `None` o 200 con corpo vuoto.
**Verifica:** id esistente → 200; id inesistente → 404 (gli id possono avere buchi: la sequenza di PostgreSQL non torna indietro dopo un `INSERT` fallito); id non numerico → 422 (visibile con una richiesta diretta; l'interfaccia `/docs` blocca prima l'invio).
**Limite noto:** la query sta ancora nella rotta; quando nasceranno repository e servizi si sposterà nello strato repository.

**Prossimo passo:** da decidere.

## 2026-11-04 – Creazione di un macchinario: POST /macchinari

**Decisione:** `POST /macchinari` crea un macchinario. I dati in ingresso sono descritti da `MacchinarioCreazione` (`matricola`, `nome`, `reparto_id`; `modello` e `descrizione` facoltativi; `stato` con predefinito `"attivo"`), la risposta da `MacchinarioLettura` (gli stessi campi più `id`). In entrambi gli schemi `stato` è un `Literal["attivo", "fermo", "dismesso"]`. La rotta risponde 201 e, in ordine: controlla con `db.get(Reparto, dati.reparto_id)` che il reparto esista (altrimenti 404 "Reparto non trovato"); crea `Macchinario(**dati.model_dump())`; fa `db.commit()` dentro un `try` (su `IntegrityError`: `rollback` e 409 "Esiste già un macchinario con questa matricola"); infine `db.refresh` e restituisce l'oggetto.
**Motivo:**
- `Literal` fa rifiutare a Pydantic uno stato fuori elenco con 422, prima che la richiesta arrivi al database; il `CHECK` del database resta come seconda barriera.
- Il reparto si controlla prima dell'`INSERT`: una chiave esterna violata darebbe un `IntegrityError` uguale a quello della matricola doppia, e il 409 avrebbe un messaggio falso. Con il controllo, il reparto inesistente ha il suo 404 e l'`IntegrityError` che resta è quello della matricola.
- 404 per il reparto: la risorsa a cui la richiesta si riferisce non esiste.
- `dati.model_dump()` trasforma lo schema in dizionario e `**` lo passa come argomenti con nome, senza ricopiare i campi uno a uno; funziona finché schema e modello usano gli stessi nomi.
**Alternative scartate:** affidarsi alla sola chiave esterna del database (non permette di distinguere la causa dell'errore).
**Verifica (da `/docs`):** dati validi → 201 (id 1); matricola già esistente → 409; `reparto_id` 10 → 404; stato "rotto" → 422 (`literal_error`).
**Errori e correzioni:** `reparto_id: str` invece di `int` in `MacchinarioLettura` (con Pydantic v2 avrebbe dato un 500 al momento della risposta); 500 invece di 404 per il reparto inesistente; `db.refresh()` senza argomento.
**Limiti noti / da fare:**
- Il controllo del reparto e l'`INSERT` sono due operazioni separate, non atomiche. Se tra le due il reparto venisse cancellato, la chiave esterna darebbe un `IntegrityError` e il messaggio 409 sarebbe sbagliato. I dati non si rovinano (il database rifiuta comunque l'`INSERT`); sbaglia solo il messaggio. Oggi non esiste una rotta per cancellare i reparti e la chiave esterna è `RESTRICT`, quindi il caso non si può provocare. Risolto il 2026-11-04 leggendo il codice SQLSTATE dell'errore (voce successiva).
- `matricola` e `descrizione` vuote (`""`) sono accettate: Swagger invia `descrizione` come `""` e nel database finisce una stringa vuota invece di `NULL` (stesso caso del nome vuoto dei reparti): validazione in fase 2.
- L'elenco degli stati è scritto in tre punti (due schemi e il `CHECK`): se cambia, vanno aggiornati tutti.
- Il 404 e il 409 non sono ancora documentati in Swagger (`responses=`): fase 2.
- La rotta scrive ancora direttamente nel database, senza servizi né repository.

**Prossimo passo:** da decidere.

## 2026-11-04 – Distinzione 404/409 con il codice SQLSTATE

**Decisione:** in `POST /macchinari`, nell'`except IntegrityError as e`, dopo il `rollback` la rotta legge `codice = e.orig.sqlstate`. Se il codice è `"23503"` (violazione di chiave esterna) risponde 404 "Reparto non trovato"; altrimenti 409 "Esiste già un macchinario con questa matricola". Il controllo iniziale con `db.get` resta per il caso normale.
**Motivo:**
- `IntegrityError` copre qualunque vincolo violato, ma PostgreSQL indica quale con un codice SQLSTATE standard: `23505` per `UNIQUE`, `23503` per chiave esterna.
- Controllo e `INSERT` sono due operazioni separate: se il reparto sparisse tra le due, il solo `db.get` non basterebbe e il 409 avrebbe un messaggio falso. Leggendo il vincolo realmente violato, la risposta è corretta anche in quel caso.
- Con il driver psycopg 3 l'attributo è `sqlstate`; con psycopg2 sarebbe `pgcode`.
**Alternative scartate:** togliere il `db.get` (nel caso normale si tenterebbe un `INSERT` destinato a fallire); un solo `except` con 409 (messaggio falso quando la causa è il reparto); confrontare il testo del messaggio d'errore (dipende dalla lingua e dalla versione del database).
**Verifica:** togliendo temporaneamente le righe del `db.get`, `reparto_id` 10 → 404 dall'`except`; con le righe ripristinate, matricola già esistente → 409.
**Limiti noti:** qualunque altro `IntegrityError` (`NOT NULL` `23502`, `CHECK` `23514`) finirebbe nel 409 con il messaggio della matricola; oggi la validazione Pydantic li blocca prima. La rotta scrive ancora direttamente nel database, senza servizi né repository.

**Prossimo passo:** da decidere.

## 2026-11-04 – Elenco dei macchinari con filtro facoltativo: GET /macchinari

**Decisione:** `GET /macchinari` restituisce l'elenco dei macchinari. Un filtro facoltativo `reparto_id`, passato come parametro di query (`/macchinari?reparto_id=1`), restringe l'elenco ai macchinari di quel reparto. La funzione è `elenca_macchinari(reparto_id: int | None = None, db: Session = Depends(get_db))` con `response_model=list[MacchinarioLettura]`. La query si costruisce a pezzi: `query = select(Macchinario)`; solo se `reparto_id is not None` si aggiunge `query = query.where(Macchinario.reparto_id == reparto_id)`; poi `return db.scalars(query).all()`.
**Motivo:**
- Il filtro è un parametro di **query** e non di percorso: il percorso (`/reparti/{reparto_id}`) identifica una risorsa precisa, la query restringe un elenco e può mancare.
- `int | None = None` dice che il parametro è facoltativo e che, se manca, vale `None`; il tipo dichiarato ammette il valore predefinito.
- `select(...)` descrive la query ma non la esegue, e `.where(...)` ne restituisce una nuova: così il filtro si aggiunge solo quando serve e l'esecuzione resta una sola, in `db.scalars(...)`.
- Un filtro senza risultati risponde 200 con `[]`, non 404: l'elenco esiste ed è vuoto; il 404 è per una risorsa specifica che non c'è.
**Alternative scartate:** nessuna discussa in questo passo.
**Verifica (da `/docs`):** senza filtro 3 macchinari (id 1 e 4 nel reparto 1, id 6 nel reparto 3); `reparto_id=1` → 2 macchinari; `reparto_id=10` → `[]`; `reparto_id=abc` → 422 (`loc: query`). Il primo tentativo non dimostrava il filtro, perché tutti i macchinari erano nel reparto 1 e il risultato sarebbe stato identico anche con un filtro che non filtra; il test è stato rifatto aggiungendo un macchinario nel reparto 3.
**Errori e correzioni:** `select(reparto_id)` invece di `select(Macchinario)` (si seleziona la classe del modello, non il valore del filtro); `int = None` invece di `int | None = None`.
**Limiti noti:**
- Un `reparto_id` inesistente non dà 404 ma `[]`: la rotta non controlla che il reparto esista.
- L'elenco è completo, senza paginazione.
- La query sta ancora nella rotta; quando nasceranno repository e servizi si sposterà nello strato repository.

**Prossimo passo:** da decidere.

## 2026-11-07 – Docstring alle rotte e lettura di un macchinario: GET /macchinari/{macchinario_id}

**Decisione:** (1) il modulo `app/main.py` e ogni rotta hanno un docstring; nelle rotte che possono rispondere con un errore il docstring elenca i codici (404, 409). (2) `GET /macchinari/{macchinario_id}` restituisce un macchinario per id: `db.get(Macchinario, macchinario_id)`; se non esiste risponde 404 "Macchinario non trovato". Risposta con `response_model=MacchinarioLettura`.
**Motivo:**
- Il docstring spiega cosa fa la rotta e quali errori può dare; non cambia il comportamento.
- Per leggere una risorsa precisa l'id va nel percorso (`/macchinari/{macchinario_id}`); `db.get` cerca per chiave primaria. Un id che non esiste è un 404, non un elenco vuoto.
- Il nome tra graffe nel percorso deve coincidere con il nome del parametro della funzione: FastAPI li collega per nome. Se differiscono, il parametro della funzione diventa un parametro di query obbligatorio e la richiesta risponde 422.
- A `Depends` si passa la funzione (`Depends(get_db)`), non il suo risultato: FastAPI la chiama a ogni richiesta.
**Alternative scartate:** nessuna discussa in questo passo.
**Verifica (da `/docs`):** id esistente → 200; id 200 (inesistente) → 404 "Macchinario non trovato".
**Errori e correzioni:** nome nel percorso `{macchinari_id}` diverso dal parametro `macchinario_id`; `Depends(get_db())` con le parentesi.
**Limiti noti:** il 404 compare in Swagger come "Undocumented": si documenta con `responses=` in fase 2. La lettura sta ancora nella rotta, senza strato servizi né repository.

**Prossimo passo:** da decidere.

## 2026-11-07 – Segnalazione di un guasto: POST /guasti

**Decisione:** `POST /guasti` crea un guasto su un macchinario esistente e risponde 201 con `GuastoLettura`. Schema d'ingresso `GuastoCreazione` (`macchinario_id`, `descrizione`, `priorita`, `segnalato_da`); `stato` (`aperto`) e `data_segnalazione` non vengono dal client: li scrive il database. Se il macchinario non esiste risponde 404 "Macchinario non trovato".
**Motivo:**
- Due schemi, come per reparti e macchinari: uno d'ingresso (senza `id`, `stato`, date automatiche) e uno di lettura (con tutti i campi, `from_attributes=True`). Entrambi sono oggetti di trasferimento dati, separati dal modello SQLAlchemy.
- `priorita` è obbligatoria nello schema perché la colonna non ha un valore predefinito.
- Il macchinario si controlla prima con `db.get` (messaggio chiaro, nessun `INSERT` inutile); l'`except IntegrityError` con SQLSTATE `23503` copre il caso in cui il macchinario sparisca tra il controllo e il `commit`, come in `POST /macchinari`.
- Ogni altro `IntegrityError` viene rilanciato con `raise`: senza, la funzione restituirebbe un guasto mai salvato.
**Alternative scartate:** nessuna discussa in questo passo.
**Verifica (da `/docs`):** dati validi → 201 con `stato` "aperto", `data_segnalazione` valorizzata e `data_chiusura` null; `macchinario_id` 99 → 404; `priorita` "lorenzo" → 500.
**Errori e correzioni:** schema d'ingresso sbagliato nella firma (`MacchinarioCreazione`); `macchinario_id` mancante in `GuastoLettura`; `db.refresh()` senza argomento; `except` che non rilanciava gli errori diversi da 23503.
**Limiti noti:**
- Una priorità non valida dà 500 invece di 422: il `CHECK` del database scatta e l'errore viene rilanciato. Da risolvere in fase 2 con `Literal["bassa", "media", "alta", "critica"]` nello schema.
- `descrizione` e `segnalato_da` accettano la stringa vuota (fase 2).
- Controllo e scrittura sono nella rotta, senza strato servizi né repository.

**Prossimo passo:** da decidere.

## 2026-11-07 – Elenco dei guasti: GET /guasti

**Decisione:** `GET /guasti` restituisce l'elenco dei guasti, con filtro facoltativo `?macchinario_id=`. Risposta 200 con `list[GuastoLettura]`; senza filtro tutti i guasti, con filtro solo quelli del macchinario indicato.
**Motivo:**
- Stesso schema di `GET /macchinari`: il parametro facoltativo si scrive `int | None = None` e la query si costruisce a pezzi (`query = query.where(...)`) ed è eseguita una volta sola alla fine.
- Il filtro si applica con `is not None`, non con un controllo di verità: così anche un valore come 0 sarebbe un filtro valido.
- Un macchinario senza guasti (o inesistente) dà `[]` con 200, non 404: un elenco vuoto è una risposta valida; il 404 è per la singola risorsa che non esiste.
**Alternative scartate:** nessuna discussa in questo passo.
**Verifica (da `/docs`):** senza filtro tutti i guasti; `macchinario_id=1` solo i guasti di quel macchinario; `macchinario_id=99` lista vuota.
**Errori e correzioni:** percorso `/macchinari` al posto di `/guasti` (rotta duplicata); condizione `is None` invertita; `.all` senza parentesi; docstring con la frase invertita.
**Note:** gli id dei guasti non sono consecutivi (manca il 2): probabile effetto della sequenza di PostgreSQL, che non torna indietro dopo un `INSERT` fallito (ipotesi, non verificata). Non è un errore.
**Limiti noti:** nessun ordinamento né paginazione; la query sta ancora nella rotta, senza strato servizi né repository.

**Prossimo passo:** da decidere.

## 2026-11-07 – Creazione di un tecnico: POST /tecnici

**Decisione:** `POST /tecnici` crea un tecnico e risponde 201 con `TecnicoLettura`. Schema d'ingresso `TecnicoCreazione` (`codice_dipendente`, `nome`, `cognome`, `specializzazione` facoltativa); `attivo` non viene dal client: lo scrive il database (`true`). Se il codice dipendente esiste già risponde 409 "Esiste già un tecnico con questo codice".
**Motivo:**
- Il codice dipendente ha un vincolo `UNIQUE` nel database: è lui la garanzia, quindi la rotta non fa un controllo preventivo ma intercetta l'`IntegrityError` al `commit`.
- Nell'`except` il `rollback` va per primo (rende di nuovo utilizzabile la sessione); poi il codice SQLSTATE `23505` (`UNIQUE`) diventa 409 e ogni altro errore viene rilanciato con `raise`, come in `POST /guasti`.
- `attivo` non sta nello schema d'ingresso perché nel modello ha `server_default="true"`; sta nello schema di lettura (`bool`), riletto da `db.refresh`.
**Alternative scartate:** nessuna discussa in questo passo.
**Verifica (da `/docs`):** dati validi → 201 con `attivo` true; codice già esistente → 409; `specializzazione` fuori elenco o stringa vuota → 500; `specializzazione` omessa → 201 con `null`.
**Errori e correzioni:** `id = int` al posto di `id: int`; `from_attributes` mancante; `attivo` nello schema d'ingresso e poi dichiarato `str` invece di `bool`; codice doppio non gestito (500); nell'`except`, `23514` al posto di `23505` e `rollback` dopo l'`if`.
**Limiti noti:**
- Una `specializzazione` non valida dà 500 invece di 422: il `CHECK` del database scatta e l'errore viene rilanciato. La stringa vuota non è `null` e viola lo stesso `CHECK`. Da risolvere in fase 2 con `Literal["meccanica", "elettrica", "idraulica", "elettronica"] | None = None` nello schema.
- `nome`, `cognome` e `codice_dipendente` accettano la stringa vuota (fase 2).
- Controllo e scrittura sono nella rotta, senza strato servizi né repository.

**Prossimo passo:** da decidere.
