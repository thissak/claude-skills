---
name: qa-host
description: 사용자가 "qa-host", "호스트 로그", "host log", "judge 확인"이라고 말하면 기본 E:/KAI_HOST/debug_qa.log 또는 지정 로그를 읽어 Unreal↔Host 판정 문제를 분석하고, Task 문맥이 있으면 절차 검증 SSOT에 진단 증거로 연결한다.
---

# QA Host Debug

Host 로그 파일을 읽어서 언리얼-Host 간 통신 문제를 디버깅합니다.

## 전체 절차 검증 SSOT 연결

Task 문맥이 있는 로그 분석은 `.claude/docs/qa-procedure-verification-ssot.md`를 따른다. Host 로그는 원인 증거이며 단독 Task clean 판정에 사용하지 않는다.

- 문제를 확인하면 에이전트가 `record-supporting --method LOG --verdict ISSUE`로 등록한다.
- 정상 흐름이나 기존 IssueKey의 근거는 `OBSERVATION`으로 연결한다.
- 사용자는 로그 내용을 말로 전달할 수 있고, 구조화된 기록은 에이전트가 작성한다.

## 로그 파일 경로

기본: `E:\KAI_HOST\debug_qa.log`

## 실행 단계

### Step 1: Host 로그 파일 읽기

```bash
tail -100 "$ARGUMENTS"
```

인자가 없으면 기본 경로를 사용합니다.

### Step 2: JUDGE 결과 필터링

```bash
tail -500 "$ARGUMENTS" | grep -E "(JUDGE|RECV|UDP)"
```

## 참고

주요 로그 패턴과 문제 해결 가이드는 `references/` 폴더를 참조하세요.
