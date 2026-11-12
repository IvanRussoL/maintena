# Piano di test — Maintena

Piano di test dell'API del gestionale (fase 1). I casi descrivono il comportamento **attuale** del codice, compresi i limiti noti elencati nella sezione 4: dove un caso documenta un limite, l'atteso è il comportamento di oggi, non quello desiderato.

## 1. Introduzione e ambiente di test

- **Indirizzo dell'applicazione**: `http://127.0.0.1:8000`. Nei casi di test i percorsi sono relativi a questo indirizzo.
- **Avvio**: dalla cartella del repository, con l'ambiente virtuale attivo, `uvicorn app.main:app --reload`.
- **Strumenti**: la documentazione interattiva di FastAPI (`/docs`, Swagger UI), oppure curl o un client HTTP equivalente. `/openapi.json` elenca le quindici rotte e i cinque tag (`reparti`, `macchinari`, `guasti`, `tecnici`, `ordini-lavoro`).
- **Database**: PostgreSQL locale. Per una sessione di test usare un database separato da quello di sviluppo, con le tabelle create da `crea_tabelle.py` e la variabile `DATABASE_URL` del file `.env` (escluso da Git) puntata a quel database.
- **Utenti di test**: nessuno. L'autenticazione non è ancora implementata (prevista in fase 2): tutte le rotte sono aperte e i casi non richiedono credenziali. Quando l'autenticazione sarà introdotta, questa sezione elencherà i ruoli necessari, senza password.
- **Servizi esterni**: nessuno. L'LLM e gli embeddings non sono ancora usati dall'applicazione.
- **Dati di test**: solo dati inventati.

## 2. Casi di test manuali

I casi sono raggruppati per area:

| Prefisso | Area | Rotte |
|---|---|---|
| TC-A | Applicazione | `GET /` |
| TC-R | Reparti | `GET /reparti`, `POST /reparti`, `GET /reparti/{reparto_id}` |
| TC-M | Macchinari | `GET /macchinari`, `POST /macchinari`, `GET /macchinari/{macchinario_id}` |
| TC-T | Tecnici | `GET /tecnici`, `POST /tecnici` |
| TC-G | Guasti | `GET /guasti`, `POST /guasti`, `PATCH /guasti/{guasto_id}` |
| TC-O | Ordini di lavoro | `GET /ordini-lavoro`, `POST /ordini-lavoro`, `PATCH /ordini-lavoro/{ordine_id}` |

Convenzioni: `{id}` indica l'identificativo restituito dalla creazione del record, da riusare nei passi successivi. Gli identificativi non sono consecutivi (vedi sezione 4): non vanno dati per scontati. Nei casi 4xx il corpo contiene `{"detail": ...}`; nei 422 generati dalla validazione dei dati in ingresso `detail` è un elenco di errori, negli altri è una stringa.

### TC-A — Applicazione

**TC-A01 — Controllo dello stato dell'applicazione**

| Campo | Contenuto |
|---|---|
| **Precondizione** | Applicazione avviata. |
| **Passi** | 1. `GET /` |
| **Atteso** | 1. Codice 200 e corpo `{"applicazione": "Maintena", "stato": "attiva"}`. |

### TC-R — Reparti

**TC-R01 — Elenco dei reparti con tabella vuota**

| Campo | Contenuto |
|---|---|
| **Precondizione** | Nessun reparto presente. |
| **Passi** | 1. `GET /reparti` |
| **Atteso** | 1. Codice 200 e corpo `[]`. |

**TC-R02 — Creazione di un reparto**

| Campo | Contenuto |
|---|---|
| **Precondizione** | Non esiste un reparto con nome "Pressatura". |
| **Passi** | 1. `POST /reparti` con `{"nome": "Pressatura"}`. 2. `GET /reparti`. |
| **Atteso** | 1. Codice 201 e corpo con `id`, `nome` "Pressatura" e `descrizione` `null`. 2. Il reparto compare nell'elenco. |

**TC-R03 — Creazione di un reparto con descrizione**

| Campo | Contenuto |
|---|---|
| **Precondizione** | Non esiste un reparto con nome "Montaggio". |
| **Passi** | 1. `POST /reparti` con `{"nome": "Montaggio", "descrizione": "Linea 2"}`. |
| **Atteso** | 1. Codice 201 e corpo con la descrizione "Linea 2". |

**TC-R04 — Nome di reparto già usato**

| Campo | Contenuto |
|---|---|
| **Precondizione** | Esiste il reparto "Pressatura" (TC-R02). |
| **Passi** | 1. `POST /reparti` con `{"nome": "Pressatura"}`. 2. `GET /reparti`. |
| **Atteso** | 1. Codice 409 e `detail` "Esiste già un reparto con questo nome". 2. Esiste ancora un solo reparto "Pressatura". |

**TC-R05 — Creazione di un reparto senza nome**

| Campo | Contenuto |
|---|---|
| **Precondizione** | Nessuna. |
| **Passi** | 1. `POST /reparti` con `{}`. |
| **Atteso** | 1. Codice 422; l'errore indica il campo `nome` mancante. Nessun reparto creato. |

