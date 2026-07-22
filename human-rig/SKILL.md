---
name: human-rig
description: 사용자가 "휴먼리그", "휴먼리그 띄워줘"라고 말하면 기존 리그를 내리고 Python IOS, Host, AC, CP 네 프로그램만 직접 실행한다. Task 설정, manifest, 세션 daemon, viewer, readiness 대기는 사용하지 않는다.
---

# 휴먼 리그 — 단순 수동 실행

휴먼리그는 사용자가 직접 확인할 수 있도록 네 프로그램을 띄우는 단순 실행 절차다.

## 불변 규칙

- 실행 전 기존 리그를 내린다.
- 실행 순서는 `Python IOS → Host → AC → CP`다.
- Task 번호나 회차 인자가 있어도 Task를 설정하지 않는다.
- Task 설정, 추가 자동화, 상태 대기를 하지 않는다.
- Host·DB·Unreal 설정이나 소스를 수정하지 않는다.

## 기동

PowerShell에서 아래 블록을 그대로 실행한다. 네 `Start-Process` 호출이 반환되면 기동 요청은 끝이다.

```powershell
$IosDir = 'E:\KAI_HOST\iostestapp'
$IosMain = Join-Path $IosDir 'main.py'
$HostDir = 'E:\KAI_HOST\fa50m-host'
$HostExe = Join-Path $HostDir 'x64\FA50MHOST.exe'
$UnrealExe = 'E:\Program Files\Epic Games\UE_5.4\Engine\Binaries\Win64\UnrealEditor.exe'
$AcDir = 'E:\KAI_VCBT\fa50visualdev_new_AC'
$AcProject = Join-Path $AcDir 'FA50VisualDev.uproject'
$CpDir = 'E:\KAI_VCBT\fa50visualdev_new'
$CpProject = Join-Path $CpDir 'FA50VisualDev.uproject'

Set-Location $IosDir
python qa_rig.py down

$IosPattern = [regex]::Escape($IosMain)
Get-CimInstance Win32_Process |
    Where-Object {
        $_.Name -in @('python.exe', 'pythonw.exe') -and
        $_.CommandLine -match $IosPattern
    } |
    ForEach-Object { Stop-Process -Id $_.ProcessId -Force }

$AcArgs = '"{0}" /Game/01_Visual/00_Level/VCBT/FA50_Maintenance_AP -game -windowed -ResX=800 -ResY=450 -nosplash -AutomationDriver -AutomationDriverPort=8791' -f $AcProject
$CpArgs = '"{0}" /Game/01_Visual/00_Level/VCBT/FA50_Maintenance_CP -game -windowed -ResX=800 -ResY=450 -nosplash -AutomationDriver -AutomationDriverPort=8790 -AutomationAutoCamera' -f $CpProject

Start-Process -FilePath 'pythonw.exe' -ArgumentList ('"{0}"' -f $IosMain) -WorkingDirectory $IosDir
Start-Process -FilePath $HostExe -WorkingDirectory $HostDir
Start-Process -FilePath $UnrealExe -ArgumentList $AcArgs -WorkingDirectory $AcDir
Start-Process -FilePath $UnrealExe -ArgumentList $CpArgs -WorkingDirectory $CpDir
```

완료 보고는 `Python IOS, Host, AC, CP 실행 명령 완료`로만 한다. Task 상태나 READY를 보고하지 않는다.

## 종료

사용자가 "휴먼리그 내려줘", "리그 내려줘", "종료"라고 하면 아래만 실행한다.

```powershell
$IosDir = 'E:\KAI_HOST\iostestapp'
$IosMain = Join-Path $IosDir 'main.py'

Set-Location $IosDir
python qa_rig.py down

$IosPattern = [regex]::Escape($IosMain)
Get-CimInstance Win32_Process |
    Where-Object {
        $_.Name -in @('python.exe', 'pythonw.exe') -and
        $_.CommandLine -match $IosPattern
    } |
    ForEach-Object { Stop-Process -Id $_.ProcessId -Force }
```

종료 후 `python qa_rig.py status`로 Host·AC·CP가 down인지 확인한다. Python IOS는 위의 exact command-line match가 없으면 down이다.
