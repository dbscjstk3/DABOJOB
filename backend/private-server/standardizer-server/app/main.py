from fastapi import FastAPI

app = FastAPI(title="standardizer-server")


@app.get("/health")
def health_check() -> dict:
    return {"status": "ok"}
