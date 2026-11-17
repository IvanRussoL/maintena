""" Test delle rotte /reparti (casi TC-R di docs/PIANO_TEST.md)"""

def crea_reparto(client, nome, descrizione=None):
    """
    Crea un reparto via API; la descrizione si invia solo se presente.
    """
    corpo = {"nome": nome}
    if descrizione is not None:
        corpo["descrizione"] = descrizione
    return client.post("/reparti", json=corpo)


def test_TC_R01_elenco_vuoto(client):
    # DB di test vuoto: la lista dei reparti è vuota.
    risposta = client.get("/reparti")
    assert risposta.status_code == 200
    assert risposta.json() == []


def test_TC_R02_crea_reparto(client):
    # Senza descrizione il campo torna None.
    risposta = crea_reparto(client, "Pressatura")
    assert risposta.status_code == 201
    corpo = risposta.json()
    assert "id" in corpo
    assert corpo["nome"] == "Pressatura"
    assert corpo["descrizione"] is None
    elenco = client.get("/reparti").json()
    assert "Pressatura" in [r["nome"] for r in elenco]


def test_TC_R03_crea_reparto_con_descrizione(client):
    # Con descrizione: il campo torna valorizzato.
    risposta = crea_reparto(client, "Montaggio", "Linea 2")
    assert risposta.status_code == 201
    assert risposta.json()["descrizione"] == "Linea 2"


def test_TC_R04_nome_doppio(client):
    # Primo inserimento: deve riuscire.
    crea_reparto(client, "Pressatura")
    # Secondo con lo stesso nome: il vincolo unique deve bloccarlo.
    risposta = crea_reparto(client, "Pressatura")
    assert risposta.status_code == 409
    assert "detail" in risposta.json()
    elenco = client.get("/reparti").json()
    assert len(elenco) == 1


def test_TC_R05_reparto_senza_nome(client):
    # Corpo vuoto: Pydantic rifiuta prima di arrivare al DB.
    risposta = client.post("/reparti", json={})
    assert risposta.status_code == 422
    assert client.get("/reparti").json() == []


def test_TC_R06_leggi_reparto_per_id(client):
    # Riusiamo l'id restituito dalla creazione.
    reparto_id = crea_reparto(client, "Pressatura").json()["id"]
    risposta = client.get(f"/reparti/{reparto_id}")
    assert risposta.status_code == 200
    assert risposta.json()["nome"] == "Pressatura"


def test_TC_R07_reparto_inesistente(client):
    # DB vuoto: nessun reparto con id 999999.
    risposta = client.get("/reparti/999999")
    assert risposta.status_code == 404


def test_TC_R08_id_non_numerico(client):
    # "abc" non è un intero: errore di validazione del percorso.
    risposta = client.get("/reparti/abc")
    assert risposta.status_code == 422