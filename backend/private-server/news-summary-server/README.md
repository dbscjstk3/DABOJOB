# news-summary-server

FastAPI 기반 뉴스 요약 마이크로서비스.

## 로컬 실행

```bash
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8200 --reload
```

## 헬스 체크

- GET `/health` → `{ "status": "ok" }`
