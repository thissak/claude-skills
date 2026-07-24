---
name: qa-workflow
description: 사용자가 "qa-workflow", "QA 워크플로우", "다음 QA", "QA 시작"이라고 말하면 웹 API Task 조회, 사전 검증, physical 실행, 절차 검증 SSOT 등록을 조율한다. Task ID를 함께 지정할 수 있으며 외부 Inspection/workflow 쓰기는 명시적 게시 요청에서만 수행한다.
---

# QA 워크플로우 오케스트레이터

웹 API 조회 → Task 제안 → 사전 검증 → Host/IOS 실행 → 테스트 → 결과 기록까지의 전체 QA 프로세스를 오케스트레이션합니다.

## 절차 검증 SSOT와 게시 경계

실행 전에 [`../../docs/qa-procedure-verification-ssot.md`](../../docs/qa-procedure-verification-ssot.md)와 생성된 현재 표를 읽는다.

- physical JSON은 `Scripts/qa_procedure_status.py record-auto`로 현재 절차 SSOT에 먼저 등록한다.
- 정적·신호·로그 결과는 공통 IssueKey에 보조 증거로 연결한다.
- 검증 실행과 외부 DB Inspection/workflow 게시를 분리한다.
- 기본 검증 모드에서는 외부 API를 조회만 하며 Inspection, workflow status, QA issue를 쓰지 않는다.
- 사용자가 명시적으로 “결과 게시”, “Inspection 반영”, “workflow 상태 변경”을 요청한 경우에만 Phase 5 게시를 수행한다.
- 외부 게시 상태는 현재 runtime 검증 SSOT를 덮어쓰지 않는다.

## 자동검증 하네스 필수 원칙

자동검증을 실행하거나 하네스를 변경할 때는 먼저 [`../../docs/qa-harness-ssot.md`](../../docs/qa-harness-ssot.md)를 읽고 준수합니다.

