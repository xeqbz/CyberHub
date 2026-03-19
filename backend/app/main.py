from fastapi import FastAPI

app = FastAPI(title="CyberHub Backend")

@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}