---
name: anim-fresh
description: 사용자가 "anim-fresh", "신선도 확인", "검증 페이지 최신이야?", "애니 검증 갱신"이라고 말하면 자동시현 검증 페이지의 애셋·DB 신선도를 확인·해석·갱신하고 Task별 결과를 절차검증대장의 애니메이션 차원에 기록한다.
---

# Anim Review Freshness

자동시현 검증 페이지(`qa/runs/review/`)가 최신 애셋·DB를 반영하는지 확인하고,
애니메이터 정본(`origin/dev`)을 받아 재수집·재렌더·운영 게시까지 수행합니다.

## 운영 서버 경계

- 이 작업 PC `QART / 192.168.10.113`의 `qa/runs/review/`는 생성·점검용 staging일 뿐
  운영 페이지 서버가 아니다. 이 PC의 `qa.tools.anim.serve_review`와 8779 경로는
  deprecated이므로 실행하거나 운영 게시 source로 사용하지 않는다.
- 운영 리뷰·렌더 서버 접속 정본은 `ssh vivtech@192.168.10.73`이다. 갱신 결과는
  이 SSH 서버의 배포 경로에 반영하고, 원격 manifest와 페이지를 확인한 뒤 DB Tool
  운영 snapshot을 동기화한다. 서버가 노출하는 HTTP 주소와 포트는 SSH 서버의 현재
  설정에서 확인하며 이 PC 주소를 대체값으로 추정하지 않는다.
- SSH 서버 내부에서 실행되는 `AnimReviewServer`와 서버 자신의
  `127.0.0.1:8779` 동기 source는 현행 운영 경로다. deprecated 범위와 혼동하지 않는다.
- SSH 배포 경로나 접속 상태를 확인할 수 없으면 로컬 서버로 우회하지 말고 갱신을
  중단한 뒤 배포 경계가 확인되지 않았다고 보고한다.

## 절차검증대장 연결

실행 전에 `.claude/docs/qa-procedure-verification-ssot.md`를 읽는다. Task별 fresh/stale 결과는 에이전트가 `record-supporting --method ANIMATION`으로 현재 절차 상태에 연결한다.

- fresh는 애니메이션 차원의 `CLEAN`이며 runtime 절차 전체 clean을 단독으로 만들지 않는다.
- stale이나 실제 매핑 문제는 `ISSUE`로 기록하되 절차 진행을 차단하는 경우에만 `--blocking`을 사용한다.
- 페이지 갱신으로 기존 애니메이션 IssueKey가 해소되면 `RESOLVED --resolves <IssueKey>`로 연결한다.
- 사용자는 결과를 말로 확인할 뿐 검증대장 표나 명령을 작성하지 않는다.

## 사람 정합성 승인 SSOT

자동시현 페이지의 각 절차 행에는 사람이 현재 영상과 Subsequence의 정합성을
`승인`, `불승인`, `미검토`로 확정하는 상호 배타적 체크박스가 있다. 계약은
[`anim-consistency-approval-ssot.md`](../../docs/anim-consistency-approval-ssot.md)를 따른다.

- 승인한 occurrence만 시퀀스 재사용·자동 배치 후보 필터에 포함한다.
- 불승인은 미검토와 구분해 보존하며 승인 필터에는 포함하지 않는다.
- 페이지 재수집·재렌더는 승인 정본을 덮어쓰지 않는다.
- DB 설명, Marker, 프레임, Subsequence 경로 또는 영상 콘텐츠 지문이 바뀐 승인은
  자동으로 stale 처리하며 사람이 다시 확인하기 전까지 필터에서 제외한다.
- 체크 자체는 애니메이션 부분 승인이지 runtime Task 전체 clean 판정이 아니다.

## Step 0: 실행 경로와 Unreal 점유 확인

사람이 실행하는 기본 CP→AC 경로에서는 `UnrealEditor.exe` 또는
`UnrealEditor-Cmd.exe`가 하나라도 실행 중이면 소스 오버레이·동기화를 시작하지 않습니다.
다른 세션의 자동검증이 끝난 후 다시 실행합니다.

