---
name: qa-workflow
description: QA 워크플로우 오케스트레이터 - 웹 API로 Task 관리, 사전 검증, Host/IOS 실행, 결과 기록
user-invocable: true
allowed-tools: Read, Grep, Glob, Bash, Task, AskUserQuestion
triggers:
  - qa-workflow
  - QA 워크플로우
  - 다음 QA
  - QA 시작
args:
  - name: task_id
    description: Task ID (예: 333005). 미지정 시 대시보드에서 선택
    required: false
---

# QA 워크플로우 오케스트레이터

웹 API 조회 → Task 제안 → 사전 검증 → Host/IOS 실행 → 테스트 → 결과 기록까지의 전체 QA 프로세스를 오케스트레이션합니다.

## 자동검증 하네스 필수 원칙

자동검증을 실행하거나 하네스를 변경할 때는 먼저 [`../../docs/qa-harness-ssot.md`](../../docs/qa-harness-ssot.md)를 읽고 준수합니다.

- 하네스는 **실제 언리얼을 AutomationDriver CLI로 조종하여 훈련생 조작을 모사**합니다. UDP 패킷은 Unreal 원본이 생성·송신합니다.
- 절차를 넘어가게 만드는 것 자체는 목적이 아닙니다.
- 출력 목표를 향한 후보 입력 탐색·교체와 Host 내부 시험값 직접 주입을 Unreal 모사로 간주하지 않습니다. 훈련내용에 반복이 명시된 경우에만 지정 조작을 조건부 반복합니다.
- Python의 직접 UDP41/51/61 패킷 재구현을 실언리얼 검증으로 간주하지 않습니다.
- 하네스 문제를 해결하기 위해 원본 Host·Unreal·DB를 변경하지 않습니다.
- Unreal 동등성을 입증할 수 없는 경로는 PASS가 아니라 `ERROR` 또는 `COVERAGE GAP`으로 기록합니다.

## 실행 모드

1. 메인 Unreal 프로젝트와 Harness 저장소의 **실언리얼 physical 자동검증 모드**만 정식 절차 검증에 사용합니다. 실행 명령, fresh 수명주기, 판정과 증거 위치는 [`../../docs/qa-harness-manual.md`](../../docs/qa-harness-manual.md)를 따릅니다.
2. physical adapter가 없는 컨트롤은 직접 상태 쓰기나 후보 입력 탐색으로 우회하지 않고 `COVERAGE_GAP`으로 중단합니다.
3. 격리 worktree, 백업 하네스, 기존 IOS/PIE 수동 흐름은 자동검증 실행 경로로 사용하지 않습니다.
4. Task 완료 여부만으로 PASS 처리하지 않습니다. JSON이 `FINISHED_WITH_FINDINGS`이면 findings를 해결하거나 명시한 채 결과를 보고합니다.

## 전제 조건

| 항목 | 경로/값 |
|------|---------|
| db_input_tool API | `http://192.168.11.201:6001` |
| 인증 | admin / admin1 |
| IOS | `E:\KAI_HOST\iostestapp\main.py` |
| IOS config | `E:\KAI_HOST\iostestapp\app_config.ini` |
| Host | `E:\KAI_HOST\fa50m-host\x64\FA50MHOST.exe` |
| DT_ControlData | `E:\KAI_VCBT\fa50visualdev_new\DT_ControlData.csv` |
| AnimIdMarkerMapping | `E:\KAI_VCBT\fa50visualdev_new\DT_AnimIdMarkerMapping.csv` |

---

## Phase 1: 대시보드 (Task 선택)

### 1-1. JWT 토큰 획득

```bash
TOKEN=$(curl -s -X POST http://192.168.11.201:6001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin1"}' | python -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
```

### 1-2. QA 대기 Task 조회

```bash
# workflow_status_id=4 (검토 완료 = QA 대기)
curl -s "http://192.168.11.201:6001/api/tasks?workflow_status_id=4&limit=100" \
  -H "Authorization: Bearer $TOKEN"

# workflow_status_id=9 (1차 검증 실패 = 재테스트)
curl -s "http://192.168.11.201:6001/api/tasks?workflow_status_id=9&limit=100" \
  -H "Authorization: Bearer $TOKEN"

# Inspection 요약
curl -s "http://192.168.11.201:6001/api/inspection-results/summary" \
  -H "Authorization: Bearer $TOKEN"
```

