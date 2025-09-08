from fastapi import FastAPI

app = FastAPI(title="news-summary-server")


@app.get("/health")
def health_check() -> dict:
    return {"status": "ok"}