```bash
cd E:/KAI_HOST/iostestapp && py -3.11 -m qa.tools.anim.source_sync
```

`source_sync` 는 `origin/dev`를 fetch하고 시퀀서 경로와
`DT_TaskMasterSequence.csv`·`DT_TaskMasterSequence.uasset`만 CP 작업트리에
오버레이한 뒤, 바뀐 경로만 AC 복사 프로젝트에 동기화합니다.
오버레이 위의 사용자 변경이 발견되면 덮어쓰지 않고 중단합니다.

### GitLab `dev` Push Hook 자동 경로

SSH 연결 리뷰 서버는 `POST /api/gitlab/anim-refresh`로 GitLab Push Hook을
받습니다. 정확한 프로젝트 `fa50m-dev-new/fa50visualdev_new`와
`refs/heads/dev`, 공유 토큰이 모두 일치한 요청만 큐에 넣습니다.

- 자동 렌더는 `E:/KAI_VCBT/fa50visualdev_render` 단일 전용 worktree를 사용합니다.
  일반 CP 작업트리와 AC 복사 프로젝트는 수정하지 않습니다.
- webhook 처리를 시작할 때 전용 worktree에서 `origin/dev`를 fetch한 뒤
  `git merge --ff-only origin/dev`로 전체 Unreal 기준선을 먼저 최신화합니다.
  fast-forward할 수 없으면 렌더를 중단하며, 일반 VisualRoot는 pull/reset/clean하지
  않습니다. 이후 시퀀서 경로와 `DT_TaskMasterSequence.csv` 및
  `Content/Data/DT_TaskMasterSequence.uasset` 동기화 검증을 거쳐 stale Task를 렌더합니다.
- CP/AC 구분은 실행 레벨·UDP 구성의 차이이며 최신 시퀀서 판정용 저장소를 둘로
  나누는 근거가 아닙니다. 자동 경로에서는 AC 동기화를 비활성화합니다.
- 전용 worktree이므로 사람이 다른 Unreal Editor를 열어 둔 상태에서도
  `UnrealEditor-Cmd`를 실행할 수 있습니다. 파일 충돌은 없지만 렌더 중에는 GPU를
  함께 사용합니다.
- 여러 push가 겹치면 가장 최신 commit 요청만 보존하고 한 작업씩 실행합니다.
  freshness가 stale로 판정한 Task만 재수집·재렌더합니다.

## Step 1: 신선도 체크 실행

```bash
cd E:/KAI_HOST/iostestapp && PYTHONIOENCODING=utf-8 py -3.11 -m qa.tools.anim.freshness_check --json
```

exit 0=fresh, 1=stale, 2=오류. JSON에 `fresh`(bool), `stale_tasks`(태스크→사유 목록), `checked_utc`가 담겨 있습니다.

## Step 2: stale 사유 해석

`stale_tasks`의 각 사유는 접두사로 구분됩니다:

- `asset: <path>` — 마스 시퀀스 또는 `DT_TaskMasterSequence` 애셋이 manifest 앵커에서
  `origin/dev`까지 변경됨 → 재수집, 해시가 바뀐 Master는 재렌더 필요
- `db: steps 불일치` — DB의 스텝/애니메이션 ID/절차 텍스트가 manifest와 달라짐 → 재수집 필요
- `dirty: <path>` — 커밋 안 된 변경(보수적으로 항상 재확인 대상)

태스크별로 사유를 사용자에게 요약해서 보고하세요.

## Step 3: 갱신 이력 확인

```bash
tail -5 "E:/KAI_HOST/iostestapp/qa/runs/review/_nightly.log"
tail -5 "E:/KAI_HOST/iostestapp/qa/runs/review/_webhook.log"
```

각 줄 형식: `<UTC ISO> FRESH|SKIP|REFRESHED|ERROR ...`
- `FRESH stale=0` — 정상, 변경 없음
- `REFRESHED stale_before=N tasks=M` — stale Task 갱신 완료
- `ERROR ...` — 예외 발생, 원인 확인 필요

