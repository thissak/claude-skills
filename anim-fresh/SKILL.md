---
name: anim-fresh
description: 자동시현 검증 페이지 신선도 체크·해석·갱신 ("신선도 확인", "검증 페이지 최신이야?" 등에 사용)
triggers:
  - anim-fresh
  - 신선도 확인
  - 검증 페이지 최신
  - 애니 검증 갱신
---

# Anim Review Freshness

자동시현 검증 페이지(`qa/runs/review/`)가 최신 애셋·DB를 반영하는지 확인하고, 필요하면 갱신을 제안합니다.

## Step 1: 신선도 체크 실행

```bash
cd E:/KAI_HOST/iostestapp && PYTHONIOENCODING=utf-8 py -3.11 -m qa.tools.anim.freshness_check --json
```

exit 0=fresh, 1=stale, 2=오류. JSON에 `fresh`(bool), `stale_tasks`(태스크→사유 목록), `checked_utc`가 담겨 있습니다.

## Step 2: stale 사유 해석

`stale_tasks`의 각 사유는 접두사로 구분됩니다:

- `asset: <path>` — 마스터 시퀀스 또는 `DT_AnimIdMarkerMapping` 애셋이 앵커 커밋 이후 변경됨 → 재렌더 필요
- `db: steps 불일치` — DB의 스텝/애니메이션 ID/절차 텍스트가 manifest와 달라짐 → 재수집 필요
- `dirty: <path>` — 커밋 안 된 변경(보수적으로 항상 재확인 대상)

태스크별로 사유를 사용자에게 요약해서 보고하세요.

## Step 3: 야간 갱신 이력 확인

```bash
tail -5 "E:/KAI_HOST/iostestapp/qa/runs/review/_nightly.log"
```

각 줄 형식: `<UTC ISO> FRESH|SKIP|REFRESHED|ERROR ...`
- `FRESH stale=0` — 정상, 변경 없음
- `SKIP editor-down stale=N` — stale이 있었지만 에디터(원격실행 노드) 미기동으로 갱신 스킵(실패 아님)
- `REFRESHED stale_before=N tasks=M` — 야간에 정상 갱신됨
- `ERROR ...` — 예외 발생, 원인 확인 필요

## Step 4: stale 있으면 갱신 제안

**평일 낮 시간이면 먼저 경고하세요**: 렌더는 UnrealEditor 프로세스를 새로 스폰하고, manifest 재수집은 CP 에디터가 원격실행 중이어야 합니다 — GPU와 에디터 세션을 점유하므로 작업 중(낮 시간)이라면 방해가 될 수 있습니다. 야간 자동 갱신(21:00 스케줄러)에 맡기거나, 급하면 사용자 확인을 받은 뒤 진행하세요.

사용자가 갱신을 원하면:

```bash
# 전체 재수집
cd E:/KAI_HOST/iostestapp && py -3.11 -m qa.tools.anim.review_run --all-anim

# 특정 태스크만
cd E:/KAI_HOST/iostestapp && py -3.11 -m qa.tools.anim.review_run <task_id> [<task_id> ...]
```

## Step 5: 결과 확인 안내

인덱스 페이지 경로를 안내하세요: `E:\KAI_HOST\iostestapp\qa\runs\review\index.html` (브라우저로 열람)
