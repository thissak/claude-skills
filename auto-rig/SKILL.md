---
name: auto-rig
description: 사용자가 "자동리그 TASK_ID", "자동리그 5차·6차", 또는 "자동리그 --all"이라고 말하면 자동검증(실언리얼 CLI 물리 검증)을 실행한다. `--all`은 현재 DB의 전체 절차를 fresh 실행하고 전회 대비 회귀·진전·잔여 이슈를 정리해 일일 회귀 문서까지 갱신한다. 예 - "자동리그 394020", "자동리그 6차", "자동리그 5차", "자동리그 --all".
---

# 자동 리그 (자동검증 물리 실행)

사용자가 "자동리그 + 절차번호(또는 회차)"를 말하면 해당 범위의 자동검증을 실행한다. `자동리그 --all`만 현재 DB 전체 절차의 일일 회귀·비교·문서화까지 수행한다. `--all` 없는 실행은 해당 Task의 현재 검증 SSOT만 갱신하며 일일 기준선이나 회귀 문서는 갱신하지 않는다.

목적·금지사항·판정 계약은 `.claude/docs/qa-harness-ssot.md`, 운영법은 `.claude/docs/qa-harness-manual.md`(§5 실행, §7 판정 읽는 법)가 정본이다. 모든 실행 결과의 현재 상태 합성은 `.claude/docs/qa-procedure-verification-ssot.md`를 따른다. `--all`은 추가로 `.claude/docs/qa-daily-full-regression-ssot.md`와 `.claude/docs/qa-procedure-fix-tracker.md`를 따른다. **실행·수정 전 반드시 해당 SSOT를 읽는다.**

## 0. 선행 확인

작업 디렉터리: `E:\KAI_HOST\iostestapp`

- 실행 전에 runner의 rig session lease로 Host·CP·AP·같은 프로젝트 Unreal·Python IOS 점유를 확인한다.
- 하나라도 이미 실행 중이거나 다른 runner의 lease가 살아 있으면 `RIG_IN_USE`로 중단한다. 기존 프로세스를 재사용하거나 `qa_rig.py down`으로 강제 종료하지 않는다.
- 빈 상태에서 lease를 획득한 runner만 Host·CP·AP를 fresh 기동하며, 종료 시 자신이 기록한 정확한 PID만 대칭 종료한다. 점유 여부가 불명확해도 보수적으로 중단한다.

## 1. 인자 해석과 실행

실행은 수 분~수십 분 걸리므로 **백그라운드로 실행**하고 완료 통지를 기다린다. 장시간 프로세스는 메인 세션에서 관리한다(서브에이전트 bg 금지).

| 사용자 입력 | 실행 |
|---|---|
| Task 번호 1개 | `powershell -ExecutionPolicy Bypass -File qa\tools\run_physical_task.ps1 -TaskId <id> -UnrealProject E:\KAI_VCBT\fa50visualdev_new\FA50VisualDev.uproject` |
| 긴 Task 수정 지점만 빠르게 확인 | 위 단건 명령에 `-StartStep <step>` 추가. `DIAGNOSTIC_*`, `baseline_eligible=false`이며 최종 PASS 근거로 사용 금지 |
| `6차` | `powershell -ExecutionPolicy Bypass -File qa\tools\run_physical_sweep.ps1` (기본 manifest=6차) |
| `5차` | `... run_physical_sweep.ps1 -Manifest qa\plans\5th_qa_20260721.json -State qa\runs\sweeps\5th_qa_<오늘>.json` |
| Task 번호 여러 개 | sweep을 `-TaskId`로 반복하거나, 번호별 단건 실행을 순차로 |
| `--all` | 아래 `--all` 전용 전체 회귀·문서화 절차를 끝까지 수행 |

- 사람이 특정 스텝만 직접 수행하는 혼합 실행은 `-HumanGate STEP:I_ID` (매뉴얼 §5.3).
- `-StartStep`은 `INIT`에서 UDP12 목표 Step 도달을 확인한 뒤 `RUN`으로 전환한다. 기본 INIT 대기는 180초이며 timeout이면 RUN으로 넘어가지 않는다.
- `-StartStep` 진단이 성공해도 수정 완료 판정은 Step 1 fresh 단건 실행으로 다시 확인한다.
- 중단 후 재개는 sweep `-Resume`, 계획 확인은 `-DryRun`.
- `--all`은 Task 번호·회차·`StartStep`·`HumanGate`와 결합하지 않는다. 결합 입력은 실행하지 말고 범위를 다시 확인한다.

