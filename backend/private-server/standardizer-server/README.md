# standardizer-server

FastAPI 기반 표준화(standardizer) 마이크로서비스.

## 로컬 실행

```bash
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## 헬스 체크

- GET `/health` → `{ "status": "ok" }`
