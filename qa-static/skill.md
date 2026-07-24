---
name: qa-static
description: 사용자가 "qa-static", "정적 QA", "정적 검증", "static qa", "매핑 검증"이라고 말하면 DB i_id 정적 교차 검증, Task별 리포트, 승인된 수정 조율, 절차 검증 SSOT 등록을 수행한다. Task ID 목록을 지정하거나 전체를 검사할 수 있다.
---

# 정적 QA 오케스트레이터

훈련항목 전체를 파악하고, 검증 에이전트를 병렬 실행하여 매핑 누락을 탐지하고, 수정을 조율합니다.

## 전체 절차 검증 SSOT 연결

실행 전에 [`../../docs/qa-procedure-verification-ssot.md`](../../docs/qa-procedure-verification-ssot.md)를 읽는다. `.claude/qa-reports/history.md`는 정적 QA 실행 이력이고, Task의 현재 종합 판정은 `.claude/docs/qa-procedure-verification-current.md`가 소유한다.

- Task별 정적 PASS/ERROR/WARN을 `record-supporting --method STATIC`으로 등록한다.
- 실제 절차 진행을 차단하는 정적 결함만 `ISSUE --blocking`으로 기록한다.
- 경고·검토 항목은 `OBSERVATION`으로 기록한다.
- 정적 전체 PASS는 정적 차원의 `CLEAN`일 뿐 runtime Task 전체 clean을 단독으로 만들지 않는다.
- 수정·재검증으로 기존 정적 IssueKey가 해소되면 `RESOLVED --resolves <IssueKey>`로 연결한다.

## 역할

- **전체 그림 파악**: DB에서 훈련항목 현황 조회, 무엇을 검증/수정할지 판단
- **에이전트 지시**: 검증/수정 에이전트에 구체적 작업 명령
- **결과 조율**: 리포트 수집, 사용자 보고, 승인 요청
- **DB 수정**: 승인된 DB 수정만 직접 실행 (스냅샷/트랜잭션)

## 검증 체인

```
DB tbl_step (i_id)
  ↓
[CHECK 1] tc_lnk_ext_input  → Host EX_IN 연결 여부 (ERROR, equipment_mapping 존재하는 것만)
[CHECK 2] equipment_mapping → Host→언리얼 매핑 여부 (WARN)
[CHECK 3] DT_ControlData    → 언리얼 컨트롤 등록 여부 (WARN)
[CHECK 4] UDP path          → UDP 통신 경로 존재 여부 (WARN)
```

## 에이전트 구성

| 에이전트 | 역할 | 병렬 |
|----------|------|------|
| `qa-static-verify` | Task 1개 검증 + 리포트 작성 | 1 Task = 1 에이전트, 병렬 가능 |
| `qa-static-fix` | 승인된 파일 수정 실행 | 수정 완료 후 재검증 |

## 실행 절차

### Phase 0: 히스토리 확인

실행 시작 전에 이전 실행 이력을 읽어서 사용자에게 표시합니다.

1. 히스토리 파일 읽기:
```
E:\KAI_VCBT\fa50visualdev_new\.claude\qa-reports\history.md
```

2. 파일이 존재하면 최근 5건을 요약 표시:
```
=== 정적 QA 히스토리 ===
[2026-02-19 08:19] 80 Task | ERROR 56 | WARN 103
[2026-02-18 15:30] 3 Task (324004,333005,334003) | ERROR 2 | WARN 5
```

3. 파일이 없으면 "이전 실행 이력 없음"으로 표시하고 계속 진행

### Phase 1: 현황 파악

1. 타임스탬프로 리포트 디렉토리 생성:
```bash
mkdir -p "E:/KAI_VCBT/fa50visualdev_new/.claude/qa-reports/{YYYYMMDD_HHMMSS}"
```

2. 전체 스캔으로 이슈 있는 Task 식별:
```bash
python "E:/KAI_HOST/iostestapp/qa/tools/static_qa.py" --all --output "E:/KAI_VCBT/fa50visualdev_new/.claude/qa-reports/{YYYYMMDD_HHMMSS}/overview.json"
```

3. overview.json 읽고 이슈 있는 Task 목록 추출 (`by_task` 키에서 task_id 목록)

### Phase 2: 검증 에이전트 병렬 실행

이슈 있는 Task마다 검증 에이전트를 병렬로 실행합니다.

**하나의 메시지에서 여러 Task() 호출로 병렬 실행:**

