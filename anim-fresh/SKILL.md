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
- `REFRESHED stale_before=N tasks=M` — 야간에 정상 갱신됨
- `ERROR ...` — 예외 발생, 원인 확인 필요

## Step 4: stale 있으면 갱신 제안

갱신은 UnrealEditor-Cmd를 직접 스폰한다(에디터를 열어둘 필요 없음). 다만 렌더가 도는 경우
GPU를 점유하므로, 평일 낮이면 야간 자동 갱신(21:00)에 맡길지 먼저 물어보세요. DB만 바뀐
stale은 렌더 없이 수집만 다시 하므로 1~2분이면 끝납니다.

사용자가 갱신을 원하면:

```bash
# 전체 재수집
cd E:/KAI_HOST/iostestapp && py -3.11 -m qa.tools.anim.review_run --all-anim

# 특정 태스크만
cd E:/KAI_HOST/iostestapp && py -3.11 -m qa.tools.anim.review_run <task_id> [<task_id> ...]
```

## Step 5: 결과 확인 안내

인덱스 페이지 경로를 안내하세요: `E:\KAI_HOST\iostestapp\qa\runs\review\index.html` (브라우저로 열람)
