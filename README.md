# demo01-back

TimeBox Planner MVP 백엔드(FastAPI)입니다.

## 실행
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## 테스트
```bash
pytest -q
```

## 주요 엔드포인트
- 인증: `/api/auth/*`
- 양식: `/api/templates*`
- 일별 계획: `/api/daily-plans*`

> 현재 소셜 로그인은 placeholder이며, 테스트용 `/api/auth/mock-login`을 제공합니다.
