# Claude Code 복붙용 프롬프트 (단계별)

> 사용법: 이 폴더를 리포 루트로 열고 터미널에서 `claude` 실행 → 아래 프롬프트를 순서대로 붙여넣기.
> 각 단계는 독립적으로 커밋 가능한 산출을 낸다. 먼저 계획을 받고(플랜 모드) 확인한 뒤 실행시킬 것.

## 0) 온보딩
```
CLAUDE.md와 docs/01_마이그레이션_설계서.md, reference/ 폴더를 모두 읽어.
전체 그림과 P0~P4 단계를 한 번 요약해서 확인시켜줘. 아직 코드는 만들지 마.
```

## P0 — 엔진 패키지 + 골든 테스트 (여기부터 시작)
```
P0을 시작하자. pnpm + Turborepo 모노레포를 스캐폴딩하고,
packages/scheduler 를 TypeScript로 만들어.
reference/scheduler.reference.mjs 를 정본으로 삼아 computeSchedule(model, mode)와
rollupMM(model)을 타입 안전하게 이식해줘(순수 함수, I/O 없음, hasCycle 포함).
그리고 reference/wbs_model.json 을 시드로 CLAUDE.md의 '골든값'을 그대로 검증하는
회귀 테스트(vitest)를 작성하고 전부 통과시켜. 끝나면 커밋해.
```

## P1 — React 앱으로 현재 대시보드 재현
```
P1. apps/web 를 React+TS+Vite+Tailwind로 만들고, @scheduler 패키지를 import해서
reference/current_app.html 의 화면(KPI·WBS·간트·M/M·크리티컬 패스·주말 on/off·공휴일 음영)을
컴포넌트로 재현해. 데이터는 아직 로컬 상태(시드 JSON)로. 편집 폼은 P3에서.
반응형 유지. 끝나면 커밋.
```

## P2 — API + DB (단일 프로젝트 CRUD)
```
P2. apps/api 를 NestJS로, prisma/schema.prisma 를 설계서 6장대로 만들어
(project, phase, task, task_dependency, holiday, user, membership, audit_log).
태스크·설정·공휴일 CRUD API와, 저장 시 @scheduler로 정본 재계산해 반환하는
recompute를 구현해. 서버 검증에 필수값·순환의존성 차단 포함. seed로 wbs_model.json 적재.
web을 API에 연결(TanStack Query). 통합 테스트 추가. 커밋.
```

## P3 — 인증 + 권한(RBAC) + 편집 UI
```
P3. 로그인과 RBAC(admin/editor/viewer)를 붙여. 설계서 9장 권한 매트릭스를
백엔드 미들웨어에서 강제하고 프론트에서도 숨김 처리해. current_app.html의 편집 모드
(태스크 CRUD 폼·설정 패널·되돌리기·내보내기/가져오기)를 web에 구현.
변경은 audit_log에 기록. 커밋.
```

## P4 — (옵션) 협업·알림
```
P4. WebSocket으로 다중 사용자 동시 편집 반영, 마감 임박/변경 알림을 추가해.
성능을 위해 계산 결과 캐시+무효화 전략을 검토해 제안 후 적용. 커밋.
```

## 자주 쓰는 보조 프롬프트
```
# 계획부터: "바로 코딩하지 말고 먼저 계획을 보여줘."
# 안전장치: "이 변경이 골든 테스트를 깨지 않는지 먼저 테스트 돌려서 확인해."
# 리뷰: "방금 변경을 설계서 기준으로 셀프 리뷰하고 리스크를 알려줘."
```
