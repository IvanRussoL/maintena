# tests/test_reparti.py
# Test automatici delle rotte /reparti (casi TC-R del PIANO_TEST.md).


def test_TC_R02_crea_reparto(client):
    """TC-R02: creare un reparto con un nome valido restituisce 201 e il reparto creato."""
    risposta = client.post("/reparti", json={"nome": "smistamento"})
    assert risposta.status_code == 201                 # 201 Created
    assert risposta.json()["nome"] == "smistamento"    # il corpo contiene il nome inviato