### 1-3. 사용자에게 Task 목록 표로 제시

```
| # | Task ID | 이름 | 상태 | Step 수 |
|---|---------|------|------|---------|
| 1 | 333005  | ... | QA대기 | 25 |
```

→ 사용자가 Task 선택 (또는 args로 task_id 지정)

### Workflow Status ID

| ID | 이름 | 의미 |
|----|------|------|
| 1 | 검토 대기 | 담당자 검토 필요 |
| 4 | 검토 완료 | QA 대기 |
| 6 | 1차 검증 통과 | 툴 검증 통과 |
| 8 | 시연 완료 | 시연 완료 |
| 9 | 1차 검증 실패 | 재테스트 필요 |
| 11 | 2차 언리얼 통과 | 최종 통과 |
| 12 | 언리얼 QA 중 | 테스트 진행 중 |
| 13 | 지원장비 구현 완료 | 지원장비 구현됨 |
| 14 | 자동시현 완료 | 자동시현 완료 |

---

## Phase 2: 사전 검증 (Pre-flight Check)

Task 선택 후 10개 항목을 자동 검증. **차단이 아닌 경고** 수준.
문제 발견 시 먼저 `하네스 불일치 / Unreal / Host / DB 절차 정의`로 분류합니다. 하네스 통과를 위한 DB 수정은 금지하며, 독립적으로 확인된 DB 정의 결함만 별도 변경 절차와 재검증 대상으로 다룹니다.

### 검증 항목 (10개)

| # | 검증 | 심각도 | 비고 |
|---|------|--------|------|
| 1 | sub_no 전부 동일 | 경고 | `COUNT(DISTINCT sub_no) = 1` |
| 2 | 미구현 장비 (DT_ControlData 미등록) | 정보 | i_id가 DT_ControlData에 없음 = 언리얼 미구현 (추후 추가 필요) |
| 3 | i_term 범위 외 (6~9) | 오류 | 0~5, >10, >999 외 |
| 4 | i_term = NULL | 경고 | 비교 모드 미설정 |
| 5 | i_margin != 0 인데 i_term != 3 | 정보 | margin 무시됨 (i_term>10은 정상) |
| 6 | animation ID 미매핑 | 경고 | DT_AnimIdMarkerMapping.csv (판정에 영향 없음) |
| 7 | animation 시퀀스 파일 없음 | 경고 | .uasset 미존재 (판정에 영향 없음) |
| 8 | animation 통계 | 정보 | -1(없음), -2(특수), 유효 비율 |
| 9 | 초기값 누락 | 경고 | tbl_input_variable_initialize (공통 초기값은 별도) |
| 10 | step_no 내 sub_no 중복 | 오류 | 동일 step_no에 같은 sub_no |

**i_id 분류 기준**:
- DT_ControlData.csv EquipmentId에 있음 → **언리얼 구현 완료** (항공기 내외부 + 지원장비)
- DT_ControlData.csv에 없음 → **언리얼 미구현** (physical 자동검증은 `COVERAGE_GAP`)
- 283 (CONFIRM_BUTTON) → **IOS 확인 버튼**

### 검증 SQL 모음