**TC-R06 — Lettura di un reparto per id**

| Campo | Contenuto |
|---|---|
| **Precondizione** | Esiste il reparto creato in TC-R02. |
| **Passi** | 1. `GET /reparti/{id}` con l'id del reparto. |
| **Atteso** | 1. Codice 200 e corpo con `id`, `nome` e `descrizione` del reparto. |

**TC-R07 — Lettura di un reparto inesistente**

| Campo | Contenuto |
|---|---|
| **Precondizione** | Non esiste un reparto con id 999999. |
| **Passi** | 1. `GET /reparti/999999`. |
| **Atteso** | 1. Codice 404 e `detail` "Reparto non trovato". |

**TC-R08 — Id del reparto non numerico**

| Campo | Contenuto |
|---|---|
| **Precondizione** | Nessuna. |
| **Passi** | 1. `GET /reparti/abc`. |
| **Atteso** | 1. Codice 422; l'errore riguarda il parametro di percorso `reparto_id`. |

### TC-M — Macchinari

**TC-M01 — Creazione di un macchinario con i soli campi obbligatori**

| Campo | Contenuto |
|---|---|
| **Precondizione** | Esiste un reparto (id `{reparto}`). Non esiste un macchinario con matricola "M-1". |
| **Passi** | 1. `POST /macchinari` con `{"matricola": "M-1", "nome": "Pressa", "reparto_id": {reparto}}`. |
| **Atteso** | 1. Codice 201; `stato` "attivo" (valore predefinito), `modello` e `descrizione` `null`. |

**TC-M02 — Creazione di un macchinario con stato indicato**

| Campo | Contenuto |
|---|---|
| **Precondizione** | Esiste un reparto. Non esiste la matricola "M-2". |
| **Passi** | 1. `POST /macchinari` con `{"matricola": "M-2", "nome": "Tornio", "reparto_id": {reparto}, "stato": "fermo"}`. |
| **Atteso** | 1. Codice 201 e `stato` "fermo". |

**TC-M03 — Matricola già usata**

| Campo | Contenuto |
|---|---|
| **Precondizione** | Esiste il macchinario con matricola "M-1" (TC-M01). |
| **Passi** | 1. `POST /macchinari` con la stessa matricola "M-1" (altri campi validi). |
| **Atteso** | 1. Codice 409 e `detail` "Esiste già un macchinario con questa matricola". Nessun macchinario aggiunto. |

**TC-M04 — Reparto inesistente**

| Campo | Contenuto |
|---|---|
| **Precondizione** | Non esiste un reparto con id 999999. |
| **Passi** | 1. `POST /macchinari` con `{"matricola": "M-3", "nome": "X", "reparto_id": 999999}`. |
| **Atteso** | 1. Codice 404 e `detail` "Reparto non trovato". |

**TC-M05 — Stato non valido**

| Campo | Contenuto |
|---|---|
| **Precondizione** | Esiste un reparto. |
| **Passi** | 1. `POST /macchinari` con `"stato": "rotto"` (altri campi validi). |
| **Atteso** | 1. Codice 422; l'errore indica che i valori ammessi sono "attivo", "fermo" e "dismesso". |

**TC-M06 — Campi obbligatori mancanti**

| Campo | Contenuto |
|---|---|
| **Precondizione** | Nessuna. |
| **Passi** | 1. `POST /macchinari` con `{"matricola": "M-9"}`. |
| **Atteso** | 1. Codice 422; gli errori indicano `nome` e `reparto_id` mancanti. |

**TC-M07 — Elenco dei macchinari**

| Campo | Contenuto |
|---|---|
| **Precondizione** | Esistono i macchinari di TC-M01 e TC-M02. |
| **Passi** | 1. `GET /macchinari`. |
| **Atteso** | 1. Codice 200 e un elenco che contiene tutti i macchinari creati. |

**TC-M08 — Filtro per reparto**

| Campo | Contenuto |
|---|---|
| **Precondizione** | Esistono due reparti (A e B). Il reparto A ha almeno un macchinario, il reparto B ne ha almeno uno diverso. |
| **Passi** | 1. `GET /macchinari?reparto_id={A}`. |
| **Atteso** | 1. Codice 200; l'elenco contiene solo i macchinari del reparto A e nessuno del reparto B. |

**TC-M09 — Filtro per reparto senza macchinari o inesistente**

| Campo | Contenuto |
|---|---|
| **Precondizione** | Esiste un reparto senza macchinari. Non esiste un reparto con id 999999. |
| **Passi** | 1. `GET /macchinari?reparto_id={reparto senza macchinari}`. 2. `GET /macchinari?reparto_id=999999`. |
| **Atteso** | 1. e 2. Codice 200 e corpo `[]` (non 404). |

**TC-M10 — Filtro per reparto non numerico**

| Campo | Contenuto |
|---|---|
| **Precondizione** | Nessuna. |
| **Passi** | 1. `GET /macchinari?reparto_id=abc`. |
| **Atteso** | 1. Codice 422. |

