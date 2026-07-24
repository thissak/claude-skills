---
name: human-rig
description: 사용자가 "휴먼리그", "휴먼리그 띄워줘"라고 말하면 기존 리그를 내리고 Python IOS, Host, AC, CP 네 프로그램만 직접 실행한다. 이후 사용자가 말로 전달하는 Step 통과·정체·UI 문제·전체 완료 관찰은 에이전트가 절차 검증 SSOT 형식으로 직접 기록한다. Task 설정, manifest, 세션 daemon, viewer, readiness 대기는 사용하지 않는다.
---

# 휴먼 리그 — 단순 수동 실행

휴먼리그는 사용자가 직접 확인할 수 있도록 네 프로그램을 띄우는 단순 실행 절차다. 기동 뒤의 검증 기록은 사용자가 양식을 작성하는 방식이 아니라, 에이전트가 자연어 대화를 구조화하는 방식으로 수행한다.

## 불변 규칙

- 실행 전 기존 리그를 내린다.
- 실행 순서는 `Python IOS → Host → AC → CP`다.
- Task 번호나 회차 인자가 있어도 Task를 설정하지 않는다.
- Task 설정, 추가 자동화, 상태 대기를 하지 않는다.
- Host·DB·Unreal 설정이나 소스를 수정하지 않는다.
- 프로그램 기동 성공을 Task 검증 성공으로 기록하지 않는다.
- 대화 관찰의 판정·충돌 규칙은 `.claude/docs/qa-procedure-verification-ssot.md`를 따른다.

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

## 대화로 전달된 검증 관찰 기록

사용자는 표, JSON, 명령어를 작성하지 않는다. “Step이 넘어갔어”, “여기서 멈췄어”, “화면이 이상해”, “처음부터 끝까지 완료됐어”처럼 평소 말로 관찰만 전달한다.

에이전트는 다음 순서로 처리한다.

1. 최근 대화에서 Task와 현재 검증 범위를 찾는다. Task를 특정할 수 없을 때만 Task를 한 번 묻는다.
2. Step/Sub/I_ID가 명시되지 않았으면 아는 범위만 기록한다. 번호를 모른다는 이유로 관찰을 버리거나 사용자에게 양식 작성을 요구하지 않는다.
3. 관찰을 다음 중 하나로 분류한다.
   - 특정 Step이 넘어감: `passed`, 부분 관찰
   - 정체·오동작·화면 문제: `issue`, 부분 범위라도 IssueKey 생성
   - 전체 Task를 처음부터 끝까지 정상 완료: `full-clean`
   - 이전에 기록한 문제가 같은 범위에서 해결됨: `resolved`, 기존 IssueKey 연결
4. 에이전트가 아래 내부 등록기를 실행한다. 명령과 필드 입력을 사용자에게 넘기지 않는다.

```powershell
Set-Location E:\KAI_VCBT\fa50visualdev_new
python Scripts\qa_procedure_status.py record-human `
  --task <TaskId> `
  --observation <passed|issue|full-clean|resolved> `
  --summary "<사용자 관찰을 에이전트가 한 문장으로 정리>" `
  [--step <Step>] [--sub <Sub>] [--iid <I_ID>] `
  [--owner "<책임 경계>"] [--evidence "<스크린샷·로그·문서 경로>"] `
  [--resolves "<IssueKey>"] [--resolves-all-human]
```

5. 생성된 `.claude/docs/qa-procedure-verification-current.md`에서 해당 Task의 상태를 확인한다.
6. 사용자에게는 “기록한 관찰, 현재 상태, 열린 IssueKey 또는 해소 결과”만 자연어로 짧게 알려준다.

단일 Step 통과는 `PARTIAL`이며 전체 clean이 아니다. 부분 관찰만으로도 실제 문제는 `ISSUE_OPEN`으로 등록할 수 있다. 자동 결과와 반대되는 휴먼 관찰은 마지막 기록으로 덮지 않고 `CONFLICT`로 보존한다.

`--resolves-all-human`은 같은 휴먼 검증 범위에서 처음부터 끝까지 정상 완료해 이전 휴먼 이슈가 모두 해소됐다고 판단할 수 있을 때만 에이전트가 내부적으로 사용한다.

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
