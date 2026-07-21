---
name: screenshot
description: Windows 스크린샷을 캡처하여 세션에 첨부합니다
triggers:
  - screenshot
  - 스크린샷
  - 캡처
  - capture
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
