---
name: qa-host
description: Host 로그 파일을 읽어서 언리얼-Host 간 UDP 통신 문제를 디버깅합니다
triggers:
  - qa-host
  - 호스트 로그
  - host log
  - judge 확인
args:
  - name: logpath
    description: Host 로그 파일 경로
    required: false
    default: "D:/KAI/Host/logs/host.log"
---

# QA Host Debug

Host 로그 파일을 읽어서 언리얼-Host 간 통신 문제를 디버깅합니다.

## 로그 파일 경로

기본: `D:\KAI\Host\logs\host.log`

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