- 하네스는 **실제 언리얼을 AutomationDriver CLI로 조종하여 훈련생 조작을 모사**합니다. UDP 패킷은 Unreal 원본이 생성·송신합니다.
- 기하 기반 컨트롤은 카메라 화면 투영이 아니라 `CAPS target_world_path`와 `ACT HOLD_WORLD`로 실제 interaction ray를 구성합니다. 자동 카메라는 AutomationDriver 프로세스에서만 비영속 비활성화합니다.
- 현재 커버 비검증 탐색은 Task 시작 시 `PRECOND COVERS_OPEN`을 적용하고 `procedural_evidence=false`로 분리합니다. 개별 `PREP` lazy-open은 사용하지 않습니다.
- 절차를 넘어가게 만드는 것 자체는 목적이 아닙니다.
- 출력 목표를 향한 임의 후보 입력 탐색·교체와 Host 내부 시험값 직접 주입을 Unreal 모사로 간주하지 않습니다. 훈련내용 또는 같은 DB 입력 그룹의 `O_ID/O_VAL`이 반복 종료 조건을 명시한 경우에만 조건부 반복합니다. 같은 `(step_no, step_sub_no)`에 여러 DCS 입력 행이 있으면 그 행들만 절차가 허용한 후보이며, 그룹 밖 입력은 시도하지 않습니다. 현재 하네스가 다중 후보를 처리하지 못하면 제품 실패가 아니라 `HARNESS_DCS_GROUP_INPUT_GAP`으로 남깁니다.
- DCS/FourWay 입력 반복은 각 ACT 뒤 Unreal 자식 STATE와 Host `EX_IN`이 release 상태로 돌아온 다음에만 다음 pulse를 보냅니다. `EX_OUT`의 중간 변화만 보고 0.15초 복귀 전에 재입력하지 않습니다. 출력의 완전 순환이나 정체가 보이면 시간 준비 조건과 DB 허용 후보 그룹을 분리해 조사합니다.
- 물리 pulse와 Host `EX_IN` 복귀는 정상인데 DCS 출력이 고정되면 실제 FWD/AFT 페이지·mode 초기값·시간 준비 상태를 알려진 정상 Task와 비교합니다. `DECOUPLE`처럼 페이지가 독립인데 DB가 필요한 AFT LIST·숫자키 진입 행을 생략했다면 `PROCEDURE_AFT_IUFC_PAGE_PRECONDITION_GAP`으로 분류합니다.
- 훈련내용 설명문을 추론해 DB에 없는 페이지 진입·모드 전환을 하네스가 합성하지 않습니다. 대표 Task의 같은 control/output Step PASS는 하네스 범주 해소 증거일 뿐, 실행하지 않은 개별 Task의 full PASS로 승격하지 않습니다.
- Wheel/아날로그 입력은 이름으로 `0..255`를 추정하지 않고 실제 송수신 변환식의 정수 버킷 중앙을 목표로 합니다. FWD IUFC는 Host `normalized×250`, AFT/generic Wheel은 UDP51 `normalized×100` 계약을 사용하며 0과 최대 스토퍼는 정확한 끝값을 사용합니다.
- 시간·화면 상태가 다음 입력의 전제이면 고정 sleep이나 Host 타이머 직접 설정으로 통과시키지 않습니다. 권위 있는 실제 출력 관측을 사용하고, EGI ALIGN `O_ID=133, O_VAL=5`는 UDP15 IUFC 텍스트의 `RDY`가 확인된 뒤에만 DCS ACT를 시작합니다. CP/AP 중 nonzero `TIMETAG`를 받은 route를 선택하며, 디코드 텍스트는 Host 신호 증거이지 렌더링 픽셀 증거가 아닙니다.
- physical 실행 전 선택한 Host 실행 파일과 실제 활성 프로세스 경로가 같은지 확인합니다. 명시적 `QA_HOST_EXE`가 없으면 root/x64 후보 중 최신 artifact를 사용하고, 불일치하면 `HOST_ARTIFACT_MISMATCH`로 중단합니다. 보고서의 `rig_artifacts.host`에서 경로·SHA-256·`deployment_drift`를 확인한 뒤에만 제품·DB·Unreal·하네스 문제로 귀속합니다. 구형 artifact에서만 재현되면 `HOST_ARTIFACT_DRIFT`로 분리하며 Host 파일을 자동 복사·덮어쓰기하지 않습니다.
- Python의 직접 UDP41/51/61 패킷 재구현을 실언리얼 검증으로 간주하지 않습니다.
- 하네스 문제를 해결하기 위해 원본 Host·Unreal·DB를 변경하지 않습니다.
- Unreal 동등성을 입증할 수 없는 경로는 PASS가 아니라 `ERROR` 또는 `COVERAGE GAP`으로 기록합니다.
- IOS 283 확인 행은 안정 실행 identity `(substep_id, equipment_id)`의 짧은 진행 grace를 먼저 관찰합니다. Host가 자동 진행하면 UDP31을 보내지 않고 `IOS_CONFIRM_AUTO_ADVANCED`를 기록하며, 같은 실행이 남아 있을 때만 확인을 보냅니다.
- 현재 physical 상태가 DB 목표와 이미 같아 edge가 없으면 반대 상태로 합성 re-arm하지 않습니다. `NO_PHYSICAL_EDGE`로 중단하고 전체 sweep은 `PROCEDURE_MISMATCH`로 분류합니다.
- StickAxis의 중립은 spring-return 결과이지 독립 방향 조작이 아닙니다. 같은 all-required DB 그룹에서 조작 축과 이미 중립인 형제 축을 함께 요구하면 형제 축을 임의로 이탈·복귀시켜 edge를 합성하지 않습니다. 지정 축 held STATE와 Host PASS가 확인됐어도 형제 축 edge가 없어 그룹이 미완료이면 `PROCEDURE_STICK_AXIS_NEUTRAL_EDGE_GAP`으로 재분류해 절차/Host 소유자 게이트로 보냅니다.
- DB `I_ID`가 DT에 없으면 곧바로 Unreal 미구현으로 확정하지 않습니다. DB 변수 SIGNAL, Host `EX_IN[].DATA`, 같은 의미의 활성 ID, Unreal 태그·송신 경로를 교차검증합니다. 구형/dummy ID이면 `DB_I_ID_LEGACY_ORPHAN`으로 분류하고 활성 ID 별칭으로 우회하지 않습니다.
- DB Inspection PASS/FAIL/NA는 사람 QA 이력이며 실행 지시가 아닙니다. 기존 FAIL만으로 ACT를 생략하거나 Step을 넘기지 않습니다. 현재 실행에서 실제 `COVERAGE_GAP`이 발생하고 같은 `ms_step_id`에 FAIL이 있을 때만 `KNOWN_INSPECTION_FAIL_COVERAGE_BOUNDARY`로 구체화하고, `db_inspection_context[].advisory_only=true`와 원래 action 증거를 함께 보존합니다.
- 생성된 `equipment_mapping.h`의 enum이 DB `iv_data_type` 또는 Host 실제 구조체 필드 타입과 다르면 `UNREAL_EQUIPMENT_MAPPING_ENUM_DRIFT`로 분류합니다. Host enum 값·DT 상태 순서·UDP 수신 대입·EX_IN 링크를 대조하고, 생성 헤더를 직접 고치지 말고 `generate_equipment_mapping.py`의 `SPECIAL_MAPPINGS`에서 수정한 뒤 SSOT 파이프라인으로 재생성합니다. 매핑 수정 뒤 초기 상태와 첫 목표가 같으면 별도 `PROCEDURE_INITIAL_STATE_EDGE_GAP`으로 유지합니다.
- 첫 blocker 뒤를 수집하려고 Host 수동 Skip이나 later `start_step`을 일반 continuation으로 사용하지 않습니다. 수동 Skip은 stale/unmapped ID의 UDP100 EquipmentSet 동기화를 완료하지 못할 수 있고, `start_step`은 목표 Step 직접 점프가 아니라 선행 상태를 순차 재생하다 actual input에서 멈출 수 있습니다. 반복 blocker는 owner dossier로 묶고 소유자 수정 뒤 fresh full-run으로 다음 구간을 엽니다.
- spring-return 또는 HOLD target은 `CAPS momentary_indices/return_index`와 target label로 구분하고 release 전 실제 `state_held`와 Host 진행을 관찰합니다. 설명의 `for N seconds`는 최소 유지시간이며, 관찰 예외가 나도 successful PRESS 뒤 RELEASE를 `finally`에서 시도합니다.
- `LinkedMomentaryPushButtonComponent`처럼 일반 momentary push의 상호작용을 상속한 subclass는 PRESS context를 유지한 채 중간 DB physical ACT를 수행하고 RELEASE합니다. 오래 누른다는 이유로 `ACT HOLD`를 합성해 제품의 hold-lock 의미로 바꾸지 않으며, 대표 runtime의 held ON·중간 ACT·release OFF를 확인한 뒤에만 같은 계열로 분류합니다.
- 같은 held control의 명시적 return 행이 뒤에 있으면 중간의 다른 physical 입력도 primary hold 안에서 실제 조작하고 return 행까지 유지합니다. 명시적 return 행이 없을 때만 다음 physical 입력을 보수적 release 경계로 사용합니다.