**TC-M11 — Lettura di un macchinario per id**

| Campo | Contenuto |
|---|---|
| **Precondizione** | Esiste il macchinario di TC-M01. |
| **Passi** | 1. `GET /macchinari/{id}`. |
| **Atteso** | 1. Codice 200 e corpo con tutti i campi del macchinario. |

**TC-M12 — Lettura di un macchinario inesistente o con id non numerico**

| Campo | Contenuto |
|---|---|
| **Precondizione** | Non esiste un macchinario con id 999999. |
| **Passi** | 1. `GET /macchinari/999999`. 2. `GET /macchinari/abc`. |
| **Atteso** | 1. Codice 404 e `detail` "Macchinario non trovato". 2. Codice 422. |

### TC-T — Tecnici

**TC-T01 — Creazione di un tecnico con specializzazione**

| Campo | Contenuto |
|---|---|
| **Precondizione** | Non esiste un tecnico con codice "T1". |
| **Passi** | 1. `POST /tecnici` con `{"codice_dipendente": "T1", "nome": "Luca", "cognome": "Rossi", "specializzazione": "meccanica"}`. |
| **Atteso** | 1. Codice 201; `attivo` `true`; `specializzazione` "meccanica". |

**TC-T02 — Creazione di un tecnico senza specializzazione**

| Campo | Contenuto |
|---|---|
| **Precondizione** | Non esiste un tecnico con codice "T2". |
| **Passi** | 1. `POST /tecnici` con `{"codice_dipendente": "T2", "nome": "Anna", "cognome": "Verdi"}`. |
| **Atteso** | 1. Codice 201; `specializzazione` `null`; `attivo` `true`. |

**TC-T03 — Codice dipendente già usato**

| Campo | Contenuto |
|---|---|
| **Precondizione** | Esiste il tecnico "T1" (TC-T01). |
| **Passi** | 1. `POST /tecnici` con `codice_dipendente` "T1" (altri campi validi). |
| **Atteso** | 1. Codice 409 e `detail` "Esiste già un tecnico con questo codice". |

**TC-T04 — Campi obbligatori mancanti**

| Campo | Contenuto |
|---|---|
| **Precondizione** | Nessuna. |
| **Passi** | 1. `POST /tecnici` con `{"codice_dipendente": "T5"}`. |
| **Atteso** | 1. Codice 422; gli errori indicano `nome` e `cognome` mancanti. |

**TC-T05 — Specializzazione non valida (limite noto)**

| Campo | Contenuto |
|---|---|
| **Precondizione** | Non esiste un tecnico con codice "T3". |
| **Passi** | 1. `POST /tecnici` con `"specializzazione": "magia"` (altri campi validi). 2. Ripetere con `"specializzazione": ""` e codice "T4". |
| **Atteso** | 1. e 2. Codice 500: il vincolo CHECK del database rifiuta il valore e l'errore non è tradotto. Nessun tecnico creato. Comportamento da correggere in fase 2 (vedi sezione 4). |

**TC-T06 — Elenco dei tecnici**

| Campo | Contenuto |
|---|---|
| **Precondizione** | Esistono i tecnici di TC-T01 e TC-T02. |
| **Passi** | 1. `GET /tecnici`. |
| **Atteso** | 1. Codice 200; l'elenco contiene tutti i tecnici, senza filtro su `attivo`. |

**TC-T07 — Filtro per tecnici attivi e non attivi**

| Campo | Contenuto |
|---|---|
| **Precondizione** | Esistono tecnici con `attivo` `true`. Nessuna rotta consente di disattivare un tecnico: per avere un tecnico non attivo occorre modificare il campo direttamente nel database di test. |
| **Passi** | 1. `GET /tecnici?attivo=true`. 2. `GET /tecnici?attivo=false`. |
| **Atteso** | 1. Codice 200; solo tecnici con `attivo` `true`. 2. Codice 200; solo tecnici con `attivo` `false`, oppure `[]` se non ne esistono. |

**TC-T08 — Filtro `attivo` non booleano**

| Campo | Contenuto |
|---|---|
| **Precondizione** | Nessuna. |
| **Passi** | 1. `GET /tecnici?attivo=boh`. |
| **Atteso** | 1. Codice 422; l'errore riguarda il parametro `attivo`. |

### TC-G — Guasti

**TC-G01 — Segnalazione di un guasto**

| Campo | Contenuto |
|---|---|
| **Precondizione** | Esiste un macchinario (id `{macchinario}`). |
| **Passi** | 1. `POST /guasti` con `{"macchinario_id": {macchinario}, "descrizione": "Perdita olio", "priorita": "alta", "segnalato_da": "Mario"}`. |
| **Atteso** | 1. Codice 201; `stato` "aperto"; `data_segnalazione` valorizzata dal database; `data_chiusura` `null`. |

**TC-G02 — Guasto su macchinario inesistente**

| Campo | Contenuto |
|---|---|
| **Precondizione** | Non esiste un macchinario con id 999999. |
| **Passi** | 1. `POST /guasti` con `macchinario_id` 999999 e gli altri campi validi. |
| **Atteso** | 1. Codice 404 e `detail` "Macchinario non trovato". |