### 1.1 단건·회차 결과의 현재 SSOT 등록

각 physical 실행이 끝나면 에이전트가 결과 JSON을 판독한 뒤 아래 내부 등록기를 실행한다. 사용자에게 이 명령을 실행시키지 않는다.

```powershell
Set-Location E:\KAI_VCBT\fa50visualdev_new
python Scripts\qa_procedure_status.py record-auto `
  --report E:\KAI_HOST\iostestapp\qa\runs\physical_<TaskId>_<timestamp>.json
```

- Step 1 fresh는 `AUTO_FULL`로 현재 Task 행을 갱신한다.
- `StartStep`은 `PARTIAL` 진단 증거만 추가하며 기존 전체 issue를 닫지 않는다.
- 단건 fresh clean은 같은 Task의 이전 자동 IssueKey를 닫을 수 있지만 휴먼·정적·애니메이션 IssueKey는 자동으로 삭제하지 않는다.
- 현재 표 `.claude/docs/qa-procedure-verification-current.md`는 생성 결과이므로 직접 편집하지 않는다.

## 2. `--all` 전용 전체 회귀·문서화

`--all`은 raw sweep 실행으로 끝내지 않는다. 전체 실행, 전회 비교, 회귀 재현, 잔여 이슈 정리, 문서 갱신을 하나의 작업으로 완료한다. 수 시간 걸릴 수 있으므로 백그라운드 프로세스는 메인 세션이 소유하고 완료까지 계속 관찰한다.

1. `.claude/docs/qa-daily-full-regression-ssot.md`의 보고서 색인에서 직전 공식 `COMPLETE` 기준선과 최신 날짜별 보고서를 읽는다.
2. `python qa_rig.py status`, `python qa\tools\db_query_readonly.py --test`, `python -m pytest -q`로 점유·DB read-only·정적 preflight를 확인한다. `RIG_IN_USE`이면 기존 세션을 종료하지 말고 일일 SSOT 규칙대로 `NOT_RUN/RIG_IN_USE`를 기록하며 기준선을 바꾸지 않는다.
3. `kai_readonly`, `transaction_read_only=on` 세션에서 `tbl_step`이 있는 현재 전체 Task inventory를 읽어 KST timestamp의 새 manifest를 만든다. 기존 timestamp manifest를 재사용하거나 덮어쓰지 않는다. Task 수·distinct Step 수·`tbl_step` 행 수와 manifest SHA-256을 보존한다.
4. 새 manifest와 새 state로 전체 sweep을 시작한다.

   ```powershell
   powershell -ExecutionPolicy Bypass -File qa\tools\run_physical_sweep.ps1 `
     -Manifest qa\plans\all_procedural_tasks_<KST timestamp>.json `
     -State qa\runs\sweeps\daily_full_<KST timestamp>.json
   ```

5. 중단되면 같은 manifest/state에 `-Resume`을 사용한다. 계획 Task가 모두 terminal이고 sweep state가 `COMPLETE`가 될 때까지 새 일일 기준선으로 판정하지 않는다.
6. 계획/결과/고유 Task 수, 각 `physical_*.json`, CP/AP/monitor/runner artifact, timeout, `baseline_eligible`, 시작 Step, Task ID, 외부 workflow write, 직접 `SET/GET/SETID` 사용을 검사한다. 하나라도 누락되면 증거 불완전 상태를 명시하고 clean 기준선으로 승격하지 않는다.
7. 직전 공식 기준선과 현재 결과를 Task별로 비교한다. 원본 `classification`·`outcome`·`terminal_verdict`를 보존하고 `STABLE_CLEAN`, `NEW_CLEAN`, `REGRESSION_CANDIDATE`, `PROGRESS_CANDIDATE`, `UNCHANGED_BLOCKER`, `CHANGED_BLOCKER`, `NEW_TASK`, `REMOVED_TASK`로 분류한다. Inventory 변화는 회귀 수치와 분리한다.
8. `REGRESSION_CANDIDATE`는 같은 소스 상태에서 Step 1 fresh 단건으로 우선 재실행해 `REGRESSION_CONFIRMED` 또는 미재현으로 정리한다. `PROGRESS_CANDIDATE`는 이전 첫 blocker가 현재 보고서에서 실제 PASS하고 더 뒤의 독립 blocker가 드러난 경우에만 인정한다.
9. 남은 이슈는 현재 첫 blocker만 요약하고 `하네스/인프라`, `DB 절차`, `ControlData/SSOT`, `Unreal`, `Host`, `소유자 판단 대기`로 책임 경계를 나눈다. 자동으로 코드를 고치지 말고, 확인된 회귀 → 여러 Task를 가리는 공통 문제 → 새로 드러난 문제 → 지속 문제 순으로 다음 수정 큐를 작성한다.
10. `COMPLETE` raw sweep을 전체 절차 현재 SSOT의 자동 기준선으로 반영한다.

    ```powershell
    Set-Location E:\KAI_VCBT\fa50visualdev_new
    python Scripts\qa_procedure_status.py build-auto `
      --sweep E:\KAI_HOST\iostestapp\qa\runs\sweeps\daily_full_<timestamp>.json
    ```

    이후 Step 1 fresh로 재현한 회귀 후보는 §1.1의 `record-auto`로 차례로 등록한다.
