# Progettazione – Maintena

Questo documento raccoglie le scelte di progetto di Maintena e, per ognuna, l'alternativa scartata e il motivo. Descrive lo stato alla chiusura della fase 1 (gestionale: schema dati e API). Il diario cronologico dei singoli passi è in [DEVLOG.md](../DEVLOG.md); i casi di test sono in [PIANO_TEST.md](PIANO_TEST.md).

## 1. Problema e utenti

In uno stabilimento i guasti dei macchinari si segnalano a voce o su fogli sparsi, ed è facile perdere lo storico: chi ha segnalato cosa, quale intervento è stato fatto, chi lo ha eseguito, se un guasto è davvero risolto. Maintena tiene insieme macchinari, guasti, ordini di lavoro e tecnici in un'unica base dati, esposta da un'API JSON.

Il progetto ha due obiettivi successivi:

- **Gestionale (fase 1, chiusa):** anagrafica di reparti, macchinari e tecnici; segnalazione dei guasti; ordini di lavoro collegati a macchinario, guasto e tecnico.
- **Parte intelligente (fasi 3 e 4, da fare):** ricerca nei manuali tecnici (RAG, con citazione delle fonti) e un agente che propone interventi e chiede la conferma di una persona prima di modificare i dati.

Utenti previsti: chi segnala un guasto, chi assegna e segue gli ordini, chi esegue gli interventi. Nella fase 1 non esiste autenticazione e tutte le rotte sono aperte; i ruoli si decidono in fase 2 (sezione 8).

## 2. Requisiti della fase 1

- Gestire i **reparti** e i **macchinari** che vi appartengono, con uno stato (attivo, fermo, dismesso).
- Segnalare i **guasti** di un macchinario, con priorità e stato, e cambiarne lo stato.
- Gestire i **tecnici**, senza perdere lo storico quando smettono di essere disponibili.
- Creare **ordini di lavoro**, collegati a un macchinario e facoltativamente a un guasto e a un tecnico, e cambiarne lo stato.
- Elencare i dati con filtri semplici (per reparto, per macchinario, per stato, per tecnico attivo).
- Rifiutare con un errore chiaro le richieste incoerenti (id inesistenti, duplicati, chiusure non permesse).

## 3. Regole di business

- **Un macchinario appartiene a un solo reparto.** Un reparto con macchinari non si cancella.
- **La matricola di un macchinario e il codice dipendente di un tecnico sono unici**, così come il nome di un reparto.
- **Un guasto nasce `aperto`**; la data di segnalazione la scrive il database.
- **Un guasto non si può chiudere** (`risolto` o `annullato`) **se ha ordini di lavoro aperti**, cioè né `completato` né `annullato`: risposta 409. Chiudendo si imposta `data_chiusura`.
- **Un ordine collegato a un guasto deve riguardare lo stesso macchinario del guasto**: altrimenti 409.
- **Un ordine con un tecnico nasce `assegnato`**, senza tecnico `da_assegnare`. Completando un ordine si imposta `data_completamento`.
- **Un tecnico non si cancella: si disattiva** (`attivo = false`).
- Id inesistenti nelle richieste danno 404 con un messaggio che dice quale entità manca.

Regole non ancora applicate: le transizioni di stato (per esempio un ordine `completato` può tornare `da_assegnare`) e la coerenza fra stato e date. Vedi sezione 8.

## 4. Modello dei dati

Cinque tabelle, definite in `app/models.py` con SQLAlchemy 2.

