---
name: auto-rig
description: 사용자가 "자동리그 <절차번호|회차>"라고 말하면 자동검증(실언리얼 CLI 물리 검증)을 실행한다. 예 - "자동리그 394020", "자동리그 6차", "자동리그 5차".
---

# 자동 리그 (자동검증 물리 실행)

사용자가 "자동리그 + 절차번호(또는 회차)"를 말하면 자동검증을 실행한다. 목적·금지사항·판정 계약은 `docs/qa-harness-ssot.md`, 운영법은 `docs/qa-harness-manual.md`(§5 실행, §7 판정 읽는 법)가 정본이다 — **실행·수정 전 반드시 SSOT를 읽는다.**

## 0. 선행 확인

작업 디렉터리: `E:\KAI_HOST\iostestapp`

- fresh 원칙: `python qa_rig.py down`으로 수동 휴먼리그를 포함한 기존 Host·AC·CP를 정리한다. Python IOS가 직접 실행 중이면 종료한 뒤 진행한다.

## 1. 인자 해석과 실행

실행은 수 분~수십 분 걸리므로 **백그라운드로 실행**하고 완료 통지를 기다린다. 장시간 프로세스는 메인 세션에서 관리한다(서브에이전트 bg 금지).

| 사용자 입력 | 실행 |
|---|---|
| Task 번호 1개 | `powershell -ExecutionPolicy Bypass -File qa\tools\run_physical_task.ps1 -TaskId <id> -UnrealProject E:\KAI_VCBT\fa50visualdev_new\FA50VisualDev.uproject` |
| `6차` | `powershell -ExecutionPolicy Bypass -File qa\tools\run_physical_sweep.ps1` (기본 manifest=6차) |
| `5차` | `... run_physical_sweep.ps1 -Manifest qa\plans\5th_qa_20260721.json -State qa\runs\sweeps\5th_qa_<오늘>.json` |
| Task 번호 여러 개 | sweep을 `-TaskId`로 반복하거나, 번호별 단건 실행을 순차로 |

- 사람이 특정 스텝만 직접 수행하는 혼합 실행은 `-HumanGate STEP:I_ID` (매뉴얼 §5.3).
- 중단 후 재개는 sweep `-Resume`, 계획 확인은 `-DryRun`.

## 2. 판정 읽기 (매뉴얼 §7 요약)

- **종료 코드로 판단 금지**: `FINISHED_WITH_FINDINGS`도 exit 0. 반드시 결과 JSON(`qa/runs/physical_<TaskId>_<ts>.json`)의 `outcome`·`terminal_verdict`·`findings[]`를 읽는다.
- `FINISHED`=클린 / `FINISHED_WITH_FINDINGS`=완주했으나 findings 조사 필요 / `BLOCKED`(exit 2)=terminal_verdict에서 원인(`COVERAGE_GAP`·`NO_PHYSICAL_EDGE`·`PROCEDURE_MISMATCH` 등) 확인.
- `KNOWN_INSPECTION_FAIL_COVERAGE_BOUNDARY`는 현재 실행의 실제 `COVERAGE_GAP`과 같은 MainStep에 기존 DB Inspection FAIL이 함께 있다는 뜻이다. `action.verdict`와 `db_inspection_context[].advisory_only`를 분리해 읽으며, 동일 결함 재현이나 자동 skip으로 해석하지 않는다.
- 증거는 JSON 옆 `_artifacts/`(autodrv_cp/ap.log, qa_monitor.log)와 함께 읽는다.
- 사용자 보고: outcome, 스텝 진행 범위, findings 요약, 보고서 경로.

## 3. 금지 (SSOT 발췌)

- 후보 입력 탐색·임의 반복 금지, 초기 상태 사전 조성 금지, SET/GET/SETID 직접 상태 경로 없음.
- 하네스 한계를 Host/DB/운영 Unreal 수정으로 해결하지 않는다 — `COVERAGE_GAP` 등은 그대로 보고.
- 기존 Inspection FAIL만으로 ACT를 생략하거나 Step을 넘기거나 API에 결과를 쓰지 않는다.
- 실행 후 정리: `python qa_rig.py down` (sweep은 Task별 자체 재생성).
