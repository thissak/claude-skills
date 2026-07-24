---
name: screenshot
description: 사용자가 "screenshot", "스크린샷", "캡처", "capture"라고 말하면 Windows 스크린샷을 캡처해 세션에 첨부하고, 활성 절차 검증 문맥이면 에이전트가 해당 Task·IssueKey의 보조 증거로 등록한다.
---

# Screenshot Capture

Windows Snipping Tool로 스크린샷을 캡처하고 세션에 첨부합니다.

## 실행 단계

### Step 1: 스크린샷 캡처

PowerShell 스크립트를 실행하여 Snipping Tool을 열고 캡처 완료를 대기합니다.

```bash
powershell.exe -ExecutionPolicy Bypass -File "E:/KAI_VCBT/fa50visualdev_new/.claude/skills/screenshot/scripts/capture.ps1"
```

스크립트가 파일 경로를 출력합니다. 30초 타임아웃이 있습니다.

### Step 2: 세션에 첨부

출력된 경로의 PNG 파일을 Read 도구로 읽어서 세션에 첨부합니다.

### Step 3: 절차 검증 증거 연결

활성 Task나 휴먼리그 관찰을 증명하기 위한 캡처라면 에이전트가 `.claude/docs/qa-procedure-verification-ssot.md`에 따라 `record-supporting --method SCREENSHOT --verdict OBSERVATION`으로 해당 Task와 IssueKey에 연결합니다. 스크린샷 단독으로 Task를 clean 판정하지 않으며, 사용자에게 SSOT 필드나 명령 실행을 요구하지 않습니다.