**TC-G03 — Campi obbligatori mancanti**

| Campo | Contenuto |
|---|---|
| **Precondizione** | Esiste un macchinario. |
| **Passi** | 1. `POST /guasti` senza il campo `priorita`. |
| **Atteso** | 1. Codice 422; l'errore indica `priorita` mancante. |

**TC-G04 — Priorità non valida (limite noto)**

| Campo | Contenuto |
|---|---|
| **Precondizione** | Esiste un macchinario. |
| **Passi** | 1. `POST /guasti` con `"priorita": "urgentissima"` (altri campi validi). |
| **Atteso** | 1. Codice 500: il vincolo CHECK del database rifiuta il valore e l'errore viene rilanciato. Nessun guasto creato. Comportamento da correggere in fase 2 (vedi sezione 4). |

**TC-G05 — Elenco dei guasti**

| Campo | Contenuto |
|---|---|
| **Precondizione** | Esiste almeno un guasto (TC-G01). |
| **Passi** | 1. `GET /guasti`. |
| **Atteso** | 1. Codice 200 e un elenco che contiene i guasti creati. |

**TC-G06 — Filtro per macchinario**

| Campo | Contenuto |
|---|---|
| **Precondizione** | Esistono due macchinari (A e B), ciascuno con almeno un guasto. |
| **Passi** | 1. `GET /guasti?macchinario_id={A}`. |
| **Atteso** | 1. Codice 200; l'elenco contiene solo i guasti del macchinario A. |

**TC-G07 — Filtro per macchinario senza guasti o inesistente**

| Campo | Contenuto |
|---|---|
| **Precondizione** | Esiste un macchinario senza guasti. Non esiste un macchinario con id 999999. |
| **Passi** | 1. `GET /guasti?macchinario_id={macchinario senza guasti}`. 2. `GET /guasti?macchinario_id=999999`. 3. `GET /guasti?macchinario_id=abc`. |
| **Atteso** | 1. e 2. Codice 200 e `[]` (non 404). 3. Codice 422. |

**TC-G08 — Passaggio del guasto in lavorazione**

| Campo | Contenuto |
|---|---|
| **Precondizione** | Esiste un guasto con stato "aperto" (TC-G01). |
| **Passi** | 1. `PATCH /guasti/{id}` con `{"stato": "in_lavorazione"}`. |
| **Atteso** | 1. Codice 200; `stato` "in_lavorazione"; `data_chiusura` `null`. |

**TC-G09 — Chiusura di un guasto senza ordini di lavoro**

| Campo | Contenuto |
|---|---|
| **Precondizione** | Esiste un guasto senza ordini di lavoro collegati. |
| **Passi** | 1. `PATCH /guasti/{id}` con `{"stato": "risolto"}`. |
| **Atteso** | 1. Codice 200; `stato` "risolto"; `data_chiusura` valorizzata. |

**TC-G10 — Chiusura bloccata da un ordine di lavoro aperto**

| Campo | Contenuto |
|---|---|
| **Precondizione** | Esiste un guasto con un ordine di lavoro collegato in stato diverso da "completato" e "annullato" (creato come in TC-O03). |
| **Passi** | 1. `PATCH /guasti/{id}` con `{"stato": "risolto"}`. 2. `PATCH /guasti/{id}` con `{"stato": "annullato"}`. 3. Leggere il guasto con `GET /guasti?macchinario_id={macchinario}`. |
| **Atteso** | 1. e 2. Codice 409 e `detail` "Il guasto ha ordini di lavoro aperti". 3. Lo stato del guasto è invariato e `data_chiusura` è `null`. |

**TC-G11 — Chiusura consentita quando gli ordini sono completati o annullati**

