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



def test_TC_M01_crea_macchinario_campi_obbligatori(client):
    reparto_id = crea_reparto(client)

    risposta = client.post("/macchinari", json={
        "matricola": "M-1",
        "nome": "Pressa",
        "reparto_id": reparto_id,
    })

    assert risposta.status_code == 201
    dati = risposta.json()
    assert dati["stato"] == "attivo"
    assert dati["modello"] is None
    assert dati["descrizione"] is None

def test_TC_M02_crea_macchinario_con_stato(client):
    reparto_id = crea_reparto(client)

    risposta = client.post("/macchinari", json={
            "matricola": "M-2",
            "nome": "Tornio",
            "reparto_id": reparto_id,
            "stato": "fermo",
    })
    
    assert risposta.status_code == 201
    assert risposta.json()["stato"] == "fermo"

def test_TC_M03_matricola_duplicata(client):
    reparto_id = crea_reparto(client)

    corpo = {"matricola": "M-1", "nome": "Pressa", "reparto_id": reparto_id}
    client.post("/macchinari", json=corpo)

    corpo_duplicato = {"matricola":"M-1", "nome": "Presa", "reparto_id": reparto_id}
    risposta = client.post("/macchinari", json=corpo_duplicato)

    assert risposta.status_code == 409
    assert risposta.json()["detail"] == "Esiste già un macchinario con questa matricola"
    assert len(client.get("/macchinari").json()) == 1

def test_TC_M04_reparto_inesistente(client):

    corpo = {"matricola": "M-3", "nome": "X", "reparto_id": 999999}
    risposta = client.post("/macchinari", json=corpo)

    assert risposta.status_code == 404
    assert risposta.json()["detail"] == "Reparto non trovato"

def test_TC_M05_stato_non_valido(client):
    reparto_id = crea_reparto(client)

    corpo = {"matricola": "M-1", "nome":"X", "reparto_id": reparto_id, "stato":"rotto"}
    risposta = client.post("/macchinari", json=corpo)

    assert risposta.status_code == 422
    campi = [errore["loc"][-1] for errore in risposta.json()["detail"]]
    assert "stato" in campi

def test_TC_M06_campi_obbligatori_mancanti(client):
    risposta = client.post("/macchinari", json={"matricola": "M-1"})
    assert risposta.status_code == 422
    campi = [errore["loc"][-1] for errore in risposta.json()["detail"]]
    assert "nome" in campi
    assert "reparto_id" in campi


def test_TC_M07_elenco_macchinari(client):

    reparto_id = crea_reparto(client)

    crea_macchinario(client, "M-1", reparto_id)
    crea_macchinario(client, "M-2", reparto_id)

    risposta = client.get("/macchinari")

    assert risposta.status_code == 200
    matricole = [m["matricola"] for m in risposta.json()]
    assert sorted(matricole) == ["M-1", "M-2"]


def test_TC_M08_filtro_per_reparto(client):

    reparto_a = crea_reparto(client)
    reparto_b = crea_reparto(client, nome="Assemblaggio")

    crea_macchinario(client, "M-A", reparto_a)
    crea_macchinario(client, "M-B", reparto_b)

    risposta = client.get("/macchinari", params={"reparto_id": reparto_a})

    assert risposta.status_code == 200
    matricola = [m["matricola"] for m in risposta.json()]
    assert matricola == ["M-A"]


def test_TC_M09_filtro_reparto_vuoto_o_inesistente(client):
    reparto_senza_macchinari = crea_reparto(client)

    risposta_senza_macchinari = client.get("/macchinari", params={"reparto_id": reparto_senza_macchinari})
    risposta_reparto_inesistente = client.get("/macchinari", params={"reparto_id": 999999})

    assert risposta_reparto_inesistente.status_code == 200
    assert risposta_senza_macchinari.status_code == 200

    assert risposta_reparto_inesistente.json() == []
    assert risposta_senza_macchinari.json() == []


def test_TC_M10_filtro_reparto_non_numerico(client):

    risposta = client.get("/macchinari", params={"reparto_id": "abc"})

    assert risposta.status_code == 422


def test_TC_M11_lettura_macchinario_tramite_id(client):

    reparto_id = crea_reparto(client)
    macchinario_id = crea_macchinario(client, "M-1", reparto_id)

    risposta = client.get(f"/macchinari/{macchinario_id}")

    assert risposta.status_code == 200
    dati = risposta.json()
    assert dati["id"] == macchinario_id
    assert dati["matricola"] == "M-1"
    assert dati["reparto_id"] == reparto_id


def test_TC_M12_lettura_macchinario_inesistente_o_id_non_numerico(client):

    risposta_id_inesistente = client.get("/macchinari/999999")
    risposta_id_nonNumerico = client.get("/macchinari/abc")

    assert risposta_id_inesistente.status_code == 404
    assert risposta_id_inesistente.json()["detail"] == "Macchinario non trovato"
    assert risposta_id_nonNumerico.status_code == 422

    
   