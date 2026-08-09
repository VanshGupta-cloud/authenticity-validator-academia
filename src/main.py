from fastapi import FastAPI
from src.routers import auth


app = FastAPI(title="Authenticity Validator for Academia")

app.include_router(auth.router)


@app.get("/")
def root():
    return {"status": "AVFA API is running"}