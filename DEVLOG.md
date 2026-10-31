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
