from fastapi import FastAPI

app = FastAPI(title="Authenticity Validator for Academia")

@app.get("/")
def root():
    return {"status": "AVFA API is running"}