## 실행 모드

1. 메인 Unreal 프로젝트와 Harness 저장소의 **실언리얼 physical 자동검증 모드**만 정식 절차 검증에 사용합니다. 실행 명령, fresh 수명주기, Host artifact identity, 판정과 증거 위치는 [`../../docs/qa-harness-manual.md`](../../docs/qa-harness-manual.md)를 따릅니다.
2. physical adapter가 없는 컨트롤은 직접 상태 쓰기나 후보 입력 탐색으로 우회하지 않고 `COVERAGE_GAP`으로 중단합니다.
3. 격리 worktree, 백업 하네스, 기존 IOS/PIE 수동 흐름은 자동검증 실행 경로로 사용하지 않습니다.
4. Task 완료 여부만으로 PASS 처리하지 않습니다. JSON이 `FINISHED_WITH_FINDINGS`이면 findings를 해결하거나 명시한 채 결과를 보고합니다.
5. 이전 실행에서 carry-in된 `err_count`를 다음 physical action의 새 finding으로 귀속하지 않습니다. 실제 조작 또는 실제 confirm 중 새로 증가한 오류만 해당 실행에 연결합니다.
6. 회차 전체 탐색은 DB 목록을 읽기 전용 manifest로 고정하고 `run_physical_sweep.py --manifest <path> --state <new-path>`로 실행합니다. Task마다 fresh 리그를 만들고 실패 뒤에도 다음 Task를 계속하며 API workflow 상태는 쓰지 않습니다.
7. 특정 입력만 사람이 수행해야 하면 매뉴얼의 `-HumanGate STEP:I_ID`를 사용합니다. CP는 에디터·전체화면 없이 `800×450` 창 모드 `-game`, AP는 헤드리스로 실행합니다. 지정 입력에는 ACT를 보내지 않고 목표·release STATE와 Host 진행을 관찰하며 실행 뒤 리그를 대칭 종료합니다.
8. 소유자 blocker 이후의 구간은 같은 root cause를 여러 Task에서 중복 실행하지 않습니다. 영향 Task/행을 묶어 보고하고 정정 뒤 P2 fresh 회귀를 실행합니다. 별도 Host 계약 없이 skip된 후속 결과를 PASS 또는 부분 PASS로 기록하지 않습니다.

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
| 2 | DT_ControlData 미등록 ID | 정보 | 표면 coverage gap. SIGNAL·Host 링크·동일 의미 활성 ID 교차검증 뒤 미구현/DB 식별자 결함으로 귀속 |
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
- DT_ControlData.csv에 없음 → physical 자동검증의 표면 판정은 `COVERAGE_GAP`. DB 변수명·`astd/fstd`, Host `EX_IN[].DATA`, 같은 의미의 활성 ID, Unreal 태그·송신 경로를 교차검증한다.
- 구형 SIGNAL-disabled/dummy ID와 현재 활성 ID가 따로 있음 → **DB 식별자 결함** (`DB_I_ID_LEGACY_ORPHAN`/`DB_IDENTIFIER_MISMATCH`). 하니스 별칭 금지.
- 활성 DB/Host ID인데 DT와 실제 Unreal 경로가 모두 없음 → **Unreal/control data 미구현** 후보.
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