| Campo | Contenuto |
|---|---|
| **Precondizione** | Esiste un guasto i cui ordini collegati sono tutti in stato "completato" o "annullato" (si può partire dal guasto di TC-G10 portando a "completato" l'ordine collegato con `PATCH /ordini-lavoro/{id}`, come in TC-O13). |
| **Passi** | 1. `PATCH /guasti/{id}` con `{"stato": "risolto"}`. |
| **Atteso** | 1. Codice 200; `stato` "risolto"; `data_chiusura` valorizzata. |

**TC-G12 — Stato non valido**

| Campo | Contenuto |
|---|---|
| **Precondizione** | Esiste un guasto. |
| **Passi** | 1. `PATCH /guasti/{id}` con `{"stato": "boh"}`. 2. `PATCH /guasti/{id}` con `{}`. |
| **Atteso** | 1. Codice 422 e `detail` "Stato non valido"; lo stato del guasto è invariato. 2. Codice 422; l'errore indica `stato` mancante. |

**TC-G13 — Aggiornamento di un guasto inesistente**

| Campo | Contenuto |
|---|---|
| **Precondizione** | Non esiste un guasto con id 999999. |
| **Passi** | 1. `PATCH /guasti/999999` con `{"stato": "risolto"}`. |
| **Atteso** | 1. Codice 404 e `detail` "Guasto non trovato". |

**TC-G14 — Riapertura di un guasto chiuso (limite noto)**

| Campo | Contenuto |
|---|---|
| **Precondizione** | Esiste un guasto in stato "risolto" con `data_chiusura` valorizzata (TC-G09). |
| **Passi** | 1. `PATCH /guasti/{id}` con `{"stato": "in_lavorazione"}`. |
| **Atteso** | 1. Codice 200; `stato` "in_lavorazione"; `data_chiusura` **resta valorizzata**. Nessun controllo sulle transizioni di stato (vedi sezione 4). |

### TC-O — Ordini di lavoro

**TC-O01 — Creazione di un ordine senza tecnico**

| Campo | Contenuto |
|---|---|
| **Precondizione** | Esiste un macchinario (id `{macchinario}`). |
| **Passi** | 1. `POST /ordini-lavoro` con `{"macchinario_id": {macchinario}, "descrizione": "Sostituire guarnizione"}`. |
| **Atteso** | 1. Codice 201; `stato` "da_assegnare"; `guasto_id`, `tecnico_id`, `data_pianificata`, `data_completamento` ed `esito` `null`; `data_creazione` valorizzata. |

**TC-O02 — Creazione di un ordine con tecnico**

| Campo | Contenuto |
|---|---|
| **Precondizione** | Esistono un macchinario e un tecnico (id `{tecnico}`). |
| **Passi** | 1. `POST /ordini-lavoro` con `{"macchinario_id": {macchinario}, "tecnico_id": {tecnico}, "descrizione": "Riparare"}`. |
| **Atteso** | 1. Codice 201; `stato` "assegnato"; `tecnico_id` uguale a `{tecnico}`. |

**TC-O03 — Creazione di un ordine collegato a un guasto**

| Campo | Contenuto |
|---|---|
| **Precondizione** | Esiste un guasto (id `{guasto}`) sul macchinario `{macchinario}`. |
| **Passi** | 1. `POST /ordini-lavoro` con `{"macchinario_id": {macchinario}, "guasto_id": {guasto}, "descrizione": "Riparare", "data_pianificata": "2026-12-01T09:00:00Z"}`. |
| **Atteso** | 1. Codice 201; `guasto_id` uguale a `{guasto}`; `data_pianificata` valorizzata; `stato` "da_assegnare". |

**TC-O04 — Macchinario inesistente**

| Campo | Contenuto |
|---|---|
| **Precondizione** | Non esiste un macchinario con id 999999. |
| **Passi** | 1. `POST /ordini-lavoro` con `macchinario_id` 999999 e `descrizione` valida. |
| **Atteso** | 1. Codice 404 e `detail` "Macchinario non trovato". |

**TC-O05 — Guasto inesistente**

| Campo | Contenuto |
|---|---|
| **Precondizione** | Esiste un macchinario. Non esiste un guasto con id 999999. |
| **Passi** | 1. `POST /ordini-lavoro` con `guasto_id` 999999. |
| **Atteso** | 1. Codice 404 e `detail` "Guasto non trovato". |

**TC-O06 — Tecnico inesistente**

| Campo | Contenuto |
|---|---|
| **Precondizione** | Esiste un macchinario. Non esiste un tecnico con id 999999. |
| **Passi** | 1. `POST /ordini-lavoro` con `tecnico_id` 999999. |
| **Atteso** | 1. Codice 404 e `detail` "Tecnico non trovato". |

**TC-O07 — Guasto di un altro macchinario**

| Campo | Contenuto |
|---|---|
| **Precondizione** | Esistono due macchinari (A e B) e un guasto sul macchinario A. |
| **Passi** | 1. `POST /ordini-lavoro` con `macchinario_id` B e `guasto_id` del guasto di A. |
| **Atteso** | 1. Codice 409 e `detail` "Il guasto non corrisponde al macchinario". Nessun ordine creato. |

**TC-O08 — Campi non validi o mancanti**

| Campo | Contenuto |
|---|---|
| **Precondizione** | Esiste un macchinario. |
| **Passi** | 1. `POST /ordini-lavoro` con `{"macchinario_id": {macchinario}}` (senza `descrizione`). 2. `POST /ordini-lavoro` con `data_pianificata` "non-una-data". |
| **Atteso** | 1. Codice 422; l'errore indica `descrizione` mancante. 2. Codice 422; l'errore riguarda `data_pianificata`. |

**TC-O09 — Elenco degli ordini di lavoro**

| Campo | Contenuto |
|---|---|
| **Precondizione** | Esistono gli ordini di TC-O01 e TC-O02. |
| **Passi** | 1. `GET /ordini-lavoro`. |
| **Atteso** | 1. Codice 200 e un elenco che contiene tutti gli ordini creati. |

**TC-O10 — Filtro per stato**

| Campo | Contenuto |
|---|---|
| **Precondizione** | Esiste almeno un ordine "da_assegnare" e almeno uno "assegnato". |
| **Passi** | 1. `GET /ordini-lavoro?stato=assegnato`. |
| **Atteso** | 1. Codice 200; l'elenco contiene solo ordini "assegnato" e nessuno "da_assegnare". |

**TC-O11 — Filtro con stato non valido (limite noto)**

| Campo | Contenuto |
|---|---|
| **Precondizione** | Nessuna. |
| **Passi** | 1. `GET /ordini-lavoro?stato=boh`. |
| **Atteso** | 1. Codice 200 e `[]`: il valore non viene validato (vedi sezione 4). |

**TC-O12 — Passaggio dell'ordine in corso**

| Campo | Contenuto |
|---|---|
| **Precondizione** | Esiste un ordine "assegnato" (TC-O02). |
| **Passi** | 1. `PATCH /ordini-lavoro/{id}` con `{"stato": "in_corso"}`. |
| **Atteso** | 1. Codice 200; `stato` "in_corso"; `data_completamento` `null`. |

**TC-O13 — Completamento dell'ordine**

| Campo | Contenuto |
|---|---|
| **Precondizione** | Esiste un ordine "in_corso" (TC-O12). |
| **Passi** | 1. `PATCH /ordini-lavoro/{id}` con `{"stato": "completato"}`. |
| **Atteso** | 1. Codice 200; `stato` "completato"; `data_completamento` valorizzata. |

**TC-O14 — Annullamento dell'ordine**

| Campo | Contenuto |
|---|---|
| **Precondizione** | Esiste un ordine "da_assegnare" (TC-O01). |
| **Passi** | 1. `PATCH /ordini-lavoro/{id}` con `{"stato": "annullato"}`. |
| **Atteso** | 1. Codice 200; `stato` "annullato"; `data_completamento` `null`. |

**TC-O15 — Stato non valido**

| Campo | Contenuto |
|---|---|
| **Precondizione** | Esiste un ordine. |
| **Passi** | 1. `PATCH /ordini-lavoro/{id}` con `{"stato": "volando"}`. 2. `PATCH /ordini-lavoro/{id}` con `{}`. |
| **Atteso** | 1. Codice 422 e `detail` "Stato non valido"; lo stato dell'ordine è invariato. 2. Codice 422; l'errore indica `stato` mancante. |

**TC-O16 — Aggiornamento di un ordine inesistente**

| Campo | Contenuto |
|---|---|
| **Precondizione** | Non esiste un ordine con id 999999. |
| **Passi** | 1. `PATCH /ordini-lavoro/999999` con `{"stato": "in_corso"}`. |
| **Atteso** | 1. Codice 404 e `detail` "L'ordine non esiste". |

**TC-O17 — Transizioni di stato senza controllo (limite noto)**

| Campo | Contenuto |
|---|---|
| **Precondizione** | Esiste un ordine "completato" con `data_completamento` valorizzata (TC-O13). |
| **Passi** | 1. `PATCH /ordini-lavoro/{id}` con `{"stato": "da_assegnare"}`. 2. Riportare l'ordine a "completato" con `PATCH` e confrontare `data_completamento` con il valore del passo precedente. |
| **Atteso** | 1. Codice 200; `stato` "da_assegnare"; `data_completamento` **resta valorizzata**. 2. Codice 200; `data_completamento` viene **sovrascritta** con la data del nuovo completamento. Nessun controllo sulle transizioni (vedi sezione 4). |

## 3. Test automatici

Non ancora presenti. I test automatici con pytest sono previsti nella fase 2 (qualità e sicurezza) e verranno descritti in questa sezione, un file di test alla volta, nel formato seguente.

File: `tests/test_xxx.py`

| Test | Scenario |
|---|---|
| `nome_test_che_descrive_la_regola` | Condizione → risultato atteso |

Fino ad allora la verifica è solo manuale, con i casi della sezione 2.

## 4. Note per il tester

**Fuori dal perimetro**
- Autenticazione e autorizzazione: non implementate (fase 2).
- Ricerca nei manuali (RAG) e agente: non implementati (fasi 3 e 4).
- Test di carico, concorrenza e sicurezza. In particolare non sono coperti i rami di gestione degli errori del database che scattano solo se un record viene eliminato tra il controllo e il salvataggio (stato di competizione tra richieste).

**Limiti noti: il comportamento attuale non è quello definitivo**
- **Valori non validati in ingresso → 500.** Una priorità di guasto non valida (TC-G04) o una specializzazione di tecnico non valida o vuota (TC-T05) superano la validazione dei dati e vengono rifiutate dal vincolo CHECK del database, che produce un errore 500. La validazione con tipi a valori ammessi è prevista in fase 2 (restituirà 422).
- **Filtri non validati.** `GET /ordini-lavoro?stato=...` con uno stato inesistente risponde 200 con elenco vuoto (TC-O11).
- **Nessun controllo sulle transizioni di stato.** `PATCH` su guasti e ordini accetta qualunque stato valido a partire da qualunque stato. Le date restano valorizzate quando lo stato torna indietro: `data_chiusura` del guasto dopo una riapertura (TC-G14) e `data_completamento` dell'ordine dopo un ritorno a "da_assegnare"; un nuovo completamento sovrascrive la data (TC-O17).
- **Coerenza stato/date.** Il database non verifica che le date siano coerenti con lo stato: la coerenza è affidata alle rotte.
- **Nomi vuoti.** Il nome di un reparto e la descrizione di un macchinario accettano la stringa vuota (`POST /reparti` con `{"nome": ""}` risponde 201).
- **Tecnici non attivi.** `POST /ordini-lavoro` accetta anche un tecnico con `attivo` `false`. Non esiste una rotta per disattivare un tecnico.
- **Ordine degli elenchi.** Nessun elenco ha un ordinamento esplicito: l'ordine dei risultati non è garantito e i casi non devono dipendere da esso.
- **Altri errori di integrità in `POST /macchinari`.** Qualunque violazione di integrità diversa dalla chiave esterna del reparto viene riportata come 409 "matricola già usata".
- **Identificativi non consecutivi.** Un inserimento fallito (409 o 500) consuma comunque un numero della sequenza degli identificativi, quindi dopo i casi negativi compaiono "buchi" negli `id`. Non è un difetto.
- **Documentazione OpenAPI.** Le risposte 404, 409 e 422 non sono ancora dichiarate nella documentazione interattiva (`/docs`): compaiono solo nelle docstring e nel comportamento reale.

**Verifiche sul database dopo una sessione**
- Nessun record creato dai casi negativi (409, 422, 500, 404): ad esempio dopo TC-R04 deve esistere un solo reparto "Pressatura", dopo TC-G04 e TC-T05 nessun guasto o tecnico con i valori non validi.
- Ogni `ordine_lavoro` con `guasto_id` valorizzato ha lo stesso `macchinario_id` del guasto.
- Nessun guasto "risolto" o "annullato" con ordini di lavoro ancora aperti, se creati solo tramite l'API.

**Log**
- L'applicazione scrive nel terminale in cui gira `uvicorn`, comprese le istruzioni SQL (l'engine ha `echo` attivo). In caso di 500 la traccia dell'eccezione è lì.