| Tabella | Colonne principali | Note |
|---|---|---|
| `reparto` | `id`, `nome` (unico), `descrizione` (facoltativa) | |
| `macchinario` | `id`, `matricola` (unica), `nome`, `reparto_id`, `modello` (facoltativo), `stato`, `descrizione` (facoltativa) | `stato`: attivo, fermo, dismesso; predefinito attivo |
| `guasto` | `id`, `macchinario_id`, `descrizione`, `data_segnalazione`, `priorita`, `stato`, `data_chiusura` (facoltativa), `segnalato_da` | `priorita`: bassa, media, alta, critica; `stato`: aperto, in_lavorazione, risolto, annullato |
| `tecnico` | `id`, `codice_dipendente` (unico), `nome`, `cognome`, `specializzazione` (facoltativa), `attivo` | `specializzazione`: meccanica, elettrica, idraulica, elettronica |
| `ordine_lavoro` | `id`, `macchinario_id`, `guasto_id` (facoltativo), `tecnico_id` (facoltativo), `descrizione`, `stato`, `data_creazione`, `data_pianificata`, `data_completamento`, `esito` (facoltativi) | `stato`: da_assegnare, assegnato, in_corso, completato, annullato |

Relazioni: un reparto ha molti macchinari; un macchinario ha molti guasti e molti ordini; un guasto può avere più ordini; un tecnico può avere molti ordini.

Le date sono `DateTime(timezone=True)`, e quelle di creazione e segnalazione le scrive il database (`now()`).

## 5. Struttura del progetto

```
app/
├── main.py          crea l'applicazione e aggancia i router
├── database.py      engine, sessione, get_db
├── models.py        tabelle (SQLAlchemy)
├── schemas.py       schemi Pydantic di ingresso e uscita
└── routers/         reparti, macchinari, guasti, tecnici, ordini_lavoro
```

Ogni router ha un prefisso e un tag per la documentazione interattiva: `/reparti`, `/macchinari`, `/guasti`, `/tecnici`, `/ordini-lavoro`. Gli schemi sono separati in ingresso (`...Creazione`, `...AggiornamentoStato`) e in uscita (`...Lettura`).

**Architettura a quattro strati (rotte → servizi → repository → modelli):** oggi esiste solo lo strato delle rotte più i modelli. Le rotte contengono ancora controlli, query e scrittura. La divisione in servizi e repository è rimandata alla fase 2.

## 6. API

Quindici rotte; l'elenco con i codici di risposta è nel [README](../README.md) e i casi di test in [PIANO_TEST.md](PIANO_TEST.md). Convenzioni:

- 201 per le creazioni, 404 per entità inesistente, 409 per conflitti (duplicati, regole di coerenza), 422 per dati non validi.
- I filtri sono parametri di query facoltativi. Un filtro senza risultati dà una lista vuota, non 404.
- Per distinguere la causa di un errore del database si legge il codice SQLSTATE dell'eccezione (23503 chiave esterna, 23505 unicità, 23514 vincolo CHECK).

## 7. Scelte tecniche e alternative scartate