11. 다음 문서를 UTF-8로 갱신한다.
    - 새 `.claude/docs/qa-daily-full-regression-YYYYMMDD-HHMMSS.md`: 실행 식별, 증거 무결성, 전회 대비 요약, 성과, 회귀 재현, 지속 문제, 다음 수정 큐, 기준선 판정을 기록한다. 과거 보고서는 수정하지 않는다.
    - `.claude/docs/qa-daily-full-regression-ssot.md`: 보고서 색인에 한 줄을 추가한다.
    - `.claude/docs/qa-procedure-fix-tracker.md`: 실제 수정 대상이나 fresh 검증 상태가 바뀐 항목만 갱신한다. 날짜별 보고서의 전체 이슈를 복사하지 않는다.
    - `.claude/docs/qa-procedure-verification-state.json`과 `.claude/docs/qa-procedure-verification-current.md`: 등록기가 생성한다. 수동 편집하지 않는다.
    - `.claude/docs/qa-harness-ssot.md`와 별도 `.claude/docs/qa-harness-validation-*.md`는 하네스 계약 변경 또는 독립적인 상세 원인·검증 증거가 생겼을 때만 갱신·추가한다.
12. 최종 보고에는 전체 상태, clean/non-clean 증감, 신규 clean, 확인된 회귀, 진전, 잔여 이슈 책임 경계, 다음 수정 대상, raw sweep과 현재 표·갱신 문서 경로를 포함한다.

## 3. 판정 읽기 (매뉴얼 §7 요약)

- **종료 코드로 판단 금지**: `FINISHED_WITH_FINDINGS`도 exit 0. 반드시 결과 JSON(`qa/runs/physical_<TaskId>_<ts>.json`)의 `outcome`·`terminal_verdict`·`findings[]`를 읽는다.
- `FINISHED`=클린 / `FINISHED_WITH_FINDINGS`=완주했으나 findings 조사 필요 / `BLOCKED`(exit 2)=terminal_verdict에서 원인(`COVERAGE_GAP`·`NO_PHYSICAL_EDGE`·`PROCEDURE_MISMATCH` 등) 확인.
- `KNOWN_INSPECTION_FAIL_COVERAGE_BOUNDARY`는 현재 실행의 실제 `COVERAGE_GAP`과 같은 MainStep에 기존 DB Inspection FAIL이 함께 있다는 뜻이다. `action.verdict`와 `db_inspection_context[].advisory_only`를 분리해 읽으며, 동일 결함 재현이나 자동 skip으로 해석하지 않는다.
- 증거는 JSON 옆 `_artifacts/`(autodrv_cp/ap.log, qa_monitor.log)와 함께 읽는다.
- 사용자 보고: outcome, 스텝 진행 범위, findings 요약, 보고서 경로.

## 4. 금지 (SSOT 발췌)

- 후보 입력 탐색·임의 반복 금지, 초기 상태 사전 조성 금지, SET/GET/SETID 직접 상태 경로 없음.
- 하네스 한계를 Host/DB/운영 Unreal 수정으로 해결하지 않는다 — `COVERAGE_GAP` 등은 그대로 보고.
- 기존 Inspection FAIL만으로 ACT를 생략하거나 Step을 넘기거나 API에 결과를 쓰지 않는다.
- 실행 후 정리는 runner의 `down_owned`가 담당한다. 에이전트가 별도로 `python qa_rig.py down`을 호출하지 않는다. sweep도 Task별 child runner의 lease·소유 PID 정리를 사용한다.