Inspection 상태는 pre-flight 맥락이다. 기존 FAIL이 있어도 현재 지원되는 physical control은 실행하며, FAIL API를 절차 skip이나 자동 판정 입력으로 호출하지 않는다. 현재 runtime의 실제 coverage gap과 같은 MainStep일 때만 새 경계 verdict로 결합한다.

### 사전 검증 후 분기

- **오류 있음**: 원인 경계와 증거를 보고. DB 정의 결함이 독립적으로 확인된 경우에만 별도 수정 후 fresh 재검증
- **경고만**: 사용자에게 알리고 테스트 진행 여부 확인
- **모두 PASS**: 바로 Phase 3으로

---

## Phase 3: Fresh 실행 설정

`app_config.ini`를 수동 편집하지 않습니다. 매뉴얼의 PowerShell runner가 control session lock을 획득하고 Host `WAIT` 확인 후 UDP21로 Task와 Step 1을 설정한 다음 `INIT → RUN` 순서로 시작합니다. AutomationDriver readiness 뒤에는 자동 카메라 비영속 비활성화와 CP/AP 커버 선행조건 결과를 확인합니다.

---

## Phase 4: 테스트 진행

`qa/runs/physical_<TaskId>_<timestamp>.json`의 `outcome`, `terminal_verdict`, `preconditions`, `results`, `findings`, `artifacts`, `rig_artifacts.host`를 판정 근거로 사용합니다. Host 실제 경로와 SHA-256이 없거나 활성 경로가 불일치하면 정식 제품 판정으로 승격하지 않습니다. 프로세스 종료 코드 0이어도 `FINISHED_WITH_FINDINGS`일 수 있으므로 JSON을 생략하지 않습니다. 조작은 Harness가 실제 Unreal의 `ACT PRESS/HOLD/HOLD_WORLD/RELEASE` API로 수행합니다. held action은 `state_held`, `held_phase`, `held_placeholder`, `held_release_boundary`, `held_intervening_action`, `held_explicit_release_boundary`, `held_release_observed`와 press-to-release 간격을 함께 확인합니다. EGI readiness를 사용한 결과는 첫 `host_observations`의 `iufc_readiness_gate`, `required_marker`, `observer.route/timetag/text`, `elapsed_seconds`를 확인합니다. `KNOWN_INSPECTION_FAIL_COVERAGE_BOUNDARY`이면 원래 `action.verdict=COVERAGE_GAP`과 `db_inspection_context[].advisory_only=true`, 같은 `ms_step_id`의 inspection 메모를 분리해 확인합니다. 자연 release나 준비 상태 미관측이 Host 오류를 드러내더라도 release 생략, 고정 대기, 직접 상태 쓰기로 통과시키지 않습니다.