```sql
-- 검증 1: sub_no 전부 동일
SELECT COUNT(DISTINCT step_sub_no) as unique_subs
FROM tbl_step WHERE step_task_id = {TASK_ID};

-- 검증 3: i_term 범위 외 (6~9만 오류)
SELECT step_no, step_sub_no, step_i_id, step_i_term
FROM tbl_step WHERE step_task_id = {TASK_ID}
  AND step_i_term BETWEEN 6 AND 9;

-- 검증 4: i_term NULL
SELECT COUNT(*) FROM tbl_step
WHERE step_task_id = {TASK_ID} AND step_i_term IS NULL;

-- 검증 5: i_margin 정합성
SELECT step_no, step_sub_no, step_i_id, step_i_term, step_i_margin
FROM tbl_step WHERE step_task_id = {TASK_ID}
  AND step_i_margin != 0 AND (step_i_term IS NULL OR step_i_term != 3);

-- 검증 6: animation 유효 ID 목록 추출
SELECT DISTINCT animation, animation / 10 as anim_id
FROM tbl_step WHERE step_task_id = {TASK_ID} AND animation > 0;
-- → DT_AnimIdMarkerMapping.csv에서 "{TASK_ID},{anim_id}" 존재 확인

-- 검증 9: 초기값 존재
SELECT COUNT(*) FROM tbl_input_variable_initialize
WHERE ivi_task = {TASK_ID};

-- 검증 10: sub_no 중복
SELECT step_no, step_sub_no, COUNT(*)
FROM tbl_step WHERE step_task_id = {TASK_ID}
GROUP BY step_no, step_sub_no HAVING COUNT(*) > 1;
```

### 검증 2: i_id 유효성 (파일 기반)

`DT_ControlData.csv`의 마지막 컬럼(EquipmentId)에서 유효 ID 목록 추출 후 DB의 `step_i_id` 대조:

```bash
# DB에서 사용하는 i_id 목록
PGPASSWORD=kai psql -h 192.168.11.201 -p 5432 -U kai -d FA_50_KAI -t -A -c \
"SELECT DISTINCT step_i_id FROM tbl_step
 WHERE step_task_id = {TASK_ID} AND step_i_id > 0
 ORDER BY step_i_id;"
```

→ CSV EquipmentId 컬럼과 교차 확인

### 검증 7: animation 시퀀스 파일

`DT_AnimIdMarkerMapping.csv`에서 MasterSequencePath 추출 → `.uasset` 존재 확인:

```bash
# Content/ 이하 경로를 실제 프로젝트 경로로 변환
# /Game/01_Visual/... → Content/01_Visual/...
```

### 검증 출력 형식

```
═══ Task {TASK_ID} 사전 검증 (10항목) ═══

 [PASS] #1  sub_no 다양성: OK (1~13 범위)
 [PASS] #2  i_id 유효성: 25개 모두 DT_ControlData 존재
 [PASS] #3  i_term 범위: 정상
 [PASS] #4  i_term NULL: 없음
 [PASS] #5  i_margin 정합성: OK
 [PASS] #6  animation 매핑: 5개 AnimID 존재
 [PASS] #7  animation 시퀀스: 5개 .uasset 존재
 [INFO] #8  animation 통계: 유효 5/25, 없음(-1) 20/25
 [PASS] #9  초기값: 12건 존재
 [PASS] #10 sub_no 중복: 없음

결론: 모두 PASS. 테스트 진행 가능.
```

### 이전 Inspection/QA 이슈 확인

```bash
# 이전 Inspection 결과
curl -s "http://192.168.11.201:6001/api/inspection-results/by-task/{TASK_ID}" \
  -H "Authorization: Bearer $TOKEN"

# QA 이슈
curl -s "http://192.168.11.201:6001/api/qa-issues?task_id={TASK_ID}" \
  -H "Authorization: Bearer $TOKEN"
```

### 사전 검증 후 분기

- **오류 있음**: 원인 경계와 증거를 보고. DB 정의 결함이 독립적으로 확인된 경우에만 별도 수정 후 fresh 재검증
- **경고만**: 사용자에게 알리고 테스트 진행 여부 확인
- **모두 PASS**: 바로 Phase 3으로

---

## Phase 3: Fresh 실행 설정

`app_config.ini`를 수동 편집하지 않습니다. 매뉴얼의 PowerShell runner가 control session lock을 획득하고 Host `WAIT` 확인 후 UDP21로 Task와 Step 1을 설정한 다음 `INIT → RUN` 순서로 시작합니다.

---

## Phase 4: 테스트 진행

`qa/runs/physical_<TaskId>_<timestamp>.json`의 `outcome`, `terminal_verdict`, `results`, `findings`, `artifacts`를 판정 근거로 사용합니다. 프로세스 종료 코드 0이어도 `FINISHED_WITH_FINDINGS`일 수 있으므로 JSON을 생략하지 않습니다. 조작은 Harness가 실제 Unreal의 `ACT PRESS/HOLD/RELEASE` API로 수행합니다.

