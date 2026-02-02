---
name: qa-log
description: 언리얼 로그 파일을 실시간으로 읽어서 UDP 통신 및 상태 변경을 디버깅합니다
triggers:
  - qa-log
  - 로그 확인
  - 언리얼 로그
  - unreal log
args:
  - name: lines
    description: 읽을 줄 수
    required: false
    default: "100"
---

# QA Log Debug

언리얼 로그 파일을 실시간으로 읽어서 디버깅합니다.

## 로그 파일 경로

`E:\KAI_VCBT\fa50visualdev_new\Saved\Logs\FA50VisualDev.log`

## 실행 단계

### Step 1: 최근 로그 읽기

```bash
tail -$ARGUMENTS "E:/KAI_VCBT/fa50visualdev_new/Saved/Logs/FA50VisualDev.log"
```

인자가 없으면 기본 100줄을 읽습니다.

### Step 2: 주요 패턴 필터링 (필요시)

```bash
tail -500 "E:/KAI_VCBT/fa50visualdev_new/Saved/Logs/FA50VisualDev.log" | grep -E "(UDP61|UDP51|UDP41|Error|Warning|JUDGE)"
```

## 참고

주요 로그 패턴은 `references/log-patterns.md`를 참조하세요.
