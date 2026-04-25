# AGENT Guide - TimeBox Planner Backend

## 북극성 (North Star)
사용자가 **3분 이내**에 "오늘 목표 + 시간 블록"을 빠르게 작성하고 저장하게 만든다.

## 설계 원칙
1. 웹 API는 항상 인증 우선(기본 거부, 명시 허용).
2. 도메인 규칙(목표 1~5, 10분 단위, 비겹침)을 DTO/서비스 계층에서 강제.
3. 양식(Template)과 실행 결과(DailyPlan)를 분리 저장.
4. 사용자 데이터는 반드시 사용자 단위로 격리.
5. 추후 앱 동기화/AI 추천 확장을 고려해 모델 호환성을 유지.

## 구현 체크리스트
- [ ] 인증 없는 요청은 401 처리
- [ ] 목표 개수 정책 검증
- [ ] 시간 단위(10분) 검증
- [ ] 시작/종료 시간 유효성 검증
- [ ] 시간 블록 겹침 검증
- [ ] 템플릿 CRUD + 복사 + 기본 지정
- [ ] 일별 계획 CRUD + 템플릿 기반 생성

## 에러 메시지 가이드
- 겹침: `Time blocks cannot overlap.`
- 목표 개수: `Goals must be between 1 and 5.`
- 인증: `Login required`

## 확장 메모
- OAuth 실제 연동 시 `/api/auth/*` placeholder를 provider SDK 기반으로 교체.
- 저장소를 in-memory에서 DB로 교체할 때도 validation contract는 동일하게 유지.