### 실패 시 디버깅 연계

Step 실패 보고 시 `/qa-signal`로 신호 디버깅:

```
/qa-signal {TASK_ID} {FAIL_STEP_NO}
```

## Phase 5: 결과 기록

physical 자동검증의 workflow PASS 기록은 clean `FINISHED`와 필수 증거 보존이 확인된 경우에만 수행합니다. `FINISHED_WITH_FINDINGS`, `BLOCKED`, `COVERAGE_GAP`을 PASS 상태로 기록하지 않습니다.

### 5-1. MainStep별 Inspection 결과

```bash
# 단건 기록
curl -s -X POST "http://192.168.11.201:6001/api/inspection-results/upsert" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"ir_ms_step_id":"{MS_STEP_UUID}","ir_task_id":{TASK_ID},"ir_status":"PASS"}'

# Batch (여러 Step)
curl -s -X POST "http://192.168.11.201:6001/api/inspection-results/batch-upsert" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"task_id":{TASK_ID},"results":[
    {"ir_ms_step_id":"{UUID1}","ir_status":"PASS"},
    {"ir_ms_step_id":"{UUID2}","ir_status":"FAIL"}
  ]}'
```

### 5-2. Workflow 상태 변경

```bash
# PASS → 1차 검증 통과 (6)
curl -s -X PATCH "http://192.168.11.201:6001/api/tasks/{TASK_ID}/workflow-status" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"workflow_status_id": 6}'

# FAIL → 1차 검증 실패 (9)
curl -s -X PATCH "http://192.168.11.201:6001/api/tasks/{TASK_ID}/workflow-status" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"workflow_status_id": 9}'
```

### 5-3. FAIL 시 QA 이슈 생성

```bash
# 이슈 생성
curl -s -X POST "http://192.168.11.201:6001/api/qa-issues" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"qa_title":"Step {N} 판정 실패","qa_description":"{상세 설명}","qa_priority":"HIGH"}'

# 이슈에 Step 링크
curl -s -X POST "http://192.168.11.201:6001/api/qa-issues/{QA_ID}/link-step" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"ms_step_id":"{MS_STEP_UUID}","task_id":{TASK_ID}}'
```

### 5-4. 결과 요약

```
═══ Task {TASK_ID} QA 결과 ═══

 전체: {N} MainStep 중 {PASS}건 PASS, {FAIL}건 FAIL
 상태: {workflow_status} → {new_status}

 FAIL Steps:
  - Step {NO}: {증상 요약} → QA Issue #{QA_ID}

 다음 QA: /qa-workflow 로 계속
```

---

## 기존 스킬 연계

| 상황 | 스킬 |
|------|------|
| 특정 Step 신호 디버깅 | `/qa-signal {TASK_ID} {STEP_NO}` |
| Host 로그 확인 | `/qa-host` |
| 언리얼 로그 확인 | `/qa-log` |

**연계 시나리오**:
`/qa-workflow` 사전 검증 → 테스트 → Step 실패 → `/qa-signal` 디버깅 → 결과 기록

---

## 참고 문서

- [`../../docs/qa-harness-ssot.md`](../../docs/qa-harness-ssot.md): 언리얼 모사 하네스의 목적, 경계, 금지사항, 판정 기준
- [`../../docs/qa-harness-manual.md`](../../docs/qa-harness-manual.md): 메인 통합 환경의 fresh 실행, 결과 판독, 종료와 문제 해결 매뉴얼
- [`../../docs/qa-harness-validation-394020-20260720.md`](../../docs/qa-harness-validation-394020-20260720.md): 기준 구현의 확인사항, 미해결 이슈, 미확인 범위 기록
- [`../../docs/db-host-judgment-reference.md`](../../docs/db-host-judgment-reference.md): DB 컬럼 ↔ Host 판정 로직 레퍼런스
- [`../qa-signal/skill.md`](../qa-signal/skill.md): 신호 검증 스킬
