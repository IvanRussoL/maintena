from fastapi import FastAPI

app = FastAPI(title="Maintena")

@app.get("/")
def stato():
    return {"applicazione": "Maintena", "stato": "attiva"}