| Scelta | Alternativa scartata | Motivo |
|---|---|---|
| **FastAPI** per l'API | Flask | Validazione dei dati e documentazione interattiva integrate; schemi tipizzati con Pydantic |
| **SQLAlchemy 2** come ORM | SQLModel, Django ORM, SQL scritto a mano | Standard di fatto in Python, tiene separati modelli del database e schemi dell'API, permette di leggere l'SQL generato |
| **PostgreSQL 18** installato in nativo su Windows | WSL2, Docker | Il modo più semplice per iniziare; Docker arriva con la fase di produzione. Servirà anche per pgvector |
| **psycopg 3** come driver | psycopg2 | Versione attuale; la variante `[binary]` non richiede un compilatore |
| Elenchi fissi come **`String(20)` + `CHECK`** | `Enum` del database | Più facile da modificare (basta cambiare la condizione) |
| **`ondelete="RESTRICT"`** su tutte le chiavi esterne | `CASCADE`, `SET NULL` | Conserva lo storico; `SET NULL` cambierebbe in silenzio il significato di un ordine |
| **Cancellazione logica** del tecnico (`attivo`) | Cancellare la riga | Gli ordini storici restano collegati |
| **Stato del guasto salvato**, non calcolato | Ricavarlo dagli ordini | "Risolto" è una decisione di una persona; la coerenza è una regola di business |
| Nessuna colonna `tipo` (correttiva/preventiva) nell'ordine | Colonna `tipo` | Si ricava da `guasto_id` vuoto o presente |
| Nessun `reparto_id` nell'ordine | Colonna ridondante | Si ricava dal macchinario |
| **409 per i conflitti di stato** (chiusura con ordini aperti, guasto di un altro macchinario) | 400 o 422 | Il dato è valido, è in conflitto con lo stato di altri dati |
| **Controllo preventivo + vincolo del database** (`db.get` prima, poi gestione di `IntegrityError`) | Solo uno dei due | Il controllo dà messaggi chiari nel caso normale; il vincolo copre le richieste simultanee |
| `GET /tecnici` mostra **tutti** i tecnici per default | Solo gli attivi | Scelta del progetto; il filtro `?attivo=` restringe |
| Rotte divise in **router** per argomento, un solo commit di refactoring | Tutto in `main.py`; un commit per router | File più piccoli e prefisso scritto una volta; il comportamento non cambia |
| `create_all` per creare le tabelle | Migrazioni | Basta finché le tabelle sono nuove; le migrazioni servono quando se ne modifica una esistente |
| Test manuali descritti in un piano, test automatici in fase 2 | Solo pytest subito | I casi manuali sono la specifica da cui ricavare i test automatici |
| Righe a capo **LF** nel repository (`.gitattributes`: `* text=auto eol=lf`) | Impostazione locale dell'editor o `core.autocrlf` | Vale per chiunque cloni il repository e non dipende dall'editor |

## 8. Scelte rinviate alla fase 2

- **Strati servizi e repository.** Regole di coerenza e query escono dalle rotte. Rinviato perché la fase 2 riguarda comunque la qualità del codice e la tabella delle fasi non li colloca prima.
- **Transizioni di stato.** Oggi `PATCH` su guasti e ordini accetta qualunque stato valido da qualunque stato: un ordine `completato` può tornare `da_assegnare` e conserva `data_completamento`; ricompletarlo sovrascrive la data; un guasto riaperto conserva `data_chiusura`. Vanno definite le transizioni permesse e cosa succede alle date. I casi di test relativi sono TC-G14 e TC-O17.
- **Validazione in ingresso con `Literal`.** Priorità del guasto e specializzazione del tecnico non validi danno oggi 500; il filtro `?stato=` degli ordini con valore sconosciuto dà 200 e lista vuota. Con tipi a valori ammessi diventeranno 422. Lo stesso vale per il corpo di `PATCH`, dove oggi il 422 nasce dal `CHECK` del database.
- **Stringhe vuote** accettate per il nome di un reparto e la descrizione di un macchinario.
- **Documentare 404/409/422** nella documentazione interattiva (`responses=`).
- **Autenticazione e ruoli.** Se il tecnico coincide con l'utente che accede, e se `segnalato_da` (oggi testo libero) diventa un collegamento a un utente.
- **Ordinamento e paginazione** degli elenchi.
- **Tecnico disattivato** assegnabile a un nuovo ordine, e rotta per disattivare un tecnico.
- **Test automatici** con pytest, a partire dai casi del piano di test.

## 9. Sviluppi futuri

- **Fase 3:** ricerca nei manuali tecnici con embeddings e pgvector, con citazione delle fonti.
- **Fase 4:** agente con uso di strumenti (LangGraph) che propone interventi e chiede conferma prima di scrivere dati.
- **Fase 5:** container, integrazione continua, versionamento dei prompt, monitoraggio di costi, latenza e qualità.
- **Fase 6 (facoltativa):** interfaccia web, deploy su cloud.

Esclusi per ora per non complicare il modello: componenti dei macchinari e ruoli (relazione molti-a-molti); si riprendono solo se serve un caso d'uso.