사람 게이트 실행은 `execution_mode=HUMAN_GATE`, 지정 입력의 `HUMAN_GATE_PASS`, `human_observation.target_observed/release_observed`, `err_count`, 그리고 지정 EquipmentId에 ACT가 없음을 함께 확인합니다. primary hold 중 하네스가 수행한 중간 DB 입력은 `HELD_INTERVENING_PASS`와 `actions[]` 증거가 있어야 합니다.

### 실패 시 디버깅 연계

Step 실패 보고 시 `/qa-signal`로 신호 디버깅:

```
/qa-signal {TASK_ID} {FAIL_STEP_NO}
```

## Phase 5: 결과 등록과 명시적 외부 게시

physical 결과는 먼저 절차 검증 SSOT에 등록한다. 이 등록은 검증 흐름의 필수 단계이며 외부 API 쓰기가 아니다.

```powershell
Set-Location E:\KAI_VCBT\fa50visualdev_new
python Scripts\qa_procedure_status.py record-auto `
  --report E:\KAI_HOST\iostestapp\qa\runs\physical_<TaskId>_<timestamp>.json
```

아래 Inspection/workflow/QA issue API는 **명시적 외부 게시 모드**에서만 사용한다. 사용자가 게시를 요청하지 않았다면 결과 요약과 현재 IssueKey까지만 보고하고 Phase 5-1~5-3을 실행하지 않는다.

게시 요청이 있을 때도 physical workflow PASS 기록은 clean `FINISHED`와 필수 증거 보존이 확인된 경우에만 수행합니다. `FINISHED_WITH_FINDINGS`, `BLOCKED`, `COVERAGE_GAP`, `KNOWN_INSPECTION_FAIL_COVERAGE_BOUNDARY`를 PASS 상태로 기록하지 않습니다.

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

- [`../../docs/qa-harness-validation-dcs-p3-20260722-020057.md`](../../docs/qa-harness-validation-dcs-p3-20260722-020057.md): 잔여 DCS 14 Task의 12건 해결·2건 AFT 페이지 선행조건 결함 재분류 기록
- [`../../docs/qa-harness-validation-394009-334006-followup-20260722-004256.md`](../../docs/qa-harness-validation-394009-334006-followup-20260722-004256.md): FWD Wheel 스케일 수정과 ID 259·245 중단점 재분류 기록
- [`../../../docs/adr/006-qa-reject-stale-control-id-aliases.md`](../../../docs/adr/006-qa-reject-stale-control-id-aliases.md): stale DB control ID를 하니스 별칭으로 우회하지 않는 결정
- [`../../../docs/adr/007-qa-inspection-status-is-advisory.md`](../../../docs/adr/007-qa-inspection-status-is-advisory.md): DB Inspection 상태를 실행 지시가 아닌 읽기 전용 QA 맥락으로 결합하는 결정
- [`../../docs/qa-harness-validation-inspection-boundary-20260722-082122.md`](../../docs/qa-harness-validation-inspection-boundary-20260722-082122.md): Task 321003 Step 11의 실제 runtime 경계와 기존 Inspection FAIL 결합 검증
- [`../../docs/qa-harness-validation-all-procedural-p1-20260721-211000.md`](../../docs/qa-harness-validation-all-procedural-p1-20260721-211000.md): 전체 107 Task P1 탐색과 원인 경계 1차 재분류
- [`../../docs/qa-all-procedural-sweep-plan-20260721.md`](../../docs/qa-all-procedural-sweep-plan-20260721.md): 전체 107 Task 하네스 보강·대표 분석·P2 회귀 체크리스트
- [`../../docs/qa-harness-validation-dcs-p2-20260721-230903.md`](../../docs/qa-harness-validation-dcs-p2-20260721-230903.md): 실제 Unreal DCS 펄스 재무장 검증, DB 입력 그룹·시간 준비도 재분류 기록
- [`../../docs/qa-harness-validation-iufc-readiness-20260722-002223.md`](../../docs/qa-harness-validation-iufc-readiness-20260722-002223.md): 실제 UDP15 `RDY` 관측과 394009·334006 EGI 대표 Step 확정 기록
- [`../../docs/qa-harness-validation-host-artifact-20260721-233920.md`](../../docs/qa-harness-validation-host-artifact-20260721-233920.md): Host artifact drift와 Task 394024 최신 x64 clean A/B 확정 기록
- [`../../docs/qa-harness-ssot.md`](../../docs/qa-harness-ssot.md): 언리얼 모사 하네스의 목적, 경계, 금지사항, 판정 기준
- [`../../docs/qa-harness-manual.md`](../../docs/qa-harness-manual.md): 메인 통합 환경의 fresh 실행, 결과 판독, 종료와 문제 해결 매뉴얼
- [`../../docs/qa-harness-validation-394020-20260720.md`](../../docs/qa-harness-validation-394020-20260720.md): 기준 구현의 확인사항, 미해결 이슈, 미확인 범위 기록
- [`../../docs/qa-harness-validation-world-input-20260721-110535.md`](../../docs/qa-harness-validation-world-input-20260721-110535.md): 카메라 독립 월드 입력, Tasks 394024·370002 확인·미확인 기록
- [`../../docs/qa-harness-validation-6thqa-p9-20260721-113727.md`](../../docs/qa-harness-validation-6thqa-p9-20260721-113727.md): 보강된 하네스의 6차 QA 10 Task 전체 회귀와 잔여 분류
- [`../../docs/qa-harness-validation-6thqa-p11-20260721-133802.md`](../../docs/qa-harness-validation-6thqa-p11-20260721-133802.md): confirmation-aware 6차 QA 10 Task 최신 전체 회귀와 최종 분류
- [`../../docs/qa-harness-validation-5thqa-p1-20260721-153857.md`](../../docs/qa-harness-validation-5thqa-p1-20260721-153857.md): 5차 QA 10 Task 최초 전체 탐색과 hold-conditioned 경계 분류
- [`../../docs/qa-harness-validation-5thqa-p2-20260721-164329.md`](../../docs/qa-harness-validation-5thqa-p2-20260721-164329.md): hold-conditioned 수명주기 보강 뒤 5차 QA 10 Task 2차 전체 회귀 역사 기록
- [`../../docs/qa-harness-validation-324000-human-gate-20260721-173708.md`](../../docs/qa-harness-validation-324000-human-gate-20260721-173708.md): 교차 Step hold 수정과 Task 324000 자동·사람 clean 검증
- [`../../docs/qa-harness-validation-5thqa-p3-20260721-181545.md`](../../docs/qa-harness-validation-5thqa-p3-20260721-181545.md): 교차 Step hold 보강 뒤 5차 QA 10 Task 최신 전체 회귀와 최종 분류
- [`../../docs/db-host-judgment-reference.md`](../../docs/db-host-judgment-reference.md): DB 컬럼 ↔ Host 판정 로직 레퍼런스
- [`../qa-signal/skill.md`](../qa-signal/skill.md): 신호 검증 스킬