```
Task(subagent_type="general-purpose", prompt="""
정적 QA 검증 에이전트로 동작하세요.

## 작업
Task {TASK_ID}에 대해 정적 QA 검증을 수행하고 리포트를 작성하세요.

## 절차
1. static_qa.py 실행:
   python "E:/KAI_HOST/iostestapp/qa/tools/static_qa.py" --task_id {TASK_ID}

2. JSON 리포트 읽기:
   E:\KAI_HOST\iostestapp\qa\tools\qa_report_{TASK_ID}.json

3. 이슈를 다음 카테고리로 분류:
   - HOST_FIX: ex_in 누락 → Host 개발자 작업 필요
   - SSOT_FIX: equipment_mapping/control_data 누락 → /generate-ssot 필요
   - REVIEW: udp_path 누락 → 수동 확인 필요

4. 마크다운 리포트를 아래 파일에 저장:
   E:\KAI_VCBT\fa50visualdev_new\.claude\qa-reports\{TIMESTAMP}\{TASK_ID}.md

   리포트 형식:
   # Task {TASK_ID} 정적 QA 리포트
   ## 요약
   - 검증 i_id: N개 | ERROR: N건 | WARN: N건
   ## HOST_FIX / SSOT_FIX / REVIEW
   (각 카테고리별 테이블)
   ## PASS
   이슈 없는 i_id: N개

5. 요약을 텍스트로 반환
""")
```

**병렬 실행 규칙:**
- 이슈 있는 Task만 에이전트 실행 (PASS인 Task는 스킵)
- 한 번에 최대 5개 에이전트 병렬 실행
- 5개 초과 시 배치로 나눠서 순차 실행

### Phase 3: 결과 수집 및 사용자 보고

1. 모든 에이전트 완료 후 per-task 리포트 읽기
2. 전체 요약 작성하여 `{report_dir}/summary.md`에 저장
3. 사용자에게 카테고리별 요약 표시:

```
=== 정적 QA 결과 ===

검증 Task: 80 | 이슈 Task: 33 | 정상 Task: 47

카테고리별 이슈:
  HOST_FIX (Host 개발자):      2개 i_id
  SSOT_FIX (SSOT 재생성):     50개 i_id
  REVIEW (수동 확인):          3개 i_id

리포트: .claude/qa-reports/{TIMESTAMP}/
```

4. 사용자에게 질문:
   - "수정 가능한 항목이 있으면 진행할까요?"
   - "그 외 항목은 리포트에 기록되었습니다."

### Phase 4: 승인된 수정 실행

**DB 수정 (오케스트레이터가 직접):**

DB 수정이 필요한 경우 오케스트레이터가 CLAUDE.md의 DB 수정 절차를 따라 직접 실행:
1. `save_task_snapshot(task_id, '정적 QA 수정')`
2. 사용자에게 수정 계획 표시 및 최종 승인
3. 트랜잭션으로 실행
4. 결과 확인
5. 문제 시 `restore_task_snapshot(snapshot_id)`

### Phase 5: 최종 보고 및 히스토리 기록

1. 수정 결과 요약
2. 잔여 이슈 목록 (HOST_FIX, SSOT_FIX 등 자동 수정 불가 항목)
3. 다음 조치 제안

4. **히스토리 파일에 이번 실행 기록 추가** (`E:\KAI_VCBT\fa50visualdev_new\.claude\qa-reports\history.md`):

파일이 없으면 새로 생성. 최신 항목을 파일 상단에 추가 (최신순 정렬).

```markdown
## {YYYY-MM-DD HH:MM} | {전체/Task목록}

| 항목 | 값 |
|------|-----|
| 대상 | 전체 80 Task / Task 324004, 333005 |
| 이슈 Task | N개 |
| ERROR | N건 (eq_id: N, ex_in: N) |
| WARN | N건 (mapping: N, control: N, udp: N) |
| 수정 | DB 수정 N건 / 없음 |
| 리포트 | `.claude/qa-reports/{TIMESTAMP}/` |

변경사항: {한줄 요약 - ex: "ex_in 필터 적용, DB 수정 3건"}
```

5. 에이전트가 Task별 결과를 현재 절차 SSOT에 등록한다. 사용자에게 명령 실행이나 표 작성을 요구하지 않는다.

```powershell
Set-Location E:\KAI_VCBT\fa50visualdev_new
python Scripts\qa_procedure_status.py record-supporting `
  --method STATIC --task <TaskId> `
  --verdict <CLEAN|ISSUE|OBSERVATION|RESOLVED> `
  --summary "<정적 검증 요약>" --scope <FULL|PARTIAL> `
  [--blocking] [--owner "<책임 경계>"] [--evidence "<리포트 경로>"] `
  [--resolves "<IssueKey>"]
```

## 참고

- **워크플로우 필터 (기본 적용)**: `2차 언리얼 통과`(11), `탑재`(15) 상태 Task는 검증 제외
  - `--no-exclude` 플래그로 전체 포함 가능
  - `--exclude-status 11 15 14` 로 제외 상태 커스터마이즈 가능
- 시스템 변수(283, 284, 285, 286, 2999, 3000)는 기본 제외
- `--include-system` 플래그로 포함 가능
- DB 접근은 `kai_readonly` (읽기 전용)
- 에이전트 정의: `.claude/agents/qa-static-verify.md`, `.claude/agents/qa-static-fix.md`
- 리포트 보존: `.claude/qa-reports/{TIMESTAMP}/` 디렉토리에 타임스탬프로 관리
