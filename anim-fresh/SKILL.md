---
name: anim-fresh
description: 사용자가 "anim-fresh", "신선도 확인", "검증 페이지 최신이야?", "애니 검증 갱신"이라고 말하면 자동시현 검증 페이지의 애셋·DB 신선도를 확인·해석·갱신하고 Task별 결과를 절차 검증 SSOT의 애니메이션 차원에 등록한다.
---

# Anim Review Freshness

자동시현 검증 페이지(`qa/runs/review/`)가 최신 애셋·DB를 반영하는지 확인하고,
애니메이터 정본(`origin/dev`)을 받아 재수집·재렌더·운영 게시까지 수행합니다.

## 전체 절차 검증 SSOT 연결

실행 전에 `.claude/docs/qa-procedure-verification-ssot.md`를 읽는다. Task별 fresh/stale 결과는 에이전트가 `record-supporting --method ANIMATION`으로 현재 절차 상태에 연결한다.

- fresh는 애니메이션 차원의 `CLEAN`이며 runtime 절차 전체 clean을 단독으로 만들지 않는다.
- stale이나 실제 매핑 문제는 `ISSUE`로 기록하되 절차 진행을 차단하는 경우에만 `--blocking`을 사용한다.
- 페이지 갱신으로 기존 애니메이션 IssueKey가 해소되면 `RESOLVED --resolves <IssueKey>`로 연결한다.
- 사용자는 결과를 말로 확인할 뿐 SSOT 표나 명령을 작성하지 않는다.

## Step 0: Unreal 점유 확인

`UnrealEditor.exe` 또는 `UnrealEditor-Cmd.exe`가 하나라도 실행 중이면 소스 오버레이·CP→AC
동기화를 시작하지 않습니다. 다른 세션의 자동검증이 끝난 후 다시 실행합니다.

```bash
cd E:/KAI_HOST/iostestapp && py -3.11 -m qa.tools.anim.source_sync
```

`source_sync` 는 `origin/dev`를 fetch하고 시퀀서 경로와 `DT_TaskMasterSequence.uasset`만
CP 작업트리에 오버레이한 뒤, 바뀐 경로만 AC 복사 프로젝트에 동기화합니다.
오버레이 위의 사용자 변경이 발견되면 덮어쓰지 않고 중단합니다.

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

## Step 3: 야간 갱신 이력 확인

```bash
tail -5 "E:/KAI_HOST/iostestapp/qa/runs/review/_nightly.log"
```

각 줄 형식: `<UTC ISO> FRESH|SKIP|REFRESHED|ERROR ...`
- `FRESH stale=0` — 정상, 변경 없음
- `REFRESHED stale_before=N tasks=M` — 야간에 정상 갱신됨
- `ERROR ...` — 예외 발생, 원인 확인 필요

## Step 4: stale 있으면 갱신 제안

갱신은 UnrealEditor-Cmd를 직접 스폰한다(에디터를 열어둘 필요 없음). 다만 렌더가 도는 경우
GPU를 점유하므로, 평일 낮이면 야간 자동 갱신(21:00)에 맡길지 먼저 물어보세요.
전체 재수집에서도 영상은 Master 콘텐츠 해시가 바뀐 건만 새로 렌더합니다.

사용자가 갱신을 원하면:

```bash
# 전체 재수집
cd E:/KAI_HOST/iostestapp && py -3.11 -m qa.tools.anim.review_run --all-anim

# 특정 태스크만
cd E:/KAI_HOST/iostestapp && py -3.11 -m qa.tools.anim.review_run <task_id> [<task_id> ...]

# 소스 동기화 + 신선도 판정 + 전체 재수집 + DB Tool 운영 스냅샷 게시
cd E:/KAI_HOST/iostestapp && py -3.11 -m qa.tools.anim.nightly_refresh
```

Master 매핑의 정본은 `E:/KAI_VCBT/fa50visualdev_new/DT_TaskMasterSequence.csv`이고,
`Content/Data/DT_TaskMasterSequence.uasset`은 그 CSV를 `Scripts/import_task_master_dt.py`로 import한
Unreal 런타임 자산입니다. `qa/runs/review/task_master_mapping.xlsx/html`은 표시·배포용
파생 리포트이며 SSOT가 아닙니다.

2026-07-23 영구 개명은 `VARD → VADR`, `SUU → SSU`입니다. QA 덤프와 매핑 페이지는
이전 DT/리포트가 예전 SoftObjectPath를 담고 있어도 새 이름으로 정규화합니다.

## Step 5: 결과 확인 안내

로컬 인덱스는 `E:\KAI_HOST\iostestapp\qa\runs\review\index.html`, 운영 UI는
`http://192.168.11.201:6003/auto-visualization`입니다. 운영 동기 API 대상은 `:6001`입니다.

확인 뒤 Task별 결과를 에이전트가 내부 등록기로 기록하고, 생성된 `.claude/docs/qa-procedure-verification-current.md`에서 반영 여부를 확인합니다.
