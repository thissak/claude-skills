---
name: human-rig
description: 사용자가 "휴먼리그 <절차번호|회차>"라고 말하면 회차 사람 관찰 세션(휴먼 리그)을 띄운다. 예 - "휴먼리그 321003", "휴먼리그 6차", "휴먼리그 394020 394024". 리그 기동·Task 셋팅까지 자동 수행 후 사용자는 언리얼 조작만 한다.
---

# 휴먼 리그 (회차 사람 관찰 세션) 기동

사용자가 "휴먼리그 + 절차번호(또는 회차)"를 말하면 사람 관찰 세션을 띄운다. 계약은 `docs/qa-harness-ssot.md`의 "사람 관찰 세션 모드", 운영법은 `docs/qa-harness-manual.md` §5.5가 정본이다.

**역할 분담(고정)**: 에이전트가 세션을 열고 명령(start/next/redo/skip/problem/auto/end)을 담당한다. 사용자는 언리얼 조작만 한다.

## 1. 인자 해석

작업 디렉터리: `E:\KAI_HOST\iostestapp`

| 사용자 입력 | 해석 |
|---|---|
| `6차`, `6차 QA` | `--manifest qa\plans\6th_qa_20260721.json` (전체 회차, 필터 없음) |
| `5차`, `5차 QA` | `--manifest qa\plans\5th_qa_20260721.json` |
| Task 번호 1개 이상 | 아래 멤버십 확인 후 `--tasks <콤마목록>` 또는 ad-hoc manifest |

Task 번호가 오면 **manifest 멤버십을 먼저 확인**한다 (빈 큐는 start가 거부함):

```powershell
python -c "import json; print([t['task_id'] for t in json.load(open(r'qa\plans\6th_qa_20260721.json', encoding='utf-8'))['tasks']])"
```

- 전부 6차(또는 5차)에 있으면: 그 manifest + `--tasks <ids>`
- 어느 manifest에도 없으면: ad-hoc manifest 생성 후 필터 없이 사용

```powershell
python -c "
import json, time
ids = [321003]  # 사용자 지정 번호로 교체
path = rf'qa\runs\human_sessions\adhoc_{time.strftime(\"%Y%m%d_%H%M%S\")}_manifest.json'
json.dump({'schema_version': 1, 'name': 'adhoc_human', 'tasks': [{'task_id': i} for i in ids]},
          open(path, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print(path)
"
```

## 2. 기동

기동은 수 분 걸리므로 **백그라운드로 실행**하고 완료 통지를 기다린다 (렌더 CP·AC 부팅 포함).

```powershell
Set-Location E:\KAI_HOST\iostestapp
python -m qa.human_session start --manifest <manifest> [--tasks <ids>]
```

- 실행 전 별도 정리 불필요 (데몬이 `qa_rig.down → up(interactive CP+AP)` 수행, 창 800×450)
- start가 거부하면 이유가 JSON으로 온다: `writer GUI ... running`(뷰어 아닌 IOSTestApp 종료 필요), `no matching tasks`(번호가 manifest에 없음 → ad-hoc 경로)
- ok 후 `python -m qa.human_session status`로 확인: `rig_ready: true` + 첫 Task `active` + `mtd_mode: RUN_MODE`

준비되면 사용자에게 보고: 현재 Task(id·이름), 현재 요구 입력(status의 description), 그리고 조작 중 쓸 말("다음"/"다시"/"건너뛰어"/"문제야"/"이건 자동으로"/"종료").

## 3. 세션 중 명령 매핑

| 사용자가 말하면 | 실행 |
|---|---|
| 다음 | `python -m qa.human_session next` |
| 다시 | `python -m qa.human_session redo` |
| 건너뛰어 | `python -m qa.human_session skip` |
| 문제야 | `python -m qa.human_session problem on` + 타임라인·로그 분석 (아래 §4) |
| (해결 후) | `python -m qa.human_session problem off` — 보고서 경로의 `acts_issued`가 0인지 확인 |
| 이건 자동으로 | `python -m qa.human_session auto <task_id>` (problem off 상태에서만; warm-rig라 fresh 증거 아님) |
| 종료/리그 내려줘 | `python -m qa.human_session end` 후 `python qa_rig.py status`로 all down 확인 |

## 4. 문제 분석 루틴

세션 dir은 start 응답의 `session_dir`. 분석 소스 우선순위:

1. `<session_dir>\timeline.jsonl` — 현재 Task 구간(host_phase·err_change·ios_confirm_*·session_error)
2. `E:\KAI_HOST\debug_qa.log` — Host RECV/JUDGE/STEP (JUDGE는 ERR_COUNT==0일 때만 발화)
3. `E:\KAI_VCBT\fa50visualdev_new\Saved\Logs\autodrv_cp.log`(·`autodrv_ap.log`) — `[SetControlState]`=UDP100 외부 주입(Host발), 사용자 조작은 Interact 경로. **"혼자 움직임/혼자 넘어감"은 1순위로 Host self-echo·자동시현 확인** (검증 기록 `docs/qa-harness-validation-human-session-20260721-215500.md`의 이슈 2·3 패턴)

err가 쌓여 진행이 멈추면: err_i_ids의 컨트롤을 원위치로 되돌리게 안내(err 감소 후 판정 재개), 안 되면 `redo`.

## 5. 금지·주의

- 사람 세션 중 ACT/SET/SETID 절대 금지 (SSOT). 세션 기록은 자동검증 PASS 증거로 승격 금지.
- Connect 상태의 IOSTestApp GUI와 병행 금지 (뷰어 `--viewer`만).
- 장시간 리그 프로세스는 메인 세션에서 관리 (서브에이전트 bg 금지).
