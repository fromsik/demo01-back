# TimeBox Planner Backend (MVP)

타임박싱 작성 솔루션의 Node.js 백엔드입니다.

## 실행
```bash
npm install
npm start
```

## 테스트
```bash
npm test
```

## 주요 API
- 인증: `GET /api/auth/google|kakao|naver`, `POST /api/auth/login/dev`, `POST /api/auth/logout`, `GET /api/auth/me`
- 템플릿: `GET/POST /api/templates`, `GET/PUT/DELETE /api/templates/:templateId`, `POST /api/templates/:templateId/copy`, `PUT /api/templates/:templateId/default`
- 일별 계획: `GET/POST /api/daily-plans`, `GET/PUT/DELETE /api/daily-plans/:dailyPlanId`, `POST /api/daily-plans/from-template/:templateId`

## 인증 방법(개발)
`POST /api/auth/login/dev`로 토큰 발급 후 `Authorization: Bearer <token>` 헤더를 사용합니다.
