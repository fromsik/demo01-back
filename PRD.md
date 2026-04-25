# PRD - TimeBox Planner (MVP)

## 1) 제품 방향
- 웹: **로그인 필수**(Google/Kakao/Naver), 서버 저장 기반.
- 앱: **로컬 모드 우선**(로그인 없이 기기 내부 저장), 서버 비전송.
- 핵심: 오늘 목표(1~5개) + 10분 단위 시간 블록 + 겹침 없는 타임박싱.

## 2) MVP 범위
- 인증: 소셜 로그인 진입점, 로그인 사용자 식별, 보호 API 접근 제어.
- 양식: 생성/조회/수정/삭제/복사/기본 양식 지정.
- 일별 계획: 생성/조회/수정/삭제, 양식 기반 계획 생성.
- 기록 조회: 날짜별 필터 조회.
- 검증 정책:
  - 목표 개수 1~5개
  - 시간 10분 단위
  - 시작 < 종료
  - 동일 계획 내 블록 겹침 금지

## 3) 데이터 모델(서버)
- User
- TimeboxTemplate / TimeboxTemplateBlock
- DailyPlan / DailyGoal / DailyTimeBlock

## 4) 정책 요약
- 웹 비로그인 사용자는 작성/저장/조회 API 호출 불가.
- 데이터는 사용자 단위로 분리.
- 양식 변경은 기존 일별 계획에 자동 전파하지 않음.

## 5) 향후 확장(비-MVP)
- 앱 계정 연동/동기화
- 캘린더 연동
- 통계/알림
- AI 추천

## 6) API 개요
- Auth: `/api/auth/*`
- Templates: `/api/templates*`
- Daily plans: `/api/daily-plans*`

## 7) 비고
본 PRD는 제공된 원문 PRD를 구현 관점으로 요약한 개발 기준 문서다.
