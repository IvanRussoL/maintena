import pytest
from sqlalchemy.exc import IntegrityError

def crea_reparto(client, nome="Stampaggio"):
    risposta = client.post("/reparti", json={"nome": nome})
    assert risposta.status_code == 201
    return risposta.json()["id"]


def crea_macchinario(client, matricola, reparto_id, nome="Pressa"):
    risposta = client.post("/macchinari", json={
        "matricola": matricola,
        "reparto_id": reparto_id,
        "nome": nome
    })
    assert risposta.status_code == 201
    return risposta.json()["id"]


def crea_guasto(client, macchinario_id, priorita="alta"):
    risposta = client.post("/guasti", json={
        "macchinario_id": macchinario_id,
        "descrizione": "Perdita olio",
        "priorita": priorita,
        "segnalato_da": "Mario",
    })
    assert risposta.status_code == 201
    return risposta.json()


# POST /guasti

def test_TC_G01_segnalazione_guasto(client):
    reparto_id = crea_reparto(client, "Pressatura")
    macchinario_id = crea_macchinario(client, "M-1", reparto_id)
    corpo = {
        "macchinario_id": macchinario_id,
        "descrizione": "Perdita olio",
        "priorita": "alta",
        "segnalato_da": "Marco"
        }

    risposta = client.post("/guasti", json=corpo)

    assert risposta.status_code == 201
    assert risposta.json()["stato"] == "aperto"
    assert risposta.json()["data_segnalazione"] is not None
    assert risposta.json()["data_chiusura"] is None


def test_TC_G02_macchinario_inesistente(client):
    risposta = client.post("/guasti", json={
        "macchinario_id": 999999,
        "descrizione": "Perdita d'olio",
        "priorita": "alta",
        "segnalato_da": "Mario",
    })

    assert risposta.status_code == 404
    assert risposta.json()["detail"] == "Macchinario non trovato"


def test_TC_G03_campi_obbligatori_mancanti(client):
    reparto_id = crea_reparto(client)
    macchinario_id = crea_macchinario(client, "M-1", reparto_id)
    risposta = client.post("/guasti", json={
        "macchinario_id": macchinario_id,
        "descrizione": "Perdita olio",
        "segnalato_da": "Mario",
    })

    assert risposta.status_code == 422
    assert risposta.json()["detail"][0]["loc"] == ["body", "priorita"]


def test_TC_G04_priorita_non_valida(client):
    reparto_id = crea_reparto(client)
    macchinario_id = crea_macchinario(client, "M-1", reparto_id)

    with pytest.raises(IntegrityError):
        client.post("/guasti", json={
            "macchinario_id": macchinario_id,
            "descrizione": "Perdita olio",
            "priorita": "urgentissima",
            "segnalato_da": "Mario",
        })

    elenco = client.get("/guasti", params={
        "macchinario_id": macchinario_id,
    }).json()

    assert elenco == []


# GET /guasti

def test_TC_G05_elenco_guasti(client):
    reparto_id = crea_reparto(client)
    macchinario_id = crea_macchinario(client, "M-1", reparto_id)
    guasto = crea_guasto(client, macchinario_id)

    risposta = client.get("/guasti")

    assert risposta.status_code == 200
    ids = [g["id"] for g in risposta.json()]
    assert guasto["id"] in ids


def test_TC_G06_filtro_per_macchinario(client):
    reparto_id = crea_reparto(client)
    macchinario_A = crea_macchinario(client, "M-A", reparto_id)
    macchinario_B = crea_macchinario(client, "M-B", reparto_id)

    guasto_A = crea_guasto(client, macchinario_A)
    guasto_B = crea_guasto(client, macchinario_B)

    risposta = client.get("/guasti", params={"macchinario_id": macchinario_A})

    assert risposta.status_code == 200
    ids = [g["id"] for g in risposta.json()]
    assert guasto_A["id"] in ids
    assert guasto_B["id"] not in ids


def test_TC_G07_filtro_senza_guasti_o_inesistente(client):
    reparto_id = crea_reparto(client)
    macchinario_vuoto = crea_macchinario(client, "M-A", reparto_id) 

    risposta_a = client.get("/guasti", params={"macchinario_id": macchinario_vuoto})

    assert risposta_a.status_code == 200
    assert risposta_a.json() == []

    risposta_b = client.get("/guasti", params={"macchinario_id": 999999})

    assert risposta_b.status_code == 200
    assert risposta_b.json() == []

    risposta_c = client.get("/guasti", params={"macchinario_id": "abc"})

    assert risposta_c.status_code == 422


def test_TC_G08_in_lavorazione(client):
    reparto_id = crea_reparto(client)
    macchinario_id = crea_macchinario(client, "M-1", reparto_id)
    guasto = crea_guasto(client, macchinario_id)

    risposta = client.patch(f"/guasti/{guasto['id']}", json={
        "stato": "in_lavorazione",
    })

    assert risposta.status_code == 200
    dati = risposta.json()
    assert dati["stato"] == "in_lavorazione"
    assert dati["data_chiusura"] is None


def test_TC_G09_risolto_senza_ordini(client):
    reparto_id = crea_reparto(client)
    macchinario_id = crea_macchinario(client, "M-1", reparto_id)
    guasto = crea_guasto(client, macchinario_id)

    risposta = client.patch(f"/guasti/{guasto['id']}", json={
        "stato": "risolto",
    })

    assert risposta.status_code == 200
    assert risposta.json()["stato"] == "risolto"
    assert risposta.json()["data_chiusura"] is not None


# TC-G10, TC-G11: serve un ordine di lavoro, rinviati.

def test_TC_G12_stato_non_valido(client):
    reparto_id = crea_reparto(client)
    macchinario_id = crea_macchinario(client, "M-1", reparto_id)
    guasto = crea_guasto(client, macchinario_id)

    risposta = client.patch(f"/guasti/{guasto['id']}", json={
        "stato": "boh"
    })

    assert risposta.status_code == 422
    assert risposta.json()["detail"] == "Stato non valido"

    elenco = client.get("/guasti", params={
        "macchinario_id": macchinario_id
        }).json()

    assert elenco[0]["stato"] == "aperto"

    risposta = client.patch(f"/guasti/{guasto['id']}", json={})

    assert risposta.status_code == 422
    assert risposta.json()["detail"][0]["loc"] == ["body", "stato"]


def test_TC_G13_guasto_inesistente(client):

    risposta = client.patch("/guasti/999999", json={
        "stato": "risolto",
    })

    assert risposta.status_code == 404
    assert risposta.json()["detail"] == "Guasto non trovato"


def test_TC_G14_riapertura_guasto_chiuso(client):
    reparto_id = crea_reparto(client)
    macchinario_id = crea_macchinario(client, "M-1", reparto_id)
    guasto = crea_guasto(client, macchinario_id)

    chiusura_guasto = client.patch(f"/guasti/{guasto['id']}", json={
        "stato": "risolto",
    })

    assert chiusura_guasto.status_code == 200

    elenco = client.get("/guasti", params={
        "macchinario_id": macchinario_id,
    }).json()

    assert elenco[0]["stato"] == "risolto"
    assert elenco[0]["data_chiusura"] is not None

    riapertura_guasto = client.patch(f"/guasti/{guasto['id']}", json={
        "stato": "in_lavorazione",
    })

    assert riapertura_guasto.status_code == 200
    assert riapertura_guasto.json()["stato"] == "in_lavorazione"
    assert riapertura_guasto.json()["data_chiusura"] is not None



    


