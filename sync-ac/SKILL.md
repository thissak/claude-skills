---
name: sync-ac
description: 빌드 후 CP(콕핏) ↔ AC(항공기) 프로젝트 동기화
triggers:
  - sync-ac
  - 동기화
  - 빌드
  - build
args:
  - name: direction
    description: 동기화 방향 (cp2ac 또는 ac2cp)
    required: false
    default: "cp2ac"
---

# Build and Sync Projects

빌드 후 CP(콕핏) ↔ AC(항공기) 동기화

## 프로젝트 경로

| 프로젝트 | 경로 |
|----------|------|
| CP (Cockpit) | `E:\KAI_VCBT\fa50visualdev_new` |
| AC (Aircraft) | `E:\KAI_VCBT\fa50visualdev_new_AC` |

## 사용법

- `/sync-ac` 또는 `/sync-ac cp2ac`: 빌드 + CP → AC
- `/sync-ac ac2cp`: AC → CP (빌드 없음)

## 실행 단계

### CP → AC (기본)

**Step 1: 빌드**

```bash
"E:/Program Files/Epic Games/UE_5.4/Engine/Build/BatchFiles/Build.bat" FA50VisualDevEditor Win64 Development -Project="E:/KAI_VCBT/fa50visualdev_new/FA50VisualDev.uproject" -WaitMutex
```

**Step 2: 동기화**

```bash
powershell.exe -ExecutionPolicy Bypass -File "E:/KAI_VCBT/fa50visualdev_new/.claude/skills/sync-ac/scripts/sync-folders.ps1" -Direction cp2ac
```

### AC → CP

```bash
powershell.exe -ExecutionPolicy Bypass -File "E:/KAI_VCBT/fa50visualdev_new/.claude/skills/sync-ac/scripts/sync-folders.ps1" -Direction ac2cp
```

## 참고

동기화 대상 폴더와 스크립트 상세는 `references/sync-info.md`를 참조하세요.
