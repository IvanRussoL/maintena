from app.models import Tecnico
import pytest
from sqlalchemy.exc import IntegrityError

def crea_tecnico(client, codice, nome="Luca", cognome="Rossi", specializzazione=None):
    corpo = {"codice_dipendente": codice, "nome": nome, "cognome": cognome}
    if specializzazione is not None:
        corpo["specializzazione"] = specializzazione
    risposta = client.post("/tecnici", json=corpo)

    assert risposta.status_code == 201
    return risposta.json()


def test_TC_T01_crea_tecnico_con_specializzazione(client):
    risposta = client.post("/tecnici", json={
          "codice_dipendente":"T1", 
          "nome": "Luca", 
          "cognome": "Rossi" , 
          "specializzazione": "meccanica"})
    
    assert risposta.status_code == 201
    dati = risposta.json()
    assert dati["attivo"] is True
    assert dati["specializzazione"] == "meccanica"


def test_TC_T02_crea_tecnico_senza_specializzazione(client):
    risposta = client.post("/tecnici", json={
        "codice_dipendente":"T2", 
        "nome": "Anna", 
        "cognome": "Verdi"})
    
    assert risposta.status_code == 201
    dati = risposta.json()
    assert dati["attivo"] is True
    assert dati["specializzazione"] is None


def test_TC_T03_codice_dipendente_duplicato(client):
    crea_tecnico(client, "T1")

    risposta = client.post("/tecnici", json={
            "codice_dipendente": "T1",
            "nome": "Mario",
            "cognome": "Bianchi"
    })

    assert risposta.status_code == 409
    assert risposta.json()["detail"] == "Esiste già un tecnico con questo codice"
    assert len(client.get("/tecnici").json()) == 1


def test_TC_T04_campi_obbligatori_mancanti(client):
    risposta = client.post("/tecnici", json={"codice_dipendente": "T5"})

    assert risposta.status_code == 422
    errori = risposta.json()["detail"]
    campi = sorted(errore["loc"][-1] for errore in errori)
    assert campi == ["cognome", "nome"]
      


def test_TC_T05_specializzazione_non_valida_limite_noto(client):
    # limite noto: il CHECK del database rifiuta il valore e la rotta non traduce l'errore
    with pytest.raises(IntegrityError):
        client.post("/tecnici", json={
            "codice_dipendente": "T1",
            "nome": "Luca",
            "cognome": "Rossi",
            "specializzazione": "magia",
        })

    with pytest.raises(IntegrityError):
        client.post("/tecnici", json={
                "codice_dipendente": "T4",
                "nome": "Luca",
                "cognome": "Rossi",
                "specializzazione": "",
            })

    assert client.get("/tecnici").json() == []



def test_TC_T06_elenco_tecnici(client):
    crea_tecnico(client, "T-1")
    crea_tecnico(client, "T-2", nome="Anna", cognome="Verdi")

    risposta = client.get("/tecnici")

    assert risposta.status_code == 200
    codici = sorted(tecnico["codice_dipendente"] for tecnico in risposta.json())
    assert codici == ["T-1", "T-2"]
    # print(risposta.json())


def test_TC_T07_filtro_attivi_e_non_attivi(client, db):
    crea_tecnico(client, "T1")
    inattivo = crea_tecnico(client, "T2", nome="Anna", cognome="Verdi")

    # porta di servizio: nessuna rotta disattiva un tecnico
    tecnico = db.get(Tecnico, inattivo["id"])
    tecnico.attivo = False 
    db.commit()

    risposta_attivi = client.get("/tecnici", params={"attivo": "true"})
    risposta_non_attivi = client.get("/tecnici", params={"attivo": "false"})

    assert risposta_attivi.status_code == 200
    assert risposta_non_attivi.status_code == 200

    assert [t["codice_dipendente"] for t in risposta_attivi.json()] == ["T1"]
    assert [t["codice_dipendente"] for t in risposta_non_attivi.json()] == ["T2"]
      


def test_TC_T08_filtro_attivo_non_booleano(client):
    risposta = client.get("/tecnici", params={"attivo": "boh"})

    assert risposta.status_code == 422
    errore = risposta.json()["detail"][0]
    assert errore["loc"][-1] == "attivo"