**Ordine di esecuzione consigliato**
1. TC-A (applicazione attiva) e TC-R (i reparti servono ai macchinari).
2. TC-M (i macchinari servono a guasti e ordini).
3. TC-T (i tecnici servono agli ordini assegnati).
4. TC-G dal 01 al 07 (creazione e lettura dei guasti).
5. TC-O dal 01 all'11 (creazione e lettura degli ordini).
6. TC-G08-G09 e TC-O12-O17, poi TC-G10, TC-G11 e TC-G14 (aggiornamenti di stato; TC-G10 e TC-G11 richiedono l'ordine di TC-O03).
7. I casi di limiti noti (TC-G04, TC-T05, TC-O11) in qualunque momento: non cambiano i dati.

## 5. Tracciamento dell'esito

Per ogni caso eseguito, registrare:

| Campo | Contenuto |
|---|---|
| ID test | es. TC-O03 |
| Esito | PASS / FAIL / BLOCKED / N.A. |
| Data e ora | es. 2026-11-12 14:35 |
| Evidenza | Richiesta e risposta, oppure screenshot |
| Errori | Codice di stato, messaggio, riga di log |
| Riferimento ai dati | ID dei record coinvolti (utile per il debug sul database) |
| Note | Differenze rispetto all'atteso, soluzioni temporanee |

In caso di **FAIL** indicare sempre: richiesta esatta, risposta ricevuta (codice e corpo), eventuali errori nei log.

Tabella degli esiti. Le prove manuali sono state eseguite durante lo sviluppo di ciascuna rotta; data e ora e riferimenti ai dati non sono stati registrati. Da compilare per intero a ogni sessione successiva:

| ID test | Esito | Data e ora | Evidenza | Errori | Riferimento ai dati | Note |
|---|---|---|---|---|---|---|
| TC-A01 | PASS | | Prova manuale |  | | Provato durante lo sviluppo della rotta |
| TC-R01 | PASS | | Prova manuale |  | | Provato durante lo sviluppo della rotta |
| TC-R02 | PASS | | Prova manuale |  | | Provato durante lo sviluppo della rotta |
| TC-R03 | PASS | | Prova manuale |  | | Provato durante lo sviluppo della rotta |
| TC-R04 | PASS | | Prova manuale |  | | Provato durante lo sviluppo della rotta |
| TC-R05 | PASS | | Prova manuale |  | | Provato durante lo sviluppo della rotta |
| TC-R06 | PASS | | Prova manuale |  | | Provato durante lo sviluppo della rotta |
| TC-R07 | PASS | | Prova manuale |  | | Provato durante lo sviluppo della rotta |
| TC-R08 | PASS | | Prova manuale |  | | Provato durante lo sviluppo della rotta |
| TC-M01 | PASS | | Prova manuale |  | | Provato durante lo sviluppo della rotta |
| TC-M02 | PASS | | Prova manuale |  | | Provato durante lo sviluppo della rotta |
| TC-M03 | PASS | | Prova manuale |  | | Provato durante lo sviluppo della rotta |
| TC-M04 | PASS | | Prova manuale |  | | Provato durante lo sviluppo della rotta |
| TC-M05 | PASS | | Prova manuale |  | | Provato durante lo sviluppo della rotta |
| TC-M06 | PASS | | Prova manuale |  | | Provato durante lo sviluppo della rotta |
| TC-M07 | PASS | | Prova manuale |  | | Provato durante lo sviluppo della rotta |
| TC-M08 | PASS | | Prova manuale |  | | Provato durante lo sviluppo della rotta |
| TC-M09 | PASS | | Prova manuale |  | | Provato durante lo sviluppo della rotta |
| TC-M10 | PASS | | Prova manuale |  | | Provato durante lo sviluppo della rotta |
| TC-M11 | PASS | | Prova manuale |  | | Provato durante lo sviluppo della rotta |
| TC-M12 | PASS | | Prova manuale |  | | Provato durante lo sviluppo della rotta |
| TC-T01 | PASS | | Prova manuale |  | | Provato durante lo sviluppo della rotta |
| TC-T02 | PASS | | Prova manuale |  | | Provato durante lo sviluppo della rotta |
| TC-T03 | PASS | | Prova manuale |  | | Provato durante lo sviluppo della rotta |
| TC-T04 | PASS | | Prova manuale |  | | Provato durante lo sviluppo della rotta |
| TC-T05 | PASS | | Prova manuale | 500 (atteso, limite noto) | | Provato durante lo sviluppo della rotta |
| TC-T06 | PASS | | Prova manuale |  | | Provato durante lo sviluppo della rotta |
| TC-T07 | PASS | | Prova manuale |  | | Provato durante lo sviluppo della rotta |
| TC-T08 | PASS | | Prova manuale |  | | Provato durante lo sviluppo della rotta |
| TC-G01 | PASS | | Prova manuale |  | | Provato durante lo sviluppo della rotta |
| TC-G02 | PASS | | Prova manuale |  | | Provato durante lo sviluppo della rotta |
| TC-G03 | PASS | | Prova manuale |  | | Provato durante lo sviluppo della rotta |
| TC-G04 | PASS | | Prova manuale | 500 (atteso, limite noto) | | Provato durante lo sviluppo della rotta |
| TC-G05 | PASS | | Prova manuale |  | | Provato durante lo sviluppo della rotta |
| TC-G06 | PASS | | Prova manuale |  | | Provato durante lo sviluppo della rotta |
| TC-G07 | PASS | | Prova manuale |  | | Provato durante lo sviluppo della rotta |
| TC-G08 | PASS | | Prova manuale |  | | Provato durante lo sviluppo della rotta |
| TC-G09 | PASS | | Prova manuale |  | | Provato durante lo sviluppo della rotta |
| TC-G10 | PASS | | Prova manuale |  | | Provato durante lo sviluppo della rotta |
| TC-G11 | PASS | | Prova manuale |  | | Provato durante lo sviluppo della rotta |
| TC-G12 | PASS | | Prova manuale |  | | Provato durante lo sviluppo della rotta |
| TC-G13 | PASS | | Prova manuale |  | | Provato durante lo sviluppo della rotta |
| TC-G14 | PASS | | Prova manuale |  | | Provato durante lo sviluppo della rotta |
| TC-O01 | PASS | | Prova manuale |  | | Provato durante lo sviluppo della rotta |
| TC-O02 | PASS | | Prova manuale |  | | Provato durante lo sviluppo della rotta |
| TC-O03 | PASS | | Prova manuale |  | | Provato durante lo sviluppo della rotta |
| TC-O04 | PASS | | Prova manuale |  | | Provato durante lo sviluppo della rotta |
| TC-O05 | PASS | | Prova manuale |  | | Provato durante lo sviluppo della rotta |
| TC-O06 | PASS | | Prova manuale |  | | Provato durante lo sviluppo della rotta |
| TC-O07 | PASS | | Prova manuale |  | | Provato durante lo sviluppo della rotta |
| TC-O08 | PASS | | Prova manuale |  | | Provato durante lo sviluppo della rotta |
| TC-O09 | PASS | | Prova manuale |  | | Provato durante lo sviluppo della rotta |
| TC-O10 | PASS | | Prova manuale |  | | Provato durante lo sviluppo della rotta |
| TC-O11 | PASS | | Prova manuale |  | | Provato durante lo sviluppo della rotta |
| TC-O12 | PASS | | Prova manuale |  | | Provato durante lo sviluppo della rotta |
| TC-O13 | PASS | | Prova manuale |  | | Provato durante lo sviluppo della rotta |
| TC-O14 | PASS | | Prova manuale |  | | Provato durante lo sviluppo della rotta |
| TC-O15 | PASS | | Prova manuale |  | | Provato durante lo sviluppo della rotta |
| TC-O16 | PASS | | Prova manuale |  | | Provato durante lo sviluppo della rotta |
| TC-O17 | PASS | | Prova manuale |  | | Provato durante lo sviluppo della rotta |