`_webhook.log`의 `DONE commit=<sha>`는 해당 push 요청 처리를 마쳤다는 뜻이며,
`ERROR ...`는 최신 요청을 보존한 채 재시도 중이라는 뜻입니다.

## Step 4: stale 있으면 갱신 제안

갱신은 UnrealEditor-Cmd를 직접 스폰한다(에디터를 열어둘 필요 없음). 다만 렌더가 도는 경우
GPU를 점유하므로, 평일 낮이면 야간 자동 갱신(21:00)에 맡길지 먼저 물어보세요.
이미 사용자가 GitLab Push Hook 자동 실행을 승인한 PC에서는 push마다 다시 묻지 않습니다.
수동 전체 재수집에서도 영상은 Master 콘텐츠 해시가 바뀐 건만 새로 렌더합니다.

사용자가 갱신을 원하면:

```bash
# 전체 재수집
cd E:/KAI_HOST/iostestapp && py -3.11 -m qa.tools.anim.review_run --all-anim

# 특정 태스크만
cd E:/KAI_HOST/iostestapp && py -3.11 -m qa.tools.anim.review_run <task_id> [<task_id> ...]

# SSH 서버에서 특정 태스크를 pull부터 DB Tool 게시까지 강제 갱신
# (서버 Worker 환경에서 호출)
py -3.11 -c "from qa.tools.anim.serve_review import RefreshWorker; RefreshWorker().refresh_task(<task_id>)"

# 소스 동기화 + 신선도 판정 + stale Task 재수집 + SSH 리뷰 서버 배포
# + 원격 source 기준 DB Tool 운영 스냅샷 게시
cd E:/KAI_HOST/iostestapp && py -3.11 -m qa.tools.anim.nightly_refresh
```

`RefreshWorker.refresh_task()`는 전용 RenderRoot를 `origin/dev`로 fast-forward한 뒤
내부적으로 `nightly_refresh --task <Task>`를 호출한다. 대상 Task는 freshness와 무관하게
강제 재수집하고, 완료 후 전체 freshness를 다시 판정해 다른 stale Task를 숨기지 않으며
DB Tool 운영 snapshot을 한 번 동기화한다.

이 작업 PC에서 `nightly_refresh` 또는 개별 게시 도구가 `127.0.0.1:8779`를 source로
사용하면 운영 토폴로지와 어긋난 구현이다. SSH 리뷰 서버 내부에서 서버 자신의
`127.0.0.1:8779`를 source로 쓰는 것은 정상이다.

Master 매핑의 정본은 `E:/KAI_VCBT/fa50visualdev_new/DT_TaskMasterSequence.csv`이고,
`Content/Data/DT_TaskMasterSequence.uasset`은 그 CSV를 `Scripts/import_task_master_dt.py`로 import한
Unreal 런타임 자산입니다. `qa/runs/review/task_master_mapping.xlsx/html`은 표시·배포용
파생 리포트이며 SSOT가 아닙니다.

2026-07-23 영구 개명은 `VARD → VADR`, `SUU → SSU`입니다. QA 덤프와 매핑 페이지는
이전 DT/리포트가 예전 SoftObjectPath를 담고 있어도 새 이름으로 정규화합니다.

## Step 5: 결과 확인 안내

로컬 인덱스 `E:\KAI_HOST\iostestapp\qa\runs\review\index.html`은 staging 확인용입니다.
운영 원본은 `ssh vivtech@192.168.10.73` 서버에서 확인하고, 운영 DB Tool UI는
`http://192.168.11.201:6003/auto-visualization`입니다. 운영 동기 API 대상은 `:6001`이며,
동기 source는 반드시 SSH 리뷰 서버의 현재 HTTP endpoint여야 합니다.

확인 뒤 Task별 결과를 에이전트가 내부 등록기로 검증대장에 기록하고, 생성된 `.claude/docs/qa-procedure-verification-current.md`에서 반영 여부를 확인합니다.

현재 유효한 사람 승인 필터는 다음 명령으로 확인합니다.

```bash
cd E:/KAI_HOST/iostestapp && py -3.11 -m qa.tools.anim.consistency_store
```
